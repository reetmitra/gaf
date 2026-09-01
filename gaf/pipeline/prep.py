"""Deterministic preparation — everything the fast loop does before a model is called.

What this module does. Three pure functions, run in this order for every response:

* **segmentation** (`segment_response`) — cut the response into quotable phrase-level
  `Segment` spans over ``gaf.textnorm.normalise(response.content)``;
* **dedup pre-check** (`dedup_precheck`) — the cheap deterministic look that spots a
  response whose normalised text has already been coded in this run, before two model
  calls are spent on it a second time;
* **context assembly** (`assemble_context`) — the hierarchy skeleton of a **frozen
  snapshot** plus the top-k codes retrieval chose, returned as a `CoderContext`.

`prepare` runs all three and is the only function the fast loop calls.

Everything here is a pure function of its arguments: no I/O, no store, no model, no
randomness, no wall clock. That is the point — the design law says deterministic code
runs *before* any LLM call, and a model is consulted only where the geometry is
genuinely ambiguous. Prep is the deterministic half of that sentence.

**Spans index the normalised text, never the raw source** (`gaf.textnorm`). A segment
carried into the store, re-checked by S2 and displayed in the HTML explorer all refer
to the same characters because there is exactly one normalisation function.

**Segmentation must not assume a full stop exists.** Three of the twenty responses in
the real seed sample carry no sentence terminator at all, at 107 to 115 words, and five
are under the survey's own 100-word minimum, the shortest at 28 words (ADR-0015). A
splitter that cut only on ``.?!`` would return one 110-word "sentence" on 15% of the
corpus, which is the shape S2b, S4 and S5 all misread. So the cascade is sentences,
then clause boundaries, then fixed word windows, and it degrades gracefully in the
other direction too: a 28-word answer yields the two or three phrases it actually
contains rather than being padded out to a quota.

Validation principles: **reliability** — the same response yields the same segments,
the same retrieval and the same context in every run and every process, which is what
makes "re-running a batch against the same snapshot reproduces the same output" a
checkable claim; **transparency** — the coder's whole visible context is assembled by
code a reviewer can read, not by a model.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from gaf.agents.coder import CoderContext
from gaf.config import CodingRules, RunConfig
from gaf.embed.matcher import ScoredCode, top_k_codes
from gaf.embed.protocol import Embedder
from gaf.ids import content_hash, mint
from gaf.models import Response, Segment
from gaf.store.snapshot import Snapshot
from gaf.textnorm import NORMALISATION_VERSION, normalise

__all__ = [
    "MIN_SEGMENT_WORDS",
    "DedupVerdict",
    "PreparedResponse",
    "assemble_context",
    "dedup_precheck",
    "prepare",
    "segment_id",
    "segment_response",
    "segment_spans",
]

#: A span shorter than this is not a phrase, it is a fragment, and it is folded back
#: into the segmentation's fallback rather than offered as a coding unit. Three words
#: is the shortest span that can carry a subject and a predicate; the number lives here
#: rather than in `CodingRules` because it describes *this splitter's* floor and not a
#: rule of the PI's, and `gaf.llm.mock` names the same floor for the same reason.
MIN_SEGMENT_WORDS = 3

#: A sentence: a run of non-terminator characters plus whatever terminators close it.
#: Terminators are kept, so a segment reads as the sentence it came from.
_SENTENCE_RE = re.compile(r"[^.!?]+[.!?]*")

#: Clause boundaries, used when sentences are absent or too long. Punctuation and
#: coordinating conjunctions are both *dropped* from the pieces they separate: a
#: segment is a phrase, and the joining word belongs to neither side of the join.
_CLAUSE_RE = re.compile(
    r"[,;:]+|\s+(?:and|but|so|because|while|which|whereas|although|though|however|or|yet)\s+",
    re.IGNORECASE,
)

_WORD_RE = re.compile(r"\S+")


# --------------------------------------------------------------------------- #
# Span arithmetic
# --------------------------------------------------------------------------- #


def _strip(text: str, start: int, end: int) -> tuple[int, int]:
    """Shrink ``[start, end)`` past leading and trailing whitespace."""
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return start, end


def _words(text: str, span: tuple[int, int]) -> int:
    return len(_WORD_RE.findall(text[span[0] : span[1]]))


def _nonempty(spans: Sequence[tuple[int, int]]) -> list[tuple[int, int]]:
    return [span for span in spans if span[1] > span[0]]


def _sentences(text: str) -> list[tuple[int, int]]:
    """Sentence spans of the whole text, terminators kept, whitespace stripped."""
    return _nonempty([_strip(text, m.start(), m.end()) for m in _SENTENCE_RE.finditer(text)])


def _clauses(text: str, span: tuple[int, int]) -> list[tuple[int, int]]:
    """Cut `span` at every clause boundary, discarding the delimiter itself."""
    start, end = span
    pieces: list[tuple[int, int]] = []
    cursor = start
    for match in _CLAUSE_RE.finditer(text, start, end):
        piece = _strip(text, cursor, match.start())
        if piece[1] > piece[0]:
            pieces.append(piece)
        cursor = match.end()
    tail = _strip(text, cursor, end)
    if tail[1] > tail[0]:
        pieces.append(tail)
    return pieces or [span]


def _windows(text: str, span: tuple[int, int], max_words: int) -> list[tuple[int, int]]:
    """Last resort: cut a still-too-long span into runs of at most `max_words` words.

    Reached only by text that has neither a terminator nor a clause boundary in
    `max_words` words — rare, and better served by an arbitrary but reproducible cut
    than by a quote the PI's phrase/sentence rule would reject.
    """
    words = [(m.start(), m.end()) for m in _WORD_RE.finditer(text, span[0], span[1])]
    if len(words) <= max_words:
        return [span]
    return [
        (chunk[0][0], chunk[-1][1])
        for index in range(0, len(words), max_words)
        if (chunk := words[index : index + max_words])
    ]


#: A splitter: given the text and one span, the pieces that span becomes.
_Splitter = Callable[[str, tuple[int, int]], list[tuple[int, int]]]


def _expand(
    text: str,
    spans: Sequence[tuple[int, int]],
    split: _Splitter,
    *,
    when_longer_than: int,
) -> list[tuple[int, int]]:
    """Apply `split` to every span over `when_longer_than` words, keep the rest."""
    return [
        piece
        for span in spans
        for piece in (split(text, span) if _words(text, span) > when_longer_than else [span])
    ]


# --------------------------------------------------------------------------- #
# Segmentation
# --------------------------------------------------------------------------- #


def segment_spans(normalised: str, rules: CodingRules | None = None) -> list[tuple[int, int]]:
    """Phrase-level spans of `normalised`, in reading order. The splitter itself.

    The cascade, in order, and each step's reason:

    1. **sentences** — the PI's unit is "the level of phrase or sentence";
    2. **clauses**, applied to everything when step 1 produced fewer than
       ``rules.min_codes_per_response`` spans, and otherwise only to the spans longer
       than ``rules.max_quote_words``. The first condition is what handles a response
       with no sentence terminator at all: one enormous "sentence" becomes the phrases
       it is actually made of;
    3. **fixed word windows** for anything still over ``rules.max_quote_words``.

    Spans that come out under `MIN_SEGMENT_WORDS` words are dropped — unless that would
    leave nothing, in which case the unfiltered spans are returned, because a very short
    response must still be segmentable into the little it contains.

    Deterministic and total: `normalised` is assumed to be `gaf.textnorm.normalise`d
    already, spans never overlap, and they are returned in ascending start order.
    """
    rules = rules or CodingRules()
    max_words = rules.max_quote_words
    if not normalised:
        return []

    spans = _sentences(normalised)
    if not spans:
        return []
    if len(spans) < rules.min_codes_per_response:
        spans = [piece for span in spans for piece in _clauses(normalised, span)]
    spans = _expand(normalised, spans, _clauses, when_longer_than=max_words)
    spans = _expand(
        normalised,
        spans,
        lambda text, span: _windows(text, span, max_words),
        when_longer_than=max_words,
    )
    kept = [span for span in spans if _words(normalised, span) >= MIN_SEGMENT_WORDS]
    return kept or spans


def segment_id(response: Response, start: int, end: int) -> str:
    """Content-addressed id of one segment: the response it cuts and where it cuts it."""
    return mint("seg", response.source, response.id, start, end)


def segment_response(response: Response, rules: CodingRules | None = None) -> list[Segment]:
    """Cut `response` into `Segment` objects over its normalised text.

    ``Segment.start``/``end`` index ``normalise(response.content)`` and ``Segment.text``
    is the slice itself, so a segment survives a JSON round-trip without the corpus at
    hand. Ids are content-addressed, so the same response segments to the same ids in
    every run.
    """
    normalised = normalise(response.content)
    return [
        Segment(
            id=segment_id(response, start, end),
            response_id=response.id,
            start=start,
            end=end,
            text=normalised[start:end],
        )
        for start, end in segment_spans(normalised, rules)
    ]


# --------------------------------------------------------------------------- #
# Dedup pre-check
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class DedupVerdict:
    """What the cheap deterministic look found, before any model was asked anything.

    A duplicate is **reported, never dropped**: two respondents who wrote the same
    sentence are two respondents, and the occurrence matrix must say so. What the
    verdict buys is that the audit log names the earlier response, so a reviewer seeing
    the same quote twice can tell an echo from a coincidence.
    """

    content_hash: str
    duplicate_of: int | None = None

    @property
    def is_duplicate(self) -> bool:
        return self.duplicate_of is not None

    def to_json(self) -> dict[str, Any]:
        return {"content_hash": self.content_hash, "duplicate_of": self.duplicate_of}


def dedup_precheck(
    response: Response, seen: Mapping[str, int] | None = None
) -> DedupVerdict:
    """Hash the normalised response and look it up among the responses already prepared.

    Exact-match only, and deliberately so: "is this the same text" is a question
    deterministic code answers exactly, while "is this the same meaning" is a judgment
    about meaning and belongs to the embedding layer and the judge. Mixing the two here
    would put a threshold in front of the coders that nothing downstream could audit.
    """
    digest = content_hash(f"{NORMALISATION_VERSION}\x1f{normalise(response.content)}")
    earlier = (seen or {}).get(digest)
    return DedupVerdict(
        content_hash=digest,
        duplicate_of=None if earlier is None or earlier == response.id else earlier,
    )


# --------------------------------------------------------------------------- #
# Context assembly
# --------------------------------------------------------------------------- #


def retrieve(
    response: Response,
    snapshot: Snapshot,
    embedder: Embedder,
    *,
    top_k: int,
) -> list[ScoredCode]:
    """The top-k codes of the frozen snapshot nearest this response, best first.

    The query is the normalised response text and the codes are rendered by
    `gaf.embed.protocol.code_text`, which is the single rendering function: retrieval,
    the dedup gate and cross-coder matching therefore measure the same object in the
    same versioned space.
    """
    return top_k_codes(normalise(response.content), snapshot.codebook, embedder, k=top_k)


def assemble_context(
    response: Response,
    snapshot: Snapshot,
    retrieved: Sequence[ScoredCode],
) -> CoderContext:
    """Build the coder's context from a **frozen** snapshot and a retrieval ranking.

    Both coders receive this one object, so any asymmetry between them would have to be
    introduced deliberately downstream. Handoffs carry ids, not prose: only the ranked
    code ids cross this boundary and the codes themselves are re-grounded from the
    snapshot inside `CoderContext.from_snapshot`.
    """
    return CoderContext.from_snapshot(
        response, snapshot, retrieved_ids=[scored.code_id for scored in retrieved]
    )


# --------------------------------------------------------------------------- #
# The one entry point the fast loop calls
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class PreparedResponse:
    """Everything deterministic prep produced for one response.

    Carried into the loop whole, so that the audit log can record what the coders were
    given without re-deriving any of it.
    """

    response: Response
    normalised: str
    context: CoderContext
    snapshot_id: str = ""
    segments: list[Segment] = field(default_factory=list)
    retrieved: list[ScoredCode] = field(default_factory=list)
    dedup: DedupVerdict = DedupVerdict(content_hash="")

    def segment_for(self, span: tuple[int, int] | None) -> Segment | None:
        """The segment a verified quote span sits in — the one it overlaps most.

        Ties resolve to the earliest segment, so the mapping is a function of the spans
        rather than of iteration order. `None` when the span is `None` (S2 could not
        locate the quote) or overlaps no segment at all.
        """
        if span is None:
            return None
        best: Segment | None = None
        best_overlap = 0
        for segment in self.segments:
            overlap = min(segment.end, span[1]) - max(segment.start, span[0])
            if overlap > best_overlap:
                best, best_overlap = segment, overlap
        return best

    def to_json(self) -> dict[str, Any]:
        """The shape the audit log records: what was prepared, not the prose of it."""
        return {
            "response_id": self.response.id,
            "source": self.response.source,
            "snapshot_id": self.snapshot_id,
            "norm_version": NORMALISATION_VERSION,
            "n_segments": len(self.segments),
            "n_retrieved": len(self.retrieved),
            "retrieved": [scored.to_json() for scored in self.retrieved],
            "dedup": self.dedup.to_json(),
        }


def prepare(
    response: Response,
    snapshot: Snapshot,
    embedder: Embedder,
    *,
    config: RunConfig | None = None,
    seen: Mapping[str, int] | None = None,
) -> PreparedResponse:
    """Segment, dedup-check and assemble the context for one response. Pure.

    This is the whole of the fast loop's first stage: after it returns, everything a
    coder will see has been decided by deterministic code, and the only remaining
    question is what the two models make of it.
    """
    config = config or RunConfig()
    normalised = normalise(response.content)
    retrieved = retrieve(response, snapshot, embedder, top_k=config.retrieval_top_k)
    return PreparedResponse(
        response=response,
        normalised=normalised,
        context=assemble_context(response, snapshot, retrieved),
        snapshot_id=snapshot.snapshot_id,
        segments=segment_response(response, config.rules),
        retrieved=retrieved,
        dedup=dedup_precheck(response, seen),
    )
