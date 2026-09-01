"""The geometry: cosine, optimal assignment, top-k retrieval, and the routing band.

This module is the direct answer to a documented failure. The predecessor study matched
two coders' codebooks with TF-IDF cosine blended with word-set Jaccard (0.6/0.4) at a
single threshold of 0.3, **greedily**, and recovered 21 matched pairs against 66 and 73
codes left unmatched (Ng & Chan 2026, §4). Two things were wrong with that: lexical
overlap is not meaning (answered by `gaf.embed.service`), and greedy matching is not
matching. Greedy takes the single best pair first and then lives with whatever is left,
so one strong pair can force several weak ones; `hungarian_match` solves the assignment
problem outright with `scipy.optimize.linear_sum_assignment`.

Three rules hold everywhere in here:

* codes are rendered by `gaf.embed.protocol.code_text` and never by hand — a code
  embedded one way for retrieval and another way for dedup would silently break every
  threshold in `CodingRules`;
* the bands come from `gaf.embed.protocol.route_similarity` and are not redefined —
  MERGE / JUDGE / CREATE is a three-way outcome declared in exactly one place;
* every score carries the `space_id` it was computed in, because scores from different
  spaces are not comparable.

Ties are broken deterministically (score, then name, then index) so that two runs of the
same batch produce the same pairs in the same order.

Validation principles: **reliability** — an optimal assignment is a defined answer, a
greedy one is an artefact of iteration order; **interpretive depth** — the unmatched
lists are returned rather than discarded, because what two coders *failed* to agree on
is the finding, not the residue.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment

from gaf.embed.protocol import Embedder, Route, code_text, cosine, route_similarity
from gaf.models import Codebook

__all__ = [
    "EmbedFn",
    "Embedder",
    "Match",
    "MatchResult",
    "Route",
    "ScoredCode",
    "code_text",
    "cosine",
    "cosine_matrix",
    "hungarian_match",
    "route_similarity",
    "top_k_codes",
]

#: Anything that turns a batch of strings into a row-per-string array of unit vectors.
#: `EmbeddingService.embed` and `StubEmbedder.embed` both satisfy it.
EmbedFn = Callable[[Sequence[str]], np.ndarray]


# --------------------------------------------------------------------------- #
# Cosine
# --------------------------------------------------------------------------- #


def cosine_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """All-pairs cosine similarity between two batches of **L2-normalised** rows.

    On unit vectors cosine is a dot product, so this is one matrix multiply — which is
    the whole reason the design law can say "a NumPy matrix and cosine similarity are
    sufficient at this corpus size" and mean it. The result is clipped into ``[-1, 1]``
    to absorb floating-point overshoot, so a score is never 1.0000000000000002 and a
    threshold comparison never depends on rounding.

    Callers pass normalised inputs; `Embedder` guarantees them. Rows that are all zero
    (a code text with no features at all) yield 0.0 against everything, matching
    `gaf.embed.protocol.cosine`.
    """
    left = np.atleast_2d(np.asarray(a, dtype=np.float64))
    right = np.atleast_2d(np.asarray(b, dtype=np.float64))
    if left.size == 0 or right.size == 0:
        return np.zeros((left.shape[0], right.shape[0]), dtype=np.float64)
    if left.shape[1] != right.shape[1]:
        raise ValueError(
            f"dimension mismatch: {left.shape[1]} vs {right.shape[1]}; "
            "scores from different embedding spaces are not comparable"
        )
    return np.clip(left @ right.T, -1.0, 1.0)


def _resolve(embed_fn: EmbedFn | Embedder) -> tuple[EmbedFn, str]:
    """Accept either a bare callable or a full `Embedder`, and recover the space id."""
    if isinstance(embed_fn, Embedder):
        return embed_fn.embed, embed_fn.space_id
    return embed_fn, ""


# --------------------------------------------------------------------------- #
# Cross-coder matching
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class Match:
    """One assigned pair, with the score and the band it fell in."""

    index_a: int
    index_b: int
    label_a: str
    label_b: str
    score: float
    route: Route
    space_id: str = ""

    def to_json(self) -> dict[str, Any]:
        return {
            "index_a": self.index_a,
            "index_b": self.index_b,
            "label_a": self.label_a,
            "label_b": self.label_b,
            "score": self.score,
            "route": self.route.value,
            "space_id": self.space_id,
        }


@dataclass(frozen=True, slots=True)
class MatchResult:
    """The optimal assignment, plus what it could not pair on either side.

    `unmatched_a` and `unmatched_b` are ``(index, label)`` pairs so a caller can map
    back to its own objects exactly, and a report can print a name without a lookup.
    """

    matches: list[Match]
    unmatched_a: list[tuple[int, str]]
    unmatched_b: list[tuple[int, str]]
    space_id: str = ""

    @property
    def matched_count(self) -> int:
        return len(self.matches)

    def by_route(self, route: Route) -> list[Match]:
        return [m for m in self.matches if m.route is route]

    def mean_score(self) -> float:
        """Mean similarity over matched pairs; 0.0 when nothing matched."""
        return float(np.mean([m.score for m in self.matches])) if self.matches else 0.0

    def to_json(self) -> dict[str, Any]:
        return {
            "space_id": self.space_id,
            "matches": [m.to_json() for m in self.matches],
            "unmatched_a": [[i, label] for i, label in self.unmatched_a],
            "unmatched_b": [[i, label] for i, label in self.unmatched_b],
        }


def hungarian_match(
    items_a: Sequence[str],
    items_b: Sequence[str],
    embed_fn: EmbedFn | Embedder,
    tau_high: float,
    tau_low: float,
) -> MatchResult:
    """Optimally pair two lists of rendered texts, and band each pair.

    `items_a` and `items_b` are the strings to embed — for codes and candidates that
    means `code_text(name, description)`, rendered by the caller so that this function
    never has to know which of the two it is looking at. Positions are preserved, so a
    `Match` maps straight back to the caller's own objects by index.

    The assignment maximises total similarity via `scipy.optimize.linear_sum_assignment`
    rather than repeatedly taking the best remaining pair. Those differ, and they differ
    in the direction that matters: greedy can consume a code that was the only good
    partner for something else, and then report both as unmatched.

    A pair the assignment produced but whose score falls **below `tau_low`** is not a
    match — the solver has to pair everything it can, but "certainly different" is one
    of the three declared outcomes. Such pairs are dissolved and both sides join the
    unmatched lists. Surviving pairs are banded MERGE (>= `tau_high`) or JUDGE (the grey
    zone), by `route_similarity`, which is the only definition of those bands.

    Returns matches sorted by descending score, then by `label_a`, then by index, so the
    order is a fact about the data rather than about the solver.
    """
    if tau_low > tau_high:
        raise ValueError(f"tau_low ({tau_low}) must not exceed tau_high ({tau_high})")
    embed, space_id = _resolve(embed_fn)
    labels_a, labels_b = list(items_a), list(items_b)
    if not labels_a or not labels_b:
        return MatchResult(
            matches=[],
            unmatched_a=list(enumerate(labels_a)),
            unmatched_b=list(enumerate(labels_b)),
            space_id=space_id,
        )

    scores = cosine_matrix(embed(labels_a), embed(labels_b))
    rows, cols = linear_sum_assignment(-scores)

    matches: list[Match] = []
    paired_a: set[int] = set()
    paired_b: set[int] = set()
    for row, col in zip(rows.tolist(), cols.tolist(), strict=True):
        score = float(scores[row, col])
        if score < tau_low:
            continue  # certainly different: the solver had to pair them, we do not
        paired_a.add(row)
        paired_b.add(col)
        matches.append(
            Match(
                index_a=row,
                index_b=col,
                label_a=labels_a[row],
                label_b=labels_b[col],
                score=score,
                route=route_similarity(score, tau_high, tau_low),
                space_id=space_id,
            )
        )
    matches.sort(key=lambda m: (-m.score, m.label_a, m.index_a))

    return MatchResult(
        matches=matches,
        unmatched_a=[(i, label) for i, label in enumerate(labels_a) if i not in paired_a],
        unmatched_b=[(i, label) for i, label in enumerate(labels_b) if i not in paired_b],
        space_id=space_id,
    )


# --------------------------------------------------------------------------- #
# Retrieval over a codebook
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class ScoredCode:
    """One retrieved code and its similarity to the query, in a named space."""

    code_id: str
    name: str
    score: float
    space_id: str = ""

    def to_json(self) -> dict[str, Any]:
        return {
            "code_id": self.code_id,
            "name": self.name,
            "score": self.score,
            "space_id": self.space_id,
        }


def top_k_codes(
    query: str,
    codebook: Codebook,
    embedder: Embedder,
    k: int = 8,
) -> list[ScoredCode]:
    """The `k` codes in `codebook` nearest to `query`, best first.

    This is the context-assembly step of the fast loop: deterministic code decides what
    a coder gets to see, before any model is called. Codes are rendered by `code_text`,
    the single rendering function, so retrieval, the dedup gate and cross-coder matching
    all measure the same object.

    `query` is embedded as given — a caller comparing a *candidate* against the codebook
    renders it with `code_text` first, so that both sides of the comparison have the
    same shape. Ties break by name and then by code id, so a codebook with two equally
    close codes retrieves them in a stable order.
    """
    if k <= 0:
        return []
    codes = codebook.sorted_codes()
    if not codes:
        return []
    texts = [code_text(code.name, code.description) for code in codes]
    scores = cosine_matrix(embedder.embed_one(query), embedder.embed(texts))[0]
    ranked = sorted(
        (
            ScoredCode(
                code_id=code.id,
                name=code.name,
                score=float(score),
                space_id=embedder.space_id,
            )
            for code, score in zip(codes, scores.tolist(), strict=True)
        ),
        key=lambda scored: (-scored.score, scored.name, scored.code_id),
    )
    return ranked[:k]
