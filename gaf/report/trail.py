"""A readable trail of every codebook reorganisation.

Where `gaf.report.timeline` reads a whole run, this module reads the slow loop's own
checkpoints (`gaf.store.blackboard.Blackboard.read_checkpoints`) and turns each one
into an entry a person can read on its own: why the slow loop woke, what the
Refactorer proposed and why, what deterministic validation dropped, the human's
verdict on each surviving operation, what applying it actually did, and the codebook's
shape before and after. A run with no checkpoint gets a trail that says so in one
sentence; a checkpoint where a human rejected every operation is still an entry,
because a rejection is a decision (`gaf.pipeline.slow_loop.RejectAllGate` is the
default, and the whole point of that default is that it is auditable, not invisible).

This module re-derives none of the slow loop's own logic. `gaf.pipeline.slow_loop.
Changelog` already renders exactly this story — trigger, base and result snapshot,
per-operation verdicts and effects, codes and evidence before and after, the removed
names — so `build_trail` reconstructs one real `Changelog` per checkpoint from what
the store actually holds (`CheckpointRecord.proposal`/`.decisions` and this run's own
``operation_applied``/``operation_rejected`` events) and calls its own `.render()`
rather than re-writing a second description of the same facts.

Two things the stored record does not hold, said here rather than guessed at:

* **The exact reason sentence `should_checkpoint` produced is not persisted.**
  `gaf.pipeline.slow_loop.run_checkpoint` accepts a bare `trigger` string; the prose
  explanation is a property of the transient `CheckpointTrigger` object a caller may
  have computed beforehand, and neither `gaf checkpoint` nor `run_checkpoint` writes
  it to the store. `build_trail` reconstructs an equivalent sentence from what *is*
  stored — the `checkpoint_started` event's counts and the checkpoint's own recorded
  health — rather than replaying a string that was never written down.
* **The stored health row has no "previous" codebook.** `run_checkpoint` calls
  `gaf.checks.health.codebook_health` once, without ``previous=``, so its ``new_codes``
  field is the whole codebook rather than the growth since the last checkpoint. This
  module therefore reports that number as what it is — ``N code(s) in the codebook``
  — and never as ``N new code(s) since the last checkpoint``, which is a different
  and unrecorded quantity.
* **Codebook health *after* a checkpoint is not recomputed by the pipeline.**
  `run_checkpoint` measures health once, before proposing, against the *base*
  snapshot; nothing calls `gaf.checks.health.codebook_health` again afterwards, and
  that check needs an embedding space this module is not given (`build_trail`'s
  signature takes only a store and a run id). This module reports what a plain
  reading of the result codebook can say without one — its code and family counts —
  and reports near-duplicate pairs after as unavailable rather than approximating one
  from a fallback embedder the run may not have used.

Validation principle: **transparency** — a reorganisation is read from the same rows
the audit log and the checkpoints table already hold, in the order the slow loop wrote
them, so a methods reviewer can check this module's account against the store itself.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from dataclasses import replace as dataclass_replace
from typing import Any

from gaf.models import Codebook, Operation
from gaf.pipeline.slow_loop import Changelog, ChangelogEntry, DroppedOperation, OperationEffect
from gaf.store.audit import AuditEvent
from gaf.store.blackboard import Blackboard, CheckpointRecord

__all__ = [
    "DROP_GLOSS",
    "RATIONALE_GLOSS",
    "RATIONALE_SHINGLE_WORDS",
    "REASONING_GLOSS",
    "SHAREABLE_PAYLOAD_KEYS",
    "EditedOperation",
    "LineageRow",
    "ReorganisationTrail",
    "TrailEntry",
    "build_trail",
]

#: The only `gaf.models.Operation` payload keys this artefact may carry, at any depth.
#: Everything else is withheld by name. An operation payload is where respondent text
#: enters a reorganisation: a ``create`` carries ``evidence``, and a split entry
#: carries ``quotes`` — editing a split *means* moving quotes, so the operation a
#: human is most likely to edit is the one most likely to hold them. Rendering the raw
#: payload wrote those quotes verbatim into `reorganisation_trail.json` and ``.md``
#: (R1 C1), contradicting ADR-0036. An allow-list rather than a deny-list, so a
#: payload key added later is withheld until somebody decides it is safe.
SHAREABLE_PAYLOAD_KEYS: frozenset[str] = frozenset(
    {"name", "into", "new_parent_id", "parent_id", "response_ids"}
)

#: What each validation marker means, written **here** rather than taken from the
#: validator. A validator's own sentence names the data it rejected — an
#: `EvidenceLossError` embeds a ``(response_id, quote)`` pair verbatim — so the trail
#: carries the marker, the operation's structure and this gloss, and sends a reader to
#: the run's own ``findings.json`` (under ``runs/``) for the sentence itself.
DROP_GLOSS: dict[str, str] = {
    "operation_shape": (
        "the operation's own shape was wrong: a missing or malformed payload field"
    ),
    "unknown_target": "the operation named a code that is not a code in this codebook",
    "duplicate_name": "applying it would have produced two codes with the same name",
    "new_error": "the resulting codebook would have gained a new S6 error",
    "evidence_loss": (
        "applying it would have lost, invented or multiplied a piece of evidence"
    ),
}

_WITHHELD_SENTENCE = (
    "The validator's own sentence can name the respondent text it rejected and is "
    "withheld here; it is in this run's findings.json, under runs/."
)

#: What stands in for a rationale that shares wording with the run's own text. The
#: operation's type, targets and filtered payload are still emitted beside it:
#: withholding a rationale is not withholding the operation.
RATIONALE_GLOSS = "rationale withheld: shares wording with a response"

#: The same, for the Refactorer's closing paragraph about the script as a whole.
REASONING_GLOSS = "reasoning withheld: shares wording with a response"

#: The window, **in words**, at which a rationale counts as reproducing respondent
#: text. Words rather than the repository's character shingles because a rationale is
#: model prose *about* codes: it names them, it counts responses, and it will share
#: short character runs with any response on the same subject no matter how it is
#: written. Eight consecutive words in common is not a subject in common; it is a
#: sentence in common. A text shorter than the window is compared whole, so a quote
#: too short to fill it is still caught entire.
RATIONALE_SHINGLE_WORDS = 8

_WORD = re.compile(r"\w+")


def _words(text: str) -> tuple[str, ...]:
    """`text` as case-folded word tokens, punctuation and spacing discarded.

    Comparing tokens rather than characters is what makes the test survive the
    re-punctuation a model does when it embeds a quote in a sentence of its own.
    """
    return tuple(_WORD.findall(text.casefold()))


class _RunWording:
    """Every run of `RATIONALE_SHINGLE_WORDS` words this run's own text contains.

    Built from the quotes in the run's evidence and from every response in the store,
    which is the whole of what a Refactorer could have read. A text of fewer than
    `RATIONALE_SHINGLE_WORDS` words is held whole and looked for whole, so a short
    quote is not invisible merely for being short — the gap the repository's
    30-character provenance shingle had (R2 I-1).
    """

    def __init__(self, texts: Iterable[str], width: int = RATIONALE_SHINGLE_WORDS) -> None:
        self.width = width
        #: run length -> the runs of that length. Short texts get their own bucket so
        #: they can be matched at their own length rather than not at all.
        self._runs: dict[int, set[tuple[str, ...]]] = {}
        for text in texts:
            words = _words(text)
            if not words:
                continue
            size = min(self.width, len(words))
            bucket = self._runs.setdefault(size, set())
            for i in range(len(words) - size + 1):
                bucket.add(words[i : i + size])

    def shares_a_run(self, text: str) -> bool:
        """Whether `text` reproduces any run of the run's own wording."""
        words = _words(text)
        if not words:
            return False
        for size, bucket in self._runs.items():
            for i in range(len(words) - size + 1):
                if words[i : i + size] in bucket:
                    return True
        return False

    def guarded(self, text: str, gloss: str = RATIONALE_GLOSS) -> str:
        """`text`, or `gloss` where it shares wording with the run's own text."""
        if not text:
            return text
        return gloss if self.shares_a_run(text) else text


def _run_wording(board: Blackboard, run_id: str, snapshots: Iterable[Codebook]) -> _RunWording:
    """The needle set for one run: its evidence quotes and every stored response.

    Read here rather than passed in because `build_trail`'s signature is a store and a
    run id, and the store is where both live.
    """
    texts: list[str] = [response.content for response in board.read_responses()]
    for codebook in snapshots:
        for code in codebook.sorted_codes():
            texts.extend(evidence.quote for evidence in code.evidence)
    for assignment in board.assignments_for_run(run_id):
        if assignment.segment:
            texts.append(assignment.segment)
    return _RunWording(texts)


def _shareable_payload(value: Any) -> Any:
    """`value` with every key outside `SHAREABLE_PAYLOAD_KEYS` removed, recursively.

    Recursive because a ``split`` hides its text one level down: ``payload["into"]`` is
    a list of ``{"name": ..., "quotes": [...]}`` entries.
    """
    if isinstance(value, Mapping):
        return {
            key: _shareable_payload(item)
            for key, item in value.items()
            if key in SHAREABLE_PAYLOAD_KEYS
        }
    if isinstance(value, list):
        return [_shareable_payload(item) for item in value]
    return value


def _withheld_keys(value: Any) -> set[str]:
    """Every key `_shareable_payload` would remove from `value`, at any depth."""
    out: set[str] = set()
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key not in SHAREABLE_PAYLOAD_KEYS:
                out.add(str(key))
            else:
                out |= _withheld_keys(item)
    elif isinstance(value, list):
        for item in value:
            out |= _withheld_keys(item)
    return out


def _shareable_operation(operation: Operation, guard: _RunWording) -> Operation:
    """The same operation with a payload *and a rationale* this artefact may carry.

    `Operation.to_json` emits `rationale`, so every sink that renders an operation —
    a dropped one, and both sides of an edited one — carried it too (R2 C-1).
    """
    return dataclass_replace(
        operation,
        payload=_shareable_payload(dict(operation.payload)),
        rationale=guard.guarded(operation.rationale),
    )


def _drop_reason(marker: str, withheld: Sequence[str]) -> str:
    """What to say about a dropped operation, from its marker and what was removed."""
    gloss = DROP_GLOSS.get(marker, "dropped in validation")
    parts = [f"{gloss} (marker {marker!r})."]
    if withheld:
        parts.append(f"Payload keys withheld here: {', '.join(withheld)}.")
    parts.append(_WITHHELD_SENTENCE)
    return " ".join(parts)


@dataclass(frozen=True, slots=True)
class EditedOperation:
    """One operation the human edited: the model's proposal and the replacement.

    `before` and `after` are the two operations **with their payloads filtered to
    `SHAREABLE_PAYLOAD_KEYS` and their rationales put through the wording guard**, not
    as they were proposed. Editing a split is how a
    human moves quotes between the parts, so this is precisely where respondent text
    entered the trail (R1 C1). `withheld_payload_keys` names what was removed, from
    either side, so the artefact does not read as complete when it is not. The
    operations as written are on the checkpoint record in the store, under ``runs/``.
    """

    index: int
    before: Operation
    after: Operation
    withheld_payload_keys: list[str] = field(default_factory=list)

    @classmethod
    def from_pair(
        cls, index: int, before: Operation, after: Operation, guard: _RunWording
    ) -> EditedOperation:
        withheld = _withheld_keys(dict(before.payload)) | _withheld_keys(dict(after.payload))
        return cls(
            index=index,
            before=_shareable_operation(before, guard),
            after=_shareable_operation(after, guard),
            withheld_payload_keys=sorted(withheld),
        )

    def to_json(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "before": self.before.to_json(),
            "after": self.after.to_json(),
            "withheld_payload_keys": list(self.withheld_payload_keys),
        }


@dataclass(frozen=True, slots=True)
class TrailEntry:
    """One checkpoint, readable on its own.

    Wraps a real `gaf.pipeline.slow_loop.Changelog` — reconstructed from the store
    rather than re-derived — with the facts a changelog does not itself carry: why
    the checkpoint opened, the codebook's health going in, and what a human changed
    when they edited an operation instead of accepting or rejecting it outright.
    """

    status: str
    trigger: str
    reason: str
    health_before: dict[str, Any]
    families_before: int
    families_after: int
    refactorer_reasoning: str
    edited: list[EditedOperation]
    changelog: Changelog
    #: Every operation payload key this entry withheld, across its dropped and edited
    #: operations. Withholding has to be visible, or the artefact reads as complete.
    withheld_payload_keys: list[str] = field(default_factory=list)

    @property
    def near_duplicate_pairs_before(self) -> int:
        return int(self.health_before.get("near_duplicate_pairs", 0))

    def to_json(self) -> dict[str, Any]:
        return {
            "checkpoint_id": self.changelog.checkpoint_id,
            "status": self.status,
            "trigger": self.trigger,
            "reason": self.reason,
            "at_response_count": self.changelog.at_response_count,
            "base_snapshot_id": self.changelog.base_snapshot_id,
            "result_snapshot_id": self.changelog.result_snapshot_id,
            "health_before": dict(self.health_before),
            "families_before": self.families_before,
            "families_after": self.families_after,
            "near_duplicate_pairs_before": self.near_duplicate_pairs_before,
            # Not computed: codebook_health needs an embedding space this module is
            # not given, and run_checkpoint never recomputes it after applying a
            # script. See the module docstring.
            "near_duplicate_pairs_after": None,
            "refactorer_reasoning": self.refactorer_reasoning,
            "edited": [e.to_json() for e in self.edited],
            "withheld_payload_keys": list(self.withheld_payload_keys),
            "net_change": {
                "codes": self.changelog.codes_after - self.changelog.codes_before,
                "families": self.families_after - self.families_before,
                "near_duplicate_pairs": None,
            },
            "changelog": self.changelog.to_json(),
        }


@dataclass(frozen=True, slots=True)
class LineageRow:
    """One name that no longer exists in the final codebook, and what it became."""

    from_name: str
    to_names: list[str]
    reason: str  # "merged" | "split" | "renamed"
    checkpoint_id: str

    def to_json(self) -> dict[str, Any]:
        return {
            "from_name": self.from_name,
            "to_names": list(self.to_names),
            "reason": self.reason,
            "checkpoint_id": self.checkpoint_id,
        }


@dataclass(frozen=True, slots=True)
class ReorganisationTrail:
    """One entry per checkpoint, in order, plus the lineage of every name that no
    longer exists across the whole run."""

    run_id: str
    entries: list[TrailEntry] = field(default_factory=list)
    lineage: list[LineageRow] = field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "n_checkpoints": len(self.entries),
            "entries": [entry.to_json() for entry in self.entries],
            "lineage": [row.to_json() for row in self.lineage],
        }

    def to_json_str(self) -> str:
        return json.dumps(self.to_json(), sort_keys=True, ensure_ascii=False, indent=2)

    def to_markdown(self) -> str:
        lines = ["## Codebook reorganisation trail", ""]
        if not self.entries:
            lines.append(
                f"No checkpoint ran in run `{self.run_id}`: the codebook was never "
                "reorganised."
            )
            return "\n".join(lines) + "\n"

        lines.append(f"Run `{self.run_id}` — {len(self.entries)} checkpoint(s).")
        for position, entry in enumerate(self.entries, start=1):
            lines.append("")
            lines.append(
                f"### Checkpoint {position} — {entry.changelog.checkpoint_id} "
                f"({entry.status})"
            )
            lines.append("")
            lines.append(f"Woke on trigger **{entry.trigger}**: {entry.reason}")
            lines.append("")
            lines.append(
                f"Codebook health before: {entry.health_before.get('n_codes', '?')} codes, "
                f"{entry.families_before} families, "
                f"{entry.near_duplicate_pairs_before} near-duplicate pair(s)."
            )
            if entry.refactorer_reasoning:
                lines.append("")
                lines.append(f"Refactorer: {entry.refactorer_reasoning}")
            lines.append("")
            lines.append(entry.changelog.render())
            if entry.edited:
                lines.append("")
                lines.append("Edited operations — the model's proposal, then the human's replacement:")
                for edit in entry.edited:
                    lines.append(f"  [{edit.index}] {edit.before.to_json()}")
                    lines.append(f"       -> {edit.after.to_json()}")
            if entry.withheld_payload_keys:
                lines.append("")
                lines.append(
                    "Operation payload key(s) withheld from this artefact: "
                    f"{', '.join(entry.withheld_payload_keys)}. They can carry a "
                    "respondent's words, which this document never does (ADR-0036); "
                    "the operations as written are on the checkpoint record under "
                    "`runs/`."
                )
            net_codes = entry.changelog.codes_after - entry.changelog.codes_before
            net_families = entry.families_after - entry.families_before
            lines.append("")
            lines.append(
                f"Health after: {entry.families_after} families. Net change: "
                f"{net_codes:+d} code(s), {net_families:+d} famil{'y' if abs(net_families) == 1 else 'ies'}, "
                "near-duplicate pairs not recomputed (see the module note above)."
            )

        if self.lineage:
            lines.append("")
            lines.append("### Lineage — every name that no longer exists")
            lines.append("")
            lines.append("| was | became | how | checkpoint |")
            lines.append("|---|---|---|---|")
            for row in self.lineage:
                lines.append(
                    f"| {row.from_name} | {', '.join(row.to_names)} | {row.reason} | "
                    f"{row.checkpoint_id} |"
                )
        return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
# Reconstructing a Changelog from the store
# --------------------------------------------------------------------------- #


def _group_operation_events(events: Sequence[AuditEvent]) -> dict[str, list[AuditEvent]]:
    """checkpoint id -> its own ``operation_applied``/``operation_rejected`` events,
    in order.

    Bracketed by ``checkpoint_proposed`` (which mints the checkpoint id) and
    ``checkpoint_decided``. ``operation_dropped`` events are not collected here:
    `CheckpointRecord.proposal["validation"]["dropped"]` already holds the same
    facts, stored once, on the record itself.
    """
    groups: dict[str, list[AuditEvent]] = {}
    current_id: str | None = None
    for event in events:
        if event.event == "checkpoint_proposed":
            current_id = str(event.payload.get("checkpoint_id", ""))
            groups.setdefault(current_id, [])
        elif event.event in ("operation_applied", "operation_rejected") and current_id is not None:
            groups[current_id].append(event)
        elif event.event == "checkpoint_decided":
            current_id = None
    return groups


def _started_payload_by_checkpoint(events: Sequence[AuditEvent]) -> dict[str, Mapping[str, Any]]:
    """checkpoint id -> the payload of its own ``checkpoint_started`` event.

    ``checkpoint_started`` fires before the checkpoint id is minted (`checkpoint_
    proposed` mints it), so this pairs the two by their known adjacency rather than a
    shared id neither event carries.
    """
    out: dict[str, Mapping[str, Any]] = {}
    pending: Mapping[str, Any] = {}
    for event in events:
        if event.event == "checkpoint_started":
            pending = event.payload
        elif event.event == "checkpoint_proposed":
            out[str(event.payload.get("checkpoint_id", ""))] = pending
            pending = {}
    return out


def _effect_from_json(payload: Mapping[str, Any]) -> OperationEffect:
    return OperationEffect(
        index=int(payload["index"]),
        type=str(payload["type"]),
        summary=str(payload["summary"]),
        created=[str(c) for c in payload.get("created", [])],
        removed=[str(c) for c in payload.get("removed", [])],
        changed=[str(c) for c in payload.get("changed", [])],
        renamed={str(k): str(v) for k, v in (payload.get("renamed") or {}).items()},
        names={str(k): str(v) for k, v in (payload.get("names") or {}).items()},
        evidence_before=int(payload.get("evidence_before", 0)),
        evidence_after=int(payload.get("evidence_after", 0)),
    )


def _reason_sentence(trigger: str, started: Mapping[str, Any], health_before: Mapping[str, Any]) -> str:
    """An equivalent of `CheckpointTrigger.reason`, reconstructed from stored counts.

    Not the same string `should_checkpoint` would have produced — that sentence is
    never written to the store (see the module docstring) — but the same facts: how
    many responses had been coded, how many near-duplicate pairs and new codes the
    health row carried.
    """
    at_response_count = started.get("at_response_count")
    if trigger == "floor":
        return f"the hard floor was reached at {at_response_count} responses coded"
    if trigger == "cadence":
        return f"a fixed-cadence checkpoint at {at_response_count} responses coded"
    if trigger == "health":
        bits: list[str] = []
        near_duplicates = health_before.get("near_duplicate_pairs")
        if near_duplicates:
            bits.append(f"{near_duplicates} near-duplicate pair(s)")
        # NOT "new since the last checkpoint": `run_checkpoint` calls
        # `codebook_health` with no `previous=`, so the stored `new_codes` is the whole
        # codebook every time. Relabelling it read "14 new code(s) since the last
        # checkpoint" at the *first* checkpoint of a 14-code run (R1, brief
        # Important). The sentence now says what the stored number is.
        n_codes = health_before.get("n_codes")
        if n_codes:
            bits.append(f"{n_codes} code(s) in the codebook")
        detail = ", ".join(bits) if bits else "an event-driven threshold was exceeded"
        return f"codebook health trigger at {at_response_count} responses: {detail}"
    if trigger == "manual":
        return "opened manually"
    return f"trigger {trigger!r} at {at_response_count} responses coded"


def _trail_entry(
    record: CheckpointRecord,
    *,
    ops_events: Sequence[AuditEvent],
    started: Mapping[str, Any],
    snapshot_by_id: Mapping[str, Codebook],
    guard: _RunWording,
) -> TrailEntry:
    operations = record.operations()
    # Neither the payload, the rationale nor the validator's sentence may travel: a
    # dropped `create` carries its `evidence` in the payload, the Refactorer prompt
    # once required the rationale to name the quotes the operation rests on (R2 C-1),
    # and an `EvidenceLossError` embeds a
    # ``(response_id, quote)`` pair in its message (R1 C1). `DroppedOperation` is the
    # slow loop's own shape and is reused, carrying a filtered operation and a reason
    # written from the marker here.
    dropped: list[DroppedOperation] = []
    dropped_withheld: list[str] = []
    for item in (record.proposal.get("validation") or {}).get("dropped", []):
        operation = Operation.from_json(item["operation"])
        marker = str(item["marker"])
        withheld = sorted(_withheld_keys(dict(operation.payload)))
        dropped.append(
            DroppedOperation(
                index=int(item["index"]),
                operation=_shareable_operation(operation, guard),
                marker=marker,
                reason=_drop_reason(marker, withheld),
            )
        )
        dropped_withheld.extend(withheld)

    verdict_by_index: dict[int, str] = {}
    note_by_index: dict[int, str] = {}
    reason_by_index: dict[int, str] = {}
    summary_by_index: dict[int, str] = {}
    effect_by_index: dict[int, OperationEffect] = {}
    for event in ops_events:
        payload = event.payload
        index = int(payload["index"])
        verdict_by_index[index] = str(payload.get("verdict", ""))
        note_by_index[index] = str(payload.get("note", ""))
        reason_by_index[index] = str(payload.get("reason", ""))
        summary_by_index[index] = str(payload.get("summary", ""))
        effect = payload.get("effect")
        if effect:
            effect_by_index[index] = _effect_from_json(effect)

    entries = [
        ChangelogEntry(
            index=index,
            type=operation.type,
            verdict=verdict_by_index.get(index, ""),
            applied=index in effect_by_index,
            rationale=guard.guarded(operation.rationale),
            note=note_by_index.get(index, ""),
            summary=summary_by_index.get(index, ""),
            effect=effect_by_index.get(index),
            reason=reason_by_index.get(index, ""),
        )
        for index, operation in enumerate(operations)
    ]

    edited: list[EditedOperation] = []
    for decision in record.decisions:
        if str(decision.get("verdict", "")).strip().casefold() != "edit":
            continue
        replacement = decision.get("operation")
        index = int(decision["index"])
        if replacement is None or not 0 <= index < len(operations):
            continue
        edited.append(
            EditedOperation.from_pair(
                index, operations[index], Operation.from_json(replacement), guard
            )
        )

    changelog = Changelog(
        run_id=record.run_id,
        checkpoint_id=record.checkpoint_id,
        trigger=record.trigger,
        at_response_count=record.at_response_count,
        base_snapshot_id=record.base_snapshot_id,
        result_snapshot_id=record.result_snapshot_id,
        entries=entries,
        dropped=dropped,
        codes_before=int(started.get("n_codes", 0)),
        codes_after=_codebook_size(snapshot_by_id, record.result_snapshot_id or record.base_snapshot_id),
        evidence_before=_evidence_total(snapshot_by_id, record.base_snapshot_id),
        evidence_after=_evidence_total(
            snapshot_by_id, record.result_snapshot_id or record.base_snapshot_id
        ),
    )

    health_before = dict(record.proposal.get("health") or {})
    families_before = int(health_before.get("n_families", 0))
    result_codebook = snapshot_by_id.get(record.result_snapshot_id or record.base_snapshot_id)
    families_after = len(result_codebook.families()) if result_codebook is not None else families_before

    return TrailEntry(
        status=record.status,
        trigger=record.trigger,
        reason=_reason_sentence(record.trigger, started, health_before),
        health_before=health_before,
        families_before=families_before,
        families_after=families_after,
        refactorer_reasoning=guard.guarded(
            str(record.proposal.get("reasoning", "")), REASONING_GLOSS
        ),
        edited=edited,
        changelog=changelog,
        withheld_payload_keys=sorted(
            set(dropped_withheld) | {k for e in edited for k in e.withheld_payload_keys}
        ),
    )


def _codebook_size(snapshot_by_id: Mapping[str, Codebook], snapshot_id: str) -> int:
    codebook = snapshot_by_id.get(snapshot_id)
    return len(codebook) if codebook is not None else 0


def _evidence_total(snapshot_by_id: Mapping[str, Codebook], snapshot_id: str) -> int:
    codebook = snapshot_by_id.get(snapshot_id)
    if codebook is None:
        return 0
    return sum(len(code.evidence) for code in codebook.sorted_codes())


# --------------------------------------------------------------------------- #
# Lineage
# --------------------------------------------------------------------------- #


def _lineage_from_entry(
    entry: TrailEntry, base_codebook: Codebook | None
) -> list[LineageRow]:
    """Rows for the "every name that no longer exists" table.

    A row is only earned by a name the operation actually took out of the codebook. An
    operation that removes a name and puts the same name back — a split whose heir is
    named after its target, which `_apply_split` explicitly permits — removes nothing
    and earns nothing.
    """
    rows: list[LineageRow] = []
    for changelog_entry in entry.changelog.applied:
        effect = changelog_entry.effect
        if effect is None:
            continue
        if effect.type == "merge":
            target_id = effect.changed[0] if effect.changed else None
            target_name = effect.names.get(target_id, target_id or "") if target_id else ""
            for removed_id in effect.removed:
                rows.append(
                    LineageRow(
                        from_name=effect.names.get(removed_id, removed_id),
                        to_names=[target_name],
                        reason="merged",
                        checkpoint_id=entry.changelog.checkpoint_id,
                    )
                )
        elif effect.type == "split":
            target_id = effect.removed[0] if effect.removed else None
            if target_id is None:
                continue
            created_names = [effect.names.get(cid, cid) for cid in effect.created]
            from_name = effect.names.get(target_id, target_id)
            # A code id is the content hash of its name, so a split whose heir keeps
            # the target's name re-creates the same id: the name is removed and
            # created by one operation and is alive in the final codebook. Under the
            # heading "every name that no longer exists" that row is simply false
            # (R1, brief Important).
            if target_id in effect.created or from_name in created_names:
                continue
            rows.append(
                LineageRow(
                    from_name=from_name,
                    to_names=created_names,
                    reason="split",
                    checkpoint_id=entry.changelog.checkpoint_id,
                )
            )
        elif effect.type == "rename":
            for old_id, new_id in effect.renamed.items():
                old_name = effect.names.get(old_id)
                if old_name is None and base_codebook is not None and old_id in base_codebook.codes:
                    old_name = base_codebook.codes[old_id].name
                rows.append(
                    LineageRow(
                        from_name=old_name or old_id,
                        to_names=[effect.names.get(new_id, new_id)],
                        reason="renamed",
                        checkpoint_id=entry.changelog.checkpoint_id,
                    )
                )
    return rows


# --------------------------------------------------------------------------- #
# The public entry point
# --------------------------------------------------------------------------- #


def _checkpoint_order(events: Sequence[AuditEvent]) -> dict[str, int]:
    """checkpoint id -> the `event_id` of its own ``checkpoint_decided`` event.

    `Blackboard.read_checkpoints` orders by ``(at_response_count, checkpoint_id)``,
    which is a total order but not always a *chronological* one: two checkpoints run
    back to back with no response coded between them (a rejected checkpoint followed
    immediately by another, say) share an `at_response_count`, and the tiebreaker is
    then a content hash unrelated to which one actually ran first. The audit log's own
    `event_id` — its insertion order, and the one ordering this whole module treats as
    authoritative — is what `build_trail` sorts checkpoints by instead.
    """
    order: dict[str, int] = {}
    for event in events:
        if event.event == "checkpoint_decided":
            order[str(event.payload.get("checkpoint_id", ""))] = event.event_id
    return order


def build_trail(board: Blackboard, run_id: str) -> ReorganisationTrail:
    """Read one run's checkpoints into a `ReorganisationTrail`, in the order they fired.

    Reads `board.read_checkpoints(run_id)` for the stored proposal and decisions, this
    run's audit log once for the operation-level detail a `CheckpointRecord` does not
    itself carry (and for the true firing order — see `_checkpoint_order`), and this
    run's snapshots for the codebooks each checkpoint's `Changelog` needs to report
    codes and evidence before and after.
    """
    checkpoints = board.read_checkpoints(run_id)
    if not checkpoints:
        return ReorganisationTrail(run_id=run_id, entries=[], lineage=[])

    events = board.audit(run_id).events()
    order = _checkpoint_order(events)
    checkpoints = sorted(
        checkpoints, key=lambda record: order.get(record.checkpoint_id, record.at_response_count)
    )
    ops_by_checkpoint = _group_operation_events(events)
    started_by_checkpoint = _started_payload_by_checkpoint(events)
    snapshot_by_id = {
        snapshot.snapshot_id: snapshot.codebook
        for snapshot in board.read_snapshots(run_id=run_id)
    }
    # Read once for the whole trail: the Refactorer's prose is tested against every
    # response the store holds and every quote this run's evidence carries (R2 C-1).
    guard = _run_wording(board, run_id, snapshot_by_id.values())

    entries: list[TrailEntry] = []
    lineage: list[LineageRow] = []
    for record in checkpoints:
        entry = _trail_entry(
            record,
            ops_events=ops_by_checkpoint.get(record.checkpoint_id, []),
            started=started_by_checkpoint.get(record.checkpoint_id, {}),
            snapshot_by_id=snapshot_by_id,
            guard=guard,
        )
        entries.append(entry)
        lineage.extend(_lineage_from_entry(entry, snapshot_by_id.get(record.base_snapshot_id)))

    return ReorganisationTrail(run_id=run_id, entries=entries, lineage=lineage)
