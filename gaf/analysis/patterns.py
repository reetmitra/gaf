"""Pattern mapping: which responses look alike, and which codes travel together.

This is a *view* over an :class:`~gaf.analysis.matrix.OccurrenceMatrix`, not a
restructuring of anything. It answers three questions a reader of the codebook cannot
answer from the codebook alone: which responses share the same combination of
families (pattern groups), which pairs and triples of codes recur together more often
than chance (frequent combinations), and, for any one response, which others look most
like it (nearest pattern-mates). No model runs here and no code is merged, split or
renamed — restructuring happens only behind the human gate in the slow loop.

**Unfiltered by default, on purpose.** A pattern view exists to show which elements
co-occur, including rare ones; the low-frequency filter that :mod:`gaf.analysis.matrix`
applies before Ward's HCA would silently remove exactly the rare combinations this
module is for. :func:`build_patterns` does not re-filter — it reports whichever filter
already produced the matrix it was given (:attr:`PatternReport.filter`), so a caller
who wants "no codes dropped" passes a matrix built with
``AnalysisConfig(min_code_frequency=1)`` (or an equivalent no-op filter) and the
resulting report says so.

**The triple enumeration is bounded, not exhaustive by brute force.** Pairs are cheap
at a few hundred codes (at most a few tens of thousands), so every pair is scored.
Triples are not: a naive `C(n, 3)` blows up long before a few hundred codes. Instead,
candidate triples come from an Apriori join — a triple can only meet
``min_support`` if each of its three constituent pairs does, because support is
monotone non-increasing as a combination grows — and only candidates surviving that
join are ever scored exactly. :data:`MAX_TRIPLE_CANDIDATES` is a second, hard bound on
top of the join. **It does bite at this project's own corpus scale**: 200 responses
over 117 codes reach it from about twelve codes per response upward, so the order the
bound cuts in is not a detail. Candidates are therefore ranked by the *smallest of
their three pair supports* — an exact upper bound on the triple's own support —
before the cut, so the kept set is the candidates that could possibly rank highest,
and a discarded triple cannot beat the last one kept. The report says the bound was
hit and by how much.

Output is response numbers, code names and family names only. No respondent text
enters or leaves this module.

Validation principles: **transparency** (the filter and the triple bound are both
named in the output) and **reliability** (a pure, seedless function of one matrix).
"""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from itertools import combinations
from typing import Any

import numpy as np

from gaf.analysis.matrix import FilterReport, OccurrenceMatrix
from gaf.models import family_of

__all__ = [
    "DEFAULT_MIN_SUPPORT",
    "MAX_TRIPLE_CANDIDATES",
    "TOP_K_PATTERN_MATES",
    "Combination",
    "CombinationReport",
    "CooccurrenceTable",
    "NearestMate",
    "PatternGroup",
    "PatternReport",
    "ResponsePattern",
    "build_patterns",
    "jaccard_matrix",
]

#: Chan's own filter is documented per-run; a pattern view has its own default of "no
#: extra filtering beyond min_support" for the combinations it computes.
DEFAULT_MIN_SUPPORT = 2

#: Nearest pattern-mates reported per response.
TOP_K_PATTERN_MATES = 3

#: Hard cap on Apriori-joined triple candidates actually scored. See the module
#: docstring: the join restricts candidates to those whose three constituent pairs are
#: all independently frequent, which is enough at low coding density and is *not*
#: enough at this project's own scale — measured, 200 responses over 117 codes at
#: twelve codes per response produce roughly 57,000 candidates. The cap is therefore a
#: real prune, applied to candidates ranked by their exact support bound, and it is
#: reported whenever it is hit.
MAX_TRIPLE_CANDIDATES = 20_000


# --------------------------------------------------------------------------- #
# Pairwise Jaccard over binary columns
# --------------------------------------------------------------------------- #


def jaccard_matrix(values: np.ndarray) -> np.ndarray:
    """Pairwise Jaccard similarity between the **columns** of a binary matrix.

    ``values`` is a 0/1 array of shape ``(n_units, n_items)``. The result is a
    symmetric ``(n_items, n_items)`` array whose ``[i, j]`` cell is the Jaccard index
    of column ``i`` and column ``j`` treated as sets of units. The diagonal is 1.0 by
    convention — a set is identical to itself, whether or not it is empty — which
    matters here because an all-zero column (a code or family that never occurs in
    this matrix) is a legitimate input.

    Computed with one matrix multiply (exact because the columns are 0/1), the same
    trick :func:`gaf.embed.matcher.cosine_matrix` uses for cosine similarity.
    """
    data = values.astype(np.float64)
    intersection = data.T @ data
    counts = np.diag(intersection).copy()
    union = counts[:, None] + counts[None, :] - intersection
    result = np.divide(
        intersection,
        union,
        out=np.zeros_like(intersection),
        where=union > 0,
    )
    np.fill_diagonal(result, 1.0)
    return result


# --------------------------------------------------------------------------- #
# Per-response signatures and nearest mates
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class NearestMate:
    """One entry in a response's nearest-pattern-mates list."""

    response_id: int
    jaccard: float

    def to_json(self) -> dict[str, Any]:
        return {"response_id": self.response_id, "jaccard": self.jaccard}


@dataclass(frozen=True, slots=True)
class ResponsePattern:
    """One response's family signature, code set, and nearest pattern-mates.

    ``family_signature`` is the sorted set of families the response touches;
    ``code_set`` is the sorted set of codes. Two responses with the same code set
    necessarily have the same family signature, but the reverse is not true — that gap
    is exactly what :class:`PatternGroup` groups on.
    """

    response_id: int
    family_signature: tuple[str, ...]
    code_set: tuple[str, ...]
    nearest: tuple[NearestMate, ...]

    def to_json(self) -> dict[str, Any]:
        return {
            "response_id": self.response_id,
            "family_signature": list(self.family_signature),
            "code_set": list(self.code_set),
            "nearest": [m.to_json() for m in self.nearest],
        }


@dataclass(frozen=True, slots=True)
class PatternGroup:
    """Two or more responses sharing an identical family signature.

    A group of one response is not a pattern shared with anything; those are counted
    and listed separately as :attr:`PatternReport.singleton_response_ids`.
    """

    family_signature: tuple[str, ...]
    response_ids: tuple[int, ...]

    @property
    def size(self) -> int:
        return len(self.response_ids)

    def to_json(self) -> dict[str, Any]:
        return {
            "family_signature": list(self.family_signature),
            "response_ids": list(self.response_ids),
            "size": self.size,
        }


# --------------------------------------------------------------------------- #
# Co-occurrence tables
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class CooccurrenceTable:
    """A code-by-code or family-by-family co-occurrence table: counts and Jaccard.

    ``counts[i][j]`` is the number of responses in which both ``names[i]`` and
    ``names[j]`` occur; the diagonal is each item's own frequency. ``jaccard[i][j]``
    is the Jaccard index of their occurrence sets over responses; the diagonal is 1.0.
    """

    names: tuple[str, ...]
    counts: np.ndarray
    jaccard: np.ndarray

    def to_json(self) -> dict[str, Any]:
        return {
            "names": list(self.names),
            "counts": [[int(v) for v in row] for row in self.counts],
            "jaccard": [[float(v) for v in row] for row in self.jaccard],
        }


def _cooccurrence(names: tuple[str, ...], values: np.ndarray) -> CooccurrenceTable:
    counts = (values.astype(np.int64).T @ values.astype(np.int64))
    jaccard = jaccard_matrix(values)
    return CooccurrenceTable(names=names, counts=counts, jaccard=jaccard)


def _family_occurrence(matrix: OccurrenceMatrix) -> tuple[tuple[str, ...], np.ndarray]:
    """Response x family binary matrix: family ``f`` occurs when any of its codes do."""
    families = tuple(sorted({family_of(c) for c in matrix.code_names}))
    out = np.zeros((matrix.n_responses, len(families)), dtype=np.int8)
    if not families:
        return families, out
    column_of = {f: i for i, f in enumerate(families)}
    for j, code in enumerate(matrix.code_names):
        fam_col = column_of[family_of(code)]
        out[:, fam_col] = np.maximum(out[:, fam_col], matrix.values[:, j])
    return families, out


# --------------------------------------------------------------------------- #
# Frequent combinations
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class Combination:
    """One pair or triple of codes at or above ``min_support``.

    ``share`` is ``support / n_responses``. ``lift`` is the joint share divided by the
    product of the individual codes' shares — 1.0 means the combination occurs exactly
    as often as independence would predict, above 1.0 means the codes travel together
    more than chance, and it is left undefined (0.0) only when a constituent code has
    zero frequency, which cannot happen for a combination that met ``min_support``.
    """

    codes: tuple[str, ...]
    support: int
    share: float
    lift: float

    def to_json(self) -> dict[str, Any]:
        return {
            "codes": list(self.codes),
            "support": self.support,
            "share": self.share,
            "lift": self.lift,
        }


@dataclass(frozen=True, slots=True)
class CombinationReport:
    """Frequent pairs and triples, and what the triple bound did.

    ``triple_candidates_total`` is the number of triples surviving the Apriori join
    (every sub-pair independently frequent); ``triple_candidates_considered`` is how
    many were actually scored against ``min_support`` after :data:`MAX_TRIPLE_CANDIDATES`
    was applied. ``triple_bound_hit`` is true exactly when the two differ.
    """

    min_support: int
    pairs: tuple[Combination, ...]
    triples: tuple[Combination, ...]
    triple_bound: int
    triple_candidates_total: int
    triple_candidates_considered: int

    @property
    def triple_bound_hit(self) -> bool:
        return self.triple_candidates_considered < self.triple_candidates_total

    def to_json(self) -> dict[str, Any]:
        return {
            "min_support": self.min_support,
            "pairs": [c.to_json() for c in self.pairs],
            "triples": [c.to_json() for c in self.triples],
            "triple_bound": self.triple_bound,
            "triple_candidates_total": self.triple_candidates_total,
            "triple_candidates_considered": self.triple_candidates_considered,
            "triple_bound_hit": self.triple_bound_hit,
        }


def _lift(share: float, freq: Sequence[float], n: int) -> float:
    if n <= 0:
        return 0.0
    denom = 1.0
    for f in freq:
        denom *= f / n
    return share / denom if denom > 0 else 0.0


def _combinations(
    code_names: tuple[str, ...],
    values: np.ndarray,
    counts: np.ndarray,
    n_responses: int,
    min_support: int,
    max_triple_candidates: int,
) -> CombinationReport:
    n_codes = len(code_names)
    freq = [int(values[:, i].sum()) for i in range(n_codes)]

    pairs: list[Combination] = []
    frequent_pair_index: set[tuple[int, int]] = set()
    for i, j in combinations(range(n_codes), 2):
        support = int(counts[i, j])
        if support < min_support:
            continue
        frequent_pair_index.add((i, j))
        share = support / n_responses if n_responses else 0.0
        pairs.append(
            Combination(
                codes=(code_names[i], code_names[j]),
                support=support,
                share=share,
                lift=_lift(share, (freq[i], freq[j]), n_responses),
            )
        )
    pairs.sort(key=lambda c: (-c.support, c.codes))

    # Apriori join: a triple {i, j, k} is a candidate only if all three of its
    # constituent pairs are independently frequent — a necessary condition for the
    # triple itself to meet min_support, since support cannot increase as a
    # combination grows.
    adjacency: dict[int, set[int]] = defaultdict(set)
    for i, j in frequent_pair_index:
        adjacency[i].add(j)
        adjacency[j].add(i)

    candidates: set[tuple[int, int, int]] = set()
    for i, j in frequent_pair_index:
        for k in adjacency[i] & adjacency[j]:
            if k > j:
                candidates.add((i, j, k))

    total_candidates = len(candidates)

    # Rank before truncating, by the **exact upper bound** on a triple's support: the
    # smallest of its three pair supports, since a triple cannot occur more often than
    # any pair it contains. Sorting by name and slicing scored an alphabetical prefix
    # and then re-sorted the survivors by support, so the table read as a top-by-support
    # list and was not one (R1 C4). The name tuple breaks ties, so the cut stays
    # deterministic.
    def support_bound(triple: tuple[int, int, int]) -> tuple[int, str, str, str]:
        i, j, k = triple
        bound = min(int(counts[i, j]), int(counts[i, k]), int(counts[j, k]))
        return (-bound, code_names[i], code_names[j], code_names[k])

    ordered = sorted(candidates, key=support_bound)
    bounded = ordered[:max_triple_candidates]

    triples: list[Combination] = []
    for i, j, k in bounded:
        mask = (values[:, i] == 1) & (values[:, j] == 1) & (values[:, k] == 1)
        support = int(mask.sum())
        if support < min_support:
            continue
        share = support / n_responses if n_responses else 0.0
        triples.append(
            Combination(
                codes=(code_names[i], code_names[j], code_names[k]),
                support=support,
                share=share,
                lift=_lift(share, (freq[i], freq[j], freq[k]), n_responses),
            )
        )
    triples.sort(key=lambda c: (-c.support, c.codes))

    return CombinationReport(
        min_support=min_support,
        pairs=tuple(pairs),
        triples=tuple(triples),
        triple_bound=max_triple_candidates,
        triple_candidates_total=total_candidates,
        triple_candidates_considered=len(bounded),
    )


# --------------------------------------------------------------------------- #
# The report
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class PatternReport:
    """The whole pattern-mapping dossier for one occurrence matrix."""

    n_responses: int
    n_codes: int
    filter: FilterReport
    min_support: int
    responses: tuple[ResponsePattern, ...]
    groups: tuple[PatternGroup, ...]
    singleton_response_ids: tuple[int, ...]
    code_cooccurrence: CooccurrenceTable
    family_cooccurrence: CooccurrenceTable
    combinations: CombinationReport
    #: Responses in the matrix's universe carrying no code at all. They are neither a
    #: group nor a singleton: an empty family signature is the absence of a pattern.
    uncoded_response_ids: tuple[int, ...] = ()

    def to_json(self) -> dict[str, Any]:
        return {
            "n_responses": self.n_responses,
            "n_codes": self.n_codes,
            "filter": self.filter.to_json(),
            "min_support": self.min_support,
            "responses": [r.to_json() for r in self.responses],
            "groups": [g.to_json() for g in self.groups],
            "singleton_response_ids": list(self.singleton_response_ids),
            "uncoded_response_ids": list(self.uncoded_response_ids),
            "code_cooccurrence": self.code_cooccurrence.to_json(),
            "family_cooccurrence": self.family_cooccurrence.to_json(),
            "combinations": self.combinations.to_json(),
        }

    def to_json_str(self) -> str:
        return json.dumps(self.to_json(), sort_keys=True, ensure_ascii=False, indent=2)

    def to_markdown(self, *, top_n: int = 15) -> str:
        """Pattern groups, then frequent combinations. No respondent text anywhere."""
        lines = [
            "## Pattern mapping",
            "",
            f"{self.n_responses} responses x {self.n_codes} codes. {self.filter.summary()}",
            f"Frequent combinations at min_support = {self.min_support}.",
            "",
            "### Pattern groups — identical family signature, largest first",
            "",
        ]
        if not self.groups:
            lines.append("_No two responses share an identical family signature._")
        else:
            lines.append("| n | responses | family signature |")
            lines.append("|---:|---|---|")
            for group in self.groups[:top_n]:
                signature = ", ".join(group.family_signature) if group.family_signature else "_(no codes)_"
                ids = ", ".join(str(r) for r in group.response_ids)
                lines.append(f"| {group.size} | {ids} | {signature} |")
            if len(self.groups) > top_n:
                lines.append("")
                lines.append(f"_Showing the largest {top_n} of {len(self.groups)} groups._")
        lines.append("")
        singleton_ids = ", ".join(str(r) for r in self.singleton_response_ids) or "_none_"
        lines.append(
            f"**{len(self.singleton_response_ids)}** response(s) carry a family signature "
            f"no other response shares: {singleton_ids}."
        )
        if self.uncoded_response_ids:
            uncoded_ids = ", ".join(str(r) for r in self.uncoded_response_ids)
            lines.append("")
            lines.append(
                f"**{len(self.uncoded_response_ids)}** response(s) carry no code at all "
                f"and are grouped with nothing: {uncoded_ids}."
            )
        lines.extend(["", "### Frequent code combinations", ""])
        lines.append("| codes | support | share | lift |")
        lines.append("|---|---:|---:|---:|")
        if not self.combinations.pairs and not self.combinations.triples:
            lines.append("| _none at this min_support_ | | | |")
        for combo in (*self.combinations.pairs[:top_n], *self.combinations.triples[:top_n]):
            lines.append(
                f"| {' + '.join(combo.codes)} | {combo.support} | {combo.share:.1%} "
                f"| {combo.lift:.2f} |"
            )
        if self.combinations.triple_bound_hit:
            lines.extend(
                [
                    "",
                    f"> **Warning.** {self.combinations.triple_candidates_total} triple "
                    "candidate(s) passed the frequent-pair join; the enumeration is bounded "
                    f"to {self.combinations.triple_bound}, so the "
                    f"{self.combinations.triple_candidates_considered} candidates with the "
                    "**highest possible support** (the smallest of each triple's three pair "
                    "supports, which is an exact upper bound on the triple's own) were "
                    "scored against min_support. A triple outside the kept set cannot have "
                    "a support above the bound of the last one kept.",
                ]
            )
        return "\n".join(lines)


def build_patterns(
    matrix: OccurrenceMatrix,
    *,
    min_support: int = DEFAULT_MIN_SUPPORT,
    top_k_mates: int = TOP_K_PATTERN_MATES,
    max_triple_candidates: int = MAX_TRIPLE_CANDIDATES,
) -> PatternReport:
    """Build the pattern-mapping report from an occurrence matrix.

    Pass the matrix built with whatever filter the caller wants reflected in the
    report (:attr:`PatternReport.filter`) — a pattern view must not silently lose rare
    codes, so this function does not filter again; it only reports the filter that
    already ran. An empty matrix (no responses or no codes) is not an error: the
    result is an empty report, consistent with :attr:`OccurrenceMatrix.is_empty`.
    """
    if min_support < 1:
        raise ValueError(f"min_support must be >= 1, got {min_support}")
    if top_k_mates < 0:
        raise ValueError(f"top_k_mates must be >= 0, got {top_k_mates}")
    if max_triple_candidates < 0:
        raise ValueError(f"max_triple_candidates must be >= 0, got {max_triple_candidates}")

    response_patterns: list[ResponsePattern] = []
    signatures: dict[int, tuple[str, ...]] = {}
    response_jaccard = jaccard_matrix(matrix.values.T) if matrix.n_responses else np.zeros((0, 0))

    for row_index, response_id in enumerate(matrix.response_ids):
        row = matrix.values[row_index, :]
        code_set = tuple(matrix.code_names[j] for j in range(matrix.n_codes) if row[j])
        signature = tuple(sorted({family_of(c) for c in code_set}))
        signatures[response_id] = signature

        order = sorted(
            range(matrix.n_responses),
            key=lambda j: (-float(response_jaccard[row_index, j]), matrix.response_ids[j]),
        )
        # A response with no codes has no pattern, so it has nothing to be near: the
        # three mates it used to collect all scored Jaccard 0.0 and said only that it
        # was empty (R1 I6).
        mates = [j for j in order if j != row_index][:top_k_mates] if code_set else []
        nearest = tuple(
            NearestMate(
                response_id=matrix.response_ids[j],
                jaccard=float(response_jaccard[row_index, j]),
            )
            for j in mates
        )
        response_patterns.append(
            ResponsePattern(
                response_id=response_id,
                family_signature=signature,
                code_set=code_set,
                nearest=nearest,
            )
        )

    # Responses carrying no code at all share the empty signature and would otherwise
    # compete for "largest pattern group" and win it on any corpus built with
    # `responses=` -- the documented way to build the matrix (R1 I6). They are counted
    # on their own instead: the absence of a pattern is not a pattern.
    uncoded_response_ids = tuple(
        sorted(rid for rid in matrix.response_ids if not signatures[rid])
    )
    grouped: dict[tuple[str, ...], list[int]] = defaultdict(list)
    for response_id in matrix.response_ids:
        if not signatures[response_id]:
            continue
        grouped[signatures[response_id]].append(response_id)

    groups = sorted(
        (
            PatternGroup(family_signature=sig, response_ids=tuple(sorted(ids)))
            for sig, ids in grouped.items()
            if len(ids) >= 2
        ),
        key=lambda g: (-g.size, g.family_signature),
    )
    singleton_response_ids = tuple(
        sorted(ids[0] for ids in grouped.values() if len(ids) == 1)
    )

    code_cooccurrence = _cooccurrence(matrix.code_names, matrix.values)
    family_names, family_values = _family_occurrence(matrix)
    family_cooccurrence = _cooccurrence(family_names, family_values)

    combos = _combinations(
        matrix.code_names,
        matrix.values,
        code_cooccurrence.counts,
        matrix.n_responses,
        min_support,
        max_triple_candidates,
    )

    return PatternReport(
        n_responses=matrix.n_responses,
        n_codes=matrix.n_codes,
        filter=matrix.filter,
        min_support=min_support,
        responses=tuple(response_patterns),
        groups=tuple(groups),
        singleton_response_ids=singleton_response_ids,
        code_cooccurrence=code_cooccurrence,
        family_cooccurrence=family_cooccurrence,
        combinations=combos,
        uncoded_response_ids=uncoded_response_ids,
    )
