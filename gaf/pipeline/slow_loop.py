"""The slow loop — health, a proposed edit script, the human gate, a new snapshot.

Per checkpoint, in this exact order::

    blackboard + working codebook
      -> health + saturation metrics          (deterministic, gaf.checks.health)
      -> should_checkpoint: does this fire, and why      (auditable, never implicit)
      -> Refactorer: the whole codebook + usage -> an EDIT SCRIPT   (proposes only)
      -> deterministic VALIDATION of the script         (an unappliable op is dropped)
      -> HUMAN GATE: accept / reject / edit, per operation
      -> apply the accepted operations -> new snapshot -> changelog

This module is the **only place in the system where the codebook changes structurally**,
and it does so only with explicit human consent. The fast loop integrates evidence into
codes; splitting, merging, re-parenting and renaming happen here and nowhere else.

Why the gate is here, and not per response
------------------------------------------
Vaccaro et al. (2024, *Nature Human Behaviour*) meta-analyse 106 effect sizes and find
that human-AI combinations average **worse** than the better of the two alone
(Hedges' g = -0.23, 95% CI -0.39 to -0.07). The losses concentrate in **decision tasks**
(g = -0.27), the gains in **creation tasks** (g = 0.19), and synergy is moderated by
whether the division of labour is **predetermined**.

Item-by-item human verification of each machine coding is precisely the decision-task
overlay the meta-analysis finds harmful, so the gate is not there. It is here, at
codebook-refactor level, where the task is generative (restructure a hierarchy) and the
division of labour is fixed in advance: the machine proposes an edit script, the human
accepts, rejects or edits each operation. Less labour per checkpoint, more leverage per
decision. See ADR-0004 and `docs/ARCHITECTURE.md`.

Five properties this module is responsible for holding up
---------------------------------------------------------
**A run with no human present is a no-op.** `RejectAllGate` is the default gate. A
non-interactive checkpoint proposes, validates, records and rejects; it never applies,
never writes a snapshot, and leaves the codebook byte-identical. Auto-accepting in the
absence of a human would put the machine on both sides of its own gate.

**An operation that cannot be applied never reaches the human.** Every script is
validated deterministically first: shapes, targets, name collisions, and then the
question S6 already answers — would the resulting codebook still be well formed? A bad
operation is *dropped with a finding*, never silently repaired and never fatal to the
operations beside it, because one hallucinated row must not cost five good ones.

**Evidence is never lost.** After every applied operation the set of
``(response_id, quote)`` pairs in the codebook is compared with the set before it. A
merge carries the evidence of every source into the target (merge-with-re-examination,
per the PI's §8, not merge-and-discard); a split distributes the target's evidence
across the resulting codes and drops none of it. A violation raises
`EvidenceLossError` rather than being written to a snapshot.

**`split` and `reparent` are first-class.** The predecessor study could only create,
merge, rename or do nothing; unable to restructure, it accreted parallel concepts and
its clustering collapsed. Those two operations exist because their absence is the
documented cause of that failure, so they are implemented properly here rather than
left as the untested members of the set.

**Determinism.** Operations apply in proposal order; new code ids are content hashes of
their names; evidence is content-ordered by `gaf.pipeline.router.merge_evidence`; a code
admitted at a checkpoint records the *base* snapshot it was proposed against, so the
codebook carries no wall clock (ADR-0007). Applying the same accepted script to the same
codebook twice produces the same codebook bytes and the same snapshot id.

Findings are reported through `gaf.checks.contracts`, under check id ``"S6"`` — the
question edit-script validation asks *is* S6's question, "is this codebook well formed",
and a parallel diagnostics channel would be a second place to look. Each finding carries
the repo-wide `gaf.checks.structural.MARKER_KEY` sub-kind.

Validation principles: **interpretive depth** — the human gate sits where a person's
judgment restructures the analysis rather than rubber-stamping it; **transparency** —
the proposal, the drops, the per-operation verdicts, the changelog and both snapshot ids
are all rows.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import Any, Protocol, TextIO, TypeGuard, runtime_checkable

from gaf.agents.refactorer import (
    EditScript,
    RefactorContext,
    RefactorerAgent,
    usage_from_codebook,
)
from gaf.checks.contracts import CheckReport, Severity
from gaf.checks.health import (
    CheckpointSignals,
    HealthMetrics,
    checkpoint_signals,
    codebook_health,
)
from gaf.checks.structural import MARKER_KEY, check_codebook
from gaf.config import CodingRules, RunConfig
from gaf.embed.protocol import Embedder
from gaf.ids import code_id as mint_code_id
from gaf.models import (
    OPERATION_TYPES,
    Code,
    Codebook,
    Evidence,
    Operation,
    family_of,
)
from gaf.pipeline.router import merge_evidence
from gaf.store.blackboard import Blackboard
from gaf.store.snapshot import Snapshot

__all__ = [
    "ACCEPT",
    "BLOCKING_MARKERS",
    "CHECK_ID",
    "EDIT",
    "REJECT",
    "TRIGGERS",
    "VERDICTS",
    "AppliedScript",
    "Changelog",
    "ChangelogEntry",
    "CheckpointResult",
    "CheckpointTrigger",
    "ConsoleGate",
    "DroppedOperation",
    "EvidenceLossError",
    "Gate",
    "GateDecision",
    "OperationDiff",
    "OperationEffect",
    "OperationError",
    "RefactorProposal",
    "RejectAllGate",
    "ScriptValidation",
    "ScriptedGate",
    "apply_operations",
    "build_diff",
    "evidence_pairs",
    "render_diff",
    "render_operation",
    "run_checkpoint",
    "should_checkpoint",
    "validate_script",
]

#: Edit-script validation reports under S6. It is S6's own question — "is the codebook
#: well formed" — asked of the codebook an operation *would* produce, so it belongs on
#: S6's row rather than on a check id no other part of the system knows about.
CHECK_ID = "S6"

#: S6 severities that block an operation. Every new ERROR blocks. `hierarchy_too_deep`
#: is a WARN when S6 observes an existing codebook — the depth rule is the PI's "a
#: codebook with two levels of codes", which is advisory about what exists — but an
#: *edit* that would deepen the hierarchy past the limit is an edit this build refuses
#: to make, so it blocks here.
BLOCKING_MARKERS: tuple[str, ...] = ("hierarchy_too_deep",)

ACCEPT = "accept"
REJECT = "reject"
EDIT = "edit"

#: The three verdicts a human may return for one operation.
VERDICTS: tuple[str, ...] = (ACCEPT, REJECT, EDIT)

#: Why a checkpoint fired. Written to `checkpoints.trigger`, which is free text; these
#: are the values this module mints, and "manual" is the caller-supplied default.
TRIGGERS: tuple[str, ...] = ("health", "floor", "cadence", "manual", "none")


class OperationError(ValueError):
    """One operation cannot be applied to this codebook.

    Carries the `gaf.checks.structural.MARKER_KEY` sub-kind so the finding the slow loop
    writes says *which* invariant the operation would break, machine-readably.
    """

    def __init__(self, message: str, *, marker: str, **data: Any) -> None:
        super().__init__(message)
        self.marker = marker
        self.data = data


class EvidenceLossError(RuntimeError):
    """An applied operation dropped or invented a ``(response_id, quote)`` pair.

    Never caught inside this module: a codebook that has quietly lost evidence must not
    reach a snapshot, because every downstream claim rests on the occurrence table.
    """


# --------------------------------------------------------------------------- #
# 1. Triggers — when the slow loop wakes up, and why it is auditable
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class CheckpointTrigger:
    """Whether a checkpoint fires now, and the reason a reviewer can read.

    The reason is carried rather than recomputed so that "why did the slow loop wake up
    here" is a recorded fact about the run rather than something re-derived from metrics
    that have since moved on.
    """

    fires: bool
    trigger: str
    reason: str
    signals: CheckpointSignals
    metrics: HealthMetrics

    def to_json(self) -> dict[str, Any]:
        return {
            "fires": self.fires,
            "trigger": self.trigger,
            "reason": self.reason,
            "signals": self.signals.to_json(),
            "health": self.metrics.to_json(),
        }


def should_checkpoint(
    codebook: Codebook,
    embedder: Embedder,
    config: RunConfig,
    *,
    responses_coded: int,
    responses_since_checkpoint: int,
    previous: Codebook | None = None,
) -> CheckpointTrigger:
    """Report whether a checkpoint fires, which trigger fired it, and why.

    Delegates every metric to `gaf.checks.health` — this function decides, it does not
    measure. Brief §16.7's chosen default is `CheckpointPolicy.mode == "event_driven"`
    with a hard floor of every `hard_floor_responses` (50) responses:

    * **health** — near-duplicate pairs or new-codes-per-batch exceed the policy *and*
      enough responses have passed since the last checkpoint;
    * **floor** — the hard floor is reached, whatever the codebook looks like, so a
      quiet codebook still gets a human look;
    * **cadence** — `mode == "fixed"`: `responses_coded` is one of
      `CheckpointPolicy.fixed_cadence` (Chan's cadence: first 10, then every 10).

    `previous` is the codebook as of the last checkpoint; without it the whole codebook
    reads as new, which is the correct reading of a first batch.
    """
    policy = config.checkpoints
    metrics = codebook_health(codebook, embedder, config.rules, previous=previous)
    signals = checkpoint_signals(
        metrics,
        policy,
        responses_coded=responses_coded,
        responses_since_checkpoint=responses_since_checkpoint,
    )
    event = (
        policy.mode == "event_driven"
        and signals.spacing_satisfied
        and (signals.near_duplicates_exceeded or signals.new_codes_exceeded)
    )
    cadence = policy.mode == "fixed" and responses_coded in policy.fixed_cadence

    if event:
        trigger = "health"
    elif signals.hard_floor_reached:
        trigger = "floor"
    elif cadence:
        trigger = "cadence"
    else:
        trigger = "none"

    reasons = list(signals.reasons)
    if cadence and trigger == "cadence":
        reasons.append(
            f"fixed cadence: {responses_coded} is a scheduled checkpoint "
            f"({', '.join(str(n) for n in policy.fixed_cadence)})"
        )
    if not reasons:
        reasons.append(
            f"no trigger exceeded: {signals.near_duplicate_pairs} near-duplicate pairs, "
            f"{signals.new_codes} new codes, {responses_coded} responses coded"
        )
    return CheckpointTrigger(
        fires=trigger != "none",
        trigger=trigger,
        reason="; ".join(reasons),
        signals=signals,
        metrics=metrics,
    )


# --------------------------------------------------------------------------- #
# 2. Evidence accounting — the invariant every apply is measured against
# --------------------------------------------------------------------------- #


def evidence_pairs(codebook: Codebook) -> Counter[tuple[int, str]]:
    """The multiset of ``(response_id, quote)`` pairs the codebook carries.

    Counted across every code, verified or not: a quote a coder produced is a fact about
    the run whatever S2 made of it, and a restructuring operation has no business
    changing that count.
    """
    return Counter(
        (evidence.response_id, evidence.quote)
        for code in codebook.sorted_codes()
        for evidence in code.evidence
    )


def _check_evidence_conserved(before: Codebook, after: Codebook, *, what: str) -> tuple[int, int]:
    """Raise unless every quote survived; return the (before, after) totals.

    Two things are checked. **Nothing vanished and nothing was invented**: the *sets* of
    pairs are equal. **Nothing multiplied**: no pair's count rose. A count may fall,
    because merging two codes that quoted the same phrase collapses one duplicate — the
    same fact recorded twice becoming the same fact recorded once, which is what a merge
    means — and the changelog records the collapse.
    """
    left, right = evidence_pairs(before), evidence_pairs(after)
    lost = sorted(set(left) - set(right))
    invented = sorted(set(right) - set(left))
    multiplied = sorted(pair for pair in right if right[pair] > left[pair])
    if lost or invented or multiplied:
        raise EvidenceLossError(
            f"{what} did not conserve evidence: {len(lost)} pair(s) lost, "
            f"{len(invented)} invented, {len(multiplied)} multiplied. "
            f"First lost: {lost[0] if lost else None}; "
            f"first invented: {invented[0] if invented else None}."
        )
    return sum(left.values()), sum(right.values())


# --------------------------------------------------------------------------- #
# 3. Applying one operation — the whole structural vocabulary, in one place
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class OperationEffect:
    """What one applied operation did, in code ids and names. One changelog row."""

    index: int
    type: str
    summary: str
    created: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    changed: list[str] = field(default_factory=list)
    renamed: dict[str, str] = field(default_factory=dict)
    names: dict[str, str] = field(default_factory=dict)
    evidence_before: int = 0
    evidence_after: int = 0

    @property
    def evidence_deduplicated(self) -> int:
        """Quotes that two merged codes both carried, now carried once."""
        return self.evidence_before - self.evidence_after

    def to_json(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "type": self.type,
            "summary": self.summary,
            "created": list(self.created),
            "removed": list(self.removed),
            "changed": list(self.changed),
            "renamed": dict(self.renamed),
            "names": dict(self.names),
            "evidence_before": self.evidence_before,
            "evidence_after": self.evidence_after,
            "evidence_deduplicated": self.evidence_deduplicated,
        }


def _resolve_rules(rules: CodingRules | None) -> CodingRules:
    return rules if rules is not None else CodingRules()


def _payload_str(operation: Operation, key: str) -> str:
    value = operation.payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise OperationError(
            f"{operation.type} needs a non-empty {key!r} in its payload.",
            marker="operation_shape",
            key=key,
        )
    return value.strip()


def _target_code(codebook: Codebook, operation: Operation, *, expected: int = 1) -> Code:
    """The single existing code an operation targets."""
    if len(operation.targets) != expected:
        raise OperationError(
            f"{operation.type} needs exactly {expected} target; got {len(operation.targets)}.",
            marker="operation_shape",
            targets=list(operation.targets),
        )
    code = codebook.codes.get(operation.targets[0])
    if code is None:
        raise OperationError(
            f"Target {operation.targets[0]!r} is not a code in this codebook.",
            marker="unknown_target",
            target=operation.targets[0],
        )
    return code


def _refuse_name_collision(codebook: Codebook, name: str, *, exclude: Iterable[str] = ()) -> None:
    """Refuse a name already used, case-insensitively.

    Checked explicitly rather than left to S6 because code ids are minted from names:
    a colliding name mints a colliding id, and the coming code would *overwrite* the
    existing one in the codebook dict rather than sitting beside it as a duplicate S6
    could report. Silent replacement is the one failure mode a report cannot show.
    """
    excluded = set(exclude)
    folded = name.strip().casefold()
    for code in codebook.sorted_codes():
        if code.id in excluded:
            continue
        if code.name.strip().casefold() == folded:
            raise OperationError(
                f"The name {name!r} is already used by code {code.id!r}; S6 treats a "
                "duplicate name as an ERROR.",
                marker="duplicate_name",
                name=name,
                existing_id=code.id,
            )


def _evidence_from_payload(raw: Any) -> list[Evidence]:
    """Parse an ``evidence`` payload, refusing anything that is not evidence-shaped."""
    if raw is None:
        return []
    if not isinstance(raw, Sequence) or isinstance(raw, str | bytes):
        raise OperationError(
            "An 'evidence' payload must be a list of evidence objects.",
            marker="operation_shape",
        )
    parsed: list[Evidence] = []
    for item in raw:
        if not isinstance(item, Mapping):
            raise OperationError(
                "Each evidence entry must be an object with a response_id and a quote.",
                marker="operation_shape",
            )
        try:
            parsed.append(Evidence.from_json(dict(item)))
        except (KeyError, TypeError, ValueError) as exc:
            raise OperationError(
                f"Unreadable evidence entry: {exc}", marker="operation_shape"
            ) from exc
    return parsed


def _family_parent_id(codebook: Codebook, name: str) -> str | None:
    """The id of the code named after this name's family, when one exists.

    The same rule the fast loop's integration uses: family membership is derived from
    the name (the S3 grammar is canonical) and a missing family node yields no parent
    rather than a fabricated one.
    """
    family = family_of(name)
    if family == name:
        return None
    parent = codebook.by_name(family)
    return parent.id if parent is not None else None


def _with(codebook: Codebook, codes: Iterable[Code]) -> Codebook:
    return Codebook(codes={code.id: code for code in codes})


def _apply_create(
    codebook: Codebook, operation: Operation, index: int, *, snapshot_id: str
) -> tuple[Codebook, OperationEffect]:
    """Admit a code the coders never proposed — a category the human wants named."""
    name = _payload_str(operation, "name")
    _refuse_name_collision(codebook, name)
    payload = operation.payload
    parent_id = (
        payload["parent_id"]
        if "parent_id" in payload
        else _family_parent_id(codebook, name)
    )
    if parent_id is not None and parent_id not in codebook.codes:
        raise OperationError(
            f"Parent {parent_id!r} is not a code in this codebook.",
            marker="unknown_target",
            target=parent_id,
        )
    created = Code(
        id=mint_code_id(name),
        name=name,
        description=str(payload.get("description", "")),
        parent_id=parent_id,
        created_in_snapshot=snapshot_id,
        evidence=merge_evidence(_evidence_from_payload(payload.get("evidence"))),
    )
    codes = dict(codebook.codes)
    codes[created.id] = created
    parent_name = codebook.codes[parent_id].name if parent_id else None
    return Codebook(codes=codes), OperationEffect(
        index=index,
        type="create",
        summary=(
            f"created {name!r}"
            + (f" under {parent_name!r}" if parent_name else " at the top level")
        ),
        created=[created.id],
        names={created.id: created.name},
    )


def _apply_merge(
    codebook: Codebook, operation: Operation, index: int
) -> tuple[Codebook, OperationEffect]:
    """Fold several codes into one, carrying every source's evidence into the target.

    Merge-with-re-examination, per the PI's §8 ("Merge or split codes as required;
    reapply the new codebook to all responses coded to that point"): the surviving code
    inherits the quotes of everything folded into it, so the merged category can be read
    against the evidence that justified each of its parts. Merge-and-discard would throw
    away exactly what a re-examination needs.

    Children of a removed source are re-parented onto the target rather than orphaned,
    and the move is recorded.
    """
    distinct = list(dict.fromkeys(operation.targets))
    if len(distinct) < 2:
        raise OperationError(
            f"merge needs at least 2 distinct targets; got {len(distinct)}.",
            marker="operation_shape",
            targets=list(operation.targets),
        )
    missing = [t for t in distinct if t not in codebook.codes]
    if missing:
        raise OperationError(
            f"Targets {missing!r} are not codes in this codebook.",
            marker="unknown_target",
            targets=missing,
        )
    into = operation.payload.get("into", distinct[0])
    if into not in distinct:
        raise OperationError(
            f"merge payload 'into' must name one of the targets; got {into!r}.",
            marker="operation_shape",
            into=into,
            targets=distinct,
        )
    target = codebook.codes[str(into)]
    sources = [codebook.codes[t] for t in distinct if t != target.id]

    description = operation.payload.get("description")
    merged = replace(
        target,
        description=str(description) if isinstance(description, str) else target.description,
        evidence=merge_evidence(target.evidence, *[s.evidence for s in sources]),
    )
    removed = {s.id for s in sources}
    codes: list[Code] = [merged]
    for code in codebook.sorted_codes():
        if code.id == target.id or code.id in removed:
            continue
        codes.append(
            replace(code, parent_id=target.id) if code.parent_id in removed else code
        )
    reparented = [c.name for c in codebook.sorted_codes() if c.parent_id in removed]
    summary = (
        f"merged {', '.join(repr(s.name) for s in sources)} into {target.name!r}"
        + (f"; re-parented {len(reparented)} child code(s) onto it" if reparented else "")
    )
    return _with(codebook, codes), OperationEffect(
        index=index,
        type="merge",
        summary=summary,
        removed=sorted(removed),
        changed=[target.id],
        names={c.id: c.name for c in [target, *sources]},
    )


def _split_entries(operation: Operation) -> list[Mapping[str, Any]]:
    raw = operation.payload.get("into")
    if not isinstance(raw, Sequence) or isinstance(raw, str | bytes) or len(raw) < 2:
        raise OperationError(
            "split needs a payload 'into' naming at least 2 resulting codes.",
            marker="operation_shape",
        )
    entries: list[Mapping[str, Any]] = []
    for item in raw:
        if not isinstance(item, Mapping) or not str(item.get("name", "")).strip():
            raise OperationError(
                "Each entry of a split payload must be an object with a 'name'.",
                marker="operation_shape",
            )
        entries.append(item)
    return entries


def _is_list(value: Any) -> TypeGuard[Sequence[Any]]:
    """True for a JSON array — a sequence that is not a string."""
    return isinstance(value, Sequence) and not isinstance(value, str | bytes)


def _claims(entry: Mapping[str, Any], evidence: Evidence) -> bool:
    """Whether a split entry claims this quote, by quote text or by response id."""
    quotes = entry.get("quotes")
    if _is_list(quotes) and any(str(q) == evidence.quote for q in quotes):
        return True
    ids = entry.get("response_ids")
    return _is_list(ids) and any(int(i) == evidence.response_id for i in ids)


def _apply_split(
    codebook: Codebook, operation: Operation, index: int, *, snapshot_id: str
) -> tuple[Codebook, OperationEffect]:
    """Separate one overloaded code into several, distributing its evidence.

    One of the two anti-flattening operations. The predecessor study could not split, so
    when one code came to carry two distinguishable strands of meaning it accreted a
    parallel code instead of restructuring; the clustering downstream collapsed.

    Evidence goes to the **first** entry that claims it — by exact quote in the entry's
    ``quotes``, or by response id in its ``response_ids`` — and every unclaimed quote
    goes to the first resulting code. Every quote therefore lands in exactly one place:
    a split redistributes evidence and cannot lose it, which
    `_check_evidence_conserved` then verifies rather than trusting.
    """
    target = _target_code(codebook, operation)
    entries = _split_entries(operation)
    names = [str(entry["name"]).strip() for entry in entries]
    seen: set[str] = set()
    for name in names:
        folded = name.casefold()
        if folded in seen:
            raise OperationError(
                f"split would produce two codes named {name!r}.",
                marker="duplicate_name",
                name=name,
            )
        seen.add(folded)
        _refuse_name_collision(codebook, name, exclude={target.id})

    buckets: list[list[Evidence]] = [[] for _ in entries]
    for evidence in target.evidence:
        position = next(
            (i for i, entry in enumerate(entries) if _claims(entry, evidence)), 0
        )
        buckets[position].append(evidence)

    created: list[Code] = []
    for entry, name, bucket in zip(entries, names, buckets, strict=True):
        parent_id = entry.get("parent_id", target.parent_id)
        if parent_id is not None and parent_id not in codebook.codes:
            raise OperationError(
                f"Parent {parent_id!r} is not a code in this codebook.",
                marker="unknown_target",
                target=parent_id,
            )
        created.append(
            Code(
                id=mint_code_id(name),
                name=name,
                description=str(entry.get("description", target.description)),
                parent_id=parent_id,
                created_in_snapshot=snapshot_id,
                evidence=merge_evidence(bucket),
            )
        )

    heir = created[0]
    codes: list[Code] = list(created)
    for code in codebook.sorted_codes():
        if code.id == target.id or code.id in {c.id for c in created}:
            continue
        codes.append(replace(code, parent_id=heir.id) if code.parent_id == target.id else code)
    orphans = [c.name for c in codebook.sorted_codes() if c.parent_id == target.id]
    summary = (
        f"split {target.name!r} into {', '.join(repr(n) for n in names)} "
        f"({', '.join(f'{len(b)} quote(s)' for b in buckets)})"
        + (f"; {len(orphans)} child code(s) moved under {heir.name!r}" if orphans else "")
    )
    return _with(codebook, codes), OperationEffect(
        index=index,
        type="split",
        summary=summary,
        created=[c.id for c in created],
        removed=[target.id],
        names={target.id: target.name, **{c.id: c.name for c in created}},
    )


def _apply_reparent(
    codebook: Codebook, operation: Operation, index: int
) -> tuple[Codebook, OperationEffect]:
    """Move a code under a different parent, or promote it to the top level.

    The second anti-flattening operation. ``payload["new_parent_id"]`` must be present;
    ``null`` is a legitimate value and means "promote this code to a family of its own".

    Only the structural link moves. A code's *name* carries its family by the S3 grammar,
    so a re-parent that should also change the family reads as two operations — the
    reparent and a rename — which is deliberate: the human sees, and decides on, both.

    Cycles and over-deep chains are not re-implemented here. The projection gate in
    `validate_script` puts the resulting codebook through `check_codebook`, whose
    ``parent_cycle`` ERROR and ``hierarchy_too_deep`` WARN are exactly these two
    questions, already asked in the one place that owns them.
    """
    target = _target_code(codebook, operation)
    if "new_parent_id" not in operation.payload:
        raise OperationError(
            "reparent needs a 'new_parent_id' in its payload (null promotes to the top level).",
            marker="operation_shape",
        )
    new_parent = operation.payload["new_parent_id"]
    if new_parent is not None:
        new_parent = str(new_parent)
        if new_parent not in codebook.codes:
            raise OperationError(
                f"New parent {new_parent!r} is not a code in this codebook.",
                marker="unknown_target",
                target=new_parent,
            )
    if new_parent == target.parent_id:
        raise OperationError(
            f"{target.name!r} already sits under that parent; the operation would do nothing.",
            marker="operation_shape",
            target=target.id,
        )
    codes = dict(codebook.codes)
    codes[target.id] = replace(target, parent_id=new_parent)
    parent_name = codebook.codes[new_parent].name if new_parent else None
    summary = (
        f"re-parented {target.name!r} under {parent_name!r}"
        if parent_name
        else f"promoted {target.name!r} to the top level"
    )
    return Codebook(codes=codes), OperationEffect(
        index=index,
        type="reparent",
        summary=summary,
        changed=[target.id],
        names={target.id: target.name},
    )


def _rename_map(codebook: Codebook, old: str, new: str) -> dict[str, str]:
    """Old name -> new name for the target and every sub-code carrying its family.

    A family node's name *is* the family of its sub-codes (`gaf.models.family_of`), so
    renaming ``positive_impacts`` to ``benefits`` without also renaming
    ``positive_impacts-healthcare`` would leave the codebook saying two different things
    about the same family. This is the batch-rename `docs/ARCHITECTURE.md` names.
    """
    mapping = {old: new}
    prefix = f"{old}-"
    for code in codebook.sorted_codes():
        if code.name.startswith(prefix):
            mapping[code.name] = f"{new}-{code.name[len(prefix):]}"
    return mapping


def _apply_rename(
    codebook: Codebook, operation: Operation, index: int
) -> tuple[Codebook, OperationEffect]:
    """Rename a code, cascading to the sub-codes that carry its family in their names.

    A code's id is the content hash of its name (`gaf.ids.code_id`), so a rename mints a
    new id and every `parent_id` pointing at the old one is rewritten. The old-to-new
    mapping goes in the changelog, which is what keeps a renamed code traceable across
    snapshots.
    """
    target = _target_code(codebook, operation)
    new_name = _payload_str(operation, "name")
    if new_name == target.name:
        raise OperationError(
            f"rename would leave {target.name!r} unchanged.",
            marker="operation_shape",
            name=new_name,
        )
    mapping = _rename_map(codebook, target.name, new_name)
    touched = {code.id for code in codebook.sorted_codes() if code.name in mapping}
    for name in mapping.values():
        _refuse_name_collision(codebook, name, exclude=touched)
    folded = Counter(name.casefold() for name in mapping.values())
    clash = sorted(name for name, count in folded.items() if count > 1)
    if clash:
        raise OperationError(
            f"rename would produce duplicate names: {clash}.",
            marker="duplicate_name",
            names=clash,
        )

    id_map = {
        code.id: mint_code_id(mapping[code.name])
        for code in codebook.sorted_codes()
        if code.name in mapping
    }
    codes: list[Code] = []
    for code in codebook.sorted_codes():
        renamed_to = mapping.get(code.name)
        codes.append(
            replace(
                code,
                id=id_map.get(code.id, code.id),
                name=renamed_to if renamed_to is not None else code.name,
                parent_id=id_map.get(code.parent_id, code.parent_id)
                if code.parent_id
                else code.parent_id,
            )
        )
    cascaded = len(mapping) - 1
    summary = f"renamed {target.name!r} to {new_name!r}" + (
        f", cascading to {cascaded} sub-code(s)" if cascaded else ""
    )
    return _with(codebook, codes), OperationEffect(
        index=index,
        type="rename",
        summary=summary,
        changed=sorted(id_map.values()),
        renamed=dict(sorted(id_map.items())),
        names={
            id_map[code.id]: mapping[code.name]
            for code in codebook.sorted_codes()
            if code.name in mapping
        },
    )


def _apply_one(
    codebook: Codebook, operation: Operation, index: int, *, snapshot_id: str
) -> tuple[Codebook, OperationEffect]:
    """Apply one operation, or raise `OperationError`. Never mutates the input."""
    if operation.type not in OPERATION_TYPES:
        raise OperationError(
            f"Unknown operation type {operation.type!r}; expected one of {OPERATION_TYPES}.",
            marker="operation_shape",
        )
    if operation.type == "create":
        return _apply_create(codebook, operation, index, snapshot_id=snapshot_id)
    if operation.type == "merge":
        return _apply_merge(codebook, operation, index)
    if operation.type == "split":
        return _apply_split(codebook, operation, index, snapshot_id=snapshot_id)
    if operation.type == "reparent":
        return _apply_reparent(codebook, operation, index)
    if operation.type == "rename":
        return _apply_rename(codebook, operation, index)
    return codebook, OperationEffect(
        index=index, type="noop", summary="no structural change"
    )


# --------------------------------------------------------------------------- #
# 4. Validation — deterministic, before any human sees the script
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class DroppedOperation:
    """An operation validation removed from the script, and why."""

    index: int
    operation: Operation
    marker: str
    reason: str

    def to_json(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "operation": self.operation.to_json(),
            "marker": self.marker,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class ScriptValidation:
    """What survived deterministic validation, what did not, and the findings.

    `kept` is what the human is shown. `projected` is the codebook that would result if
    every kept operation were accepted — computed here so that validation and
    application can never disagree about what an operation does: both run the same
    `_apply_one`.
    """

    kept: list[Operation]
    dropped: list[DroppedOperation]
    report: CheckReport
    projected: Codebook
    effects: list[OperationEffect] = field(default_factory=list)

    @property
    def n_proposed(self) -> int:
        return len(self.kept) + len(self.dropped)

    def passed(self) -> bool:
        """True when nothing had to be dropped."""
        return not self.dropped

    def to_json(self) -> dict[str, Any]:
        return {
            "n_proposed": self.n_proposed,
            "kept": [op.to_json() for op in self.kept],
            "dropped": [d.to_json() for d in self.dropped],
            "findings": self.report.to_json(),
            "summary": self.report.summary(),
        }


def _severity_fingerprint(report: CheckReport) -> Counter[tuple[str, str]]:
    """Counts by (severity, marker), which is stable under a rename.

    Fingerprinting by subject would make renaming a code with a pre-existing WARN look
    like a *new* WARN, and would block an operation for a finding that was already
    there. Counts by kind answer the question actually being asked: did this operation
    make the codebook worse?
    """
    return Counter(
        (finding.severity.value, str(finding.data.get(MARKER_KEY, "")))
        for finding in report.findings
    )


def _blocking_regressions(
    before: Counter[tuple[str, str]], after: Counter[tuple[str, str]]
) -> list[str]:
    """Which blocking S6 kinds this operation increased."""
    worse: list[str] = []
    for key, count in sorted(after.items()):
        severity, marker = key
        blocks = severity == Severity.ERROR.value or marker in BLOCKING_MARKERS
        if blocks and count > before[key]:
            worse.append(f"{severity} {marker or 'unmarked'} ({before[key]} -> {count})")
    return worse


def validate_script(
    operations: Sequence[Operation],
    codebook: Codebook,
    rules: CodingRules | None = None,
    *,
    corpus_response_ids: Iterable[int] | None = None,
    snapshot_id: str = "",
) -> ScriptValidation:
    """Validate an edit script against a codebook. Reports; applies nothing permanent.

    Two layers, and both are needed.

    **Shape.** Every ``type`` is in `gaf.models.OPERATION_TYPES`; every target id exists;
    ``merge`` has at least two distinct targets; ``split`` has a payload naming the
    resulting codes; ``reparent`` has a ``new_parent_id`` key; ``rename`` has a new name.
    A name collision is refused here rather than left to S6 because ids are minted from
    names, so a colliding name would overwrite a code instead of duplicating it.

    **Projection.** Each surviving operation is applied to a running projection and the
    result is put through `gaf.checks.structural.check_codebook`. Any *new* S6 ERROR —
    a dangling parent, a parent cycle, a duplicate name, evidence naming a response
    outside the corpus — or any new ``hierarchy_too_deep`` WARN blocks the operation. Not
    reimplemented: S6 already owns those invariants, and a second implementation of them
    would be a second thing to keep in step.

    Operations are validated **in order against the accumulating projection**, so an
    operation that is only invalid because of an earlier one — two renames onto the same
    name, a reparent under a code a merge removed — is caught at the operation that
    causes it. A dropped operation is dropped alone: one hallucinated row must not cost
    the good rows beside it.
    """
    resolved = _resolve_rules(rules)
    corpus_ids = None if corpus_response_ids is None else sorted(set(corpus_response_ids))
    report = CheckReport()
    kept: list[Operation] = []
    dropped: list[DroppedOperation] = []
    effects: list[OperationEffect] = []
    projected = codebook
    fingerprint = _severity_fingerprint(check_codebook(projected, corpus_ids, resolved))

    for index, operation in enumerate(operations):
        subject = f"op{index}:{operation.type}"
        try:
            candidate, effect = _apply_one(
                projected, operation, index, snapshot_id=snapshot_id
            )
        except OperationError as exc:
            dropped.append(
                DroppedOperation(
                    index=index, operation=operation, marker=exc.marker, reason=str(exc)
                )
            )
            report.add(
                CHECK_ID,
                Severity.ERROR,
                "codebook",
                subject,
                f"Operation {index} ({operation.type}) dropped: {exc}",
                **{MARKER_KEY: exc.marker},
                operation_index=index,
                operation_type=operation.type,
                targets=list(operation.targets),
                detail=dict(exc.data),
            )
            continue

        after = _severity_fingerprint(check_codebook(candidate, corpus_ids, resolved))
        regressions = _blocking_regressions(fingerprint, after)
        if regressions:
            reason = (
                f"the resulting codebook would gain {', '.join(regressions)} under S6"
            )
            dropped.append(
                DroppedOperation(
                    index=index,
                    operation=operation,
                    marker="new_error",
                    reason=reason,
                )
            )
            report.add(
                CHECK_ID,
                Severity.ERROR,
                "codebook",
                subject,
                f"Operation {index} ({operation.type}) dropped: {reason}.",
                **{MARKER_KEY: "new_error"},
                operation_index=index,
                operation_type=operation.type,
                targets=list(operation.targets),
                regressions=regressions,
            )
            continue

        try:
            before_total, after_total = _check_evidence_conserved(
                projected, candidate, what=f"operation {index} ({operation.type})"
            )
        except EvidenceLossError as exc:
            dropped.append(
                DroppedOperation(
                    index=index,
                    operation=operation,
                    marker="evidence_loss",
                    reason=str(exc),
                )
            )
            report.add(
                CHECK_ID,
                Severity.ERROR,
                "codebook",
                subject,
                f"Operation {index} ({operation.type}) dropped: {exc}",
                **{MARKER_KEY: "evidence_loss"},
                operation_index=index,
                operation_type=operation.type,
            )
            continue

        projected = candidate
        fingerprint = after
        kept.append(operation)
        effects.append(
            replace(effect, evidence_before=before_total, evidence_after=after_total)
        )

    return ScriptValidation(
        kept=kept, dropped=dropped, report=report, projected=projected, effects=effects
    )


# --------------------------------------------------------------------------- #
# 5. Application — only what the human accepted, in a deterministic order
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class AppliedScript:
    """The codebook an accepted script produced, and what each operation did."""

    codebook: Codebook
    effects: list[OperationEffect]
    evidence_before: int
    evidence_after: int

    @property
    def changed(self) -> bool:
        return bool(self.effects) and any(effect.type != "noop" for effect in self.effects)

    def to_json(self) -> dict[str, Any]:
        return {
            "effects": [effect.to_json() for effect in self.effects],
            "evidence_before": self.evidence_before,
            "evidence_after": self.evidence_after,
            "n_codes": len(self.codebook),
        }


def apply_operations(
    codebook: Codebook,
    operations: Sequence[Operation],
    *,
    snapshot_id: str,
) -> AppliedScript:
    """Apply a **validated** script in proposal order. Strict: raises on a bad operation.

    Proposal order is the deterministic order. It is the order the Refactorer reasoned
    in, the order validation projected in, and the order the human reviewed in; sorting
    by type would silently reorder a script whose operations depend on each other.

    Evidence conservation is asserted after every operation, not just at the end, so a
    violation names the operation that caused it. Nothing here mutates the input
    codebook: each step returns a new one.
    """
    working = codebook
    effects: list[OperationEffect] = []
    for index, operation in enumerate(operations):
        candidate, effect = _apply_one(working, operation, index, snapshot_id=snapshot_id)
        before, after = _check_evidence_conserved(
            working, candidate, what=f"operation {index} ({operation.type})"
        )
        working = candidate
        effects.append(replace(effect, evidence_before=before, evidence_after=after))
    total_before = sum(evidence_pairs(codebook).values())
    total_after = sum(evidence_pairs(working).values())
    return AppliedScript(
        codebook=working,
        effects=effects,
        evidence_before=total_before,
        evidence_after=total_after,
    )


# --------------------------------------------------------------------------- #
# 6. The diff — what the human actually reads
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class OperationDiff:
    """One reviewable operation: what it does, to what, why, and what is at stake.

    "What is at stake" is the count of responses whose evidence the affected codes
    carry. The human at this gate is reading a compact diff, not re-reading raw codings
    — that is the whole point of the gate's placement (ADR-0004) — so the weight of
    evidence behind an operation has to be *on* the diff rather than a query away.
    """

    index: int
    type: str
    summary: str
    rationale: str
    targets: list[str]
    target_names: list[str]
    evidence_at_stake: dict[str, int]
    responses_at_stake: int
    detail: list[str]

    def to_json(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "type": self.type,
            "summary": self.summary,
            "rationale": self.rationale,
            "targets": list(self.targets),
            "target_names": list(self.target_names),
            "evidence_at_stake": dict(self.evidence_at_stake),
            "responses_at_stake": self.responses_at_stake,
            "detail": list(self.detail),
        }


def _affected(codebook: Codebook, operation: Operation) -> list[Code]:
    """Existing codes an operation touches, name-sorted and de-duplicated."""
    ids = list(operation.targets)
    if operation.type == "reparent":
        parent = operation.payload.get("new_parent_id")
        if isinstance(parent, str):
            ids.append(parent)
    if operation.type == "create":
        parent = operation.payload.get("parent_id")
        if isinstance(parent, str):
            ids.append(parent)
    found = {code_id: codebook.codes[code_id] for code_id in ids if code_id in codebook.codes}
    return sorted(found.values(), key=lambda c: (c.name, c.id))


def build_diff(operations: Sequence[Operation], codebook: Codebook) -> list[OperationDiff]:
    """Render each operation as a reviewable diff against `codebook`.

    A diff is built by *actually applying* the operation to a projection and reading the
    effect back, so the summary the human accepts describes what accepting it will do
    rather than a second, hand-written account of the same operation that could drift
    from it. An operation that cannot be applied is described as such — though
    `run_checkpoint` has already dropped those before the gate sees them.
    """
    diffs: list[OperationDiff] = []
    projected = codebook
    for index, operation in enumerate(operations):
        affected = _affected(projected, operation)
        at_stake = {code.name: len(code.response_ids()) for code in affected}
        responses = {rid for code in affected for rid in code.response_ids()}
        try:
            after, effect = _apply_one(projected, operation, index, snapshot_id="")
            summary = effect.summary
            detail = _detail_lines(projected, after, effect)
            projected = after
        except OperationError as exc:
            summary = f"cannot be applied: {exc}"
            detail = [f"! {exc}"]
        diffs.append(
            OperationDiff(
                index=index,
                type=operation.type,
                summary=summary,
                rationale=operation.rationale,
                targets=list(operation.targets),
                target_names=[code.name for code in affected],
                evidence_at_stake=at_stake,
                responses_at_stake=len(responses),
                detail=detail,
            )
        )
    return diffs


def _detail_lines(before: Codebook, after: Codebook, effect: OperationEffect) -> list[str]:
    """Before/after lines for one operation, in the order a reader scans them."""
    lines: list[str] = []
    for code_id in effect.removed:
        code = before.codes.get(code_id)
        if code is not None:
            lines.append(f"  - {code.name}  ({len(code.response_ids())} responses)")
    for old_id, new_id in sorted(effect.renamed.items()):
        old, new = before.codes.get(old_id), after.codes.get(new_id)
        if old is not None and new is not None and old.name != new.name:
            lines.append(f"  ~ {old.name}  ->  {new.name}")
    for code_id in effect.created:
        code = after.codes.get(code_id)
        if code is not None:
            lines.append(f"  + {code.name}  ({len(code.response_ids())} responses)")
    for code_id in effect.changed:
        old, new = before.codes.get(code_id), after.codes.get(code_id)
        if old is None or new is None or old == new:
            continue
        if old.parent_id != new.parent_id:
            old_parent = before.codes.get(old.parent_id or "")
            new_parent = after.codes.get(new.parent_id or "")
            lines.append(
                f"  ~ {new.name}: parent "
                f"{old_parent.name if old_parent else '(top level)'}  ->  "
                f"{new_parent.name if new_parent else '(top level)'}"
            )
        if len(old.evidence) != len(new.evidence):
            lines.append(
                f"  ~ {new.name}: evidence {len(old.evidence)}  ->  {len(new.evidence)} quote(s)"
            )
        if old.description != new.description:
            lines.append(f"  ~ {new.name}: description rewritten")
    return lines


def render_operation(diff: OperationDiff) -> str:
    """One operation as the block a human reads at the console."""
    lines = [
        f"[{diff.index}] {diff.type.upper()}  {diff.summary}",
    ]
    if diff.rationale:
        lines.append(f"    why: {diff.rationale}")
    if diff.evidence_at_stake:
        stake = ", ".join(
            f"{name} ({count})" for name, count in sorted(diff.evidence_at_stake.items())
        )
        lines.append(f"    evidence at stake: {stake}")
        lines.append(f"    responses affected: {diff.responses_at_stake}")
    lines.extend(diff.detail)
    return "\n".join(lines)


def render_diff(diffs: Sequence[OperationDiff], *, header: str = "") -> str:
    """The whole proposal as text. The same body `ConsoleGate` prints."""
    blocks = [header] if header else []
    blocks.extend(render_operation(diff) for diff in diffs)
    if not diffs:
        blocks.append("(no operations survived validation; nothing to review)")
    return "\n\n".join(blocks)


# --------------------------------------------------------------------------- #
# 7. The proposal and the human gate
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class RefactorProposal:
    """What the human is asked to decide on: a validated script and its diff.

    `script.operations` is the **validated** list — an operation that cannot be applied
    never reaches the gate, because an unactionable row is wasted human attention — and
    `GateDecision.index` indexes into exactly that list. What was dropped, and why, is
    on `validation` for the run report.
    """

    snapshot_id: str
    trigger: str
    script: EditScript
    diffs: list[OperationDiff]
    validation: ScriptValidation
    health: HealthMetrics | None = None

    @property
    def operations(self) -> list[Operation]:
        return list(self.script.operations)

    def __len__(self) -> int:
        return len(self.script.operations)

    def is_noop(self) -> bool:
        """True when there is nothing structural for a human to decide."""
        return not self.script.operations or self.script.is_noop()

    def to_json(self) -> dict[str, Any]:
        """The stored proposal.

        ``operations`` sits at the top level because
        `gaf.store.blackboard.CheckpointRecord.operations()` reads it from there.
        """
        return {
            "operations": [op.to_json() for op in self.script.operations],
            "reasoning": self.script.reasoning,
            "snapshot_id": self.snapshot_id,
            "trigger": self.trigger,
            "prompt_version": self.script.prompt_version,
            "subject": self.script.subject,
            "fail_safe": self.script.fail_safe,
            "types": self.script.types(),
            "diff": [diff.to_json() for diff in self.diffs],
            "validation": self.validation.to_json(),
            "health": self.health.to_json() if self.health is not None else None,
        }


@dataclass(frozen=True, slots=True)
class GateDecision:
    """One human verdict on one operation.

    `index` is the position in `RefactorProposal.script.operations`. `operation` is the
    human's replacement and is required when `verdict` is ``"edit"``; an edit without
    one is treated as a rejection, because the safe reading of an ambiguous human
    instruction at this gate is "do not change the codebook".
    """

    index: int
    verdict: str
    operation: Operation | None = None
    note: str = ""

    def to_json(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "verdict": self.verdict,
            "operation": self.operation.to_json() if self.operation is not None else None,
            "note": self.note,
        }

    @classmethod
    def from_json(cls, obj: Mapping[str, Any]) -> GateDecision:
        raw = obj.get("operation")
        return cls(
            index=int(obj["index"]),
            verdict=str(obj["verdict"]),
            operation=Operation.from_json(dict(raw)) if isinstance(raw, Mapping) else None,
            note=str(obj.get("note", "")),
        )


@runtime_checkable
class Gate(Protocol):
    """How a human decides on a proposed edit script.

    One method, per-operation verdicts out. Any operation the gate returns no decision
    for is rejected: the gate says what to change, and silence changes nothing.
    """

    def review(self, proposal: RefactorProposal) -> list[GateDecision]:
        """Return one decision per operation the human ruled on."""
        ...


class RejectAllGate:
    """The default gate. Rejects every operation, and applies nothing.

    **This is what a non-interactive run does, and it is the single most important
    property of the slow loop.** A checkpoint with no human present must be a no-op, not
    an auto-accept: the machine proposes and a person disposes, and a machine that
    disposed of its own proposals when nobody was watching would be the design's own
    failure mode with extra steps. A run under this gate still proposes, still validates
    and still records — the proposal and the rejection are both rows — but the codebook
    comes out byte-identical and no snapshot is written.
    """

    def __init__(self, note: str = "no human at the gate; rejected by default") -> None:
        self.note = note

    def review(self, proposal: RefactorProposal) -> list[GateDecision]:
        return [
            GateDecision(index=index, verdict=REJECT, note=self.note)
            for index in range(len(proposal.script.operations))
        ]


class ScriptedGate:
    """A gate that replays a fixed list of decisions.

    For a human who has already decided — decisions read back from a previous
    checkpoint, or supplied on a command line — and for tests. It is not a way to accept
    without a human: the decisions it replays are a human's, recorded elsewhere.
    """

    def __init__(self, decisions: Sequence[GateDecision]) -> None:
        self.decisions = list(decisions)

    def review(self, proposal: RefactorProposal) -> list[GateDecision]:
        limit = len(proposal.script.operations)
        return [d for d in self.decisions if 0 <= d.index < limit]


class ConsoleGate:
    """The interactive gate: prints the diff, reads a verdict per operation from stdin.

    One line per operation. ``a``/``accept`` accepts, ``r``/``reject`` rejects, ``e``/
    ``edit`` then reads one line of JSON for the replacement operation. Anything after
    the verdict on the same line is kept as the note, so ``r not convinced by the
    evidence`` records both the verdict and the reason.

    **The default answer is reject.** An empty line, an unrecognised verdict, an
    unreadable edit and end-of-input all reject — and end-of-input rejects everything
    remaining without prompting further, so a `ConsoleGate` wired to a closed pipe
    behaves exactly like `RejectAllGate` rather than blocking or, worse, accepting.
    """

    def __init__(
        self, stream_in: TextIO = sys.stdin, stream_out: TextIO = sys.stdout
    ) -> None:
        self.stream_in = stream_in
        self.stream_out = stream_out

    # -- output ----------------------------------------------------------- #

    def _write(self, text: str = "") -> None:
        self.stream_out.write(f"{text}\n")

    def header(self, proposal: RefactorProposal) -> str:
        """The banner: where the proposal came from and what validation made of it."""
        lines = [
            "=" * 72,
            f"CHECKPOINT  snapshot {proposal.snapshot_id}  trigger {proposal.trigger}",
            f"{len(proposal.script.operations)} operation(s) to review; "
            f"{len(proposal.validation.dropped)} dropped in validation.",
        ]
        if proposal.health is not None:
            health = proposal.health
            lines.append(
                f"codebook: {health.n_codes} codes in {health.n_families} families, "
                f"{health.near_duplicate_pairs} near-duplicate pair(s), "
                f"{health.new_codes} new since the last checkpoint."
            )
        if proposal.script.reasoning:
            lines.append(f"refactorer: {proposal.script.reasoning}")
        for dropped in proposal.validation.dropped:
            lines.append(f"  (dropped [{dropped.index}] {dropped.operation.type}: {dropped.reason})")
        lines.append("=" * 72)
        return "\n".join(lines)

    # -- input ------------------------------------------------------------ #

    def _read(self) -> str | None:
        """One line, or None at end of input."""
        line = self.stream_in.readline()
        if line == "":
            return None
        return line.strip()

    def _edited(self, index: int, note: str) -> GateDecision:
        """Read the replacement operation for an edited row."""
        self._write("    paste the replacement operation as one line of JSON:")
        raw = self._read()
        if raw is None or not raw:
            return GateDecision(
                index=index,
                verdict=REJECT,
                note=(note + " " if note else "") + "(no replacement supplied; rejected)",
            )
        try:
            operation = Operation.from_json(json.loads(raw))
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            self._write(f"    unreadable replacement ({exc}); rejected.")
            return GateDecision(
                index=index,
                verdict=REJECT,
                note=(note + " " if note else "") + f"(unreadable replacement: {exc})",
            )
        return GateDecision(index=index, verdict=EDIT, operation=operation, note=note)

    def review(self, proposal: RefactorProposal) -> list[GateDecision]:
        self._write(self.header(proposal))
        decisions: list[GateDecision] = []
        closed = False
        for diff in proposal.diffs:
            if closed:
                decisions.append(
                    GateDecision(
                        index=diff.index, verdict=REJECT, note="(input closed; rejected)"
                    )
                )
                continue
            self._write()
            self._write(render_operation(diff))
            self._write("    [a]ccept / [r]eject / [e]dit  (default: reject) > ")
            answer = self._read()
            if answer is None:
                closed = True
                decisions.append(
                    GateDecision(
                        index=diff.index, verdict=REJECT, note="(input closed; rejected)"
                    )
                )
                continue
            verdict_token, _, note = answer.partition(" ")
            token = verdict_token.strip().casefold()
            note = note.strip()
            if token in ("a", "accept", "y", "yes"):
                decisions.append(GateDecision(index=diff.index, verdict=ACCEPT, note=note))
            elif token in ("e", "edit"):
                decisions.append(self._edited(diff.index, note))
            else:
                if token not in ("", "r", "reject", "n", "no"):
                    note = (f"unrecognised verdict {verdict_token!r}; " + note).strip()
                decisions.append(GateDecision(index=diff.index, verdict=REJECT, note=note))
        self._write()
        accepted = sum(1 for d in decisions if d.verdict in (ACCEPT, EDIT))
        self._write(f"{accepted} of {len(decisions)} operation(s) accepted.")
        return decisions


# --------------------------------------------------------------------------- #
# 8. The changelog
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class ChangelogEntry:
    """One proposed operation, the human's verdict on it, and what it did."""

    index: int
    type: str
    verdict: str
    applied: bool
    rationale: str
    note: str
    summary: str
    effect: OperationEffect | None = None
    reason: str = ""

    def to_json(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "type": self.type,
            "verdict": self.verdict,
            "applied": self.applied,
            "rationale": self.rationale,
            "note": self.note,
            "summary": self.summary,
            "reason": self.reason,
            "effect": self.effect.to_json() if self.effect is not None else None,
        }


@dataclass(frozen=True, slots=True)
class Changelog:
    """What was proposed, what the human decided, what was applied, and between which
    snapshots.

    The artefact a methods reviewer reads to answer "how did this codebook become that
    one, and who said so". Deliberately flat and JSON-shaped: `gaf.report` renders it,
    and never reaches into the slow loop's internals.
    """

    run_id: str
    checkpoint_id: str
    trigger: str
    at_response_count: int
    base_snapshot_id: str
    result_snapshot_id: str | None
    entries: list[ChangelogEntry]
    dropped: list[DroppedOperation]
    codes_before: int
    codes_after: int
    evidence_before: int
    evidence_after: int

    @property
    def applied(self) -> list[ChangelogEntry]:
        return [entry for entry in self.entries if entry.applied]

    @property
    def verdicts(self) -> dict[str, int]:
        counts = Counter(entry.verdict for entry in self.entries)
        return {verdict: counts.get(verdict, 0) for verdict in VERDICTS}

    @property
    def removed_code_names(self) -> list[str]:
        """Every code an applied operation removed. A removal is never implicit."""
        return sorted(
            {
                entry.effect.names.get(code_id, code_id)
                for entry in self.applied
                if entry.effect is not None
                for code_id in entry.effect.removed
            }
        )

    def to_json(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "checkpoint_id": self.checkpoint_id,
            "trigger": self.trigger,
            "at_response_count": self.at_response_count,
            "base_snapshot_id": self.base_snapshot_id,
            "result_snapshot_id": self.result_snapshot_id,
            "n_proposed": len(self.entries),
            "n_applied": len(self.applied),
            "verdicts": self.verdicts,
            "entries": [entry.to_json() for entry in self.entries],
            "dropped": [d.to_json() for d in self.dropped],
            "codes_before": self.codes_before,
            "codes_after": self.codes_after,
            "evidence_before": self.evidence_before,
            "evidence_after": self.evidence_after,
            "removed_code_names": self.removed_code_names,
        }

    def render(self) -> str:
        """The changelog as text, for the run report and for a reviewer's eye."""
        lines = [
            f"CHECKPOINT {self.checkpoint_id}  ({self.trigger}, "
            f"at {self.at_response_count} responses)",
            f"  base snapshot   {self.base_snapshot_id}",
            f"  result snapshot {self.result_snapshot_id or '(none — nothing applied)'}",
            f"  codes {self.codes_before} -> {self.codes_after}; "
            f"evidence {self.evidence_before} -> {self.evidence_after} quote(s)",
        ]
        for dropped in self.dropped:
            lines.append(
                f"  [{dropped.index}] {dropped.operation.type}: DROPPED IN VALIDATION — "
                f"{dropped.reason}"
            )
        for entry in self.entries:
            mark = "applied" if entry.applied else "not applied"
            lines.append(f"  [{entry.index}] {entry.type}: {entry.verdict.upper()} ({mark})")
            lines.append(f"        {entry.summary}")
            if entry.note:
                lines.append(f"        note: {entry.note}")
            if entry.reason:
                lines.append(f"        {entry.reason}")
        if self.removed_code_names:
            lines.append(f"  codes removed: {', '.join(self.removed_code_names)}")
        return "\n".join(lines)


# --------------------------------------------------------------------------- #
# 9. The checkpoint result
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class CheckpointResult:
    """One whole checkpoint: proposal, validation, decisions, outcome, changelog.

    JSON-serialisable end to end — `gaf.cli` and `gaf.report` render this and never the
    loop's internals. `codebook` is the input codebook itself when nothing was applied,
    so "a rejected checkpoint leaves the codebook byte-identical" is true by
    construction rather than by careful copying.
    """

    run_id: str
    checkpoint_id: str
    trigger: str
    status: str
    at_response_count: int
    base_snapshot_id: str
    proposal: RefactorProposal
    validation: ScriptValidation
    decisions: list[GateDecision]
    applied: bool
    codebook: Codebook
    snapshot_id: str | None
    changelog: Changelog
    report: CheckReport
    health: HealthMetrics | None = None

    @property
    def operations_applied(self) -> list[ChangelogEntry]:
        return self.changelog.applied

    def codebook_json(self) -> str:
        """The canonical serialisation — the bytes a no-op checkpoint must not change."""
        return self.codebook.to_json_str()

    def passed(self) -> bool:
        """True when validation and application produced no ERROR finding."""
        return self.report.passed()

    def to_json(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "checkpoint_id": self.checkpoint_id,
            "trigger": self.trigger,
            "status": self.status,
            "at_response_count": self.at_response_count,
            "base_snapshot_id": self.base_snapshot_id,
            "result_snapshot_id": self.snapshot_id,
            "applied": self.applied,
            "proposal": self.proposal.to_json(),
            "validation": self.validation.to_json(),
            "decisions": [decision.to_json() for decision in self.decisions],
            "changelog": self.changelog.to_json(),
            "codebook": self.codebook.to_json(),
            "findings": self.report.to_json(),
            "health": self.health.to_json() if self.health is not None else None,
        }


# --------------------------------------------------------------------------- #
# 10. The checkpoint itself
# --------------------------------------------------------------------------- #


def _health_scalars(metrics: HealthMetrics) -> dict[str, float]:
    """The scalar health row, for the `health_metrics` table. Name-sorted on write."""
    return {
        "n_codes": float(metrics.n_codes),
        "n_families": float(metrics.n_families),
        "n_leaves": float(metrics.n_leaves),
        "n_parents": float(metrics.n_parents),
        "leaf_ratio": metrics.leaf_ratio,
        "n_orphans": float(metrics.n_orphans),
        "orphan_ratio": metrics.orphan_ratio,
        "largest_family_share": metrics.largest_family_share,
        "family_balance_gini": metrics.family_balance_gini,
        "near_duplicate_pairs": float(metrics.near_duplicate_pairs),
        "new_codes": float(metrics.new_codes),
        "growth_rate": metrics.growth_rate,
        "evidence_per_code_mean": metrics.evidence_per_code.mean,
        "zero_evidence_codes": float(metrics.evidence_per_code.zero_evidence_codes),
    }


def _decision_index(
    decisions: Sequence[GateDecision], n_operations: int, report: CheckReport
) -> dict[int, GateDecision]:
    """Index decisions by operation, reporting anything the gate said that cannot apply.

    A decision for an operation that is not in the proposal is a finding rather than a
    crash — a gate is an interface a human sits behind, and a mistyped index must not
    take the checkpoint down. The last decision for an index wins, which is what
    correcting yourself means.
    """
    indexed: dict[int, GateDecision] = {}
    for decision in decisions:
        if not 0 <= decision.index < n_operations:
            report.add(
                CHECK_ID,
                Severity.WARN,
                "codebook",
                f"gate:{decision.index}",
                f"The gate returned a decision for operation {decision.index}, which is "
                f"not in a proposal of {n_operations} operation(s); ignored.",
                **{MARKER_KEY: "gate_index"},
                index=decision.index,
                verdict=decision.verdict,
            )
            continue
        indexed[decision.index] = decision
    return indexed


def _accepted_operations(
    proposal: RefactorProposal,
    indexed: Mapping[int, GateDecision],
    report: CheckReport,
) -> tuple[list[Operation], list[int], dict[int, str]]:
    """The operations the human let through, in proposal order.

    Silence is a rejection: an operation the gate returned no decision for is not
    applied. An ``edit`` without a replacement operation, or with an unrecognised
    verdict, is likewise a rejection with a finding — every ambiguity at this gate
    resolves toward "do not change the codebook".
    """
    operations: list[Operation] = []
    indices: list[int] = []
    reasons: dict[int, str] = {}
    for index, proposed in enumerate(proposal.script.operations):
        decision = indexed.get(index)
        if decision is None:
            reasons[index] = "no decision returned by the gate; rejected by default"
            continue
        verdict = decision.verdict.strip().casefold()
        if verdict == REJECT:
            reasons[index] = "rejected at the gate"
            continue
        if verdict == ACCEPT:
            operations.append(proposed)
            indices.append(index)
            continue
        if verdict == EDIT:
            if decision.operation is None:
                report.add(
                    CHECK_ID,
                    Severity.WARN,
                    "codebook",
                    f"op{index}:{proposed.type}",
                    f"Operation {index} was marked 'edit' with no replacement operation; "
                    "treated as a rejection.",
                    **{MARKER_KEY: "gate_edit_missing"},
                    index=index,
                )
                reasons[index] = "marked 'edit' with no replacement; rejected"
                continue
            operations.append(decision.operation)
            indices.append(index)
            continue
        report.add(
            CHECK_ID,
            Severity.WARN,
            "codebook",
            f"op{index}:{proposed.type}",
            f"Operation {index} carries an unrecognised verdict {decision.verdict!r}; "
            f"expected one of {VERDICTS}. Treated as a rejection.",
            **{MARKER_KEY: "gate_verdict"},
            index=index,
            verdict=decision.verdict,
        )
        reasons[index] = f"unrecognised verdict {decision.verdict!r}; rejected"
    return operations, indices, reasons


def run_checkpoint(
    *,
    board: Blackboard,
    config: RunConfig,
    codebook: Codebook,
    snapshot_id: str,
    agent: RefactorerAgent,
    embedder: Embedder,
    gate: Gate | None = None,
    trigger: str = "manual",
) -> CheckpointResult:
    """Run one slow-loop checkpoint: propose, validate, gate, apply, snapshot, record.

    `gate` defaults to `RejectAllGate`, which is the whole point: a checkpoint run with
    no human present proposes and records but changes nothing. Passing `ConsoleGate()`
    is what puts a person at the gate.

    `snapshot_id` names the frozen snapshot the proposal is made against; it must
    already be in the store, because a checkpoint's provenance is a snapshot the run
    actually wrote. `codebook` is the working codebook at this point in the run, which
    ADR-0021 allows to have moved on from the last snapshot the coders read; when the
    two disagree the mismatch is reported as a WARN rather than assumed away.

    Nothing is written to the codebook unless an operation was accepted. In particular
    **no snapshot is frozen for a checkpoint that applies nothing** — `snapshot_id` on
    the result is then `None`, and the returned `codebook` is the very object that came
    in.
    """
    resolved_gate: Gate = gate if gate is not None else RejectAllGate()
    board.register_run(config)
    if not board.snapshot_exists(snapshot_id):
        raise KeyError(
            f"no snapshot {snapshot_id!r} in this store; a checkpoint is proposed "
            "against a snapshot the run has already frozen."
        )
    log = board.audit(config.run_id)
    at_response_count = board.coded_response_count(config.run_id)
    corpus_ids = [response.id for response in board.read_responses()]
    report = CheckReport()

    # -- 1. health ------------------------------------------------------- #
    health = codebook_health(codebook, embedder, config.rules)
    board.write_health_metrics(
        run_id=config.run_id,
        at_response_count=at_response_count,
        metrics=_health_scalars(health),
    )
    log.emit(
        "checkpoint_started",
        scope="codebook",
        subject=snapshot_id,
        snapshot_id=snapshot_id,
        trigger=trigger,
        at_response_count=at_response_count,
        n_codes=len(codebook),
        near_duplicate_pairs=health.near_duplicate_pairs,
        space_id=embedder.space_id,
    )
    if not _matches_snapshot(board, snapshot_id, codebook):
        report.add(
            CHECK_ID,
            Severity.WARN,
            "codebook",
            snapshot_id,
            "The working codebook does not match the snapshot the proposal names; the "
            "refactorer sees the working codebook and the new snapshot descends from "
            f"{snapshot_id}. (ADR-0021 permits the two to differ within a batch.)",
            **{MARKER_KEY: "snapshot_drift"},
            snapshot_id=snapshot_id,
        )

    # -- 2. the proposal -------------------------------------------------- #
    context = RefactorContext(
        codebook=codebook,
        snapshot_id=snapshot_id,
        usage=usage_from_codebook(codebook),
        health=health.to_json(),
    )
    script = agent.propose(context)
    board.write_llm_call(
        script.result, run_id=config.run_id, role="refactorer", subject=script.subject
    )

    # -- 3. deterministic validation, before any human sees it ------------ #
    validation = validate_script(
        script.operations,
        codebook,
        config.rules,
        corpus_response_ids=corpus_ids,
        snapshot_id=snapshot_id,
    )
    report.extend(validation.report)
    for dropped in validation.dropped:
        log.emit(
            "operation_dropped",
            scope="codebook",
            subject=f"op{dropped.index}:{dropped.operation.type}",
            snapshot_id=snapshot_id,
            index=dropped.index,
            marker=dropped.marker,
            reason=dropped.reason,
            operation=dropped.operation.to_json(),
        )

    validated = replace(script, operations=validation.kept)
    proposal = RefactorProposal(
        snapshot_id=snapshot_id,
        trigger=trigger,
        script=validated,
        diffs=build_diff(validation.kept, codebook),
        validation=validation,
        health=health,
    )
    record = board.write_checkpoint(
        run_id=config.run_id,
        at_response_count=at_response_count,
        trigger=trigger,
        base_snapshot_id=snapshot_id,
        proposal=proposal.to_json(),
        status="proposed",
    )
    log.emit(
        "checkpoint_proposed",
        scope="codebook",
        subject=record.checkpoint_id,
        snapshot_id=snapshot_id,
        checkpoint_id=record.checkpoint_id,
        n_proposed=validation.n_proposed,
        n_valid=len(validation.kept),
        n_dropped=len(validation.dropped),
        types=validated.types(),
        prompt_version=validated.prompt_version,
        fail_safe=validated.fail_safe,
    )

    # -- 4. the human gate ------------------------------------------------ #
    decisions = list(resolved_gate.review(proposal))
    indexed = _decision_index(decisions, len(validation.kept), report)
    chosen, chosen_indices, reasons = _accepted_operations(proposal, indexed, report)

    # A human's edit is an operation like any other and is validated like any other:
    # the gate may not put into the codebook something the machine would have been
    # stopped from putting there.
    accepted = validate_script(
        chosen,
        codebook,
        config.rules,
        corpus_response_ids=corpus_ids,
        snapshot_id=snapshot_id,
    )
    report.extend(accepted.report)
    surviving: list[Operation] = []
    surviving_indices: list[int] = []
    dropped_after_gate = {d.index for d in accepted.dropped}
    for position, operation in enumerate(chosen):
        if position in dropped_after_gate:
            reason = next(d.reason for d in accepted.dropped if d.index == position)
            reasons[chosen_indices[position]] = f"accepted but dropped in validation: {reason}"
            continue
        surviving.append(operation)
        surviving_indices.append(chosen_indices[position])

    # -- 5. apply, snapshot, changelog ------------------------------------ #
    applied_script = apply_operations(codebook, surviving, snapshot_id=snapshot_id)
    changed = bool(surviving) and applied_script.codebook.to_json_str() != codebook.to_json_str()
    result_codebook = applied_script.codebook if changed else codebook

    snapshot: Snapshot | None = None
    if changed:
        snapshot = board.freeze_codebook(
            result_codebook,
            run_id=config.run_id,
            parent_id=snapshot_id,
            reason="checkpoint_apply",
        )
        log.emit(
            "snapshot_frozen",
            scope="codebook",
            subject=snapshot.snapshot_id,
            snapshot_id=snapshot.snapshot_id,
            parent_id=snapshot_id,
            reason="checkpoint_apply",
            code_count=snapshot.code_count,
        )

    effects = dict(zip(surviving_indices, applied_script.effects, strict=True))
    entries: list[ChangelogEntry] = []
    for index, operation in enumerate(proposal.script.operations):
        decision = indexed.get(index)
        verdict = decision.verdict if decision is not None else REJECT
        effect = effects.get(index)
        entries.append(
            ChangelogEntry(
                index=index,
                type=operation.type,
                verdict=verdict,
                applied=effect is not None,
                rationale=operation.rationale,
                note=decision.note if decision is not None else "",
                summary=(
                    effect.summary
                    if effect is not None
                    else proposal.diffs[index].summary
                ),
                effect=effect,
                reason=reasons.get(index, ""),
            )
        )
        log.emit(
            "operation_applied" if effect is not None else "operation_rejected",
            scope="codebook",
            subject=f"op{index}:{operation.type}",
            snapshot_id=snapshot.snapshot_id if snapshot is not None else snapshot_id,
            index=index,
            verdict=verdict,
            note=decision.note if decision is not None else "",
            summary=entries[-1].summary,
            reason=reasons.get(index, ""),
            effect=effect.to_json() if effect is not None else None,
        )

    changelog = Changelog(
        run_id=config.run_id,
        checkpoint_id=record.checkpoint_id,
        trigger=trigger,
        at_response_count=at_response_count,
        base_snapshot_id=snapshot_id,
        result_snapshot_id=snapshot.snapshot_id if snapshot is not None else None,
        entries=entries,
        dropped=list(validation.dropped),
        codes_before=len(codebook),
        codes_after=len(result_codebook),
        evidence_before=sum(evidence_pairs(codebook).values()),
        evidence_after=sum(evidence_pairs(result_codebook).values()),
    )

    if changed:
        status = "applied"
    elif proposal.is_noop():
        # Nothing structural was on the table. A checkpoint that found the codebook
        # healthy is a legitimate outcome, and it is not the same fact as a refusal.
        status = "noop"
    else:
        status = "rejected"
    board.decide_checkpoint(
        record.checkpoint_id,
        status=status,
        decisions=[decision.to_json() for decision in decisions],
        result_snapshot_id=snapshot.snapshot_id if snapshot is not None else None,
    )
    board.write_report(
        report,
        run_id=config.run_id,
        snapshot_id=snapshot.snapshot_id if snapshot is not None else snapshot_id,
    )
    log.emit(
        "checkpoint_decided",
        scope="codebook",
        subject=record.checkpoint_id,
        snapshot_id=snapshot.snapshot_id if snapshot is not None else snapshot_id,
        checkpoint_id=record.checkpoint_id,
        status=status,
        applied=changed,
        n_applied=len(surviving),
        n_rejected=len(proposal.script.operations) - len(surviving),
        verdicts=changelog.verdicts,
        result_snapshot_id=snapshot.snapshot_id if snapshot is not None else None,
        codes_before=changelog.codes_before,
        codes_after=changelog.codes_after,
        evidence_before=changelog.evidence_before,
        evidence_after=changelog.evidence_after,
        removed_code_names=changelog.removed_code_names,
    )

    return CheckpointResult(
        run_id=config.run_id,
        checkpoint_id=record.checkpoint_id,
        trigger=trigger,
        status=status,
        at_response_count=at_response_count,
        base_snapshot_id=snapshot_id,
        proposal=proposal,
        validation=validation,
        decisions=decisions,
        applied=changed,
        codebook=result_codebook,
        snapshot_id=snapshot.snapshot_id if snapshot is not None else None,
        changelog=changelog,
        report=report,
        health=health,
    )


def _matches_snapshot(board: Blackboard, snapshot_id: str, codebook: Codebook) -> bool:
    """Whether the working codebook is byte-identical to the named stored snapshot."""
    try:
        stored = board.read_snapshot(snapshot_id)
    except KeyError:  # pragma: no cover - run_checkpoint checks existence first
        return False
    return stored.codebook_json == codebook.to_json_str()
