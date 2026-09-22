"""Crosswalk: Hungarian assignment, unconstrained nearest neighbour, family roll-up.

A small, fully hand-derivable scenario drives the main tests: four source leaves in
two families, three target leaves in three families, embedded with a tiny fixed-vector
stub (not the hashed lexical fallback) so every cosine, band and roll-up is exact
arithmetic rather than something a reviewer has to trust.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np
import pytest

from gaf.analysis.crosswalk import build_crosswalk
from gaf.config import CodingRules
from gaf.models import Code, Codebook
from tests.fixtures.embedding import StubEmbedder

RULES = CodingRules()  # tau_high=0.80, tau_low=0.45


def _leaf(name: str, description: str = "") -> Code:
    return Code(id=f"c-{name}", name=name, description=description)


def _codebook(*names: str) -> Codebook:
    codes = [_leaf(name) for name in names]
    return Codebook(codes={c.id: c for c in codes})


class _FixedVectorEmbedder:
    """A minimal `Embedder` returning hand-chosen vectors, keyed by exact text.

    Not the lexical fallback: every cosine in these tests is chosen geometry, not a
    hash. `space_id` deliberately does not start with "lexical".
    """

    def __init__(self, vectors: dict[str, np.ndarray]) -> None:
        self._vectors = {text: v / np.linalg.norm(v) for text, v in vectors.items()}
        self._dim = len(next(iter(vectors.values())))

    @property
    def space_id(self) -> str:
        return "fixed-vector-test-space"

    @property
    def dim(self) -> int:
        return self._dim

    def embed_one(self, text: str) -> np.ndarray:
        return self._vectors[text]

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        return np.vstack([self._vectors[t] for t in texts])


# --------------------------------------------------------------------------- #
# The hand-derivable scenario
# --------------------------------------------------------------------------- #
#
# Source leaves (family in parens): benefit_family-benefit (benefit_family),
# danger_family-risk_a / -risk_b / -risk_c (danger_family, all three).
# Target leaves: danger_side-danger, gain_side-gain, mystery_side-mystery — one
# leaf per family.
#
# Vectors (angles from the danger axis, in the xy-plane; benefit sits on a third,
# orthogonal axis so it is equidistant — cosine exactly 0.0 — from every target):
#   danger_side-danger      = (1, 0, 0)
#   gain_side-gain          = (0, 1, 0)
#   mystery_side-mystery    = (-1, 0, 0)
#   danger_family-risk_a    = (1, 0, 0)                    cos(danger)=1.0
#   danger_family-risk_b    = (cos 40 deg, sin 40 deg, 0)   cos(danger)~0.766, cos(gain)~0.643
#   danger_family-risk_c    = (0, 1, 0)                     cos(gain)=1.0
#   benefit_family-benefit  = (0, 0, 1)                     cos = 0.0 with every target
#
# tau_high=0.80, tau_low=0.45, so: risk_a -> danger is "same" (1.0); risk_b -> danger
# is "grey" (0.766, and closer to danger than to gain's 0.643); risk_c -> gain is
# "same" (1.0); benefit -> everything is "unmapped" (0.0).
_ANGLE = math.radians(40)


def _scenario() -> tuple[Codebook, Codebook, _FixedVectorEmbedder]:
    source = _codebook(
        "benefit_family-benefit",
        "danger_family-risk_a",
        "danger_family-risk_b",
        "danger_family-risk_c",
    )
    target = _codebook("danger_side-danger", "gain_side-gain", "mystery_side-mystery")
    embedder = _FixedVectorEmbedder(
        {
            "danger_side-danger": np.array([1.0, 0.0, 0.0]),
            "gain_side-gain": np.array([0.0, 1.0, 0.0]),
            "mystery_side-mystery": np.array([-1.0, 0.0, 0.0]),
            "danger_family-risk_a": np.array([1.0, 0.0, 0.0]),
            "danger_family-risk_b": np.array([math.cos(_ANGLE), math.sin(_ANGLE), 0.0]),
            "danger_family-risk_c": np.array([0.0, 1.0, 0.0]),
            "benefit_family-benefit": np.array([0.0, 0.0, 1.0]),
        }
    )
    return source, target, embedder


def _by_source(crosswalk: object, name: str) -> object:
    return next(m for m in crosswalk.mappings if m.source == name)  # type: ignore[attr-defined]


# --------------------------------------------------------------------------- #
# Bands
# --------------------------------------------------------------------------- #


def test_perfect_match_bands_as_same_on_both_mappings() -> None:
    source, target, embedder = _scenario()
    result = build_crosswalk(source, target, embedder, RULES)
    mapping = _by_source(result, "danger_family-risk_a")
    assert mapping.hungarian.target == "danger_side-danger"
    assert mapping.hungarian.score == pytest.approx(1.0)
    assert mapping.hungarian.band == "same"
    assert mapping.nearest.target == "danger_side-danger"
    assert mapping.nearest.score == pytest.approx(1.0)
    assert mapping.nearest.band == "same"


def test_grey_band_and_nearest_prefers_the_closer_target() -> None:
    source, target, embedder = _scenario()
    result = build_crosswalk(source, target, embedder, RULES)
    mapping = _by_source(result, "danger_family-risk_b")
    # nearest must pick danger (cos 40 deg ~ 0.766) over gain (cos 50 deg ~ 0.643)
    assert mapping.nearest.target == "danger_side-danger"
    assert mapping.nearest.score == pytest.approx(math.cos(_ANGLE))
    assert mapping.nearest.band == "grey"
    # left out of the Hungarian assignment entirely (rectangular leftover — see below)
    assert mapping.hungarian.target is None
    assert mapping.hungarian.score is None
    assert mapping.hungarian.band is None


def test_unmapped_band_is_an_invention() -> None:
    source, target, embedder = _scenario()
    result = build_crosswalk(source, target, embedder, RULES)
    mapping = _by_source(result, "benefit_family-benefit")
    assert mapping.nearest.score == pytest.approx(0.0)
    assert mapping.nearest.band == "unmapped"
    assert result.unmapped_source_leaves == ("benefit_family-benefit",)


def test_hungarian_assignment_optimises_total_similarity_over_the_rectangle() -> None:
    """4 source leaves x 3 target leaves: the optimal 3-pair total is 2.0 (risk_a-danger
    at 1.0, risk_c-gain at 1.0, benefit-mystery at 0.0), which leaves risk_b — whose
    best own score (0.766) is smaller than what pairing it instead would cost the
    total — out of the assignment altogether."""
    source, target, embedder = _scenario()
    result = build_crosswalk(source, target, embedder, RULES)
    assert _by_source(result, "danger_family-risk_c").hungarian.target == "gain_side-gain"
    assert _by_source(result, "danger_family-risk_c").hungarian.band == "same"
    # benefit's Hungarian pairing (mystery, score 0.0) is below tau_low and dissolved
    assert _by_source(result, "benefit_family-benefit").hungarian.target is None


# --------------------------------------------------------------------------- #
# Granularity, blind spots and inventions
# --------------------------------------------------------------------------- #


def test_two_source_leaves_land_on_the_same_nearest_target() -> None:
    """The granularity finding: risk_a and risk_b both nearest-map to danger_side."""
    source, target, embedder = _scenario()
    result = build_crosswalk(source, target, embedder, RULES)
    landers = [
        m.source
        for m in result.mappings
        if m.nearest.target == "danger_side-danger" and m.nearest.band != "unmapped"
    ]
    assert sorted(landers) == ["danger_family-risk_a", "danger_family-risk_b"]


def test_blind_spot_is_the_target_leaf_nobody_maps_to() -> None:
    source, target, embedder = _scenario()
    result = build_crosswalk(source, target, embedder, RULES)
    assert result.unmapped_target_leaves == ("mystery_side-mystery",)


# --------------------------------------------------------------------------- #
# Family roll-up
# --------------------------------------------------------------------------- #


def test_source_family_rollup_shows_the_scattered_family() -> None:
    source, target, embedder = _scenario()
    result = build_crosswalk(source, target, embedder, RULES)
    by_family = {r.family: r for r in result.source_family_rollup}

    benefit = by_family["benefit_family"]
    assert benefit.n_leaves == 1
    assert benefit.distribution == {}
    assert benefit.n_unmapped == 1
    assert benefit.scattered is False

    danger = by_family["danger_family"]
    assert danger.n_leaves == 3
    # risk_a and risk_b both land in danger_side; risk_c lands in gain_side
    assert danger.distribution == {"danger_side": 2, "gain_side": 1}
    assert danger.n_unmapped == 0
    assert danger.scattered is True
    assert danger.n_other_families == 2


def test_target_family_rollup_is_the_mirror_and_names_the_blind_spot() -> None:
    source, target, embedder = _scenario()
    result = build_crosswalk(source, target, embedder, RULES)
    by_family = {r.family: r for r in result.target_family_rollup}

    assert by_family["danger_side"].distribution == {"danger_family": 2}
    assert by_family["danger_side"].n_leaves == 1
    assert by_family["danger_side"].n_blind_spots == 0
    assert by_family["gain_side"].distribution == {"danger_family": 1}
    assert by_family["gain_side"].n_blind_spots == 0
    assert by_family["mystery_side"].distribution == {}
    assert by_family["mystery_side"].n_blind_spots == 1


# --------------------------------------------------------------------------- #
# names_only and the fairness note (ADR-0029)
# --------------------------------------------------------------------------- #


def test_names_only_ignores_an_asymmetric_description() -> None:
    """Same name on both sides, but the source carries a long, unrelated description.

    With names_only=True both sides render identically (`code_text(name, "")`), so a
    real embedder (the lexical stub, not the fixed-vector one) must score them 1.0.
    Without it, the differing description depresses the score below 1.0.
    """
    source = _codebook_with_description(
        "concept-x", "A long description mentioning elephants, rainfall and ledgers."
    )
    target = _codebook_with_description("concept-x", "")
    embedder = StubEmbedder()

    exact = build_crosswalk(source, target, embedder, RULES, names_only=True)
    mapping = exact.mappings[0]
    assert mapping.nearest.score == pytest.approx(1.0)
    assert mapping.nearest.band == "same"
    assert "names only" in exact.fair_mode_note

    with_descriptions = build_crosswalk(source, target, embedder, RULES, names_only=False)
    assert with_descriptions.mappings[0].nearest.score < 1.0
    assert exact.source_has_descriptions is True
    assert exact.target_has_descriptions is False
    assert "ADR-0029" in with_descriptions.fair_mode_note


def _codebook_with_description(name: str, description: str) -> Codebook:
    code = _leaf(name, description)
    return Codebook(codes={code.id: code})


def test_fair_mode_note_when_both_sides_symmetric() -> None:
    source = _codebook("a-one")
    target = _codebook("b-one")
    result = build_crosswalk(source, target, StubEmbedder(), RULES)
    assert result.source_has_descriptions is False
    assert result.target_has_descriptions is False
    assert "no fairness gap" in result.fair_mode_note


# --------------------------------------------------------------------------- #
# Degenerate sizes
# --------------------------------------------------------------------------- #


def test_empty_target_codebook_is_not_an_error() -> None:
    source = _codebook("a-one", "a-two")
    target = Codebook(codes={})
    result = build_crosswalk(source, target, StubEmbedder(), RULES)
    assert len(result.mappings) == 2
    for mapping in result.mappings:
        assert mapping.nearest.target is None
        assert mapping.nearest.band == "unmapped"
        assert mapping.hungarian.target is None
    assert result.unmapped_target_leaves == ()
    assert set(result.unmapped_source_leaves) == {"a-one", "a-two"}


def test_empty_source_codebook_is_not_an_error() -> None:
    source = Codebook(codes={})
    target = _codebook("b-one")
    result = build_crosswalk(source, target, StubEmbedder(), RULES)
    assert result.mappings == ()
    assert result.unmapped_target_leaves == ("b-one",)
    assert result.source_family_rollup == ()


# --------------------------------------------------------------------------- #
# Determinism and markdown
# --------------------------------------------------------------------------- #


def test_to_json_str_is_byte_identical_across_calls() -> None:
    source, target, embedder = _scenario()
    first = build_crosswalk(source, target, embedder, RULES).to_json_str()
    second = build_crosswalk(source, target, embedder, RULES).to_json_str()
    assert first == second


def test_markdown_names_blind_spots_and_inventions() -> None:
    source, target, embedder = _scenario()
    result = build_crosswalk(source, target, embedder, RULES)
    text = result.to_markdown()
    assert "Blind spots" in text
    assert "mystery_side-mystery" in text
    assert "Inventions" in text
    assert "benefit_family-benefit" in text


# --------------------------------------------------------------------------- #
# R1 audit findings
# --------------------------------------------------------------------------- #


def test_the_fairness_flags_are_computed_over_the_leaves_actually_compared() -> None:
    """R1 C5. A described *parent* is not a described leaf, and only leaves are embedded."""
    parent = Code(id="c-m", name="m", description="A family carrying a description of its own.")
    leaf = Code(id="c-m-one", name="m-one", description="", parent_id=parent.id)
    source = Codebook(codes={parent.id: parent, leaf.id: leaf})
    target = _codebook_with_description("m-one", "A description on the target side.")

    result = build_crosswalk(source, target, StubEmbedder(), RULES)
    assert result.source_has_descriptions is False, "its only leaf is bare"
    assert result.target_has_descriptions is True
    assert "ADR-0029" in result.fair_mode_note
    assert "no fairness gap" not in result.fair_mode_note

    fair = build_crosswalk(source, target, StubEmbedder(), RULES, names_only=True)
    assert fair.mappings[0].nearest.score == pytest.approx(1.0)
    assert fair.mappings[0].nearest.band == "same"


def test_partial_description_coverage_is_not_reported_as_a_fair_comparison() -> None:
    """R1 C5. `any()` over the leaves is still not "both sides carry descriptions"."""
    described = Code(id="c-a", name="a-one", description="One leaf carries a description.")
    bare = Code(id="c-b", name="a-two", description="")
    source = Codebook(codes={described.id: described, bare.id: bare})
    target = Codebook(
        codes={
            "t1": Code(id="t1", name="b-one", description="Described."),
            "t2": Code(id="t2", name="b-two", description="Described too."),
        }
    )
    result = build_crosswalk(source, target, StubEmbedder(), RULES)
    assert (result.source_described_leaves, result.n_source_leaves) == (1, 2)
    assert (result.target_described_leaves, result.n_target_leaves) == (2, 2)
    assert "1 of 2" in result.fair_mode_note and "2 of 2" in result.fair_mode_note
    assert "no fairness gap" not in result.fair_mode_note


def test_the_target_rollup_has_its_own_column_names_and_reconciles() -> None:
    """R1 I7. Three populations under one set of headers do not add up."""
    source, target, embedder = _scenario()
    result = build_crosswalk(source, target, embedder, RULES)
    by_family = {r.family: r for r in result.target_family_rollup}

    danger = by_family["danger_side"]
    assert danger.n_leaves == 1, "one target leaf in this family"
    assert danger.distribution == {"danger_family": 2}
    assert danger.n_source_leaves == 2 and danger.n_source_families == 1
    assert danger.n_blind_spots == 0
    assert danger.drawn_from_several_families is False

    mystery = by_family["mystery_side"]
    assert mystery.n_leaves == 1 and mystery.n_source_leaves == 0
    assert mystery.n_blind_spots == 1, "nothing maps onto it"
    assert mystery.n_leaves == mystery.n_blind_spots + len(
        [n for n in ("mystery_side-mystery",) if n not in result.unmapped_target_leaves]
    )

    markdown = result.to_markdown()
    assert "| target family | target leaves | source leaves landing here |" in markdown
    assert "| family | leaves | scattered | distribution | unmapped |" in markdown, (
        "the source table keeps its own headers"
    )
    payload = result.to_json()["target_family_rollup"][0]
    assert set(payload) == {
        "family",
        "n_leaves",
        "distribution",
        "n_source_leaves",
        "n_source_families",
        "drawn_from_several_families",
        "n_blind_spots",
    }


def test_an_empty_target_reports_no_score_rather_than_a_measured_zero() -> None:
    """R1 Minor. 0.0 reads as a measurement; there was nothing to measure."""
    source = _codebook("a-one")
    result = build_crosswalk(source, Codebook(codes={}), StubEmbedder(), RULES)
    assert result.mappings[0].nearest.score is None
    assert result.mappings[0].nearest.band == "unmapped"
    assert "—" in result.to_markdown()


def test_a_score_exactly_at_tau_high_is_same_and_exactly_at_tau_low_is_grey() -> None:
    """R1, weak-test scan: no test sat on either boundary, so neither was pinned."""
    import math

    rules = CodingRules()
    source = _codebook("s-high", "s-low")
    target = _codebook("t-axis")
    embedder = _FixedVectorEmbedder(
        {
            "t-axis": np.array([1.0, 0.0]),
            "s-high": np.array([rules.tau_high, math.sqrt(1.0 - rules.tau_high**2)]),
            "s-low": np.array([rules.tau_low, math.sqrt(1.0 - rules.tau_low**2)]),
        }
    )
    result = build_crosswalk(source, target, embedder, rules)
    by_name = {m.source: m for m in result.mappings}
    assert by_name["s-high"].nearest.score == pytest.approx(rules.tau_high)
    assert by_name["s-high"].nearest.band == "same", "tau_high is inclusive"
    assert by_name["s-low"].nearest.score == pytest.approx(rules.tau_low)
    assert by_name["s-low"].nearest.band == "grey", "tau_low is the bottom of the grey band"
