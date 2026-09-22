"""A readable timeline of code generation and change.

The raw material already exists, append-only: the audit log (`gaf.store.audit`), the
content-addressed snapshots (`gaf.store.snapshot`) and the checkpoints table
(`gaf.store.blackboard.Blackboard.read_checkpoints`). What is missing is a reading of
it a person can follow response by response and batch by batch, without opening the
database — that is what this module builds.

`build_timeline` reads one run's own store: every response coded, the codes it created
or added evidence to, the snapshot the coders read for it, and — from
``operation_applied`` events, once a checkpoint has run — the eventual fate of every
code that ever existed, including the ones later removed. A removed code still gets a
biography; that is the point of a timeline (see `CodeBiography`).

`timeline_from_assignments` builds the same shape of picture — steps, batches, the
codes born — from a bare, ordered list of `gaf.models.Assignment` rows, so a human
coding exported from a spreadsheet is read with the same tool as the machine's run. It
carries no snapshot ids (a spreadsheet names none) and no fates (a flat coding has no
operation log to read one from). A flat `Assignment` row cannot distinguish "this code
is being applied for the first time" from "evidence is being added to a code that
already exists" the way the fast loop's audit trail can; this module reads a code
name's *first* appearance in the given order as its birth and every later appearance as
evidence merged into it. That is a reading of the data, not a fact it states, so it is
documented here rather than left implicit.

`timeline_svg` draws cumulative codes as a step line over responses coded, new codes
per batch as bars, and vertical markers for the snapshots and checkpoints a `Timeline`
carries, plus whatever markers the caller supplies. It is hand-rendered SVG in the
manner of `gaf.analysis.hca`, and reuses that module's `_svg_open` and `_num` helpers
rather than re-deriving the boilerplate they already hold.

No wall-clock time appears anywhere in this module's output. `created_at` orders
nothing here; `event_id` — the audit log's own insertion order — is what "the log's
total order" means throughout (ADR-0007, ADR-0017).

Validation principle: **transparency** — how the codebook came to look the way it
does is a story a methods reviewer can follow, not a fact they have to take on trust.
"""

from __future__ import annotations

import html
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from itertools import pairwise
from typing import Any

from gaf.analysis.hca import _num, _svg_open
from gaf.models import Assignment, Codebook, family_of
from gaf.store.audit import AuditEvent
from gaf.store.blackboard import Blackboard
from gaf.store.snapshot import Snapshot

__all__ = [
    "RENAME_MATCHED_BY",
    "SNAPSHOT_MATCHING",
    "BatchSummary",
    "BirthEvent",
    "CheckpointMarker",
    "CodeBiography",
    "EvidencePoint",
    "HandoverEvaluation",
    "RenamedCode",
    "SnapshotDiff",
    "Timeline",
    "TimelineStep",
    "build_timeline",
    "timeline_from_assignments",
    "timeline_svg",
]

#: Nominal width of one character in the ``lbl`` class, used only to decide whether a
#: marker label fits before the right edge. An estimate on purpose: the alternative is
#: measuring text, which needs a font engine this project does not have and would make
#: the SVG depend on one.
_CHAR_WIDTH = 5.4

#: Vertical distance between two marker labels stacked at the same x.
_LABEL_ROW = 11.0

#: Extra marker styles this module needs beyond what `gaf.analysis.hca._SVG_CSS`
#: already defines (axis, grid, bar, curve, tick, lbl, ttl are all reused from there).
_MARKER_CSS = (
    ".snapmark{stroke:#a0aec0;stroke-width:1;stroke-dasharray:2 3}"
    ".ckptmark{stroke:#9b2c2c;stroke-width:1.4;stroke-dasharray:5 3}"
    ".usermark{stroke:#6b46c1;stroke-width:1.2;stroke-dasharray:4 2}"
)


# --------------------------------------------------------------------------- #
# 1. Steps and batches
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class TimelineStep:
    """One response coded: what the codebook gained, against which context.

    `codes_created` are candidate names admitted as brand-new codes at this response;
    `codes_merged` are existing codes this response added verified evidence to. Both
    are read straight from the router's own decision (`code_created` / `code_merged`
    audit events, or — for `timeline_from_assignments` — a name's first-versus-later
    appearance in the given order).
    """

    response_id: int
    batch: int
    snapshot_id: str | None
    codes_created: list[str] = field(default_factory=list)
    codes_merged: list[str] = field(default_factory=list)
    n_assignments: int = 0
    duplicate_of: int | None = None

    def to_json(self) -> dict[str, Any]:
        return {
            "response_id": self.response_id,
            "batch": self.batch,
            "snapshot_id": self.snapshot_id,
            "codes_created": list(self.codes_created),
            "codes_merged": list(self.codes_merged),
            "n_assignments": self.n_assignments,
            "duplicate_of": self.duplicate_of,
        }


@dataclass(frozen=True, slots=True)
class HandoverEvaluation:
    """The fast loop's own per-batch read of whether the slow loop is due.

    Sourced from the optional ``checkpoint_evaluated`` event (batch number, verdict
    ``"continue"`` or ``"checkpoint_due"``, reason, fired rules). Treated as optional
    input throughout this module: a `BatchSummary` simply carries `None` when the audit
    log this run wrote predates that event.
    """

    batch: int
    verdict: str
    reason: str
    fired_rules: list[str] = field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        return {
            "batch": self.batch,
            "verdict": self.verdict,
            "reason": self.reason,
            "fired_rules": list(self.fired_rules),
        }


@dataclass(frozen=True, slots=True)
class BatchSummary:
    """One coding batch: the responses it covered and what the codebook gained.

    A "batch" here is the fast loop's own unit — every response prepared against the
    same snapshot id belongs to the same batch — which reads the same whichever
    `RunConfig.snapshot_policy` a run used, since it is defined by what the coders
    actually read rather than by a batch-size arithmetic this module would have to
    re-derive. `batch` is numbered from **1**, matching
    `gaf.pipeline.decision_matrix.HandoverEvaluation.batch` and `gaf.checks.growth.
    GrowthCurve`, so a `checkpoint_evaluated` event's own batch number joins directly
    onto the batch of the same number here.
    """

    batch: int
    snapshot_id: str | None
    responses: list[int]
    new_codes: list[str]
    merges: int
    cumulative_codes: int
    judge_consultations: int
    handover: HandoverEvaluation | None = None

    @property
    def n_responses(self) -> int:
        return len(self.responses)

    @property
    def n_new_codes(self) -> int:
        return len(self.new_codes)

    def to_json(self) -> dict[str, Any]:
        return {
            "batch": self.batch,
            "snapshot_id": self.snapshot_id,
            "responses": list(self.responses),
            "n_responses": self.n_responses,
            "new_codes": list(self.new_codes),
            "n_new_codes": self.n_new_codes,
            "merges": self.merges,
            "cumulative_codes": self.cumulative_codes,
            "judge_consultations": self.judge_consultations,
            "handover": self.handover.to_json() if self.handover is not None else None,
        }


# --------------------------------------------------------------------------- #
# 2. Snapshot diffs
# --------------------------------------------------------------------------- #


#: How two snapshots' codes were put beside each other. Stated in the artefact so a
#: reader can tell a *recorded* rename from an inferred one; nothing here infers one,
#: and saying so is the point (R1 Minor).
SNAPSHOT_MATCHING = "code id, then this run's own recorded rename operations"

#: What a `RenamedCode` row rests on. One value today, named rather than implied.
RENAME_MATCHED_BY = "recorded rename operation"


@dataclass(frozen=True, slots=True)
class RenamedCode:
    """One code identified as the same thread of meaning under two names.

    `matched_by` says what the identification rests on. It is never a guess: only a
    ``rename`` operation this run actually applied can say that a removed id became an
    added one, and a removed id with no such record is reported as removed.
    """

    from_name: str
    to_name: str
    matched_by: str = RENAME_MATCHED_BY

    def to_json(self) -> dict[str, Any]:
        return {"from": self.from_name, "to": self.to_name, "matched_by": self.matched_by}


@dataclass(frozen=True, slots=True)
class SnapshotDiff:
    """What changed between two consecutive snapshots, and why the later one froze.

    Matched by code id first: a code with the same id in both snapshots is unchanged
    (a rename always mints a new id from the new name, `gaf.ids.code_id`, so an
    unchanged id is genuinely an unchanged code, never a coincidence). What is left
    over is matched against this run's own recorded ``rename`` operations — the only
    source that can say "this removed id became that added id", since two arbitrary
    codebooks carry no such link on their own; a removed id with no recorded rename,
    or an added id no rename produced, is reported as removed or added rather than
    guessed at.
    """

    from_snapshot: str
    to_snapshot: str
    reason: str
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    renamed: list[RenamedCode] = field(default_factory=list)
    #: How the two snapshots' codes were matched. Always `SNAPSHOT_MATCHING`; carried
    #: on the row rather than left to the docstring so the artefact itself says it.
    matching: str = SNAPSHOT_MATCHING

    def to_json(self) -> dict[str, Any]:
        return {
            "from_snapshot": self.from_snapshot,
            "to_snapshot": self.to_snapshot,
            "reason": self.reason,
            "matching": self.matching,
            "added": list(self.added),
            "removed": list(self.removed),
            "renamed": [r.to_json() for r in self.renamed],
        }


# --------------------------------------------------------------------------- #
# 3. Code biographies
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class EvidencePoint:
    """One (context, count) sample of a code's verified-evidence growth."""

    kind: str  # "response" | "checkpoint"
    ref: str
    n_evidence: int

    def to_json(self) -> dict[str, Any]:
        return {"kind": self.kind, "ref": self.ref, "n_evidence": self.n_evidence}


@dataclass(frozen=True, slots=True)
class BirthEvent:
    """How and where one code first entered the codebook.

    ``origin`` is ``"coded"`` for a candidate a coder proposed and the router
    admitted, ``"created"`` for a code a human invented at the slow-loop gate,
    ``"split"`` or ``"renamed"`` for a code born out of restructuring an earlier one
    (named in `predecessor`). Only ``"coded"`` births carry a `response_id`/`batch`;
    the other three are born at a checkpoint, not a response.
    """

    origin: str
    response_id: int | None = None
    batch: int | None = None
    checkpoint_id: str | None = None
    snapshot_id: str | None = None
    coders: list[str] = field(default_factory=list)
    predecessor: str | None = None

    def to_json(self) -> dict[str, Any]:
        return {
            "origin": self.origin,
            "response_id": self.response_id,
            "batch": self.batch,
            "checkpoint_id": self.checkpoint_id,
            "snapshot_id": self.snapshot_id,
            "coders": list(self.coders),
            "predecessor": self.predecessor,
        }


@dataclass(frozen=True, slots=True)
class CodeBiography:
    """Everything the log knows about one code, from birth to its eventual fate.

    Every code id that ever appeared in this run's codebook gets an entry, whether or
    not it is still there: a code the slow loop merged away, split apart or renamed is
    exactly the case a timeline exists to keep visible.

    `fate_kind` is ``"alive"`` for a code the final snapshot still carries (whether or
    not it was ever re-parented — `reparenting` carries that history regardless), or
    one of ``"merged"``, ``"split"``, ``"renamed"`` for one that is not. `successors`
    names what it became: one name for a merge or a rename, two or more for a split.

    ``"narrowed"`` is the fifth value and the one that is *not* a removal: a split
    whose heir keeps the target's name leaves that code alive with a smaller share of
    the evidence, so it keeps its own birth and its successors are the codes that were
    split off it, never itself.
    """

    code_id: str
    name: str
    family: str
    born: BirthEvent
    evidence_over_time: list[EvidencePoint]
    fate_kind: str
    fate: str
    successors: list[str] = field(default_factory=list)
    reparenting: list[str] = field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        return {
            "code_id": self.code_id,
            "name": self.name,
            "family": self.family,
            "born": self.born.to_json(),
            "evidence_over_time": [p.to_json() for p in self.evidence_over_time],
            "fate_kind": self.fate_kind,
            "fate": self.fate,
            "successors": list(self.successors),
            "reparenting": list(self.reparenting),
        }


# --------------------------------------------------------------------------- #
# 4. Checkpoint markers (for timeline_svg; the trail is `gaf.report.trail`'s job)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class CheckpointMarker:
    """Just enough about one checkpoint to place and label it on the timeline SVG."""

    at_response_count: int
    checkpoint_id: str
    status: str

    def to_json(self) -> dict[str, Any]:
        return {
            "at_response_count": self.at_response_count,
            "checkpoint_id": self.checkpoint_id,
            "status": self.status,
        }


# --------------------------------------------------------------------------- #
# 5. The timeline
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class Timeline:
    """Steps, batches, snapshot diffs and code biographies for one run — or one
    bare, ordered coding.

    `run_id` is `None` for a timeline built from assignment rows alone.
    `snapshot_diffs`, `biographies` and `checkpoints` are always empty in that case:
    a flat coding names no snapshots and carries no operation log to read a fate from.
    """

    run_id: str | None
    steps: list[TimelineStep]
    batches: list[BatchSummary]
    snapshot_diffs: list[SnapshotDiff] = field(default_factory=list)
    biographies: dict[str, CodeBiography] = field(default_factory=dict)
    checkpoints: list[CheckpointMarker] = field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "steps": [s.to_json() for s in self.steps],
            "batches": [b.to_json() for b in self.batches],
            "snapshot_diffs": [d.to_json() for d in self.snapshot_diffs],
            "biographies": {
                code_id: bio.to_json() for code_id, bio in sorted(self.biographies.items())
            },
            "checkpoints": [c.to_json() for c in self.checkpoints],
        }

    def to_json_str(self) -> str:
        return json.dumps(self.to_json(), sort_keys=True, ensure_ascii=False, indent=2)

    def to_markdown(self) -> str:
        """A readable account: batches first, then what the snapshots and the codes
        themselves show, matching the order a reader would ask about them in."""
        lines = ["## Timeline of code generation and change", ""]
        if self.run_id is not None:
            lines.append(
                f"Run `{self.run_id}` — {len(self.steps)} response(s) coded over "
                f"{len(self.batches)} batch(es)."
            )
        else:
            lines.append(
                f"{len(self.steps)} response(s) over {len(self.batches)} batch(es), "
                "from an ordered coding export (no snapshots, no fates)."
            )
        lines.append("")
        lines.append("### Batches")
        lines.append("")
        lines.append("| batch | responses | new codes | merges | cumulative codes | judge calls |")
        lines.append("|---:|---:|---:|---:|---:|---:|")
        for batch in self.batches:
            lines.append(
                f"| {batch.batch} | {batch.n_responses} | {batch.n_new_codes} | "
                f"{batch.merges} | {batch.cumulative_codes} | {batch.judge_consultations} |"
            )
        # Below the table, never inside it: a ``>`` blockquote in a table body ends the
        # table in every CommonMark renderer, so every row after the first handover was
        # rendered as raw pipes (R1 Minor).
        handovers = [batch for batch in self.batches if batch.handover is not None]
        if handovers:
            lines.append("")
            lines.append("Handover evaluated at every batch boundary:")
            lines.append("")
            for batch in handovers:
                handover = batch.handover
                assert handover is not None  # for the type checker; filtered above
                lines.append(
                    f"- batch {batch.batch} handover: **{handover.verdict}** — "
                    f"{handover.reason}"
                )
        if self.snapshot_diffs:
            lines.append("")
            lines.append("### Snapshot diffs")
            lines.append("")
            lines.append(
                f"Codes are matched by {SNAPSHOT_MATCHING}; a rename is reported only "
                "where an operation recorded it, and never inferred. A code that only "
                "moved has no line at all, because re-parenting keeps a code's id and "
                "so changes nothing this diff can see."
            )
            lines.append("")
            for diff in self.snapshot_diffs:
                lines.append(
                    f"- `{diff.from_snapshot}` -> `{diff.to_snapshot}` ({diff.reason}): "
                    f"{len(diff.added)} added, {len(diff.removed)} removed, "
                    f"{len(diff.renamed)} renamed"
                )
                for rename in diff.renamed:
                    lines.append(
                        f"  - renamed ({rename.matched_by}): "
                        f"{rename.from_name!r} -> {rename.to_name!r}"
                    )
                for name in diff.added:
                    lines.append(f"  - added: {name!r}")
                for name in diff.removed:
                    lines.append(f"  - removed: {name!r}")
        if self.biographies:
            lines.append("")
            lines.append("### Code biographies")
            lines.append("")
            lines.append("| code | family | born | fate |")
            lines.append("|---|---|---|---|")
            ordered = sorted(self.biographies.values(), key=lambda bio: (bio.name, bio.code_id))
            for bio in ordered:
                lines.append(
                    f"| {bio.name} | {bio.family} | {_describe_birth(bio.born)} | {bio.fate} |"
                )
                for note in bio.reparenting:
                    lines.append(f"| | | | {note} |")
        return "\n".join(lines) + "\n"


def _describe_birth(born: BirthEvent) -> str:
    if born.origin == "coded":
        who = ", ".join(born.coders) if born.coders else "an unrecorded coder"
        return f"response {born.response_id} (batch {born.batch}), proposed by {who}"
    if born.predecessor is not None:
        return f"{born.origin} from {born.predecessor!r} at checkpoint {born.checkpoint_id}"
    return f"{born.origin} at checkpoint {born.checkpoint_id}"


# --------------------------------------------------------------------------- #
# 6. Building a Timeline from a run's own store
# --------------------------------------------------------------------------- #


def _batches(events: Sequence[AuditEvent]) -> tuple[dict[int, int], dict[int, list[int]]]:
    """``(response id -> batch, batch -> its responses in order)``.

    **From the handover evaluations where there are any.** The fast loop writes one
    ``checkpoint_evaluated`` event at every batch boundary, carrying that boundary's
    own 1-based batch number, so the batches are stated in the log rather than
    inferred: every ``response_prepared`` since the previous boundary belongs to the
    batch the next evaluation names.

    Falling back to the snapshot the coders read — which is what this did before —
    is only correct under ``snapshot_policy="per_batch"``. Under ``per_checkpoint``
    every response shares the seed snapshot, so a 14-response run over three batches
    read as one batch of 14 carrying only batch 1's handover, and the other two
    evaluations were discarded (R1, brief Important). The fallback is kept for an
    audit log written before ``checkpoint_evaluated`` existed.

    Numbered from 1 either way, matching
    `gaf.pipeline.decision_matrix.HandoverEvaluation.batch` and
    `gaf.checks.growth.GrowthCurve`, so a `checkpoint_evaluated` event's own batch
    number joins on with no off-by-one translation in either direction.
    """
    batch_of_response: dict[int, int] = {}
    responses_by_batch: dict[int, list[int]] = {}

    pending: list[int] = []
    saw_evaluation = False
    for event in events:
        if event.event == "response_prepared":
            pending.append(int(event.subject))
        elif event.event == "checkpoint_evaluated":
            raw = event.payload.get("batch")
            if raw is None:
                continue
            saw_evaluation = True
            batch = int(raw)
            responses_by_batch.setdefault(batch, []).extend(pending)
            for response_id in pending:
                batch_of_response[response_id] = batch
            pending = []
    if saw_evaluation:
        if pending:
            # Responses after the last evaluation: a halted run stops mid-stream, and
            # an audit log can always end early. They are a batch of their own rather
            # than silently absent from every batch.
            trailing = max(responses_by_batch) + 1
            responses_by_batch[trailing] = list(pending)
            for response_id in pending:
                batch_of_response[response_id] = trailing
        return batch_of_response, responses_by_batch

    batch_of_snapshot: dict[str, int] = {}
    for event in events:
        if event.event != "response_prepared":
            continue
        snap = event.snapshot_id or ""
        batch = batch_of_snapshot.setdefault(snap, len(batch_of_snapshot) + 1)
        responses_by_batch.setdefault(batch, []).append(int(event.subject))
        batch_of_response[int(event.subject)] = batch
    return batch_of_response, responses_by_batch


def _coders_index(events: Sequence[AuditEvent]) -> dict[tuple[int, str], list[str]]:
    """(response id, accepted candidate name) -> the coder(s) who proposed it.

    Read from `candidates_accepted` rather than `coding_proposed`: it is the router's
    own accepted list that names the coder(s) behind the candidate that actually
    reached integration, agreed or not.
    """
    index: dict[tuple[int, str], list[str]] = {}
    for event in events:
        if event.event != "candidates_accepted":
            continue
        response_id = int(event.subject)
        for item in event.payload.get("accepted", []):
            name = str(item.get("name", ""))
            index[(response_id, name)] = [str(c) for c in item.get("coders", [])]
    return index


def _created_and_merged_by_response(
    events: Sequence[AuditEvent],
) -> tuple[dict[int, list[str]], dict[int, list[str]]]:
    created: dict[int, list[str]] = {}
    merged: dict[int, list[str]] = {}
    for event in events:
        if event.event == "code_created":
            rid = int(event.payload["response_id"])
            created.setdefault(rid, []).append(str(event.subject))
        elif event.event == "code_merged":
            rid = int(event.payload["response_id"])
            merged.setdefault(rid, []).append(str(event.subject))
    return created, merged


def _n_assignments_by_response(events: Sequence[AuditEvent]) -> dict[int, int]:
    counts: dict[int, int] = {}
    for event in events:
        if event.event != "assignments_written":
            continue
        counts[int(event.subject)] = int(event.payload.get("n_assignments", 0))
    return counts


def _dedup_by_response(events: Sequence[AuditEvent]) -> dict[int, int | None]:
    out: dict[int, int | None] = {}
    for event in events:
        if event.event != "response_prepared":
            continue
        rid = int(event.subject)
        duplicate_of = event.payload.get("dedup", {}).get("duplicate_of")
        out[rid] = int(duplicate_of) if duplicate_of is not None else None
    return out


def _judge_calls_by_batch(
    events: Sequence[AuditEvent], batch_of_response: Mapping[int, int]
) -> dict[int, int]:
    """batch -> how many times the judge was consulted while coding it.

    A ``judge_consulted`` event names a candidate or a pair, never a response, so it
    is attributed to the response being coded when it fired -- the last
    ``response_prepared`` before it in the log's own order. Keying on the snapshot
    instead credited a whole ``per_checkpoint`` run's judge calls to one batch.
    """
    counts: dict[int, int] = {}
    current: int | None = None
    for event in events:
        if event.event == "response_prepared":
            current = batch_of_response.get(int(event.subject))
        elif event.event == "judge_consulted" and current is not None:
            counts[current] = counts.get(current, 0) + 1
    return counts


def _handovers_by_batch(events: Sequence[AuditEvent]) -> dict[int, HandoverEvaluation]:
    """Optional per-batch ``checkpoint_evaluated`` events, keyed by their own batch
    number. Absent entirely from an audit log this event predates.

    `gaf.pipeline.decision_matrix.HandoverEvaluation.to_json()` is the actual, richer
    payload this event carries (`fired`/`held` trigger names, the growth curve, the
    near-duplicate count); this module reads only the four fields the brief asks a
    timeline to show — batch, verdict, reason, and which rules fired — under the key
    that payload actually uses (`"fired"`), falling back to `"fired_rules"` so a
    differently-named producer of this same event is read just as well.
    """
    out: dict[int, HandoverEvaluation] = {}
    for event in events:
        if event.event != "checkpoint_evaluated":
            continue
        payload = event.payload
        batch = payload.get("batch")
        if batch is None:
            continue
        fired = payload.get("fired", payload.get("fired_rules", []))
        out[int(batch)] = HandoverEvaluation(
            batch=int(batch),
            verdict=str(payload.get("verdict", "")),
            reason=str(payload.get("reason", "")),
            fired_rules=[str(rule) for rule in fired],
        )
    return out


def _checkpoint_markers(events: Sequence[AuditEvent]) -> list[CheckpointMarker]:
    """One marker per checkpoint this run's audit log recorded, in the order they ran.

    `at_response_count` is on `checkpoint_started`, not on `checkpoint_decided`, and
    `checkpoint_id` is minted only once `checkpoint_proposed` fires; this pairs the
    three events of one checkpoint by their known order rather than re-deriving a
    checkpoint id that is already stored.
    """
    markers: list[CheckpointMarker] = []
    pending_at: int | None = None
    pending_id: str | None = None
    for event in events:
        if event.event == "checkpoint_started":
            pending_at = int(event.payload.get("at_response_count", 0))
        elif event.event == "checkpoint_proposed":
            pending_id = str(event.payload.get("checkpoint_id", ""))
        elif event.event == "checkpoint_decided":
            markers.append(
                CheckpointMarker(
                    at_response_count=pending_at if pending_at is not None else 0,
                    checkpoint_id=pending_id or str(event.payload.get("checkpoint_id", "")),
                    status=str(event.payload.get("status", "")),
                )
            )
            pending_at = None
            pending_id = None
    return markers


def _renamed_id_map(events: Sequence[AuditEvent]) -> dict[str, str]:
    """old code id -> new code id, from every `rename` operation this run applied."""
    mapping: dict[str, str] = {}
    for event in events:
        if event.event != "operation_applied":
            continue
        effect = event.payload.get("effect") or {}
        if effect.get("type") != "rename":
            continue
        for old_id, new_id in (effect.get("renamed") or {}).items():
            mapping[str(old_id)] = str(new_id)
    return mapping


def _run_snapshots(board: Blackboard, run_id: str, events: Sequence[AuditEvent]) -> list[Snapshot]:
    """This run's snapshots, in the order it froze them.

    Snapshots are content-addressed, and `Blackboard.freeze_codebook` keeps the *first*
    writer's ``run_id`` when a later run freezes an identical codebook. A second run
    into a shared store therefore gets nothing at all from
    ``read_snapshots(run_id=...)``, and the whole "Snapshot diffs" section vanished
    without a word (R1, brief Important). This run's own ``snapshot_frozen`` events
    say which snapshots it froze and in what order, whoever wrote the row first.

    Every snapshot id the run *touched*, in first-touch order, rather than only the
    ones it froze: a warm-started run codes against, and a checkpoint proposes from, a
    snapshot some earlier run wrote, and that snapshot is part of this run's story.
    First touch is freeze order for the ones this run froze, because nothing can read
    a snapshot before it exists.

    Falls back to ``read_snapshots(run_id=...)`` when the log names no snapshot at all.
    """
    ordered: list[Snapshot] = []
    seen: set[str] = set()
    by_id = {snapshot.snapshot_id: snapshot for snapshot in board.read_snapshots()}
    for event in events:
        snapshot_id = str(event.snapshot_id or "")
        snapshot = by_id.get(snapshot_id)
        if snapshot is None or snapshot_id in seen:
            continue
        seen.add(snapshot_id)
        ordered.append(snapshot)
    return ordered or board.read_snapshots(run_id=run_id)


def _snapshot_diffs(
    snapshots: Sequence[Snapshot], events: Sequence[AuditEvent]
) -> list[SnapshotDiff]:
    renamed_map = _renamed_id_map(events)
    diffs: list[SnapshotDiff] = []
    for prev, curr in pairwise(snapshots):
        prev_codes = prev.codebook.codes
        curr_codes = curr.codebook.codes
        removed_ids = set(prev_codes) - set(curr_codes)
        added_ids = set(curr_codes) - set(prev_codes)

        renamed: list[RenamedCode] = []
        matched_old: set[str] = set()
        matched_new: set[str] = set()
        for old_id in sorted(removed_ids):
            new_id = renamed_map.get(old_id)
            if new_id is not None and new_id in added_ids:
                renamed.append(RenamedCode(prev_codes[old_id].name, curr_codes[new_id].name))
                matched_old.add(old_id)
                matched_new.add(new_id)

        removed = sorted(prev_codes[i].name for i in removed_ids - matched_old)
        added = sorted(curr_codes[i].name for i in added_ids - matched_new)
        diffs.append(
            SnapshotDiff(
                from_snapshot=prev.snapshot_id,
                to_snapshot=curr.snapshot_id,
                reason=curr.reason,
                added=added,
                removed=removed,
                renamed=renamed,
            )
        )
    return diffs


def _resolve_name(
    code_id: str,
    *,
    effect_names: Mapping[str, str],
    running_names: Mapping[str, str],
    base_codebook: Codebook | None,
    result_codebook: Codebook | None,
) -> str:
    """Best available name for a code id touched by one operation.

    In order: the operation's own `effect.names` (authoritative for the ids it
    mentions), this pass's running record of names seen so far, the checkpoint's base
    snapshot, then its result snapshot. Falls back to the id itself only if none of
    those know it, which should not happen for an id this run actually touched.
    """
    if code_id in effect_names:
        return effect_names[code_id]
    if code_id in running_names:
        return running_names[code_id]
    if base_codebook is not None and code_id in base_codebook.codes:
        return str(base_codebook.codes[code_id].name)
    if result_codebook is not None and code_id in result_codebook.codes:
        return str(result_codebook.codes[code_id].name)
    return code_id


def _evidence_count(codebook: Codebook | None, code_id: str) -> int:
    if codebook is not None and code_id in codebook.codes:
        return len(codebook.codes[code_id].evidence)
    return 0


def _apply_operation_to_biographies(
    event: AuditEvent,
    *,
    current_checkpoint_id: str | None,
    base_codebook: Codebook | None,
    result_codebook: Codebook | None,
    names: dict[str, str],
    born: dict[str, BirthEvent],
    evidence: dict[str, list[EvidencePoint]],
    fate_kind: dict[str, str],
    fate: dict[str, str],
    successors: dict[str, list[str]],
    reparenting: dict[str, list[str]],
) -> None:
    """Fold one ``operation_applied`` event into the running biography state.

    A free function taking every piece of state explicitly, rather than a closure
    defined inside `_biographies`'s own event loop: a closure there would capture
    `base_codebook`/`result_codebook`, which are reassigned on every iteration, and a
    linter (correctly) refuses to trust that such a closure is only ever called before
    the next reassignment — which it is, but a rule that has to reason about call order
    inside a loop body is exactly the kind of rule not worth arguing with.
    """
    payload = event.payload
    effect = payload.get("effect") or {}
    etype = str(effect.get("type", ""))
    effect_names = {str(k): str(v) for k, v in (effect.get("names") or {}).items()}

    def resolve(code_id: str) -> str:
        return _resolve_name(
            code_id,
            effect_names=effect_names,
            running_names=names,
            base_codebook=base_codebook,
            result_codebook=result_codebook,
        )

    if etype == "merge":
        changed = [str(c) for c in effect.get("changed", [])]
        target_id = changed[0] if changed else ""
        target_name = resolve(target_id)
        for removed_id in [str(r) for r in effect.get("removed", [])]:
            fate_kind[removed_id] = "merged"
            fate[removed_id] = f"merged into {target_name!r}"
            successors[removed_id] = [target_name]
        if target_id:
            evidence.setdefault(target_id, []).append(
                EvidencePoint(
                    kind="checkpoint",
                    ref=current_checkpoint_id or "",
                    n_evidence=_evidence_count(result_codebook, target_id),
                )
            )
    elif etype == "split":
        removed = [str(r) for r in effect.get("removed", [])]
        target_id = removed[0] if removed else ""
        target_name = resolve(target_id)
        created_ids = [str(c) for c in effect.get("created", [])]
        created_names = [resolve(cid) for cid in created_ids]
        # A code id is the content hash of its name, and `_apply_split` explicitly
        # permits an heir named after its target, so the "removed" id and one of the
        # "created" ids can be the same id. That code was narrowed, not split away: it
        # is alive in the final codebook, and overwriting its birth erased the
        # response, the batch and the coders that proposed it (R1 C6).
        survivors = set(created_ids) & set(removed)
        if target_id:
            others = [
                name for cid, name in zip(created_ids, created_names, strict=True)
                if cid != target_id
            ]
            if target_id in survivors:
                fate_kind[target_id] = "narrowed"
                fate[target_id] = (
                    "narrowed; " + ", ".join(repr(name) for name in others) + " split off"
                )
                successors[target_id] = others
            else:
                fate_kind[target_id] = "split"
                fate[target_id] = f"split into {', '.join(created_names)}"
                successors[target_id] = created_names
        for code_id, name in zip(created_ids, created_names, strict=True):
            names[code_id] = name
            if code_id in survivors:
                continue
            born[code_id] = BirthEvent(
                origin="split",
                checkpoint_id=current_checkpoint_id,
                snapshot_id=event.snapshot_id,
                predecessor=target_name,
            )
            evidence.setdefault(code_id, []).append(
                EvidencePoint(
                    kind="checkpoint",
                    ref=current_checkpoint_id or "",
                    n_evidence=_evidence_count(result_codebook, code_id),
                )
            )
    elif etype == "rename":
        for raw_old_id, raw_new_id in (effect.get("renamed") or {}).items():
            old_id, new_id = str(raw_old_id), str(raw_new_id)
            old_name = resolve(old_id)
            new_name = resolve(new_id)
            fate_kind[old_id] = "renamed"
            fate[old_id] = f"renamed to {new_name!r}"
            successors[old_id] = [new_name]
            names[new_id] = new_name
            born[new_id] = BirthEvent(
                origin="renamed",
                checkpoint_id=current_checkpoint_id,
                snapshot_id=event.snapshot_id,
                predecessor=old_name,
            )
            evidence.setdefault(new_id, []).append(
                EvidencePoint(
                    kind="checkpoint",
                    ref=current_checkpoint_id or "",
                    n_evidence=_evidence_count(result_codebook, new_id),
                )
            )
    elif etype == "reparent":
        changed = [str(c) for c in effect.get("changed", [])]
        target_id = changed[0] if changed else ""
        summary = str(payload.get("summary", ""))
        if target_id and summary:
            reparenting.setdefault(target_id, []).append(summary)
    elif etype == "create":
        for code_id in [str(c) for c in effect.get("created", [])]:
            name = resolve(code_id)
            names[code_id] = name
            born[code_id] = BirthEvent(
                origin="created",
                checkpoint_id=current_checkpoint_id,
                snapshot_id=event.snapshot_id,
            )
            evidence.setdefault(code_id, []).append(
                EvidencePoint(
                    kind="checkpoint",
                    ref=current_checkpoint_id or "",
                    n_evidence=_evidence_count(result_codebook, code_id),
                )
            )


def _biographies(
    events: Sequence[AuditEvent],
    snapshots: Sequence[Snapshot],
    coders_index: Mapping[tuple[int, str], list[str]],
    batch_of_response: Mapping[int, int],
) -> dict[str, CodeBiography]:
    """Every code that ever existed in this run, born through to its eventual fate.

    Fast-loop births (`code_created`) and evidence growth (`code_created` /
    `code_merged`) are read directly; slow-loop births, fates and re-parenting notes
    are read from `operation_applied` events, correlated to the checkpoint they belong
    to by the `checkpoint_proposed` / `checkpoint_decided` events bracketing them.
    """
    names: dict[str, str] = {}
    born: dict[str, BirthEvent] = {}
    evidence: dict[str, list[EvidencePoint]] = {}
    fate_kind: dict[str, str] = {}
    fate: dict[str, str] = {}
    successors: dict[str, list[str]] = {}
    reparenting: dict[str, list[str]] = {}

    snapshot_by_id = {snapshot.snapshot_id: snapshot for snapshot in snapshots}
    current_checkpoint_id: str | None = None
    current_base_snapshot: str | None = None

    for event in events:
        if event.event == "code_created":
            payload = event.payload
            code_id = str(payload["code_id"])
            response_id = int(payload["response_id"])
            names[code_id] = str(event.subject)
            born[code_id] = BirthEvent(
                origin="coded",
                response_id=response_id,
                batch=batch_of_response.get(response_id),
                snapshot_id=event.snapshot_id,
                coders=list(
                    coders_index.get((response_id, str(payload.get("candidate_name", ""))), [])
                ),
            )
            evidence.setdefault(code_id, []).append(
                EvidencePoint(
                    kind="response", ref=str(response_id), n_evidence=int(payload.get("n_evidence", 0))
                )
            )
        elif event.event == "code_merged":
            payload = event.payload
            code_id = str(payload["code_id"])
            response_id = int(payload["response_id"])
            evidence.setdefault(code_id, []).append(
                EvidencePoint(
                    kind="response", ref=str(response_id), n_evidence=int(payload.get("n_evidence", 0))
                )
            )
        elif event.event == "checkpoint_proposed":
            current_checkpoint_id = str(event.payload.get("checkpoint_id", ""))
            current_base_snapshot = event.snapshot_id
        elif event.event == "checkpoint_decided":
            current_checkpoint_id = None
            current_base_snapshot = None
        elif event.event == "operation_applied":
            base_codebook = (
                snapshot_by_id[current_base_snapshot].codebook
                if current_base_snapshot in snapshot_by_id
                else None
            )
            result_codebook = (
                snapshot_by_id[event.snapshot_id].codebook
                if event.snapshot_id in snapshot_by_id
                else None
            )
            _apply_operation_to_biographies(
                event,
                current_checkpoint_id=current_checkpoint_id,
                base_codebook=base_codebook,
                result_codebook=result_codebook,
                names=names,
                born=born,
                evidence=evidence,
                fate_kind=fate_kind,
                fate=fate,
                successors=successors,
                reparenting=reparenting,
            )

    # A code touched by a fate (merged away, split, renamed) or a re-parenting note may
    # never have been "born" within *this* run's own audit log at all — it can be a code
    # a warm-started run inherited from an earlier one (`run_fast_loop`'s own docstring:
    # "the codebook a previous run ... left behind"), present in the base snapshot before
    # this run's first event. It still existed and still had something happen to it, so
    # it still gets a biography, marked as pre-existing rather than silently dropped.
    for code_id in {*fate_kind, *reparenting}:
        if code_id not in born:
            earliest_snapshot = snapshots[0].snapshot_id if snapshots else None
            born[code_id] = BirthEvent(origin="pre_existing", snapshot_id=earliest_snapshot)
            if code_id not in names:
                names[code_id] = next(
                    (
                        snapshot.codebook.codes[code_id].name
                        for snapshot in snapshots
                        if code_id in snapshot.codebook.codes
                    ),
                    code_id,
                )

    biographies: dict[str, CodeBiography] = {}
    for code_id, birth in born.items():
        name = names.get(code_id, code_id)
        biographies[code_id] = CodeBiography(
            code_id=code_id,
            name=name,
            family=family_of(name),
            born=birth,
            evidence_over_time=list(evidence.get(code_id, [])),
            fate_kind=fate_kind.get(code_id, "alive"),
            fate=fate.get(code_id, "alive"),
            successors=list(successors.get(code_id, [])),
            reparenting=list(reparenting.get(code_id, [])),
        )
    return biographies


def build_timeline(board: Blackboard, run_id: str) -> Timeline:
    """Read one run's own store into a `Timeline`.

    Reads the audit log in full once (`board.audit(run_id).events()`, the log's own
    total order) and this run's snapshots in freeze order
    (`board.read_snapshots(run_id=run_id)`); everything else is derived from those two
    reads, never from a second query of the loop's internals.
    """
    events = board.audit(run_id).events()
    snapshots = _run_snapshots(board, run_id, events)

    batch_of_response, responses_by_batch = _batches(events)
    snapshot_of_response: dict[int, str | None] = {}
    coders_index = _coders_index(events)
    created_by_response, merged_by_response = _created_and_merged_by_response(events)
    n_assignments_by_response = _n_assignments_by_response(events)
    dedup_by_response = _dedup_by_response(events)
    judge_calls_by_batch = _judge_calls_by_batch(events, batch_of_response)
    handovers_by_batch = _handovers_by_batch(events)

    steps: list[TimelineStep] = []
    for event in events:
        if event.event != "response_prepared":
            continue
        response_id = int(event.subject)
        snapshot_of_response[response_id] = event.snapshot_id
        steps.append(
            TimelineStep(
                response_id=response_id,
                batch=batch_of_response[response_id],
                snapshot_id=event.snapshot_id,
                codes_created=list(created_by_response.get(response_id, [])),
                codes_merged=list(merged_by_response.get(response_id, [])),
                n_assignments=n_assignments_by_response.get(response_id, 0),
                duplicate_of=dedup_by_response.get(response_id),
            )
        )

    batches: list[BatchSummary] = []
    cumulative_codes = 0
    seen_code_names: set[str] = set()
    for batch in sorted(responses_by_batch):
        members = responses_by_batch[batch]
        batch_snapshot = snapshot_of_response.get(members[0]) if members else None
        new_codes: list[str] = []
        merges = 0
        for response_id in responses_by_batch[batch]:
            for name in created_by_response.get(response_id, []):
                if name not in seen_code_names:
                    seen_code_names.add(name)
                    new_codes.append(name)
            merges += len(merged_by_response.get(response_id, []))
        cumulative_codes += len(new_codes)
        batches.append(
            BatchSummary(
                batch=batch,
                snapshot_id=batch_snapshot,
                responses=list(responses_by_batch[batch]),
                new_codes=new_codes,
                merges=merges,
                cumulative_codes=cumulative_codes,
                judge_consultations=judge_calls_by_batch.get(batch, 0),
                handover=handovers_by_batch.get(batch),
            )
        )

    return Timeline(
        run_id=run_id,
        steps=steps,
        batches=batches,
        snapshot_diffs=_snapshot_diffs(snapshots, events),
        biographies=_biographies(events, snapshots, coders_index, batch_of_response),
        checkpoints=_checkpoint_markers(events),
    )


# --------------------------------------------------------------------------- #
# 7. Building a Timeline from a bare, ordered coding
# --------------------------------------------------------------------------- #


def timeline_from_assignments(
    rows: Sequence[Assignment],
    *,
    batch_size: int,
    response_order: Sequence[int] | None = None,
) -> Timeline:
    """The same steps and batches, from an ordered human coding.

    No snapshots (a spreadsheet names none) and no fates (there is no operation log to
    read one from) — see the module docstring for what "first appearance" means here.
    `batch_size` groups consecutive *responses*, exactly as
    `gaf.analysis.hca.saturation_curve` batches a matrix's rows.

    **Supply `response_order` whenever the coding processed a response that produced
    no assignment row.** Without it the batches are cut on the responses that *have* a
    row, so a response coded to nothing pulls every later response one slot earlier and
    a batch number computed here stops meaning the batch number `build_timeline`
    computes — which matters because a caller's spike marker
    (`timeline_svg(markers=...)`) is keyed on exactly that number. It is the same root
    cause as the growth curve's ``order=`` (`gaf.checks.growth.code_growth`), and the
    same answer: the processing order is a fact about the run, not something to infer
    from its output. A response in the order with no rows is a step with no codes.

    Raises `ValueError` if `response_order` omits a response `rows` carries: silently
    dropping a coded response is the failure this argument exists to prevent.
    """
    if batch_size < 1:
        raise ValueError(f"batch_size must be at least 1, got {batch_size}")

    rows_by_response: dict[int, list[Assignment]] = {}
    from_rows: list[int] = []
    seen_responses: set[int] = set()
    for row in rows:
        if row.response_id not in seen_responses:
            seen_responses.add(row.response_id)
            from_rows.append(row.response_id)
        rows_by_response.setdefault(row.response_id, []).append(row)

    if response_order is None:
        order = from_rows
    else:
        order = list(dict.fromkeys(int(r) for r in response_order))
        missing = sorted(seen_responses - set(order))
        if missing:
            raise ValueError(
                f"response_order omits {len(missing)} response(s) that carry assignment "
                f"rows (first: {missing[0]}); every coded response takes a place in its "
                "batch, and leaving one out re-cuts every batch after it"
            )
    response_order = order

    steps: list[TimelineStep] = []
    batches: list[BatchSummary] = []
    seen_code_names: set[str] = set()
    cumulative_codes = 0

    for start in range(0, len(response_order), batch_size):
        chunk = response_order[start : start + batch_size]
        batch_number = start // batch_size + 1  # 1-based, matching build_timeline
        new_codes: list[str] = []
        merges = 0
        for response_id in chunk:
            here = rows_by_response.get(response_id, [])
            codes_here: list[str] = []
            for code_name in dict.fromkeys(row.code for row in here):
                codes_here.append(code_name)
            created_here = [name for name in codes_here if name not in seen_code_names]
            merged_here = [name for name in codes_here if name in seen_code_names]
            seen_code_names.update(created_here)
            new_codes.extend(created_here)
            merges += len(merged_here)
            steps.append(
                TimelineStep(
                    response_id=response_id,
                    batch=batch_number,
                    snapshot_id=None,
                    codes_created=created_here,
                    codes_merged=merged_here,
                    n_assignments=len(here),
                    duplicate_of=None,
                )
            )
        cumulative_codes += len(new_codes)
        batches.append(
            BatchSummary(
                batch=batch_number,
                snapshot_id=None,
                responses=list(chunk),
                new_codes=new_codes,
                merges=merges,
                cumulative_codes=cumulative_codes,
                judge_consultations=0,
                handover=None,
            )
        )

    return Timeline(run_id=None, steps=steps, batches=batches)


# --------------------------------------------------------------------------- #
# 8. The SVG
# --------------------------------------------------------------------------- #


def _short(snapshot_id: str, length: int = 12) -> str:
    return snapshot_id if len(snapshot_id) <= length else snapshot_id[:length]


def _axis_label(value: float) -> str:
    """A gridline label that is the value the line sits on.

    Five evenly spaced lines over a whole-number maximum land on halves whenever that
    maximum is odd: ``_num(value, 0)`` labelled a y_max of 14 as 0, 4, 7, 10, 14, so a
    value read off the chart was out by up to half a code (R1 Minor). A line at a
    whole number is still labelled as one; a line between two is labelled as what it
    is.
    """
    rounded = round(value, 2)
    if rounded == int(rounded):
        return _num(rounded, 0)
    return _num(rounded, 2).rstrip("0").rstrip(".")


def _label_anchor(x: float, width: int, *, text_width: float) -> tuple[float, str]:
    """Where to draw a marker label, and how to anchor it, so it stays on the page.

    Drawn at ``x + 2`` with no clamp, a marker at the end of the run rendered its label
    off the right edge of the viewport (R1 Minor). A label that would not fit is
    anchored to the marker's left instead.
    """
    if x + 2 + text_width <= width - 4:
        return x + 2, "start"
    return max(4.0, x - 2), "end"


def timeline_svg(
    timeline: Timeline,
    *,
    width: int = 860,
    height: int = 420,
    title: str = "Timeline of code generation and change",
    markers: Sequence[tuple[int, str]] = (),
) -> str:
    """A self-contained, hand-rendered SVG.

    Cumulative codes are drawn as a step line, new codes per batch as bars sized to
    the batch's own share of responses coded, and vertical markers name the snapshot
    each batch read and every checkpoint `timeline` recorded. `markers` lets another
    module draw its own vertical lines (a batch number, a label — a spike detection,
    say) without this module importing it. A batch number is `BatchSummary.batch`
    itself — 1-based, the same numbering `timeline.batches` and every step already
    use — not a position in the `batches` list.

    Pure function of its arguments: fixed viewport, two-decimal coordinates, no
    timestamp, no generated id — in the manner of `gaf.analysis.hca`'s hand-rendered
    figures, whose `_svg_open` and `_num` this reuses rather than re-deriving.
    """
    batches = timeline.batches
    if not batches:
        parts = _svg_open(width, height, title)
        parts.append(f'<text class="ttl" x="40" y="30">{html.escape(title)}</text>')
        parts.append(
            '<text class="tick" x="40" y="56">No batches — nothing was coded.</text>'
        )
        parts.append("</svg>")
        return "\n".join(parts) + "\n"

    left, right, top, bottom = 56, 24, 44, 40
    plot_w = max(1, width - left - right)
    plot_h = max(1, height - top - bottom)

    total_responses = sum(batch.n_responses for batch in batches) or 1
    y_max = max(
        max((batch.cumulative_codes for batch in batches), default=0),
        max((batch.n_new_codes for batch in batches), default=0),
        1,
    )

    def sx(value: float) -> float:
        return left + (value / total_responses) * plot_w

    def sy(value: float) -> float:
        return top + plot_h * (1.0 - value / y_max)

    parts = _svg_open(width, height, title)
    parts.append(f"<style>{_MARKER_CSS}</style>")
    parts.append(f'<text class="ttl" x="{left}" y="24">{html.escape(title)}</text>')

    for step in range(5):
        value = y_max * step / 4.0
        y = sy(value)
        parts.append(
            f'<line class="grid" x1="{left}" y1="{_num(y)}" x2="{left + plot_w}" y2="{_num(y)}"/>'
        )
        parts.append(
            f'<text class="tick" x="{left - 6}" y="{_num(y + 3)}" text-anchor="end">'
            f"{_axis_label(value)}</text>"
        )
    parts.append(
        f'<line class="axis" x1="{left}" y1="{_num(sy(0))}" x2="{left + plot_w}" y2="{_num(sy(0))}"/>'
    )

    # Bars: one per batch, spanning its own share of responses coded.
    batch_starts: dict[int, float] = {}
    cursor = 0.0
    for batch in batches:
        batch_starts[batch.batch] = cursor
        x0, x1 = sx(cursor), sx(cursor + batch.n_responses)
        y = sy(batch.n_new_codes)
        parts.append(
            f'<rect class="bar" x="{_num(x0)}" y="{_num(y)}" '
            f'width="{_num(max(1.0, x1 - x0))}" height="{_num(sy(0) - y)}"/>'
        )
        parts.append(
            f'<text class="lbl" x="{_num((x0 + x1) / 2)}" y="{_num(sy(0) + 14)}" '
            f'text-anchor="middle">{batch.batch}</text>'
        )
        cursor += batch.n_responses

    # The cumulative-codes step line: flat across a batch, a step at each boundary.
    points: list[str] = []
    cursor = 0.0
    previous = 0
    for batch in batches:
        x0 = sx(cursor)
        points.append(f"{_num(x0)},{_num(sy(previous))}")
        cursor += batch.n_responses
        x1 = sx(cursor)
        points.append(f"{_num(x1)},{_num(sy(previous))}")
        points.append(f"{_num(x1)},{_num(sy(batch.cumulative_codes))}")
        previous = batch.cumulative_codes
    parts.append(f'<polyline class="curve" points="{" ".join(points)}"/>')

    # Snapshot markers, at the start of every batch after the first.
    for batch in batches:
        start = batch_starts[batch.batch]
        if batch.snapshot_id is None or start == 0:
            continue
        x = sx(start)
        text = _short(batch.snapshot_id)
        label_x, anchor = _label_anchor(x, width, text_width=_CHAR_WIDTH * len(text))
        parts.append(
            f'<line class="snapmark" x1="{_num(x)}" y1="{_num(top)}" x2="{_num(x)}" '
            f'y2="{_num(sy(0))}"/>'
        )
        parts.append(
            f'<text class="lbl" x="{_num(label_x)}" y="{_num(top + 10)}" '
            f'text-anchor="{anchor}">{html.escape(text)}</text>'
        )

    # Checkpoint markers. Two checkpoints can sit at the same response count -- a
    # rejected one followed by an accepted one codes nothing between them -- so each
    # one after the first at a given x drops a row rather than printing over it
    # (R1 Minor).
    rows_used: dict[str, int] = {}
    for marker in timeline.checkpoints:
        x = sx(min(float(marker.at_response_count), float(total_responses)))
        row = rows_used.get(_num(x), 0)
        rows_used[_num(x)] = row + 1
        text = f"checkpoint {marker.checkpoint_id}"
        label_x, anchor = _label_anchor(x, width, text_width=_CHAR_WIDTH * len(text))
        parts.append(
            f'<line class="ckptmark" x1="{_num(x)}" y1="{_num(top)}" x2="{_num(x)}" '
            f'y2="{_num(sy(0))}"/>'
        )
        parts.append(
            f'<text class="lbl" x="{_num(label_x)}" y="{_num(top + 22 + row * _LABEL_ROW)}" '
            f'text-anchor="{anchor}" fill="#9b2c2c">{html.escape(text)}</text>'
        )

    # Caller-supplied markers, positioned at the named batch's own start.
    checkpoint_rows = max(rows_used.values(), default=0)
    for batch_number, label in markers:
        if batch_number not in batch_starts:
            continue
        x = sx(batch_starts[batch_number])
        label_x, anchor = _label_anchor(x, width, text_width=_CHAR_WIDTH * len(label))
        parts.append(
            f'<line class="usermark" x1="{_num(x)}" y1="{_num(top)}" x2="{_num(x)}" '
            f'y2="{_num(sy(0))}"/>'
        )
        parts.append(
            f'<text class="lbl" x="{_num(label_x)}" '
            f'y="{_num(top + 34 + max(0, checkpoint_rows - 1) * _LABEL_ROW)}" '
            f'text-anchor="{anchor}" fill="#6b46c1">{html.escape(label)}</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts) + "\n"
