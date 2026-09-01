"""Deterministic mock model clients — the offline path, which is the default path.

Every test, every CI run and `make demo` run on these. They are pure functions of
their `LLMRequest`: the same request yields a byte-identical `LLMResult` across runs,
processes and platforms, because every branch is driven by `hashlib` rather than by
`hash()` (salted per process) or an unseeded RNG. No wall-clock latency is recorded,
because none was spent: an offline call is arithmetic, and a fabricated latency in an
audit log is a small lie.

Three personas, matching the three LLM roles:

* `MockCoderClient` — proposes candidates derived **from the response text itself**, so
  it works on arbitrary input, not only on the fixture corpus. Two personas, A and B,
  agree on most codes and diverge on some; that divergence is what gives the
  cross-coder agreement check (M1) and the disagreement router something to do.
* `MockJudgeClient` — recognises the task and answers deterministically, biased toward
  keeping data.
* `MockRefactorerClient` — emits a small, structurally valid edit script including a
  `split` and a `reparent`, the two operations whose absence in the predecessor study
  is the documented cause of codebook flattening.

**Segmentation is phrase-level, not sentence-level.** The PI's rule is "coding is
applied on the level of phrase or sentence", and three of the twenty real seed
responses contain no sentence terminator at all (ADR-0015). Splitting only on `.?!`
would quote such a response whole, which trips S2b, starves S5 of codes and can raise a
spurious S4 error when several codes land on one enormous span. So the splitter falls
back to clause boundaries whenever a sentence split yields too few segments or a
segment exceeds `CodingRules.max_quote_words`, and hard-windows anything still too long.
Every quote it emits is a **verbatim substring of `gaf.textnorm.normalise(text)`**,
which is the property the S2 provenance check depends on.

Validation principles: **reliability** — an offline run is reproducible to the byte;
**epistemic diversity** — two personas that genuinely disagree are what make an
agreement statistic mean something.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from gaf.checks.contracts import FIT_VERDICTS
from gaf.config import MOCK_REGISTRY, CodingRules, ModelSpec
from gaf.llm.base import LLMRequest, LLMResult, TaskType, fail_safe_for, validate_enum
from gaf.models import family_of
from gaf.textnorm import normalise

__all__ = [
    "DISPUTE_VERDICTS",
    "FABRICATED_QUOTE",
    "FALLBACK_CODES",
    "KEYWORD_TABLE",
    "MOCKDISPUTE_DROP",
    "MOCKFIT_UNNECESSARY",
    "MOCKROUTE_MERGE",
    "PERSONAS",
    "ROUTE_VERDICTS",
    "MockCode",
    "MockCoderClient",
    "MockJudgeClient",
    "MockRefactorerClient",
    "extract_code_ids",
    "extract_response_id",
    "extract_response_text",
    "mock_candidates_for",
    "split_segments",
]

# --------------------------------------------------------------------------- #
# Sentinels
# --------------------------------------------------------------------------- #

#: Persona B cites this rarely and deterministically, so the S2 provenance-drop path is
#: exercised on any corpus. Declared here rather than imported from `tests.fixtures`:
#: the package must not depend on its own test tree. It occurs in no real response.
FABRICATED_QUOTE = "in 2050 every household will be issued a personal weather licence"

#: `MockJudgeClient` rules UNNECESSARY on a JUDGE_FIT request whose prompt contains
#: this token. The same literal is planted in `tests.fixtures.corpus`; the string *is*
#: the contract between the fixture and the mock, so both spell it out.
MOCKFIT_UNNECESSARY = "MOCKFIT_UNNECESSARY"

#: Forces a JUDGE_DISPUTE reply of DROP. Without it the judge keeps, unless the
#: content digest lands on the rare drop branch.
MOCKDISPUTE_DROP = "MOCKDISPUTE_DROP"

#: Forces a JUDGE_ROUTE reply of MERGE.
MOCKROUTE_MERGE = "MOCKROUTE_MERGE"

#: Verdict whitelists. They mirror the shape of `FAIL_SAFE_DEFAULTS` in
#: `gaf.llm.base`, which is frozen and does not export them.
DISPUTE_VERDICTS: tuple[str, ...] = ("KEEP", "DROP")
ROUTE_VERDICTS: tuple[str, ...] = ("MERGE", "CREATE")

PERSONAS: tuple[str, ...] = ("A", "B")

_RULES = CodingRules()

#: How often persona B prefers the runner-up code for a segment (1 in N segments).
#: Calibrated on the synthetic corpus to leave the two personas agreeing on about
#: four names in five while still diverging on about a third of responses — enough
#: disagreement to exercise M1 and the router, not so much that agreement is noise.
_B_DIVERGENCE_MODULUS = 5
#: How often persona B adds a fabricated-quote candidate (1 in N responses).
_B_FABRICATION_MODULUS = 6
#: 1 in N JUDGE_DISPUTE calls are dropped; the rest are kept.
_DISPUTE_DROP_MODULUS = 8
#: 1 in N JUDGE_ROUTE calls merge; the rest create.
_ROUTE_MERGE_MODULUS = 3

#: Never propose more than this many codes for one response. Well inside the PI's
#: "usually between 2 and 12" (`CodingRules.max_codes_per_response`).
_MAX_CANDIDATES = 6
#: Below this many segments a response is re-split at clause boundaries.
_MIN_SEGMENTS = 3
#: A segment shorter than this is not worth quoting.
_MIN_SEGMENT_WORDS = 3


def _digest(*parts: str) -> int:
    """A stable non-negative integer from the parts. blake2b, never `hash()`."""
    hasher = hashlib.blake2b(digest_size=8)
    for part in parts:
        hasher.update(part.encode("utf-8"))
        hasher.update(b"\x1f")
    return int.from_bytes(hasher.digest(), "big")


def _token_estimate(text: str) -> int:
    """A deterministic stand-in for a tokeniser: roughly four characters per token."""
    return max(1, len(text) // 4)


# --------------------------------------------------------------------------- #
# Segmentation — phrase or sentence, never a whole unpunctuated response
# --------------------------------------------------------------------------- #

_SENTENCE_RE = re.compile(r"[^.!?]+[.!?]*")

#: Clause boundaries. Punctuation and coordinating conjunctions are both *excluded*
#: from the segments they separate — quotes need only be verbatim substrings, not a
#: tiling of the response, and dropping the joining word yields a cleaner phrase.
_CLAUSE_RE = re.compile(
    r"[,;:]+|\s+(?:and|but|so|because|while|which|whereas|although|though|however|or|yet)\s+",
    re.IGNORECASE,
)

_SPACE_RE = re.compile(r"\S+")


def _strip_span(text: str, start: int, end: int) -> tuple[int, int]:
    """Shrink ``[start, end)`` past leading and trailing whitespace."""
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return start, end


def _word_count(text: str, start: int, end: int) -> int:
    return len(text[start:end].split())


def _split_by(text: str, span: tuple[int, int], pattern: re.Pattern[str]) -> list[tuple[int, int]]:
    """Cut a span at every match of `pattern`, discarding the matched delimiters."""
    start, end = span
    pieces: list[tuple[int, int]] = []
    cursor = start
    for match in pattern.finditer(text, start, end):
        piece = _strip_span(text, cursor, match.start())
        if piece[1] > piece[0]:
            pieces.append(piece)
        cursor = match.end()
    tail = _strip_span(text, cursor, end)
    if tail[1] > tail[0]:
        pieces.append(tail)
    return pieces or [span]


def _window_split(text: str, span: tuple[int, int], max_words: int) -> list[tuple[int, int]]:
    """Last resort: cut a still-too-long span into runs of at most `max_words` words."""
    words = [(m.start(), m.end()) for m in _SPACE_RE.finditer(text, span[0], span[1])]
    if len(words) <= max_words:
        return [span]
    pieces: list[tuple[int, int]] = []
    for index in range(0, len(words), max_words):
        chunk = words[index : index + max_words]
        pieces.append((chunk[0][0], chunk[-1][1]))
    return pieces


def split_segments(
    text: str,
    *,
    max_words: int = _RULES.max_quote_words,
    min_segments: int = _MIN_SEGMENTS,
) -> list[str]:
    """Split `text` into quotable phrase-level segments.

    Every returned string is a **verbatim substring of ``normalise(text)``**, is at most
    `max_words` words long, and contains at most one sentence terminator — the three
    properties S2, S2b and S4 rely on.

    The cascade is: sentences (`.?!`); then clause boundaries, applied to everything if
    the sentence split produced fewer than `min_segments` segments and otherwise only to
    the segments that are too long; then fixed word windows for anything still over the
    bound. Abbreviations ("e.g.") are deliberately not special-cased — a wrong cut costs
    a slightly odd quote, while a rule table would be a source of drift.

    Very short input degrades gracefully: a 28-word response yields the two or three
    phrases it actually contains rather than being padded out to a quota.
    """
    norm = normalise(text)
    if not norm:
        return []
    spans = [
        span
        for match in _SENTENCE_RE.finditer(norm)
        if (span := _strip_span(norm, match.start(), match.end()))[1] > span[0]
    ]
    if not spans:
        return []
    if len(spans) < min_segments:
        spans = [piece for span in spans for piece in _split_by(norm, span, _CLAUSE_RE)]
    spans = [
        piece
        for span in spans
        for piece in (
            _split_by(norm, span, _CLAUSE_RE)
            if _word_count(norm, *span) > max_words
            else [span]
        )
    ]
    spans = [
        piece
        for span in spans
        for piece in (
            _window_split(norm, span, max_words)
            if _word_count(norm, *span) > max_words
            else [span]
        )
    ]
    kept = [span for span in spans if _word_count(norm, *span) >= _MIN_SEGMENT_WORDS]
    return [norm[start:end] for start, end in (kept or spans)]


# --------------------------------------------------------------------------- #
# The keyword table — how a segment becomes a two-level code
# --------------------------------------------------------------------------- #


class MockCode:
    """One row of the keyword table: a two-level code and the vocabulary that evokes it."""

    __slots__ = ("description", "keywords", "name")

    def __init__(self, name: str, description: str, keywords: tuple[str, ...]) -> None:
        self.name = name
        self.description = description
        self.keywords = keywords

    def score(self, haystack: str) -> int:
        """How many distinct keywords of this code occur in `haystack`."""
        return sum(1 for keyword in self.keywords if keyword in haystack)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"MockCode({self.name!r})"


#: The vocabulary of *this* corpus: open-ended responses about AI in 2050 from an Indian
#: sample. Names follow the two-level `toplevel-sub_level` grammar of S3. Order is the
#: tie-break when two codes match a segment equally well, so it is part of the contract
#: and must not be shuffled. Every description is a real sentence about the code, never
#: a copy of a quote — a description that copies its own evidence trips S1.
KEYWORD_TABLE: tuple[MockCode, ...] = (
    MockCode(
        "negative_impacts-job_loss",
        "Existing categories of paid work disappear as AI replaces human labour.",
        (
            "unemployment", "unemployed", "jobless", "job loss", "lose their job",
            "redundant", "laid off", "retrench", "replace", "replaced", "replaces",
            "replacing", "fewer job", "no income", "livelihood", "out of work",
            "will suffer", "disappear",
        ),
    ),
    MockCode(
        "negative_impacts-unskilled_workers",
        "Workers without formal skills or education carry the cost of automation.",
        (
            "non skilled", "unskilled", "low skilled", "manual worker", "labourer",
            "labour class", "factory worker", "uneducated", "without education",
            "blue collar", "daily wage", "do not have", "entry level",
        ),
    ),
    MockCode(
        "applications-healthcare",
        "AI is applied to diagnosis, treatment or access to medical care.",
        (
            "health", "healthcare", "doctor", "medical", "medicine", "diagnose",
            "diagnosis", "illness", "disease", "scan", "patient", "hospital",
            "treatment", "nurse", "surgery", "clinic",
        ),
    ),
    MockCode(
        "applications-education",
        "AI changes how teaching and learning are delivered.",
        (
            "education", "school", "teacher", "teach", "student", "classroom",
            "lecturer", "tutor", "curriculum", "exam", "university", "college",
            "children will", "guide",
        ),
    ),
    MockCode(
        "applications-automation",
        "Physical or clerical work is carried out by machines instead of by people.",
        (
            "automate", "automated", "automation", "automatic", "machine", "robot",
            "factory", "factories", "packing", "sorting", "assembly", "manual work",
            "manually", "mechanis", "production line", "whole line",
        ),
    ),
    MockCode(
        "applications-data_driven_systems",
        "Systems that learn from accumulated data direct everyday decisions.",
        (
            "machine learning", "algorithm", "data", "dataset", "training",
            "predictive", "prediction", "analyse", "analysis", "processing",
            "learns from", "pattern",
        ),
    ),
    MockCode(
        "applications-industry_and_transport",
        "AI is deployed across industry, agriculture, transport and infrastructure.",
        (
            "industry", "industries", "manufactur", "transport", "vehicle", "driving",
            "drive", "traffic", "logistics", "supply chain", "agriculture", "farming",
            "farmer", "crop", "electricity", "water", "infrastructure", "market",
        ),
    ),
    MockCode(
        "applications-personalisation",
        "Services are tailored to each individual from that person's own data.",
        (
            "personalis", "personaliz", "personal assistant", "tailored", "customis",
            "customiz", "recommend", "your own data", "your news", "your shopping",
            "suited to", "individual need",
        ),
    ),
    MockCode(
        "negative_impacts-surveillance",
        "Data gathered by AI systems exposes people to monitoring or misuse.",
        (
            "privacy", "surveillance", "monitor", "tracked", "tracking", "watching us",
            "misuse", "personal data", "picture of your life", "hacked", "leak",
            "spy", "consent",
        ),
    ),
    MockCode(
        "negative_impacts-dependence",
        "People lose the ability, or the habit, of working without the system.",
        (
            "depend", "rely", "reliance", "hand over", "handed over", "addicted",
            "lazy", "forget", "remember how", "without the system", "take over",
            "goes down", "helpless",
        ),
    ),
    MockCode(
        "negative_impacts-inequality",
        "The gains and the losses from AI fall unevenly across groups.",
        (
            "inequality", "unequal", "divide", "gap between", "the poor", "the rich",
            "wealthy", "disparity", "left behind", "cannot afford", "privileged",
        ),
    ),
    MockCode(
        "negative_impacts-bias",
        "AI reproduces the biases already present in the data it is given.",
        ("bias", "discriminat", "unfair", "prejudice", "stereotype", "one sided"),
    ),
    MockCode(
        "governance-responsible_development",
        "AI needs deliberate rules, ethics or oversight if it is to be used well.",
        (
            "responsible", "responsibl", "responsibility", "regulat", "govern",
            "policy", "policies", "ethic", "oversight", "accountab", "guideline",
            "carefully", "be careful", "crucial to ensure", "who controls",
        ),
    ),
    MockCode(
        "positive_impacts-job_creation",
        "New categories of paid work appear alongside the ones AI removes.",
        (
            "new job", "new roles", "new career", "new industries", "jobs will be created",
            "will be generated", "opportunit", "created in maintaining", "new areas",
        ),
    ),
    MockCode(
        "positive_impacts-problem_solving",
        "AI solves problems respondents believe people cannot solve alone.",
        (
            "solve", "solution", "problem", "efficien", "faster", "accurate",
            "optimis", "improve", "better than", "effective", "in advance",
            "before anything fails",
        ),
    ),
    MockCode(
        "positive_impacts-quality_of_life",
        "Everyday life becomes easier, safer or more comfortable.",
        (
            "quality of life", "comfortable", "convenien", "easier", "standard of living",
            "well being", "wellbeing", "happier", "safer", "save time", "leisure",
            "genuine improvement",
        ),
    ),
    MockCode(
        "positive_impacts-access",
        "AI extends services to people who cannot reach them today.",
        (
            "access", "reach", "village", "rural", "remote area", "available to",
            "affordable", "benefit the most", "everyone will have", "no specialist",
        ),
    ),
    MockCode(
        "adoption-everyday_life",
        "AI becomes an unremarkable part of ordinary daily life.",
        (
            "everyday", "every day", "daily", "ordinary life", "household", "at home",
            "everywhere", "part of life", "routine", "every office", "every home",
            "common", "part of ordinary",
        ),
    ),
    MockCode(
        "future-superintelligence",
        "AI's capability comes to exceed human capability in general.",
        (
            "superintelligence", "super intelligence", "smarter than", "more intelligent",
            "beyond human", "far ahead", "powerful", "capable of", "do almost everything",
            "conscious", "sentient", "general intelligence", "take charge",
        ),
    ),
    MockCode(
        "future-inevitability",
        "AI's arrival is treated as unavoidable rather than as chosen.",
        (
            "inevitab", "unavoidab", "certainly", "definitely", "bound to", "no choice",
            "cannot stop", "without doubt", "day by day", "getting better",
        ),
    ),
    MockCode(
        "future-uncertainty",
        "What AI will do next is treated as genuinely unknown.",
        (
            "uncertain", "hard to say", "hard to guess", "difficult to predict",
            "cannot imagine", "unknown", "who knows", "perhaps", "worry", "worries",
            "worried", "fear", "afraid", "transition", "not the destination",
        ),
    ),
)

#: Used when a segment matches nothing in the table. Both are honest, contentful codes
#: — the point of the fallback is that an unmatched phrase still gets coded, which is
#: what a human coder would do, rather than being silently dropped.
FALLBACK_CODES: tuple[MockCode, ...] = (
    MockCode(
        "future-imagined_scenario",
        "The respondent sketches a specific scenario for the years up to 2050.",
        (),
    ),
    MockCode(
        "adoption-social_change",
        "AI is expected to reshape how society at large operates.",
        (),
    ),
)

_NON_WORD_RE = re.compile(r"[^a-z0-9]+")


def _match_text(segment: str) -> str:
    """Casefolded, punctuation-flattened form used only for keyword lookup.

    Never used to compute a span: `gaf.textnorm.normalise` owns offsets, and this form
    is not offset-compatible with it.
    """
    return f" {_NON_WORD_RE.sub(' ', segment.casefold()).strip()} "


def _rank_codes(segment: str) -> list[MockCode]:
    """Table rows that match `segment`, best first; table order breaks ties."""
    haystack = _match_text(segment)
    scored = [
        (-hits, index, code)
        for index, code in enumerate(KEYWORD_TABLE)
        if (hits := code.score(haystack)) > 0
    ]
    scored.sort(key=lambda row: (row[0], row[1]))
    return [code for _, _, code in scored]


def _fallback_code(segment: str, persona: str) -> MockCode:
    return FALLBACK_CODES[_digest(segment, persona) % len(FALLBACK_CODES)]


# --------------------------------------------------------------------------- #
# The public helper the orchestrator drives directly
# --------------------------------------------------------------------------- #


def mock_candidates_for(
    text: str,
    response_id: int,
    persona: str,
    *,
    max_quote_words: int = _RULES.max_quote_words,
    max_candidates: int = _MAX_CANDIDATES,
) -> list[dict[str, Any]]:
    """Candidate objects derived from `text`, as a coder would emit them.

    Public because the coder agent's prompt templates are a later wave: this is how the
    pipeline can be demonstrated on real input today, without a template and without a
    key. Each object parses through `gaf.models.Candidate.from_json`.

    The two personas mostly agree. Persona B differs in two documented ways, both
    keyed on a blake2b digest so they are stable across processes:

    1. on roughly one segment in three it prefers the runner-up code rather than the
       best-scoring one, which is the ordinary "two readers, one text" divergence the
       cross-coder check exists to measure;
    2. on roughly one response in five it adds a candidate citing `FABRICATED_QUOTE`,
       which occurs in no response — so the S2 provenance-drop path is exercised on any
       corpus, not only on a fixture with a quote planted in it.

    Codes are emitted at most `max_candidates` at a time, keeping a response inside the
    PI's "usually between 2 and 12". A response with only one quotable phrase yields one
    candidate: padding a 28-word answer out to a quota would manufacture evidence, and
    S5's `too_few_codes` warning is the correct, visible outcome.
    """
    if persona not in PERSONAS:
        raise ValueError(f"unknown persona {persona!r}; expected one of {PERSONAS}")

    segments = split_segments(text, max_words=max_quote_words)
    grouped: dict[str, tuple[MockCode, list[str]]] = {}
    for index, segment in enumerate(segments):
        ranked = _rank_codes(segment)
        if not ranked:
            chosen = _fallback_code(segment, persona)
        elif (
            persona == "B"
            and len(ranked) > 1
            and _digest(segment, persona, str(index)) % _B_DIVERGENCE_MODULUS == 0
        ):
            chosen = ranked[1]
        else:
            chosen = ranked[0]
        grouped.setdefault(chosen.name, (chosen, []))[1].append(segment)

    # Two codes on one response is the PI's usual minimum; supply a second only when
    # there is a second phrase to attach it to.
    if len(grouped) == 1 and len(segments) > 1:
        spare = next(c for c in FALLBACK_CODES if c.name not in grouped)
        orphan = segments[-1]
        name, (code, quotes) = next(iter(grouped.items()))
        if len(quotes) > 1:
            grouped[name] = (code, [q for q in quotes if q != orphan] or quotes)
            grouped[spare.name] = (spare, [orphan])

    ordered = sorted(grouped.values(), key=lambda item: (-len(item[1]), item[0].name))
    candidates = [
        {
            "name": code.name,
            "description": code.description,
            "evidence": [{"response_id": response_id, "quote": quote} for quote in quotes],
            "parent_hint": family_of(code.name),
        }
        for code, quotes in ordered[:max_candidates]
    ]

    if (
        persona == "B"
        and segments
        and _digest(text, persona, str(response_id)) % _B_FABRICATION_MODULUS == 0
    ):
        candidates.append(
            {
                "name": "future-superintelligence",
                "description": "AI's capability comes to exceed human capability in general.",
                "evidence": [{"response_id": response_id, "quote": FABRICATED_QUOTE}],
                "parent_hint": "future",
            }
        )
    return candidates


# --------------------------------------------------------------------------- #
# Prompt-shape helpers
# --------------------------------------------------------------------------- #

_RESPONSE_BLOCK_RE = re.compile(r"<response[^>]*>(.*?)</response>", re.DOTALL | re.IGNORECASE)
_INT_RE = re.compile(r"-?\d+")
_JSON_ID_RE = re.compile(r'"id"\s*:\s*"([^"]+)"')
_SLUG_ID_RE = re.compile(r"\bc-[A-Za-z0-9_][A-Za-z0-9_-]*")


def extract_response_text(user: str) -> str:
    """The response body inside a prompt.

    Prompt templates are a later wave, so the convention is stated here and is
    deliberately forgiving: a ``<response>...</response>`` block is used when present,
    and otherwise the whole user message is treated as the text. Either way the mock
    codes real words rather than requiring a template that does not exist yet.
    """
    match = _RESPONSE_BLOCK_RE.search(user)
    return match.group(1) if match else user


def extract_response_id(subject: str) -> int:
    """The response id `LLMRequest.subject` names; 0 when it names no integer."""
    match = _INT_RE.search(subject)
    return int(match.group(0)) if match else 0


def extract_code_ids(text: str) -> list[str]:
    """Code ids visible in a prompt, in order of first appearance, de-duplicated.

    Two documented patterns: a JSON ``"id": "..."`` field (the shape of
    `Codebook.to_json_str`, which is what a refactor prompt carries) and, failing that,
    a bare ``c-...`` slug in prose.
    """
    found = _JSON_ID_RE.findall(text) or _SLUG_ID_RE.findall(text)
    seen: dict[str, None] = {}
    for identifier in found:
        seen.setdefault(identifier, None)
    return list(seen)


# --------------------------------------------------------------------------- #
# Clients
# --------------------------------------------------------------------------- #


class _MockClient:
    """Shared result assembly. Every mock is a pure function of its request."""

    spec: ModelSpec

    def _result(
        self,
        request: LLMRequest,
        data: dict[str, Any],
        *,
        fail_safe: bool = False,
    ) -> LLMResult:
        raw_text = json.dumps(data, sort_keys=True, ensure_ascii=False)
        input_tokens = _token_estimate(request.system) + _token_estimate(request.user)
        output_tokens = _token_estimate(raw_text)
        return LLMResult(
            data=data,
            task=request.task,
            provider=self.spec.provider,
            model=self.spec.model,
            prompt_version=request.prompt_version,
            raw_text=raw_text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=self.spec.cost_usd(input_tokens, output_tokens),
            # No wall clock: an offline call spends no time talking to a model, and a
            # measured duration would make two runs of `make demo` differ.
            latency_ms=0.0,
            cache_hit=False,
            fail_safe=fail_safe,
            attempts=1,
        )

    def _wrong_task(self, request: LLMRequest) -> LLMResult:
        """A role asked for a task it does not answer degrades, it does not raise."""
        return self._result(request, fail_safe_for(request.task), fail_safe=True)


class MockCoderClient(_MockClient):
    """A coder persona. Same request, same candidates — across runs and processes."""

    def __init__(
        self,
        spec: ModelSpec | None = None,
        *,
        persona: str | None = None,
        rules: CodingRules | None = None,
    ) -> None:
        self.spec = spec or MOCK_REGISTRY.coder_a
        self.rules = rules or _RULES
        resolved = persona or ("B" if self.spec.role == "coder_b" else "A")
        if resolved not in PERSONAS:
            raise ValueError(f"unknown persona {resolved!r}; expected one of {PERSONAS}")
        self.persona = resolved

    def complete_json(self, request: LLMRequest) -> LLMResult:
        if request.task is not TaskType.CODE:
            return self._wrong_task(request)
        candidates = mock_candidates_for(
            extract_response_text(request.user),
            extract_response_id(request.subject),
            self.persona,
            max_quote_words=self.rules.max_quote_words,
        )
        return self._result(request, {"candidates": candidates})


class MockJudgeClient(_MockClient):
    """The frontier judge, offline. Dispatches on `LLMRequest.task`.

    * `JUDGE_FIT` — UNNECESSARY exactly when the prompt carries `MOCKFIT_UNNECESSARY`,
      otherwise APPLIES. Verdicts come from `gaf.checks.contracts.FIT_VERDICTS`.
    * `JUDGE_DISPUTE` — KEEP unless `MOCKDISPUTE_DROP` is present or the content digest
      lands on one branch in eight. Biased to KEEP by construction: the fast loop must
      not lose data to a mock.
    * `JUDGE_ROUTE` — MERGE when `MOCKROUTE_MERGE` is present or the digest lands on one
      branch in three, otherwise CREATE.
    """

    def __init__(self, spec: ModelSpec | None = None) -> None:
        self.spec = spec or MOCK_REGISTRY.judge

    def complete_json(self, request: LLMRequest) -> LLMResult:
        if request.task is TaskType.JUDGE_FIT:
            return self._result(request, self._fit(request))
        if request.task is TaskType.JUDGE_DISPUTE:
            return self._result(request, self._dispute(request))
        if request.task is TaskType.JUDGE_ROUTE:
            return self._result(request, self._route(request))
        return self._wrong_task(request)

    @staticmethod
    def _fit(request: LLMRequest) -> dict[str, Any]:
        unnecessary = MOCKFIT_UNNECESSARY in request.user
        verdict = validate_enum(
            "UNNECESSARY" if unnecessary else "APPLIES", FIT_VERDICTS, "APPLIES"
        )
        reason = (
            "the sentinel marks this segment as one the code did not have to be applied to"
            if unnecessary
            else "the quoted segment carries the meaning the code names"
        )
        return {"verdict": verdict, "reasoning": reason}

    @staticmethod
    def _dispute(request: LLMRequest) -> dict[str, Any]:
        drop = (
            MOCKDISPUTE_DROP in request.user
            or _digest(request.subject, request.user) % _DISPUTE_DROP_MODULUS == 0
        )
        verdict = validate_enum("DROP" if drop else "KEEP", DISPUTE_VERDICTS, "KEEP")
        reason = (
            "the disputed candidate adds nothing the other coder did not already capture"
            if drop
            else "both readings are defensible, so the candidate is kept and flagged"
        )
        return {"verdict": verdict, "reasoning": reason}

    @staticmethod
    def _route(request: LLMRequest) -> dict[str, Any]:
        merge = (
            MOCKROUTE_MERGE in request.user
            or _digest(request.subject, request.user) % _ROUTE_MERGE_MODULUS == 0
        )
        route = validate_enum("MERGE" if merge else "CREATE", ROUTE_VERDICTS, "CREATE")
        reason = (
            "the candidate restates an existing code rather than adding a distinction"
            if merge
            else "the candidate names a distinction the codebook does not yet carry"
        )
        return {"route": route, "reasoning": reason}


class MockRefactorerClient(_MockClient):
    """The slow-loop refactorer, offline.

    Targets are the code ids visible in the request, so the script applies to whatever
    codebook was actually put in front of it. The proposals are **structurally valid and
    semantically arbitrary** by design: the mock exists to exercise edit-script
    validation, the diff and the human gate, not to produce a good refactor. It always
    includes a `split` and a `reparent` when the request shows at least one code —
    those two operations exist because the predecessor's narrow set (create / merge /
    rename / no-op) is the documented cause of codebook flattening.
    """

    def __init__(self, spec: ModelSpec | None = None) -> None:
        self.spec = spec or MOCK_REGISTRY.refactorer

    def complete_json(self, request: LLMRequest) -> LLMResult:
        if request.task is not TaskType.REFACTOR:
            return self._wrong_task(request)
        data: dict[str, Any] = {
            "operations": self._operations(request),
            "reasoning": (
                "one overloaded code separated, one code moved under a better parent, "
                "and the rest of the codebook left alone"
            ),
        }
        return self._result(request, data)

    @staticmethod
    def _operations(request: LLMRequest) -> list[dict[str, Any]]:
        ids = extract_code_ids(request.user)
        if not ids:
            # An edit script with nothing to edit is a no-op, not an invented target.
            return [
                {
                    "type": "noop",
                    "targets": [],
                    "payload": {},
                    "rationale": "the request names no codes, so there is nothing to restructure",
                }
            ]
        pivot = _digest(request.subject, *ids) % len(ids)
        split_target = ids[pivot]
        moved = ids[(pivot + 1) % len(ids)]
        new_parent: str | None = ids[(pivot + 2) % len(ids)] if len(ids) > 2 else None
        if new_parent == moved:
            new_parent = None
        base = split_target.removeprefix("c-") or split_target
        return [
            {
                "type": "split",
                "targets": [split_target],
                "payload": {
                    "into": [
                        {
                            "name": f"{base}_a",
                            "description": "First strand of an overloaded code, separated for review.",
                        },
                        {
                            "name": f"{base}_b",
                            "description": "Second strand of an overloaded code, separated for review.",
                        },
                    ]
                },
                "rationale": "the code carries two distinguishable strands of evidence",
            },
            {
                "type": "reparent",
                "targets": [moved],
                "payload": {"new_parent_id": new_parent},
                "rationale": (
                    "the code sits under a family that does not describe it"
                    if new_parent
                    else "the code is a family in its own right and is promoted to the top level"
                ),
            },
            {
                "type": "noop",
                "targets": [],
                "payload": {},
                "rationale": "the remainder of the codebook needs no change at this checkpoint",
            },
        ]
