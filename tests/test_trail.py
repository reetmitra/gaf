"""Tests for `gaf.report.trail`.

Real checkpoints are driven through `gaf.pipeline.slow_loop.run_checkpoint` with
`ScriptedGate` over an offline fast-loop run of the synthetic corpus, exactly as
`tests/test_slow_loop.py` does — merge, split, reparent, rename, a dropped operation,
an edited operation and a reject-all. No respondent text appears anywhere: the corpus
is the project's own synthetic fixture and every invented code name is structural.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

from gaf.agents.refactorer import RefactorerAgent
from gaf.config import RunConfig
from gaf.llm.base import LLMRequest, LLMResult, TaskType
from gaf.llm.mock import MockRefactorerClient
from gaf.models import Codebook, Operation
from gaf.pipeline.fast_loop import FastLoopResult, LoopComponents, offline_components, run_fast_loop
from gaf.pipeline.slow_loop import (
    ACCEPT,
    EDIT,
    REJECT,
    CheckpointResult,
    Gate,
    GateDecision,
    RejectAllGate,
    ScriptedGate,
    run_checkpoint,
)
from gaf.report.trail import (
    RATIONALE_GLOSS,
    REASONING_GLOSS,
    ReorganisationTrail,
    TrailEntry,
    build_trail,
)
from gaf.store.blackboard import Blackboard
from tests.fixtures.corpus import synthetic_corpus

# --------------------------------------------------------------------------- #
# Helpers
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


def _coded_run(run_id: str) -> tuple[Blackboard, RunConfig, LoopComponents, FastLoopResult]:
    config = _config(run_id)
    board = Blackboard(":memory:")
    components = offline_components(config)
    result = run_fast_loop(synthetic_corpus(), config=config, board=board, components=components)
    return board, config, components, result


def accept_all(n: int) -> ScriptedGate:
    return ScriptedGate([GateDecision(index=i, verdict=ACCEPT) for i in range(n)])


def _checkpoint(
    board: Blackboard,
    config: RunConfig,
    codebook: Codebook,
    snapshot_id: str,
    components: LoopComponents,
    operations: Sequence[Operation],
    *,
    gate: Gate,
    trigger: str = "manual",
) -> CheckpointResult:
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


# --------------------------------------------------------------------------- #
# 1. No checkpoint
# --------------------------------------------------------------------------- #


def test_build_trail_with_no_checkpoint_says_so_in_one_sentence() -> None:
    board, config, _, _ = _coded_run("trail-none")
    trail = build_trail(board, config.run_id)
    assert isinstance(trail, ReorganisationTrail)
    assert trail.entries == []
    assert trail.lineage == []
    text = trail.to_markdown()
    lines = [line for line in text.splitlines() if line.strip()]
    # One sentence naming the run, after the heading.
    assert any("never reorganised" in line and config.run_id in line for line in lines)


# --------------------------------------------------------------------------- #
# 2. Merge and split
# --------------------------------------------------------------------------- #


def test_build_trail_reads_a_merge_and_a_split() -> None:
    board, config, components, result = _coded_run("trail-merge-split")
    codebook = result.codebook
    codes = codebook.sorted_codes()
    assert len(codes) >= 3
    merge_targets = [codes[0].id, codes[1].id]
    split_target = codes[2]
    ops = [
        Operation(type="merge", targets=merge_targets, payload={"into": merge_targets[0]}),
        Operation(
            type="split",
            targets=[split_target.id],
            payload={
                "into": [
                    {"name": "invented-part_one", "description": "First part."},
                    {"name": "invented-part_two", "description": "Second part."},
                ]
            },
            rationale="two distinguishable strands of meaning",
        ),
    ]
    base_snapshot = result.snapshot_ids[-1]
    cp = _checkpoint(board, config, codebook, base_snapshot, components, ops, gate=accept_all(2))
    assert cp.applied is True

    trail = build_trail(board, config.run_id)
    assert len(trail.entries) == 1
    entry = trail.entries[0]
    assert isinstance(entry, TrailEntry)
    assert entry.status == "applied"
    assert entry.changelog.checkpoint_id == cp.checkpoint_id
    assert entry.changelog.base_snapshot_id == base_snapshot
    assert entry.changelog.result_snapshot_id == cp.snapshot_id
    assert [e.type for e in entry.changelog.entries] == ["merge", "split"]
    assert all(e.applied for e in entry.changelog.entries)
    assert entry.changelog.entries[1].rationale == "two distinguishable strands of meaning"
    # Reused directly from the slow loop: the rendered text names both snapshots.
    rendered = entry.changelog.render()
    assert base_snapshot in rendered
    assert cp.snapshot_id in rendered

    reasons = {row.reason for row in trail.lineage}
    assert reasons == {"merged", "split"}
    merged_row = next(row for row in trail.lineage if row.reason == "merged")
    assert merged_row.from_name == codes[1].name
    assert merged_row.to_names == [codes[0].name]
    split_row = next(row for row in trail.lineage if row.reason == "split")
    assert split_row.from_name == split_target.name
    assert set(split_row.to_names) == {"invented-part_one", "invented-part_two"}


# --------------------------------------------------------------------------- #
# 3. Rename cascade and reparent, and the lineage of a rename
# --------------------------------------------------------------------------- #


def test_build_trail_reads_a_rename_and_a_reparent() -> None:
    board, config, components, result = _coded_run("trail-rename-reparent")
    codebook = result.codebook
    codes = codebook.sorted_codes()
    rename_target = codes[0]
    reparent_target = codes[1]
    new_parent = codes[2]
    ops = [
        Operation(type="rename", targets=[rename_target.id], payload={"name": "renamed_code"}),
        Operation(
            type="reparent", targets=[reparent_target.id], payload={"new_parent_id": new_parent.id}
        ),
    ]
    base_snapshot = result.snapshot_ids[-1]
    cp = _checkpoint(board, config, codebook, base_snapshot, components, ops, gate=accept_all(2))
    assert cp.applied is True

    trail = build_trail(board, config.run_id)
    entry = trail.entries[0]
    assert [e.type for e in entry.changelog.entries] == ["rename", "reparent"]
    assert entry.changelog.entries[0].effect is not None
    assert entry.changelog.entries[0].effect.renamed  # old id -> new id

    lineage_row = next(row for row in trail.lineage if row.reason == "renamed")
    assert lineage_row.from_name == rename_target.name
    assert lineage_row.to_names == ["renamed_code"]
    assert not any(row.reason == "reparented" for row in trail.lineage), (
        "a reparent changes no name, so it never belongs in the lineage table"
    )


# --------------------------------------------------------------------------- #
# 4. A dropped operation and a surviving one, together
# --------------------------------------------------------------------------- #


def test_build_trail_reports_a_dropped_operation_beside_an_applied_one() -> None:
    board, config, components, result = _coded_run("trail-dropped")
    codebook = result.codebook
    codes = codebook.sorted_codes()
    missing_target = "code-this-does-not-exist"
    ops = [
        Operation(type="reparent", targets=[missing_target], payload={"new_parent_id": None}),
        Operation(type="rename", targets=[codes[0].id], payload={"name": "survives_validation"}),
    ]
    base_snapshot = result.snapshot_ids[-1]
    cp = _checkpoint(board, config, codebook, base_snapshot, components, ops, gate=accept_all(1))
    assert cp.validation.dropped, "the missing-target operation must be dropped, not applied"
    assert cp.applied is True

    trail = build_trail(board, config.run_id)
    entry = trail.entries[0]
    assert len(entry.changelog.dropped) == 1
    assert entry.changelog.dropped[0].marker == "unknown_target"
    assert entry.changelog.dropped[0].operation.targets == [missing_target]
    # The surviving operation is unaffected by its dropped neighbour.
    assert len(entry.changelog.entries) == 1
    assert entry.changelog.entries[0].type == "rename"
    assert entry.changelog.entries[0].applied is True


# --------------------------------------------------------------------------- #
# 5. An edited operation
# --------------------------------------------------------------------------- #


def test_build_trail_reports_the_models_proposal_and_the_humans_edit() -> None:
    board, config, components, result = _coded_run("trail-edit")
    codebook = result.codebook
    target = codebook.sorted_codes()[0]
    model_proposed = Operation(type="rename", targets=[target.id], payload={"name": "model_name"})
    human_edit = Operation(type="rename", targets=[target.id], payload={"name": "human_name"})
    base_snapshot = result.snapshot_ids[-1]
    cp = _checkpoint(
        board,
        config,
        codebook,
        base_snapshot,
        components,
        [model_proposed],
        gate=ScriptedGate(
            [GateDecision(index=0, verdict=EDIT, operation=human_edit, note="clearer name")]
        ),
    )
    assert cp.applied is True

    trail = build_trail(board, config.run_id)
    entry = trail.entries[0]
    assert len(entry.edited) == 1
    edit = entry.edited[0]
    assert edit.index == 0
    assert edit.before.payload["name"] == "model_name"
    assert edit.after.payload["name"] == "human_name"
    assert entry.changelog.entries[0].note == "clearer name"
    assert "human_name" in entry.changelog.entries[0].summary

    # The edit must show up in both serialisations, not just on the dataclass.
    payload = trail.to_json()
    assert payload["entries"][0]["edited"][0] == edit.to_json()
    assert json.dumps(payload)
    text = trail.to_markdown()
    assert "Edited operations" in text
    assert "model_name" in text and "human_name" in text


def test_build_trail_treats_an_edit_with_no_replacement_as_no_edit_at_all() -> None:
    """`run_checkpoint` itself treats an edit verdict with no replacement operation as
    a rejection (see `tests/test_slow_loop.py::test_an_edit_with_no_replacement_operation_rejects`);
    the decision is still recorded with `operation: null`, and `build_trail` must skip
    it rather than crash on the missing replacement."""
    board, config, components, result = _coded_run("trail-empty-edit")
    codebook = result.codebook
    target = codebook.sorted_codes()[0]
    base_snapshot = result.snapshot_ids[-1]
    cp = _checkpoint(
        board,
        config,
        codebook,
        base_snapshot,
        components,
        [Operation(type="rename", targets=[target.id], payload={"name": "would_not_apply"})],
        gate=ScriptedGate([GateDecision(index=0, verdict=EDIT, operation=None)]),
    )
    assert cp.applied is False

    trail = build_trail(board, config.run_id)
    entry = trail.entries[0]
    assert entry.edited == []
    assert entry.changelog.entries[0].applied is False
    assert "no replacement" in entry.changelog.entries[0].reason


# --------------------------------------------------------------------------- #
# 6. Reject-all is still an entry
# --------------------------------------------------------------------------- #


def test_build_trail_records_a_reject_all_checkpoint_as_a_decision() -> None:
    board, config, components, result = _coded_run("trail-reject-all")
    codebook = result.codebook
    target = codebook.sorted_codes()[0]
    ops = [Operation(type="rename", targets=[target.id], payload={"name": "would_not_apply"})]
    base_snapshot = result.snapshot_ids[-1]
    cp = _checkpoint(
        board, config, codebook, base_snapshot, components, ops, gate=RejectAllGate()
    )
    assert cp.applied is False
    assert cp.status == "rejected"

    trail = build_trail(board, config.run_id)
    assert len(trail.entries) == 1
    entry = trail.entries[0]
    assert entry.status == "rejected"
    assert entry.changelog.entries[0].verdict == REJECT
    assert entry.changelog.entries[0].applied is False
    assert entry.changelog.codes_before == entry.changelog.codes_after
    assert entry.changelog.result_snapshot_id is None
    assert entry.families_after == entry.families_before
    assert trail.lineage == []


# --------------------------------------------------------------------------- #
# 7. Multiple checkpoints — chronological order even when at_response_count ties
# --------------------------------------------------------------------------- #


def test_build_trail_orders_checkpoints_chronologically_not_just_by_response_count() -> None:
    """Two checkpoints run back to back, with no response coded between them, tie on
    `at_response_count`; `Blackboard.read_checkpoints` then breaks the tie by a content
    hash unrelated to execution order. `build_trail` must still report them in the
    order they actually fired, read from the audit log's own event order.
    """
    board, config, components, result = _coded_run("trail-order")
    codebook = result.codebook
    target = codebook.sorted_codes()[0]
    base_snapshot = result.snapshot_ids[-1]

    first = _checkpoint(
        board,
        config,
        codebook,
        base_snapshot,
        components,
        [Operation(type="rename", targets=[target.id], payload={"name": "first_pass"})],
        gate=accept_all(1),
        trigger="health",
    )
    assert first.applied is True
    second = _checkpoint(
        board,
        config,
        first.codebook,
        first.snapshot_id,
        components,
        [Operation(type="noop")],
        gate=accept_all(1),
        trigger="manual",
    )
    assert second.status == "noop"

    trail = build_trail(board, config.run_id)
    assert [entry.changelog.checkpoint_id for entry in trail.entries] == [
        first.checkpoint_id,
        second.checkpoint_id,
    ]
    assert trail.entries[0].trigger == "health"
    assert trail.entries[1].trigger == "manual"


# --------------------------------------------------------------------------- #
# 8. The reason sentence, health, and net change
# --------------------------------------------------------------------------- #


def test_build_trail_reason_sentence_names_the_trigger() -> None:
    board, config, components, result = _coded_run("trail-reason")
    codebook = result.codebook
    base_snapshot = result.snapshot_ids[-1]
    cp = _checkpoint(
        board,
        config,
        codebook,
        base_snapshot,
        components,
        [Operation(type="noop")],
        gate=accept_all(1),
        trigger="floor",
    )
    trail = build_trail(board, config.run_id)
    entry = trail.entries[0]
    assert entry.trigger == "floor"
    assert "floor" in entry.reason
    assert entry.refactorer_reasoning == (cp.proposal.script.reasoning or "")
    assert entry.health_before["n_codes"] == len(codebook)
    assert entry.families_before == len(codebook.families())


def test_reason_sentence_covers_every_trigger_shape() -> None:
    """A direct, exhaustive check of `_reason_sentence`'s own branches: the four named
    triggers, the "health" trigger both with and without a near-duplicate count to
    report, and a trigger this module has never seen a name for."""
    from gaf.report.trail import _reason_sentence

    started = {"at_response_count": 42}
    assert _reason_sentence("floor", started, {}) == (
        "the hard floor was reached at 42 responses coded"
    )
    assert _reason_sentence("cadence", started, {}) == (
        "a fixed-cadence checkpoint at 42 responses coded"
    )
    assert _reason_sentence("manual", started, {}) == "opened manually"
    assert _reason_sentence("mystery", started, {}) == "trigger 'mystery' at 42 responses coded"

    empty_health = _reason_sentence("health", started, {})
    assert "an event-driven threshold was exceeded" in empty_health

    detailed_health = _reason_sentence(
        "health", started, {"near_duplicate_pairs": 6, "new_codes": 12, "n_codes": 12}
    )
    assert "6 near-duplicate pair(s)" in detailed_health
    # The stored `new_codes` is the whole codebook (`run_checkpoint` passes no
    # `previous=`), so the sentence reports it as the codebook's size and never as
    # growth since a checkpoint. That the two really are the same number on a real run
    # is pinned by `test_the_health_line_says_what_the_stored_number_means`; this test
    # only covers the branch (R1, weak-test scan).
    assert "12 code(s) in the codebook" in detailed_health
    assert "since the last checkpoint" not in detailed_health


def test_trail_entry_net_change_and_health_after_are_computed_without_an_embedder() -> None:
    """`build_trail(board, run_id)` takes no embedder, so near-duplicate-pairs-after is
    reported as unavailable rather than approximated; codes and families after are
    always available because they need no embedding space."""
    board, config, components, result = _coded_run("trail-health-after")
    codebook = result.codebook
    codes = codebook.sorted_codes()
    ops = [
        Operation(
            type="create",
            payload={"name": "invented-brand_new", "description": "A human-invented category."},
        )
    ]
    base_snapshot = result.snapshot_ids[-1]
    cp = _checkpoint(board, config, codebook, base_snapshot, components, ops, gate=accept_all(1))
    assert cp.applied is True

    trail = build_trail(board, config.run_id)
    entry = trail.entries[0]
    payload = entry.to_json()
    assert payload["near_duplicate_pairs_after"] is None
    assert payload["net_change"]["near_duplicate_pairs"] is None
    assert payload["net_change"]["codes"] == 1
    assert entry.families_after >= entry.families_before
    assert entry.changelog.codes_after == entry.changelog.codes_before + 1
    _ = codes  # not otherwise needed; keeps the corpus read explicit for the reader


# --------------------------------------------------------------------------- #
# 9. Shape: to_json / to_json_str / to_markdown
# --------------------------------------------------------------------------- #


def test_reorganisation_trail_to_json_round_trips_and_is_json_serialisable() -> None:
    board, config, components, result = _coded_run("trail-json")
    codebook = result.codebook
    target = codebook.sorted_codes()[0]
    base_snapshot = result.snapshot_ids[-1]
    _checkpoint(
        board,
        config,
        codebook,
        base_snapshot,
        components,
        [Operation(type="rename", targets=[target.id], payload={"name": "shape_check"})],
        gate=accept_all(1),
    )
    trail = build_trail(board, config.run_id)
    payload = trail.to_json()
    assert json.loads(trail.to_json_str()) == payload
    assert json.dumps(payload)  # must not raise
    assert set(payload) == {"run_id", "n_checkpoints", "entries", "lineage"}
    assert payload["n_checkpoints"] == 1
    assert isinstance(payload["entries"][0]["changelog"], dict)


def test_reorganisation_trail_to_markdown_names_the_checkpoint_and_the_lineage() -> None:
    board, config, components, result = _coded_run("trail-markdown")
    codebook = result.codebook
    codes = codebook.sorted_codes()
    ops = [Operation(type="merge", targets=[codes[0].id, codes[1].id], payload={"into": codes[0].id})]
    base_snapshot = result.snapshot_ids[-1]
    cp = _checkpoint(board, config, codebook, base_snapshot, components, ops, gate=accept_all(1))
    trail = build_trail(board, config.run_id)
    text = trail.to_markdown()
    assert "## Codebook reorganisation trail" in text
    assert cp.checkpoint_id in text
    assert "### Lineage" in text
    assert codes[1].name in text


# --------------------------------------------------------------------------- #
# R1 audit findings
# --------------------------------------------------------------------------- #

#: The same length `tests/test_views.py` holds the shareable page to, and the same one
#: `make provenance` now uses (ADR-0047). The trail is the artefact most likely to be
#: pasted into a methods appendix.
TRAIL_SHINGLE = 20


def _corpus_leaks(haystack: str) -> list[tuple[int, str]]:
    """Every synthetic response with a `TRAIL_SHINGLE`-character run inside `haystack`."""
    found: list[tuple[int, str]] = []
    for response in synthetic_corpus():
        text = response.content
        for start in range(0, max(0, len(text) - TRAIL_SHINGLE) + 1):
            shingle = text[start : start + TRAIL_SHINGLE]
            if shingle in haystack:
                found.append((response.id, shingle))
                break
    return found


def _a_long_quote(codebook: Codebook) -> tuple[int, str]:
    """A real (response_id, quote) pair from the run, long enough to be a leak."""
    for code in codebook.sorted_codes():
        for evidence in code.evidence:
            if len(evidence.quote) >= TRAIL_SHINGLE + 6:
                return evidence.response_id, evidence.quote
    raise AssertionError("the fast loop must produce at least one long verified quote")


def _leaky_script(codebook: Codebook) -> tuple[list[Operation], Operation, int, str]:
    """Three operations that each carry respondent text, plus the human's edit.

    op0 a `create` whose parent does not exist, carrying evidence -> dropped
        `unknown_target`, with the quote sitting in its payload;
    op1 a `create` carrying evidence no code holds -> dropped `evidence_loss`, with
        the quote in the payload *and* in the validator's own sentence;
    op2 a `split` the human edits into one that moves quotes between the parts.
    """
    response_id, quote = _a_long_quote(codebook)
    evidence = [{"response_id": response_id, "quote": quote, "verified": True, "score": 1.0}]
    split_target = codebook.sorted_codes()[0]
    proposed_split = Operation(
        type="split",
        targets=[split_target.id],
        payload={
            "into": [
                {"name": "invented-part_one"},
                {"name": "invented-part_two"},
            ]
        },
    )
    edited_split = Operation(
        type="split",
        targets=[split_target.id],
        payload={
            "into": [
                {"name": "invented-part_one", "quotes": [quote]},
                {"name": "invented-part_two", "response_ids": [response_id]},
            ]
        },
    )
    operations = [
        Operation(
            type="create",
            payload={
                "name": "invented-orphan",
                "parent_id": "code-this-does-not-exist",
                "evidence": evidence,
            },
        ),
        Operation(
            type="create",
            payload={"name": "invented-with_evidence", "evidence": evidence},
        ),
        proposed_split,
    ]
    return operations, edited_split, response_id, quote


def test_the_trail_never_carries_respondent_text_from_a_dropped_or_edited_operation() -> None:
    """R1 C1. The trail is a shareable artefact; an operation payload is not."""
    board, config, components, result = _coded_run("trail-privacy")
    codebook = result.codebook
    operations, edited_split, response_id, quote = _leaky_script(codebook)

    cp = _checkpoint(
        board,
        config,
        codebook,
        result.snapshot_ids[-1],
        components,
        operations,
        gate=ScriptedGate(
            [GateDecision(index=0, verdict=EDIT, operation=edited_split, note="moved the quotes")]
        ),
    )
    markers = sorted(d.marker for d in cp.validation.dropped)
    assert markers == ["evidence_loss", "unknown_target"], (
        "the fixture must really produce both drops, or this test proves nothing"
    )
    assert any(quote in json.dumps(d.to_json()) for d in cp.validation.dropped), (
        "the slow loop's own record does carry the quote; runs/ is where that belongs"
    )

    trail = build_trail(board, config.run_id)
    rendered = trail.to_json_str() + "\n" + trail.to_markdown()
    assert quote not in rendered
    assert _corpus_leaks(rendered) == []

    entry = trail.entries[0]
    assert [d.marker for d in entry.changelog.dropped] == ["unknown_target", "evidence_loss"]
    for dropped in entry.changelog.dropped:
        assert "evidence" not in dropped.operation.payload
        assert dropped.operation.payload.get("name", "").startswith("invented-")
    assert entry.changelog.dropped[0].operation.targets == []
    assert str(response_id) in rendered, "a response number is not respondent text"

    edit = entry.edited[0]
    assert "quotes" not in edit.after.payload["into"][0]
    assert edit.after.payload["into"][1]["response_ids"] == [response_id]
    assert "quotes" in edit.withheld_payload_keys


def test_the_trail_names_the_payload_keys_it_withheld() -> None:
    """R1 C1. Withholding must be visible, or the artefact reads as complete."""
    board, config, components, result = _coded_run("trail-withheld")
    codebook = result.codebook
    operations, edited_split, _, _ = _leaky_script(codebook)
    _checkpoint(
        board,
        config,
        codebook,
        result.snapshot_ids[-1],
        components,
        operations,
        gate=ScriptedGate([GateDecision(index=0, verdict=EDIT, operation=edited_split)]),
    )
    trail = build_trail(board, config.run_id)
    entry = trail.entries[0]

    payload = entry.to_json()
    assert payload["edited"][0]["withheld_payload_keys"] == ["quotes"]
    assert payload["withheld_payload_keys"] == ["evidence", "quotes"]
    assert "Payload keys withheld here: evidence." in (
        payload["changelog"]["dropped"][0]["reason"]
    )
    text = trail.to_markdown()
    assert "withheld from this artefact: evidence, quotes" in text


def test_a_dropped_operation_reports_its_marker_rather_than_the_validators_sentence() -> None:
    """R1 C1. A validator's sentence quotes what it rejected; a marker cannot."""
    board, config, components, result = _coded_run("trail-drop-reason")
    codebook = result.codebook
    operations, edited_split, _, quote = _leaky_script(codebook)
    _checkpoint(
        board,
        config,
        codebook,
        result.snapshot_ids[-1],
        components,
        operations,
        gate=ScriptedGate([GateDecision(index=0, verdict=EDIT, operation=edited_split)]),
    )
    trail = build_trail(board, config.run_id)
    dropped = {d.marker: d.reason for d in trail.entries[0].changelog.dropped}

    assert quote not in dropped["evidence_loss"]
    assert "evidence" in dropped["evidence_loss"]
    assert "findings.json" in dropped["evidence_loss"]
    assert "not a code in this codebook" in dropped["unknown_target"]


def test_the_lineage_omits_a_split_whose_heir_keeps_the_original_name() -> None:
    """R1, brief Important. A name still in the codebook never "no longer exists"."""
    board, config, components, result = _coded_run("trail-same-name-split")
    codebook = result.codebook
    target = codebook.sorted_codes()[0]
    cp = _checkpoint(
        board,
        config,
        codebook,
        result.snapshot_ids[-1],
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
    assert cp.applied is True

    trail = build_trail(board, config.run_id)
    assert [row.from_name for row in trail.lineage] == [], (
        f"{target.name!r} is still in the final codebook"
    )
    assert "Lineage" not in trail.to_markdown()


def test_the_health_line_says_what_the_stored_number_means() -> None:
    """R1, brief Important. `run_checkpoint` passes no `previous`, so new == n_codes."""
    board, config, components, result = _coded_run("trail-health-wording")
    codebook = result.codebook
    _checkpoint(
        board,
        config,
        codebook,
        result.snapshot_ids[-1],
        components,
        [Operation(type="noop")],
        gate=accept_all(1),
        trigger="health",
    )
    trail = build_trail(board, config.run_id)
    entry = trail.entries[0]
    assert entry.health_before["new_codes"] == entry.health_before["n_codes"], (
        "the stored health row was measured with no previous codebook"
    )
    assert "since the last checkpoint" not in entry.reason
    assert f"{len(codebook)} code(s) in the codebook" in entry.reason


def test_two_checkpoints_tying_on_every_identifying_field_stay_two() -> None:
    """R1 C7. The documented happy path: reject all, then re-run interactively."""
    board, config, components, result = _coded_run("trail-tied")
    codebook = result.codebook
    target = codebook.sorted_codes()[0]
    base = result.snapshot_ids[-1]
    operations = [Operation(type="rename", targets=[target.id], payload={"name": "renamed_once"})]

    rejected = _checkpoint(
        board, config, codebook, base, components, operations, gate=RejectAllGate()
    )
    assert rejected.applied is False and rejected.status == "rejected"
    accepted = _checkpoint(
        board, config, codebook, base, components, operations, gate=accept_all(1)
    )
    assert accepted.applied is True
    assert accepted.checkpoint_id != rejected.checkpoint_id, (
        "two checkpoints are two rows, whatever their identifying fields tie on"
    )

    assert len(board.read_checkpoints(config.run_id)) == 2
    trail = build_trail(board, config.run_id)
    assert [e.status for e in trail.entries] == ["rejected", "applied"]
    assert [e.changelog.checkpoint_id for e in trail.entries] == [
        rejected.checkpoint_id,
        accepted.checkpoint_id,
    ]
    assert trail.entries[0].changelog.entries[0].verdict == REJECT
    assert trail.entries[1].changelog.entries[0].verdict == ACCEPT


def test_no_shareable_artefact_carries_respondent_text_after_a_leaky_checkpoint(
    tmp_path: Path,
) -> None:
    """R1 C1, end to end: the trail, the timeline and the page, from one real run.

    A checkpoint carrying all three triggers at once — an edited split that moves
    quotes, a dropped `create` whose evidence sits in its payload, and an
    evidence-loss drop whose validator sentence embeds a ``(response_id, quote)``
    pair — is driven through the CLI's own run directory, and every artefact D7 and
    ADR-0036 call shareable is scanned for a twenty-character run of any response.
    """
    import json as _json

    from gaf.cli import main
    from gaf.cli._common import _run_config_from_json
    from gaf.ingest.corpus import write_corpus_json
    from gaf.report.run_report import RunArtefact
    from gaf.report.timeline import build_timeline, timeline_svg
    from gaf.report.views import render_views_html, views_from_run

    corpus_path = tmp_path / "corpus.json"
    write_corpus_json(synthetic_corpus(), corpus_path)
    run_dir = tmp_path / "run"
    assert (
        main(
            [
                "run",
                "--corpus",
                str(corpus_path),
                "--run-id",
                "leaky",
                "--out",
                str(run_dir),
                "--cache-dir",
                str(tmp_path / "cache"),
            ]
        )
        == 0
    )

    document = _json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    artefact = RunArtefact.from_json(document)
    config = _run_config_from_json(artefact.config)
    components = offline_components(config)
    with Blackboard(run_dir / "gaf.sqlite") as board:
        snapshots = board.read_snapshots(run_id="leaky")
        codebook = snapshots[-1].codebook
        operations, edited_split, _, quote = _leaky_script(codebook)
        cp = _checkpoint(
            board,
            config,
            codebook,
            snapshots[-1].snapshot_id,
            components,
            operations,
            gate=ScriptedGate([GateDecision(index=0, verdict=EDIT, operation=edited_split)]),
        )
        assert sorted(d.marker for d in cp.validation.dropped) == [
            "evidence_loss",
            "unknown_target",
        ]
        assert cp.applied is True, "the edited split must really apply"

        trail = build_trail(board, "leaky")
        timeline = build_timeline(board, "leaky")
        artefacts = {
            "reorganisation_trail.json": trail.to_json_str(),
            "reorganisation_trail.md": trail.to_markdown(),
            "timeline.json": _json.dumps(timeline.to_json(), sort_keys=True),
            "timeline.md": timeline.to_markdown(),
            "timeline.svg": timeline_svg(timeline),
        }

    artefacts["views.html"] = render_views_html(views_from_run(artefact, run_dir))

    # A positive control: the scan must really find respondent text where there is
    # some, or a clean result below would mean nothing. `codebook.json` carries the
    # verified quotes and belongs under `runs/`, which is exactly the point.
    assert _corpus_leaks((run_dir / "codebook.json").read_text(encoding="utf-8"))

    leaks = {name: _corpus_leaks(text) for name, text in artefacts.items()}
    assert {name: found for name, found in leaks.items() if found} == {}
    for name, text in artefacts.items():
        assert quote not in text, name


# --------------------------------------------------------------------------- #
# R2 audit findings
# --------------------------------------------------------------------------- #


def _rationale_script(codebook: Codebook) -> tuple[list[Operation], Operation, int, str]:
    """An edit script whose *rationales* carry respondent text, at all three sinks.

    R2 C-1: the Refactorer prompt required the model to name the quotes an operation
    rests on, and `Operation.rationale` reached the trail — as a changelog entry, on a
    dropped operation and on both sides of an edited one — with nothing testing it.

    op0 a `create` whose parent does not exist -> dropped `unknown_target`, so the
        rationale travels on `DroppedOperation.operation`;
    op1 a `merge` the human accepts, so the rationale travels as a `ChangelogEntry`;
    op2 a `split` the human edits, so the rationale travels on `before` and `after`.
    """
    response_id, quote = _a_long_quote(codebook)
    codes = codebook.sorted_codes()
    leaky = f"The quotes under this code say {quote}, which is one idea and not two."
    operations = [
        Operation(
            type="create",
            payload={"name": "invented-orphan", "parent_id": "code-this-does-not-exist"},
            rationale=leaky,
        ),
        Operation(
            type="merge",
            targets=[codes[0].id, codes[1].id],
            payload={"into": codes[0].id},
            rationale=leaky,
        ),
        Operation(
            type="split",
            targets=[codes[2].id],
            payload={"into": [{"name": "invented-part_one"}, {"name": "invented-part_two"}]},
            rationale=leaky,
        ),
    ]
    edited_split = Operation(
        type="split",
        targets=[codes[2].id],
        payload={"into": [{"name": "invented-part_one"}, {"name": "invented-part_two"}]},
        rationale=leaky,
    )
    return operations, edited_split, response_id, quote


def test_a_rationale_quoting_a_response_is_withheld_from_the_trail() -> None:
    """R2 C-1. The prompt required quotes in the rationale; the trail rendered it raw."""
    board, config, components, result = _coded_run("trail-rationale")
    codebook = result.codebook
    operations, edited_split, _, quote = _rationale_script(codebook)

    cp = _checkpoint(
        board,
        config,
        codebook,
        result.snapshot_ids[-1],
        components,
        operations,
        gate=ScriptedGate(
            [
                GateDecision(index=0, verdict=ACCEPT),
                GateDecision(index=1, verdict=EDIT, operation=edited_split),
            ]
        ),
    )
    assert [d.marker for d in cp.validation.dropped] == ["unknown_target"], (
        "the fixture must really drop op0, or the dropped-operation sink is untested"
    )

    trail = build_trail(board, config.run_id)
    rendered = trail.to_json_str() + "\n" + trail.to_markdown()
    assert quote not in rendered
    assert _corpus_leaks(rendered) == []
    assert "rationale withheld: shares wording with a response" in rendered

    entry = trail.entries[0]
    assert entry.changelog.entries[0].rationale == RATIONALE_GLOSS
    assert entry.changelog.dropped[0].operation.rationale == RATIONALE_GLOSS
    assert entry.edited[0].before.rationale == RATIONALE_GLOSS
    assert entry.edited[0].after.rationale == RATIONALE_GLOSS
    # Withholding a rationale is not withholding the operation: the structure stays.
    assert entry.changelog.dropped[0].operation.payload["name"] == "invented-orphan"
    assert entry.changelog.entries[0].type == "merge"
    assert "invented-part_one" in rendered


def test_a_rationale_that_quotes_nobody_is_rendered_as_written() -> None:
    """R2 C-1. The guard withholds wording, not rationales: a clean one must survive."""
    board, config, components, result = _coded_run("trail-rationale-clean")
    codebook = result.codebook
    codes = codebook.sorted_codes()
    clean = "Responses 203 and 207 carry two different ideas under one name; split it."
    cp = _checkpoint(
        board,
        config,
        codebook,
        result.snapshot_ids[-1],
        components,
        [
            Operation(
                type="merge",
                targets=[codes[0].id, codes[1].id],
                payload={"into": codes[0].id},
                rationale=clean,
            )
        ],
        gate=accept_all(1),
    )
    assert cp.validation.dropped == []
    trail = build_trail(board, config.run_id)
    assert trail.entries[0].changelog.entries[0].rationale == clean
    assert clean in trail.to_json_str()


def test_the_refactorers_own_reasoning_paragraph_is_guarded_too() -> None:
    """R2 C-1. `reasoning` is the same free model prose, into the same artefact."""
    board, config, components, result = _coded_run("trail-reasoning")
    codebook = result.codebook
    codes = codebook.sorted_codes()
    _, quote = _a_long_quote(codebook)
    agent = RefactorerAgent(
        FixedRefactorerClient(
            [
                Operation(
                    type="merge",
                    targets=[codes[0].id, codes[1].id],
                    payload={"into": codes[0].id},
                    rationale="Two names for one idea; see responses 203 and 207.",
                )
            ],
            reasoning=f"I merged the pair whose evidence reads {quote} and left the rest.",
        )
    )
    run_checkpoint(
        board=board,
        config=config,
        codebook=codebook,
        snapshot_id=result.snapshot_ids[-1],
        agent=agent,
        embedder=components.embedder,
        gate=accept_all(1),
        trigger="manual",
    )
    trail = build_trail(board, config.run_id)
    rendered = trail.to_json_str() + "\n" + trail.to_markdown()
    assert quote not in rendered
    assert _corpus_leaks(rendered) == []
    assert trail.entries[0].refactorer_reasoning == REASONING_GLOSS
