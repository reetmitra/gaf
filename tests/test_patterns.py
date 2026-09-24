"""Pattern mapping: family signatures, groups, co-occurrence, frequent combinations.

Every expectation here is hand-computable from a small synthetic assignment table —
the arithmetic is spelled out in each test's docstring or comments so a reviewer can
recheck it without running anything.
"""

from __future__ import annotations

import pytest

from gaf.analysis.matrix import build_matrix
from gaf.analysis.patterns import (
    build_patterns,
    jaccard_matrix,
)
from gaf.config import AnalysisConfig
from gaf.models import Assignment

KEEP_ALL = AnalysisConfig(min_code_frequency=1)


def rows(*triples: tuple[int, str, str]) -> list[Assignment]:
    return [Assignment(rid, segment, code) for rid, segment, code in triples]


# =========================================================================== #
# jaccard_matrix
# =========================================================================== #


def test_jaccard_matrix_diagonal_is_one_even_for_an_empty_column() -> None:
    import numpy as np

    values = np.array([[0, 1], [0, 0], [0, 1]], dtype=np.int8)
    result = jaccard_matrix(values)
    assert result[0, 0] == pytest.approx(1.0)
    assert result[1, 1] == pytest.approx(1.0)
    # column 0 is all-zero, column 1 occurs twice: intersection 0, union 2 -> 0.0
    assert result[0, 1] == pytest.approx(0.0)


def test_jaccard_matrix_matches_hand_arithmetic() -> None:
    import numpy as np

    # column a: rows 0,1; column b: rows 1,2 -> intersection {1} = 1, union {0,1,2} = 3
    values = np.array([[1, 0], [1, 1], [0, 1]], dtype=np.int8)
    result = jaccard_matrix(values)
    assert result[0, 1] == pytest.approx(1 / 3)
    assert result[1, 0] == pytest.approx(1 / 3)


# =========================================================================== #
# Fixture corpus for the report-level tests
# =========================================================================== #
#
# Seven responses, four codes in three families:
#   r1: {a-one, b-one}            families {a, b}
#   r2: {a-two, b-one}            families {a, b}   (same signature as r1)
#   r3: {c-one}                   families {c}
#   r4: {a-one}                   families {a}
#   r5: {a-two}                   families {a}       (same signature as r4)
#   r6: {}                        families {}         (all-zero row)
#   r7: {a-one, b-one, c-one}     families {a, b, c}
#
# Code frequencies: a-one -> {r1,r4,r7} = 3; a-two -> {r2,r5} = 2;
# b-one -> {r1,r2,r7} = 3; c-one -> {r3,r7} = 2.


def _seven_response_matrix() -> object:
    return build_matrix(
        rows(
            (1, "s", "a-one"),
            (1, "s", "b-one"),
            (2, "s", "a-two"),
            (2, "s", "b-one"),
            (3, "s", "c-one"),
            (4, "s", "a-one"),
            (5, "s", "a-two"),
            (7, "s", "a-one"),
            (7, "s", "b-one"),
            (7, "s", "c-one"),
        ),
        config=KEEP_ALL,
        responses=None,
    )


def _seven_response_matrix_with_universe() -> object:
    """Same codings, but response 6 is in the corpus with no codes (an all-zero row)."""
    from gaf.models import Response

    responses = [
        Response(id=i, question="q", content=f"synthetic response {i}", source="synthetic")
        for i in range(1, 8)
    ]
    return build_matrix(
        rows(
            (1, "s", "a-one"),
            (1, "s", "b-one"),
            (2, "s", "a-two"),
            (2, "s", "b-one"),
            (3, "s", "c-one"),
            (4, "s", "a-one"),
            (5, "s", "a-two"),
            (7, "s", "a-one"),
            (7, "s", "b-one"),
            (7, "s", "c-one"),
        ),
        config=KEEP_ALL,
        responses=responses,
    )


# =========================================================================== #
# Response signatures and code sets
# =========================================================================== #


def test_family_signature_and_code_set_are_sorted_and_correct() -> None:
    matrix = _seven_response_matrix_with_universe()
    report = build_patterns(matrix)
    by_id = {r.response_id: r for r in report.responses}

    assert by_id[1].code_set == ("a-one", "b-one")
    assert by_id[1].family_signature == ("a", "b")
    assert by_id[2].code_set == ("a-two", "b-one")
    assert by_id[2].family_signature == ("a", "b")
    assert by_id[6].code_set == ()
    assert by_id[6].family_signature == ()
    assert by_id[7].family_signature == ("a", "b", "c")


# =========================================================================== #
# Pattern groups and singletons
# =========================================================================== #


def test_pattern_groups_are_keyed_on_family_signature_not_code_set() -> None:
    """r1 and r2 share a family signature but not a code set; they must still group."""
    matrix = _seven_response_matrix_with_universe()
    report = build_patterns(matrix)

    signatures = {g.family_signature: g.response_ids for g in report.groups}
    assert signatures[("a", "b")] == (1, 2)
    assert signatures[("a",)] == (4, 5)
    assert len(report.groups) == 2


def test_groups_sort_largest_first_ties_broken_by_signature() -> None:
    matrix = _seven_response_matrix_with_universe()
    report = build_patterns(matrix)
    # both groups have size 2; ("a",) sorts before ("a", "b") lexicographically
    assert [g.family_signature for g in report.groups] == [("a",), ("a", "b")]


def test_singletons_are_counted_and_listed_by_response_id() -> None:
    matrix = _seven_response_matrix_with_universe()
    report = build_patterns(matrix)
    # r3 -> {c} and r7 -> {a,b,c}: each signature unique. r6 has an all-zero row and
    # so no signature at all; it is reported as uncoded, not as a singleton (R1 I6).
    assert report.singleton_response_ids == (3, 7)
    assert report.uncoded_response_ids == (6,)


def test_without_a_supplied_corpus_universe_all_zero_responses_are_absent() -> None:
    """response 6 was never coded, so it has no row at all without `responses=`."""
    matrix = _seven_response_matrix()
    report = build_patterns(matrix)
    ids = {r.response_id for r in report.responses}
    assert 6 not in ids
    assert report.singleton_response_ids == (3, 7)


# =========================================================================== #
# Co-occurrence tables
# =========================================================================== #


def test_code_cooccurrence_counts_and_jaccard() -> None:
    matrix = _seven_response_matrix()
    report = build_patterns(matrix)
    table = report.code_cooccurrence
    assert table.names == ("a-one", "a-two", "b-one", "c-one")

    def cell(a: str, b: str) -> tuple[int, float]:
        i, j = table.names.index(a), table.names.index(b)
        return int(table.counts[i, j]), float(table.jaccard[i, j])

    # diagonal is each code's own frequency
    assert cell("a-one", "a-one") == (3, 1.0)
    assert cell("a-two", "a-two") == (2, 1.0)
    # a-one and b-one co-occur in r1 and r7: count 2, union 3+3-2=4 -> jaccard 0.5
    assert cell("a-one", "b-one")[0] == 2
    assert cell("a-one", "b-one")[1] == pytest.approx(0.5)
    # a-one and a-two never co-occur
    assert cell("a-one", "a-two") == (0, 0.0)


def test_family_cooccurrence_counts_and_jaccard() -> None:
    matrix = _seven_response_matrix()
    report = build_patterns(matrix)
    table = report.family_cooccurrence
    assert table.names == ("a", "b", "c")

    def cell(a: str, b: str) -> tuple[int, float]:
        i, j = table.names.index(a), table.names.index(b)
        return int(table.counts[i, j]), float(table.jaccard[i, j])

    # family a: {r1,r2,r4,r5,r7}=5; family b: {r1,r2,r7}=3; family c: {r3,r7}=2
    assert cell("a", "a") == (5, 1.0)
    assert cell("b", "b") == (3, 1.0)
    assert cell("c", "c") == (2, 1.0)
    # a & b co-occur in r1,r2,r7 = 3; union 5+3-3=5 -> jaccard 0.6
    assert cell("a", "b")[0] == 3
    assert cell("a", "b")[1] == pytest.approx(0.6)
    # a & c co-occur in r7 only = 1; union 5+2-1=6 -> jaccard 1/6
    assert cell("a", "c")[0] == 1
    assert cell("a", "c")[1] == pytest.approx(1 / 6)
    # b & c co-occur in r7 only = 1; union 3+2-1=4 -> jaccard 0.25
    assert cell("b", "c")[0] == 1
    assert cell("b", "c")[1] == pytest.approx(0.25)


# =========================================================================== #
# Nearest pattern-mates
# =========================================================================== #


def test_nearest_pattern_mates_for_response_one() -> None:
    """r1 = {a-one, b-one}. Hand-computed Jaccard against every other response:

    r2 {a-two,b-one}: |{b-one}| / |{a-one,a-two,b-one}| = 1/3
    r3 {c-one}: 0/3 = 0
    r4 {a-one}: |{a-one}| / |{a-one,b-one}| = 1/2
    r5 {a-two}: 0/3 = 0
    r7 {a-one,b-one,c-one}: |{a-one,b-one}| / |{a-one,b-one,c-one}| = 2/3
    Top 3, descending: r7 (2/3), r4 (1/2), r2 (1/3).
    """
    matrix = _seven_response_matrix()
    report = build_patterns(matrix)
    by_id = {r.response_id: r for r in report.responses}
    mates = by_id[1].nearest
    assert [(m.response_id, pytest.approx(m.jaccard)) for m in mates] == [
        (7, pytest.approx(2 / 3)),
        (4, pytest.approx(1 / 2)),
        (2, pytest.approx(1 / 3)),
    ]


def test_nearest_mates_ties_break_by_response_id() -> None:
    """r3, r5 and r6 (if present) all score 0.0 against r1; ascending id order."""
    matrix = _seven_response_matrix_with_universe()
    report = build_patterns(matrix, top_k_mates=5)
    by_id = {r.response_id: r for r in report.responses}
    mates = by_id[1].nearest
    tail = [m.response_id for m in mates if m.jaccard == pytest.approx(0.0)]
    assert tail == sorted(tail)


def test_top_k_mates_is_honoured() -> None:
    matrix = _seven_response_matrix()
    report = build_patterns(matrix, top_k_mates=1)
    by_id = {r.response_id: r for r in report.responses}
    assert len(by_id[1].nearest) == 1


# =========================================================================== #
# Frequent combinations — pairs
# =========================================================================== #


def test_frequent_pairs_and_their_support_share_and_lift() -> None:
    """Only (a-one, b-one) meets min_support=2.

    `_seven_response_matrix()` has no supplied corpus universe, so response 6 (never
    coded) is not a row: n_responses = 6. support=2 (r1, r7); share = 2/6 = 1/3;
    lift = (1/3) / ((3/6)*(3/6)) = (1/3) / 0.25 = 4/3.
    """
    matrix = _seven_response_matrix()
    report = build_patterns(matrix)
    pairs = report.combinations.pairs
    assert [p.codes for p in pairs] == [("a-one", "b-one")]
    combo = pairs[0]
    assert combo.support == 2
    assert combo.share == pytest.approx(1 / 3)
    assert combo.lift == pytest.approx(4 / 3)


def test_no_triples_when_fewer_than_three_pairwise_frequent_codes() -> None:
    matrix = _seven_response_matrix()
    report = build_patterns(matrix)
    assert report.combinations.triples == ()
    assert report.combinations.triple_candidates_total == 0
    assert report.combinations.triple_bound_hit is False


def test_min_support_raises_below_one() -> None:
    matrix = _seven_response_matrix()
    with pytest.raises(ValueError):
        build_patterns(matrix, min_support=0)


# =========================================================================== #
# Frequent combinations — triples and the Apriori bound
# =========================================================================== #
#
# x, y, z each pairwise co-occur >= 2 times, and all three co-occur exactly twice:
#   r1 {x,y}  r2 {y,z}  r3 {x,z}  r4 {x,y,z}  r5 {x,y,z}
# freq: x=4 (r1,r3,r4,r5), y=4 (r1,r2,r4,r5), z=4 (r2,r3,r4,r5)
# pair supports: (x,y)=3 (r1,r4,r5); (y,z)=3 (r2,r4,r5); (x,z)=3 (r3,r4,r5)
# triple support: (x,y,z) = 2 (r4,r5); share=2/5; lift = 0.4 / (0.8*0.8*0.8) = 0.78125


def _triple_matrix() -> object:
    return build_matrix(
        rows(
            (1, "s", "t-x"),
            (1, "s", "t-y"),
            (2, "s", "t-y"),
            (2, "s", "t-z"),
            (3, "s", "t-x"),
            (3, "s", "t-z"),
            (4, "s", "t-x"),
            (4, "s", "t-y"),
            (4, "s", "t-z"),
            (5, "s", "t-x"),
            (5, "s", "t-y"),
            (5, "s", "t-z"),
        ),
        config=KEEP_ALL,
    )


def test_frequent_triple_detected_via_apriori_join() -> None:
    matrix = _triple_matrix()
    report = build_patterns(matrix)
    triples = report.combinations.triples
    assert [t.codes for t in triples] == [("t-x", "t-y", "t-z")]
    combo = triples[0]
    assert combo.support == 2
    assert combo.share == pytest.approx(2 / 5)
    assert combo.lift == pytest.approx(0.78125)
    assert report.combinations.triple_candidates_total == 1
    assert report.combinations.triple_candidates_considered == 1
    assert report.combinations.triple_bound_hit is False


def test_triple_bound_hit_when_cap_is_zero() -> None:
    matrix = _triple_matrix()
    report = build_patterns(matrix, max_triple_candidates=0)
    assert report.combinations.triples == ()
    assert report.combinations.triple_candidates_total == 1
    assert report.combinations.triple_candidates_considered == 0
    assert report.combinations.triple_bound_hit is True
    assert "bound" in report.to_markdown().lower()


# =========================================================================== #
# Determinism and empty input
# =========================================================================== #


def test_to_json_str_is_byte_identical_across_calls() -> None:
    matrix = _seven_response_matrix_with_universe()
    report = build_patterns(matrix)
    assert report.to_json_str() == build_patterns(matrix).to_json_str()


def test_empty_matrix_produces_an_empty_report_without_raising() -> None:
    matrix = build_matrix([], config=KEEP_ALL)
    assert matrix.is_empty
    report = build_patterns(matrix)
    assert report.n_responses == 0
    assert report.n_codes == 0
    assert report.responses == ()
    assert report.groups == ()
    assert report.singleton_response_ids == ()
    assert report.combinations.pairs == ()
    assert report.combinations.triples == ()
    # Markdown must render without a division-by-zero or an index error.
    assert "Pattern mapping" in report.to_markdown()


def test_markdown_mentions_the_filter_and_min_support() -> None:
    matrix = _seven_response_matrix()
    report = build_patterns(matrix, min_support=3)
    text = report.to_markdown()
    assert "min_support = 3" in text
    assert report.filter.summary() in text


# =========================================================================== #
# R1 audit findings
# =========================================================================== #


def test_uncoded_responses_are_counted_apart_from_the_pattern_groups() -> None:
    """R1 I6. An empty family signature is the absence of a pattern, not a pattern."""
    from gaf.models import Response

    responses = [
        Response(id=i, question="q", content=f"synthetic response {i}", source="synthetic")
        for i in range(1, 11)
    ]
    matrix = build_matrix(
        rows((1, "s", "a-one"), (2, "s", "a-one"), (3, "s", "b-one")),
        config=KEEP_ALL,
        responses=responses,
    )
    report = build_patterns(matrix)

    assert report.uncoded_response_ids == (4, 5, 6, 7, 8, 9, 10)
    assert [(g.size, g.family_signature) for g in report.groups] == [(2, ("a",))]
    assert report.singleton_response_ids == (3,)
    assert all(g.family_signature for g in report.groups), "() is never a group"

    by_id = {r.response_id: r for r in report.responses}
    assert by_id[4].code_set == () and by_id[4].nearest == (), (
        "a response with no codes has no nearest pattern-mate"
    )
    assert by_id[1].nearest, "a coded response still gets mates"

    markdown = report.to_markdown()
    assert "_(no codes)_" not in markdown
    assert "**7** response(s) carry no code at all" in markdown
    payload = report.to_json()
    assert payload["uncoded_response_ids"] == [4, 5, 6, 7, 8, 9, 10]


def test_triple_candidates_are_ranked_by_their_support_bound_before_truncation() -> None:
    """R1 C4. Alphabetical truncation can drop the strongest triple in the data.

    Twelve responses. `zzz-one/-two/-three` co-occur in eight of them, so each of the
    three constituent pairs has support 8 and the triple itself has support 8. Six
    `aaa-*` codes pair up across four responses only, giving a far larger set of
    alphabetically-earlier candidates. With the bound at one candidate, the one kept
    must be the planted triple, not the first one in the alphabet.
    """
    planted = [(r, "s", f"zzz-{n}") for r in range(1, 9) for n in ("one", "two", "three")]
    noise = [
        (r, "s", f"aaa-{n}")
        for r in range(9, 13)
        for n in ("one", "two", "three", "four", "five", "six")
    ]
    matrix = build_matrix(rows(*planted, *noise), config=KEEP_ALL)

    unbounded = build_patterns(matrix, min_support=2)
    assert unbounded.combinations.triple_bound_hit is False
    assert unbounded.combinations.triples[0].codes == ("zzz-one", "zzz-three", "zzz-two")
    assert unbounded.combinations.triples[0].support == 8
    assert unbounded.combinations.triple_candidates_total > 1

    bounded = build_patterns(matrix, min_support=2, max_triple_candidates=1)
    assert bounded.combinations.triple_bound_hit is True
    assert bounded.combinations.triple_candidates_considered == 1
    assert [c.codes for c in bounded.combinations.triples] == [
        ("zzz-one", "zzz-three", "zzz-two")
    ]
    assert "highest possible support" in bounded.to_markdown()
    assert "lexicographically" not in bounded.to_markdown()


def test_the_triple_bound_keeps_a_deterministic_order_among_equal_bounds() -> None:
    """Ties on the support bound fall back to the code names, so the cut is stable."""
    assignments = rows(
        *[(r, "s", f"m-{n}") for r in (1, 2) for n in ("a", "b", "c", "d")],
    )
    matrix = build_matrix(assignments, config=KEEP_ALL)
    first = build_patterns(matrix, min_support=2, max_triple_candidates=2)
    second = build_patterns(matrix, min_support=2, max_triple_candidates=2)
    assert first.to_json() == second.to_json()
    assert [c.codes for c in first.combinations.triples] == [
        ("m-a", "m-b", "m-c"),
        ("m-a", "m-b", "m-d"),
    ]


def test_nearest_mates_ties_break_by_response_id_with_a_tie_to_break() -> None:
    """R1, weak-test scan: `tail == sorted(tail)` is a tautology under two mates.

    r3, r5 and r6 all score exactly 0.0 against r1, so the expected ids are written
    out rather than derived from the answer.
    """
    matrix = _seven_response_matrix_with_universe()
    report = build_patterns(matrix, top_k_mates=6)
    by_id = {r.response_id: r for r in report.responses}
    mates = [(m.response_id, m.jaccard) for m in by_id[1].nearest]
    assert [rid for rid, score in mates if score == pytest.approx(0.0)] == [3, 5, 6]
    assert [rid for rid, _ in mates] == [7, 4, 2, 3, 5, 6]
