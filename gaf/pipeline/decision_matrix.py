"""The decision matrix — which loop takes which decision, as data rather than prose.

The PI asked for a matrix between the fast loop and the slow loop. A page of prose
would answer him once and then rot, because nothing would make it false when the code
changed. So the matrix is a tuple of frozen :class:`DecisionRule` rows, and three
properties keep it honest:

* **it is rendered, not written** — a row's ``condition`` is a template filled in from
  the `RunConfig` in force, so a matrix printed for a run states that run's thresholds
  and never the defaults;
* **it cannot drift** — every row names the function that implements it as
  ``module:function``, and `tests/test_decision_matrix.py` resolves each one, then
  checks that every route `gaf.pipeline.router` can return, every member of
  `gaf.pipeline.slow_loop.TRIGGERS` and every member of `gaf.models.OPERATION_TYPES` is
  covered by some row. A new route or a renamed function fails by name;
* **it is the same object the loop uses** — `evaluate_handover` fires the handover rows
  of this very tuple at each batch boundary, so the run's decision trace and the
  printed matrix are two views of one thing rather than a description and a behaviour.

**Handover is a third column, not a third loop.** The two loops of the architecture
diagram are still two. But "should the slow loop wake up" is a decision taken *between*
them, by neither: the fast loop measures and reports and never blocks, the slow loop
needs a human at a terminal, and what sits in the middle is a deterministic rule over
health, growth and spacing. Giving that rule its own `loop` value is what lets the
matrix say where it happens; `gaf.pipeline.slow_loop.TRIGGERS` is the closed vocabulary
of its outcomes.

**This module decides; it does not measure.** `evaluate_handover` delegates every
number to `gaf.checks.health` (near-duplicate pairs, new codes, spacing, the floor) and
`gaf.checks.growth` (the growth curve and the spike rule) and then applies
`first_trigger`, the only code that implements the documented precedence —
health, spike, floor, cadence — that `gaf.pipeline.slow_loop.should_checkpoint` also
calls. Two entry points into one precedence, so the two cannot disagree.

Validation principle: **transparency** — a methods reviewer can read every decision the
system takes, the condition it takes it under, who takes it and which audit event
records it, from one table generated out of the code that takes them.
"""

from __future__ import annotations

import importlib
from collections.abc import Sequence
from dataclasses import dataclass
from functools import reduce
from typing import Any

from gaf.checks.growth import GrowthCurve, Spike, spike_at
from gaf.checks.health import checkpoint_signals, codebook_health
from gaf.config import RunConfig
from gaf.embed.protocol import Embedder
from gaf.models import Codebook

__all__ = [
    "CHECKPOINT_DUE",
    "CONTINUE",
    "DECIDED_BY",
    "DECISION_MATRIX",
    "HANDOVER_RULES",
    "LOOPS",
    "TRIGGER_PRECEDENCE",
    "VERDICTS",
    "DecisionRule",
    "HandoverEvaluation",
    "condition_values",
    "evaluate_handover",
    "first_trigger",
    "matrix_to_json",
    "render_matrix_markdown",
    "resolve_source",
    "rule",
    "trace_to_checkpoint_due",
]

#: Where a decision is taken. ``handover`` is the batch-boundary question "is the slow
#: loop due", which belongs to neither loop — see the module docstring.
LOOPS: tuple[str, ...] = ("fast", "handover", "slow")

#: Who takes it. ``deterministic`` is plain Python; the rest are the three LLM roles
#: and the person at the gate.
DECIDED_BY: tuple[str, ...] = ("deterministic", "coder", "judge", "refactorer", "human")

#: The two verdicts one handover evaluation can reach.
CONTINUE = "continue"
CHECKPOINT_DUE = "checkpoint_due"
VERDICTS: tuple[str, ...] = (CONTINUE, CHECKPOINT_DUE)

#: The documented precedence among the handover triggers. Health first because a
#: codebook already carrying near-duplicates is the most specific thing that can be
#: wrong with it; spike next because it is the newer and less calibrated rule and
#: should not mask the one that has been in the build since Wave 3; the floor and the
#: cadence last because they are schedules and say nothing about this codebook.
TRIGGER_PRECEDENCE: tuple[str, ...] = ("health", "spike", "floor", "cadence")


# --------------------------------------------------------------------------- #
# A row
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class DecisionRule:
    """One row of the matrix: a decision, where it is taken, and what decides it.

    ``condition`` is a `str.format` template over `condition_values`, not a finished
    sentence: the numbers belong to a run, and a row that hard-coded 0.80 would be
    wrong for every run that moved tau_high. ``covers`` names the closed-vocabulary
    tokens this row accounts for — route values, trigger names, operation types — which
    is what makes "the matrix is complete" a test rather than a claim.
    """

    id: str
    decision: str
    loop: str
    decided_by: str
    condition: str
    outcome: str
    audit_event: str
    source: str
    covers: tuple[str, ...] = ()

    def render_condition(self, config: RunConfig | None = None) -> str:
        """The condition with this run's numbers in it, or the raw template."""
        if config is None:
            return self.condition
        return self.condition.format(**condition_values(config))

    def to_json(self, config: RunConfig | None = None) -> dict[str, Any]:
        return {
            "id": self.id,
            "decision": self.decision,
            "loop": self.loop,
            "decided_by": self.decided_by,
            "condition": self.render_condition(config),
            "outcome": self.outcome,
            "audit_event": self.audit_event,
            "source": self.source,
            "covers": list(self.covers),
        }


def condition_values(config: RunConfig) -> dict[str, Any]:
    """Every number a condition template may name, from the config in force.

    One mapping rather than a format call per row, so that adding a threshold to a row
    is adding a name here and nothing else.
    """
    rules, policy = config.rules, config.checkpoints
    return {
        "tau_high": rules.tau_high,
        "tau_low": rules.tau_low,
        "tau_fit": rules.tau_fit,
        "fuzzy_threshold": rules.fuzzy_threshold,
        "max_codes_per_segment": rules.max_codes_per_segment,
        "min_codes_per_response": rules.min_codes_per_response,
        "max_codes_per_response": rules.max_codes_per_response,
        "hierarchy_depth": rules.hierarchy_depth,
        "batch_size": config.batch_size,
        "retrieval_top_k": config.retrieval_top_k,
        "mode": policy.mode,
        "max_near_duplicate_pairs": policy.max_near_duplicate_pairs,
        "max_new_codes_per_batch": policy.max_new_codes_per_batch,
        "min_responses_between_checkpoints": policy.min_responses_between_checkpoints,
        "hard_floor_responses": policy.hard_floor_responses,
        "fixed_cadence": ", ".join(str(n) for n in policy.fixed_cadence),
        "spike_factor": policy.spike_factor,
        "spike_window": policy.spike_window,
        "spike_min_new_codes": policy.spike_min_new_codes,
    }


def resolve_source(source: str) -> Any:
    """Import and return the callable a row's ``source`` names. Raises, never guesses.

    ``module:attribute`` — dotted attributes are allowed so a row can point at a method
    (``…:ConsoleGate.review``) rather than at the module that happens to contain it.
    """
    module_name, separator, attribute = source.partition(":")
    if not separator or not module_name or not attribute:
        raise ValueError(f"a decision rule source must be 'module:function'; got {source!r}")
    module = importlib.import_module(module_name)
    try:
        target = reduce(getattr, attribute.split("."), module)
    except AttributeError as exc:
        raise ValueError(
            f"{module_name} has no attribute {attribute!r}; the decision matrix names a "
            "function that no longer exists."
        ) from exc
    if not callable(target):
        raise ValueError(f"{source} is not callable; a decision rule must name a function.")
    return target


# --------------------------------------------------------------------------- #
# The matrix
# --------------------------------------------------------------------------- #

_ROUTER = "gaf.pipeline.router"
_SLOW = "gaf.pipeline.slow_loop"

DECISION_MATRIX: tuple[DecisionRule, ...] = (
    # -- fast loop: prep ---------------------------------------------------- #
    DecisionRule(
        id="fast.duplicate_response",
        decision="Is this response a verbatim repeat of one already coded?",
        loop="fast",
        decided_by="deterministic",
        condition="the normalised response hashes to a digest an earlier response already produced",
        outcome=(
            "flagged as a duplicate on the response's outcome row and in the log; the "
            "response is still coded, because dropping it would silently change the "
            "denominator of every rate in the report"
        ),
        audit_event="duplicate_response",
        source="gaf.pipeline.prep:dedup_precheck",
    ),
    # -- fast loop: structural checks --------------------------------------- #
    DecisionRule(
        id="fast.structural_drop",
        decision="Does a proposed candidate survive the structural checks?",
        loop="fast",
        decided_by="deterministic",
        condition=(
            "S1 (a name, a description and at least one quote) or S2 (the quote occurs "
            "in the response it cites, at or above a fuzzy similarity of "
            "{fuzzy_threshold}) reports an ERROR"
        ),
        outcome=(
            "the candidate is dropped before any embedding or model call; S2b, S3, S4 "
            "and S5 flag and never drop"
        ),
        audit_event="candidate_dropped",
        source="gaf.checks.structural:check_candidates",
    ),
    # -- fast loop: cross-coder agreement (M1) ------------------------------ #
    DecisionRule(
        id="fast.accept_agreed",
        decision="What survives when the two coders propose the same code?",
        loop="fast",
        decided_by="deterministic",
        condition="the Hungarian-matched cross-coder score is at or above tau_high ({tau_high})",
        outcome=(
            "one candidate, carrying both coders' evidence. The common case, and it "
            "costs no model call"
        ),
        audit_event="candidates_accepted",
        source=f"{_ROUTER}:accept_candidates",
    ),
    DecisionRule(
        id="fast.accept_grey",
        decision="What happens to a cross-coder pair in the grey band?",
        loop="fast",
        decided_by="judge",
        condition="the cross-coder score lies between tau_low ({tau_low}) and tau_high ({tau_high})",
        outcome=(
            "the only pair that reaches the frontier judge. DROP accepts coder A's "
            "candidate and drops coder B's; any other verdict, an unreadable reply and "
            "the offline case with no judge all keep both"
        ),
        audit_event="judge_consulted",
        source=f"{_ROUTER}:escalates",
    ),
    DecisionRule(
        id="fast.accept_disputed",
        decision="What happens to a cross-coder pair below tau_low?",
        loop="fast",
        decided_by="deterministic",
        condition="the cross-coder score is below tau_low ({tau_low})",
        outcome=(
            "both candidates are kept and flagged, never escalated: the coders named "
            "two different things, and choosing between them is a meaning judgment the "
            "fast loop is not allowed to make"
        ),
        audit_event="candidates_accepted",
        source=f"{_ROUTER}:accept_candidates",
    ),
    DecisionRule(
        id="fast.accept_unmatched",
        decision="What happens to a code only one coder proposed?",
        loop="fast",
        decided_by="deterministic",
        condition="M1's Hungarian assignment leaves the candidate unmatched",
        outcome=(
            "accepted and flagged as unmatched. A code one coder saw and the other did "
            "not is the disagreement the two-coder design exists to surface"
        ),
        audit_event="candidates_accepted",
        source=f"{_ROUTER}:accept_candidates",
    ),
    # -- fast loop: code-evidence fit (M3) ---------------------------------- #
    DecisionRule(
        id="fast.fit_below_tau_fit",
        decision="Does a quote actually evidence the code it was offered for?",
        loop="fast",
        decided_by="judge",
        condition="the code-to-evidence cosine fit is below tau_fit ({tau_fit})",
        outcome=(
            "the pairing is put to the judge; a quote ruled UNNECESSARY is removed, and "
            "a candidate left with no verified quote is dropped. Offline this escalates "
            "nearly every pairing, so those counts are artefacts of the stand-in "
            "embedder (ADR-0019)"
        ),
        audit_event="candidate_dropped",
        source="gaf.checks.semantic:check_code_evidence_fit",
    ),
    # -- fast loop: integration routing (M2) -------------------------------- #
    DecisionRule(
        id="fast.route_merge",
        decision="Does an accepted candidate fold into an existing code?",
        loop="fast",
        decided_by="deterministic",
        condition="the best retrieved code scores at or above tau_high ({tau_high})",
        outcome=(
            "MERGE: the target keeps its id, name, description and parent and gains "
            "this candidate's evidence. Merging evidence is integration; rewriting a "
            "description would be restructuring"
        ),
        audit_event="code_merged",
        source=f"{_ROUTER}:integrate",
        covers=("MERGE",),
    ),
    DecisionRule(
        id="fast.route_create",
        decision="Is an accepted candidate a genuinely new code?",
        loop="fast",
        decided_by="deterministic",
        condition="the best retrieved code scores below tau_low ({tau_low})",
        outcome=(
            "CREATE: a new code, its id the content hash of its name, its provenance "
            "the snapshot the batch's coders read. Its parent is the family node only "
            "if one already exists — the fast loop does not invent hierarchy"
        ),
        audit_event="code_created",
        source=f"{_ROUTER}:integrate",
        covers=("CREATE",),
    ),
    DecisionRule(
        id="fast.route_judge",
        decision="What happens when the geometry cannot tell merge from create?",
        loop="fast",
        decided_by="judge",
        condition="the best retrieved code scores between tau_low ({tau_low}) and tau_high ({tau_high})",
        outcome=(
            "JUDGE: the judge's MERGE is honoured; every other verdict, and the offline "
            "case with no judge, CREATEs. A spurious code is visible to M4 and "
            "recoverable at the gate; a spurious merge destroys a distinction silently"
        ),
        audit_event="route_chosen",
        source=f"{_ROUTER}:integration_actions",
        covers=("JUDGE",),
    ),
    # -- handover ------------------------------------------------------------ #
    DecisionRule(
        id="handover.near_duplicates",
        decision="Has the codebook accumulated near-duplicate leaves?",
        loop="handover",
        decided_by="deterministic",
        condition=(
            "mode is event_driven, M4 counts more than {max_near_duplicate_pairs} "
            "near-duplicate leaf pairs, and spacing is satisfied"
        ),
        outcome="verdict checkpoint_due under trigger `health`",
        audit_event="checkpoint_evaluated",
        source="gaf.checks.health:checkpoint_signals",
        covers=("health",),
    ),
    DecisionRule(
        id="handover.new_codes",
        decision="Did this batch admit too many codes in absolute terms?",
        loop="handover",
        decided_by="deterministic",
        condition=(
            "mode is event_driven, the batch admitted more than "
            "{max_new_codes_per_batch} new codes, and spacing is satisfied"
        ),
        outcome="verdict checkpoint_due under trigger `health`",
        audit_event="checkpoint_evaluated",
        source="gaf.checks.health:checkpoint_signals",
        covers=("health",),
    ),
    DecisionRule(
        id="handover.spike",
        decision="Did this batch admit far more codes than the batches just before it?",
        loop="handover",
        decided_by="deterministic",
        condition=(
            "mode is event_driven, the batch admitted at least {spike_min_new_codes} "
            "new codes and at least {spike_factor}x the median of the previous "
            "{spike_window} batches, and spacing is satisfied. The first "
            "{spike_window} batches have no baseline and do not spike at all: "
            "`handover.new_codes` is the rule that speaks there, and this one would "
            "only repeat it"
        ),
        outcome=(
            "verdict checkpoint_due under trigger `spike`. The defaults are "
            "uncalibrated (ADR-0033)"
        ),
        audit_event="checkpoint_evaluated",
        source="gaf.checks.growth:detect_spikes",
        covers=("spike",),
    ),
    DecisionRule(
        id="handover.floor",
        decision="Has a quiet codebook gone too long without a human look?",
        loop="handover",
        decided_by="deterministic",
        condition=(
            "{hard_floor_responses} responses have been coded **since the last "
            "checkpoint**, whatever the codebook looks like"
        ),
        outcome=(
            "verdict checkpoint_due under trigger `floor`. Not held by spacing: the "
            "floor exists precisely for the run where nothing else ever fires. Measured "
            "since the last checkpoint, so taking one clears it; measured from the "
            "start of the run it would latch on and report a checkpoint due at every "
            "later batch of every later run (ADR-0033, R1 I1)"
        ),
        audit_event="checkpoint_evaluated",
        source="gaf.checks.health:checkpoint_signals",
        covers=("floor",),
    ),
    DecisionRule(
        id="handover.cadence",
        decision="Is this one of the scheduled checkpoints?",
        loop="handover",
        decided_by="deterministic",
        condition="mode is fixed and the running total of responses coded is one of {fixed_cadence}",
        outcome="verdict checkpoint_due under trigger `cadence` (the predecessor's schedule)",
        audit_event="checkpoint_evaluated",
        source=f"{_SLOW}:should_checkpoint",
        covers=("cadence",),
    ),
    DecisionRule(
        id="handover.spacing_hold",
        decision="Has enough been coded since the last checkpoint for another to be worth it?",
        loop="handover",
        decided_by="deterministic",
        condition="fewer than {min_responses_between_checkpoints} responses since the last checkpoint",
        outcome=(
            "every event trigger — health, new codes, spike — is held: the evaluation "
            "names the held rule and its reason and returns verdict continue. The "
            "floor and the cadence are not held"
        ),
        audit_event="checkpoint_evaluated",
        source="gaf.pipeline.decision_matrix:evaluate_handover",
        covers=("none",),
    ),
    DecisionRule(
        id="handover.manual",
        decision="May an operator open the gate with nothing firing?",
        loop="handover",
        decided_by="human",
        condition="the operator runs `gaf checkpoint` and supplies the trigger themselves",
        outcome=(
            "a checkpoint runs under trigger `manual`. The fast loop never blocks for "
            "the gate, so this is how a person acts on a checkpoint that is due"
        ),
        audit_event="checkpoint_started",
        source=f"{_SLOW}:run_checkpoint",
        covers=("manual",),
    ),
    # -- slow loop ----------------------------------------------------------- #
    DecisionRule(
        id="slow.proposal",
        decision="What structural edits does the codebook need?",
        loop="slow",
        decided_by="refactorer",
        condition="a checkpoint has fired and the whole codebook plus usage statistics is assembled",
        outcome=(
            "an edit script. The Refactorer proposes and never applies; this is a "
            "creation task, which is where the Vaccaro et al. meta-analysis finds "
            "human-AI pairing helps"
        ),
        audit_event="checkpoint_proposed",
        source="gaf.agents.refactorer:RefactorerAgent.propose",
    ),
    DecisionRule(
        id="slow.validation_drop",
        decision="Could this operation be applied at all?",
        loop="slow",
        decided_by="deterministic",
        condition=(
            "the operation's shape, targets or name collide, or the codebook it would "
            "produce fails S6 — including a hierarchy deeper than {hierarchy_depth}"
        ),
        outcome=(
            "dropped with a finding before any human sees it, and the valid operations "
            "beside it still apply: one hallucinated row must not cost five good ones"
        ),
        audit_event="operation_dropped",
        source=f"{_SLOW}:validate_script",
    ),
    DecisionRule(
        id="slow.gate_accept",
        decision="Does this operation go into the codebook?",
        loop="slow",
        decided_by="human",
        condition="the person at the gate returns `accept` for this operation",
        outcome="the operation is applied. Silence, an unreadable verdict and no human at all all reject",
        audit_event="operation_applied",
        source=f"{_SLOW}:ConsoleGate.review",
    ),
    DecisionRule(
        id="slow.gate_reject",
        decision="Does this operation go into the codebook?",
        loop="slow",
        decided_by="human",
        condition="the person returns `reject`, returns nothing, or no human is present",
        outcome=(
            "nothing is applied and the codebook is byte-identical. A machine that "
            "disposes of its own proposals when nobody is watching is the failure the "
            "gate exists to prevent (ADR-0004)"
        ),
        audit_event="operation_rejected",
        source=f"{_SLOW}:RejectAllGate.review",
    ),
    DecisionRule(
        id="slow.gate_edit",
        decision="May the person replace the operation with their own?",
        loop="slow",
        decided_by="human",
        condition="the person returns `edit` with a replacement operation",
        outcome=(
            "the replacement is validated exactly as the machine's was, then applied. "
            "An `edit` with no replacement rejects"
        ),
        audit_event="operation_applied",
        source=f"{_SLOW}:ConsoleGate.review",
    ),
    DecisionRule(
        id="slow.op_create",
        decision="Admit a code the coders never proposed.",
        loop="slow",
        decided_by="human",
        condition="an accepted `create` operation names a new code and its parent",
        outcome="a new code, its provenance the base snapshot the proposal was made against",
        audit_event="operation_applied",
        source=f"{_SLOW}:apply_operations",
        covers=("create",),
    ),
    DecisionRule(
        id="slow.op_merge",
        decision="Fold two codes that turned out to be one.",
        loop="slow",
        decided_by="human",
        condition="an accepted `merge` operation names two or more existing codes",
        outcome=(
            "merge-with-re-examination: every source's evidence carries into the "
            "target, and an apply that lost a quote raises rather than reaching a "
            "snapshot"
        ),
        audit_event="operation_applied",
        source=f"{_SLOW}:apply_operations",
        covers=("merge",),
    ),
    DecisionRule(
        id="slow.op_split",
        decision="Break an overloaded code into the concepts it was carrying.",
        loop="slow",
        decided_by="human",
        condition="an accepted `split` operation names one code and the codes to distribute it into",
        outcome=(
            "the target's evidence is distributed across the resulting codes and none "
            "is dropped. The predecessor had no split, and that absence is the "
            "documented cause of its codebook flattening"
        ),
        audit_event="operation_applied",
        source=f"{_SLOW}:apply_operations",
        covers=("split",),
    ),
    DecisionRule(
        id="slow.op_reparent",
        decision="Move a code under a different family.",
        loop="slow",
        decided_by="human",
        condition="an accepted `reparent` operation names a code and its new parent",
        outcome=(
            "the code's parent and name change together, so the derived family and the "
            "explicit parent_id stay in agreement and S6 still passes"
        ),
        audit_event="operation_applied",
        source=f"{_SLOW}:apply_operations",
        covers=("reparent",),
    ),
    DecisionRule(
        id="slow.op_rename",
        decision="Correct a code's name without changing what it means.",
        loop="slow",
        decided_by="human",
        condition="an accepted `rename` operation names a code and its new name",
        outcome="the code keeps its evidence; a rename reads as one new and one lost code on the health row",
        audit_event="operation_applied",
        source=f"{_SLOW}:apply_operations",
        covers=("rename",),
    ),
    DecisionRule(
        id="slow.op_noop",
        decision="Record that the Refactorer looked and found nothing to change.",
        loop="slow",
        decided_by="refactorer",
        condition="the proposed operation is `noop`",
        outcome=(
            "no structural change, and the checkpoint is recorded as `noop` rather "
            "than `rejected`: a codebook found healthy is not the same fact as a "
            "refusal"
        ),
        audit_event="operation_applied",
        source=f"{_SLOW}:apply_operations",
        covers=("noop",),
    ),
    DecisionRule(
        id="slow.apply_and_snapshot",
        decision="What becomes of the codebook the accepted operations produce?",
        loop="slow",
        decided_by="deterministic",
        condition="at least one accepted operation changed the codebook's bytes",
        outcome=(
            "a new snapshot, content-addressed, its parent the base snapshot, plus a "
            "changelog naming both ids. An unchanged codebook writes no snapshot at all"
        ),
        audit_event="snapshot_frozen",
        source="gaf.store.snapshot:freeze",
    ),
)

#: The rows `evaluate_handover` may fire. Derived, so a new handover row is picked up.
HANDOVER_RULES: tuple[DecisionRule, ...] = tuple(
    row for row in DECISION_MATRIX if row.loop == "handover"
)

_BY_ID: dict[str, DecisionRule] = {row.id: row for row in DECISION_MATRIX}


def rule(rule_id: str) -> DecisionRule:
    """One row by id. Raises rather than returning `None`: a caller naming a rule that
    does not exist has a bug, not an empty result."""
    try:
        return _BY_ID[rule_id]
    except KeyError:
        raise KeyError(f"no decision rule with id {rule_id!r}") from None


# --------------------------------------------------------------------------- #
# Renderers
# --------------------------------------------------------------------------- #


def matrix_to_json(config: RunConfig) -> dict[str, Any]:
    """The whole matrix, with every condition rendered against this run's numbers."""
    return {
        "loops": list(LOOPS),
        "decided_by": list(DECIDED_BY),
        "trigger_precedence": list(TRIGGER_PRECEDENCE),
        "verdicts": list(VERDICTS),
        "n_rules": len(DECISION_MATRIX),
        "thresholds": condition_values(config),
        "rules": [row.to_json(config) for row in DECISION_MATRIX],
    }


_LOOP_HEADINGS: dict[str, tuple[str, str]] = {
    "fast": (
        "Fast loop — per response",
        "Cheap, parallel, never blocking, and it never restructures the codebook.",
    ),
    "handover": (
        "Handover — per batch boundary",
        "Neither loop: the deterministic question of whether the slow loop is due. "
        "Evaluated at every batch boundary and reported; the fast loop never blocks "
        "for it.",
    ),
    "slow": (
        "Slow loop — per checkpoint",
        "Rare, expensive, human-gated, and the only place the codebook changes "
        "structurally.",
    ),
}


def render_matrix_markdown(config: RunConfig) -> str:
    """The matrix as Markdown, one table per loop. Pure and deterministic.

    No wall clock, no run id: the same configuration renders the same bytes, so this
    file can sit beside a run report and be diffed against another run's.
    """
    values = condition_values(config)
    lines = [
        "# Decision matrix — fast loop, handover, slow loop",
        "",
        "Every decision this pipeline takes, where it is taken, what decides it and "
        "which audit event records it. Generated from "
        "`gaf.pipeline.decision_matrix.DECISION_MATRIX`, with the thresholds of the "
        "run it was generated for: a row's condition is not a description of the code, "
        "it is the code's own numbers.",
        "",
        f"Checkpoint mode `{values['mode']}`; batch size {values['batch_size']}; "
        f"tau_high {values['tau_high']}, tau_low {values['tau_low']}, "
        f"tau_fit {values['tau_fit']}.",
        "",
        "Trigger precedence when several handover rows fire at once: "
        + " > ".join(f"`{name}`" for name in TRIGGER_PRECEDENCE)
        + ".",
        "",
    ]
    for loop in LOOPS:
        rows = [row for row in DECISION_MATRIX if row.loop == loop]
        if not rows:  # pragma: no cover - every loop has rows, and a test says so
            continue
        title, blurb = _LOOP_HEADINGS[loop]
        lines.extend(
            [
                f"## {title}",
                "",
                blurb,
                "",
                "| rule | decision | decided by | condition | outcome | audit event | source |",
                "|---|---|---|---|---|---|---|",
            ]
        )
        for row in rows:
            cells = [
                f"`{row.id}`",
                _cell(row.decision),
                f"`{row.decided_by}`",
                _cell(row.render_condition(config)),
                _cell(row.outcome),
                f"`{row.audit_event}`",
                f"`{row.source}`",
            ]
            lines.append("| " + " | ".join(cells) + " |")
        lines.append("")
    return "\n".join(lines) + "\n"


def _cell(text: str) -> str:
    """One table cell: pipes escaped, newlines folded, so a row stays a row."""
    return " ".join(text.replace("|", "\\|").split())


# --------------------------------------------------------------------------- #
# One evaluation of the handover rows
# --------------------------------------------------------------------------- #


def first_trigger(*, health: bool, spike: bool, floor: bool, cadence: bool) -> str:
    """The trigger that names this checkpoint, in `TRIGGER_PRECEDENCE` order.

    The one place the precedence is implemented. `should_checkpoint` and
    `evaluate_handover` both call it, which is the only way to be sure the run's
    decision trace and a later `gaf checkpoint` agree about why the gate opened.
    Returns ``"none"`` when nothing fired, which is a member of
    `gaf.pipeline.slow_loop.TRIGGERS` and the value the audit log records.
    """
    fired = {"health": health, "spike": spike, "floor": floor, "cadence": cadence}
    for name in TRIGGER_PRECEDENCE:
        if fired[name]:
            return name
    return "none"


@dataclass(frozen=True, slots=True)
class HandoverEvaluation:
    """One evaluation of the handover rows, at one batch boundary.

    Carries the numbers it decided on as well as the verdict, because "why did the
    gate come due at batch 4" must be a recorded fact about the run rather than
    something re-derived from metrics that have since moved on — the same reason
    `gaf.pipeline.slow_loop.CheckpointTrigger` carries its reason.
    """

    batch: int
    responses_coded: int
    responses_in_batch: int
    responses_since_checkpoint: int
    new_codes: int
    cumulative_codes: int
    near_duplicate_pairs: int
    spike: Spike | None
    fired: tuple[str, ...]
    held: tuple[str, ...]
    trigger: str
    verdict: str
    reason: str

    @property
    def checkpoint_due(self) -> bool:
        return self.verdict == CHECKPOINT_DUE

    def to_json(self) -> dict[str, Any]:
        return {
            "batch": self.batch,
            "responses_coded": self.responses_coded,
            "responses_in_batch": self.responses_in_batch,
            "responses_since_checkpoint": self.responses_since_checkpoint,
            "new_codes": self.new_codes,
            "cumulative_codes": self.cumulative_codes,
            "near_duplicate_pairs": self.near_duplicate_pairs,
            "spike": self.spike.to_json() if self.spike is not None else None,
            "fired": list(self.fired),
            "held": list(self.held),
            "trigger": self.trigger,
            "verdict": self.verdict,
            "reason": self.reason,
        }


def evaluate_handover(
    codebook: Codebook,
    embedder: Embedder,
    config: RunConfig,
    *,
    batch: int,
    responses_coded: int,
    responses_since_checkpoint: int,
    curve: GrowthCurve | None = None,
    previous: Codebook | None = None,
) -> HandoverEvaluation:
    """Fire the handover rows of the matrix once, at a batch boundary.

    Delegates every measurement: `gaf.checks.health.codebook_health` and
    `checkpoint_signals` for near-duplicates, new codes, spacing and the floor;
    `gaf.checks.growth.spike_at` for the spike. What this function adds is the
    decision — which rows fired, which were held, which trigger names the result under
    `TRIGGER_PRECEDENCE`, and one reason sentence a person can read.

    ``previous`` is the codebook as it stood at the start of this batch; without it the
    whole codebook reads as new, which is the correct reading of a first batch and the
    wrong reading of a seventh. ``curve`` is the run's growth curve up to and including
    this batch; without one the spike row simply cannot fire.

    Nothing here blocks, writes or restructures. The fast loop calls this and carries
    the result; only a person at `gaf checkpoint` acts on it.
    """
    policy = config.checkpoints
    metrics = codebook_health(codebook, embedder, config.rules, previous=previous)
    spike = spike_at(curve, policy, batch=batch)
    signals = checkpoint_signals(
        metrics,
        policy,
        responses_coded=responses_coded,
        responses_since_checkpoint=responses_since_checkpoint,
        spike=spike,
    )

    event_driven = policy.mode == "event_driven"
    spacing = signals.spacing_satisfied
    cadence = policy.mode == "fixed" and responses_coded in policy.fixed_cadence

    health_fires = event_driven and spacing and (
        signals.near_duplicates_exceeded or signals.new_codes_exceeded
    )
    spike_fires = event_driven and spacing and signals.spike_detected
    trigger = first_trigger(
        health=health_fires,
        spike=spike_fires,
        floor=signals.hard_floor_reached,
        cadence=cadence,
    )

    fired: list[str] = []
    held: list[str] = []
    for rule_id, exceeded, spaced in (
        ("handover.near_duplicates", event_driven and signals.near_duplicates_exceeded, spacing),
        ("handover.new_codes", event_driven and signals.new_codes_exceeded, spacing),
        ("handover.spike", event_driven and signals.spike_detected, spacing),
        ("handover.floor", signals.hard_floor_reached, True),
        ("handover.cadence", cadence, True),
    ):
        if not exceeded:
            continue
        (fired if spaced else held).append(rule_id)
    if held:
        held.append("handover.spacing_hold")

    point = curve.point(batch) if curve is not None else None
    reasons = list(signals.reasons)
    if cadence:
        reasons.append(
            f"fixed cadence: {responses_coded} is a scheduled checkpoint "
            f"({', '.join(str(n) for n in policy.fixed_cadence)})"
        )
    if event_driven and curve is not None and batch <= max(1, int(policy.spike_window)):
        reasons.append(
            f"the spike rule has no baseline yet: a ratio needs "
            f"{max(1, int(policy.spike_window))} coded batches behind it, so batch "
            f"{batch} is judged by the absolute ceiling alone"
        )
    if not reasons:
        reasons.append(
            f"no trigger exceeded: {signals.near_duplicate_pairs} near-duplicate pairs, "
            f"{signals.new_codes} new codes in batch {batch}, {responses_coded} "
            "responses coded"
        )

    return HandoverEvaluation(
        batch=batch,
        responses_coded=responses_coded,
        responses_in_batch=point.responses_in_batch if point is not None else 0,
        responses_since_checkpoint=responses_since_checkpoint,
        new_codes=metrics.new_codes,
        cumulative_codes=metrics.n_codes,
        near_duplicate_pairs=metrics.near_duplicate_pairs,
        spike=spike,
        fired=tuple(fired),
        held=tuple(held),
        trigger=trigger,
        verdict=CHECKPOINT_DUE if trigger != "none" else CONTINUE,
        reason="; ".join(reasons),
    )


def trace_to_checkpoint_due(
    trace: Sequence[HandoverEvaluation],
) -> dict[str, Any]:
    """The run's `checkpoint_due` row, derived from the per-batch trace.

    The last batch's evaluation is the answer to "is the slow loop due *now*", which is
    what the run report and `scripts/export_results.py` read. The batches that came due
    earlier are carried alongside it, because a run that came due at batch 2, was not
    checkpointed, and had quietened by batch 7 is a different run from one that never
    came due at all — and the end-of-run number alone cannot tell them apart.
    """
    if not trace:
        return {
            "fires": False,
            "trigger": "none",
            "reason": "no batch was evaluated: the run coded no responses",
            "batch": 0,
            "verdict": CONTINUE,
            "batches_due": [],
        }
    last = trace[-1]
    return {
        "fires": last.checkpoint_due,
        "trigger": last.trigger,
        "reason": last.reason,
        "batch": last.batch,
        "verdict": last.verdict,
        "batches_due": [item.batch for item in trace if item.checkpoint_due],
    }
