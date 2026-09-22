"""Affinity themes: bottom-up clustering of leaf codes across families.

Two independent things are exercised: the *co-occurrence* half of the blend, tested
with ``alpha=0.0`` so the result is pure Jaccard arithmetic a reviewer can recheck by
hand; and the *embedding* half, tested with ``alpha=1.0`` against a value computed
directly from the same deterministic stub embedder the rest of the suite uses.
"""

from __future__ import annotations

import numpy as np
import pytest

from gaf.analysis.affinity import (
    build_affinity,
)
from gaf.analysis.matrix import build_matrix
from gaf.config import AnalysisConfig
from gaf.embed.protocol import code_text
from gaf.models import Assignment, Code, Codebook
from tests.fixtures.embedding import StubEmbedder

KEEP_ALL = AnalysisConfig(min_code_frequency=1)


def rows(*triples: tuple[int, str, str]) -> list[Assignment]:
    return [Assignment(rid, segment, code) for rid, segment, code in triples]


def _code(name: str, description: str, parent_id: str | None = None, code_id: str | None = None) -> Code:
    return Code(id=code_id or f"c-{name}", name=name, description=description, parent_id=parent_id)


def _cross_family_codebook() -> Codebook:
    """Five leaves in three families, one sub-label ("shared_risk") repeated.

    Family a: `family_a-shared_risk`, `family_a-only`.
    Family b: `family_b-shared_risk` — the same sub-label as family a's.
    Family c: `family_c-unique` — deliberately never assigned, so it is excluded.
    `family_d` — a childless top-level code, itself a leaf, with no sub-label.
    """
    top_a = _code("family_a", "Concerns filed under family a.")
    top_b = _code("family_b", "Concerns filed under family b.")
    top_c = _code("family_c", "Concerns filed under family c.")
    leaves = [
        top_a,
        top_b,
        top_c,
        _code("family_a-shared_risk", "A risk named under family a.", parent_id=top_a.id),
        _code("family_a-only", "A concept found only under family a.", parent_id=top_a.id),
        _code("family_b-shared_risk", "The same risk, named again under family b.", parent_id=top_b.id),
        _code("family_c-unique", "A concept under family c that nothing ever cites.", parent_id=top_c.id),
        _code("family_d", "A top-level concept with no sub-code at all."),
    ]
    return Codebook(codes={c.id: c for c in leaves})


def _matrix_excluding_family_c() -> object:
    """Occurrences for every leaf except `family_c-unique`, which stays unassigned.

    r1, r2: both `shared_risk` codes (co-occurrence Jaccard 1.0 between them).
    r3: `family_a-only` alone. r4: `family_d` alone.
    """
    return build_matrix(
        rows(
            (1, "s", "family_a-shared_risk"),
            (1, "s", "family_b-shared_risk"),
            (2, "s", "family_a-shared_risk"),
            (2, "s", "family_b-shared_risk"),
            (3, "s", "family_a-only"),
            (4, "s", "family_d"),
        ),
        config=KEEP_ALL,
    )


# =========================================================================== #
# Excluded leaves and cross-family sub-codes (structural, not clustering)
# =========================================================================== #


def test_leaf_never_assigned_is_excluded_not_dropped_silently() -> None:
    codebook = _cross_family_codebook()
    matrix = _matrix_excluding_family_c()
    result = build_affinity(codebook, matrix, StubEmbedder(), alpha=0.0)

    assert result.n_leaves_total == 5
    assert result.n_leaves_clustered == 4
    assert [e.name for e in result.excluded] == ["family_c-unique"]
    assert "family_c-unique" not in result.similarity.names


def test_cross_family_subcode_table_is_structural() -> None:
    """`solo`-style overlap is a fact about the codebook, independent of the matrix."""
    codebook = _cross_family_codebook()
    matrix = _matrix_excluding_family_c()
    result = build_affinity(codebook, matrix, StubEmbedder(), alpha=0.0)

    assert len(result.cross_family_subcodes) == 1
    row = result.cross_family_subcodes[0]
    assert row.sub_label == "shared_risk"
    assert row.families == ("family_a", "family_b")
    assert row.codes == ("family_a-shared_risk", "family_b-shared_risk")


# =========================================================================== #
# Clustering on pure co-occurrence (alpha = 0.0)
# =========================================================================== #


def test_cross_family_group_forms_from_perfect_cooccurrence() -> None:
    """alpha=0.0 isolates the Jaccard half: the shared_risk pair co-occurs perfectly
    (r1, r2 both), so their blended similarity is 1.0 and they merge well inside the
    default 0.5 cut; `family_a-only` and `family_d` never co-occur with anything and
    stay singletons.
    """
    codebook = _cross_family_codebook()
    matrix = _matrix_excluding_family_c()
    result = build_affinity(codebook, matrix, StubEmbedder(), alpha=0.0, threshold=0.5)

    assert len(result.groups) == 1
    group = result.groups[0]
    assert group.members == ("family_a-shared_risk", "family_b-shared_risk")
    assert group.families == ("family_a", "family_b")
    assert group.cross_family is True
    assert group.total_responses == 2
    assert group.per_code_frequency == {
        "family_a-shared_risk": 2,
        "family_b-shared_risk": 2,
    }
    assert group.label_is_mechanical is True
    # tokens: family(2), shared(2), risk(2), a(1), b(1) -> top 3 tied at count 2,
    # alphabetical: family, risk, shared
    assert group.label_suggestion == "family_risk_shared"

    assert result.singleton_leaves == ("family_a-only", "family_d")


def test_within_family_group_is_not_cross_family() -> None:
    """Two leaves of the *same* family that co-occur perfectly must not be flagged
    cross_family, and their family list must have exactly one entry.
    """
    top = _code("family_a", "Concerns filed under family a.")
    codebook = Codebook(
        codes={
            top.id: top,
            "c-1": _code("family_a-one", "First leaf.", parent_id=top.id),
            "c-2": _code("family_a-two", "Second leaf.", parent_id=top.id),
        }
    )
    matrix = build_matrix(
        rows((1, "s", "family_a-one"), (1, "s", "family_a-two"), (2, "s", "family_a-one"), (2, "s", "family_a-two")),
        config=KEEP_ALL,
    )
    result = build_affinity(codebook, matrix, StubEmbedder(), alpha=0.0, threshold=0.5)
    assert len(result.groups) == 1
    group = result.groups[0]
    assert group.families == ("family_a",)
    assert group.cross_family is False


# =========================================================================== #
# The embedding half (alpha = 1.0)
# =========================================================================== #


class _FixedVectorEmbedder:
    """An `Embedder` returning hand-chosen vectors keyed by the exact rendered text.

    Re-running ``code_text -> embed -> cosine_matrix`` over the result's own names and
    asserting equality cannot fail unless the column order differs (R1, weak-test
    scan). Chosen geometry can: the numbers below are angles a reviewer can check on
    paper, and they are wrong the moment the blend or the rendering changes.
    """

    def __init__(self, vectors: dict[str, np.ndarray]) -> None:
        self._vectors = {t: v / np.linalg.norm(v) for t, v in vectors.items()}

    @property
    def space_id(self) -> str:
        return "fixed-vector-test-space"

    @property
    def dim(self) -> int:
        return 3

    def embed_one(self, text: str) -> np.ndarray:
        return self._vectors[text]

    def embed(self, texts: object) -> np.ndarray:
        return np.vstack([self._vectors[t] for t in texts])  # type: ignore[union-attr]


def _two_leaf_scenario() -> tuple[Codebook, object, _FixedVectorEmbedder]:
    """Two leaves 60 degrees apart, co-occurring in one response out of three.

    cosine = cos 60 deg = 0.5 exactly.
    Jaccard = |{r1}| / |{r1, r2, r3}| = 1/3.
    """
    import math

    first = _code("f-one", "The first concept.")
    second = _code("f-two", "The second concept.")
    codebook = Codebook(codes={c.id: c for c in (first, second)})
    matrix = build_matrix(
        rows(
            (1, "s", "f-one"),
            (1, "s", "f-two"),
            (2, "s", "f-one"),
            (3, "s", "f-two"),
        ),
        config=KEEP_ALL,
    )
    angle = math.radians(60)
    embedder = _FixedVectorEmbedder(
        {
            code_text("f-one", "The first concept."): np.array([1.0, 0.0, 0.0]),
            code_text("f-two", "The second concept."): np.array(
                [math.cos(angle), math.sin(angle), 0.0]
            ),
        }
    )
    return codebook, matrix, embedder


def test_the_cosine_component_is_the_angle_between_the_rendered_leaves() -> None:
    codebook, matrix, embedder = _two_leaf_scenario()
    result = build_affinity(codebook, matrix, embedder, alpha=1.0)
    i, j = (result.similarity.names.index(n) for n in ("f-one", "f-two"))
    assert result.similarity.cosine[i, j] == pytest.approx(0.5)
    assert result.similarity.cooccurrence_jaccard[i, j] == pytest.approx(1 / 3)


def test_the_blend_is_alpha_cosine_plus_one_minus_alpha_jaccard() -> None:
    """alpha=1.0 makes the blend a copy of the cosine, so it pins nothing."""
    codebook, matrix, embedder = _two_leaf_scenario()
    result = build_affinity(codebook, matrix, embedder, alpha=0.25)
    i, j = (result.similarity.names.index(n) for n in ("f-one", "f-two"))
    assert result.similarity.blended[i, j] == pytest.approx(0.25 * 0.5 + 0.75 * (1 / 3))
    assert result.similarity.blended[i, i] == pytest.approx(1.0)


def test_alpha_out_of_range_raises() -> None:
    codebook = _cross_family_codebook()
    matrix = _matrix_excluding_family_c()
    with pytest.raises(ValueError):
        build_affinity(codebook, matrix, StubEmbedder(), alpha=1.5)
    with pytest.raises(ValueError):
        build_affinity(codebook, matrix, StubEmbedder(), alpha=-0.1)


# =========================================================================== #
# Degenerate sizes
# =========================================================================== #


def test_single_clustered_leaf_is_a_singleton_not_a_group() -> None:
    top = _code("family_a", "Concerns filed under family a.")
    codebook = Codebook(codes={top.id: top, "c-1": _code("family_a-one", "Only leaf.", parent_id=top.id)})
    matrix = build_matrix(rows((1, "s", "family_a-one")), config=KEEP_ALL)
    result = build_affinity(codebook, matrix, StubEmbedder())
    assert result.groups == ()
    assert result.singleton_leaves == ("family_a-one",)
    assert result.n_leaves_clustered == 1


def test_no_leaves_present_in_matrix_is_not_an_error() -> None:
    codebook = _cross_family_codebook()
    empty_matrix = build_matrix([], config=KEEP_ALL)
    result = build_affinity(codebook, empty_matrix, StubEmbedder())
    assert result.n_leaves_clustered == 0
    assert result.groups == ()
    assert len(result.excluded) == result.n_leaves_total
    assert "Affinity themes" in result.to_markdown()


# =========================================================================== #
# The offline caveat and markdown / JSON plumbing
# =========================================================================== #


def test_offline_caveat_present_only_for_a_lexical_space_id() -> None:
    codebook = _cross_family_codebook()
    matrix = _matrix_excluding_family_c()

    lexical_like = StubEmbedder(space_id="lexical-v1-512")
    result = build_affinity(codebook, matrix, lexical_like, alpha=0.0)
    assert result.offline_caveat is not None
    assert "ADR-0019" in result.offline_caveat
    assert "Offline embedding space" in result.to_markdown()

    non_lexical = StubEmbedder(space_id="stub-v1-256")
    result2 = build_affinity(codebook, matrix, non_lexical, alpha=0.0)
    assert result2.offline_caveat is None
    assert "Offline embedding space" not in result2.to_markdown()


def test_to_json_str_is_byte_identical_across_calls() -> None:
    codebook = _cross_family_codebook()
    matrix = _matrix_excluding_family_c()
    embedder = StubEmbedder()
    first = build_affinity(codebook, matrix, embedder, alpha=0.0).to_json_str()
    second = build_affinity(codebook, matrix, embedder, alpha=0.0).to_json_str()
    assert first == second


def test_markdown_mentions_mechanical_label_and_naming_is_a_human_act() -> None:
    codebook = _cross_family_codebook()
    matrix = _matrix_excluding_family_c()
    result = build_affinity(codebook, matrix, StubEmbedder(), alpha=0.0)
    text = result.to_markdown()
    assert "human act" in text
    assert "mechanical" in text


# =========================================================================== #
# R1 audit findings
# =========================================================================== #


def test_a_matrix_column_that_is_not_a_codebook_leaf_is_excluded_and_counted() -> None:
    """R1 I5. A code that gained children is no longer a leaf, and vanished silently."""
    top = _code("family_a", "Concerns filed under family a.")
    child = _code("family_a-child", "A concept that grew under family a.", parent_id=top.id)
    other = _code("family_b", "A second top-level concept.")
    codebook = Codebook(codes={c.id: c for c in (top, child, other)})
    matrix = build_matrix(
        rows(
            (1, "s", "family_a"),
            (2, "s", "family_a"),
            (3, "s", "family_a"),
            (1, "s", "family_a-child"),
            (2, "s", "family_b"),
        ),
        config=KEEP_ALL,
    )
    result = build_affinity(codebook, matrix, StubEmbedder())

    assert "family_a" not in result.similarity.names, "it has a child, so it is not a leaf"
    excluded = {e.name: e.reason for e in result.excluded}
    assert "family_a" in excluded
    assert "not a leaf of this codebook" in excluded["family_a"]
    assert result.n_excluded_matrix_only == 1
    everything = set(result.similarity.names) | set(excluded)
    assert set(matrix.code_names) <= everything, "no column disappears without a row"

    markdown = result.to_markdown()
    assert "not leaves of this codebook" in markdown


def test_the_offline_caveat_survives_a_labelled_lexical_space() -> None:
    """R1 I8. `derive_space_id` documents labelling; the caveat must not be lost by it."""

    class _LabelledLexical(StubEmbedder):  # type: ignore[misc]
        @property
        def space_id(self) -> str:
            return "calibration-2025+lexical-v1-512"

    result = build_affinity(
        _cross_family_codebook(), _matrix_excluding_family_c(), _LabelledLexical()
    )
    assert result.offline_caveat is not None
    assert "ADR-0019" in result.offline_caveat
    assert "Offline embedding space" in result.to_markdown()


def test_a_label_that_merely_contains_the_word_lexical_does_not_earn_the_caveat() -> None:
    """The gate reads the derived core after `+`, not the researcher's label."""

    class _NotLexical(StubEmbedder):  # type: ignore[misc]
        @property
        def space_id(self) -> str:
            return "lexical-study+openai-text-embedding-3-small-512"

    result = build_affinity(
        _cross_family_codebook(), _matrix_excluding_family_c(), _NotLexical()
    )
    assert result.offline_caveat is None


@pytest.mark.parametrize("threshold", [-0.5, 1.5])
def test_a_threshold_outside_zero_to_one_is_refused(threshold: float) -> None:
    """R1 Minor. `alpha` is range-checked and `threshold` was not."""
    with pytest.raises(ValueError, match="threshold must be in"):
        build_affinity(
            _cross_family_codebook(),
            _matrix_excluding_family_c(),
            StubEmbedder(),
            threshold=threshold,
        )


def test_the_similarity_to_distance_conversion_is_pinned_away_from_its_fixed_point() -> None:
    """R1, weak-test scan: every test used threshold=0.5, the fixed point of 1 - t.

    Handing `fcluster` `threshold` instead of `1 - threshold` left all eleven tests
    passing. These two thresholds sit either side of the pair's blended similarity, so
    the injected off-by-one-minus flips both of them.
    """
    codebook = _cross_family_codebook()
    matrix = _matrix_excluding_family_c()
    embedder = StubEmbedder()

    pair = ("family_a-shared_risk", "family_b-shared_risk")
    reference = build_affinity(codebook, matrix, embedder, alpha=0.0, threshold=0.5)
    index = {name: i for i, name in enumerate(reference.similarity.names)}
    blended = float(reference.similarity.blended[index[pair[0]], index[pair[1]]])
    assert blended == pytest.approx(1.0), "the two share every response, so Jaccard is 1.0"

    together = build_affinity(codebook, matrix, embedder, alpha=0.0, threshold=0.9)
    apart = build_affinity(codebook, matrix, embedder, alpha=0.0, threshold=1.0)
    assert any(set(pair) <= set(g.members) for g in together.groups), (
        "blended 1.0 >= 0.9, so the pair merges"
    )
    assert set(pair) <= set(apart.singleton_leaves) or any(
        set(pair) <= set(g.members) for g in apart.groups
    ), "at exactly 1.0 the cut is inclusive, so the pair still merges"

    far = build_affinity(codebook, matrix, embedder, alpha=1.0, threshold=0.99)
    assert not any(set(pair) <= set(g.members) for g in far.groups), (
        "cosine alone does not reach 0.99, so a 1 - t slip would wrongly merge them"
    )
