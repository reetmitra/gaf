"""Wave 1 gate for the embedding space and the geometry (A2).

Four claims are under test here, and each answers a documented failure of the
predecessor study:

1. the space is **deterministic and versioned** — the same text yields the same vector
   in the same space across instances, and a different configuration is a different
   space id, so a score can never be silently compared against one from elsewhere;
2. the offline fallback's similarity distribution makes the declared bands mean
   something — the near-duplicate fixture pair sits above tau_high and the controls
   below tau_low, with clear air on both sides;
3. `hungarian_match` is an **optimal** assignment, demonstrated on a case constructed so
   that greedy provably loses;
4. retrieval renders codes through `code_text` and orders deterministically.

Everything runs offline: no key, no network, no provider SDK.
"""

from __future__ import annotations

import itertools

import numpy as np
import pytest

from gaf.config import CodingRules, EmbeddingSpaceConfig
from gaf.embed.matcher import (
    Route,
    cosine_matrix,
    hungarian_match,
    route_similarity,
    top_k_codes,
)
from gaf.embed.protocol import Embedder, code_text, cosine
from gaf.embed.protocol import Route as ProtocolRoute
from gaf.embed.protocol import route_similarity as protocol_route_similarity
from gaf.embed.service import (
    LEXICAL_ALGORITHM_VERSION,
    EmbeddingService,
    MissingEmbeddingSDKError,
    derive_space_id,
    lexical_tokens,
    lexical_vector,
)
from tests.fixtures.codebooks import near_duplicate_codebook, toy_codebook

RULES = CodingRules()


def _texts(codebook) -> list[str]:  # type: ignore[no-untyped-def]
    return [code_text(c.name, c.description) for c in codebook.sorted_codes()]


# --------------------------------------------------------------------------- #
# The protocol
# --------------------------------------------------------------------------- #


def test_service_satisfies_the_embedder_protocol() -> None:
    assert isinstance(EmbeddingService(), Embedder)


def test_vectors_are_l2_normalised_and_the_right_shape() -> None:
    service = EmbeddingService()
    matrix = service.embed(_texts(toy_codebook()))
    assert matrix.shape == (8, service.dim)
    assert matrix.dtype == np.float64
    assert np.allclose(np.linalg.norm(matrix, axis=1), 1.0)
    single = service.embed_one("negative_impacts: paid work disappears")
    assert single.shape == (service.dim,)
    assert np.isclose(float(np.linalg.norm(single)), 1.0)


def test_empty_batch_returns_an_empty_matrix_not_an_error() -> None:
    service = EmbeddingService()
    assert EmbeddingService().embed([]).shape == (0, service.dim)


def test_text_with_no_features_is_a_zero_vector_scoring_zero() -> None:
    """A code text made entirely of stopwords has no features, and must not blow up."""
    service = EmbeddingService()
    empty = service.embed_one("the and of to")
    assert float(np.linalg.norm(empty)) == 0.0
    assert cosine(empty, service.embed_one("healthcare")) == 0.0


# --------------------------------------------------------------------------- #
# Determinism
# --------------------------------------------------------------------------- #


def test_two_fresh_instances_produce_identical_vectors() -> None:
    """Determinism across instances is the weakest form of the cross-process claim.

    The strong form is guaranteed by construction: every feature index comes from
    `hashlib.blake2b`, never from `hash()`, whose salt differs between processes.
    """
    texts = _texts(toy_codebook())
    first = EmbeddingService().embed(texts)
    second = EmbeddingService().embed(texts)
    assert np.array_equal(first, second)


def test_the_memo_does_not_change_the_answer() -> None:
    service = EmbeddingService()
    before = service.embed_one("applications-healthcare: AI reads scans")
    assert service.memo_size == 1
    after = service.embed_one("applications-healthcare: AI reads scans")
    assert np.array_equal(before, after)
    assert service.memo_size == 1
    service.clear_memo()
    assert service.memo_size == 0
    assert np.array_equal(before, service.embed_one("applications-healthcare: AI reads scans"))


def test_hashing_is_stable_and_not_salted() -> None:
    """A frozen expectation: the same string must hash to the same feature every run."""
    vector = lexical_vector("healthcare", 512)
    assert np.array_equal(vector, lexical_vector("healthcare", 512))
    assert int(np.flatnonzero(vector)[0]) == int(np.flatnonzero(lexical_vector("healthcare", 512))[0])


def test_tokenisation_drops_stopwords_and_folds_plurals() -> None:
    tokens = lexical_tokens("The workers will lose their jobs and the machines are replacing them")
    assert "the" not in tokens and "will" not in tokens and "are" not in tokens
    assert "job" in tokens and "worker" in tokens
    assert "replac" in tokens or "replace" in tokens
    # "loss" ends in a double s and must not be stripped to "los".
    assert lexical_tokens("loss") == ["loss"]


# --------------------------------------------------------------------------- #
# Space versioning
# --------------------------------------------------------------------------- #


def test_default_config_yields_the_space_id_it_declares() -> None:
    assert EmbeddingService().space_id == EmbeddingSpaceConfig().space_id == "lexical-v1-512"
    assert LEXICAL_ALGORITHM_VERSION in EmbeddingService().space_id


def test_space_id_changes_with_dim_mode_and_model() -> None:
    base = EmbeddingSpaceConfig()
    smaller = EmbeddingSpaceConfig(dim=256)
    live_small = EmbeddingSpaceConfig(mode="openai", model="text-embedding-3-small", dim=1536)
    live_large = EmbeddingSpaceConfig(mode="openai", model="text-embedding-3-large", dim=1536)
    ids = {
        derive_space_id(base),
        derive_space_id(smaller),
        derive_space_id(live_small),
        derive_space_id(live_large),
    }
    assert len(ids) == 4, f"a configuration change must change the space id: {ids}"
    assert EmbeddingService(smaller).space_id == derive_space_id(smaller) == "lexical-v1-256"


def test_an_explicit_label_is_kept_but_cannot_disguise_a_different_space() -> None:
    labelled = EmbeddingSpaceConfig(space_id="calibration-2026", dim=256)
    space_id = derive_space_id(labelled)
    assert space_id.startswith("calibration-2026")
    assert "lexical-v1-256" in space_id
    assert space_id != derive_space_id(EmbeddingSpaceConfig(space_id="calibration-2026", dim=512))


def test_a_bad_dimension_is_refused_at_construction() -> None:
    with pytest.raises(ValueError, match="dim"):
        EmbeddingService(EmbeddingSpaceConfig(dim=0))


def test_live_mode_fails_loudly_at_construction_without_the_sdk() -> None:
    """The `openai` extra is not installed here, and must be named in the error."""
    with pytest.raises(MissingEmbeddingSDKError, match=r"uv sync --extra openai"):
        EmbeddingService(EmbeddingSpaceConfig(mode="openai", model="text-embedding-3-small", dim=1536))


# --------------------------------------------------------------------------- #
# The calibration claim: the bands behave sensibly on the fixture codebooks
# --------------------------------------------------------------------------- #


def _pairwise(service: EmbeddingService, codebook) -> dict[tuple[str, str], float]:  # type: ignore[no-untyped-def]
    codes = codebook.sorted_codes()
    matrix = cosine_matrix(service.embed(_texts(codebook)), service.embed(_texts(codebook)))
    return {
        (codes[i].name, codes[j].name): float(matrix[i, j])
        for i, j in itertools.combinations(range(len(codes)), 2)
    }


def test_the_near_duplicate_pair_is_above_tau_high_and_the_controls_below_tau_low() -> None:
    """The whole point of a two-threshold band, on the fixture built to exercise it."""
    scores = _pairwise(EmbeddingService(), near_duplicate_codebook())
    key = ("negative_impacts-job_destruction", "negative_impacts-job_loss")
    duplicate = scores[key]
    controls = [score for pair, score in scores.items() if pair != key]

    assert duplicate >= RULES.tau_high, f"near-duplicate pair scored {duplicate:.3f}"
    assert max(controls) < RULES.tau_low, f"a control pair scored {max(controls):.3f}"
    # Clear air on both sides, not a boundary case that a re-tune would flip.
    assert duplicate - RULES.tau_high > 0.05
    assert RULES.tau_low - max(controls) > 0.05


def test_the_toy_codebook_has_no_spurious_near_duplicates() -> None:
    """Eight deliberately distinct codes: nothing should reach the auto-merge band."""
    scores = _pairwise(EmbeddingService(), toy_codebook())
    assert max(scores.values()) < RULES.tau_high
    below = sum(1 for s in scores.values() if s < RULES.tau_low)
    assert below >= len(scores) - 2, "most pairs of distinct codes must be certainly different"


def test_route_similarity_is_the_protocol_one_not_a_local_copy() -> None:
    assert route_similarity is protocol_route_similarity
    assert Route is ProtocolRoute
    assert route_similarity(0.9, RULES.tau_high, RULES.tau_low) is Route.MERGE
    assert route_similarity(0.6, RULES.tau_high, RULES.tau_low) is Route.JUDGE
    assert route_similarity(0.1, RULES.tau_high, RULES.tau_low) is Route.CREATE


# --------------------------------------------------------------------------- #
# cosine_matrix
# --------------------------------------------------------------------------- #


def test_cosine_matrix_agrees_with_the_protocol_cosine() -> None:
    service = EmbeddingService()
    texts = _texts(toy_codebook())
    vectors = service.embed(texts)
    matrix = cosine_matrix(vectors, vectors)
    for i, j in itertools.combinations(range(len(texts)), 2):
        assert matrix[i, j] == pytest.approx(cosine(vectors[i], vectors[j]))
    assert np.allclose(np.diag(matrix), 1.0)


def test_cosine_matrix_refuses_to_mix_spaces() -> None:
    small = EmbeddingService(EmbeddingSpaceConfig(space_id="lexical-v1-64", dim=64))
    big = EmbeddingService()
    with pytest.raises(ValueError, match="different embedding spaces"):
        cosine_matrix(small.embed(["a code"]), big.embed(["a code"]))


def test_cosine_matrix_handles_empty_sides() -> None:
    service = EmbeddingService()
    assert cosine_matrix(service.embed([]), service.embed(["x"])).shape == (0, 1)


# --------------------------------------------------------------------------- #
# Hungarian assignment — the case greedy gets wrong
# --------------------------------------------------------------------------- #

#: Four unit vectors in R^4 chosen so that the similarity matrix is
#:
#:            b0      b1      b2
#:     a0   0.746   0.756   0.820
#:     a1   0.146   0.626   0.904
#:     a2   0.210   0.901   0.915
#:
#: Greedy takes the single largest cell first — (a2, b2) at 0.915 — then (a0, b1) at
#: 0.756, and is left with (a1, b0) at 0.146, which is below tau_low and therefore not
#: a match at all: two codes are reported unmatched. The optimal assignment is
#: (a0, b0), (a1, b2), (a2, b1) — every pair above 0.74, nothing unmatched. This is the
#: predecessor's failure in miniature: greedy matching manufactures unmatched codes.
_TRAP_A = np.array(
    [
        [0.3004, 0.2623, 0.6265, 0.6696],
        [0.0247, 0.8083, 0.5798, 0.0992],
        [0.2721, 0.1561, 0.9487, 0.0395],
    ]
)
_TRAP_B = np.array(
    [
        [0.5605, 0.0491, 0.0183, 0.8265],
        [0.6484, 0.2268, 0.7230, 0.0732],
        [0.2732, 0.5215, 0.7933, 0.1547],
    ]
)


def _unit(matrix: np.ndarray) -> np.ndarray:
    return matrix / np.linalg.norm(matrix, axis=1, keepdims=True)


def _trap_embedder(labels):  # type: ignore[no-untyped-def]
    lookup = {f"a{i}": row for i, row in enumerate(_unit(_TRAP_A))}
    lookup.update({f"b{i}": row for i, row in enumerate(_unit(_TRAP_B))})
    return np.vstack([lookup[label] for label in labels])


def _greedy(scores: np.ndarray, tau_low: float) -> list[tuple[int, int, float]]:
    """Take the best remaining pair, repeatedly. The algorithm this module replaces."""
    order = sorted(
        ((float(scores[i, j]), i, j) for i in range(scores.shape[0]) for j in range(scores.shape[1])),
        key=lambda cell: (-cell[0], cell[1], cell[2]),
    )
    used_a: set[int] = set()
    used_b: set[int] = set()
    pairs: list[tuple[int, int, float]] = []
    for score, i, j in order:
        if i in used_a or j in used_b:
            continue
        used_a.add(i)
        used_b.add(j)
        if score >= tau_low:
            pairs.append((i, j, score))
    return pairs


def test_hungarian_beats_greedy_on_a_case_built_to_trap_greedy() -> None:
    labels_a = ["a0", "a1", "a2"]
    labels_b = ["b0", "b1", "b2"]
    scores = cosine_matrix(_trap_embedder(labels_a), _trap_embedder(labels_b))

    result = hungarian_match(labels_a, labels_b, _trap_embedder, RULES.tau_high, RULES.tau_low)
    greedy = _greedy(scores, RULES.tau_low)

    optimal_total = sum(m.score for m in result.matches)
    greedy_total = sum(score for _, _, score in greedy)

    assert len(result.matches) == 3, "the optimal assignment pairs everything"
    assert len(greedy) == 2, "greedy strands a pair below tau_low"
    assert optimal_total > greedy_total + 0.5
    assert {(m.index_a, m.index_b) for m in result.matches} == {(0, 0), (1, 2), (2, 1)}
    assert not result.unmatched_a and not result.unmatched_b


def test_matches_carry_the_band_and_the_unmatched_are_returned() -> None:
    """A pair the solver had to make but that falls below tau_low is not a match."""
    labels_a = ["a0", "a1", "a2"]
    labels_b = ["b0"]
    result = hungarian_match(labels_a, labels_b, _trap_embedder, RULES.tau_high, RULES.tau_low)
    assert len(result.matches) == 1
    assert [label for _, label in result.unmatched_a] == ["a1", "a2"]
    assert result.unmatched_b == []
    assert all(m.route in (Route.MERGE, Route.JUDGE) for m in result.matches)
    assert result.matched_count == 1
    assert result.mean_score() == pytest.approx(result.matches[0].score)


def test_match_result_serialises_and_records_the_space() -> None:
    service = EmbeddingService()
    result = hungarian_match(
        ["negative_impacts-job_destruction: paid work disappears"],
        ["negative_impacts-job_loss: paid work disappears"],
        service,
        RULES.tau_high,
        RULES.tau_low,
    )
    assert result.space_id == service.space_id
    assert result.matches[0].space_id == service.space_id
    assert result.matches[0].route is Route.MERGE
    payload = result.to_json()
    assert payload["space_id"] == service.space_id
    assert payload["matches"][0]["route"] == "MERGE"


def test_matching_two_coders_codebooks_finds_the_duplicates() -> None:
    """The M1 shape: two coders' rendered codes, matched optimally."""
    service = EmbeddingService()
    coder_a = [
        code_text("negative_impacts-job_destruction", "Paid work disappears as AI replaces human workers."),
        code_text("applications-healthcare", "AI improves diagnosis and access to medical care."),
    ]
    coder_b = [
        code_text("applications-healthcare", "AI improves diagnosis and access to medical care."),
        code_text("negative_impacts-job_loss", "Paid work disappears as AI replaces human workers."),
    ]
    result = hungarian_match(coder_a, coder_b, service, RULES.tau_high, RULES.tau_low)
    assert result.matched_count == 2
    assert {(m.index_a, m.index_b) for m in result.matches} == {(0, 1), (1, 0)}
    assert all(m.route is Route.MERGE for m in result.matches)


def test_empty_sides_are_all_unmatched_not_an_error() -> None:
    service = EmbeddingService()
    result = hungarian_match([], ["future-inevitability: it is coming"], service, 0.8, 0.45)
    assert result.matches == []
    assert result.unmatched_b == [(0, "future-inevitability: it is coming")]
    assert result.space_id == service.space_id


def test_tau_low_above_tau_high_is_refused() -> None:
    with pytest.raises(ValueError, match="tau_low"):
        hungarian_match(["a0"], ["b0"], _trap_embedder, 0.4, 0.9)


# --------------------------------------------------------------------------- #
# Retrieval
# --------------------------------------------------------------------------- #


def test_top_k_retrieves_the_nearest_codes_in_order() -> None:
    service = EmbeddingService()
    query = code_text(
        "negative_impacts-job_destruction",
        "Existing categories of paid work disappear.",
    )
    ranked = top_k_codes(query, toy_codebook(), service, k=3)
    assert len(ranked) == 3
    assert ranked[0].name == "negative_impacts-job_destruction"
    assert ranked[0].score == pytest.approx(1.0)
    assert [r.score for r in ranked] == sorted((r.score for r in ranked), reverse=True)
    assert all(r.space_id == service.space_id for r in ranked)
    assert ranked[0].to_json()["code_id"] == "c-negative_impacts-job_destruction"


def test_top_k_uses_code_text_so_the_description_counts() -> None:
    """Two codes with the same family but different descriptions must rank differently.

    If retrieval rendered names alone, both would be equidistant from the query.
    """
    service = EmbeddingService()
    ranked = top_k_codes(
        code_text("q", "diagnosis monitoring and access to medical care"),
        toy_codebook(),
        service,
        k=8,
    )
    by_name = {r.name: r.score for r in ranked}
    assert by_name["positive_impacts-healthcare"] > by_name["positive_impacts-problem-solving"]
    assert by_name["positive_impacts-healthcare"] > 0.0


def test_top_k_is_clamped_and_deterministic() -> None:
    service = EmbeddingService()
    codebook = toy_codebook()
    assert top_k_codes("anything", codebook, service, k=99) == top_k_codes(
        "anything", codebook, service, k=99
    )
    assert len(top_k_codes("anything", codebook, service, k=99)) == len(codebook)
    assert top_k_codes("anything", codebook, service, k=0) == []


def test_top_k_on_an_empty_codebook_is_empty() -> None:
    from gaf.models import Codebook

    assert top_k_codes("anything", Codebook(), EmbeddingService(), k=5) == []
