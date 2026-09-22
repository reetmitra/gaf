"""Codebook health, theoretical saturation, and threshold calibration.

What this module does. Three deterministic, model-free measurements over a codebook and
over a run's history:

* **health metrics** — near-duplicate pair count (from M4), code growth rate, new codes
  per batch, family balance, orphan/leaf ratios and the evidence-per-code distribution.
  These are the quantities `gaf.config.CheckpointPolicy` names, so this module also
  reports which event-driven triggers are currently exceeded;
* **saturation** — new codes per batch, cumulative unique codes and the rate of change:
  the theoretical-sampling signal grounded theory requires, returned as a table (the
  chart that draws it belongs to the report layer);
* **threshold calibration** — tau_fit, tau_high and tau_low are *provisional*: they were
  set against a lexical fallback embedder and have never been calibrated against human
  judgment (brief §11). Given a golden set of human codings and machine codings of the
  same responses, this module sweeps each threshold over a grid, scores precision,
  recall and F1 against the human decisions, and returns the full curve alongside a
  recommendation.

What this module never does. It does not decide. `checkpoint_signals` reports which
triggers are exceeded and the slow loop decides whether to run a checkpoint;
`calibrate_thresholds` returns a recommendation and **never writes to `CodingRules`**,
because a threshold change must be a reported, versioned artefact rather than a silent
constant edit. Nothing here mutates a codebook or touches the store.

Findings. This module returns *metrics*, not `CheckFinding`s — the only findings it
produces come from the M4 near-duplicate check it calls, which already carries the
repo-wide `gaf.checks.semantic.MARKER_KEY` (`"marker"`) sub-kind key that the
structural suite uses too.

Validation principles: **transparency** — every threshold in the system is a named,
sweepable field and every recommendation carries the curve that produced it;
**interpretive depth** — near duplicates and a flattening saturation curve are prompts
for a human refactor decision, never automatic ones.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np

from gaf.checks.growth import Spike
from gaf.checks.semantic import (
    DEFAULT_RULES,
    MARKER_KEY,
    check_near_duplicate_leaves,
    cosine_matrix,
)
from gaf.config import CheckpointPolicy, CodingRules
from gaf.embed.protocol import Embedder, code_text
from gaf.models import Assignment, Codebook

__all__ = [
    "DEFAULT_ROUTE_GRID",
    "DEFAULT_TAU_FIT_GRID",
    "MARKER_KEY",
    "CalibrationReport",
    "CheckpointSignals",
    "EvidenceDistribution",
    "HealthMetrics",
    "SaturationPoint",
    "SaturationTable",
    "SweepPoint",
    "ThresholdSweep",
    "calibrate_routing",
    "calibrate_tau_fit",
    "calibrate_thresholds",
    "checkpoint_signals",
    "codebook_health",
    "saturation_curve",
    "saturation_from_codebooks",
]

#: The sweep grids. 0.00 to 1.00 in steps of 0.05 — coarse enough to read in a methods
#: appendix, fine enough that every provisional threshold is on the grid.
DEFAULT_TAU_FIT_GRID: tuple[float, ...] = tuple(round(0.05 * i, 4) for i in range(21))
DEFAULT_ROUTE_GRID: tuple[float, ...] = DEFAULT_TAU_FIT_GRID


# --------------------------------------------------------------------------- #
# Codebook health
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class EvidenceDistribution:
    """How verified evidence is spread across the codes. A long tail of zero-evidence
    codes is the signal that the codebook has accreted rather than grown."""

    n_codes: int
    total: int
    mean: float
    median: float
    minimum: int
    maximum: int
    p25: float
    p75: float
    zero_evidence_codes: int

    def to_json(self) -> dict[str, Any]:
        return {
            "n_codes": self.n_codes,
            "total": self.total,
            "mean": self.mean,
            "median": self.median,
            "min": self.minimum,
            "max": self.maximum,
            "p25": self.p25,
            "p75": self.p75,
            "zero_evidence_codes": self.zero_evidence_codes,
        }


@dataclass(frozen=True, slots=True)
class HealthMetrics:
    """The deterministic health of one codebook, optionally against its predecessor.

    `near_duplicate_pairs` is M4's count, recomputed here so the health row and the M4
    findings can never disagree. `new_codes` and `growth_rate` are `None`-free: with no
    predecessor supplied they describe the codebook as wholly new, which is the correct
    reading of the first batch of a run.
    """

    n_codes: int
    n_families: int
    n_leaves: int
    n_parents: int
    leaf_ratio: float
    n_orphans: int
    orphan_ratio: float
    orphan_leaf_ratio: float
    family_balance: dict[str, int]
    largest_family_share: float
    family_balance_gini: float
    near_duplicate_pairs: int
    near_duplicate_examples: list[dict[str, Any]]
    evidence_per_code: EvidenceDistribution
    previous_n_codes: int
    new_codes: int
    growth_rate: float
    space_id: str

    def to_json(self) -> dict[str, Any]:
        return {
            "n_codes": self.n_codes,
            "n_families": self.n_families,
            "n_leaves": self.n_leaves,
            "n_parents": self.n_parents,
            "leaf_ratio": self.leaf_ratio,
            "n_orphans": self.n_orphans,
            "orphan_ratio": self.orphan_ratio,
            "orphan_leaf_ratio": self.orphan_leaf_ratio,
            "family_balance": dict(self.family_balance),
            "largest_family_share": self.largest_family_share,
            "family_balance_gini": self.family_balance_gini,
            "near_duplicate_pairs": self.near_duplicate_pairs,
            "near_duplicate_examples": [dict(e) for e in self.near_duplicate_examples],
            "evidence_per_code": self.evidence_per_code.to_json(),
            "previous_n_codes": self.previous_n_codes,
            "new_codes": self.new_codes,
            "growth_rate": self.growth_rate,
            "space_id": self.space_id,
        }


def codebook_health(
    codebook: Codebook,
    embedder: Embedder,
    rules: CodingRules = DEFAULT_RULES,
    *,
    previous: Codebook | None = None,
) -> HealthMetrics:
    """Measure one codebook. Reports; decides nothing; mutates nothing.

    An **orphan** is a code whose `parent_id` names a code that is not in this codebook
    — the same dangling reference S6 raises an ERROR for, counted here as a proportion.
    A **leaf** is a code that is no other code's parent. `new_codes` counts names
    present here and absent from `previous`, so a rename reads as one new code and one
    lost code, which is what a health row should show.
    """
    codes = codebook.sorted_codes()
    n_codes = len(codes)
    families = codebook.families()
    leaves = codebook.leaves()
    n_leaves = len(leaves)
    orphans = [c for c in codes if c.parent_id and c.parent_id not in codebook.codes]

    duplicates = check_near_duplicate_leaves(codebook, embedder, rules)
    counts = [len(members) for members in families.values()]
    evidence_counts = [len([e for e in c.evidence if e.verified]) for c in codes]

    previous_names = set(previous.names()) if previous is not None else set()
    new_codes = len([c for c in codes if c.name not in previous_names])
    previous_n = len(previous_names)

    return HealthMetrics(
        n_codes=n_codes,
        n_families=len(families),
        n_leaves=n_leaves,
        n_parents=n_codes - n_leaves,
        leaf_ratio=_ratio(n_leaves, n_codes),
        n_orphans=len(orphans),
        orphan_ratio=_ratio(len(orphans), n_codes),
        orphan_leaf_ratio=_ratio(len(orphans), n_leaves),
        family_balance={family: len(members) for family, members in families.items()},
        largest_family_share=_ratio(max(counts), n_codes) if counts else 0.0,
        family_balance_gini=_gini(counts),
        near_duplicate_pairs=len(duplicates.pairs),
        near_duplicate_examples=[p.to_json() for p in duplicates.pairs],
        evidence_per_code=_evidence_distribution(evidence_counts),
        previous_n_codes=previous_n,
        new_codes=new_codes,
        growth_rate=_ratio(new_codes, previous_n) if previous_n else float(bool(n_codes)),
        space_id=embedder.space_id,
    )


def _ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0


def _gini(values: Sequence[int]) -> float:
    """Gini coefficient of the family sizes: 0.0 is perfectly balanced, 1.0 maximally
    concentrated. One family swallowing the codebook is the flattening failure mode."""
    if len(values) <= 1:
        return 0.0
    sorted_values = np.sort(np.asarray(values, dtype=np.float64))
    total = float(sorted_values.sum())
    if total <= 0.0:
        return 0.0
    n = sorted_values.size
    index = np.arange(1, n + 1, dtype=np.float64)
    return round(float((2.0 * np.sum(index * sorted_values)) / (n * total) - (n + 1) / n), 6)


def _evidence_distribution(counts: Sequence[int]) -> EvidenceDistribution:
    if not counts:
        return EvidenceDistribution(0, 0, 0.0, 0.0, 0, 0, 0.0, 0.0, 0)
    array = np.asarray(counts, dtype=np.float64)
    return EvidenceDistribution(
        n_codes=len(counts),
        total=int(array.sum()),
        mean=round(float(array.mean()), 6),
        median=round(float(np.median(array)), 6),
        minimum=int(array.min()),
        maximum=int(array.max()),
        p25=round(float(np.percentile(array, 25)), 6),
        p75=round(float(np.percentile(array, 75)), 6),
        zero_evidence_codes=int((array == 0.0).sum()),
    )


@dataclass(frozen=True, slots=True)
class CheckpointSignals:
    """Which `CheckpointPolicy` triggers the current health row exceeds.

    `recommend_checkpoint` is a *reading of the policy*, not an instruction: the slow
    loop (Wave 3) decides whether to wake, and a human gates whatever it proposes.

    `responses_coded` is where in the run this row sits; `responses_since_checkpoint`
    is how long it has been since a human last looked. Both the spacing rule and the
    hard floor are measured against the second (R1 I1).
    """

    mode: str
    near_duplicate_pairs: int
    max_near_duplicate_pairs: int
    near_duplicates_exceeded: bool
    new_codes: int
    max_new_codes_per_batch: int
    new_codes_exceeded: bool
    responses_since_checkpoint: int
    min_responses_between_checkpoints: int
    spacing_satisfied: bool
    responses_coded: int
    hard_floor_responses: int
    hard_floor_reached: bool
    recommend_checkpoint: bool
    reasons: list[str]
    #: Whether the batch this row describes spiked, and the `gaf.checks.growth.Spike`
    #: that says so. Measured by `gaf.checks.growth.detect_spikes` and reported here
    #: beside the other two event triggers; both default to "no spike was offered", so
    #: a caller that does not compute a growth curve sees exactly the pre-ADR-0033
    #: behaviour (ADR-0033).
    spike_detected: bool = False
    spike: dict[str, Any] | None = None

    def to_json(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "near_duplicate_pairs": self.near_duplicate_pairs,
            "max_near_duplicate_pairs": self.max_near_duplicate_pairs,
            "near_duplicates_exceeded": self.near_duplicates_exceeded,
            "new_codes": self.new_codes,
            "max_new_codes_per_batch": self.max_new_codes_per_batch,
            "new_codes_exceeded": self.new_codes_exceeded,
            "responses_since_checkpoint": self.responses_since_checkpoint,
            "min_responses_between_checkpoints": self.min_responses_between_checkpoints,
            "spacing_satisfied": self.spacing_satisfied,
            "responses_coded": self.responses_coded,
            "hard_floor_responses": self.hard_floor_responses,
            "hard_floor_reached": self.hard_floor_reached,
            "recommend_checkpoint": self.recommend_checkpoint,
            "reasons": list(self.reasons),
            "spike_detected": self.spike_detected,
            "spike": dict(self.spike) if self.spike is not None else None,
        }


def checkpoint_signals(
    metrics: HealthMetrics,
    policy: CheckpointPolicy,
    *,
    responses_coded: int,
    responses_since_checkpoint: int,
    spike: Spike | None = None,
) -> CheckpointSignals:
    """Report the event-driven checkpoint triggers against a health row.

    An event trigger fires when near-duplicate pairs, new codes per batch or the spike
    rule exceed the policy *and* enough responses have passed since the last
    checkpoint. The hard floor fires on its own, so a quiet codebook still gets a human
    look.

    **The floor is measured since the last checkpoint, not since the run began.**
    ``responses_coded`` is a running total that no checkpoint resets, so comparing the
    floor against it meant that once the floor had been crossed every later batch of
    every later run reported a checkpoint due under trigger ``floor`` (R1 I1) — a
    fixed schedule wearing an event trigger's name. "A quiet codebook still gets a
    human look" is a statement about how long it has been since the last look, which is
    ``responses_since_checkpoint``. ``responses_coded`` is still reported, because a
    reader needs to know where in the run the row sits.

    A batch after the floor is crossed and before a checkpoint is taken still reports
    ``hard_floor_reached``: the look is still owed. What has gone is the latch across
    a checkpoint, which is what made the trigger uninformative.

    ``spike`` is measured elsewhere — `gaf.checks.growth.detect_spikes` reads the growth
    curve, which is a fact about a *sequence* of batches and not about the one codebook
    this health row describes. It is reported here so that the three event triggers sit
    on one row; passing nothing leaves every number and every reason exactly as it was
    before ADR-0033.
    """
    near_exceeded = metrics.near_duplicate_pairs > policy.max_near_duplicate_pairs
    new_exceeded = metrics.new_codes > policy.max_new_codes_per_batch
    spiked = spike is not None
    spacing_ok = responses_since_checkpoint >= policy.min_responses_between_checkpoints
    floor_reached = responses_since_checkpoint >= policy.hard_floor_responses

    reasons: list[str] = []
    if near_exceeded:
        reasons.append(
            f"near-duplicate pairs {metrics.near_duplicate_pairs} > "
            f"{policy.max_near_duplicate_pairs}"
        )
    if new_exceeded:
        reasons.append(
            f"new codes this batch {metrics.new_codes} > {policy.max_new_codes_per_batch}"
        )
    if spike is not None:
        reasons.append(f"spike: {spike.reason}")
    exceeded = near_exceeded or new_exceeded or spiked
    event = exceeded and spacing_ok and policy.mode == "event_driven"
    if event and not reasons:  # pragma: no cover - defensive; event implies a reason
        reasons.append("event trigger exceeded")
    if not spacing_ok and exceeded:
        reasons.append(
            f"held: only {responses_since_checkpoint} of "
            f"{policy.min_responses_between_checkpoints} responses since the last checkpoint"
        )
    if floor_reached:
        reasons.append(
            f"hard floor reached: {responses_since_checkpoint} >= "
            f"{policy.hard_floor_responses} responses since the last checkpoint"
        )
    return CheckpointSignals(
        mode=policy.mode,
        near_duplicate_pairs=metrics.near_duplicate_pairs,
        max_near_duplicate_pairs=policy.max_near_duplicate_pairs,
        near_duplicates_exceeded=near_exceeded,
        new_codes=metrics.new_codes,
        max_new_codes_per_batch=policy.max_new_codes_per_batch,
        new_codes_exceeded=new_exceeded,
        responses_since_checkpoint=responses_since_checkpoint,
        min_responses_between_checkpoints=policy.min_responses_between_checkpoints,
        spacing_satisfied=spacing_ok,
        responses_coded=responses_coded,
        hard_floor_responses=policy.hard_floor_responses,
        hard_floor_reached=floor_reached,
        recommend_checkpoint=event or floor_reached,
        reasons=reasons,
        spike_detected=spiked,
        spike=spike.to_json() if spike is not None else None,
    )


# --------------------------------------------------------------------------- #
# Saturation
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class SaturationPoint:
    """One batch of the saturation curve."""

    batch: int
    codes_seen: int
    new_codes: int
    cumulative_unique: int
    #: Fraction of the codebook that is new in this batch. Trends to zero as the
    #: theoretical categories saturate — this is the signal, not the raw count.
    growth_rate: float
    #: Change in `new_codes` against the previous batch; negative means slowing.
    new_codes_delta: int
    new_names: list[str]

    def to_json(self) -> dict[str, Any]:
        return {
            "batch": self.batch,
            "codes_seen": self.codes_seen,
            "new_codes": self.new_codes,
            "cumulative_unique": self.cumulative_unique,
            "growth_rate": self.growth_rate,
            "new_codes_delta": self.new_codes_delta,
            "new_names": list(self.new_names),
        }


@dataclass(frozen=True, slots=True)
class SaturationTable:
    """The saturation curve as a table. The SVG that draws it belongs to the report layer."""

    points: list[SaturationPoint]
    headers: tuple[str, ...] = (
        "batch",
        "codes_seen",
        "new_codes",
        "cumulative_unique",
        "growth_rate",
        "new_codes_delta",
    )

    @property
    def total_unique(self) -> int:
        return self.points[-1].cumulative_unique if self.points else 0

    def rows(self) -> list[tuple[Any, ...]]:
        return [
            (
                p.batch,
                p.codes_seen,
                p.new_codes,
                p.cumulative_unique,
                p.growth_rate,
                p.new_codes_delta,
            )
            for p in self.points
        ]

    def to_json(self) -> dict[str, Any]:
        return {
            "headers": list(self.headers),
            "rows": [p.to_json() for p in self.points],
            "total_unique": self.total_unique,
        }


def saturation_curve(batches: Sequence[Iterable[str]]) -> SaturationTable:
    """New codes per batch, cumulative unique codes and the rate of change.

    Each batch is the code names observed while coding that batch of responses. Names
    are the unit because a rename is a slow-loop event and a saturation curve should
    show it.
    """
    seen: set[str] = set()
    points: list[SaturationPoint] = []
    previous_new = 0
    for index, batch in enumerate(batches, start=1):
        names = list(batch)
        fresh = sorted({n for n in names if n not in seen})
        seen.update(fresh)
        points.append(
            SaturationPoint(
                batch=index,
                codes_seen=len(names),
                new_codes=len(fresh),
                cumulative_unique=len(seen),
                growth_rate=_ratio(len(fresh), len(seen)),
                new_codes_delta=len(fresh) - previous_new,
                new_names=fresh,
            )
        )
        previous_new = len(fresh)
    return SaturationTable(points=points)


def saturation_from_codebooks(snapshots: Sequence[Codebook]) -> SaturationTable:
    """The same curve from a sequence of codebook snapshots, one per batch."""
    return saturation_curve([snapshot.names() for snapshot in snapshots])


# --------------------------------------------------------------------------- #
# Threshold calibration (brief §11)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class SweepPoint:
    """One grid value and its confusion matrix against the human decisions."""

    threshold: float
    true_positives: int
    false_positives: int
    false_negatives: int
    true_negatives: int
    predicted_positive: int
    precision: float
    recall: float
    f1: float

    def to_json(self) -> dict[str, Any]:
        return {
            "threshold": self.threshold,
            "tp": self.true_positives,
            "fp": self.false_positives,
            "fn": self.false_negatives,
            "tn": self.true_negatives,
            "predicted_positive": self.predicted_positive,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
        }


@dataclass(frozen=True, slots=True)
class ThresholdSweep:
    """One threshold's full curve and the recommendation drawn from it.

    `recommended` is chosen by a rule stated once and applied everywhere: if the
    provisional value is itself among the F1-maximising grid values, it is kept — there
    is no evidence to move it. Otherwise the middle of the maximising range is taken
    (the upper median when the count is even), which is the least brittle point of a
    plateau. `changed` says which of the two happened.
    """

    name: str
    unit: str
    positive_label: str
    prediction_label: str
    current: float
    recommended: float
    changed: bool
    best_f1: float
    f1_at_current: float
    plateau: tuple[float, float]
    n_units: int
    n_positive: int
    curve: list[SweepPoint]

    def to_json(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "unit": self.unit,
            "positive_label": self.positive_label,
            "prediction_label": self.prediction_label,
            "current": self.current,
            "recommended": self.recommended,
            "changed": self.changed,
            "best_f1": self.best_f1,
            "f1_at_current": self.f1_at_current,
            "plateau": list(self.plateau),
            "n_units": self.n_units,
            "n_positive": self.n_positive,
            "curve": [p.to_json() for p in self.curve],
        }


@dataclass(frozen=True, slots=True)
class CalibrationReport:
    """A `calibration_report.json`-shaped artefact plus the paragraph that explains it.

    Returning this object is the whole of calibration's authority. It **does not and
    must not** write to `CodingRules`: a threshold moves only when a human accepts a
    versioned calibration artefact, never as a silent constant change.
    """

    space_id: str
    sweeps: dict[str, ThresholdSweep]
    n_human_assignments: int
    n_machine_assignments: int
    n_responses: int
    notes: list[str]

    @property
    def recommended(self) -> dict[str, float]:
        return {name: sweep.recommended for name, sweep in self.sweeps.items()}

    @property
    def current(self) -> dict[str, float]:
        return {name: sweep.current for name, sweep in self.sweeps.items()}

    def paragraph(self) -> str:
        """Plain-language prose naming the chosen values and the evidence behind them."""
        sentences = [
            f"Threshold calibration ran in embedding space {self.space_id} against "
            f"{self.n_machine_assignments} machine codings and {self.n_human_assignments} human "
            f"codings across {self.n_responses} responses."
        ]
        for name in ("tau_fit", "tau_high", "tau_low"):
            sweep = self.sweeps.get(name)
            if sweep is None:
                continue
            verb = (
                f"moves from {sweep.current:.2f} to {sweep.recommended:.2f}"
                if sweep.changed
                else f"stays at {sweep.current:.2f}"
            )
            sentences.append(
                f"{name} {verb}: over {sweep.n_units} {sweep.unit} "
                f"({sweep.n_positive} of them {sweep.positive_label}), F1 of "
                f"{sweep.prediction_label} peaks at {sweep.best_f1:.3f} across grid values "
                f"{sweep.plateau[0]:.2f} to {sweep.plateau[1]:.2f}, against "
                f"{sweep.f1_at_current:.3f} at the provisional value."
            )
        sentences.extend(self.notes)
        sentences.append(
            "These are recommendations only. CodingRules is not modified by this function; a "
            "threshold changes only through a reported, versioned calibration artefact."
        )
        return " ".join(sentences)

    def to_json(self) -> dict[str, Any]:
        return {
            "space_id": self.space_id,
            "generated_from": {
                "n_human_assignments": self.n_human_assignments,
                "n_machine_assignments": self.n_machine_assignments,
                "n_responses": self.n_responses,
            },
            "current": self.current,
            "recommended": self.recommended,
            "changed": {name: sweep.changed for name, sweep in self.sweeps.items()},
            "sweeps": {name: sweep.to_json() for name, sweep in self.sweeps.items()},
            "notes": list(self.notes),
            "narrative": self.paragraph(),
        }


def _prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return round(precision, 6), round(recall, 6), round(f1, 6)


def _sweep(
    *,
    name: str,
    unit: str,
    positive_label: str,
    prediction_label: str,
    current: float,
    scores: Sequence[float],
    labels: Sequence[bool],
    predict_below: bool,
    grid: Sequence[float],
) -> ThresholdSweep:
    """Sweep one threshold. `predict_below` means the positive prediction is
    ``score < threshold`` (escalate, create); otherwise it is ``score >= threshold``
    (merge)."""
    curve: list[SweepPoint] = []
    for threshold in grid:
        tp = fp = fn = tn = 0
        for score, positive in zip(scores, labels, strict=True):
            predicted = score < threshold if predict_below else score >= threshold
            if predicted and positive:
                tp += 1
            elif predicted:
                fp += 1
            elif positive:
                fn += 1
            else:
                tn += 1
        precision, recall, f1 = _prf(tp, fp, fn)
        curve.append(
            SweepPoint(
                threshold=round(float(threshold), 6),
                true_positives=tp,
                false_positives=fp,
                false_negatives=fn,
                true_negatives=tn,
                predicted_positive=tp + fp,
                precision=precision,
                recall=recall,
                f1=f1,
            )
        )

    best_f1 = max((p.f1 for p in curve), default=0.0)
    maximisers = [p.threshold for p in curve if math.isclose(p.f1, best_f1, abs_tol=1e-9)]
    at_current = next(
        (p.f1 for p in curve if math.isclose(p.threshold, current, abs_tol=1e-9)), 0.0
    )
    keeps_current = any(math.isclose(t, current, abs_tol=1e-9) for t in maximisers)
    recommended = current if keeps_current else maximisers[len(maximisers) // 2]
    return ThresholdSweep(
        name=name,
        unit=unit,
        positive_label=positive_label,
        prediction_label=prediction_label,
        current=current,
        recommended=round(float(recommended), 6),
        changed=not keeps_current,
        best_f1=best_f1,
        f1_at_current=at_current,
        plateau=(min(maximisers), max(maximisers)) if maximisers else (current, current),
        n_units=len(scores),
        n_positive=sum(1 for label in labels if label),
        curve=curve,
    )


def _assignment_fits(
    machine: Sequence[Assignment], embedder: Embedder
) -> tuple[list[float], list[tuple[int, str]]]:
    """Fit score per machine assignment, with its (response id, code) key.

    Descriptions are absent from an `Assignment`, so the code is rendered by
    `code_text(name)` — the same function M3 uses."""
    if not machine:
        return [], []
    codes = embedder.embed([code_text(a.code) for a in machine])
    segments = embedder.embed([a.segment for a in machine])
    similarity = cosine_matrix(codes, segments)
    scores = [round(float(similarity[i, i]), 6) for i in range(len(machine))]
    return scores, [(a.response_id, a.code) for a in machine]


def calibrate_tau_fit(
    human: Sequence[Assignment],
    machine: Sequence[Assignment],
    embedder: Embedder,
    rules: CodingRules = DEFAULT_RULES,
    *,
    grid: Sequence[float] = DEFAULT_TAU_FIT_GRID,
) -> ThresholdSweep:
    """Sweep tau_fit against the human-marked bad applications.

    The unit is one machine assignment. It is a **bad application** when the human
    coding of that response does not carry that code at all — the PI's "your code did
    not have to be applied", read at the level his golden set can support. The
    prediction under a candidate tau_fit is "M3 escalates this to the judge", i.e.
    ``fit < tau_fit``; precision, recall and F1 are of that escalation against the human
    marking, so a low threshold is cheap and blind and a high one escalates everything.
    """
    scores, keys = _assignment_fits(machine, embedder)
    human_pairs = {(a.response_id, a.code) for a in human}
    labels = [key not in human_pairs for key in keys]
    return _sweep(
        name="tau_fit",
        unit="machine code applications",
        positive_label="unsupported by the human coding",
        prediction_label="judge escalation",
        current=rules.tau_fit,
        scores=scores,
        labels=labels,
        predict_below=True,
        grid=grid,
    )


def _route_units(
    human: Sequence[Assignment], machine: Sequence[Assignment], embedder: Embedder
) -> tuple[list[float], list[bool]]:
    """One unit per distinct machine code: its best cosine to any human code, and
    whether the human coding already contains that same code.

    The unit mirrors M2 exactly — M2 routes on the *best* neighbour — so a threshold
    calibrated here means the same thing when it is applied there.
    """
    machine_codes = sorted({a.code for a in machine})
    human_codes = sorted({a.code for a in human})
    if not machine_codes or not human_codes:
        return [], []
    similarity = cosine_matrix(
        embedder.embed([code_text(c) for c in machine_codes]),
        embedder.embed([code_text(c) for c in human_codes]),
    )
    scores = [round(float(similarity[i].max()), 6) for i in range(len(machine_codes))]
    labels = [code in set(human_codes) for code in machine_codes]
    return scores, labels


def calibrate_routing(
    human: Sequence[Assignment],
    machine: Sequence[Assignment],
    embedder: Embedder,
    rules: CodingRules = DEFAULT_RULES,
    *,
    grid: Sequence[float] = DEFAULT_ROUTE_GRID,
) -> tuple[ThresholdSweep, ThresholdSweep]:
    """Sweep tau_high and tau_low against the human merge/create decisions.

    The human's own decision is recoverable from the golden set: a machine code the
    human coding also contains is a code the human would **merge**; one the human never
    uses is a code the machine would have to **create**. tau_high is scored on the merge
    prediction (``score >= tau_high``) and tau_low on the create prediction
    (``score < tau_low``); the caller enforces ``tau_low <= tau_high``.
    """
    scores, merge_labels = _route_units(human, machine, embedder)
    high = _sweep(
        name="tau_high",
        unit="candidate/nearest-neighbour pairs",
        positive_label="the same code in the human coding",
        prediction_label="auto-merge",
        current=rules.tau_high,
        scores=scores,
        labels=merge_labels,
        predict_below=False,
        grid=grid,
    )
    low = _sweep(
        name="tau_low",
        unit="candidate/nearest-neighbour pairs",
        positive_label="absent from the human coding",
        prediction_label="auto-create",
        current=rules.tau_low,
        scores=scores,
        labels=[not label for label in merge_labels],
        predict_below=True,
        grid=grid,
    )
    return high, low


def calibrate_thresholds(
    human: Sequence[Assignment],
    machine: Sequence[Assignment],
    embedder: Embedder,
    rules: CodingRules = DEFAULT_RULES,
    *,
    fit_grid: Sequence[float] = DEFAULT_TAU_FIT_GRID,
    route_grid: Sequence[float] = DEFAULT_ROUTE_GRID,
) -> CalibrationReport:
    """Calibrate tau_fit, tau_high and tau_low against a golden set. Returns a
    recommendation and the curves behind it.

    **This function never writes to `CodingRules`.** `rules` is read for the provisional
    values so the report can say what would change; the returned `CalibrationReport` is
    an artefact for a human to accept or reject, which is the only way a threshold in
    this pipeline is allowed to move (brief §11).
    """
    fit = calibrate_tau_fit(human, machine, embedder, rules, grid=fit_grid)
    high, low = calibrate_routing(human, machine, embedder, rules, grid=route_grid)

    notes: list[str] = []
    if low.recommended > high.recommended:
        notes.append(
            f"tau_low's own optimum ({low.recommended:.2f}) exceeded tau_high's "
            f"({high.recommended:.2f}); it is clamped to tau_high, which collapses the grey "
            "zone and should be read as the data failing to separate merge from create."
        )
        low = ThresholdSweep(
            name=low.name,
            unit=low.unit,
            positive_label=low.positive_label,
            prediction_label=low.prediction_label,
            current=low.current,
            recommended=high.recommended,
            changed=not math.isclose(high.recommended, low.current, abs_tol=1e-9),
            best_f1=low.best_f1,
            f1_at_current=low.f1_at_current,
            plateau=low.plateau,
            n_units=low.n_units,
            n_positive=low.n_positive,
            curve=low.curve,
        )
    for sweep in (fit, high, low):
        if sweep.n_units < 30:
            notes.append(
                f"{sweep.name} rests on only {sweep.n_units} units, which is too few to move a "
                "threshold on; treat the curve as a shape, not a measurement."
            )
        if sweep.plateau[1] - sweep.plateau[0] >= 0.3:
            notes.append(
                f"{sweep.name}'s F1 maximum is flat from {sweep.plateau[0]:.2f} to "
                f"{sweep.plateau[1]:.2f}, so this golden set barely discriminates it."
            )
    return CalibrationReport(
        space_id=embedder.space_id,
        sweeps={"tau_fit": fit, "tau_high": high, "tau_low": low},
        n_human_assignments=len(human),
        n_machine_assignments=len(machine),
        n_responses=len({a.response_id for a in human} | {a.response_id for a in machine}),
        notes=notes,
    )
