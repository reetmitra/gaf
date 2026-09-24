"""Tests for `gaf.report.timeline`.

Three sources feed these tests, matching how the module itself reads the store:

1. A real offline fast-loop run over `tests.fixtures.corpus.synthetic_corpus` —
   `build_timeline` against an actual audit log, for steps, batches and the
   fast-loop half of code biographies.
2. That same run driven through one or more real `run_checkpoint` calls (as
   `tests/test_slow_loop.py` does), covering merge, split, reparent, rename and
   create — for snapshot diffs, checkpoint markers and the slow-loop half of
   biographies.
3. Hand-written `Assignment` rows, for `timeline_from_assignments`.

No respondent text appears anywhere here: the corpus is the project's own synthetic
fixture, and every code name is either the fixture's own or invented for this file.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import replace
from typing import Any

import pytest

from gaf.agents.refactorer import RefactorerAgent
from gaf.config import RunConfig
from gaf.llm.base import LLMRequest, LLMResult, TaskType
from gaf.llm.mock import MockRefactorerClient
from gaf.models import Assignment, Codebook, Operation, Response
from gaf.pipeline.fast_loop import LoopComponents, offline_components, run_fast_loop
from gaf.pipeline.slow_loop import (
    ACCEPT,
    GateDecision,
    RejectAllGate,
    ScriptedGate,
    run_checkpoint,
)
from gaf.report.timeline import (
    CheckpointMarker,
    Timeline,
    build_timeline,
    timeline_from_assignments,
    timeline_svg,
)
from gaf.store.blackboard import Blackboard
from tests.fixtures.codebooks import toy_codebook
from tests.fixtures.corpus import synthetic_corpus
from tests.fixtures.embedding import StubEmbedder

# --------------------------------------------------------------------------- #
# Helpers — a fixed refactorer, mirroring tests/test_slow_loop.py's own style
# --------------------------------------------------------------------------- #


class FixedRefactorerClient(MockRefactorerClient):
    """A refactorer that always proposes one fixed edit script."""

    def __init__(self, operations: Sequence[Operation], reasoning: str = "a fixed test script") -> None:
        super().__init__()
        self._operations = [op.to_json() for op in operations]
        self._reasoning = reasoning

    def complete_json(self, request: LLMRequest) -> LLMResult:
        if request.task is not TaskType.REFACTOR:
            return self._wrong_task(request)
        return self._result(
            request, {"operations": list(self._operations), "reasoning": self._reasoning}
        )


def _config(run_id: str) -> RunConfig:
    return RunConfig(run_id=run_id, offline=True, cache_dir=None)


def _coded_run(run_id: str) -> tuple[Blackboard, RunConfig, LoopComponents]:
    """A real, offline fast-loop run over the synthetic corpus, stored in `board`."""
    config = _config(run_id)
    board = Blackboard(":memory:")
    components = offline_components(config)
    run_fast_loop(synthetic_corpus(), config=config, board=board, components=components)
    return board, config, components


def accept_all(n: int) -> ScriptedGate:
    return ScriptedGate([GateDecision(index=i, verdict=ACCEPT) for i in range(n)])


# --------------------------------------------------------------------------- #
# 1. build_timeline over a real fast-loop run
# --------------------------------------------------------------------------- #


def test_build_timeline_reports_one_step_per_response_in_log_order() -> None:
    board, config, _ = _coded_run("tl-steps")
    timeline = build_timeline(board, config.run_id)

    assert timeline.run_id == config.run_id
    assert len(timeline.steps) == 14  # the synthetic corpus's own size
    assert [step.response_id for step in timeline.steps] == sorted(
        step.response_id for step in timeline.steps
    ), "the fast loop codes in (source, response_id) order (ADR-0017)"
    assignments_written = {
        int(event.subject): int(event.payload["n_assignments"])
        for event in board.audit(config.run_id).events()
        if event.event == "assignments_written"
    }
    for step in timeline.steps:
        assert step.snapshot_id is not None
        # `>= 0` is vacuous for a count (R1, weak-test scan). A response either wrote
        # assignment rows, and the step carries that number, or it wrote none at all.
        assert step.n_assignments == assignments_written.get(step.response_id, 0)
        assert step.duplicate_of is None  # no duplicate content in this fixture
    assert sum(step.n_assignments for step in timeline.steps) == sum(assignments_written.values())
    assert any(step.n_assignments > 0 for step in timeline.steps)


def test_build_timeline_batches_by_the_snapshot_the_coders_actually_read() -> None:
    board, config, _ = _coded_run("tl-batches")
    timeline = build_timeline(board, config.run_id)

    # batch_size=10 (RunConfig default) over 14 responses -> two batches, numbered
    # from 1 (matching gaf.pipeline.decision_matrix.HandoverEvaluation.batch).
    assert [batch.batch for batch in timeline.batches] == [1, 2]
    assert sum(batch.n_responses for batch in timeline.batches) == 14
    assert timeline.batches[0].snapshot_id != timeline.batches[1].snapshot_id
    # Every response in a batch was actually prepared against that batch's snapshot.
    snap_of_step = {step.response_id: step.snapshot_id for step in timeline.steps}
    for batch in timeline.batches:
        for response_id in batch.responses:
            assert snap_of_step[response_id] == batch.snapshot_id

    # Cumulative codes is monotonic and ends at the run's own total.
    cumulative = [batch.cumulative_codes for batch in timeline.batches]
    assert cumulative == sorted(cumulative)
    total_created = sum(len(step.codes_created) for step in timeline.steps)
    assert cumulative[-1] == total_created
    assert sum(batch.n_new_codes for batch in timeline.batches) == total_created
    # No batch is credited with a code some other batch actually created.
    assert len({name for batch in timeline.batches for name in batch.new_codes}) == total_created


def test_build_timeline_step_created_and_merged_names_match_the_codebook() -> None:
    """Re-implementing `_created_and_merged_by_response` line for line and asserting
    equality can only fail if `build_timeline` stops calling the helper (R1, weak-test
    scan). These expectations come from the *codebook* instead: every code the run
    holds was created on exactly one response, and every step's created names are
    codes that exist and are new at that point.
    """
    board, config, _ = _coded_run("tl-created-merged")
    timeline = build_timeline(board, config.run_id)
    final = board.read_snapshots(run_id=config.run_id)[-1].codebook
    live = {code.name for code in final.sorted_codes()}

    created: list[str] = []
    for step in timeline.steps:
        assert set(step.codes_created) <= live
        assert not set(step.codes_created) & set(created), "a code is created once"
        created.extend(step.codes_created)
        assert set(step.codes_merged) <= set(created), (
            "evidence can only be merged into a code that already exists"
        )
        assert len(step.codes_created) + len(step.codes_merged) <= step.n_assignments or (
            step.duplicate_of is not None
        )
    assert sorted(created) == sorted(live)


def test_build_timeline_counts_judge_consultations_per_batch() -> None:
    """The offline run escalates nothing, so ``0 == 0`` would pass whatever the code
    did (R1, weak-test scan). The count is asserted as the literal 0 it is, and the
    non-zero case is `test_judge_consultations_are_counted_against_the_batch_being_coded`.
    """
    board, config, _ = _coded_run("tl-judge")
    timeline = build_timeline(board, config.run_id)
    assert board.audit(config.run_id).count("judge_consulted") == 0
    assert [batch.judge_consultations for batch in timeline.batches] == [0, 0]


def test_build_timeline_has_no_snapshot_diffs_or_checkpoints_without_a_checkpoint() -> None:
    board, config, _ = _coded_run("tl-no-checkpoint")
    timeline = build_timeline(board, config.run_id)
    assert timeline.checkpoints == []
    # Fast-loop-only snapshot diffs never show a rename: the fast loop cannot restructure.
    assert all(diff.renamed == [] for diff in timeline.snapshot_diffs)
    assert len(timeline.snapshot_diffs) == len(board.read_snapshots(run_id=config.run_id)) - 1


def test_every_code_the_run_created_has_a_coded_biography_and_is_alive() -> None:
    board, config, _ = _coded_run("tl-bio-alive")
    timeline = build_timeline(board, config.run_id)

    created_events = board.audit(config.run_id).events(event="code_created")
    assert len(created_events) == len(timeline.biographies)
    for event in created_events:
        code_id = str(event.payload["code_id"])
        bio = timeline.biographies[code_id]
        assert bio.name == str(event.subject)
        assert bio.born.origin == "coded"
        assert bio.born.response_id == int(event.payload["response_id"])
        assert bio.born.coders, "an accepted candidate always has at least one proposer"
        assert bio.fate_kind == "alive"
        assert bio.fate == "alive"
        assert bio.evidence_over_time, "a birth is itself an evidence point"


def test_build_timeline_is_deterministic() -> None:
    board_a, config_a, _ = _coded_run("tl-det-a")
    board_b, config_b, _ = _coded_run("tl-det-b")
    timeline_a = build_timeline(board_a, config_a.run_id)
    timeline_b = build_timeline(board_b, config_b.run_id)
    # run_id differs by construction; everything else must be byte-identical.
    json_a = {**timeline_a.to_json(), "run_id": None}
    json_b = {**timeline_b.to_json(), "run_id": None}
    assert json_a == json_b
    assert build_timeline(board_a, config_a.run_id).to_json_str() == timeline_a.to_json_str()


# --------------------------------------------------------------------------- #
# 2. build_timeline across checkpoints — merge, split, reparent, rename, create
# --------------------------------------------------------------------------- #


def _checkpoint(
    board: Blackboard,
    config: RunConfig,
    codebook: Any,
    snapshot_id: str,
    components: LoopComponents,
    operations: Sequence[Operation],
    *,
    gate: Any,
    trigger: str = "manual",
) -> Any:
    agent = RefactorerAgent(FixedRefactorerClient(operations))
    return run_checkpoint(
        board=board,
        config=config,
        codebook=codebook,
        snapshot_id=snapshot_id,
        agent=agent,
        embedder=components.embedder,
        gate=gate,
        trigger=trigger,
    )


def test_build_timeline_reads_a_merge_and_a_split_from_the_slow_loop() -> None:
    board, config, components = _coded_run("tl-merge-split")
    result_codebook = board.read_snapshots(run_id=config.run_id)[-1].codebook
    codes = result_codebook.sorted_codes()
    assert len(codes) >= 3, "the run must have produced enough codes to restructure"

    merge_targets = [codes[0].id, codes[1].id]
    split_target = codes[2]
    ops = [
        Operation(type="merge", targets=merge_targets, payload={"into": merge_targets[0]}),
        Operation(
            type="split",
            targets=[split_target.id],
            payload={
                "into": [
                    {"name": "invented-half_one", "description": "First half."},
                    {"name": "invented-half_two", "description": "Second half."},
                ]
            },
        ),
    ]
    base_snapshot = board.read_snapshots(run_id=config.run_id)[-1].snapshot_id
    cp = _checkpoint(
        board, config, result_codebook, base_snapshot, components, ops, gate=accept_all(2)
    )
    assert cp.applied is True

    timeline = build_timeline(board, config.run_id)
    assert len(timeline.checkpoints) == 1
    marker = timeline.checkpoints[0]
    assert isinstance(marker, CheckpointMarker)
    assert marker.status == "applied"
    assert marker.checkpoint_id == cp.checkpoint_id

    checkpoint_diff = timeline.snapshot_diffs[-1]
    assert checkpoint_diff.reason == "checkpoint_apply"
    assert codes[2].name in checkpoint_diff.removed
    assert "invented-half_one" in checkpoint_diff.added
    assert "invented-half_two" in checkpoint_diff.added
    assert codes[1].name in checkpoint_diff.removed  # merged away

    merged_bio = timeline.biographies[codes[1].id]
    assert merged_bio.fate_kind == "merged"
    assert merged_bio.successors == [codes[0].name]

    split_bio = timeline.biographies[split_target.id]
    assert split_bio.fate_kind == "split"
    assert set(split_bio.successors) == {"invented-half_one", "invented-half_two"}

    heirs = [bio for bio in timeline.biographies.values() if bio.born.predecessor == split_target.name]
    assert {bio.name for bio in heirs} == {"invented-half_one", "invented-half_two"}
    for heir in heirs:
        assert heir.born.origin == "split"
        assert heir.born.checkpoint_id == cp.checkpoint_id
        assert heir.fate_kind == "alive"

    # The rendered markdown must name what the diff added and removed.
    text = timeline.to_markdown()
    assert "### Snapshot diffs" in text
    assert f"- added: {'invented-half_one'!r}" in text
    assert f"- removed: {codes[2].name!r}" in text


def test_build_timeline_reads_a_rename_cascade_and_a_reparent() -> None:
    board, config, components = _coded_run("tl-rename-reparent")
    snapshot = board.read_snapshots(run_id=config.run_id)[-1]
    codes = snapshot.codebook.sorted_codes()
    rename_target = codes[0]
    reparent_target = codes[1]
    new_parent = codes[2]
    # The fast loop never creates a bare family node (no coder proposes a top-level
    # candidate on its own), so every code here already has parent_id=None; reparenting
    # onto another leaf is the only way this operation is not a no-op the validator drops.
    ops = [
        Operation(type="rename", targets=[rename_target.id], payload={"name": "renamed_top_level"}),
        Operation(
            type="reparent", targets=[reparent_target.id], payload={"new_parent_id": new_parent.id}
        ),
    ]
    cp = _checkpoint(
        board, config, snapshot.codebook, snapshot.snapshot_id, components, ops, gate=accept_all(2)
    )
    assert cp.applied is True

    timeline = build_timeline(board, config.run_id)
    diff = timeline.snapshot_diffs[-1]
    renamed_pairs = {(r.from_name, r.to_name) for r in diff.renamed}
    assert (rename_target.name, "renamed_top_level") in renamed_pairs
    assert rename_target.name not in diff.added and rename_target.name not in diff.removed

    old_bio = timeline.biographies[rename_target.id]
    assert old_bio.fate_kind == "renamed"
    assert old_bio.successors == ["renamed_top_level"]

    new_id = cp.codebook.by_name("renamed_top_level").id
    new_bio = timeline.biographies[new_id]
    assert new_bio.born.origin == "renamed"
    assert new_bio.born.predecessor == rename_target.name
    assert new_bio.fate_kind == "alive"

    reparented_bio = timeline.biographies[reparent_target.id]
    assert reparented_bio.fate_kind == "alive"
    assert reparented_bio.reparenting, "a reparent must leave a readable trace"
    assert reparent_target.name in reparented_bio.reparenting[0]

    # Both the JSON shape and the markdown rendering must show the rename and the
    # re-parenting note.
    payload = timeline.to_json()
    diff_payload = payload["snapshot_diffs"][-1]
    assert {
        "from": rename_target.name,
        "to": "renamed_top_level",
        "matched_by": "recorded rename operation",
    } in diff_payload["renamed"]
    assert diff_payload["matching"] == "code id, then this run's own recorded rename operations"
    text = timeline.to_markdown()
    assert (
        f"renamed (recorded rename operation): {rename_target.name!r} -> 'renamed_top_level'"
    ) in text
    assert reparented_bio.reparenting[0] in text


def test_build_timeline_reads_a_human_created_code_and_its_later_fast_loop_evidence() -> None:
    """A code the slow loop invents can still receive fast-loop evidence later.

    `build_timeline` must attribute that later evidence to the same code id its
    `operation_applied`-sourced birth already registered, not treat it as an unknown.
    """
    board, config, components = _coded_run("tl-create-then-merge")
    snapshot = board.read_snapshots(run_id=config.run_id)[-1]
    create_op = Operation(
        type="create",
        payload={"name": "invented-brand_new", "description": "A category no coder proposed."},
    )
    cp = _checkpoint(
        board, config, snapshot.codebook, snapshot.snapshot_id, components, [create_op], gate=accept_all(1)
    )
    assert cp.applied is True
    created_id = cp.codebook.by_name("invented-brand_new").id

    timeline = build_timeline(board, config.run_id)
    bio = timeline.biographies[created_id]
    assert bio.born.origin == "created"
    assert bio.born.checkpoint_id == cp.checkpoint_id
    assert bio.fate_kind == "alive"
    assert bio.evidence_over_time, "the birth itself is a reportable evidence point"

    # A birth with no predecessor (nothing was split or renamed to make it) reads
    # differently in the markdown than a coded or an inherited one.
    text = timeline.to_markdown()
    assert f"created at checkpoint {cp.checkpoint_id}" in text


def test_build_timeline_reports_a_reject_all_checkpoint_with_no_snapshot_diff() -> None:
    """A checkpoint under the default gate is a no-op; the timeline must say so too."""
    board, config, components = _coded_run("tl-reject-all")
    n_snapshots_before = len(board.read_snapshots(run_id=config.run_id))
    snapshot = board.read_snapshots(run_id=config.run_id)[-1]
    codes = snapshot.codebook.sorted_codes()
    ops = [Operation(type="rename", targets=[codes[0].id], payload={"name": "would_not_apply"})]
    cp = _checkpoint(
        board, config, snapshot.codebook, snapshot.snapshot_id, components, ops, gate=RejectAllGate()
    )
    assert cp.applied is False
    assert cp.snapshot_id is None

    timeline = build_timeline(board, config.run_id)
    assert len(timeline.checkpoints) == 1
    assert timeline.checkpoints[0].status == "rejected"
    assert len(board.read_snapshots(run_id=config.run_id)) == n_snapshots_before
    assert len(timeline.snapshot_diffs) == n_snapshots_before - 1


# --------------------------------------------------------------------------- #
# 3. The optional checkpoint_evaluated event — handover
# --------------------------------------------------------------------------- #


def test_batch_handover_is_populated_from_a_real_run() -> None:
    """`gaf.pipeline.decision_matrix.evaluate_handover` writes a real
    ``checkpoint_evaluated`` event at each batch *boundary* — not necessarily for the
    right after that batch's own responses are coded (`_evaluate_batch` in
    `gaf.pipeline.fast_loop`), so on the synthetic corpus's two batches (batch_size=10
    over 14 responses) both must carry one, each under its own batch number."""
    board, config, _ = _coded_run("tl-handover-real")
    timeline = build_timeline(board, config.run_id)
    assert len(timeline.batches) == 2, "batch_size=10 over 14 responses is two batches"
    assert [batch.batch for batch in timeline.batches] == [1, 2]
    for batch in timeline.batches:
        assert batch.handover is not None
        assert batch.handover.batch == batch.batch, (
            "the fast loop's own 1-based batch number must join onto this module's "
            "own batch of the same number, not by list position"
        )
        assert batch.handover.verdict in ("continue", "checkpoint_due")
        assert batch.handover.reason


def test_batch_handover_reads_the_fallback_fired_rules_key() -> None:
    """A ``checkpoint_evaluated`` event under a different key for its fired rules
    (``fired_rules`` rather than the decision matrix's own ``fired``) is read just as
    well — this module treats the event's *shape* as advisory, not fixed."""
    board, config, _ = _coded_run("tl-handover-fallback")
    log = board.audit(config.run_id)
    log.emit(
        "checkpoint_evaluated",
        scope="run",
        subject=config.run_id,
        batch=1,
        verdict="continue",
        reason="no rule fired",
        fired_rules=[],
    )
    log.emit(
        "checkpoint_evaluated",
        scope="run",
        subject=config.run_id,
        batch=2,
        verdict="checkpoint_due",
        reason="new codes per batch exceeded the policy",
        fired_rules=["max_new_codes_per_batch"],
    )
    timeline = build_timeline(board, config.run_id)
    assert timeline.batches[0].handover is not None
    assert timeline.batches[0].handover.verdict == "continue"
    assert timeline.batches[1].handover is not None
    assert timeline.batches[1].handover.verdict == "checkpoint_due"
    assert timeline.batches[1].handover.fired_rules == ["max_new_codes_per_batch"]


def test_batch_handover_is_none_when_the_event_is_absent() -> None:
    """An audit log predating `checkpoint_evaluated` (or any other producer that
    simply never emits it) must not be treated as an error: the event is optional
    input, used when present and never required."""
    config = _config("tl-no-handover")
    board = Blackboard(":memory:")
    board.register_run(config)
    snapshot = board.freeze_codebook(Codebook(), run_id=config.run_id, reason="seed")
    log = board.audit(config.run_id)
    log.emit(
        "response_prepared",
        scope="response",
        subject="1",
        snapshot_id=snapshot.snapshot_id,
        dedup={"content_hash": "x", "duplicate_of": None},
    )
    timeline = build_timeline(board, config.run_id)
    assert all(batch.handover is None for batch in timeline.batches)


# --------------------------------------------------------------------------- #
# 4. Duplicate responses — a step still names the original
# --------------------------------------------------------------------------- #


def test_step_carries_duplicate_of_from_a_hand_written_response_prepared_event() -> None:
    """The synthetic corpus plants no duplicate content, so this is exercised directly
    against the audit log rather than waiting for one to occur in a real run."""
    config = _config("tl-dedup")
    board = Blackboard(":memory:")
    board.register_run(config)
    snapshot = board.freeze_codebook(Codebook(), run_id=config.run_id, reason="seed")
    log = board.audit(config.run_id)
    log.emit(
        "response_prepared",
        scope="response",
        subject="101",
        snapshot_id=snapshot.snapshot_id,
        dedup={"content_hash": "abc123", "duplicate_of": None},
    )
    log.emit(
        "response_prepared",
        scope="response",
        subject="102",
        snapshot_id=snapshot.snapshot_id,
        dedup={"content_hash": "abc123", "duplicate_of": 101},
    )
    timeline = build_timeline(board, config.run_id)
    by_id = {step.response_id: step for step in timeline.steps}
    assert by_id[101].duplicate_of is None
    assert by_id[102].duplicate_of == 101


def test_judge_consultations_are_counted_against_the_batch_being_coded() -> None:
    """The synthetic corpus's offline run escalates no pair to the judge (ADR-0019: the
    lexical fallback's grey zone is empty), so this is exercised directly against a
    hand-written `judge_consulted` event rather than waiting for a live escalation.

    A `judge_consulted` event names a candidate or a pair, never a response, so it is
    attributed to the response being coded when it fired: the last `response_prepared`
    before it in the log's own order. Appending one to a finished run therefore lands
    it in the last batch. Keying on the event's snapshot id instead credited every
    judge call of a `per_checkpoint` run to whichever batch held the seed snapshot.
    """
    board, config, _ = _coded_run("tl-judge-direct")
    timeline = build_timeline(board, config.run_id)
    assert sum(b.judge_consultations for b in timeline.batches) == 0

    log = board.audit(config.run_id)
    log.emit(
        "judge_consulted",
        scope="pair",
        subject="invented-a<->invented-b",
        snapshot_id=timeline.batches[-1].snapshot_id,
        check_id="M1",
        score=0.5,
        band="grey",
        verdict="MERGE",
        reasoning="a hand-written escalation for this test",
    )

    reread = build_timeline(board, config.run_id)
    assert [b.judge_consultations for b in reread.batches] == [0, 1]
    assert sum(b.judge_consultations for b in reread.batches) == board.audit(
        config.run_id
    ).count("judge_consulted")


def test_name_resolution_falls_back_to_the_base_snapshot_for_a_warm_started_codebook() -> None:
    """A checkpoint may run against a codebook this run never itself coded — carried
    over from an earlier run or another slow-loop pass (`run_fast_loop`'s own docstring:
    "the codebook a previous run ... left behind"). `build_timeline` must still resolve
    such a code's name from the base snapshot rather than from an in-run record that
    was never written for it.
    """
    config = _config("tl-warm-start")
    board = Blackboard(":memory:")
    board.register_run(config)
    seed = toy_codebook()
    response_ids = {evidence.response_id for code in seed.sorted_codes() for evidence in code.evidence}
    board.write_responses(
        Response(id=response_id, question="", content="", source="") for response_id in response_ids
    )
    snapshot = board.freeze_codebook(seed, run_id=config.run_id, reason="seed")
    target = seed.sorted_codes()[0]

    agent = RefactorerAgent(FixedRefactorerClient([
        Operation(type="rename", targets=[target.id], payload={"name": "warm_started_rename"})
    ]))
    cp = run_checkpoint(
        board=board,
        config=config,
        codebook=seed,
        snapshot_id=snapshot.snapshot_id,
        agent=agent,
        embedder=StubEmbedder(),
        gate=accept_all(1),
    )
    assert cp.applied is True

    timeline = build_timeline(board, config.run_id)
    old_bio = timeline.biographies[target.id]
    assert old_bio.name == target.name
    assert old_bio.born.origin == "pre_existing", (
        "the code was never born within this run's own audit log; it was carried over"
    )
    assert old_bio.born.snapshot_id == snapshot.snapshot_id
    assert old_bio.fate_kind == "renamed"
    assert old_bio.successors == ["warm_started_rename"]
    new_bio = timeline.biographies[cp.codebook.by_name("warm_started_rename").id]
    assert new_bio.born.predecessor == target.name


# --------------------------------------------------------------------------- #
# 5. timeline_from_assignments
# --------------------------------------------------------------------------- #


def test_timeline_from_assignments_reads_first_appearance_as_birth() -> None:
    rows = [
        Assignment(response_id=10, segment="a segment", code="invented-alpha"),
        Assignment(response_id=10, segment="another segment", code="invented-beta"),
        Assignment(response_id=11, segment="a third segment", code="invented-alpha"),
        Assignment(response_id=12, segment="a fourth segment", code="invented-gamma"),
    ]
    timeline = timeline_from_assignments(rows, batch_size=2)

    assert timeline.run_id is None
    assert timeline.snapshot_diffs == []
    assert timeline.biographies == {}
    assert timeline.checkpoints == []

    by_id = {step.response_id: step for step in timeline.steps}
    assert by_id[10].codes_created == ["invented-alpha", "invented-beta"]
    assert by_id[10].codes_merged == []
    assert by_id[10].snapshot_id is None
    assert by_id[11].codes_created == []
    assert by_id[11].codes_merged == ["invented-alpha"]
    assert by_id[12].codes_created == ["invented-gamma"]

    assert [batch.batch for batch in timeline.batches] == [1, 2]
    assert timeline.batches[0].responses == [10, 11]
    assert timeline.batches[0].new_codes == ["invented-alpha", "invented-beta"]
    assert timeline.batches[0].merges == 1
    assert timeline.batches[0].cumulative_codes == 2
    assert timeline.batches[1].responses == [12]
    assert timeline.batches[1].cumulative_codes == 3


def test_timeline_from_assignments_preserves_first_seen_response_order_not_numeric_order() -> None:
    rows = [
        Assignment(response_id=5, segment="s1", code="invented-a"),
        Assignment(response_id=3, segment="s2", code="invented-b"),
    ]
    timeline = timeline_from_assignments(rows, batch_size=10)
    assert [step.response_id for step in timeline.steps] == [5, 3]
    assert timeline.batches[0].responses == [5, 3]


def test_timeline_from_assignments_rejects_a_non_positive_batch_size() -> None:
    with pytest.raises(ValueError, match="batch_size"):
        timeline_from_assignments([], batch_size=0)


def test_timeline_from_assignments_on_an_empty_list_is_an_empty_timeline() -> None:
    timeline = timeline_from_assignments([], batch_size=5)
    assert timeline.steps == []
    assert timeline.batches == []
    assert timeline.to_json()["steps"] == []


# --------------------------------------------------------------------------- #
# 6. to_json / to_json_str / to_markdown shape
# --------------------------------------------------------------------------- #


def test_timeline_to_json_round_trips_and_is_json_serialisable() -> None:
    board, config, _ = _coded_run("tl-json")
    timeline = build_timeline(board, config.run_id)
    payload = timeline.to_json()
    assert json.loads(timeline.to_json_str()) == payload
    assert set(payload) == {
        "run_id",
        "steps",
        "batches",
        "snapshot_diffs",
        "biographies",
        "checkpoints",
    }
    assert isinstance(payload["biographies"], dict)


def test_timeline_to_markdown_names_batches_and_biographies() -> None:
    board, config, _ = _coded_run("tl-markdown")
    timeline = build_timeline(board, config.run_id)
    text = timeline.to_markdown()
    assert "## Timeline of code generation and change" in text
    assert "### Batches" in text
    assert "### Code biographies" in text
    assert config.run_id in text


def test_timeline_to_markdown_of_an_assignments_timeline_says_no_snapshots() -> None:
    timeline = timeline_from_assignments(
        [Assignment(response_id=1, segment="s", code="invented-x")], batch_size=1
    )
    text = timeline.to_markdown()
    assert "no snapshots, no fates" in text
    assert "### Code biographies" not in text  # empty biographies section is omitted


# --------------------------------------------------------------------------- #
# 7. timeline_svg
# --------------------------------------------------------------------------- #


def test_timeline_svg_of_an_empty_timeline_says_so() -> None:
    empty = Timeline(run_id=None, steps=[], batches=[])
    svg = timeline_svg(empty)
    assert svg.startswith("<svg")
    assert "No batches" in svg


def test_timeline_svg_is_deterministic_and_contains_markers() -> None:
    board, config, _ = _coded_run("tl-svg")
    timeline = build_timeline(board, config.run_id)
    first = timeline_svg(timeline, markers=[(1, "a caller marker")])
    second = timeline_svg(timeline, markers=[(1, "a caller marker")])
    assert first == second
    assert first.startswith("<svg")
    assert "a caller marker" in first
    assert 'class="bar"' in first
    assert 'class="curve"' in first


def test_timeline_svg_draws_a_checkpoint_marker() -> None:
    board, config, components = _coded_run("tl-svg-checkpoint")
    snapshot = board.read_snapshots(run_id=config.run_id)[-1]
    cp = _checkpoint(
        board,
        config,
        snapshot.codebook,
        snapshot.snapshot_id,
        components,
        [Operation(type="noop")],
        gate=accept_all(1),
    )
    timeline = build_timeline(board, config.run_id)
    svg = timeline_svg(timeline)
    assert cp.checkpoint_id in svg
    assert 'class="ckptmark"' in svg


def test_timeline_svg_ignores_an_out_of_range_caller_marker() -> None:
    board, config, _ = _coded_run("tl-svg-oob-marker")
    timeline = build_timeline(board, config.run_id)
    # Must not raise, and must not draw a marker for a batch that does not exist.
    svg = timeline_svg(timeline, markers=[(999, "nowhere")])
    assert "nowhere" not in svg


# --------------------------------------------------------------------------- #
# R1 audit findings
# --------------------------------------------------------------------------- #


def _coded_run_with(run_id: str, **overrides: Any) -> tuple[Blackboard, RunConfig, LoopComponents]:
    config = RunConfig(run_id=run_id, offline=True, cache_dir=None, **overrides)
    board = Blackboard(":memory:")
    components = offline_components(config)
    run_fast_loop(synthetic_corpus(), config=config, board=board, components=components)
    return board, config, components


def test_a_split_whose_heir_keeps_the_name_keeps_its_own_biography() -> None:
    """R1 C6. A code id is the hash of its name, so the heir's id is the target's."""
    board, config, components = _coded_run("tl-same-name-split")
    snapshots = board.read_snapshots(run_id=config.run_id)
    codebook = snapshots[-1].codebook
    target = codebook.sorted_codes()[0]

    before = build_timeline(board, config.run_id).biographies[target.id]
    assert before.born.origin == "coded" and before.born.response_id is not None

    result = _checkpoint(
        board,
        config,
        codebook,
        snapshots[-1].snapshot_id,
        components,
        [
            Operation(
                type="split",
                targets=[target.id],
                payload={"into": [{"name": target.name}, {"name": "invented-narrower"}]},
            )
        ],
        gate=accept_all(1),
    )
    assert result.applied is True

    timeline = build_timeline(board, config.run_id)
    bio = timeline.biographies[target.id]
    assert bio.born == before.born, "its real birth is a fact about the run, not a casualty"
    assert bio.fate_kind == "narrowed"
    assert bio.fate == "narrowed; 'invented-narrower' split off"
    assert bio.successors == ["invented-narrower"]
    assert target.name not in bio.successors, "a code is never its own successor"

    narrower = next(b for b in timeline.biographies.values() if b.name == "invented-narrower")
    assert narrower.born.origin == "split"
    assert narrower.born.predecessor == target.name


def test_a_per_checkpoint_run_keeps_one_batch_per_handover_evaluation() -> None:
    """R1, brief Important. One snapshot for the whole run is not one batch."""
    board, config, _ = _coded_run_with(
        "tl-per-checkpoint", snapshot_policy="per_checkpoint", batch_size=5
    )
    events = board.audit(config.run_id).events()
    evaluated = [e for e in events if e.event == "checkpoint_evaluated"]
    assert [int(e.payload["batch"]) for e in evaluated] == [1, 2, 3]
    assert len({e.snapshot_id for e in events if e.event == "response_prepared"}) == 1, (
        "the fixture must really share one snapshot, or this test proves nothing"
    )

    timeline = build_timeline(board, config.run_id)
    assert [b.batch for b in timeline.batches] == [1, 2, 3]
    assert [b.n_responses for b in timeline.batches] == [5, 5, 4]
    assert [b.handover.batch for b in timeline.batches if b.handover] == [1, 2, 3]
    assert sum(b.n_responses for b in timeline.batches) == len(timeline.steps)
    assert [s.batch for s in timeline.steps[:5]] == [1] * 5
    assert [s.batch for s in timeline.steps[5:10]] == [2] * 5


def test_a_per_batch_run_still_batches_the_same_way() -> None:
    """The snapshot route and the evaluation route must agree where both are available."""
    board, config, _ = _coded_run_with("tl-per-batch", batch_size=5)
    timeline = build_timeline(board, config.run_id)
    assert [b.batch for b in timeline.batches] == [1, 2, 3]
    assert [b.n_responses for b in timeline.batches] == [5, 5, 4]
    snap_of_step = {s.response_id: s.snapshot_id for s in timeline.steps}
    for batch in timeline.batches:
        assert {snap_of_step[r] for r in batch.responses} == {batch.snapshot_id}


def test_snapshots_are_resolved_from_this_runs_own_freeze_events() -> None:
    """R1, brief Important. Snapshots are content-addressed and keep the first run_id."""
    board = Blackboard(":memory:")
    first = RunConfig(run_id="tl-shared-first", offline=True, cache_dir=None)
    run_fast_loop(synthetic_corpus(), config=first, board=board, components=offline_components(first))
    second = RunConfig(run_id="tl-shared-second", offline=True, cache_dir=None)
    run_fast_loop(
        synthetic_corpus(), config=second, board=board, components=offline_components(second)
    )

    assert board.read_snapshots(run_id=second.run_id) == [], (
        "the fixture must really lose the second run's snapshots, or this proves nothing"
    )
    timeline = build_timeline(board, second.run_id)
    assert timeline.snapshot_diffs, "the section must not vanish without a word"
    first_timeline = build_timeline(board, first.run_id)
    assert [(d.from_snapshot, d.to_snapshot) for d in timeline.snapshot_diffs] == [
        (d.from_snapshot, d.to_snapshot) for d in first_timeline.snapshot_diffs
    ]


def test_timeline_from_assignments_takes_the_order_the_run_actually_coded_in() -> None:
    """R1, brief Important (the same root cause as C2): a coded response with no row."""
    rows = [
        Assignment(response_id=1, segment="s", code="a-one"),
        Assignment(response_id=3, segment="s", code="a-two"),
        Assignment(response_id=4, segment="s", code="a-one"),
    ]
    # Response 2 was coded and produced nothing; it still took a place in batch 1.
    with_order = timeline_from_assignments(rows, batch_size=2, response_order=[1, 2, 3, 4])
    assert [b.n_responses for b in with_order.batches] == [2, 2]
    assert [b.responses for b in with_order.batches] == [[1, 2], [3, 4]]
    assert [b.n_new_codes for b in with_order.batches] == [1, 1]
    assert with_order.batches[1].cumulative_codes == 2
    empty = next(s for s in with_order.steps if s.response_id == 2)
    assert empty.n_assignments == 0 and empty.codes_created == []

    without = timeline_from_assignments(rows, batch_size=2)
    assert [b.responses for b in without.batches] == [[1, 3], [4]], (
        "without the order, response 3 moves into batch 1 and every later slot shifts"
    )


def test_a_response_order_that_omits_a_coded_response_is_refused() -> None:
    rows = [Assignment(response_id=1, segment="s", code="a-one")]
    with pytest.raises(ValueError, match="response_order"):
        timeline_from_assignments(rows, batch_size=2, response_order=[2, 3])


def test_the_handover_line_does_not_terminate_the_batch_table() -> None:
    """R1 Minor. A blockquote inside a table body ends the table in CommonMark."""
    board, config, _ = _coded_run_with("tl-md-table", batch_size=5)
    markdown = build_timeline(board, config.run_id).to_markdown()
    lines = markdown.splitlines()
    table_start = lines.index("| batch | responses | new codes | merges | cumulative codes | judge calls |")
    rows = []
    for line in lines[table_start:]:
        if not line.startswith("|"):
            break
        rows.append(line)
    assert len(rows) == 5, "header, separator and one row per batch, unbroken"
    assert "> batch 1 handover" not in "\n".join(rows)
    assert "batch 1 handover" in markdown, "the handover is still reported, below the table"


def test_the_svg_gridline_labels_are_the_values_they_sit_on() -> None:
    """R1 Minor. `_num(value, 0)` on a y_max of 14 reads 0, 4, 7, 10, 14."""
    timeline = timeline_from_assignments(
        [Assignment(response_id=i, segment="s", code=f"a-{i}") for i in range(1, 15)],
        batch_size=14,
    )
    assert timeline.batches[0].cumulative_codes == 14
    svg = timeline_svg(timeline)
    for label in ("3.5", "10.5"):
        assert f">{label}</text>" in svg
    assert ">7</text>" in svg and ">14</text>" in svg
    assert ">4</text>" not in svg


def test_a_checkpoint_label_at_the_end_of_the_run_stays_inside_the_viewport() -> None:
    """R1 Minor. Drawn at x+2 with no clamp, an end-of-run label is cut off."""
    timeline = timeline_from_assignments(
        [Assignment(response_id=i, segment="s", code="a-one") for i in range(1, 5)],
        batch_size=2,
    )
    late = CheckpointMarker(at_response_count=4, checkpoint_id="ckpt-zzzz", status="applied")
    svg = timeline_svg(replace(timeline, checkpoints=[late]), width=860, height=360)
    label = next(line for line in svg.splitlines() if "ckpt-zzzz" in line)
    assert 'text-anchor="end"' in label, "a label at the right edge is anchored to its right"
    assert 'x="834.00"' in label, "two pixels to the left of the marker, not past it"
    assert float(label.split('x="')[1].split('"')[0]) < 860


def test_two_checkpoints_at_the_same_response_count_do_not_overlap() -> None:
    timeline = timeline_from_assignments(
        [Assignment(response_id=i, segment="s", code="a-one") for i in range(1, 5)],
        batch_size=2,
    )
    svg = timeline_svg(
        replace(
            timeline,
            checkpoints=[
                CheckpointMarker(at_response_count=2, checkpoint_id="ckpt-aaaa", status="rejected"),
                CheckpointMarker(at_response_count=2, checkpoint_id="ckpt-bbbb", status="applied"),
            ],
        )
    )
    ys = [
        line.split('y="')[1].split('"')[0]
        for line in svg.splitlines()
        if "ckpt-aaaa" in line or "ckpt-bbbb" in line
    ]
    assert len(ys) == 2 and ys[0] != ys[1], "two labels at one x sit on different rows"


def test_a_snapshot_diff_says_how_its_codes_were_matched() -> None:
    """R1 Minor. A reader cannot tell a recorded rename from an inferred one."""
    board, config, components = _coded_run("tl-diff-matching")
    snapshots = board.read_snapshots(run_id=config.run_id)
    codebook = snapshots[-1].codebook
    target = codebook.sorted_codes()[0]
    other = codebook.sorted_codes()[1]
    _checkpoint(
        board,
        config,
        codebook,
        snapshots[-1].snapshot_id,
        components,
        [
            Operation(type="rename", targets=[target.id], payload={"name": "renamed_here"}),
            Operation(type="reparent", targets=[other.id], payload={"new_parent_id": None}),
        ],
        gate=accept_all(2),
    )
    timeline = build_timeline(board, config.run_id)
    diff = next(d for d in timeline.snapshot_diffs if d.renamed)
    assert diff.matching == "code id, then this run's own recorded rename operations"
    assert diff.renamed[0].matched_by == "recorded rename operation"
    payload = diff.to_json()
    assert payload["matching"] == diff.matching
    assert payload["renamed"][0]["matched_by"] == "recorded rename operation"

    markdown = timeline.to_markdown()
    assert "matched by code id" in markdown
    assert "re-parenting keeps a code's id" in markdown
