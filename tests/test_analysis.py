"""The deterministic analysis tail: occurrence matrix, Ward's HCA, concurrent validation.

Everything asserted here is a pure function of its inputs — no model, no store, no
network — so each expectation is a number a reviewer can recompute by hand. Where a
number came from arithmetic done on paper, the arithmetic is in the docstring.
"""

from __future__ import annotations

import random

# ElementTree parses only strings this test suite just generated from a linkage
# matrix — there is no untrusted document and no entity declaration anywhere in it.
import xml.etree.ElementTree as ElementTree

import numpy as np
import pytest

from gaf.analysis.agreement import (
    AgreementReport,
    cohens_kappa,
    concurrent_validation,
    descriptions_from_codebook,
    match_codes,
)
from gaf.analysis.hca import (
    DegenerateMatrixError,
    agglomeration_schedule,
    choose_n_clusters,
    cluster_means,
    cluster_responses,
    dendrogram_svg,
    saturation_curve,
    saturation_svg,
    schedule_from_distances,
    ward_linkage,
)
from gaf.analysis.matrix import (
    OccurrenceMatrix,
    assignments_from_codebook,
    build_matrix,
    matrix_from_codebook,
    metadata_crosstab,
)
from gaf.config import AnalysisConfig, CodingRules
from gaf.models import Assignment, Code, Codebook, Evidence, Response
from tests.fixtures.assignments import (
    HUMAN_ONLY,
    MACHINE_ONLY,
    human_assignments,
    machine_assignments,
)
from tests.fixtures.codebooks import toy_codebook
from tests.fixtures.corpus import corpus_by_id, synthetic_corpus
from tests.fixtures.embedding import StubEmbedder

KEEP_ALL = AnalysisConfig(min_code_frequency=1)


def rows(*triples: tuple[int, str, str]) -> list[Assignment]:
    return [Assignment(rid, segment, code) for rid, segment, code in triples]


# =========================================================================== #
# The occurrence matrix
# =========================================================================== #


def test_matrix_values_are_binary_even_when_a_code_repeats_in_one_response() -> None:
    """A code on three segments of one response is still a single occurrence."""
    matrix = build_matrix(
        rows(
            (7, "first span", "a-one"),
            (7, "second span", "a-one"),
            (7, "third span", "a-one"),
            (3, "elsewhere", "a-one"),
        ),
        config=KEEP_ALL,
    )
    assert set(np.unique(matrix.values)) <= {0, 1}
    assert matrix.frequencies() == {"a-one": 2}


def test_row_and_column_order_is_documented_and_input_order_independent() -> None:
    """Rows ascend by response id, columns sort by name, whatever order the rows arrive."""
    source = rows(
        (50, "s", "z_family-late"),
        (3, "s", "a_family-early"),
        (17, "s", "m_family-middle"),
        (3, "s", "z_family-late"),
        (17, "s", "a_family-early"),
        (50, "s", "m_family-middle"),
    )
    shuffled = list(source)
    random.Random(4).shuffle(shuffled)

    first = build_matrix(source, config=KEEP_ALL)
    second = build_matrix(shuffled, config=KEEP_ALL)

    assert first.response_ids == (3, 17, 50)
    assert first.code_names == ("a_family-early", "m_family-middle", "z_family-late")
    assert first.to_csv() == second.to_csv()
    assert first.to_csv().splitlines()[0].startswith("response_id,")


def test_absolute_filter_drops_codes_below_min_code_frequency() -> None:
    matrix = build_matrix(
        rows(
            (1, "s", "keep-me"),
            (2, "s", "keep-me"),
            (3, "s", "keep-me"),
            (1, "s", "drop-me"),
        ),
        config=AnalysisConfig(min_code_frequency=2),
    )
    assert matrix.code_names == ("keep-me",)
    assert [d.name for d in matrix.filter.dropped] == ["drop-me"]
    assert matrix.filter.dropped[0].n_responses == 1
    assert matrix.filter.dropped[0].threshold == 2
    assert matrix.filter.binding_rule == "absolute"


def test_fraction_filter_reproduces_chans_five_percent_rule() -> None:
    """Chan: "less than 5% ... three out of fifty" -> at n = 50 the threshold is 3."""
    assignments: list[Assignment] = []
    for response_id in range(1, 51):
        assignments.append(Assignment(response_id, "s", "common-code"))
    for response_id in (1, 2, 3):
        assignments.append(Assignment(response_id, "s", "borderline-three"))
    for response_id in (4, 5):
        assignments.append(Assignment(response_id, "s", "rare-two"))

    matrix = build_matrix(
        assignments,
        config=AnalysisConfig(min_code_frequency=1, min_code_frequency_fraction=0.05),
    )
    assert matrix.filter.n_responses == 50
    assert matrix.filter.fraction_threshold == 3
    assert matrix.filter.threshold == 3
    assert matrix.filter.binding_rule == "fraction"
    assert matrix.code_names == ("borderline-three", "common-code")
    assert [d.name for d in matrix.filter.dropped] == ["rare-two"]


def test_fraction_threshold_is_not_broken_by_floating_point() -> None:
    """0.05 * 60 is 3.0000000000000004 in binary floats; the threshold must still be 3."""
    assignments = [Assignment(r, "s", "everywhere") for r in range(1, 61)]
    assignments += [Assignment(r, "s", "exactly-three") for r in (1, 2, 3)]
    matrix = build_matrix(
        assignments,
        config=AnalysisConfig(min_code_frequency=1, min_code_frequency_fraction=0.05),
    )
    assert matrix.filter.fraction_threshold == 3
    assert "exactly-three" in matrix.code_names


def test_the_stricter_of_the_two_filters_wins_in_both_directions() -> None:
    assignments = [Assignment(r, "s", "everywhere") for r in range(1, 21)]
    assignments += [Assignment(r, "s", "three-responses") for r in (1, 2, 3)]

    # fraction stricter: 0.25 * 20 = 5 > absolute 2
    strict_fraction = build_matrix(
        assignments,
        config=AnalysisConfig(min_code_frequency=2, min_code_frequency_fraction=0.25),
    )
    assert strict_fraction.filter.threshold == 5
    assert strict_fraction.filter.binding_rule == "fraction"
    assert strict_fraction.code_names == ("everywhere",)

    # absolute stricter: 0.05 * 20 = 1 < absolute 4
    strict_absolute = build_matrix(
        assignments,
        config=AnalysisConfig(min_code_frequency=4, min_code_frequency_fraction=0.05),
    )
    assert strict_absolute.filter.threshold == 4
    assert strict_absolute.filter.binding_rule == "absolute"
    assert strict_absolute.code_names == ("everywhere",)

    # a tie is recorded as such: 0.15 * 20 = 3 == absolute 3
    tied = build_matrix(
        assignments,
        config=AnalysisConfig(min_code_frequency=3, min_code_frequency_fraction=0.15),
    )
    assert tied.filter.threshold == 3
    assert tied.filter.binding_rule == "both"
    assert tied.code_names == ("everywhere", "three-responses")


def test_dropped_codes_are_reported_with_a_reason_and_a_summary() -> None:
    matrix = build_matrix(
        rows((1, "s", "keep"), (2, "s", "keep"), (1, "s", "drop")),
        config=AnalysisConfig(min_code_frequency=2),
    )
    dropped = matrix.filter.dropped[0]
    assert "drop" in matrix.filter.summary()
    assert "min_code_frequency=2" in dropped.reason
    assert matrix.filter.to_json()["n_dropped"] == 1


def test_codebook_projection_uses_verified_evidence_only() -> None:
    codebook = Codebook(
        codes={
            "c-1": Code(
                id="c-1",
                name="family-verified",
                description="d",
                evidence=[
                    Evidence(response_id=203, quote="located", verified=True),
                    Evidence(response_id=9, quote="never found", verified=False),
                ],
            )
        }
    )
    assert assignments_from_codebook(codebook) == [Assignment(203, "located", "family-verified")]

    matrix = matrix_from_codebook(toy_codebook(), config=KEEP_ALL)
    assert matrix.n_responses == 7
    assert "positive_impacts-healthcare" in matrix.code_names


def test_build_matrix_refuses_assignments_outside_the_corpus() -> None:
    with pytest.raises(ValueError, match="not in the corpus"):
        build_matrix(
            rows((9999, "s", "a-b")), config=KEEP_ALL, responses=synthetic_corpus()
        )


def test_uncoded_responses_become_all_zero_rows_when_the_corpus_is_supplied() -> None:
    matrix = build_matrix(
        rows((203, "s", "a-one"), (207, "s", "a-one")),
        config=KEEP_ALL,
        responses=synthetic_corpus(),
    )
    assert matrix.n_responses == 14
    assert matrix.filter.n_responses == 14
    # `row` is keyed by response id: 253 is in the corpus and nothing above codes it,
    # so it is present as an all-zero row.
    assert int(matrix.row(253).sum()) == 0


def test_an_empty_matrix_is_empty_rather_than_an_exception() -> None:
    matrix = build_matrix([], config=KEEP_ALL)
    assert matrix.is_empty
    assert matrix.n_responses == 0
    assert matrix.frequencies() == {}
    assert matrix.to_csv() == "response_id\n"


def test_respondent_metadata_is_joined_here_and_crosstabs_against_clusters() -> None:
    responses = [
        Response(id=i, question="q", content="c", source="s", meta={"region": "north" if i < 3 else "south"})
        for i in range(1, 5)
    ]
    matrix = build_matrix(
        rows((1, "s", "a-x"), (2, "s", "a-x"), (3, "s", "b-y"), (4, "s", "b-y")),
        config=KEEP_ALL,
        responses=responses,
    )
    assert matrix.meta[1] == {"region": "north"}
    assert metadata_crosstab(matrix, [1, 1, 2, 2], "region") == {
        1: {"north": 2},
        2: {"south": 2},
    }
    assert metadata_crosstab(matrix, [1, 1, 2, 2], "absent") == {
        1: {"(missing)": 2},
        2: {"(missing)": 2},
    }
    with pytest.raises(ValueError, match="labels has"):
        metadata_crosstab(matrix, [1, 1], "region")


# =========================================================================== #
# Ward's HCA
# =========================================================================== #


def chan_worked_example_distances() -> list[float]:
    """49 coefficients whose largest jump is entering stage 47 (Chan's n = 50 example)."""
    distances = [1.0 + 0.1 * i for i in range(49)]
    for stage in range(47, 50):  # stages 47, 48, 49 -> indices 46, 47, 48
        distances[stage - 1] += 20.0
    return distances


def test_a_leaf_end_break_warns_that_the_count_is_degenerate() -> None:
    """ADR-0020's own worked case must produce the warning ADR-0020 promises.

    The rule assumes the largest break falls near the ROOT. On a small sample with sparse
    code vectors the first merges are between near-identical rows and cost almost nothing,
    so the largest jump lands at the LEAF end and `n_samples - break_stage` returns a count
    close to the sample size. On the real 20-response seed sample it returns 18.

    Constructed here rather than taken from a fixture so the arithmetic stays visible: 20
    responses, 19 merges, the first at distance 0.0 (a duplicate pair merging for free),
    the second jumping to 1.0 — a delta larger than anything later. The rule picks stage 2,
    and 20 - 2 = 18.

    Before the second adversarial review this branch existed and no test reached it:
    deleting the whole `elif` would have left the suite green.
    """
    distances = [0.0, 1.0] + [1.0 + 0.05 * i for i in range(17)]
    schedule = schedule_from_distances(distances)

    assert schedule.n_samples == 20
    assert schedule.break_stage == 2
    assert schedule.suggested_clusters == 18
    assert schedule.warnings, "the degenerate count produced no warning at all"
    text = " ".join(schedule.warnings).lower()
    assert "leaf" in text and "degenerate" in text
    assert "18 clusters for 20 responses" in text
    # it must name the usable alternatives, not merely complain
    assert "stage 18" in text or "stage 17" in text


def test_a_healthy_schedule_produces_no_degeneracy_warning() -> None:
    """The complement, so the warning cannot be satisfied by always firing.

    Chan's own shape: a long run of small even merges and a clear break near the root.
    `suggested > n_samples / 2` is false, and nothing is emitted.
    """
    schedule = schedule_from_distances(chan_worked_example_distances())
    assert schedule.suggested_clusters == 3
    assert not schedule.warnings, f"a healthy schedule warned: {schedule.warnings}"


def test_every_cluster_warning_reaches_the_markdown_artefact() -> None:
    """A caveat that only reaches the operator's terminal is not a caveat.

    `clusters.md` is what a reader keeps and quotes from, and the cluster count is the
    study's headline, so the warning has to be in the file rather than only on stdout.
    """
    rows: list[Assignment] = []
    for index in range(6):
        rows.append(Assignment(300 + index, f"segment {index}", f"family-code_{index:02d}"))
        rows.append(Assignment(300 + index, f"shared {index}", "family-shared"))
    matrix = build_matrix(rows, config=AnalysisConfig(min_code_frequency=1))
    result = cluster_responses(matrix, config=AnalysisConfig(min_code_frequency=1))

    markdown = result.to_markdown()
    for warning in result.warnings:
        assert warning in markdown, "a warning was dropped on the way into the artefact"
    if result.warnings:
        assert "Read this before quoting the cluster count" in markdown


def test_chan_essary_worked_example_gives_three_clusters() -> None:
    """Sample size 50, break at stage 47: 50 - 47 = 3 clusters."""
    schedule = schedule_from_distances(chan_worked_example_distances())
    assert schedule.n_samples == 50
    assert len(schedule.steps) == 49
    assert schedule.break_stage == 47
    assert schedule.suggested_clusters == 3
    assert choose_n_clusters(schedule) == (3, "schedule")
    assert "47" in schedule.to_markdown()


def test_schedule_has_n_minus_one_rows_with_distances_and_deltas() -> None:
    schedule = schedule_from_distances([1.0, 2.0, 2.5, 6.0])
    assert schedule.n_samples == 5
    assert [s.stage for s in schedule.steps] == [1, 2, 3, 4]
    assert [s.distance for s in schedule.steps] == [1.0, 2.0, 2.5, 6.0]
    # stage 1 has no earlier coefficient, so its delta is defined as 0.0
    assert [round(s.delta, 6) for s in schedule.steps] == [0.0, 1.0, 0.5, 3.5]
    assert schedule.break_stage == 4
    assert schedule.largest_breaks(2)[0].stage == 4


def test_a_tied_break_resolves_to_the_later_stage() -> None:
    """Preferring the earlier stage would silently inflate the cluster count."""
    schedule = schedule_from_distances([1.0, 2.0, 3.0, 4.0])
    assert schedule.break_stage == 4
    assert schedule.suggested_clusters == 1
    assert schedule.warnings  # one cluster is flagged, not silently returned


def test_schedule_from_a_real_linkage_matches_scipy() -> None:
    matrix = build_matrix(
        rows(
            (1, "s", "a-x"), (2, "s", "a-x"), (3, "s", "a-x"),
            (4, "s", "b-y"), (5, "s", "b-y"), (6, "s", "b-y"),
            (1, "s", "b-y"),
        ),
        config=KEEP_ALL,
    )
    linkage_matrix = ward_linkage(matrix)
    schedule = agglomeration_schedule(linkage_matrix)
    assert len(schedule.steps) == matrix.n_responses - 1
    assert schedule.steps[0].distance == pytest.approx(float(linkage_matrix[0, 2]))


def test_cluster_means_on_a_hand_checkable_toy_matrix() -> None:
    """Rows [1,0], [1,1], [0,1], [0,1] split 1|1|2|2.

    Cluster 1: A = (1+1)/2 = 1.00, B = (0+1)/2 = 0.50.
    Cluster 2: A = 0.00,           B = 1.00.
    """
    matrix = build_matrix(
        rows(
            (1, "s", "aaa-one"),
            (2, "s", "aaa-one"),
            (2, "s", "bbb-two"),
            (3, "s", "bbb-two"),
            (4, "s", "bbb-two"),
        ),
        config=KEEP_ALL,
    )
    means = cluster_means(matrix, [1, 1, 2, 2], highlight=0.4)
    assert [(m.code, m.mean) for m in means[1]] == [("aaa-one", 1.0), ("bbb-two", 0.5)]
    assert [(m.code, m.mean) for m in means[2]] == [("bbb-two", 1.0), ("aaa-one", 0.0)]
    assert [m.prominent for m in means[1]] == [True, True]
    assert [m.prominent for m in means[2]] == [True, False]
    assert means[1][0].count == 2

    with pytest.raises(ValueError, match="labels has"):
        cluster_means(matrix, [1, 1], highlight=0.4)


def three_group_matrix() -> OccurrenceMatrix:
    """30 responses in three planted groups of code co-occurrence."""
    generator = random.Random(11)
    assignments: list[Assignment] = []
    for index in range(30):
        group = index % 3
        for code in range(6):
            if code // 2 == group or generator.random() < 0.1:
                assignments.append(
                    Assignment(index + 1, f"seg{index}-{code}", f"fam{code // 2}-code{code}")
                )
    return build_matrix(assignments, config=AnalysisConfig(min_code_frequency=2))


def test_cluster_responses_records_where_the_count_came_from() -> None:
    matrix = three_group_matrix()
    derived = cluster_responses(matrix)
    assert derived.n_clusters_source == "schedule"
    assert derived.n_clusters == derived.schedule.suggested_clusters
    assert sum(derived.sizes.values()) == 30
    assert set(derived.labels.tolist()) == set(derived.sizes)

    overridden = cluster_responses(
        matrix,
        config=AnalysisConfig(min_code_frequency=2, n_clusters=3),
    )
    assert overridden.n_clusters == 3
    assert overridden.n_clusters_source == "config_override"
    assert len(overridden.sizes) == 3
    assert "set explicitly" in overridden.to_markdown()
    assert len(overridden.members(1)) == overridden.sizes[1]


def test_cluster_count_override_is_validated() -> None:
    schedule = schedule_from_distances([1.0, 2.0, 5.0, 6.0])
    with pytest.raises(ValueError, match="must be >= 1"):
        choose_n_clusters(schedule, 0)
    with pytest.raises(ValueError, match="exceeds the sample size"):
        choose_n_clusters(schedule, 99)


def test_dendrogram_svg_is_valid_self_contained_and_byte_identical() -> None:
    result = cluster_responses(three_group_matrix())
    first = dendrogram_svg(result)
    second = dendrogram_svg(result)

    assert first == second, "the dendrogram must be byte-identical across runs"
    root = ElementTree.fromstring(first)
    assert root.tag.endswith("svg")
    assert root.attrib["width"] == "960"
    assert first.count("<polyline") == result.linkage.shape[0]

    # self-contained: no external fetch of any kind, no script, no timestamp
    for forbidden in ("<script", "href", "<image", "url(", "@import"):
        assert forbidden not in first
    assert "cut for k=" in first


def test_saturation_curve_and_its_svg() -> None:
    matrix = three_group_matrix()
    curve = saturation_curve(matrix, config=AnalysisConfig(saturation_batch_size=10))
    assert [p.batch for p in curve.points] == [1, 2, 3]
    assert [p.cumulative_responses for p in curve.points] == [10, 20, 30]
    assert curve.points[0].new_codes == curve.points[0].cumulative_codes
    assert curve.points[-1].cumulative_codes == curve.total_codes
    assert curve.total_codes == matrix.n_codes
    # the cumulative count never decreases
    cumulative = [p.cumulative_codes for p in curve.points]
    assert cumulative == sorted(cumulative)
    assert "Saturation" in curve.to_markdown()

    svg = saturation_svg(curve)
    assert svg == saturation_svg(curve)
    assert ElementTree.fromstring(svg).tag.endswith("svg")
    assert svg.count("<rect") == len(curve.points) + 1  # one background, one bar each

    with pytest.raises(ValueError, match="absent from the matrix"):
        saturation_curve(matrix, order=[9999])


def test_degenerate_inputs_are_refused_with_the_reason() -> None:
    too_few = build_matrix(rows((1, "s", "a-x"), (2, "s", "a-x"), (2, "s", "b-y")), config=KEEP_ALL)
    with pytest.raises(DegenerateMatrixError, match="at least 3 responses"):
        ward_linkage(too_few)

    one_column = build_matrix(
        rows((1, "s", "a-x"), (2, "s", "a-x"), (3, "s", "a-x")), config=KEEP_ALL
    )
    with pytest.raises(DegenerateMatrixError, match="at least 2 codes"):
        ward_linkage(one_column)

    all_zero = build_matrix([], config=KEEP_ALL, responses=synthetic_corpus())
    with pytest.raises(DegenerateMatrixError, match="at least 2 codes"):
        ward_linkage(all_zero)

    identical = build_matrix(
        rows(
            (1, "s", "a-x"), (1, "s", "b-y"),
            (2, "s", "a-x"), (2, "s", "b-y"),
            (3, "s", "a-x"), (3, "s", "b-y"),
        ),
        config=KEEP_ALL,
    )
    with pytest.raises(DegenerateMatrixError, match="identical set of codes"):
        ward_linkage(identical)


def test_a_schedule_needs_at_least_two_merge_steps() -> None:
    with pytest.raises(DegenerateMatrixError, match="at least 2 merge steps"):
        schedule_from_distances([1.0])


def test_small_n_behaves_the_way_the_seed_sample_will() -> None:
    """The real seed sample is 20 responses; the tail must produce or refuse honestly."""
    generator = random.Random(7)
    assignments: list[Assignment] = []
    for index in range(20):
        for code in range(5):
            if (code % 3) == (index % 3) or generator.random() < 0.2:
                assignments.append(Assignment(index + 1, f"s{index}{code}", f"fam-c{code}"))
    matrix = build_matrix(assignments, config=AnalysisConfig(min_code_frequency=2))
    result = cluster_responses(matrix)
    assert 1 <= result.n_clusters <= 20
    assert sum(result.sizes.values()) == 20
    assert result.to_json()["n_clusters_source"] == "schedule"


# =========================================================================== #
# Concurrent validation
# =========================================================================== #


def stub_report(
    human: list[Assignment] | None = None,
    machine: list[Assignment] | None = None,
    *,
    corpus: dict[int, Response] | None = corpus_by_id(),
) -> AgreementReport:
    return concurrent_validation(
        human if human is not None else human_assignments(),
        machine if machine is not None else machine_assignments(),
        embedder=StubEmbedder(),
        corpus=corpus,
    )


def test_cohens_kappa_matches_a_hand_computed_value() -> None:
    """human [1,1,0,0] vs machine [1,0,0,0].

    po = 3/4 = 0.75. P(1) = 0.5 and 0.25, P(0) = 0.5 and 0.75, so
    pe = 0.5*0.25 + 0.5*0.75 = 0.5, and kappa = (0.75 - 0.5) / (1 - 0.5) = 0.5.
    """
    assert cohens_kappa([1, 1, 0, 0], [1, 0, 0, 0]) == pytest.approx(0.5)
    assert cohens_kappa([1, 0, 1, 0], [1, 0, 1, 0]) == pytest.approx(1.0)
    # both raters used one category for everything: kappa is 0/0 and reads as agreement
    assert cohens_kappa([1, 1, 1], [1, 1, 1]) == pytest.approx(1.0)
    assert cohens_kappa([0, 0, 0], [1, 1, 1]) == pytest.approx(0.0)
    with pytest.raises(ValueError, match="same length"):
        cohens_kappa([1, 0], [1])
    with pytest.raises(ValueError, match="empty table"):
        cohens_kappa([], [])


def test_an_exact_match_scores_as_full_agreement_at_both_levels() -> None:
    golden = human_assignments()
    report = stub_report(golden, list(golden))
    assert report.code_level.precision == 1.0
    assert report.code_level.recall == 1.0
    assert report.code_level.f1 == 1.0
    assert report.code_level.kappa == pytest.approx(1.0)
    assert report.segment_level.weighted_f1 == pytest.approx(1.0)
    assert report.segment_level.right_code_wrong_place == 0
    assert report.over_coding == ()
    assert report.blind_spots == ()


def test_the_fixture_scores_are_the_hand_computed_ones() -> None:
    """8 responses x 6 union codes = 48 cells; TP 6, FP 2, FN 2, TN 38.

    P = R = 6/8 = 0.75. po = 44/48 = 11/12; pe = (8/48)^2 + (40/48)^2 = 13/18;
    kappa = (11/12 - 13/18) / (1 - 13/18) = (7/36) / (10/36) = 0.7.
    Segment level: 5 of 8 machine rows land on the human's span, so the
    overlap-weighted precision and recall are both 5/8 = 0.625.
    """
    report = stub_report()
    assert report.code_level.n_cells == 48
    assert (report.code_level.tp, report.code_level.fp) == (6, 2)
    assert (report.code_level.fn, report.code_level.tn) == (2, 38)
    assert report.code_level.f1 == pytest.approx(0.75)
    assert report.code_level.kappa == pytest.approx(0.7)
    assert report.segment_level.weighted_f1 == pytest.approx(0.625)


def test_right_code_wrong_place_is_a_code_hit_and_a_segment_miss() -> None:
    """One response, one code, two different spans of it: the isolated case.

    Response 203's two segments are disjoint — [93, 145) and [151, 179) of the
    normalised text — so the span Jaccard is 0.0 while the code-level cell is a hit.
    """
    corpus = corpus_by_id()
    code = "negative_impacts-job_destruction"
    human = [Assignment(203, "Clerical posts in the district office vanish quietly", code)]
    machine = [Assignment(203, "no retraining scheme arrives", code)]
    report = stub_report(human, machine, corpus=corpus)

    assert report.code_level.f1 == 1.0, "same code, same response -> a code-level hit"
    assert report.segment_level.weighted_f1 == 0.0, "different spans -> not a segment hit"
    assert report.segment_level.right_code_wrong_place == 1
    assert report.segment_level.n_located_machine == 1

    # and inside the full fixture the same asymmetry holds
    full = stub_report()
    assert full.segment_level.weighted_f1 < full.code_level.f1
    assert full.segment_level.right_code_wrong_place == 1


def test_over_coding_and_blind_spot_lists_name_exactly_the_planted_codes() -> None:
    report = stub_report()
    assert [u.code for u in report.over_coding] == list(MACHINE_ONLY)
    assert [u.code for u in report.blind_spots] == list(HUMAN_ONLY)

    over = report.over_coding[0]
    assert over.n_assignments == 2
    # `future-inevitability` is machine-only, on responses 212 and 258.
    assert over.response_ids == (212, 258)
    assert all(row.segment for row in over.rows), "rows must be quotable"

    blind = report.blind_spots[0]
    # `negative_impacts-lack_of_inclusion` is human-only, on responses 207 and 239.
    assert blind.response_ids == (207, 239)
    assert blind.nearest_code is not None, "the near-miss belongs in the write-up"
    assert blind.nearest_similarity < CodingRules().tau_high

    markdown = report.to_markdown()
    assert MACHINE_ONLY[0] in markdown
    assert HUMAN_ONLY[0] in markdown
    assert "You did not generate a new code" in markdown


def test_matching_runs_through_the_embedding_space_not_string_equality() -> None:
    embedder = StubEmbedder()
    matching = match_codes(
        ["negative_impacts-job_destruction"],
        ["negative_impacts-job_destruction reworded"],
        embedder=embedder,
        tau_high=0.5,
    )
    pair = matching.pairs[0]
    assert pair.similarity > 0.5 and pair.accepted
    assert matching.machine_to_human() == {
        "negative_impacts-job_destruction reworded": "negative_impacts-job_destruction"
    }

    strict = match_codes(
        ["negative_impacts-job_destruction"],
        ["negative_impacts-job_destruction reworded"],
        embedder=embedder,
        tau_high=0.99,
    )
    assert not strict.pairs[0].accepted
    assert strict.unmatched_machine() and strict.unmatched_human()


def test_descriptions_travel_into_the_embedding() -> None:
    report = concurrent_validation(
        human_assignments(),
        machine_assignments(),
        embedder=StubEmbedder(),
        corpus=corpus_by_id(),
        descriptions=descriptions_from_codebook(toy_codebook()),
    )
    assert report.matching.space_id == StubEmbedder().space_id
    assert len(report.matching.accepted) == 4


def test_segment_level_degrades_honestly_without_a_corpus() -> None:
    report = stub_report(corpus=None)
    assert report.segment_level.mode == "string"
    assert report.segment_level.n_located_machine == 0
    # the right-code-wrong-place case still fails, because the two quotes differ
    assert report.segment_level.right_code_wrong_place == 1
    assert report.segment_level.weighted_f1 == pytest.approx(0.625)


def test_report_serialises_deterministically() -> None:
    first = stub_report().to_json_str()
    second = stub_report().to_json_str()
    assert first == second
