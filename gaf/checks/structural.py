"""Structural checks S1-S6: schema, provenance, name grammar, segments, counts.

Two entry points, both pure functions of ``(candidates, source text, rules, codebook
state)``:

* :func:`check_candidates` — the per-response candidate gate. S1 and S2 *drop*;
  S2b, S3, S4 and S5 *flag*. Surviving candidates are new objects built with
  ``dataclasses.replace``; nothing is ever mutated in place, which is why the types in
  :mod:`gaf.models` are frozen — a mutation is an error, not a broken convention.
* :func:`check_codebook` — the whole-codebook invariants (S6).

This suite is this pipeline's implementation of the **concurrent validation** step of
the Alqazlan et al. HITL computational grounded theory framework: validation folded
into the analysis as a practice, not bolted on afterwards as correction. Every rule
enforced here is quoted verbatim in ``docs/CODING_RULES.md`` from the PI's own coding
instructions, together with its severity and the reason for it. Severity follows his
modality: rules he states as absolutes are ERRORs, rules he hedges ("usually") are
WARNs, and grammar — where his own codes are inconsistent — is never worse than WARN.

Deterministic and offline: no randomness, no I/O, no embeddings, no model call, and
nothing beyond the standard library. Findings are emitted in a fixed order (S1, S2,
S2b, S3, S4, S5; candidates in input order, evidence in quote order), so two runs over
identical input produce byte-identical reports.

**A checker reports; the router and the audit log decide and record.** Nothing here
writes to the store, edits the codebook or calls the router.

Validation principles: **reliability** — every violation is a replayable fact derived
from the normalised source text alone; and **transparency** — each finding carries a
check id, a severity, a subject and machine-readable ``data``, so a methods reviewer
can audit a run row by row instead of reading prose.
"""

from __future__ import annotations

import difflib
import re
from collections.abc import Iterable, Sequence
from dataclasses import replace

from gaf.checks.contracts import CheckReport, Severity
from gaf.config import CodingRules
from gaf.models import Candidate, Code, Codebook, Evidence, Response, family_of, split_name
from gaf.textnorm import normalise, normalise_for_match

__all__ = [
    "MARKER_KEY",
    "NAME_PART_RE",
    "check_candidates",
    "check_codebook",
    "check_s1",
    "check_s2",
    "check_s2b",
    "check_s3",
    "check_s4",
    "check_s5",
    "locate_quote",
]

#: The key under which every finding records its machine-readable sub-kind, e.g.
#: ``data["marker"] == "sub_code_first"``. One stable key means a consumer can switch
#: on the sub-kind without parsing a message.
MARKER_KEY = "marker"

#: S3 name grammar, applied to each hyphen-split part **after lowercasing**. The PI's
#: own codes are capitalised inconsistently (``AI-superintelligence``) and one of his
#: sub-codes contains a hyphen (``positive_impacts-problem-solving``), which is why the
#: pattern never sees case, why the split is on the first hyphen only, and why every
#: S3 finding is a WARN rather than an ERROR.
NAME_PART_RE = re.compile(r"^[a-z0-9]+([_-][a-z0-9]+)*$")

_WORD_RE = re.compile(r"\S+")
_SENTENCE_END_RE = re.compile(r"[.?!]+")
_WHITESPACE_RE = re.compile(r"\s")

#: Longest excerpt used in a subject or a message; full text always goes into ``data``.
_EXCERPT_CHARS = 120


# --------------------------------------------------------------------------- #
# Small shared helpers
# --------------------------------------------------------------------------- #


def _resolve(rules: CodingRules | None) -> CodingRules:
    """Every threshold is a named field of `CodingRules`; none is written inline."""
    return CodingRules() if rules is None else rules


def _subject(candidate: Candidate, index: int) -> str:
    """A candidate's finding subject: its name, or a positional stand-in if it has none."""
    return candidate.name.strip() or f"<unnamed candidate {index}>"


def _excerpt(text: str) -> str:
    """Shorten text for a *subject* or a *message* only.

    Never use this on a value going into a finding's ``data`` payload: the audit log is
    the record a methods reviewer replays from, and a truncated quote cannot be located
    in the source. Subjects and messages are for human reading; ``data`` is the record.
    """
    return text if len(text) <= _EXCERPT_CHARS else text[: _EXCERPT_CHARS - 3] + "..."


def _grammar_reasons(name: str) -> list[str]:
    """Why `name` fails the S3 grammar, or an empty list if it does not.

    ``"whitespace"``   — the name contains a space, tab or newline.
    ``"part_pattern"`` — a part, lowercased, does not match :data:`NAME_PART_RE`.
    """
    reasons: list[str] = []
    if _WHITESPACE_RE.search(name):
        reasons.append("whitespace")
    top, sub = split_name(name)
    parts = [top, sub] if "-" in name else [top]
    if any(NAME_PART_RE.match(part.lower()) is None for part in parts):
        reasons.append("part_pattern")
    return reasons


def _sentence_count(quote: str) -> int:
    """Sentences in `quote`, counted by runs of ``.?!``, never less than one.

    An unpunctuated quote is therefore one sentence however long it is, which is
    exactly why S2b also bounds a quote by word count — see :func:`check_s2b` and
    ADR-0015.
    """
    return max(1, len(_SENTENCE_END_RE.findall(normalise(quote))))


def _word_count(quote: str) -> int:
    """Words in `quote`, counted on the normalised form (whitespace already collapsed)."""
    return len(_WORD_RE.findall(normalise(quote)))


# --------------------------------------------------------------------------- #
# S2 — the quote locator
# --------------------------------------------------------------------------- #


def _word_spans(text: str) -> list[tuple[int, int]]:
    return [(m.start(), m.end()) for m in _WORD_RE.finditer(text)]


def _candidate_windows(word_spans: Sequence[tuple[int, int]], word_count: int) -> list[tuple[int, int]]:
    """Character spans of every word-aligned window worth scoring, in a fixed order.

    Windows are one word shorter, the same length as, and one word longer than the
    quote, which is enough slack for a dropped or inserted word. Enumerated by start
    position and then by length, so ties in similarity resolve to the earliest and
    shortest window and the locator is order-independent.
    """
    total = len(word_spans)
    lengths = sorted({n for n in (word_count - 1, word_count, word_count + 1) if n >= 1})
    seen: set[tuple[int, int]] = set()
    windows: list[tuple[int, int]] = []
    for start in range(total):
        for length in lengths:
            stop = min(start + length, total)
            if stop <= start or (start, stop) in seen:
                continue
            seen.add((start, stop))
            windows.append((word_spans[start][0], word_spans[stop - 1][1]))
    return windows


def locate_quote(
    quote: str, normalised_text: str, threshold: float
) -> tuple[bool, float, tuple[int, int] | None]:
    """Locate `quote` in `normalised_text`, exactly or fuzzily.

    Returns ``(found, score, span)``. **The span indexes the normalised text**, never
    the raw source: see :mod:`gaf.textnorm`, which is the single function every
    character offset in this project is defined against. S4 clusters on these spans, so
    this locator is the one check the others build on.

    The quote is normalised before matching, so a coder that re-typed a curly quote or
    collapsed a line break still matches exactly. Failing an exact match, word-aligned
    windows around the quote's own length are scored with
    :class:`difflib.SequenceMatcher` and the best-scoring window wins if it reaches
    `threshold` (``CodingRules.fuzzy_threshold``). ``score`` is the best similarity
    seen either way — reported even when the quote is *not* found, because "0.31
    against anything in the response" is what makes a fabricated quote legible in the
    audit log. ``span`` is ``None`` exactly when ``found`` is ``False``.

    Deterministic: the window enumeration is fixed and ties keep the earliest window.
    """
    needle = normalise(quote)
    if not needle or not normalised_text:
        return False, 0.0, None

    exact = normalised_text.find(needle)
    if exact >= 0:
        return True, 1.0, (exact, exact + len(needle))

    word_spans = _word_spans(normalised_text)
    if not word_spans:
        return False, 0.0, None

    # `b` is the needle and is set once: SequenceMatcher caches its index of `b`, so
    # varying only `a` keeps the sweep to one pass per window. autojunk would treat
    # frequent characters as noise on any text over 200 characters, which is exactly
    # wrong for character-level matching.
    matcher = difflib.SequenceMatcher(None, "", needle, autojunk=False)
    best_score = 0.0
    best_span: tuple[int, int] | None = None
    for start, stop in _candidate_windows(word_spans, len(needle.split(" "))):
        matcher.set_seq1(normalised_text[start:stop])
        # Both quick ratios are upper bounds on the real one, so pruning against the
        # best score so far still yields the exact maximum.
        if matcher.real_quick_ratio() <= best_score or matcher.quick_ratio() <= best_score:
            continue
        score = matcher.ratio()
        if score > best_score:
            best_score = score
            best_span = (start, stop)

    if best_span is not None and best_score >= threshold:
        return True, best_score, best_span
    return False, best_score, None


# --------------------------------------------------------------------------- #
# S1 — schema
# --------------------------------------------------------------------------- #


def _description_copies_quote(candidate: Candidate) -> str | None:
    """The candidate's own quote that its description copies verbatim, if any."""
    description = normalise_for_match(candidate.description)
    if not description:
        return None
    for evidence in candidate.evidence:
        if normalise_for_match(evidence.quote) == description:
            return evidence.quote
    return None


def check_s1(
    candidates: Sequence[Candidate], rules: CodingRules | None = None
) -> tuple[list[Candidate], CheckReport]:
    """S1 — schema: a name, evidence, and a description that explains something.

    A missing name or missing evidence is ERROR and drops the candidate: neither can be
    repaired downstream, and a code with no quote cannot be traced to the corpus. A
    missing description is WARN and keeps it — the embedder falls back to the name, and
    a human can supply the sentence at the gate. A description that is a verbatim copy
    of one of the candidate's own quotes is also WARN (ADR-0013): a present description
    is not a *missing* one, and dropping would destroy evidence over a formatting
    complaint.
    """
    rules = _resolve(rules)
    report = CheckReport()
    kept: list[Candidate] = []
    for index, candidate in enumerate(candidates):
        subject = _subject(candidate, index)
        invalid = False
        if not candidate.name.strip():
            report.add(
                "S1",
                Severity.ERROR,
                "candidate",
                subject,
                "Candidate has no name, so there is nothing to admit to the codebook.",
                **{MARKER_KEY: "missing_name"},
                index=index,
            )
            invalid = True
        if not candidate.evidence:
            report.add(
                "S1",
                Severity.ERROR,
                "candidate",
                subject,
                "Candidate cites no evidence, so it cannot be traced back to the corpus.",
                **{MARKER_KEY: "missing_evidence"},
            )
            invalid = True
        if invalid:
            continue
        if rules.require_description and not candidate.description.strip():
            report.add(
                "S1",
                Severity.WARN,
                "candidate",
                subject,
                "Candidate has no description; the embedder falls back to its name.",
                **{MARKER_KEY: "missing_description"},
            )
        else:
            copied = _description_copies_quote(candidate)
            if copied is not None:
                report.add(
                    "S1",
                    Severity.WARN,
                    "candidate",
                    subject,
                    "Description is a verbatim copy of the candidate's own quote, so it "
                    "explains nothing about the segment.",
                    **{MARKER_KEY: "description_copies_quote"},
                    quote=copied,
                )
        kept.append(candidate)
    return kept, report


# --------------------------------------------------------------------------- #
# S2 / S2b — evidence provenance, spans, and quote length
# --------------------------------------------------------------------------- #


def check_s2(
    candidates: Sequence[Candidate],
    response: Response,
    rules: CodingRules | None = None,
) -> tuple[list[Candidate], CheckReport]:
    """S2 — provenance: every quote must be locatable in the response.

    An unlocatable quote is INFO and is dropped from the candidate's evidence; a
    candidate left with no verified quote at all is ERROR and is dropped, because a
    code with no traceable evidence is exactly the hallucination this layer exists to
    catch. Surviving candidates are rebuilt with ``dataclasses.replace`` and their
    evidence carries ``verified=True``, the match ``score`` and the ``span``.

    Quotes are located against ``normalise(response.content)`` regardless of the
    ``response_id`` they claim, so a quote attributed to the wrong response simply
    fails to verify here rather than being silently trusted.
    """
    rules = _resolve(rules)
    text = normalise(response.content)
    report = CheckReport()
    kept: list[Candidate] = []
    for index, candidate in enumerate(candidates):
        subject = _subject(candidate, index)
        verified: list[Evidence] = []
        for evidence in candidate.evidence:
            found, score, span = locate_quote(evidence.quote, text, rules.fuzzy_threshold)
            if found and span is not None:
                verified.append(replace(evidence, verified=True, score=score, span=span))
                continue
            report.add(
                "S2",
                Severity.INFO,
                "candidate",
                subject,
                "Quote could not be located in the response and has been dropped from "
                "the candidate's evidence.",
                **{MARKER_KEY: "quote_unverified"},
                quote=evidence.quote,
                score=round(score, 4),
                threshold=rules.fuzzy_threshold,
                response_id=response.id,
            )
        if not verified:
            report.add(
                "S2",
                Severity.ERROR,
                "candidate",
                subject,
                "No quote could be verified against the response, so the candidate has "
                "no evidence left to stand on.",
                **{MARKER_KEY: "no_verified_evidence"},
                response_id=response.id,
                quotes=[e.quote for e in candidate.evidence],
            )
            continue
        kept.append(replace(candidate, evidence=verified))
    return kept, report


def check_s2b(
    candidates: Sequence[Candidate], rules: CodingRules | None = None
) -> CheckReport:
    """S2b — "Coding is applied on the level of phrase or sentence."

    Two independent conditions, either of which is a WARN on its own:

    1. more than ``rules.max_quote_sentences`` sentence terminators — marker
       ``quote_too_long``;
    2. more than ``rules.max_quote_words`` words — marker ``quote_too_long_words``.

    The word bound is not a second rule but the same rule made enforceable on text that
    lacks the punctuation the terminator count relies on: three of the twenty responses
    in the real seed sample contain no ``.``, ``?`` or ``!`` at all, so a quote of such
    a response *in full* counts as one sentence and would otherwise pass clean
    (ADR-0015). Nothing here assumes a response is punctuated.

    Never a drop — the quote is real, only over-long. The coder has quoted a paragraph
    where it should have quoted a clause, which blurs the segment S4 reasons about and
    weakens the audit trail.
    """
    rules = _resolve(rules)
    report = CheckReport()
    for index, candidate in enumerate(candidates):
        subject = _subject(candidate, index)
        for evidence in candidate.evidence:
            if not evidence.verified:
                continue
            sentences = _sentence_count(evidence.quote)
            words = _word_count(evidence.quote)
            if sentences > rules.max_quote_sentences:
                report.add(
                    "S2b",
                    Severity.WARN,
                    "candidate",
                    subject,
                    f"Quote spans {sentences} sentences; coding should be applied at the "
                    f"level of phrase or sentence (at most {rules.max_quote_sentences}).",
                    **{MARKER_KEY: "quote_too_long"},
                    sentences=sentences,
                    max_quote_sentences=rules.max_quote_sentences,
                    words=words,
                    quote=evidence.quote,
                )
            if words > rules.max_quote_words:
                report.add(
                    "S2b",
                    Severity.WARN,
                    "candidate",
                    subject,
                    f"Quote runs to {words} words; coding should be applied at the level "
                    f"of phrase or sentence (at most {rules.max_quote_words} words).",
                    **{MARKER_KEY: "quote_too_long_words"},
                    words=words,
                    max_quote_words=rules.max_quote_words,
                    sentences=sentences,
                    quote=evidence.quote,
                )
    return report


# --------------------------------------------------------------------------- #
# S3 — name grammar and hierarchy discipline
# --------------------------------------------------------------------------- #


def _families(existing_names: Iterable[str]) -> dict[str, list[str]]:
    """Case-folded top-level family -> the existing names in it, sorted."""
    grouped: dict[str, list[str]] = {}
    for name in existing_names:
        grouped.setdefault(family_of(name).strip().casefold(), []).append(name)
    return {family: sorted(names) for family, names in grouped.items()}


def check_s3(
    candidates: Sequence[Candidate],
    existing_names: Sequence[str] = (),
    rules: CodingRules | None = None,
) -> CheckReport:
    """S3 — name grammar (``toplevel-sub_level``) and sub-code-first discipline.

    Names split on the **first** hyphen only and each part is matched lowercased
    against :data:`NAME_PART_RE`, so ``AI-superintelligence`` and
    ``positive_impacts-problem-solving`` — both of them the PI's own — pass. Every
    finding here is a WARN, never an ERROR, precisely because his naming is not
    internally consistent and a check may not be stricter than the codebook it audits.

    ``sub_code_first`` fires when a bare top-level candidate is proposed while the
    codebook already holds that family. It is one of the PI's explicit negative-example
    categories: "You created a code when you could have used a sub-code for an existing
    code."
    """
    rules = _resolve(rules)
    report = CheckReport()
    families = _families(existing_names)
    for index, candidate in enumerate(candidates):
        subject = _subject(candidate, index)
        name = candidate.name
        if rules.check_name_grammar:
            reasons = _grammar_reasons(name)
            if reasons:
                report.add(
                    "S3",
                    Severity.WARN,
                    "candidate",
                    subject,
                    f"Code name {name!r} does not follow the toplevel-sub_level grammar "
                    f"({', '.join(reasons)}).",
                    **{MARKER_KEY: "name_grammar"},
                    name=name,
                    reasons=reasons,
                    pattern=NAME_PART_RE.pattern,
                )
        if rules.prefer_subcode_first and "-" not in name:
            siblings = families.get(name.strip().casefold(), [])
            if siblings:
                report.add(
                    "S3",
                    Severity.WARN,
                    "candidate",
                    subject,
                    f"The family {name!r} already exists in the codebook; consider a "
                    "sub-code of it before adding another top-level code.",
                    **{MARKER_KEY: "sub_code_first"},
                    family=name,
                    existing=siblings,
                )
    return report


# --------------------------------------------------------------------------- #
# S4 — segment discipline
# --------------------------------------------------------------------------- #


def _interval_jaccard(a: tuple[int, int], b: tuple[int, int]) -> float:
    """Jaccard similarity of two half-open character intervals.

    For spans ``[a0, a1)`` and ``[b0, b1)``::

        intersection = max(0, min(a1, b1) - max(a0, b0))
        union        = (a1 - a0) + (b1 - b0) - intersection
        J            = intersection / union

    That is: **overlapping length over combined length**. Identical spans score 1.0,
    disjoint spans 0.0, and a span wholly inside one twice its size scores 0.5 — which
    is why ``segment_overlap_threshold`` sits at 0.5. Zero-length intervals score 0.0.
    """
    intersection = min(a[1], b[1]) - max(a[0], b[0])
    if intersection <= 0:
        return 0.0
    union = (a[1] - a[0]) + (b[1] - b[0]) - intersection
    if union <= 0:
        return 0.0
    return intersection / union


def _find(parent: list[int], node: int) -> int:
    while parent[node] != node:
        parent[node] = parent[parent[node]]
        node = parent[node]
    return node


def _union(parent: list[int], left: int, right: int) -> None:
    left_root, right_root = _find(parent, left), _find(parent, right)
    if left_root != right_root:
        parent[max(left_root, right_root)] = min(left_root, right_root)


def check_s4(
    candidates: Sequence[Candidate],
    response: Response,
    rules: CodingRules | None = None,
) -> CheckReport:
    """S4 — "The same piece of text can be coded with a maximum of two codes."

    Verified quotes are clustered by character-interval Jaccard (see
    :func:`_interval_jaccard`) at ``rules.segment_overlap_threshold`` using union-find,
    so a chain of mutually overlapping quotes forms one segment. A cluster carrying
    more than ``rules.max_codes_per_segment`` distinct candidate names is an ERROR —
    the one count the PI states as an absolute.

    **Resolution policy: keep-and-flag.** Choosing which of three codes to drop is a
    judgment about meaning, and the structural layer does not make meaning judgments.
    Every involved candidate survives; the finding names all of them, goes to the audit
    log for the human gate, and drives the CLI exit code. Nothing is dropped silently.
    """
    rules = _resolve(rules)
    text = normalise(response.content)
    report = CheckReport()

    names: list[str] = []
    spans: list[tuple[int, int]] = []
    quotes: list[str] = []
    for index, candidate in enumerate(candidates):
        for evidence in candidate.evidence:
            if not evidence.verified or evidence.span is None:
                continue
            names.append(_subject(candidate, index))
            spans.append(evidence.span)
            quotes.append(evidence.quote)

    parent = list(range(len(spans)))
    for i in range(len(spans)):
        for j in range(i + 1, len(spans)):
            if _interval_jaccard(spans[i], spans[j]) >= rules.segment_overlap_threshold:
                _union(parent, i, j)

    # Insertion order is ascending first member, so cluster order is fixed by input order.
    clusters: dict[int, list[int]] = {}
    for i in range(len(spans)):
        clusters.setdefault(_find(parent, i), []).append(i)

    for members in clusters.values():
        attached = sorted({names[i] for i in members})
        if len(attached) <= rules.max_codes_per_segment:
            continue
        start = min(spans[i][0] for i in members)
        stop = max(spans[i][1] for i in members)
        segment_text = text[start:stop]
        report.add(
            "S4",
            Severity.ERROR,
            "segment",
            _excerpt(segment_text),
            f"{len(attached)} distinct codes are attached to one segment "
            f"({', '.join(attached)}); the maximum is {rules.max_codes_per_segment}.",
            **{MARKER_KEY: "too_many_codes_on_segment"},
            codes=attached,
            response_id=response.id,
            span=[start, stop],
            segment_text=segment_text,
            quotes=[quotes[i] for i in members],
            max_codes_per_segment=rules.max_codes_per_segment,
            segment_overlap_threshold=rules.segment_overlap_threshold,
        )
    return report


# --------------------------------------------------------------------------- #
# S5 — response-level counts
# --------------------------------------------------------------------------- #


def check_s5(
    candidates: Sequence[Candidate],
    response: Response,
    rules: CodingRules | None = None,
    coders: Sequence[str] | None = None,
) -> CheckReport:
    """S5 — "One response can correspond to multiple codes: usually between 2 and 12."

    Surviving candidates are counted per coder per response; a count outside
    ``[min_codes_per_response, max_codes_per_response]`` is a WARN marked
    ``too_few_codes`` or ``too_many_codes``. The PI's word is **"usually"**, so this is
    advisory and never causes a drop.

    `coders` names the coders that submitted candidates for this response. Passing it
    keeps a coder whose every candidate was dropped upstream visible as
    ``too_few_codes`` with a count of zero; it defaults to the coders still present.
    """
    rules = _resolve(rules)
    report = CheckReport()
    counts: dict[str, int] = dict.fromkeys(coders or (), 0)
    for candidate in candidates:
        counts[candidate.coder] = counts.get(candidate.coder, 0) + 1

    for coder in sorted(counts):
        count = counts[coder]
        if count < rules.min_codes_per_response:
            marker, phrasing = "too_few_codes", "fewer than the usual"
        elif count > rules.max_codes_per_response:
            marker, phrasing = "too_many_codes", "more than the usual"
        else:
            continue
        report.add(
            "S5",
            Severity.WARN,
            "response",
            str(response.id),
            f"Coder {coder!r} produced {count} codes for this response, {phrasing} "
            f"{rules.min_codes_per_response} to {rules.max_codes_per_response}.",
            **{MARKER_KEY: marker},
            coder=coder,
            count=count,
            min_codes_per_response=rules.min_codes_per_response,
            max_codes_per_response=rules.max_codes_per_response,
        )
    return report


# --------------------------------------------------------------------------- #
# The candidate gate
# --------------------------------------------------------------------------- #


def check_candidates(
    candidates: Sequence[Candidate],
    response: Response,
    existing_names: Sequence[str] = (),
    rules: CodingRules | None = None,
) -> tuple[list[Candidate], CheckReport]:
    """Run the per-response structural gate over one coder batch.

    S1 then S2 drop; S2b, S3, S4 and S5 then flag what survives. Returns the surviving
    candidates — **new objects**, with verified evidence and spans attached — and one
    report holding every finding in a fixed order.

    Nothing here mutates its input, writes to the store or edits the codebook.
    `existing_names` is the codebook state S3 needs and is read only.
    """
    rules = _resolve(rules)
    report = CheckReport()
    coders = sorted({candidate.coder for candidate in candidates})

    survivors, s1_report = check_s1(candidates, rules)
    report.extend(s1_report)

    survivors, s2_report = check_s2(survivors, response, rules)
    report.extend(s2_report)

    report.extend(check_s2b(survivors, rules))
    report.extend(check_s3(survivors, existing_names, rules))
    report.extend(check_s4(survivors, response, rules))
    report.extend(check_s5(survivors, response, rules, coders=coders))
    return survivors, report


# --------------------------------------------------------------------------- #
# S6 — codebook invariants
# --------------------------------------------------------------------------- #


def _chain_depth(codebook: Codebook, code: Code) -> tuple[int, bool]:
    """Depth of `code` in its parent chain, and whether that chain contains a cycle.

    A root is depth 1, its child 2, and so on. A ``parent_id`` naming a code that does
    not exist ends the walk (S6 reports that separately as an orphan parent). The walk
    carries the ids it has already seen, so a cycle terminates it instead of hanging.
    """
    depth = 1
    seen = {code.id}
    current = code
    while current.parent_id:
        parent = codebook.codes.get(current.parent_id)
        if parent is None:
            break
        if parent.id in seen:
            return depth, True
        seen.add(parent.id)
        depth += 1
        current = parent
    return depth, False


def check_codebook(
    codebook: Codebook,
    corpus_response_ids: Iterable[int] | None = None,
    rules: CodingRules | None = None,
) -> CheckReport:
    """S6 — the shape invariants of the codebook as a whole.

    * duplicate names, case-insensitively — **ERROR** (``by_name`` assumes uniqueness)
    * ``parent_id`` naming a code that does not exist — **ERROR**
    * a parent chain deeper than ``rules.hierarchy_depth`` — **WARN** ("a codebook with
      two levels of codes")
    * a parent that carries evidence while having children — **INFO** (evidence belongs
      at the leaves)
    * an empty description, when ``rules.require_description`` — **WARN**
    * evidence naming a response id absent from `corpus_response_ids` — **ERROR**,
      checked only when a corpus id set is supplied
    * a leaf name failing the S3 grammar — **WARN**

    Codes are visited in ``sorted_codes()`` order and duplicate groups in sorted name
    order, so the report is stable across runs. `corpus_response_ids` and the codebook
    are read only.
    """
    rules = _resolve(rules)
    report = CheckReport()
    known_ids = None if corpus_response_ids is None else set(corpus_response_ids)
    codes = codebook.sorted_codes()
    leaf_ids = {code.id for code in codebook.leaves()}

    grouped: dict[str, list[Code]] = {}
    for code in codes:
        grouped.setdefault(code.name.strip().casefold(), []).append(code)
    for key in sorted(grouped):
        group = grouped[key]
        if len(group) < 2:
            continue
        report.add(
            "S6",
            Severity.ERROR,
            "codebook",
            group[0].name,
            f"{len(group)} codes share the name {group[0].name!r} "
            "(case-insensitively), so a name no longer identifies a code.",
            **{MARKER_KEY: "duplicate_name"},
            name=group[0].name,
            names=[code.name for code in group],
            ids=[code.id for code in group],
        )

    for code in codes:
        if code.parent_id and code.parent_id not in codebook.codes:
            report.add(
                "S6",
                Severity.ERROR,
                "codebook",
                code.name,
                f"Parent {code.parent_id!r} does not exist in the codebook.",
                **{MARKER_KEY: "orphan_parent"},
                code_id=code.id,
                parent_id=code.parent_id,
            )

        depth, cyclic = _chain_depth(codebook, code)
        if cyclic:
            report.add(
                "S6",
                Severity.ERROR,
                "codebook",
                code.name,
                "Parent chain forms a cycle, so this code has no root.",
                **{MARKER_KEY: "parent_cycle"},
                code_id=code.id,
                parent_id=code.parent_id,
            )
        elif depth > rules.hierarchy_depth:
            report.add(
                "S6",
                Severity.WARN,
                "codebook",
                code.name,
                f"Code sits {depth} levels deep; the codebook has "
                f"{rules.hierarchy_depth} levels.",
                **{MARKER_KEY: "hierarchy_too_deep"},
                code_id=code.id,
                depth=depth,
                hierarchy_depth=rules.hierarchy_depth,
            )

        if code.id not in leaf_ids and code.evidence:
            report.add(
                "S6",
                Severity.INFO,
                "codebook",
                code.name,
                "Code carries evidence while having children; evidence belongs at the leaves.",
                **{MARKER_KEY: "evidence_on_parent"},
                code_id=code.id,
                evidence_count=len(code.evidence),
                children=[child.name for child in codebook.children_of(code.id)],
            )

        if rules.require_description and not code.description.strip():
            report.add(
                "S6",
                Severity.WARN,
                "codebook",
                code.name,
                "Code has no description, so it does not yet explain a segment's meaning.",
                **{MARKER_KEY: "missing_description"},
                code_id=code.id,
            )

        if known_ids is not None:
            missing = sorted(
                {e.response_id for e in code.evidence if e.response_id not in known_ids}
            )
            if missing:
                report.add(
                    "S6",
                    Severity.ERROR,
                    "codebook",
                    code.name,
                    "Evidence references response ids that are not in the corpus: "
                    f"{', '.join(str(rid) for rid in missing)}.",
                    **{MARKER_KEY: "evidence_response_missing"},
                    code_id=code.id,
                    missing_response_ids=missing,
                )

        if rules.check_name_grammar and code.id in leaf_ids:
            reasons = _grammar_reasons(code.name)
            if reasons:
                report.add(
                    "S6",
                    Severity.WARN,
                    "codebook",
                    code.name,
                    f"Leaf name {code.name!r} does not follow the toplevel-sub_level "
                    f"grammar ({', '.join(reasons)}).",
                    **{MARKER_KEY: "name_grammar"},
                    code_id=code.id,
                    reasons=reasons,
                    pattern=NAME_PART_RE.pattern,
                )
    return report
