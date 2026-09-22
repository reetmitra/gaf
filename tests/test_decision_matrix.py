"""The fast-loop / slow-loop decision matrix (`gaf.pipeline.decision_matrix`).

The PI asked which decisions each loop takes. The answer has to be an artefact, and it
has to be one that cannot quietly stop being true. Nine claims:

1. **The matrix is data, not prose.** Every row is a frozen `DecisionRule` with the
   same eight fields, drawn from closed vocabularies, and the whole thing serialises.
2. **It cannot drift from the code.** Every route the router can return, every member
   of `slow_loop.TRIGGERS` and every member of `models.OPERATION_TYPES` is covered by
   some row; every row's `source` resolves to a callable that really exists.
3. **The conditions carry the numbers in force.** A row's condition is rendered against
   the `RunConfig` it is given, so a matrix printed for a run states that run's
   thresholds and not the defaults.
4. **The renderers are deterministic.** The same config renders byte-identical Markdown
   and JSON.
5. **`evaluate_handover` decides and does not measure.** It delegates to `health` and
   `growth`, and every handover row it can fire is a row of the matrix.
6. **The spacing hold is a decision the matrix states**: a trigger without spacing is
   held, and the evaluation says which rule was held rather than dropping it.
7. **The precedence is one implementation.** `should_checkpoint` and
   `evaluate_handover` name the trigger through the same function, in the documented
   order: health, spike, floor, cadence.
8. **It is wired into the fast loop at every batch boundary** — one evaluation and one
   `checkpoint_evaluated` event per batch, `checkpoint_due` derived from the trace
   rather than recomputed, and an optional halt that still closes the run normally.
9. **The report prints it** and `write_decision_matrix` writes the static matrix beside
   the run report, both deterministically and both surviving the run.json round trip.

No key, no network, no real data: the embedders are stubs and the codebooks invented,
and the only corpus is `tests.fixtures.corpus`.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from gaf.checks.growth import code_growth, detect_spikes
from gaf.config import CheckpointPolicy, RunConfig
from gaf.embed.protocol import Route
from gaf.models import OPERATION_TYPES, Assignment, Code, Codebook, Evidence
from gaf.pipeline import slow_loop
from gaf.pipeline.decision_matrix import (
    CHECKPOINT_DUE,
    CONTINUE,
    DECIDED_BY,
    DECISION_MATRIX,
    HANDOVER_RULES,
    LOOPS,
    TRIGGER_PRECEDENCE,
    VERDICTS,
    DecisionRule,
    HandoverEvaluation,
    evaluate_handover,
    first_trigger,
    matrix_to_json,
    render_matrix_markdown,
    resolve_source,
    rule,
)
from gaf.pipeline.fast_loop import (
    FastLoopResult,
    batches,
    offline_components,
    run_fast_loop,
)
from gaf.report.run_report import (
    DECISION_MATRIX_NAME,
    RunArtefact,
    render_run_report,
    write_decision_matrix,
)
from gaf.store.blackboard import Blackboard
from tests.fixtures.corpus import synthetic_corpus

# --------------------------------------------------------------------------- #
# Stubs — invented codebooks, never a respondent's words
# --------------------------------------------------------------------------- #


class OneVectorEmbedder:
    """Every text is the same vector, so every comparable leaf pair scores 1.0.

    The geometry that reliably trips M4's near-duplicate count, which is the health
    handover row's input.
    """

    space_id = "stub-one-8"
    dim = 8

    def embed_one(self, text: str) -> np.ndarray:
        return np.ones(self.dim, dtype=np.float64) / np.sqrt(self.dim)

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float64)
        return np.vstack([self.embed_one(text) for text in texts])


class DistinctEmbedder:
    """A deterministic one-hot per text, so nothing is ever a near duplicate."""

    space_id = "stub-distinct-64"
    dim = 64

    def embed_one(self, text: str) -> np.ndarray:
        vector = np.zeros(self.dim, dtype=np.float64)
        vector[sum(ord(c) for c in text) % self.dim] = 1.0
        return vector

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float64)
        return np.vstack([self.embed_one(text) for text in texts])


def quiet_codebook(n_leaves: int = 2) -> Codebook:
    """A small, well-formed two-level codebook with invented descriptions."""
    codes = [Code(id="c-topic", name="topic", description="A family of invented codes.")]
    for index in range(n_leaves):
        codes.append(
            Code(
                id=f"c-topic-leaf_{index}",
                name=f"topic-leaf_{index}",
                description=f"Invented sub-code number {index}.",
                parent_id="c-topic",
                created_in_snapshot="snap-stub",
                evidence=[
                    Evidence(
                        response_id=1 + index,
                        quote=f"invented evidence for leaf {index}",
                        verified=True,
                        score=1.0,
                    )
                ],
            )
        )
    return Codebook(codes={code.id: code for code in codes})


def config_for(run_id: str, **changes: object) -> RunConfig:
    settings: dict[str, object] = {"offline": True, "cache_dir": None}
    settings.update(changes)
    return RunConfig(run_id=run_id, **settings)  # type: ignore[arg-type]


def growth_of(counts: Sequence[int], *, responses_per_batch: int = 10) -> object:
    """A growth curve with exactly these per-batch new-code counts."""
    rows: list[Assignment] = []
    ids: list[int] = []
    response_id = 1
    minted = 0
    for count in counts:
        for position in range(responses_per_batch):
            ids.append(response_id)
            if position == 0:
                for _ in range(count):
                    rows.append(
                        Assignment(response_id, f"segment {response_id}", f"fam-c{minted}")
                    )
                    minted += 1
            elif minted:
                rows.append(Assignment(response_id, f"segment {response_id}", "fam-c0"))
            response_id += 1
    return code_growth(rows, batch_size=responses_per_batch, response_ids=ids, order=ids)


# --------------------------------------------------------------------------- #
# 1. The matrix is data
# --------------------------------------------------------------------------- #


def test_every_row_is_a_frozen_rule_from_a_closed_vocabulary() -> None:
    """Claim 1. A matrix with a free-text `loop` column is prose with a table around it."""
    assert DECISION_MATRIX, "the matrix must not be empty"
    seen: set[str] = set()
    for row in DECISION_MATRIX:
        assert isinstance(row, DecisionRule)
        assert row.id not in seen, f"duplicate rule id {row.id!r}"
        seen.add(row.id)
        assert row.loop in LOOPS, f"{row.id}: loop {row.loop!r}"
        assert row.decided_by in DECIDED_BY, f"{row.id}: decided_by {row.decided_by!r}"
        for field_name in ("decision", "condition", "outcome", "audit_event", "source"):
            assert getattr(row, field_name), f"{row.id}: empty {field_name}"
        with pytest.raises(Exception):  # noqa: B017 - FrozenInstanceError is a subclass
            row.id = "mutated"  # type: ignore[misc]


def test_the_matrix_covers_all_three_loops() -> None:
    covered = {row.loop for row in DECISION_MATRIX}
    assert covered == set(LOOPS)


def test_rows_can_be_looked_up_by_id_and_an_unknown_id_is_refused() -> None:
    first = DECISION_MATRIX[0]
    assert rule(first.id) is first
    with pytest.raises(KeyError, match="no decision rule"):
        rule("handover.not_a_rule")


# --------------------------------------------------------------------------- #
# 2. It cannot drift from the code
# --------------------------------------------------------------------------- #


def _covered() -> set[str]:
    return {token for row in DECISION_MATRIX for token in row.covers}


def test_every_route_the_router_can_return_is_in_the_matrix() -> None:
    """Claim 2. A fourth route added to `Route` fails here, by name."""
    missing = {route.value for route in Route} - _covered()
    assert not missing, f"routes absent from the decision matrix: {sorted(missing)}"


def test_every_checkpoint_trigger_is_in_the_matrix() -> None:
    missing = set(slow_loop.TRIGGERS) - _covered()
    assert not missing, f"triggers absent from the decision matrix: {sorted(missing)}"


def test_every_operation_type_is_in_the_matrix() -> None:
    """The wide operation set is the anti-flattening mechanism; the matrix states it."""
    missing = set(OPERATION_TYPES) - _covered()
    assert not missing, f"operation types absent from the decision matrix: {sorted(missing)}"


def test_every_source_resolves_to_the_function_it_names() -> None:
    """A renamed function makes its row a lie; this is the test that notices.

    ``assert callable(target)`` was dead: `resolve_source` already raises when the
    target is not callable, so the line could never fail (R1, weak-test scan). What
    can fail, and is asserted instead, is that the object resolved is the one the row
    names and lives where the row says it does.
    """
    assert DECISION_MATRIX, "an empty matrix would pass every assertion below"
    for row in DECISION_MATRIX:
        module_name, _, attribute = row.source.partition(":")
        target = resolve_source(row.source)
        assert target.__module__ == module_name or module_name.startswith(
            target.__module__
        ), f"{row.id}: {row.source} resolves into {target.__module__}"
        assert target.__qualname__ == attribute, (
            f"{row.id}: {row.source} resolves to {target.__qualname__}"
        )


def test_an_unresolvable_source_is_refused_loudly() -> None:
    with pytest.raises(ValueError, match="module:function"):
        resolve_source("gaf.pipeline.router")
    with pytest.raises(ValueError, match="no attribute"):
        resolve_source("gaf.pipeline.router:not_a_function")
    with pytest.raises(ValueError, match="not callable"):
        resolve_source("gaf.pipeline.router:ORIGINS")


def test_every_covered_token_is_one_the_code_actually_defines() -> None:
    """Coverage that names a token nothing defines would satisfy claim 2 vacuously."""
    known = (
        {route.value for route in Route}
        | set(slow_loop.TRIGGERS)
        | set(OPERATION_TYPES)
        | set(VERDICTS)
    )
    unknown = _covered() - known
    assert not unknown, f"the matrix claims to cover tokens nothing defines: {sorted(unknown)}"


# --------------------------------------------------------------------------- #
# 3 and 4. Rendering
# --------------------------------------------------------------------------- #


def test_conditions_are_rendered_with_the_numbers_in_force() -> None:
    """Claim 3. A matrix that printed the defaults for a re-tuned run would mislead."""
    config = config_for(
        "rendered",
        rules=replace(RunConfig().rules, tau_high=0.91, tau_low=0.11),
        checkpoints=replace(CheckpointPolicy(), spike_factor=3.5, max_new_codes_per_batch=42),
    )
    payload = matrix_to_json(config)
    text = json.dumps(payload)
    assert "0.91" in text and "0.11" in text
    assert "3.5" in text and "42" in text

    default = json.dumps(matrix_to_json(RunConfig()))
    assert "0.8" in default and "0.91" not in default


def test_an_unrendered_rule_still_serialises() -> None:
    """`to_json()` takes no argument, per the house rule; the template survives."""
    row = DECISION_MATRIX[0]
    payload = row.to_json()
    assert set(payload) == {
        "id",
        "decision",
        "loop",
        "decided_by",
        "condition",
        "outcome",
        "audit_event",
        "source",
        "covers",
    }
    assert json.loads(json.dumps(payload)) == payload


def test_the_renderers_are_deterministic() -> None:
    """Claim 4. Two identical configs must render byte-identical artefacts."""
    config = config_for("determinism")
    assert render_matrix_markdown(config) == render_matrix_markdown(config_for("determinism"))
    assert matrix_to_json(config) == matrix_to_json(config_for("determinism"))


def test_the_markdown_names_every_rule_and_every_column() -> None:
    text = render_matrix_markdown(config_for("markdown"))
    for row in DECISION_MATRIX:
        assert row.id in text, f"{row.id} missing from the rendered matrix"
    for heading in ("decision", "loop", "decided by", "condition", "outcome", "audit event"):
        assert heading in text
    assert "frame" not in text.lower(), "ADR-0005: the word does not appear in output"
    assert matrix_to_json(config_for("markdown"))["n_rules"] == len(DECISION_MATRIX)


# --------------------------------------------------------------------------- #
# 5, 6 and 7. evaluate_handover
# --------------------------------------------------------------------------- #


def test_a_quiet_batch_continues() -> None:
    evaluation = evaluate_handover(
        quiet_codebook(),
        DistinctEmbedder(),
        config_for("quiet"),
        batch=1,
        responses_coded=10,
        responses_since_checkpoint=10,
        curve=growth_of([1]),  # type: ignore[arg-type]
        previous=quiet_codebook(),
    )
    assert evaluation.verdict == CONTINUE
    assert evaluation.checkpoint_due is False
    assert evaluation.trigger == "none"
    assert evaluation.fired == ()
    assert evaluation.reason, "a verdict must always say why"


def test_near_duplicate_pairs_fire_the_health_row() -> None:
    """Claim 5. The measuring is `health`'s; the deciding is this module's."""
    evaluation = evaluate_handover(
        quiet_codebook(n_leaves=4),
        OneVectorEmbedder(),
        config_for("health"),
        batch=2,
        responses_coded=20,
        responses_since_checkpoint=20,
        curve=growth_of([1, 1]),  # type: ignore[arg-type]
        previous=quiet_codebook(n_leaves=4),
    )
    assert evaluation.verdict == CHECKPOINT_DUE
    assert evaluation.trigger == "health"
    assert "handover.near_duplicates" in evaluation.fired
    assert evaluation.near_duplicate_pairs > 0
    assert "near-duplicate pairs" in evaluation.reason


def test_a_spike_fires_the_spike_row_and_carries_the_spike() -> None:
    curve = growth_of([1, 1, 1, 9])
    assert [s.batch for s in detect_spikes(curve, CheckpointPolicy())] == [4]  # type: ignore[arg-type]

    evaluation = evaluate_handover(
        quiet_codebook(),
        DistinctEmbedder(),
        config_for("spike"),
        batch=4,
        responses_coded=40,
        responses_since_checkpoint=40,
        curve=curve,  # type: ignore[arg-type]
        previous=quiet_codebook(),
    )
    assert evaluation.trigger == "spike"
    assert "handover.spike" in evaluation.fired
    assert evaluation.spike is not None and evaluation.spike.batch == 4
    assert evaluation.to_json()["spike"]["new_codes"] == 9
    assert "spike" in evaluation.reason.lower()


def test_the_hard_floor_fires_without_any_event() -> None:
    evaluation = evaluate_handover(
        quiet_codebook(),
        DistinctEmbedder(),
        config_for("floor", checkpoints=replace(CheckpointPolicy(), hard_floor_responses=10)),
        batch=1,
        responses_coded=10,
        responses_since_checkpoint=10,
        curve=growth_of([1]),  # type: ignore[arg-type]
        previous=quiet_codebook(),
    )
    assert evaluation.trigger == "floor"
    assert "handover.floor" in evaluation.fired
    assert evaluation.verdict == CHECKPOINT_DUE


def test_the_fixed_cadence_fires_on_schedule() -> None:
    policy = replace(CheckpointPolicy(), mode="fixed")
    evaluation = evaluate_handover(
        quiet_codebook(),
        DistinctEmbedder(),
        config_for("cadence", checkpoints=policy),
        batch=2,
        responses_coded=20,
        responses_since_checkpoint=20,
        curve=growth_of([1, 1]),  # type: ignore[arg-type]
        previous=quiet_codebook(),
    )
    assert evaluation.trigger == "cadence"
    assert "handover.cadence" in evaluation.fired

    off = evaluate_handover(
        quiet_codebook(),
        DistinctEmbedder(),
        config_for("cadence-off", checkpoints=policy),
        batch=3,
        responses_coded=23,
        responses_since_checkpoint=23,
        curve=growth_of([1, 1, 1]),  # type: ignore[arg-type]
        previous=quiet_codebook(),
    )
    assert off.trigger == "none"


def test_a_trigger_without_spacing_is_held_and_said_to_be_held() -> None:
    """Claim 6. Keep-and-say, never silently drop: the held rule is named."""
    evaluation = evaluate_handover(
        quiet_codebook(n_leaves=4),
        OneVectorEmbedder(),
        config_for("held"),
        batch=1,
        responses_coded=4,
        responses_since_checkpoint=4,
        curve=growth_of([1], responses_per_batch=4),  # type: ignore[arg-type]
        previous=quiet_codebook(n_leaves=4),
    )
    assert evaluation.verdict == CONTINUE
    assert evaluation.trigger == "none"
    assert "handover.near_duplicates" in evaluation.held
    assert "handover.near_duplicates" not in evaluation.fired
    assert "held" in evaluation.reason


def test_every_rule_evaluate_handover_can_name_is_a_handover_row() -> None:
    """Claim 5, the other half: the evaluation cannot invent a rule id."""
    ids = {row.id for row in HANDOVER_RULES}
    assert ids, "there must be handover rows"
    assert ids <= {row.id for row in DECISION_MATRIX}

    evaluation = evaluate_handover(
        quiet_codebook(n_leaves=4),
        OneVectorEmbedder(),
        config_for("names", checkpoints=replace(CheckpointPolicy(), hard_floor_responses=1)),
        batch=4,
        responses_coded=40,
        responses_since_checkpoint=40,
        curve=growth_of([1, 1, 1, 9]),  # type: ignore[arg-type]
        previous=quiet_codebook(n_leaves=4),
    )
    assert set(evaluation.fired) | set(evaluation.held) <= ids
    assert len(evaluation.fired) > 1, "this batch trips several rows at once"


def test_the_precedence_is_health_then_spike_then_floor_then_cadence() -> None:
    """Claim 7. One function names the trigger, and this is its whole truth table."""
    assert TRIGGER_PRECEDENCE == ("health", "spike", "floor", "cadence")
    assert first_trigger(health=True, spike=True, floor=True, cadence=True) == "health"
    assert first_trigger(health=False, spike=True, floor=True, cadence=True) == "spike"
    assert first_trigger(health=False, spike=False, floor=True, cadence=True) == "floor"
    assert first_trigger(health=False, spike=False, floor=False, cadence=True) == "cadence"
    assert first_trigger(health=False, spike=False, floor=False, cadence=False) == "none"


def test_should_checkpoint_and_evaluate_handover_agree_on_the_trigger() -> None:
    """The two entry points into one precedence must not be able to disagree."""
    config = config_for("agree")
    codebook = quiet_codebook(n_leaves=4)
    curve = growth_of([1, 1, 1, 9])

    handover = evaluate_handover(
        codebook,
        OneVectorEmbedder(),
        config,
        batch=4,
        responses_coded=40,
        responses_since_checkpoint=40,
        curve=curve,  # type: ignore[arg-type]
        previous=codebook,
    )
    checkpoint = slow_loop.should_checkpoint(
        codebook,
        OneVectorEmbedder(),
        config,
        responses_coded=40,
        responses_since_checkpoint=40,
        previous=codebook,
        curve=curve,  # type: ignore[arg-type]
    )
    assert checkpoint.trigger == handover.trigger
    assert checkpoint.fires is handover.checkpoint_due


def test_should_checkpoint_gains_the_spike_trigger() -> None:
    """`spike` is now a member of `TRIGGERS`, and a spike alone fires a checkpoint."""
    assert "spike" in slow_loop.TRIGGERS

    config = config_for("spiked")
    trigger = slow_loop.should_checkpoint(
        quiet_codebook(),
        DistinctEmbedder(),
        config,
        responses_coded=40,
        responses_since_checkpoint=40,
        previous=quiet_codebook(),
        curve=growth_of([1, 1, 1, 9]),  # type: ignore[arg-type]
    )
    assert trigger.fires is True
    assert trigger.trigger == "spike"
    assert trigger.signals.spike_detected is True
    assert trigger.spike is not None
    assert trigger.to_json()["spike"]["batch"] == 4


def test_should_checkpoint_without_a_curve_behaves_exactly_as_before() -> None:
    """The spike argument is additive: no curve, no spike, no behaviour change."""
    config = config_for("nocurve")
    trigger = slow_loop.should_checkpoint(
        quiet_codebook(),
        DistinctEmbedder(),
        config,
        responses_coded=40,
        responses_since_checkpoint=40,
        previous=quiet_codebook(),
    )
    assert trigger.trigger == "none"
    assert trigger.spike is None
    assert trigger.signals.spike_detected is False
    assert trigger.to_json()["spike"] is None


# --------------------------------------------------------------------------- #
# Serialisation
# --------------------------------------------------------------------------- #


def test_the_evaluation_serialises_deterministically() -> None:
    evaluation = evaluate_handover(
        quiet_codebook(),
        DistinctEmbedder(),
        config_for("json"),
        batch=1,
        responses_coded=10,
        responses_since_checkpoint=10,
        curve=growth_of([1]),  # type: ignore[arg-type]
        previous=quiet_codebook(),
    )
    payload = evaluation.to_json()
    assert json.loads(json.dumps(payload, sort_keys=True)) == payload
    assert set(payload) == {
        "batch",
        "responses_coded",
        "responses_in_batch",
        "responses_since_checkpoint",
        "new_codes",
        "cumulative_codes",
        "near_duplicate_pairs",
        "spike",
        "fired",
        "held",
        "trigger",
        "verdict",
        "reason",
    }
    assert payload["verdict"] in VERDICTS
    assert isinstance(evaluation, HandoverEvaluation)


def test_evaluate_handover_without_a_curve_still_evaluates() -> None:
    """A caller with no growth curve yet loses the spike row, not the evaluation."""
    evaluation = evaluate_handover(
        quiet_codebook(),
        DistinctEmbedder(),
        config_for("nocurve-handover"),
        batch=1,
        responses_coded=10,
        responses_since_checkpoint=10,
        previous=quiet_codebook(),
    )
    assert evaluation.spike is None
    assert evaluation.responses_in_batch == 0
    assert evaluation.verdict in VERDICTS


# --------------------------------------------------------------------------- #
# 8. Wired into the fast loop — one evaluation per batch boundary
# --------------------------------------------------------------------------- #


def _run(run_id: str, *, halt: bool = False, **changes: object) -> FastLoopResult:
    config = config_for(run_id, **changes)
    with Blackboard(":memory:") as board:
        board.register_run(config)
        responses = synthetic_corpus()
        board.write_responses(responses)
        result = run_fast_loop(
            responses,
            config=config,
            board=board,
            components=offline_components(config),
            halt_on_checkpoint=halt,
        )
        result.stats.decision_trace  # noqa: B018 - read inside the board's lifetime
        events = board.audit(run_id).counts()
    return result, events  # type: ignore[return-value]


def test_the_handover_is_evaluated_at_every_batch_boundary() -> None:
    """Claim 8. It used to be computed once, after the last response.

    A run that only asks at the end cannot say that the codebook came due at batch 2
    and had quietened by batch 7, which is exactly the shape the PI described.
    """
    result, events = _run("per-batch")  # type: ignore[misc]
    n_batches = len(batches(synthetic_corpus(), result.stats.n_responses and 10))

    trace = result.stats.decision_trace
    assert len(trace) == n_batches, trace
    assert [row["batch"] for row in trace] == list(range(1, n_batches + 1))
    assert events["checkpoint_evaluated"] == n_batches


def test_responses_since_checkpoint_is_right_per_batch() -> None:
    """It was the whole run's count for every batch; now it is the running total.

    No checkpoint is *taken* inside a fast-loop run, so the count never resets — but it
    must at least grow batch by batch, or the spacing rule is measured against a number
    that describes a batch that has not happened yet.
    """
    result, _ = _run("spacing-per-batch")  # type: ignore[misc]
    trace = result.stats.decision_trace
    counts = [row["responses_since_checkpoint"] for row in trace]
    assert counts == sorted(counts)
    assert counts == [row["responses_coded"] for row in trace]
    assert counts[-1] == result.stats.n_responses


def test_new_codes_is_this_batch_and_not_the_whole_run() -> None:
    """The end-of-run computation passed no `previous`, so every code read as new."""
    result, _ = _run("per-batch-new-codes")  # type: ignore[misc]
    trace = result.stats.decision_trace
    assert len(trace) > 1, "this claim needs more than one batch"
    assert sum(row["new_codes"] for row in trace) <= result.stats.codes_final + len(trace)
    assert trace[-1]["cumulative_codes"] == result.stats.codes_final


def test_checkpoint_due_is_derived_from_the_trace() -> None:
    """One computation behind "is the slow loop due", not two that can disagree."""
    result, _ = _run("derived")  # type: ignore[misc]
    due = result.stats.checkpoint_due
    last = result.stats.decision_trace[-1]

    assert set(due) >= {"fires", "trigger", "reason"}, "the old keys must survive"
    assert due["trigger"] == last["trigger"]
    assert due["reason"] == last["reason"]
    assert due["fires"] is (last["verdict"] == CHECKPOINT_DUE)
    assert due["batch"] == last["batch"]
    assert due["batches_due"] == [
        row["batch"] for row in result.stats.decision_trace if row["verdict"] == CHECKPOINT_DUE
    ]


def test_the_trace_is_deterministic() -> None:
    """Two runs of the same corpus must produce the same decisions, byte for byte."""
    first, _ = _run("trace-a")  # type: ignore[misc]
    second, _ = _run("trace-b")  # type: ignore[misc]
    assert json.dumps(first.stats.decision_trace, sort_keys=True) == json.dumps(
        second.stats.decision_trace, sort_keys=True
    )


def test_the_fast_loop_does_not_halt_by_default() -> None:
    """Default `False`: the loop reports the handover and never blocks for it."""
    result, _ = _run("no-halt", checkpoints=replace(CheckpointPolicy(), hard_floor_responses=1))  # type: ignore[misc]
    assert result.stats.checkpoint_due["fires"] is True
    assert result.stats.halted_at_batch is None
    assert result.stats.responses_uncoded == 0
    assert result.stats.n_responses == len(synthetic_corpus())


def test_halt_on_checkpoint_stops_after_the_due_batch_and_closes_normally() -> None:
    """A halted run is a short run, never a half-written one.

    The closing checks, the final snapshot and `run_completed` all still happen, so the
    run directory a halted run leaves is readable by every tool that reads a complete
    one — and it says plainly what was left uncoded.
    """
    policy = replace(CheckpointPolicy(), hard_floor_responses=1, min_responses_between_checkpoints=0)
    result, events = _run("halted", halt=True, checkpoints=policy)  # type: ignore[misc]

    assert result.stats.halted_at_batch == 1
    assert len(result.stats.decision_trace) == 1
    assert result.stats.n_responses == 10
    assert result.stats.responses_uncoded == len(synthetic_corpus()) - 10
    assert result.stats.checkpoint_due["fires"] is True

    # closed normally
    assert events["run_completed"] == 1
    assert events["checkpoint_evaluated"] == 1
    assert result.snapshot_ids[-1] != result.snapshot_ids[0]
    assert result.codebook.codes, "a halted run still produced a codebook"


def test_a_halt_that_never_comes_due_codes_everything() -> None:
    """`halt_on_checkpoint` is a stop condition, not a limit on the run."""
    result, _ = _run(  # type: ignore[misc]
        "halt-quiet",
        halt=True,
        checkpoints=replace(
            CheckpointPolicy(),
            hard_floor_responses=10_000,
            max_near_duplicate_pairs=10_000,
            max_new_codes_per_batch=10_000,
            spike_min_new_codes=10_000,
        ),
    )
    assert result.stats.halted_at_batch is None
    assert result.stats.responses_uncoded == 0
    assert result.stats.n_responses == len(synthetic_corpus())


# --------------------------------------------------------------------------- #
# 9. The report
# --------------------------------------------------------------------------- #


def _matrix_section(text: str) -> str:
    """Just the DECISION MATRIX section of a rendered run report."""
    head, _, tail = text.partition("DECISION MATRIX")
    assert head, "the report must have something before the section"
    return tail.partition("\nCHECKS\n")[0]


def _artefact(run_id: str = "report") -> RunArtefact:
    config = config_for(run_id)
    with Blackboard(":memory:") as board:
        board.register_run(config)
        responses = synthetic_corpus()
        board.write_responses(responses)
        result = run_fast_loop(
            responses, config=config, board=board, components=offline_components(config)
        )
    return RunArtefact.from_result(result, config=config)


def test_the_run_report_has_a_decision_matrix_section() -> None:
    text = render_run_report(_artefact())
    assert "DECISION MATRIX" in text
    for heading in ("batch", "new codes", "near-dup", "spike", "verdict", "reason"):
        assert heading in text, heading
    assert "Code-growth spikes:" in text
    assert "frame" not in text.lower() or "framework" in text.lower()


def test_the_run_report_stays_deterministic_with_the_new_section() -> None:
    assert render_run_report(_artefact("det-a")) == render_run_report(_artefact("det-a"))


def test_write_decision_matrix_writes_the_static_matrix_beside_the_report(
    tmp_path: Path,
) -> None:
    """T6 owns `gaf/cli/report.py`; this is the function it calls."""
    artefact = _artefact("matrix-file")
    path = write_decision_matrix(tmp_path / "run", artefact)

    assert path.name == DECISION_MATRIX_NAME
    text = path.read_text(encoding="utf-8")
    assert text == render_matrix_markdown(artefact.run_config())
    for row in DECISION_MATRIX:
        assert row.id in text
    # and it is a pure function of the artefact
    assert write_decision_matrix(tmp_path / "run", artefact).read_text(encoding="utf-8") == text


def test_the_artefact_rebuilds_enough_config_for_the_matrix() -> None:
    artefact = _artefact("config-echo")
    config = artefact.run_config()
    assert config.rules.tau_high == RunConfig().rules.tau_high
    assert config.checkpoints.spike_factor == CheckpointPolicy().spike_factor
    assert config.batch_size == RunConfig().batch_size


def test_the_run_json_round_trip_carries_the_trace() -> None:
    """`gaf report` reads run.json, so the trace has to survive the round trip."""
    artefact = _artefact("round-trip")
    document = json.loads(artefact.to_json_str())
    restored = RunArtefact.from_json(document)

    assert restored.stats.decision_trace == artefact.stats.decision_trace
    assert restored.stats.halted_at_batch == artefact.stats.halted_at_batch
    assert restored.stats.responses_uncoded == artefact.stats.responses_uncoded

    # The DECISION MATRIX section itself must be identical either way. The whole report
    # is *not* compared: `RunArtefact.to_json_str` sorts keys, so two count lines
    # elsewhere print their dicts in a different order when rendered from run.json than
    # from a live result. That predates this section and the CLI never hits it — `gaf
    # report` always renders from run.json — but it is not something to assert past.
    assert _matrix_section(render_run_report(restored)) == _matrix_section(
        render_run_report(artefact)
    )
    assert render_run_report(restored) == render_run_report(RunArtefact.from_json(document))


def test_a_run_json_written_before_the_trace_existed_still_renders() -> None:
    """The three new `RunStats` fields default, so an older run directory still opens."""
    artefact = _artefact("older")
    document = json.loads(artefact.to_json_str())
    for key in ("decision_trace", "halted_at_batch", "responses_uncoded"):
        document["result"]["stats"].pop(key)

    restored = RunArtefact.from_json(document)
    assert restored.stats.decision_trace == []
    assert restored.stats.halted_at_batch is None

    text = render_run_report(restored)
    assert "No batch boundary was evaluated" in text
    # with no trace, the spikes fall back to the curve the assignments show
    assert isinstance(restored.spikes(), list)
    assert restored.growth().total_codes >= 0


def test_the_report_names_a_halt_and_what_it_left_uncoded() -> None:
    policy = replace(CheckpointPolicy(), hard_floor_responses=1, min_responses_between_checkpoints=0)
    config = config_for("halt-report", checkpoints=policy)
    with Blackboard(":memory:") as board:
        board.register_run(config)
        responses = synthetic_corpus()
        board.write_responses(responses)
        result = run_fast_loop(
            responses,
            config=config,
            board=board,
            components=offline_components(config),
            halt_on_checkpoint=True,
        )
    text = render_run_report(RunArtefact.from_result(result, config=config))
    assert "halted" in text
    assert "after batch 1" in text
    assert "left uncoded" in text
    assert "closed normally" in text


def test_the_report_says_plainly_when_nothing_spiked() -> None:
    """A run with a ceiling nothing can reach has no spikes, and the report says so."""
    config = config_for(
        "no-spikes",
        checkpoints=replace(
            CheckpointPolicy(), max_new_codes_per_batch=10_000, spike_min_new_codes=10_000
        ),
    )
    with Blackboard(":memory:") as board:
        board.register_run(config)
        responses = synthetic_corpus()
        board.write_responses(responses)
        result = run_fast_loop(
            responses, config=config, board=board, components=offline_components(config)
        )
    text = render_run_report(RunArtefact.from_result(result, config=config))
    assert "Code-growth spikes:" in text
    assert "No batch admitted codes far out of step" in text


def test_a_due_batch_reports_the_rules_that_were_held() -> None:
    """The floor is not held by spacing; the event triggers beside it are.

    The interesting row is the one that came due anyway and still has to say that a
    second trigger was exceeded and held — keep-and-say, not silently drop.
    """
    policy = replace(
        CheckpointPolicy(), hard_floor_responses=1, min_responses_between_checkpoints=10_000
    )
    config = config_for("held-report", checkpoints=policy)
    with Blackboard(":memory:") as board:
        board.register_run(config)
        responses = synthetic_corpus()
        board.write_responses(responses)
        result = run_fast_loop(
            responses, config=config, board=board, components=offline_components(config)
        )

    first = result.stats.decision_trace[0]
    assert first["verdict"] == CHECKPOINT_DUE
    assert first["trigger"] == "floor"
    assert "handover.spacing_hold" in first["held"]
    assert "handover.new_codes" in first["held"]
    assert "handover.new_codes" not in first["fired"]

    text = render_run_report(RunArtefact.from_result(result, config=config))
    assert "held: " in text
