"""Wave 3 gate for the slow loop (C1): triggers, validation, the human gate, the apply.

Twelve claims, and the first one is the one the whole work package exists for:

1. **THE NO-OP PROOF.** A full checkpoint under `RejectAllGate` — the default whenever
   no human is present — applies nothing: the codebook is byte-identical afterwards, no
   new snapshot is written, and the checkpoint is recorded as proposed-and-rejected.
   This is acceptance criterion 10. A non-interactive run must be a no-op, never an
   auto-accept, because a machine that disposes of its own proposals when nobody is
   watching is the failure mode the gate exists to prevent (ADR-0004).
2. **An accepted script applies**, produces a new snapshot whose parent is the base
   snapshot, and writes a changelog naming both ids.
3. **An edited operation applies the human's replacement**, not the model's original.
4. **Validation drops what cannot be applied** — a nonexistent target, a duplicate name,
   a hierarchy-depth violation — each with a finding, and the valid operations beside
   them still apply. One hallucinated row must not cost five good ones.
5. **A proposal that would leave the codebook failing S6 is rejected at validation**,
   before any human sees it.
6. **Evidence is never lost.** The multiset of ``(response_id, quote)`` pairs is equal
   before and after a merge and after a split, and the guard that asserts it is real.
7. **`split` and `reparent` work end to end.** They are the anti-flattening operations
   and must not be the untested ones.
8. **Triggers are auditable**: event-driven fires on health, the hard floor fires at 50
   responses regardless, and the fixed cadence fires on schedule.
9. **Determinism.** The same accepted script applied twice yields the same snapshot id.
10. **The gate's defaults are safe**: silence, an unrecognised verdict and an ``edit``
    with no replacement all reject.
11. **`ConsoleGate` reads a person**, and a closed pipe rejects rather than blocking.
12. **The whole thing runs offline** with `MockRefactorerClient`.

No key, no network, no provider SDK, no real data: every client is a deterministic mock
and the corpus is `tests.fixtures.corpus`.
"""

from __future__ import annotations

import io
import json
from collections.abc import Sequence
from dataclasses import replace
from typing import Any

import numpy as np
import pytest

from gaf.agents.refactorer import RefactorContext, RefactorerAgent
from gaf.checks.contracts import CheckReport, Severity
from gaf.checks.structural import MARKER_KEY
from gaf.config import CheckpointPolicy, RunConfig
from gaf.ids import code_id as mint_code_id
from gaf.llm.base import LLMRequest, LLMResult, TaskType
from gaf.llm.mock import MockRefactorerClient
from gaf.models import Code, Codebook, Evidence, Operation
from gaf.pipeline.slow_loop import (
    ACCEPT,
    CHECK_ID,
    EDIT,
    REJECT,
    ConsoleGate,
    EvidenceLossError,
    Gate,
    GateDecision,
    RefactorProposal,
    RejectAllGate,
    ScriptedGate,
    _check_evidence_conserved,
    _decision_index,
    apply_operations,
    build_diff,
    evidence_pairs,
    render_diff,
    run_checkpoint,
    should_checkpoint,
    validate_script,
)
from gaf.store.blackboard import Blackboard
from gaf.store.snapshot import freeze
from tests.fixtures.codebooks import toy_codebook
from tests.fixtures.corpus import synthetic_corpus
from tests.fixtures.embedding import StubEmbedder

# --------------------------------------------------------------------------- #
# Ids of the toy codebook, spelled out so a failing assertion names something
# a person can find rather than a hash.
# --------------------------------------------------------------------------- #

POSITIVE = "c-positive_impacts"
HEALTHCARE = "c-positive_impacts-healthcare"
PROBLEM_SOLVING = "c-positive_impacts-problem-solving"
NEGATIVE = "c-negative_impacts"
JOB_DESTRUCTION = "c-negative_impacts-job_destruction"
MISUSE = "c-negative_impacts-misuse"
FUTURE = "c-future"
INEVITABILITY = "c-future-inevitability"

MISSING_TARGET = "c-this_code_does_not_exist"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def config_for(run_id: str, **changes: Any) -> RunConfig:
    """An offline run config with the disk cache off, so tests share no state."""
    settings: dict[str, Any] = {"offline": True, "cache_dir": None}
    settings.update(changes)
    return RunConfig(run_id=run_id, **settings)


def seeded_board(
    codebook: Codebook | None = None, run_id: str = "slow"
) -> tuple[Blackboard, RunConfig, Codebook, str]:
    """A store with the run registered, the corpus written and the base snapshot frozen.

    The corpus matters: S6 checks evidence against the corpus ids, so a store without
    responses would make every code's evidence look like a dangling reference.
    """
    book = codebook if codebook is not None else toy_codebook()
    config = config_for(run_id)
    board = Blackboard()
    board.register_run(config)
    board.write_responses(synthetic_corpus())
    snapshot = board.freeze_codebook(book, run_id=run_id, reason="seed")
    return board, config, book, snapshot.snapshot_id


class FixedRefactorerClient(MockRefactorerClient):
    """A refactorer that always proposes one fixed edit script.

    Subclasses the offline mock so that the accounting row, the token estimate and the
    task dispatch are the mock's own; only the operations are the test's.
    """

    def __init__(self, operations: Sequence[Operation], reasoning: str = "a fixed test script"):
        super().__init__()
        self._operations = [op.to_json() for op in operations]
        self._reasoning = reasoning

    def complete_json(self, request: LLMRequest) -> LLMResult:
        if request.task is not TaskType.REFACTOR:
            return self._wrong_task(request)
        return self._result(
            request, {"operations": list(self._operations), "reasoning": self._reasoning}
        )


def agent_proposing(operations: Sequence[Operation]) -> RefactorerAgent:
    return RefactorerAgent(FixedRefactorerClient(operations))


def mock_agent() -> RefactorerAgent:
    return RefactorerAgent(MockRefactorerClient())


def accept_all(n: int) -> Gate:
    """A gate that accepts every operation. A stand-in for a person who said yes."""
    return ScriptedGate([GateDecision(index=i, verdict=ACCEPT) for i in range(n)])


class FlatEmbedder:
    """Every text is the same vector, so every comparable pair scores 1.0.

    The one geometry that reliably trips M4's near-duplicate count, which is what the
    event-driven checkpoint trigger reads.
    """

    space_id = "flat-v1-8"
    dim = 8

    def embed_one(self, text: str) -> np.ndarray:
        return np.ones(self.dim, dtype=np.float64) / np.sqrt(self.dim)

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float64)
        return np.vstack([self.embed_one(t) for t in texts])


def crowded_family_codebook() -> Codebook:
    """Four leaves in one family: six comparable pairs, which is above the policy's 3."""
    codes = [
        Code(id="c-risk", name="risk", description="Risks respondents name."),
        *[
            Code(
                id=f"c-risk-{slug}",
                name=f"risk-{slug}",
                description=description,
                parent_id="c-risk",
                created_in_snapshot="snap-seed",
                evidence=[Evidence(response_id=207, quote=quote, verified=True, score=1.0)],
            )
            for slug, description, quote in (
                ("job_loss", "Paid work disappears.", "Firms will hand ticket triage"),
                ("job_destruction", "Paid work disappears.", "first-draft paperwork to software"),
                ("employment", "Paid work disappears.", "those were the posts a graduate used to start in"),
                ("work", "Paid work disappears.", "Maintaining the systems becomes the new entry point"),
            )
        ],
    ]
    return Codebook(codes={c.id: c for c in codes})


def rename_future_to_horizon() -> Operation:
    return Operation(
        type="rename",
        targets=[FUTURE],
        payload={"name": "horizon"},
        rationale="'future' names the survey's whole subject rather than a category in it.",
    )


def merge_negative_leaves() -> Operation:
    return Operation(
        type="merge",
        targets=[JOB_DESTRUCTION, MISUSE],
        payload={"into": JOB_DESTRUCTION},
        rationale="both leaves describe harms done to people by whoever deploys the system.",
    )


def split_job_destruction() -> Operation:
    return Operation(
        type="split",
        targets=[JOB_DESTRUCTION],
        payload={
            "into": [
                {
                    "name": "negative_impacts-clerical_work",
                    "description": "Office and data-entry roles disappear.",
                    "response_ids": [207],
                },
                {
                    "name": "negative_impacts-manufacturing",
                    "description": "Production-line roles disappear.",
                    "response_ids": [239],
                },
            ]
        },
        rationale="the two quotes describe different kinds of work being displaced.",
    )


def promote_healthcare() -> Operation:
    """A second operation whose target no other operation in these tests touches.

    Deliberately independent: because validation projects operations *in order*, an
    operation whose target a preceding rename re-minted the id of is correctly dropped
    as an unknown target, which is a different property from the one under test here.
    """
    return Operation(
        type="reparent",
        targets=[HEALTHCARE],
        payload={"new_parent_id": None},
        rationale="healthcare is a family in its own right, not a kind of positive impact.",
    )


def reparent_inevitability() -> Operation:
    return Operation(
        type="reparent",
        targets=[INEVITABILITY],
        payload={"new_parent_id": NEGATIVE},
        rationale="the code reads as a harm rather than a characterisation of the future.",
    )


# --------------------------------------------------------------------------- #
# 1. THE NO-OP PROOF — acceptance criterion 10
# --------------------------------------------------------------------------- #


def test_reject_all_gate_is_the_default_and_a_checkpoint_applies_nothing() -> None:
    """A checkpoint with no human present changes NOTHING. The whole point.

    Every clause here is load-bearing:

    * the codebook that comes out is byte-identical to the one that went in;
    * it is the *same object*, so there is no copy that could have drifted;
    * no snapshot was written — the store holds exactly the snapshot it started with;
    * the checkpoint is recorded as proposed and then rejected, with a decision row per
      operation, so a reviewer can see that a proposal was made and refused rather than
      never made at all.

    `gate` is not passed. That is the test: the default is refusal.
    """
    board, config, codebook, base = seeded_board()
    before_json = codebook.to_json_str()
    before_snapshots = [s.snapshot_id for s in board.read_snapshots()]

    result = run_checkpoint(
        board=board,
        config=config,
        codebook=codebook,
        snapshot_id=base,
        agent=mock_agent(),
        embedder=StubEmbedder(),
    )

    # Something was genuinely proposed — this is not a vacuous no-op.
    assert result.proposal.script.operations, "the mock proposed nothing; the test proves nothing"

    assert result.applied is False
    assert result.snapshot_id is None
    assert result.status == "rejected"
    assert result.codebook.to_json_str() == before_json
    assert result.codebook is codebook
    assert freeze(result.codebook).snapshot_id == base

    assert [s.snapshot_id for s in board.read_snapshots()] == before_snapshots

    assert result.decisions
    assert {d.verdict for d in result.decisions} == {REJECT}
    assert len(result.decisions) == len(result.proposal.script.operations)

    record = board.read_checkpoint(result.checkpoint_id)
    assert record is not None
    assert record.status == "rejected"
    assert record.result_snapshot_id is None
    assert record.base_snapshot_id == base
    assert len(record.decisions) == len(result.decisions)
    assert record.operations() == result.proposal.script.operations

    assert result.changelog.result_snapshot_id is None
    assert result.changelog.applied == []
    assert result.changelog.codes_before == result.changelog.codes_after


def test_every_gate_satisfies_the_gate_protocol() -> None:
    """C2's CLI is typed against `Gate`; the three gates shipped here must satisfy it."""
    assert isinstance(RejectAllGate(), Gate)
    assert isinstance(ScriptedGate([]), Gate)
    assert isinstance(ConsoleGate(stream_in=io.StringIO(), stream_out=io.StringIO()), Gate)


def test_explicit_reject_all_gate_matches_the_default() -> None:
    """Passing `RejectAllGate()` and passing nothing are the same run."""
    board, config, codebook, base = seeded_board(run_id="explicit")
    result = run_checkpoint(
        board=board,
        config=config,
        codebook=codebook,
        snapshot_id=base,
        agent=mock_agent(),
        embedder=StubEmbedder(),
        gate=RejectAllGate(),
    )
    assert result.applied is False
    assert result.snapshot_id is None
    assert result.codebook.to_json_str() == codebook.to_json_str()
    assert all("no human at the gate" in d.note for d in result.decisions)


def test_rejecting_a_noop_only_script_is_recorded_as_noop() -> None:
    """A script with nothing structural in it is a no-op checkpoint, not a rejection."""
    board, config, codebook, base = seeded_board(run_id="quiet")
    result = run_checkpoint(
        board=board,
        config=config,
        codebook=codebook,
        snapshot_id=base,
        agent=agent_proposing([Operation(type="noop", rationale="the codebook is healthy")]),
        embedder=StubEmbedder(),
        gate=accept_all(1),
    )
    assert result.status == "noop"
    assert result.applied is False
    assert result.snapshot_id is None
    assert result.proposal.is_noop()


# --------------------------------------------------------------------------- #
# 2. An accepted script applies, snapshots and writes a changelog
# --------------------------------------------------------------------------- #


def test_accepted_script_applies_and_produces_a_child_snapshot_and_a_changelog() -> None:
    board, config, codebook, base = seeded_board(run_id="accepted")
    result = run_checkpoint(
        board=board,
        config=config,
        codebook=codebook,
        snapshot_id=base,
        agent=agent_proposing([rename_future_to_horizon()]),
        embedder=StubEmbedder(),
        gate=accept_all(1),
    )

    assert result.applied is True
    assert result.status == "applied"
    assert result.snapshot_id is not None
    assert result.snapshot_id != base

    stored = board.read_snapshot(result.snapshot_id)
    assert stored.parent_id == base
    assert stored.reason == "checkpoint_apply"
    assert stored.codebook_json == result.codebook.to_json_str()

    names = result.codebook.names()
    assert "horizon" in names
    assert "horizon-inevitability" in names, "a family rename must cascade to its sub-codes"
    assert "future" not in names
    assert "future-inevitability" not in names

    # The renamed sub-code still points at the renamed family.
    horizon = result.codebook.by_name("horizon")
    child = result.codebook.by_name("horizon-inevitability")
    assert horizon is not None and child is not None
    assert child.parent_id == horizon.id
    assert horizon.id == mint_code_id("horizon")

    changelog = result.changelog
    assert changelog.base_snapshot_id == base
    assert changelog.result_snapshot_id == result.snapshot_id
    assert changelog.verdicts[ACCEPT] == 1
    assert len(changelog.applied) == 1
    assert changelog.applied[0].effect is not None
    assert changelog.applied[0].effect.renamed  # the old id -> new id mapping is recorded
    assert base in changelog.render()
    assert result.snapshot_id in changelog.render()

    record = board.read_checkpoint(result.checkpoint_id)
    assert record is not None
    assert record.status == "applied"
    assert record.result_snapshot_id == result.snapshot_id

    events = {event.event for event in board.audit(config.run_id).events()}
    assert {"checkpoint_started", "checkpoint_proposed", "checkpoint_decided"} <= events
    assert "operation_applied" in events
    assert "snapshot_frozen" in events


def test_a_rejected_operation_beside_an_accepted_one_does_not_apply() -> None:
    board, config, codebook, base = seeded_board(run_id="mixed")
    result = run_checkpoint(
        board=board,
        config=config,
        codebook=codebook,
        snapshot_id=base,
        agent=agent_proposing([rename_future_to_horizon(), promote_healthcare()]),
        embedder=StubEmbedder(),
        gate=ScriptedGate(
            [
                GateDecision(index=0, verdict=ACCEPT, note="agreed"),
                GateDecision(index=1, verdict=REJECT, note="healthcare is not a family"),
            ]
        ),
    )
    assert result.applied is True
    assert "horizon" in result.codebook.names()
    assert result.codebook.codes[HEALTHCARE].parent_id == POSITIVE, (
        "the rejected reparent must not apply"
    )
    assert result.changelog.verdicts == {ACCEPT: 1, REJECT: 1, EDIT: 0}
    assert result.changelog.entries[1].note == "healthcare is not a family"


# --------------------------------------------------------------------------- #
# 3. An edited operation applies the human's replacement
# --------------------------------------------------------------------------- #


def test_edited_operation_applies_the_humans_replacement_not_the_models() -> None:
    """The human's edit is what lands in the codebook, and the model's is not."""
    board, config, codebook, base = seeded_board(run_id="edited")
    model_wanted = Operation(
        type="rename",
        targets=[FUTURE],
        payload={"name": "tomorrow"},
        rationale="the model's suggestion",
    )
    human_wanted = Operation(
        type="rename",
        targets=[FUTURE],
        payload={"name": "horizon"},
        rationale="the human's replacement",
    )
    result = run_checkpoint(
        board=board,
        config=config,
        codebook=codebook,
        snapshot_id=base,
        agent=agent_proposing([model_wanted]),
        embedder=StubEmbedder(),
        gate=ScriptedGate(
            [
                GateDecision(
                    index=0,
                    verdict=EDIT,
                    operation=human_wanted,
                    note="'tomorrow' reads as a time, not a category",
                )
            ]
        ),
    )
    assert result.applied is True
    names = result.codebook.names()
    assert "horizon" in names
    assert "tomorrow" not in names
    assert result.changelog.verdicts[EDIT] == 1
    assert result.changelog.entries[0].note.startswith("'tomorrow' reads")

    # The proposal recorded on the blackboard is still the model's, and the decision
    # carries the human's replacement: both halves of the exchange survive.
    record = board.read_checkpoint(result.checkpoint_id)
    assert record is not None
    assert record.operations() == [model_wanted]
    assert record.decisions[0]["operation"]["payload"]["name"] == "horizon"


def test_an_edited_operation_is_validated_like_any_other() -> None:
    """A human may not push through what the machine would have been stopped from doing."""
    board, config, codebook, base = seeded_board(run_id="bad-edit")
    result = run_checkpoint(
        board=board,
        config=config,
        codebook=codebook,
        snapshot_id=base,
        agent=agent_proposing([rename_future_to_horizon()]),
        embedder=StubEmbedder(),
        gate=ScriptedGate(
            [
                GateDecision(
                    index=0,
                    verdict=EDIT,
                    operation=Operation(
                        type="rename", targets=[FUTURE], payload={"name": "positive_impacts"}
                    ),
                )
            ]
        ),
    )
    assert result.applied is False
    assert result.snapshot_id is None
    assert result.codebook.to_json_str() == codebook.to_json_str()
    assert "dropped in validation" in result.changelog.entries[0].reason
    markers = {f.data.get(MARKER_KEY) for f in result.report.errors()}
    assert "duplicate_name" in markers


def test_an_edit_with_no_replacement_operation_rejects() -> None:
    board, config, codebook, base = seeded_board(run_id="empty-edit")
    result = run_checkpoint(
        board=board,
        config=config,
        codebook=codebook,
        snapshot_id=base,
        agent=agent_proposing([rename_future_to_horizon()]),
        embedder=StubEmbedder(),
        gate=ScriptedGate([GateDecision(index=0, verdict=EDIT, operation=None)]),
    )
    assert result.applied is False
    assert "no replacement" in result.changelog.entries[0].reason
    assert any(f.data.get(MARKER_KEY) == "gate_edit_missing" for f in result.report.warnings())


def test_silence_and_an_unrecognised_verdict_both_reject() -> None:
    """Every ambiguity at this gate resolves toward "do not change the codebook"."""
    board, config, codebook, base = seeded_board(run_id="ambiguous")
    result = run_checkpoint(
        board=board,
        config=config,
        codebook=codebook,
        snapshot_id=base,
        agent=agent_proposing([rename_future_to_horizon(), promote_healthcare()]),
        embedder=StubEmbedder(),
        # index 0 gets a nonsense verdict; index 1 gets no decision at all.
        gate=ScriptedGate([GateDecision(index=0, verdict="maybe")]),
    )
    assert result.applied is False
    assert result.codebook.to_json_str() == codebook.to_json_str()
    assert "unrecognised verdict" in result.changelog.entries[0].reason
    assert "no decision returned" in result.changelog.entries[1].reason
    assert any(f.data.get(MARKER_KEY) == "gate_verdict" for f in result.report.warnings())


def test_a_decision_for_an_operation_that_is_not_in_the_proposal_is_a_finding() -> None:
    board, config, codebook, base = seeded_board(run_id="stray")
    result = run_checkpoint(
        board=board,
        config=config,
        codebook=codebook,
        snapshot_id=base,
        agent=agent_proposing([rename_future_to_horizon()]),
        embedder=StubEmbedder(),
        gate=ScriptedGate(
            [
                GateDecision(index=0, verdict=ACCEPT),
                GateDecision(index=99, verdict=ACCEPT),
            ]
        ),
    )
    # ScriptedGate filters the out-of-range row itself; the guard is exercised directly
    # below so that a gate that does *not* filter cannot crash the checkpoint.
    assert result.applied is True

    proposal = result.proposal
    report = CheckReport()
    indexed = _decision_index(
        [GateDecision(index=7, verdict=ACCEPT)], len(proposal.script.operations), report
    )
    assert indexed == {}
    assert any(f.data.get(MARKER_KEY) == "gate_index" for f in report.warnings())


# --------------------------------------------------------------------------- #
# 4. Validation drops what cannot be applied — and keeps what can
# --------------------------------------------------------------------------- #


def test_validation_drops_a_nonexistent_target() -> None:
    codebook = toy_codebook()
    validation = validate_script(
        [Operation(type="reparent", targets=[MISSING_TARGET], payload={"new_parent_id": None})],
        codebook,
    )
    assert validation.kept == []
    assert len(validation.dropped) == 1
    assert validation.dropped[0].marker == "unknown_target"
    finding = validation.report.errors()[0]
    assert finding.check_id == CHECK_ID
    assert finding.data[MARKER_KEY] == "unknown_target"
    assert validation.projected.to_json_str() == codebook.to_json_str()


def test_validation_drops_an_operation_that_would_duplicate_a_name() -> None:
    codebook = toy_codebook()
    validation = validate_script(
        [Operation(type="rename", targets=[FUTURE], payload={"name": "positive_impacts"})],
        codebook,
    )
    assert validation.kept == []
    assert validation.dropped[0].marker == "duplicate_name"
    assert any(f.data.get(MARKER_KEY) == "duplicate_name" for f in validation.report.errors())


def test_validation_drops_an_operation_that_would_exceed_the_hierarchy_depth() -> None:
    """Two levels is the PI's rule; an edit that would make three is refused."""
    codebook = toy_codebook()
    validation = validate_script(
        [Operation(type="reparent", targets=[POSITIVE], payload={"new_parent_id": MISUSE})],
        codebook,
    )
    assert validation.kept == []
    assert validation.dropped[0].marker == "new_error"
    assert "hierarchy_too_deep" in validation.dropped[0].reason


def test_validation_drops_a_cycle() -> None:
    codebook = toy_codebook()
    validation = validate_script(
        [Operation(type="reparent", targets=[POSITIVE], payload={"new_parent_id": HEALTHCARE})],
        codebook,
    )
    assert validation.kept == []
    assert "parent_cycle" in validation.dropped[0].reason


def test_validation_drops_a_merge_with_fewer_than_two_distinct_targets() -> None:
    codebook = toy_codebook()
    validation = validate_script(
        [Operation(type="merge", targets=[MISUSE, MISUSE])], codebook
    )
    assert validation.kept == []
    assert validation.dropped[0].marker == "operation_shape"
    assert "at least 2 distinct targets" in validation.dropped[0].reason


def test_validation_drops_a_split_with_no_payload() -> None:
    codebook = toy_codebook()
    validation = validate_script([Operation(type="split", targets=[MISUSE])], codebook)
    assert validation.kept == []
    assert validation.dropped[0].marker == "operation_shape"


def test_the_bad_operations_are_dropped_and_the_good_ones_still_apply() -> None:
    """One hallucinated operation must not discard the good ones beside it."""
    board, config, codebook, base = seeded_board(run_id="mixed-validity")
    script = [
        Operation(type="reparent", targets=[MISSING_TARGET], payload={"new_parent_id": None}),
        Operation(type="rename", targets=[FUTURE], payload={"name": "positive_impacts"}),
        Operation(type="reparent", targets=[POSITIVE], payload={"new_parent_id": MISUSE}),
        rename_future_to_horizon(),
    ]
    result = run_checkpoint(
        board=board,
        config=config,
        codebook=codebook,
        snapshot_id=base,
        agent=agent_proposing(script),
        embedder=StubEmbedder(),
        gate=accept_all(4),
    )

    validation = result.validation
    assert len(validation.dropped) == 3
    assert [d.marker for d in validation.dropped] == [
        "unknown_target",
        "duplicate_name",
        "new_error",
    ]
    # Each drop is a finding, not a silent repair.
    assert len(validation.report.errors()) == 3

    # The one good operation reached the human, at index 0 of the *validated* script.
    assert len(result.proposal.script.operations) == 1
    assert result.proposal.script.operations[0] == rename_future_to_horizon()

    assert result.applied is True
    assert "horizon" in result.codebook.names()


def test_a_proposal_that_would_fail_s6_is_rejected_at_validation() -> None:
    """Evidence naming a response outside the corpus is an S6 ERROR, so it never lands."""
    board, config, codebook, base = seeded_board(run_id="fails-s6")
    fabricated = Operation(
        type="create",
        payload={
            "name": "negative_impacts-surveillance",
            "description": "Constant monitoring of ordinary life.",
            "evidence": [{"response_id": 9999, "quote": "a quote from nowhere", "verified": True}],
        },
        rationale="the model invented a response id",
    )
    result = run_checkpoint(
        board=board,
        config=config,
        codebook=codebook,
        snapshot_id=base,
        agent=agent_proposing([fabricated]),
        embedder=StubEmbedder(),
        gate=accept_all(1),
    )
    assert result.validation.kept == []
    assert result.validation.dropped[0].marker == "new_error"
    assert "evidence_response_missing" in result.validation.dropped[0].reason
    assert result.proposal.script.operations == []
    assert result.applied is False
    assert result.snapshot_id is None
    assert result.codebook.to_json_str() == codebook.to_json_str()


# --------------------------------------------------------------------------- #
# 5. Evidence is never lost
# --------------------------------------------------------------------------- #


def test_a_merge_carries_every_source_quote_into_the_target() -> None:
    """Merge-with-re-examination (the PI's §8), not merge-and-discard."""
    codebook = toy_codebook()
    before = evidence_pairs(codebook)
    applied = apply_operations(codebook, [merge_negative_leaves()], snapshot_id="snap-test")
    after = evidence_pairs(applied.codebook)

    assert after == before, "a merge must not lose one quote"

    survivor = applied.codebook.codes[JOB_DESTRUCTION]
    quotes = {e.quote for e in survivor.evidence}
    # the target's own two quotes, and the source's one
    assert "Firms will hand ticket triage" in quotes
    assert "the whole line runs without a shift supervisor" in quotes
    assert "how narrow the door has become" in quotes, "the source's evidence must travel"
    assert MISUSE not in applied.codebook.codes

    effect = applied.effects[0]
    assert effect.removed == [MISUSE]
    assert applied.codebook.by_name("negative_impacts-misuse") is None


def test_a_split_distributes_evidence_and_loses_none() -> None:
    codebook = toy_codebook()
    before = evidence_pairs(codebook)
    applied = apply_operations(codebook, [split_job_destruction()], snapshot_id="snap-test")
    after = evidence_pairs(applied.codebook)

    assert after == before, "a split must not lose one quote"

    clerical = applied.codebook.by_name("negative_impacts-clerical_work")
    manufacturing = applied.codebook.by_name("negative_impacts-manufacturing")
    assert clerical is not None and manufacturing is not None
    assert [e.response_id for e in clerical.evidence] == [207]
    assert [e.response_id for e in manufacturing.evidence] == [239]
    assert JOB_DESTRUCTION not in applied.codebook.codes


def test_unclaimed_evidence_goes_to_the_first_resulting_code() -> None:
    """Nothing falls between the entries of a split payload."""
    codebook = toy_codebook()
    operation = Operation(
        type="split",
        targets=[JOB_DESTRUCTION],
        payload={
            "into": [
                {"name": "negative_impacts-displacement", "description": "Work displaced."},
                {"name": "negative_impacts-automation", "description": "Work automated."},
            ]
        },
    )
    applied = apply_operations(codebook, [operation], snapshot_id="snap-test")
    assert evidence_pairs(applied.codebook) == evidence_pairs(codebook)
    first = applied.codebook.by_name("negative_impacts-displacement")
    second = applied.codebook.by_name("negative_impacts-automation")
    assert first is not None and second is not None
    assert len(first.evidence) == 2
    assert second.evidence == []


def test_evidence_is_conserved_across_a_whole_multi_operation_script() -> None:
    codebook = toy_codebook()
    applied = apply_operations(
        codebook,
        [split_job_destruction(), reparent_inevitability(), rename_future_to_horizon()],
        snapshot_id="snap-test",
    )
    assert evidence_pairs(applied.codebook) == evidence_pairs(codebook)
    assert applied.evidence_before == applied.evidence_after


def test_the_evidence_guard_is_real_and_raises() -> None:
    """The invariant is asserted, not assumed: prove the guard fires when it should."""
    codebook = toy_codebook()
    stripped = Codebook(
        codes={
            code_id: (replace(code, evidence=[]) if code_id == MISUSE else code)
            for code_id, code in codebook.codes.items()
        }
    )
    with pytest.raises(EvidenceLossError, match="did not conserve evidence"):
        _check_evidence_conserved(codebook, stripped, what="a deliberately lossy edit")


def test_a_merge_that_collapses_a_shared_quote_is_recorded_not_lost() -> None:
    """Two codes quoting the same phrase merge to one carrying it once."""
    shared = Evidence(response_id=207, quote="the same phrase", verified=True, score=1.0)
    codebook = Codebook(
        codes={
            "c-harm": Code(id="c-harm", name="harm", description="Harms."),
            "c-harm-a": Code(
                id="c-harm-a",
                name="harm-a",
                description="One reading.",
                parent_id="c-harm",
                evidence=[shared],
            ),
            "c-harm-b": Code(
                id="c-harm-b",
                name="harm-b",
                description="Another reading.",
                parent_id="c-harm",
                evidence=[shared],
            ),
        }
    )
    applied = apply_operations(
        codebook,
        [Operation(type="merge", targets=["c-harm-a", "c-harm-b"], payload={"into": "c-harm-a"})],
        snapshot_id="snap-test",
    )
    before, after = evidence_pairs(codebook), evidence_pairs(applied.codebook)
    assert set(before) == set(after), "no quote may disappear"
    assert applied.effects[0].evidence_deduplicated == 1
    assert len(applied.codebook.codes["c-harm-a"].evidence) == 1


# --------------------------------------------------------------------------- #
# 6. split and reparent end to end — the anti-flattening operations
# --------------------------------------------------------------------------- #


def test_split_runs_end_to_end_through_the_gate_and_the_store() -> None:
    board, config, codebook, base = seeded_board(run_id="split-e2e")
    result = run_checkpoint(
        board=board,
        config=config,
        codebook=codebook,
        snapshot_id=base,
        agent=agent_proposing([split_job_destruction()]),
        embedder=StubEmbedder(),
        gate=accept_all(1),
    )
    assert result.applied is True
    assert result.snapshot_id is not None
    names = result.codebook.names()
    assert "negative_impacts-clerical_work" in names
    assert "negative_impacts-manufacturing" in names
    assert "negative_impacts-job_destruction" not in names

    stored = board.read_snapshot(result.snapshot_id)
    assert stored.parent_id == base
    assert len(stored.codebook) == len(codebook) + 1  # one out, two in

    # Both new codes hang off the family the split target belonged to.
    for name in ("negative_impacts-clerical_work", "negative_impacts-manufacturing"):
        code = result.codebook.by_name(name)
        assert code is not None
        assert code.parent_id == NEGATIVE
        assert code.created_in_snapshot == base

    entry = result.changelog.applied[0]
    assert entry.effect is not None
    assert entry.effect.removed == [JOB_DESTRUCTION]
    assert len(entry.effect.created) == 2
    assert JOB_DESTRUCTION in result.changelog.removed_code_names or (
        "negative_impacts-job_destruction" in result.changelog.removed_code_names
    )


def test_reparent_runs_end_to_end_and_can_promote_to_the_top_level() -> None:
    board, config, codebook, base = seeded_board(run_id="reparent-e2e")
    result = run_checkpoint(
        board=board,
        config=config,
        codebook=codebook,
        snapshot_id=base,
        agent=agent_proposing(
            [
                reparent_inevitability(),
                Operation(
                    type="reparent",
                    targets=[HEALTHCARE],
                    payload={"new_parent_id": None},
                    rationale="healthcare is a family in its own right",
                ),
            ]
        ),
        embedder=StubEmbedder(),
        gate=accept_all(2),
    )
    assert result.applied is True
    moved = result.codebook.codes[INEVITABILITY]
    assert moved.parent_id == NEGATIVE
    promoted = result.codebook.codes[HEALTHCARE]
    assert promoted.parent_id is None
    assert "promoted" in result.changelog.applied[1].summary


def test_a_merge_reparents_the_children_of_a_removed_source() -> None:
    """A merge may not orphan anything; the move is recorded."""
    codebook = toy_codebook()
    applied = apply_operations(
        codebook,
        [Operation(type="merge", targets=[NEGATIVE, FUTURE], payload={"into": NEGATIVE})],
        snapshot_id="snap-test",
    )
    assert FUTURE not in applied.codebook.codes
    assert applied.codebook.codes[INEVITABILITY].parent_id == NEGATIVE
    assert "re-parented" in applied.effects[0].summary
    assert evidence_pairs(applied.codebook) == evidence_pairs(codebook)


def test_create_admits_a_code_under_its_family() -> None:
    codebook = toy_codebook()
    applied = apply_operations(
        codebook,
        [
            Operation(
                type="create",
                payload={
                    "name": "positive_impacts-education",
                    "description": "Learning becomes cheaper and more available.",
                },
                rationale="a category the coders never proposed",
            )
        ],
        snapshot_id="snap-base",
    )
    created = applied.codebook.by_name("positive_impacts-education")
    assert created is not None
    assert created.parent_id == POSITIVE
    assert created.created_in_snapshot == "snap-base"
    assert created.id == mint_code_id("positive_impacts-education")


# --------------------------------------------------------------------------- #
# 7. Triggers
# --------------------------------------------------------------------------- #


def test_event_driven_fires_on_codebook_health() -> None:
    """Six near-duplicate pairs against a policy maximum of three wakes the slow loop."""
    config = config_for("triggers")
    trigger = should_checkpoint(
        crowded_family_codebook(),
        FlatEmbedder(),
        config,
        responses_coded=12,
        responses_since_checkpoint=10,
    )
    assert trigger.fires is True
    assert trigger.trigger == "health"
    assert trigger.signals.near_duplicates_exceeded is True
    assert trigger.signals.hard_floor_reached is False
    assert "near-duplicate pairs" in trigger.reason
    assert trigger.metrics.near_duplicate_pairs > config.checkpoints.max_near_duplicate_pairs


def test_event_driven_is_held_when_too_few_responses_have_passed() -> None:
    """A trigger without spacing is a report, not a checkpoint."""
    config = config_for("spacing")
    trigger = should_checkpoint(
        crowded_family_codebook(),
        FlatEmbedder(),
        config,
        responses_coded=12,
        responses_since_checkpoint=2,
    )
    assert trigger.fires is False
    assert trigger.trigger == "none"
    assert "held:" in trigger.reason


def test_the_hard_floor_fires_at_fifty_responses_regardless() -> None:
    """A quiet codebook still gets a human look every 50 responses."""
    config = config_for("floor")
    assert config.checkpoints.hard_floor_responses == 50

    quiet = should_checkpoint(
        toy_codebook(),
        StubEmbedder(),
        config,
        responses_coded=49,
        responses_since_checkpoint=49,
    )
    assert quiet.fires is False
    assert quiet.trigger == "none"

    floor = should_checkpoint(
        toy_codebook(),
        StubEmbedder(),
        config,
        responses_coded=50,
        responses_since_checkpoint=50,
    )
    assert floor.fires is True
    assert floor.trigger == "floor"
    assert floor.signals.near_duplicates_exceeded is False
    assert floor.signals.new_codes_exceeded is False
    assert "hard floor reached" in floor.reason
    assert floor.to_json()["trigger"] == "floor"

    # The floor counts from the last checkpoint, not from the start of the run: a
    # checkpoint at response 50 clears it, and the run does not report one due again
    # until another fifty responses have been coded (R1 I1).
    just_after = should_checkpoint(
        toy_codebook(),
        StubEmbedder(),
        config,
        responses_coded=51,
        responses_since_checkpoint=1,
    )
    assert just_after.fires is False and just_after.trigger == "none"


def test_new_codes_per_batch_is_an_event_trigger() -> None:
    config = config_for("growth", checkpoints=CheckpointPolicy(max_new_codes_per_batch=4))
    trigger = should_checkpoint(
        toy_codebook(),
        StubEmbedder(),
        config,
        responses_coded=20,
        responses_since_checkpoint=10,
        previous=Codebook(),
    )
    assert trigger.signals.new_codes == len(toy_codebook())
    assert trigger.trigger == "health"
    assert "new codes this batch" in trigger.reason


def test_fixed_mode_fires_on_chans_cadence() -> None:
    """`mode="fixed"` follows the predecessor's schedule: first 10, then every 10."""
    config = config_for("fixed", checkpoints=CheckpointPolicy(mode="fixed"))
    on_schedule = should_checkpoint(
        toy_codebook(), StubEmbedder(), config, responses_coded=20, responses_since_checkpoint=10
    )
    assert on_schedule.fires is True
    assert on_schedule.trigger == "cadence"
    assert "fixed cadence" in on_schedule.reason

    off_schedule = should_checkpoint(
        toy_codebook(), StubEmbedder(), config, responses_coded=23, responses_since_checkpoint=10
    )
    assert off_schedule.fires is False
    assert off_schedule.trigger == "none"


# --------------------------------------------------------------------------- #
# 8. Determinism
# --------------------------------------------------------------------------- #


def test_the_same_script_applied_twice_gives_the_same_snapshot_id() -> None:
    """Acceptance criterion 3, at the slow loop: no wall clock in a codebook."""
    script = [split_job_destruction(), reparent_inevitability(), rename_future_to_horizon()]

    results = []
    for run_id in ("determinism-a", "determinism-b"):
        board, config, codebook, base = seeded_board(run_id=run_id)
        results.append(
            run_checkpoint(
                board=board,
                config=config,
                codebook=codebook,
                snapshot_id=base,
                agent=agent_proposing(script),
                embedder=StubEmbedder(),
                gate=accept_all(len(script)),
            )
        )
        board.close()

    first, second = results
    assert first.applied and second.applied
    assert first.codebook.to_json_str() == second.codebook.to_json_str()
    assert first.snapshot_id == second.snapshot_id
    assert first.checkpoint_id == second.checkpoint_id or first.run_id != second.run_id

    # And the same script applied straight, without the store, agrees with both.
    applied = apply_operations(toy_codebook(), script, snapshot_id=first.base_snapshot_id)
    assert applied.codebook.to_json_str() == first.codebook.to_json_str()
    assert freeze(applied.codebook).snapshot_id == first.snapshot_id


def test_apply_operations_never_mutates_its_input() -> None:
    codebook = toy_codebook()
    before = codebook.to_json_str()
    apply_operations(
        codebook,
        [split_job_destruction(), merge_negative_leaves()][:1],
        snapshot_id="snap-test",
    )
    assert codebook.to_json_str() == before


# --------------------------------------------------------------------------- #
# 9. The diff a human reads
# --------------------------------------------------------------------------- #


def test_the_diff_carries_the_evidence_at_stake() -> None:
    """The human reads a compact diff, so the weight of evidence must be *on* it."""
    codebook = toy_codebook()
    diffs = build_diff([merge_negative_leaves(), split_job_destruction()], codebook)

    merge_diff = diffs[0]
    assert merge_diff.type == "merge"
    assert merge_diff.evidence_at_stake == {
        "negative_impacts-job_destruction": 2,
        "negative_impacts-misuse": 1,
    }
    assert merge_diff.responses_at_stake == 3
    assert "merged" in merge_diff.summary
    assert merge_diff.rationale

    text = render_diff(diffs, header="CHECKPOINT")
    assert "CHECKPOINT" in text
    assert "evidence at stake" in text
    assert "responses affected" in text
    assert merge_diff.rationale in text
    assert json.dumps(merge_diff.to_json())  # JSON-serialisable for the report


def test_the_diff_of_an_unappliable_operation_says_so() -> None:
    diffs = build_diff(
        [Operation(type="rename", targets=[MISSING_TARGET], payload={"name": "x"})],
        toy_codebook(),
    )
    assert "cannot be applied" in diffs[0].summary


# --------------------------------------------------------------------------- #
# 10. ConsoleGate
# --------------------------------------------------------------------------- #


def console_proposal() -> RefactorProposal:
    """A validated two-operation proposal, built exactly as `run_checkpoint` builds one."""
    codebook = toy_codebook()
    operations = [rename_future_to_horizon(), promote_healthcare()]
    validation = validate_script(operations, codebook)
    assert validation.kept == operations
    script = agent_proposing(operations).propose(
        RefactorContext.from_codebook(codebook, "snap-console")
    )
    return RefactorProposal(
        snapshot_id="snap-console",
        trigger="manual",
        script=replace(script, operations=validation.kept),
        diffs=build_diff(validation.kept, codebook),
        validation=validation,
    )


def console(answers: str) -> tuple[ConsoleGate, io.StringIO]:
    out = io.StringIO()
    return ConsoleGate(stream_in=io.StringIO(answers), stream_out=out), out


def test_console_gate_reads_accept_reject_and_a_note() -> None:
    gate, out = console("a\nr not convinced by the evidence\n")
    decisions = gate.review(console_proposal())
    assert [d.verdict for d in decisions] == [ACCEPT, REJECT]
    assert decisions[1].note == "not convinced by the evidence"
    printed = out.getvalue()
    assert "CHECKPOINT" in printed
    assert "evidence at stake" in printed
    assert "1 of 2 operation(s) accepted." in printed


def test_console_gate_reads_an_edited_operation_as_one_line_of_json() -> None:
    replacement = Operation(type="rename", targets=[FUTURE], payload={"name": "horizon"})
    gate, _ = console(f"e the model's name was wrong\n{json.dumps(replacement.to_json())}\nr\n")
    decisions = gate.review(console_proposal())
    assert decisions[0].verdict == EDIT
    assert decisions[0].operation == replacement
    assert decisions[0].note == "the model's name was wrong"


def test_console_gate_rejects_an_unreadable_edit() -> None:
    gate, out = console("e\nnot json at all\nr\n")
    decisions = gate.review(console_proposal())
    assert decisions[0].verdict == REJECT
    assert "unreadable replacement" in decisions[0].note
    assert "unreadable replacement" in out.getvalue()


def test_console_gate_defaults_to_reject_on_a_blank_line_and_on_nonsense() -> None:
    gate, _ = console("\nwhat\n")
    decisions = gate.review(console_proposal())
    assert [d.verdict for d in decisions] == [REJECT, REJECT]
    assert "unrecognised verdict" in decisions[1].note


def test_console_gate_on_a_closed_pipe_rejects_everything() -> None:
    """A ConsoleGate with no input behaves exactly like RejectAllGate."""
    gate, _ = console("")
    decisions = gate.review(console_proposal())
    assert [d.verdict for d in decisions] == [REJECT, REJECT]
    assert all("input closed" in d.note for d in decisions)


def test_console_gate_drives_a_real_checkpoint() -> None:
    board, config, codebook, base = seeded_board(run_id="console-e2e")
    gate = ConsoleGate(stream_in=io.StringIO("a\n"), stream_out=io.StringIO())
    result = run_checkpoint(
        board=board,
        config=config,
        codebook=codebook,
        snapshot_id=base,
        agent=agent_proposing([rename_future_to_horizon()]),
        embedder=StubEmbedder(),
        gate=gate,
    )
    assert result.applied is True
    assert "horizon" in result.codebook.names()


# --------------------------------------------------------------------------- #
# 11. Offline, end to end, with the delivered mock refactorer
# --------------------------------------------------------------------------- #


def test_the_whole_checkpoint_runs_offline_with_the_mock_refactorer_client() -> None:
    """No key, no network: the mock proposes, validation prunes, the human decides.

    The mock's proposal is structurally valid and semantically arbitrary by design. On
    this codebook it proposes a split, a re-parent that would create a parent cycle, and
    a no-op — so this test also exercises the projection gate on a proposal nobody
    hand-wrote for it.
    """
    board, config, codebook, base = seeded_board(run_id="offline-e2e")
    result = run_checkpoint(
        board=board,
        config=config,
        codebook=codebook,
        snapshot_id=base,
        agent=mock_agent(),
        embedder=StubEmbedder(),
        gate=accept_all(3),
    )

    assert result.proposal.validation.n_proposed == 3
    assert "split" in [op.type for op in result.validation.kept]
    # Exactly which code the mock picks depends on the digest of the prompt, so the
    # claim is about the *gate*, not about the mock's arbitrary choice: whatever it
    # proposed re-parenting would have broken S6, and the projection caught it.
    assert [d.marker for d in result.validation.dropped] == ["new_error"]
    assert result.validation.dropped[0].operation.type == "reparent"

    assert result.applied is True
    assert result.snapshot_id is not None
    assert evidence_pairs(result.codebook) == evidence_pairs(codebook)

    calls = board.read_llm_calls(config.run_id)
    assert [call.role for call in calls] == ["refactorer"]
    assert calls[0].task == TaskType.REFACTOR.value

    metrics = {m.metric for m in board.read_health_metrics(config.run_id)}
    assert {"n_codes", "near_duplicate_pairs", "family_balance_gini"} <= metrics

    assert json.dumps(result.to_json()), "CheckpointResult must be JSON-serialisable"


def test_checkpoint_refuses_a_snapshot_the_store_does_not_have() -> None:
    board, config, codebook, _ = seeded_board(run_id="unknown-snapshot")
    with pytest.raises(KeyError, match="no snapshot"):
        run_checkpoint(
            board=board,
            config=config,
            codebook=codebook,
            snapshot_id="snap-never-written",
            agent=mock_agent(),
            embedder=StubEmbedder(),
        )


def test_a_working_codebook_that_has_drifted_from_its_snapshot_is_a_warning() -> None:
    """ADR-0021 permits the drift; it does not permit it to go unrecorded."""
    board, config, codebook, base = seeded_board(run_id="drift")
    drifted = Codebook(
        codes={
            **codebook.codes,
            "c-adoption": Code(
                id="c-adoption",
                name="adoption",
                description="How quickly AI arrives.",
                created_in_snapshot=base,
            ),
        }
    )
    result = run_checkpoint(
        board=board,
        config=config,
        codebook=drifted,
        snapshot_id=base,
        agent=agent_proposing([Operation(type="noop")]),
        embedder=StubEmbedder(),
    )
    assert any(f.data.get(MARKER_KEY) == "snapshot_drift" for f in result.report.warnings())


def test_every_validation_finding_is_a_check_finding_under_s6() -> None:
    """The slow loop reports through the frozen contracts, not a parallel channel."""
    codebook = toy_codebook()
    validation = validate_script(
        [
            Operation(type="merge", targets=[MISUSE]),
            Operation(type="reparent", targets=[MISSING_TARGET], payload={"new_parent_id": None}),
        ],
        codebook,
    )
    assert len(validation.report.findings) == 2
    for finding in validation.report:
        assert finding.check_id == CHECK_ID
        assert finding.severity is Severity.ERROR
        assert finding.scope == "codebook"
        assert MARKER_KEY in finding.data
        assert finding.to_json()["check_id"] == CHECK_ID
