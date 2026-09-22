"""Crosswalk: mapping one codebook's organisation onto another's.

The typical use is the machine's cold codebook as ``source`` and the PI's own
codebook as ``target`` — "how would my codes sit inside his organisation?" — but
nothing here assumes a direction; the same function run with the arguments swapped
answers the mirror question. This is a *view*: nothing here edits either codebook, and
nothing here restructures anything. Restructuring happens only behind the human gate
in the slow loop.

**Two mappings, on purpose, because one hides what the other shows.** For every
source leaf: a **Hungarian assignment** (:func:`gaf.embed.matcher.hungarian_match`,
reused rather than reimplemented) globally optimal and one-to-one, and the
**unconstrained nearest neighbour** — every source leaf compared against every target
leaf independently, with no one-to-one constraint at all. The Hungarian assignment is
the fair comparison; the unconstrained one is where the interesting finding lives,
because several source leaves landing on the same nearest target is informative about
granularity (the source codebook drew more distinctions than the target did over the
same territory) and the Hungarian assignment, being one-to-one, cannot show it at all.

**Bands, reused, not redefined.** ``same`` (score >= ``tau_high``), ``grey`` (between)
and ``unmapped`` (score < ``tau_low``) are exactly ``Route.MERGE`` / ``Route.JUDGE`` /
``Route.CREATE`` from :func:`gaf.embed.protocol.route_similarity`, under names that
fit a cross-codebook comparison rather than an integration decision. The threshold
comparison itself is not reimplemented; only the label is renamed.

**Family roll-up.** For each source family, the distribution of its leaves' *nearest*
target family (the unconstrained mapping, because the Hungarian one enforces a single
target per source leaf and would flatten the very scatter this is meant to show); a
family whose leaves scatter over several target families is reported as such
(``scattered``). The reverse direction answers the mirror question and has its own
shape, :class:`TargetFamilyRollup`, with its own column names: a target family's
``n_leaves`` are *target* leaves, its ``distribution`` counts *source* leaves landing
there, and ``n_blind_spots`` is the target leaves nothing maps onto. Sharing one
dataclass put three populations under one set of headers and made the target table
fail to reconcile (R1 I7).

**Fairness of the comparison (ADR-0029).** A name-plus-description vector compared
against a name-only vector depresses the similarity of genuinely identical concepts —
observed directly on the PI's own highlights export, where a name-only encoding scored
an identical pair at 1.000 and the same pair scored 0.4-0.7 once one side carried a
description and the other did not. ``names_only=True`` renders every leaf with
``code_text(name, "")`` on both sides; the result records how many of the **leaves
actually compared** carry a description on each side, and says in ``fair_mode_note``
whether the mode used is the fair one. Coverage rather than presence: a described
parent is not a described leaf, and one described leaf in a hundred is not a
symmetrical comparison (R1 C5).

Output is code names, family names, scores and bands. No respondent text is anywhere
near either codebook's leaves, so none can reach this module.

Validation principles: **interpretive depth** (the unconstrained mapping and the
granularity finding it enables) and **transparency** (every band, every roll-up and
the fairness of the comparison are named as what they are).
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Literal

import numpy as np

from gaf.analysis.agreement import descriptions_from_codebook
from gaf.config import CodingRules
from gaf.embed.matcher import cosine_matrix, hungarian_match
from gaf.embed.protocol import Embedder, code_text, route_similarity
from gaf.models import Codebook, family_of

__all__ = [
    "Band",
    "Crosswalk",
    "CrosswalkMatch",
    "FamilyRollup",
    "LeafMapping",
    "TargetFamilyRollup",
    "build_crosswalk",
]

#: The three bands a score can fall in, renamed from `gaf.embed.protocol.Route` for a
#: cross-codebook comparison: `same` is `Route.MERGE`, `grey` is `Route.JUDGE`,
#: `unmapped` is `Route.CREATE`. The threshold arithmetic is not reimplemented.
Band = Literal["same", "grey", "unmapped"]

_ROUTE_TO_BAND: dict[str, Band] = {"MERGE": "same", "JUDGE": "grey", "CREATE": "unmapped"}


def _band(score: float, tau_high: float, tau_low: float) -> Band:
    route = route_similarity(score, tau_high, tau_low)
    return _ROUTE_TO_BAND[route.value]


# --------------------------------------------------------------------------- #
# Per-leaf mapping
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class CrosswalkMatch:
    """One candidate target for a source leaf: which one, what score, what band.

    ``target`` and ``band`` are ``None`` together only for the Hungarian side, and
    only when the source leaf was not part of the optimal one-to-one assignment at
    all — dissolved because its best pairing scored below ``tau_low``, or left over
    because the two codebooks have different numbers of leaves.

    On the nearest side a ``score`` of ``None`` beside a ``band`` of ``unmapped``
    means the target codebook has no leaves at all: there was nothing to measure, and
    the band states that rather than banding a placeholder.
    """

    target: str | None
    score: float | None
    band: Band | None

    def to_json(self) -> dict[str, Any]:
        return {"target": self.target, "score": self.score, "band": self.band}


@dataclass(frozen=True, slots=True)
class LeafMapping:
    """One source leaf, its Hungarian assignment, and its unconstrained nearest match."""

    source: str
    hungarian: CrosswalkMatch
    nearest: CrosswalkMatch

    def to_json(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "hungarian": self.hungarian.to_json(),
            "nearest": self.nearest.to_json(),
        }


# --------------------------------------------------------------------------- #
# Family roll-up
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class FamilyRollup:
    """One family's leaves, distributed over the other codebook's families.

    ``distribution`` is ``{other_family: n_leaves}``. ``scattered`` is true when the
    family's mapped leaves land in more than one family on the other side — the
    granularity finding this roll-up exists to surface.
    """

    family: str
    n_leaves: int
    distribution: dict[str, int]
    n_unmapped: int

    @property
    def n_other_families(self) -> int:
        return len(self.distribution)

    @property
    def scattered(self) -> bool:
        return self.n_other_families >= 2

    def to_json(self) -> dict[str, Any]:
        return {
            "family": self.family,
            "n_leaves": self.n_leaves,
            "distribution": dict(sorted(self.distribution.items())),
            "n_other_families": self.n_other_families,
            "scattered": self.scattered,
            "n_unmapped": self.n_unmapped,
        }


@dataclass(frozen=True, slots=True)
class TargetFamilyRollup:
    """One **target** family: how many of its leaves there are, and what reaches them.

    Deliberately not a `FamilyRollup`. Reusing that shape put three different
    populations under one set of column headers — ``n_leaves`` counted target
    leaves, ``distribution`` counted *source* leaves, ``n_unmapped`` counted target
    leaves again — so the target table did not reconcile while the source table,
    under identical headings, did (R1 I7). ``scattered`` also changed meaning between
    the two: on the source side it means "this family's leaves land in several
    families", and the mirror question here is "several families land on this one",
    which is why it is named `drawn_from_several_families`.

    ``distribution`` is ``{source_family: n_source_leaves landing in this family}``.
    ``n_blind_spots`` is the target leaves of this family that nothing maps onto.
    """

    family: str
    n_leaves: int
    distribution: dict[str, int]
    n_blind_spots: int

    @property
    def n_source_leaves(self) -> int:
        return sum(self.distribution.values())

    @property
    def n_source_families(self) -> int:
        return len(self.distribution)

    @property
    def drawn_from_several_families(self) -> bool:
        return self.n_source_families >= 2

    def to_json(self) -> dict[str, Any]:
        return {
            "family": self.family,
            "n_leaves": self.n_leaves,
            "distribution": dict(sorted(self.distribution.items())),
            "n_source_leaves": self.n_source_leaves,
            "n_source_families": self.n_source_families,
            "drawn_from_several_families": self.drawn_from_several_families,
            "n_blind_spots": self.n_blind_spots,
        }


def _family_rollup(
    leaves: tuple[str, ...], mapped_family_of_leaf: dict[str, str | None]
) -> tuple[FamilyRollup, ...]:
    """Group ``leaves`` by family, and each family's mapped leaves by the family they
    landed in (``None`` for a leaf with no defined mapping, counted as unmapped)."""
    by_family: dict[str, list[str | None]] = defaultdict(list)
    for leaf in leaves:
        by_family[family_of(leaf)].append(mapped_family_of_leaf[leaf])

    rollups: list[FamilyRollup] = []
    for family in sorted(by_family):
        landed = by_family[family]
        distribution: dict[str, int] = defaultdict(int)
        n_unmapped = 0
        for other in landed:
            if other is None:
                n_unmapped += 1
            else:
                distribution[other] += 1
        rollups.append(
            FamilyRollup(
                family=family,
                n_leaves=len(landed),
                distribution=dict(distribution),
                n_unmapped=n_unmapped,
            )
        )
    return tuple(rollups)


# --------------------------------------------------------------------------- #
# The result
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class Crosswalk:
    """The whole crosswalk dossier mapping ``source`` onto ``target``."""

    space_id: str
    names_only: bool
    tau_high: float
    tau_low: float
    source_has_descriptions: bool
    target_has_descriptions: bool
    #: How many of the leaves actually compared carry a description, per side. The
    #: booleans above are these counts reduced to "> 0" and are kept for readers of
    #: the older artefact shape; the counts are what `fair_mode_note` reasons from.
    source_described_leaves: int
    target_described_leaves: int
    fair_mode_note: str
    n_target_leaves: int
    mappings: tuple[LeafMapping, ...]
    source_family_rollup: tuple[FamilyRollup, ...]
    target_family_rollup: tuple[TargetFamilyRollup, ...]
    unmapped_target_leaves: tuple[str, ...]
    unmapped_source_leaves: tuple[str, ...]

    @property
    def n_source_leaves(self) -> int:
        return len(self.mappings)

    def to_json(self) -> dict[str, Any]:
        return {
            "space_id": self.space_id,
            "names_only": self.names_only,
            "tau_high": self.tau_high,
            "tau_low": self.tau_low,
            "source_has_descriptions": self.source_has_descriptions,
            "target_has_descriptions": self.target_has_descriptions,
            "source_described_leaves": self.source_described_leaves,
            "target_described_leaves": self.target_described_leaves,
            "fair_mode_note": self.fair_mode_note,
            "n_source_leaves": self.n_source_leaves,
            "n_target_leaves": self.n_target_leaves,
            "mappings": [m.to_json() for m in self.mappings],
            "source_family_rollup": [r.to_json() for r in self.source_family_rollup],
            "target_family_rollup": [r.to_json() for r in self.target_family_rollup],
            "unmapped_target_leaves": list(self.unmapped_target_leaves),
            "unmapped_source_leaves": list(self.unmapped_source_leaves),
        }

    def to_json_str(self) -> str:
        return json.dumps(self.to_json(), sort_keys=True, ensure_ascii=False, indent=2)

    def to_markdown(self, *, top_n: int = 25) -> str:
        lines = [
            "## Crosswalk — mapping one codebook's organisation onto another's",
            "",
            f"Embedding space `{self.space_id}`; same >= tau_high = {self.tau_high:g}, "
            f"grey between, unmapped < tau_low = {self.tau_low:g}. "
            f"names_only = {self.names_only}. {self.fair_mode_note}",
            "",
            "### Per-leaf mapping",
            "",
            "| source | Hungarian target | score | band | nearest target | score | band |",
            "|---|---|---:|---|---|---:|---|",
        ]
        for mapping in self.mappings[:top_n]:
            h, n = mapping.hungarian, mapping.nearest
            h_score = f"{h.score:.3f}" if h.score is not None else "—"
            n_score = f"{n.score:.3f}" if n.score is not None else "—"
            lines.append(
                f"| {mapping.source} | {h.target or '—'} | {h_score} | {h.band or '—'} "
                f"| {n.target or '—'} | {n_score} | {n.band or '—'} |"
            )
        if len(self.mappings) > top_n:
            lines.append("")
            lines.append(f"_Showing {top_n} of {len(self.mappings)} source leaves._")

        lines.extend(
            ["", "### Source family roll-up (nearest target family per leaf)", ""]
        )
        if not self.source_family_rollup:
            lines.append("_No leaves to roll up._")
        else:
            lines.append("| family | leaves | scattered | distribution | unmapped |")
            lines.append("|---|---:|:---:|---|---:|")
            for row in self.source_family_rollup:
                dist = ", ".join(f"{k}: {v}" for k, v in sorted(row.distribution.items())) or "—"
                lines.append(
                    f"| {row.family} | {row.n_leaves} | {'yes' if row.scattered else 'no'} "
                    f"| {dist} | {row.n_unmapped} |"
                )

        # Its own headers, because its own columns count their own populations: the
        # source table's "leaves" and this one's are different things (R1 I7).
        lines.extend(
            ["", "### Target family roll-up (nearest source family per leaf)", ""]
        )
        if not self.target_family_rollup:
            lines.append("_No leaves to roll up._")
        else:
            lines.append(
                "| target family | target leaves | source leaves landing here "
                "| source families | blind spots |"
            )
            lines.append("|---|---:|---:|---|---:|")
            for target_row in self.target_family_rollup:
                dist = (
                    ", ".join(f"{k}: {v}" for k, v in sorted(target_row.distribution.items()))
                    or "—"
                )
                lines.append(
                    f"| {target_row.family} | {target_row.n_leaves} "
                    f"| {target_row.n_source_leaves} | {dist} | {target_row.n_blind_spots} |"
                )

        lines.extend(
            [
                "",
                "### Blind spots — target leaves nothing maps to",
                "",
                ", ".join(self.unmapped_target_leaves) or "_none_",
                "",
                "### Inventions — source leaves mapping to nothing",
                "",
                ", ".join(self.unmapped_source_leaves) or "_none_",
            ]
        )
        return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Construction
# --------------------------------------------------------------------------- #


def _fair_mode_note(
    names_only: bool,
    source_described: int,
    n_source: int,
    target_described: int,
    n_target: int,
) -> str:
    """The fairness of this comparison, stated from *coverage* rather than presence.

    A boolean per side cannot say this. ``any()`` over the codebook reported "no
    fairness gap" while the leaves being compared were bare on one side (R1 C5), and
    ``any()`` over the leaves would still report it when one leaf in a hundred carries
    a description. The depression ADR-0029 measured is per pair, so what a reader
    needs is how much of each side is described.
    """
    if names_only:
        return (
            "Compared as names only, by request: fair regardless of which side "
            "carries descriptions."
        )
    source_full = n_source > 0 and source_described == n_source
    target_full = n_target > 0 and target_described == n_target
    if source_described == 0 and target_described == 0:
        return (
            "Compared as name + description on both sides (neither side's leaves carry "
            "a description); no fairness gap."
        )
    if source_full and target_full:
        return (
            "Compared as name + description on both sides (every leaf on both sides "
            "carries one); no fairness gap."
        )
    return (
        f"{source_described} of {n_source} source leaves and {target_described} of "
        f"{n_target} target leaves carry a description. A name+description vector "
        "against a name-only vector depresses the similarity of identical concepts "
        "(ADR-0029), so every pair where one side is bare is compared unfairly. "
        "names_only=True would be the fair comparison."
    )


def build_crosswalk(
    source: Codebook,
    target: Codebook,
    embedder: Embedder,
    config: CodingRules,
    *,
    names_only: bool = False,
) -> Crosswalk:
    """Map every leaf of ``source`` onto ``target``, by Hungarian assignment and by
    unconstrained nearest neighbour, banded by ``config.tau_high`` / ``config.tau_low``.

    ``names_only=True`` renders every leaf as ``code_text(name, "")`` on both sides —
    see the module docstring and ADR-0029 for why an asymmetric description makes the
    unqualified comparison unfair. Either codebook may be empty; the result is empty
    rather than an error, matching :func:`gaf.embed.matcher.hungarian_match`.
    """
    source_leaves = tuple(sorted(c.name for c in source.leaves()))
    target_leaves = tuple(sorted(c.name for c in target.leaves()))

    source_desc = descriptions_from_codebook(source)
    target_desc = descriptions_from_codebook(target)
    # Over the leaves **actually embedded**, not over every code in the codebook: a
    # described parent whose only leaf is bare set the flag and bought a "no fairness
    # gap" note for precisely the comparison the flag exists to warn about (R1 C5).
    source_described_leaves = sum(1 for n in source_leaves if source_desc.get(n, "").strip())
    target_described_leaves = sum(1 for n in target_leaves if target_desc.get(n, "").strip())
    source_has_descriptions = source_described_leaves > 0
    target_has_descriptions = target_described_leaves > 0
    fair_mode_note = _fair_mode_note(
        names_only,
        source_described_leaves,
        len(source_leaves),
        target_described_leaves,
        len(target_leaves),
    )

    def render(name: str, descriptions: dict[str, str]) -> str:
        description = "" if names_only else descriptions.get(name, "")
        return code_text(name, description)

    source_texts = [render(name, source_desc) for name in source_leaves]
    target_texts = [render(name, target_desc) for name in target_leaves]

    hungarian_result = hungarian_match(
        source_texts, target_texts, embedder, config.tau_high, config.tau_low
    )
    hungarian_by_source_index = {m.index_a: m for m in hungarian_result.matches}

    sims = (
        cosine_matrix(embedder.embed(source_texts), embedder.embed(target_texts))
        if source_leaves and target_leaves
        else None
    )

    mappings: list[LeafMapping] = []
    for i, name in enumerate(source_leaves):
        match = hungarian_by_source_index.get(i)
        if match is None:
            hungarian_field = CrosswalkMatch(target=None, score=None, band=None)
        else:
            hungarian_field = CrosswalkMatch(
                target=target_leaves[match.index_b],
                score=match.score,
                band=_band(match.score, config.tau_high, config.tau_low),
            )

        if sims is None:
            # There is no target leaf, so there is nothing to score and nothing to
            # band. `unmapped` here answers "what does this map to", not a threshold
            # comparison, so it is stated rather than routed through
            # `route_similarity` -- routing a placeholder 0.0 would make the answer
            # depend on tau_low and, at tau_low = 0, would report every source leaf as
            # `grey` and empty the "inventions" list (R1 Minor). The score is None
            # rather than 0.0 because 0.0 reads as a measurement that was never made.
            nearest_field = CrosswalkMatch(target=None, score=None, band="unmapped")
        else:
            row = sims[i]
            best_j = int(np.argmax(row))
            best_score = float(row[best_j])
            nearest_field = CrosswalkMatch(
                target=target_leaves[best_j],
                score=best_score,
                band=_band(best_score, config.tau_high, config.tau_low),
            )

        mappings.append(LeafMapping(source=name, hungarian=hungarian_field, nearest=nearest_field))

    # Family roll-up is built from the *unconstrained* mapping: the Hungarian
    # assignment is one-to-one by construction and would flatten exactly the
    # many-to-one scatter this roll-up exists to show.
    source_to_target_family: dict[str, str | None] = {
        m.source: (family_of(m.nearest.target) if m.nearest.band != "unmapped" and m.nearest.target else None)
        for m in mappings
    }
    source_family_rollup = _family_rollup(source_leaves, source_to_target_family)

    reachable_targets = {
        m.nearest.target
        for m in mappings
        if m.nearest.band != "unmapped" and m.nearest.target is not None
    }
    target_family_distribution: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for m in mappings:
        if m.nearest.band == "unmapped" or m.nearest.target is None:
            continue
        target_family_distribution[family_of(m.nearest.target)][family_of(m.source)] += 1

    target_leaves_by_family: dict[str, list[str]] = defaultdict(list)
    for name in target_leaves:
        target_leaves_by_family[family_of(name)].append(name)

    target_family_rollup = tuple(
        TargetFamilyRollup(
            family=family,
            n_leaves=len(members),
            distribution=dict(target_family_distribution.get(family, {})),
            n_blind_spots=sum(1 for leaf in members if leaf not in reachable_targets),
        )
        for family, members in sorted(target_leaves_by_family.items())
    )

    unmapped_source_leaves = tuple(
        sorted(m.source for m in mappings if m.nearest.band == "unmapped")
    )
    unmapped_target_leaves = tuple(
        sorted(name for name in target_leaves if name not in reachable_targets)
    )

    return Crosswalk(
        space_id=embedder.space_id,
        names_only=names_only,
        tau_high=config.tau_high,
        tau_low=config.tau_low,
        source_has_descriptions=source_has_descriptions,
        target_has_descriptions=target_has_descriptions,
        source_described_leaves=source_described_leaves,
        target_described_leaves=target_described_leaves,
        fair_mode_note=fair_mode_note,
        n_target_leaves=len(target_leaves),
        mappings=tuple(mappings),
        source_family_rollup=source_family_rollup,
        target_family_rollup=target_family_rollup,
        unmapped_target_leaves=unmapped_target_leaves,
        unmapped_source_leaves=unmapped_source_leaves,
    )
