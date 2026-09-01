"""Concurrent validation: machine codings against the PI's human golden set.

Alqazlan-style concurrent validation measures the residual error of the machine
coding rather than trying to eliminate it by hand — which is the corollary of ADR-0004,
where the human gate deliberately sits at codebook-refactor level and not on every
item. This module is the measurement.

**Two levels, because they answer different questions.**

*Code level* — did the machine apply the same elements to the same responses? Machine
code names are matched to human code names **through the embedding space**, never
lexically (ADR-0003): cosine similarity over ``code_text`` renderings, a Hungarian
assignment so the matching is globally optimal rather than greedy, and a pair is
accepted only at or above ``CodingRules.tau_high``. Precision, recall and F1 are then
computed over the response x code cell matrix, together with a chance-corrected
statistic.

*Segment level* — did they attach those codes to the same **spans**? Reported as
span-overlap-weighted precision/recall/F1, so that "right code, wrong place" shows up
as a code-level hit and a segment-level miss instead of being scored as a clean
success. The fixture contains exactly that case on purpose.

**Which chance-corrected statistic, and why.** Cohen's kappa, on the flattened
response x code binary decisions. The design here has exactly two coders (the human
golden set and the machine), every cell is rated by both by construction, the
categories are binary and nominal, and there is no missing data — the conditions
Cohen's kappa is defined for. Krippendorff's alpha exists to handle more raters,
missing values and non-nominal levels, none of which occur here; for two raters with
complete nominal data it differs from kappa only by a finite-sample ``(n-1)/n``
correction, so it would buy no robustness while making the number harder for a
reviewer to re-derive by hand. Kappa is also what the concurrent-validation literature
this replicates reports.

**The unmatched lists are the point.** ``over_coding`` (machine codes with no human
counterpart) and ``blind_spots`` (human codes the machine never produced) are rendered
with response id, segment, code and the near-miss, ready to quote in the write-up.

The blind-spot list is also the **only** place one of the PI's negative-example
categories — "You did not generate a new code" — can be detected at all. The other
three negative examples (imprecise, incomplete, unnecessary) all leave an artefact
inside a run: a candidate exists and a check can rule on it. A code the machine never
invented leaves nothing behind; it is visible only by comparison against a coding that
does contain it. That is what this list is.

Validation principles: **interpretive depth** (what the machine missed, not the
headline percentage) and **reliability** (a pure function of two assignment lists, one
embedder and one corpus).
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment

from gaf.config import CodingRules
from gaf.embed.protocol import Embedder, code_text, cosine
from gaf.models import Assignment, Codebook, Response
from gaf.textnorm import normalise

__all__ = [
    "AgreementReport",
    "CodeLevelAgreement",
    "CodeMatch",
    "CodeMatching",
    "PerCodeScore",
    "SegmentLevelAgreement",
    "UnmatchedCode",
    "UnmatchedRow",
    "cohens_kappa",
    "concurrent_validation",
    "descriptions_from_codebook",
    "match_codes",
    "observed_and_expected_agreement",
]


# --------------------------------------------------------------------------- #
# Matching code vocabularies through the embedding space
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class CodeMatch:
    """One human code paired with one machine code, and the cosine that paired them."""

    human_code: str
    machine_code: str
    similarity: float
    accepted: bool

    def to_json(self) -> dict[str, Any]:
        return {
            "human_code": self.human_code,
            "machine_code": self.machine_code,
            "similarity": self.similarity,
            "accepted": self.accepted,
        }


@dataclass(frozen=True, slots=True)
class CodeMatching:
    """The full Hungarian assignment between the two code vocabularies."""

    human_codes: tuple[str, ...]
    machine_codes: tuple[str, ...]
    pairs: tuple[CodeMatch, ...]
    tau_high: float
    space_id: str

    @property
    def accepted(self) -> tuple[CodeMatch, ...]:
        return tuple(p for p in self.pairs if p.accepted)

    def machine_to_human(self) -> dict[str, str]:
        return {p.machine_code: p.human_code for p in self.accepted}

    def unmatched_machine(self) -> tuple[str, ...]:
        paired = {p.machine_code for p in self.accepted}
        return tuple(c for c in self.machine_codes if c not in paired)

    def unmatched_human(self) -> tuple[str, ...]:
        paired = {p.human_code for p in self.accepted}
        return tuple(c for c in self.human_codes if c not in paired)

    def to_json(self) -> dict[str, Any]:
        return {
            "space_id": self.space_id,
            "tau_high": self.tau_high,
            "n_human_codes": len(self.human_codes),
            "n_machine_codes": len(self.machine_codes),
            "pairs": [p.to_json() for p in self.pairs],
            "unmatched_machine": list(self.unmatched_machine()),
            "unmatched_human": list(self.unmatched_human()),
        }


def descriptions_from_codebook(codebook: Codebook) -> dict[str, str]:
    """Code name -> description, for embedding codes as ``code_text(name, description)``."""
    return {c.name: c.description for c in codebook.sorted_codes()}


def match_codes(
    human_codes: Sequence[str],
    machine_codes: Sequence[str],
    *,
    embedder: Embedder,
    tau_high: float,
    descriptions: Mapping[str, str] | None = None,
) -> CodeMatching:
    """Hungarian assignment between the two vocabularies in one embedding space.

    Greedy matching is deliberately avoided: it is order-dependent and can pair a code
    with its second-best counterpart because a third code got there first. The
    assignment maximises total similarity over the whole bipartite graph, and only
    then is each pair tested against ``tau_high``. A pair below the threshold is
    reported with ``accepted=False`` and both of its codes count as unmatched — a
    near-miss is evidence, not a match.
    """
    texts = descriptions or {}
    human = tuple(sorted(set(human_codes)))
    machine = tuple(sorted(set(machine_codes)))
    if not human or not machine:
        return CodeMatching(
            human_codes=human,
            machine_codes=machine,
            pairs=(),
            tau_high=tau_high,
            space_id=embedder.space_id,
        )

    human_vectors = embedder.embed([code_text(n, texts.get(n, "")) for n in human])
    machine_vectors = embedder.embed([code_text(n, texts.get(n, "")) for n in machine])
    similarity = np.zeros((len(human), len(machine)), dtype=np.float64)
    for i in range(len(human)):
        for j in range(len(machine)):
            similarity[i, j] = cosine(human_vectors[i], machine_vectors[j])

    rows, cols = linear_sum_assignment(-similarity)
    pairs = [
        CodeMatch(
            human_code=human[i],
            machine_code=machine[j],
            similarity=float(similarity[i, j]),
            accepted=bool(float(similarity[i, j]) >= tau_high),
        )
        for i, j in zip(rows, cols, strict=True)
    ]
    pairs.sort(key=lambda p: (-p.similarity, p.human_code, p.machine_code))
    return CodeMatching(
        human_codes=human,
        machine_codes=machine,
        pairs=tuple(pairs),
        tau_high=tau_high,
        space_id=embedder.space_id,
    )


def _nearest(
    source: Sequence[str],
    target: Sequence[str],
    *,
    embedder: Embedder,
    descriptions: Mapping[str, str] | None = None,
) -> dict[str, tuple[str | None, float]]:
    """For each code in ``source``, its nearest counterpart in ``target`` and the cosine."""
    texts = descriptions or {}
    if not source:
        return {}
    if not target:
        return dict.fromkeys(source, (None, 0.0))
    source_vectors = embedder.embed([code_text(n, texts.get(n, "")) for n in source])
    target_vectors = embedder.embed([code_text(n, texts.get(n, "")) for n in target])
    out: dict[str, tuple[str | None, float]] = {}
    for i, name in enumerate(source):
        scores = [cosine(source_vectors[i], target_vectors[j]) for j in range(len(target))]
        best = int(np.argmax(scores))
        # A "nearest" code at cosine 0 shares nothing with the query and is not a
        # near-miss; reporting one would invite a reader to see a relationship that
        # the geometry says does not exist.
        out[name] = (target[best], float(scores[best])) if scores[best] > 0.0 else (None, 0.0)
    return out


# --------------------------------------------------------------------------- #
# Cohen's kappa
# --------------------------------------------------------------------------- #


def cohens_kappa(a: Sequence[int], b: Sequence[int]) -> float:
    """Cohen's kappa for two raters over paired binary decisions.

    Implemented from the definition rather than pulled from a library, so the number
    in the report can be re-derived from the confusion counts printed beside it:

        po = observed agreement = (n11 + n00) / n
        pe = sum over categories k of  P_a(k) * P_b(k)
        kappa = (po - pe) / (1 - pe)

    ``pe == 1`` — both raters used one category for everything — leaves kappa
    undefined (0/0). It returns 1.0 when the raters nevertheless agreed on every cell
    and 0.0 when they did not, which is the conventional degenerate-case reading and
    is stated here rather than left to a library's choice.
    """
    left = [int(x) for x in a]
    right = [int(x) for x in b]
    if len(left) != len(right):
        raise ValueError(f"paired ratings must be the same length: {len(left)} vs {len(right)}")
    n = len(left)
    if n == 0:
        raise ValueError("Cohen's kappa is undefined on an empty table")

    observed, expected = observed_and_expected_agreement(left, right)
    if expected >= 1.0:
        return 1.0 if observed >= 1.0 else 0.0
    return (observed - expected) / (1.0 - expected)


def observed_and_expected_agreement(
    a: Sequence[int], b: Sequence[int]
) -> tuple[float, float]:
    """``(po, pe)`` for two raters over paired nominal decisions.

    Exposed because the report prints both beside kappa: a reviewer who can see the
    observed and chance-expected agreement can re-derive the statistic in one line,
    and the two numbers cannot drift apart from the kappa they produced.
    """
    left = [int(x) for x in a]
    right = [int(x) for x in b]
    n = len(left)
    if n == 0:
        raise ValueError("agreement is undefined on an empty table")
    observed = sum(1 for x, y in zip(left, right, strict=True) if x == y) / n
    expected = sum(
        (left.count(k) / n) * (right.count(k) / n)
        for k in sorted(set(left) | set(right))
    )
    return observed, expected


# --------------------------------------------------------------------------- #
# Spans
# --------------------------------------------------------------------------- #


def _locate(segment: str, haystack: str) -> tuple[int, int] | None:
    """Character span of ``segment`` inside an already-normalised response text.

    Exact search first; then a case-insensitive search, taken only when lower-casing
    preserved the length of both strings, so the returned offsets still index the
    normalised text (see `gaf.textnorm.normalise_for_match`, which is explicitly not
    offset-compatible). Anything looser would be a fuzzy locator, and quote provenance
    already has one in S2 — this module does not duplicate it.
    """
    needle = normalise(segment)
    if not needle:
        return None
    index = haystack.find(needle)
    if index >= 0:
        return (index, index + len(needle))
    lowered_hay, lowered_needle = haystack.lower(), needle.lower()
    if len(lowered_hay) == len(haystack) and len(lowered_needle) == len(needle):
        index = lowered_hay.find(lowered_needle)
        if index >= 0:
            return (index, index + len(needle))
    return None


def _span_jaccard(a: tuple[int, int], b: tuple[int, int]) -> float:
    """Character-span Jaccard: |intersection| / |union|. Disjoint spans score 0."""
    intersection = max(0, min(a[1], b[1]) - max(a[0], b[0]))
    union = (a[1] - a[0]) + (b[1] - b[0]) - intersection
    return intersection / union if union > 0 else 0.0


def _string_overlap(a: str, b: str) -> float:
    """Fallback overlap when no corpus is available to locate the spans in.

    Identical normalised quotes score 1.0; a quote wholly containing the other scores
    ``len(shorter) / len(longer)``, which is what the span Jaccard would be for nested
    spans; anything else scores 0.0. Documented as a degradation, and reported as
    ``segment_mode == "string"`` so a reader never mistakes it for a real span
    comparison.
    """
    left, right = normalise(a), normalise(b)
    if not left or not right:
        return 0.0
    if left == right:
        return 1.0
    short, long = (left, right) if len(left) <= len(right) else (right, left)
    if short in long:
        return len(short) / len(long)
    return 0.0


# --------------------------------------------------------------------------- #
# Results
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class PerCodeScore:
    """Precision/recall/F1 for one column of the response x code matrix."""

    code: str
    human_n: int
    machine_n: int
    tp: int
    fp: int
    fn: int
    precision: float
    recall: float
    f1: float

    def to_json(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "human_n": self.human_n,
            "machine_n": self.machine_n,
            "tp": self.tp,
            "fp": self.fp,
            "fn": self.fn,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
        }


@dataclass(frozen=True, slots=True)
class CodeLevelAgreement:
    """Micro-averaged agreement over the response x code cells."""

    n_responses: int
    n_codes: int
    n_cells: int
    tp: int
    fp: int
    fn: int
    tn: int
    precision: float
    recall: float
    f1: float
    kappa: float
    observed_agreement: float
    expected_agreement: float
    per_code: tuple[PerCodeScore, ...]

    def to_json(self) -> dict[str, Any]:
        return {
            "n_responses": self.n_responses,
            "n_codes": self.n_codes,
            "n_cells": self.n_cells,
            "tp": self.tp,
            "fp": self.fp,
            "fn": self.fn,
            "tn": self.tn,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
            "cohens_kappa": self.kappa,
            "observed_agreement": self.observed_agreement,
            "expected_agreement": self.expected_agreement,
            "per_code": [p.to_json() for p in self.per_code],
        }


@dataclass(frozen=True, slots=True)
class SegmentLevelAgreement:
    """Span-overlap-weighted agreement — "right code, wrong place" made visible."""

    mode: str
    overlap_threshold: float
    n_human: int
    n_machine: int
    n_located_human: int
    n_located_machine: int
    weighted_precision: float
    weighted_recall: float
    weighted_f1: float
    strict_precision: float
    strict_recall: float
    strict_f1: float
    mean_overlap_on_shared_codes: float
    right_code_wrong_place: int

    def to_json(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "overlap_threshold": self.overlap_threshold,
            "n_human": self.n_human,
            "n_machine": self.n_machine,
            "n_located_human": self.n_located_human,
            "n_located_machine": self.n_located_machine,
            "weighted_precision": self.weighted_precision,
            "weighted_recall": self.weighted_recall,
            "weighted_f1": self.weighted_f1,
            "strict_precision": self.strict_precision,
            "strict_recall": self.strict_recall,
            "strict_f1": self.strict_f1,
            "mean_overlap_on_shared_codes": self.mean_overlap_on_shared_codes,
            "right_code_wrong_place": self.right_code_wrong_place,
        }


@dataclass(frozen=True, slots=True)
class UnmatchedRow:
    """One quotable row of an over-coding or blind-spot list."""

    kind: str
    side: str
    response_id: int
    segment: str
    code: str
    nearest_code: str | None
    nearest_similarity: float

    def to_json(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "side": self.side,
            "response_id": self.response_id,
            "segment": self.segment,
            "code": self.code,
            "nearest_code": self.nearest_code,
            "nearest_similarity": self.nearest_similarity,
        }


@dataclass(frozen=True, slots=True)
class UnmatchedCode:
    """One code with no counterpart on the other side, and every row it produced."""

    kind: str
    side: str
    code: str
    n_assignments: int
    response_ids: tuple[int, ...]
    nearest_code: str | None
    nearest_similarity: float
    rows: tuple[UnmatchedRow, ...]

    def to_json(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "side": self.side,
            "code": self.code,
            "n_assignments": self.n_assignments,
            "response_ids": list(self.response_ids),
            "nearest_code": self.nearest_code,
            "nearest_similarity": self.nearest_similarity,
            "rows": [r.to_json() for r in self.rows],
        }


@dataclass(frozen=True, slots=True)
class AgreementReport:
    """The whole concurrent-validation dossier for one golden set."""

    matching: CodeMatching
    code_level: CodeLevelAgreement
    matched_only: CodeLevelAgreement
    segment_level: SegmentLevelAgreement
    over_coding: tuple[UnmatchedCode, ...]
    blind_spots: tuple[UnmatchedCode, ...]

    def to_json(self) -> dict[str, Any]:
        return {
            "matching": self.matching.to_json(),
            "code_level": self.code_level.to_json(),
            "matched_only": self.matched_only.to_json(),
            "segment_level": self.segment_level.to_json(),
            "over_coding": [u.to_json() for u in self.over_coding],
            "blind_spots": [u.to_json() for u in self.blind_spots],
        }

    def to_json_str(self) -> str:
        return json.dumps(self.to_json(), sort_keys=True, ensure_ascii=False, indent=2)

    def to_markdown(self) -> str:
        code = self.code_level
        segment = self.segment_level
        lines = [
            "## Concurrent validation — machine codings against the human golden set",
            "",
            f"Embedding space `{self.matching.space_id}`; code matching by Hungarian "
            f"assignment at tau_high = {self.matching.tau_high:g}. "
            f"{len(self.matching.accepted)} of {len(self.matching.human_codes)} human "
            f"and {len(self.matching.machine_codes)} machine codes matched.",
            "",
            "### Code level",
            "",
            "| scope | precision | recall | F1 | Cohen's kappa | TP | FP | FN |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
            f"| all codes (union vocabulary) | {code.precision:.3f} | {code.recall:.3f} "
            f"| {code.f1:.3f} | {code.kappa:.3f} | {code.tp} | {code.fp} | {code.fn} |",
            f"| matched codes only | {self.matched_only.precision:.3f} | "
            f"{self.matched_only.recall:.3f} | {self.matched_only.f1:.3f} | "
            f"{self.matched_only.kappa:.3f} | {self.matched_only.tp} | "
            f"{self.matched_only.fp} | {self.matched_only.fn} |",
            "",
            f"Observed agreement {code.observed_agreement:.4f}, expected by chance "
            f"{code.expected_agreement:.4f}, over {code.n_cells} cells "
            f"({code.n_responses} responses x {code.n_codes} codes).",
            "",
            "### Segment level",
            "",
            f"Span overlap computed in `{segment.mode}` mode; a hit at or above "
            f"overlap {segment.overlap_threshold:g} counts as strict.",
            "",
            "| measure | precision | recall | F1 |",
            "|---|---:|---:|---:|",
            f"| span-overlap-weighted | {segment.weighted_precision:.3f} | "
            f"{segment.weighted_recall:.3f} | {segment.weighted_f1:.3f} |",
            f"| strict (overlap >= {segment.overlap_threshold:g}) | "
            f"{segment.strict_precision:.3f} | {segment.strict_recall:.3f} | "
            f"{segment.strict_f1:.3f} |",
            "",
            f"**{segment.right_code_wrong_place}** machine assignment(s) carry a code "
            "the human also applied to that response but attach it to a different span "
            "— right code, wrong place. These score as code-level hits and segment-level "
            "misses, which is the distinction this level exists to make.",
        ]
        lines.extend(["", "### Over-coding — machine codes with no human counterpart", ""])
        lines.extend(_unmatched_table(self.over_coding, "nearest human code"))
        lines.extend(
            [
                "",
                "### Blind spots — human codes the machine never produced",
                "",
                "The only place the negative example \"You did not generate a new code\" "
                "is observable: a code the machine never invented leaves no artefact "
                "inside a run.",
                "",
            ]
        )
        lines.extend(_unmatched_table(self.blind_spots, "nearest machine code"))
        return "\n".join(lines)


def _unmatched_table(items: Sequence[UnmatchedCode], nearest_label: str) -> list[str]:
    if not items:
        return ["_None._"]
    lines = [
        f"| response | segment | code | {nearest_label} | cosine |",
        "|---:|---|---|---|---:|",
    ]
    for item in items:
        for row in item.rows:
            nearest = row.nearest_code or "—"
            lines.append(
                f"| {row.response_id} | {row.segment} | `{row.code}` | `{nearest}` "
                f"| {row.nearest_similarity:.3f} |"
            )
    return lines


# --------------------------------------------------------------------------- #
# The comparison
# --------------------------------------------------------------------------- #


def _cell_scores(
    human_cells: Sequence[int],
    machine_cells: Sequence[int],
    *,
    n_responses: int,
    codes: Sequence[str],
    per_code: Sequence[PerCodeScore],
) -> CodeLevelAgreement:
    tp = sum(1 for h, m in zip(human_cells, machine_cells, strict=True) if h and m)
    fp = sum(1 for h, m in zip(human_cells, machine_cells, strict=True) if m and not h)
    fn = sum(1 for h, m in zip(human_cells, machine_cells, strict=True) if h and not m)
    tn = len(human_cells) - tp - fp - fn
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    if human_cells:
        observed, expected = observed_and_expected_agreement(human_cells, machine_cells)
        kappa = cohens_kappa(human_cells, machine_cells)
    else:
        observed = expected = 0.0
        kappa = 0.0

    return CodeLevelAgreement(
        n_responses=n_responses,
        n_codes=len(codes),
        n_cells=len(human_cells),
        tp=tp,
        fp=fp,
        fn=fn,
        tn=tn,
        precision=precision,
        recall=recall,
        f1=f1,
        kappa=kappa,
        observed_agreement=observed,
        expected_agreement=expected,
        per_code=tuple(per_code),
    )


def concurrent_validation(
    human: Sequence[Assignment],
    machine: Sequence[Assignment],
    *,
    embedder: Embedder,
    rules: CodingRules | None = None,
    corpus: Mapping[int, Response] | None = None,
    descriptions: Mapping[str, str] | None = None,
) -> AgreementReport:
    """Compare a machine coding against the human golden set at both levels.

    ``corpus`` is what makes the segment level a real span comparison: quotes are
    located in ``normalise(response.content)`` and compared as character intervals.
    Without it the module degrades to string containment and says so in
    ``segment_level.mode``.

    ``descriptions`` supplies code descriptions for the embedding — codes are rendered
    with :func:`gaf.embed.protocol.code_text`, exactly as every other stage renders
    them, so a similarity here is comparable with a similarity anywhere else in the
    system. :func:`descriptions_from_codebook` builds the mapping from a codebook.
    """
    coding_rules = rules or CodingRules()

    human_codes = sorted({a.code for a in human})
    machine_codes = sorted({a.code for a in machine})
    matching = match_codes(
        human_codes,
        machine_codes,
        embedder=embedder,
        tau_high=coding_rules.tau_high,
        descriptions=descriptions,
    )
    machine_to_human = matching.machine_to_human()

    # Canonical column names: a matched machine code is renamed to its human
    # counterpart, so both sides index the same column. Unmatched codes keep their own
    # name and therefore occupy a column the other side can never fill — which is
    # exactly how over-coding and blind spots enter precision and recall.
    def canonical(code: str, side: str) -> str:
        return machine_to_human.get(code, code) if side == "machine" else code

    responses = sorted({a.response_id for a in human} | {a.response_id for a in machine})
    columns = sorted(
        {canonical(a.code, "human") for a in human}
        | {canonical(a.code, "machine") for a in machine}
    )
    matched_columns = sorted({p.human_code for p in matching.accepted})

    human_set = {(a.response_id, canonical(a.code, "human")) for a in human}
    machine_set = {(a.response_id, canonical(a.code, "machine")) for a in machine}

    def build(cols: Sequence[str]) -> tuple[list[int], list[int], list[PerCodeScore]]:
        human_cells: list[int] = []
        machine_cells: list[int] = []
        per_code: list[PerCodeScore] = []
        for column in cols:
            tp = fp = fn = human_n = machine_n = 0
            for response_id in responses:
                in_human = int((response_id, column) in human_set)
                in_machine = int((response_id, column) in machine_set)
                human_cells.append(in_human)
                machine_cells.append(in_machine)
                human_n += in_human
                machine_n += in_machine
                tp += in_human and in_machine
                fp += in_machine and not in_human
                fn += in_human and not in_machine
            precision = tp / (tp + fp) if (tp + fp) else 0.0
            recall = tp / (tp + fn) if (tp + fn) else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
            per_code.append(
                PerCodeScore(
                    code=column,
                    human_n=human_n,
                    machine_n=machine_n,
                    tp=tp,
                    fp=fp,
                    fn=fn,
                    precision=precision,
                    recall=recall,
                    f1=f1,
                )
            )
        return human_cells, machine_cells, per_code

    all_human_cells, all_machine_cells, all_per_code = build(columns)
    code_level = _cell_scores(
        all_human_cells,
        all_machine_cells,
        n_responses=len(responses),
        codes=columns,
        per_code=all_per_code,
    )
    matched_human_cells, matched_machine_cells, matched_per_code = build(matched_columns)
    matched_only = _cell_scores(
        matched_human_cells,
        matched_machine_cells,
        n_responses=len(responses),
        codes=matched_columns,
        per_code=matched_per_code,
    )

    segment_level = _segment_agreement(
        human,
        machine,
        canonical=canonical,
        corpus=corpus,
        threshold=coding_rules.segment_overlap_threshold,
    )

    nearest_machine = _nearest(
        matching.unmatched_machine(),
        matching.human_codes,
        embedder=embedder,
        descriptions=descriptions,
    )
    nearest_human = _nearest(
        matching.unmatched_human(),
        matching.machine_codes,
        embedder=embedder,
        descriptions=descriptions,
    )

    over_coding = _unmatched_codes(
        matching.unmatched_machine(), machine, nearest_machine, kind="over_coding", side="machine"
    )
    blind_spots = _unmatched_codes(
        matching.unmatched_human(), human, nearest_human, kind="blind_spot", side="human"
    )

    return AgreementReport(
        matching=matching,
        code_level=code_level,
        matched_only=matched_only,
        segment_level=segment_level,
        over_coding=over_coding,
        blind_spots=blind_spots,
    )


def _unmatched_codes(
    codes: Sequence[str],
    assignments: Sequence[Assignment],
    nearest: Mapping[str, tuple[str | None, float]],
    *,
    kind: str,
    side: str,
) -> tuple[UnmatchedCode, ...]:
    out: list[UnmatchedCode] = []
    for code in sorted(codes):
        rows_for_code = sorted(
            (a for a in assignments if a.code == code),
            key=lambda a: (a.response_id, a.segment),
        )
        near_code, near_score = nearest.get(code, (None, 0.0))
        rows = tuple(
            UnmatchedRow(
                kind=kind,
                side=side,
                response_id=a.response_id,
                segment=a.segment,
                code=code,
                nearest_code=near_code,
                nearest_similarity=near_score,
            )
            for a in rows_for_code
        )
        out.append(
            UnmatchedCode(
                kind=kind,
                side=side,
                code=code,
                n_assignments=len(rows),
                response_ids=tuple(sorted({a.response_id for a in rows_for_code})),
                nearest_code=near_code,
                nearest_similarity=near_score,
                rows=rows,
            )
        )
    return tuple(out)


def _segment_agreement(
    human: Sequence[Assignment],
    machine: Sequence[Assignment],
    *,
    canonical: Callable[[str, str], str],
    corpus: Mapping[int, Response] | None,
    threshold: float,
) -> SegmentLevelAgreement:
    """Span-overlap-weighted precision/recall/F1 over individual assignment rows."""
    mode = "span" if corpus else "string"
    normalised: dict[int, str] = (
        {rid: normalise(r.content) for rid, r in corpus.items()} if corpus else {}
    )

    def span_of(assignment: Assignment) -> tuple[int, int] | None:
        text = normalised.get(assignment.response_id)
        return _locate(assignment.segment, text) if text is not None else None

    human_rows = [(a, canonical(a.code, "human"), span_of(a)) for a in human]
    machine_rows = [(a, canonical(a.code, "machine"), span_of(a)) for a in machine]

    def overlap(
        row: tuple[Assignment, str, tuple[int, int] | None],
        others: Sequence[tuple[Assignment, str, tuple[int, int] | None]],
    ) -> float:
        assignment, column, span = row
        best = 0.0
        for other_assignment, other_column, other_span in others:
            if other_assignment.response_id != assignment.response_id:
                continue
            if other_column != column:
                continue
            if span is not None and other_span is not None:
                score = _span_jaccard(span, other_span)
            else:
                score = _string_overlap(assignment.segment, other_assignment.segment)
            best = max(best, score)
        return best

    machine_scores = [overlap(row, human_rows) for row in machine_rows]
    human_scores = [overlap(row, machine_rows) for row in human_rows]

    n_machine = len(machine_rows) or 1
    n_human = len(human_rows) or 1
    weighted_precision = sum(machine_scores) / n_machine
    weighted_recall = sum(human_scores) / n_human
    weighted_f1 = (
        2 * weighted_precision * weighted_recall / (weighted_precision + weighted_recall)
        if (weighted_precision + weighted_recall)
        else 0.0
    )
    strict_precision = sum(1 for s in machine_scores if s >= threshold) / n_machine
    strict_recall = sum(1 for s in human_scores if s >= threshold) / n_human
    strict_f1 = (
        2 * strict_precision * strict_recall / (strict_precision + strict_recall)
        if (strict_precision + strict_recall)
        else 0.0
    )

    # "Right code, wrong place": the human applied this code to this response too, so
    # it is a code-level hit, yet no human span for it overlaps enough to be the same
    # piece of text (CodingRules.segment_overlap_threshold).
    human_columns = {(a.response_id, column) for a, column, _ in human_rows}
    right_code_wrong_place = sum(
        1
        for (assignment, column, _), score in zip(machine_rows, machine_scores, strict=True)
        if (assignment.response_id, column) in human_columns and score < threshold
    )
    shared = [
        score
        for (assignment, column, _), score in zip(machine_rows, machine_scores, strict=True)
        if (assignment.response_id, column) in human_columns
    ]

    return SegmentLevelAgreement(
        mode=mode,
        overlap_threshold=threshold,
        n_human=len(human_rows),
        n_machine=len(machine_rows),
        n_located_human=sum(1 for _, _, span in human_rows if span is not None),
        n_located_machine=sum(1 for _, _, span in machine_rows if span is not None),
        weighted_precision=weighted_precision,
        weighted_recall=weighted_recall,
        weighted_f1=weighted_f1,
        strict_precision=strict_precision,
        strict_recall=strict_recall,
        strict_f1=strict_f1,
        mean_overlap_on_shared_codes=sum(shared) / len(shared) if shared else 0.0,
        right_code_wrong_place=right_code_wrong_place,
    )
