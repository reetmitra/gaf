"""The code-growth curve and the spike rule (`gaf.checks.growth`).

The PI noticed the number of codes spiking as coding went on. Eight claims:

1. **The curve is one curve.** `code_growth` delegates to the existing
   `gaf.analysis.hca.saturation_curve` rather than counting codes a second time, so a
   growth point and a saturation point can never disagree about a batch.
2. **Two ways in, one curve out.** The same coding, read from an ordered list of
   `Assignment` rows and read from a run's audit log, produces the same points.
3. **Order is the caller's, not the id order.** A coding whose export order differs
   from ascending response id gets the curve of *its* order.
4. **A response that produced no code still occupies its place in a batch**, because
   omitting it silently re-cuts the batches.
5. **The ratio rule fires** on a late batch that is a multiple of the recent median.
6. **The ratio rule cannot fire before it has a baseline**: the first `spike_window`
   batches fall back to the absolute `max_new_codes_per_batch` ceiling.
7. **The floor holds.** A batch below `spike_min_new_codes` never spikes, which is what
   stops a baseline median of zero from making every batch a spike.
8. **Everything serialises** deterministically, and the refusal paths refuse.

No key, no network, no real data: the assignments are invented here and the audit rows
are hand-built dicts.
"""

from __future__ import annotations

import json
from dataclasses import replace

import pytest

from gaf.analysis.hca import saturation_curve
from gaf.analysis.matrix import build_matrix
from gaf.checks.growth import (
    RULE_ABSOLUTE,
    RULE_RATIO,
    SOURCES,
    SPIKE_RULES,
    GrowthCurve,
    GrowthPoint,
    Spike,
    code_growth,
    detect_spikes,
    growth_from_audit,
)
from gaf.config import AnalysisConfig, CheckpointPolicy, RunConfig
from gaf.models import Assignment

# --------------------------------------------------------------------------- #
# Fixtures — invented codings, never a respondent's words
# --------------------------------------------------------------------------- #


def _rows(plan: dict[int, list[str]]) -> list[Assignment]:
    """Assignment rows in the order the responses are listed, segment text invented."""
    return [
        Assignment(response_id=rid, segment=f"segment of response {rid}", code=code)
        for rid, codes in plan.items()
        for code in codes
    ]


#: Four responses per batch; batch 1 is all new, batch 2 adds one, batch 3 spikes.
GROWTH_PLAN: dict[int, list[str]] = {
    1: ["alpha-one", "alpha-two"],
    2: ["alpha-one"],
    3: ["alpha-three"],
    4: ["alpha-one", "alpha-two"],
    5: ["alpha-one"],
    6: ["alpha-four"],
    7: ["alpha-two"],
    8: ["alpha-three"],
    9: ["beta-one", "beta-two"],
    10: ["beta-three", "beta-four"],
    11: ["beta-five"],
    12: ["alpha-one"],
}


def _audit_rows(plan: dict[int, list[str]]) -> list[dict[str, object]]:
    """The audit rows a run writes for this coding: one prepare, then its creations."""
    events: list[dict[str, object]] = []
    seen: set[str] = set()
    for response_id, codes in plan.items():
        events.append(
            {
                "event": "response_prepared",
                "scope": "response",
                "subject": str(response_id),
                "payload": {"snapshot_id": "snap-0"},
            }
        )
        for code in codes:
            if code in seen:
                events.append(
                    {
                        "event": "code_merged",
                        "scope": "codebook",
                        "subject": code,
                        "payload": {"response_id": response_id},
                    }
                )
                continue
            seen.add(code)
            events.append(
                {
                    "event": "code_created",
                    "scope": "codebook",
                    "subject": code,
                    "payload": {"response_id": response_id},
                }
            )
    return events


# --------------------------------------------------------------------------- #
# 1. One curve, not two
# --------------------------------------------------------------------------- #


def test_the_growth_curve_is_the_saturation_curve_with_a_per_response_rate() -> None:
    """Claim 1. Reuse, not a second implementation.

    The project already has a saturation curve. A growth curve that counted new codes
    independently would be a second saturation with its own rounding, its own batch
    edges and its own bugs. `code_growth` adds exactly one column the saturation curve
    does not carry — new codes per response — and takes the rest verbatim.
    """
    assignments = _rows(GROWTH_PLAN)
    curve = code_growth(assignments, batch_size=4)

    matrix = build_matrix(
        assignments,
        config=replace(AnalysisConfig(), min_code_frequency=1, min_code_frequency_fraction=None),
    )
    reference = saturation_curve(
        matrix, config=replace(AnalysisConfig(), saturation_batch_size=4)
    )

    assert curve.batch_size == reference.batch_size
    assert curve.total_codes == reference.total_codes
    assert curve.saturated_at_batch == reference.saturated_at_batch
    assert len(curve.points) == len(reference.points)
    for grown, saturated in zip(curve.points, reference.points, strict=True):
        assert grown.batch == saturated.batch
        assert grown.new_codes == saturated.new_codes
        assert grown.cumulative_codes == saturated.cumulative_codes
        assert grown.responses_in_batch == saturated.responses_in_batch
        assert grown.cumulative_responses == saturated.cumulative_responses
        assert grown.new_code_names == saturated.new_code_names


def test_new_codes_per_response_is_the_column_growth_adds() -> None:
    """The rate, not the raw count, is what a reader compares across batches."""
    curve = code_growth(_rows(GROWTH_PLAN), batch_size=4)
    for point in curve.points:
        assert point.new_codes_per_response == pytest.approx(
            point.new_codes / point.responses_in_batch
        )


def test_an_empty_coding_is_an_empty_curve_not_an_exception() -> None:
    """Nothing coded yet is a legitimate state at the start of a run."""
    curve = code_growth([], batch_size=4)
    assert curve.points == ()
    assert curve.total_codes == 0
    assert curve.saturated_at_batch is None
    assert curve.to_json()["points"] == []


# --------------------------------------------------------------------------- #
# 2. Two ways in, one curve out
# --------------------------------------------------------------------------- #


def test_the_same_coding_from_assignments_and_from_a_run_gives_the_same_curve() -> None:
    """Claim 2. This is the whole point of the two entry points.

    The PI codes in a spreadsheet and the pipeline codes into an audit log. If the two
    readings of the same coding produced different curves, neither could be used to
    check the other.
    """
    from_rows = code_growth(_rows(GROWTH_PLAN), batch_size=4)
    from_run = growth_from_audit(_audit_rows(GROWTH_PLAN), batch_size=4)

    assert from_rows.source == "assignments"
    assert from_run.source == "audit"
    assert [p.to_json() for p in from_rows.points] == [p.to_json() for p in from_run.points]
    assert from_rows.total_codes == from_run.total_codes


def test_every_source_name_is_declared() -> None:
    for curve in (code_growth([], batch_size=4), growth_from_audit([], batch_size=4)):
        assert curve.source in SOURCES


# --------------------------------------------------------------------------- #
# 3 and 4. The order, and the responses that produced nothing
# --------------------------------------------------------------------------- #


def test_the_curve_follows_the_coding_order_it_is_given() -> None:
    """Claim 3. The PI's export order is the order his codes actually arrived in."""
    plan = {9: ["a-one"], 1: ["a-two"], 5: ["a-one"], 3: ["a-three"]}
    curve = code_growth(_rows(plan), batch_size=2)

    # First batch is responses 9 and 1 — the order of the rows, not 1 and 3.
    assert curve.points[0].new_code_names == ("a-one", "a-two")
    assert curve.points[1].new_code_names == ("a-three",)

    ascending = code_growth(_rows(plan), batch_size=2, order=[1, 3, 5, 9])
    assert ascending.points[0].new_code_names == ("a-three", "a-two")


def test_an_uncoded_response_still_takes_its_place_in_a_batch() -> None:
    """Claim 4. Omitting it silently re-cuts every batch after it.

    Response 2 produced no code — every candidate dropped, say. It has no assignment
    row, so it can only be supplied by the caller who knows the run processed it.
    """
    plan = {1: ["a-one"], 3: ["a-two"], 4: ["a-three"]}
    without = code_growth(_rows(plan), batch_size=2)
    withit = code_growth(_rows(plan), batch_size=2, response_ids=[1, 2, 3, 4], order=[1, 2, 3, 4])

    assert [p.responses_in_batch for p in without.points] == [2, 1]
    assert [p.responses_in_batch for p in withit.points] == [2, 2]
    assert [p.new_codes for p in without.points] == [2, 1]
    assert [p.new_codes for p in withit.points] == [1, 2]


def test_an_order_that_is_not_a_permutation_of_the_universe_is_refused() -> None:
    """A short order would silently truncate the curve; say so instead."""
    rows = _rows({1: ["a-one"], 2: ["a-two"]})
    with pytest.raises(ValueError, match="every response"):
        code_growth(rows, batch_size=2, order=[1])
    with pytest.raises(ValueError, match="not in"):
        code_growth(rows, batch_size=2, order=[1, 2, 3])


def test_a_batch_size_below_one_is_clamped_to_one_response_per_batch() -> None:
    """Deliberately `gaf.analysis.hca.saturation_curve`'s clamp, not the fast loop's.

    `gaf.pipeline.fast_loop.batches` reads `size <= 0` as "one batch of everything";
    the saturation curve reads it as "one response per batch". This module is a reading
    of the curve, so it follows the curve — and never silently picks the other meaning,
    which would put a growth point and a saturation point at different batch edges.
    """
    curve = code_growth(_rows(GROWTH_PLAN), batch_size=0)
    assert curve.batch_size == 1
    assert len(curve.points) == 12
    assert all(point.responses_in_batch == 1 for point in curve.points)


# --------------------------------------------------------------------------- #
# 5, 6 and 7. The spike rule
# --------------------------------------------------------------------------- #


def _curve_of(counts: list[int], *, responses_per_batch: int = 4) -> GrowthCurve:
    """A curve with exactly these new-code counts, built through the real constructor."""
    plan: dict[int, list[str]] = {}
    response_id = 1
    minted = 0
    for count in counts:
        for position in range(responses_per_batch):
            codes: list[str] = []
            if position == 0:
                codes = [f"fam-code_{minted + i}" for i in range(count)]
                minted += count
            elif not codes:
                codes = ["fam-code_0"] if minted else []
            plan[response_id] = codes
            response_id += 1
    ids = list(plan)
    return code_growth(
        _rows(plan), batch_size=responses_per_batch, response_ids=ids, order=ids
    )


def test_a_late_batch_that_multiplies_the_recent_median_spikes() -> None:
    """Claim 5. The rule the PI's observation asks for.

    Baseline is the median of the previous three batches (1, 1, 1 = 1.0); batch 4's
    nine new codes is nine times that and clears the four-code floor.
    """
    curve = _curve_of([1, 1, 1, 9])
    spikes = detect_spikes(curve, CheckpointPolicy())

    assert [s.batch for s in spikes] == [4]
    spike = spikes[0]
    assert spike.rule == RULE_RATIO
    assert spike.new_codes == 9
    assert spike.baseline == pytest.approx(1.0)
    assert spike.ratio == pytest.approx(9.0)
    assert spike.window == 3
    assert spike.reason.endswith("."), spike.reason
    assert "median" in spike.reason


def test_the_first_window_batches_do_not_spike_at_all() -> None:
    """Claim 6, as revised. A ratio against nothing is not a measurement.

    The fallback this rule used to make in the first `spike_window` batches was the
    absolute `max_new_codes_per_batch` ceiling, which is definitionally the comparison
    `gaf.checks.health.checkpoint_signals` already makes under `handover.new_codes`;
    both fired on the same condition and the batch's reason stated one fact twice
    (R1 Minor). Batch 1's twelve new codes are over that ceiling and are still reported
    — by the health rule, which is the one that owns it.
    """
    curve = _curve_of([12, 1, 1, 1])
    assert detect_spikes(curve, CheckpointPolicy()) == []
    assert RULE_ABSOLUTE in SPIKE_RULES, "the name stays readable for an older Spike"

    # It is the ratio rule, and only the ratio rule, from the fourth batch on.
    later = detect_spikes(_curve_of([1, 1, 1, 12]), CheckpointPolicy())
    assert [(s.batch, s.rule) for s in later] == [(4, RULE_RATIO)]


def test_a_quiet_first_batch_does_not_spike_on_the_absolute_rule() -> None:
    curve = _curve_of([3, 2, 2, 2])
    assert detect_spikes(curve, CheckpointPolicy()) == []


def test_the_minimum_stops_a_zero_baseline_making_every_batch_a_spike() -> None:
    """Claim 7. Two new codes after three empty batches is not a spike.

    With a baseline median of 0 the ratio test degenerates — every count is at or above
    `spike_factor * 0` — so `spike_min_new_codes` is the only thing holding the rule up,
    and this is the test that says so.
    """
    policy = CheckpointPolicy()
    quiet = _curve_of([1, 0, 0, 2])
    assert detect_spikes(quiet, policy) == []

    loud = detect_spikes(_curve_of([1, 0, 0, 5]), policy)
    assert [s.batch for s in loud] == [4]
    assert loud[0].ratio is None
    assert loud[0].baseline == pytest.approx(0.0)
    assert "baseline of zero" in loud[0].reason


def test_the_spike_policy_is_configurable_and_additive() -> None:
    """The three fields are new on a frozen contract; their defaults change nothing."""
    default = CheckpointPolicy()
    assert (default.spike_factor, default.spike_window, default.spike_min_new_codes) == (
        2.0,
        3,
        4,
    )
    assert RunConfig().checkpoints.spike_factor == 2.0

    # Baseline 3.0: five new codes is under 2.0x but over 1.5x.
    curve = _curve_of([3, 3, 3, 5])
    assert detect_spikes(curve, default) == []
    assert [s.batch for s in detect_spikes(curve, replace(default, spike_factor=1.5))] == [4]

    strict = replace(default, spike_min_new_codes=99)
    assert detect_spikes(_curve_of([1, 1, 1, 9]), strict) == []


def test_the_policy_round_trips_through_json_with_the_new_fields() -> None:
    payload = CheckpointPolicy(spike_factor=3.5, spike_window=5, spike_min_new_codes=2).to_json()
    assert payload["spike_factor"] == 3.5
    assert payload["spike_window"] == 5
    assert payload["spike_min_new_codes"] == 2
    assert json.loads(json.dumps(payload)) == payload


def test_a_window_below_one_is_clamped_to_one() -> None:
    """A zero-length window has no median; one previous batch is the honest minimum."""
    curve = _curve_of([1, 9, 1, 1])
    spikes = detect_spikes(curve, replace(CheckpointPolicy(), spike_window=0))
    assert [s.batch for s in spikes] == [2]
    assert spikes[0].window == 1


# --------------------------------------------------------------------------- #
# 8. Serialisation
# --------------------------------------------------------------------------- #


def test_every_result_object_serialises_to_json_deterministically() -> None:
    curve = _curve_of([1, 1, 1, 9])
    spikes = detect_spikes(curve, CheckpointPolicy())

    for obj in (curve, curve.points[0], spikes[0]):
        payload = obj.to_json()
        text = json.dumps(payload, sort_keys=True)
        assert json.loads(text) == payload
        assert "Infinity" not in text and "NaN" not in text

    assert set(curve.to_json()) == {
        "source",
        "batch_size",
        "total_codes",
        "saturated_at_batch",
        "points",
    }
    assert set(spikes[0].to_json()) == {
        "batch",
        "new_codes",
        "baseline",
        "ratio",
        "rule",
        "window",
        "reason",
    }


def test_the_curve_exposes_its_counts_and_its_last_point() -> None:
    curve = _curve_of([1, 1, 1, 9])
    assert curve.new_code_counts() == (1, 1, 1, 9)
    assert curve.point(4) is not None and curve.point(4).new_codes == 9  # type: ignore[union-attr]
    assert curve.point(99) is None
    assert curve.last() is not None and curve.last().batch == 4  # type: ignore[union-attr]
    assert code_growth([], batch_size=4).last() is None


def test_the_dataclasses_are_frozen() -> None:
    curve = _curve_of([1, 1, 1, 9])
    spike = detect_spikes(curve, CheckpointPolicy())[0]
    for obj, attribute in ((curve, "batch_size"), (curve.points[0], "batch"), (spike, "batch")):
        with pytest.raises(Exception):  # noqa: B017 - FrozenInstanceError is a subclass
            setattr(obj, attribute, 0)
    assert isinstance(curve, GrowthCurve)
    assert isinstance(curve.points[0], GrowthPoint)
    assert isinstance(spike, Spike)


def test_an_admission_event_without_a_response_id_is_skipped_not_guessed() -> None:
    """A `code_created` row that names no response cannot be placed in a batch.

    Attributing it to the nearest response would invent a fact about the run; dropping
    it understates the growth by one code and says nothing false. The response order is
    unaffected either way.
    """
    events = [
        {"event": "response_prepared", "subject": "1", "payload": {}},
        {"event": "code_created", "subject": "fam-good", "payload": {"response_id": 1}},
        {"event": "code_created", "subject": "fam-orphan", "payload": {}},
        {"event": "code_created", "subject": "fam-also_orphan"},
        {"event": "response_prepared", "subject": "not-a-number", "payload": {}},
    ]
    curve = growth_from_audit(events, batch_size=2)
    assert [p.new_code_names for p in curve.points] == [("fam-good",)]
    assert curve.points[0].responses_in_batch == 1
