"""Code growth across batches, and the spike rule that reads it.

What this module does. Two deterministic, model-free measurements over a coding:

* **the growth curve** — per batch: responses in the batch, new codes, cumulative
  codes and **new codes per response**. Computable two ways from the same coding: from
  an ordered list of :class:`gaf.models.Assignment` rows (which is the shape a human's
  coding spreadsheet exports in), and from a run's audit log (which records the order
  codes were admitted, as ``code_created`` events). Both go through one implementation,
  so a hand coding and a pipeline run can be put on the same axes;
* **the spike rule** — which batches admitted far more codes than the batches just
  before them. An absolute ceiling (`CheckpointPolicy.max_new_codes_per_batch`) cannot
  tell a *first* batch, where every code is new and a large count is expected, from a
  *late* batch where eight new codes means the codebook has stopped converging. The
  ratio rule here sits beside the absolute one rather than replacing it (ADR-0033).

**There is only one saturation curve in this project.** `code_growth` delegates the
counting to :func:`gaf.analysis.hca.saturation_curve` and adds exactly one column that
curve does not carry — new codes per response — plus the entry points that let the same
curve be read out of a run. Counting new codes a second time would give the reader two
numbers for one fact, and `gaf.checks.health.saturation_curve` (over batches of *names*)
and `gaf.analysis.hca.saturation_curve` (over an occurrence matrix) are already as many
views of it as the project should have.

What this module never does. It does not decide. `detect_spikes` reports which batches
spiked and why; `gaf.pipeline.decision_matrix` and `gaf.pipeline.slow_loop` decide what
a spike is worth. Nothing here mutates a codebook or touches the store — the audit
entry point reads JSON-shaped rows, so it works on a live log, on ``audit.jsonl``, or on
rows a test invents, and this module never imports the database.

The defaults of the spike rule are **uncalibrated** (ADR-0033): like tau_fit they are
set by argument rather than against human judgment, and they should move through a
calibration report rather than by hand.

Validation principles: **transparency** — the growth of a codebook is a table a reviewer
can recompute from the audit log rather than a claim in a summary; **interpretive
depth** — a spike is the signal that the codebook has begun accreting parallel concepts
rather than converging, which is the judgment the human gate exists to make.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from statistics import median
from typing import Any

from gaf.analysis.hca import saturation_curve
from gaf.analysis.matrix import build_matrix
from gaf.config import AnalysisConfig, CheckpointPolicy
from gaf.models import Assignment, Response

__all__ = [
    "PREPARED_EVENT",
    "RULE_ABSOLUTE",
    "RULE_RATIO",
    "SOURCES",
    "SPIKE_RULES",
    "GrowthCurve",
    "GrowthPoint",
    "Spike",
    "code_growth",
    "detect_spikes",
    "growth_from_admissions",
    "growth_from_audit",
    "spike_at",
]

#: Where a curve was read from. Recorded on the curve so a reader of the JSON knows
#: whether they are looking at a hand coding or at a run.
SOURCES: tuple[str, ...] = ("assignments", "audit")

#: The batch spiked against the median of the previous `spike_window` batches. The one
#: rule `detect_spikes` raises a `Spike` under.
RULE_RATIO = "ratio"
#: **Retired.** `detect_spikes` used to judge a batch with no baseline against the
#: absolute `CheckpointPolicy.max_new_codes_per_batch` ceiling, which is the same
#: comparison `gaf.checks.health.checkpoint_signals` makes under ``handover.new_codes``
#: — so the two rules reported one fact twice (R1 Minor). The first `spike_window`
#: batches now simply do not spike. The name is kept so a `Spike` written by an earlier
#: build still reads, and `SPIKE_RULES` still names both.
RULE_ABSOLUTE = "absolute"

#: Every rule name a `Spike` may carry, including the retired one.
SPIKE_RULES: tuple[str, ...] = (RULE_ABSOLUTE, RULE_RATIO)

#: The audit event that marks one response entering the fast loop. It is emitted for
#: every response, including one whose every candidate is later dropped, which is what
#: makes the batch edges of an audit-derived curve the batch edges the run really used.
PREPARED_EVENT = "response_prepared"

#: The audit event that records one code being admitted to the codebook.
_CREATED_EVENT = "code_created"


# --------------------------------------------------------------------------- #
# The curve
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class GrowthPoint:
    """One batch of the growth curve.

    Every field but `new_codes_per_response` is taken verbatim from the saturation
    point this batch corresponds to. The rate is the column growth adds: a reader
    comparing batch 1 of a 10-response batch with batch 7 of a 4-response tail needs
    the rate, not the raw count.
    """

    batch: int
    responses_in_batch: int
    cumulative_responses: int
    new_codes: int
    cumulative_codes: int
    new_codes_per_response: float
    new_code_names: tuple[str, ...]

    def to_json(self) -> dict[str, Any]:
        return {
            "batch": self.batch,
            "responses_in_batch": self.responses_in_batch,
            "cumulative_responses": self.cumulative_responses,
            "new_codes": self.new_codes,
            "cumulative_codes": self.cumulative_codes,
            "new_codes_per_response": self.new_codes_per_response,
            "new_code_names": list(self.new_code_names),
        }


@dataclass(frozen=True, slots=True)
class GrowthCurve:
    """How the codebook grew, batch by batch, in one coding order.

    ``saturated_at_batch`` is the first batch that contributed no new code, carried
    through from the saturation curve so that "the codebook stopped growing" and "the
    codebook spiked" are read off one table rather than two.
    """

    source: str
    batch_size: int
    points: tuple[GrowthPoint, ...]
    total_codes: int
    saturated_at_batch: int | None

    def new_code_counts(self) -> tuple[int, ...]:
        """The per-batch new-code counts — the series the spike rule reads."""
        return tuple(point.new_codes for point in self.points)

    def point(self, batch: int) -> GrowthPoint | None:
        """The point for this 1-based batch number, or `None` if the curve has none."""
        for candidate in self.points:
            if candidate.batch == batch:
                return candidate
        return None

    def last(self) -> GrowthPoint | None:
        """The most recent batch, or `None` for an empty curve."""
        return self.points[-1] if self.points else None

    def to_json(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "batch_size": self.batch_size,
            "total_codes": self.total_codes,
            "saturated_at_batch": self.saturated_at_batch,
            "points": [point.to_json() for point in self.points],
        }


def code_growth(
    assignments: Sequence[Assignment],
    *,
    batch_size: int,
    order: Sequence[int] | None = None,
    response_ids: Sequence[int] | None = None,
    source: str = "assignments",
) -> GrowthCurve:
    """The growth curve of a coding given as assignment rows.

    ``order`` is the order the responses were coded in. It defaults to the order the
    rows first name each response — which is the order a coding spreadsheet exports in,
    and therefore the order the PI's own coding actually happened in. It must be a
    permutation of the response universe: a short order would silently truncate the
    curve and a long one would ask for a response that was never coded, and both are
    refused rather than absorbed.

    ``response_ids`` fixes that universe. Supply it whenever the run processed a
    response that produced no assignment row — every candidate dropped on an
    unverifiable quote, say. Such a response still consumed a place in its batch, and
    leaving it out re-cuts every batch after it (the same care
    :meth:`gaf.report.run_report.RunArtefact.saturation` takes).

    The counting is :func:`gaf.analysis.hca.saturation_curve`'s, over the **unfiltered**
    occurrence matrix: the low-frequency filter removes exactly the rare codes whose
    arrival is the interesting part of this curve.
    """
    universe = _universe(assignments, response_ids)
    sequence = _sequence(assignments, order, universe)
    size = max(1, int(batch_size))

    unfiltered = replace(
        AnalysisConfig(), min_code_frequency=1, min_code_frequency_fraction=None
    )
    matrix = build_matrix(
        list(assignments),
        config=unfiltered,
        responses=[Response(id=rid, question="", content="", source="") for rid in universe],
    )
    curve = saturation_curve(
        matrix,
        config=replace(unfiltered, saturation_batch_size=size),
        order=sequence or None,
    )
    return GrowthCurve(
        source=source,
        batch_size=curve.batch_size,
        points=tuple(
            GrowthPoint(
                batch=point.batch,
                responses_in_batch=point.responses_in_batch,
                cumulative_responses=point.cumulative_responses,
                new_codes=point.new_codes,
                cumulative_codes=point.cumulative_codes,
                new_codes_per_response=_rate(point.new_codes, point.responses_in_batch),
                new_code_names=point.new_code_names,
            )
            for point in curve.points
        ),
        total_codes=curve.total_codes,
        saturated_at_batch=curve.saturated_at_batch,
    )


def growth_from_admissions(
    admissions: Sequence[tuple[int, str]],
    *,
    response_order: Sequence[int],
    batch_size: int,
) -> GrowthCurve:
    """The growth curve of a run, from the admissions themselves.

    ``admissions`` are ``(response_id, code_name)`` pairs in the order the codes were
    admitted; ``response_order`` is every response the run processed, in processing
    order, including the ones that admitted nothing. This is the shape the fast loop
    has in hand at a batch boundary and the shape `growth_from_audit` reduces a log to,
    so the curve a run computes about itself and the curve a reader recomputes from its
    ``code_created`` events are the same curve.

    Admission is deliberately the unit rather than assignment rows: a code admitted
    with no verified quote writes no assignment row, and a curve built from rows alone
    would not know it had grown.
    """
    order = [int(rid) for rid in response_order]
    known = set(order)
    extra = sorted({int(rid) for rid, _ in admissions} - known)
    order = order + extra
    rows = [
        Assignment(response_id=int(response_id), segment="", code=str(name))
        for response_id, name in admissions
    ]
    return code_growth(
        rows,
        batch_size=batch_size,
        order=order or None,
        response_ids=order or None,
        source="audit",
    )


def growth_from_audit(
    events: Iterable[Mapping[str, Any]],
    *,
    batch_size: int,
) -> GrowthCurve:
    """The same curve, read out of a run's audit log.

    ``events`` are audit rows in the log's own order — :meth:`gaf.store.audit.AuditEvent.to_json`
    dicts, the lines of an ``audit.jsonl``, or rows a test builds by hand. Two event
    names carry the whole curve: ``response_prepared`` marks each response entering the
    fast loop, in processing order, and ``code_created`` records one code being
    admitted, carrying the response that admitted it. The snapshots record the same
    fact — each batch freezes one, and the difference between consecutive codebooks is
    that batch's new codes — but the log carries the response order too, so nothing here
    has to assume a batch size the run may not have used.

    Events of any other name are ignored, so passing the whole log is correct.
    """
    prepared: list[int] = []
    admissions: list[tuple[int, str]] = []
    for event in events:
        name = str(event.get("event", ""))
        if name == PREPARED_EVENT:
            subject = str(event.get("subject", ""))
            if subject.lstrip("-").isdigit():
                prepared.append(int(subject))
        elif name == _CREATED_EVENT:
            payload = event.get("payload") or {}
            raw = payload.get("response_id") if isinstance(payload, Mapping) else None
            if raw is None:
                continue
            admissions.append((int(raw), str(event.get("subject", ""))))
    return growth_from_admissions(
        admissions, response_order=prepared, batch_size=batch_size
    )


def _universe(
    assignments: Sequence[Assignment], response_ids: Sequence[int] | None
) -> list[int]:
    """The rows of the curve: the caller's universe, or the responses the rows name."""
    if response_ids is not None:
        return sorted({int(rid) for rid in response_ids})
    return sorted({a.response_id for a in assignments})


def _sequence(
    assignments: Sequence[Assignment],
    order: Sequence[int] | None,
    universe: Sequence[int],
) -> list[int]:
    """The coding order, validated as a permutation of `universe`."""
    known = set(universe)
    if order is None:
        seen: dict[int, None] = {}
        for assignment in assignments:
            seen.setdefault(assignment.response_id, None)
        return list(seen) + sorted(known - set(seen))

    sequence = [int(rid) for rid in order]
    unknown = sorted(set(sequence) - known)
    if unknown:
        raise ValueError(
            "the coding order names response ids that are not in the coding: "
            f"{unknown[:10]}{' ...' if len(unknown) > 10 else ''}"
        )
    missing = sorted(known - set(sequence))
    if missing:
        raise ValueError(
            "the coding order must name every response in the coding, or the curve is "
            f"silently truncated; missing: {missing[:10]}"
            f"{' ...' if len(missing) > 10 else ''}"
        )
    return sequence


def _rate(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0


# --------------------------------------------------------------------------- #
# The spike rule
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class Spike:
    """One batch that admitted far more codes than the batches before it.

    ``baseline`` is the median new-code count of the previous ``window`` batches under
    the ratio rule, and the absolute ceiling under the fallback rule. ``ratio`` is
    ``new_codes / baseline`` and is ``None`` exactly when no ratio was taken — the batch
    had no baseline, or the baseline was zero, and a division there would put an
    infinity into JSON that no reader could interpret.
    """

    batch: int
    new_codes: int
    baseline: float
    ratio: float | None
    rule: str
    window: int
    reason: str

    def to_json(self) -> dict[str, Any]:
        return {
            "batch": self.batch,
            "new_codes": self.new_codes,
            "baseline": self.baseline,
            "ratio": self.ratio,
            "rule": self.rule,
            "window": self.window,
            "reason": self.reason,
        }


def detect_spikes(curve: GrowthCurve, policy: CheckpointPolicy) -> list[Spike]:
    """Which batches of this curve spiked, and why. Reports; decides nothing.

    A batch spikes when it admitted at least ``policy.spike_min_new_codes`` codes **and**
    at least ``policy.spike_factor`` times the median new-code count of the previous
    ``policy.spike_window`` batches.

    **The first ``spike_window`` batches do not spike at all.** A ratio against nothing
    is not a measurement, and the fallback this rule used to make there — the absolute
    ceiling ``policy.max_new_codes_per_batch`` — is definitionally the comparison
    :func:`gaf.checks.health.checkpoint_signals` already makes under
    ``handover.new_codes``. Both fired on the same condition, so the batch's own reason
    string stated one fact twice and ``CheckpointSignals.spike_detected`` was true on a
    batch where no *ratio* spike had occurred (R1 Minor). The absolute rule alone now
    carries the early batches; this one reports that it has no baseline yet and stands
    aside. The two still coexist for the reason ADR-0033 gives: the absolute rule is
    the only thing that can speak about a first batch, and the ratio rule is the only
    thing that can tell a late batch's eight new codes from an early batch's.

    ``spike_min_new_codes`` is load-bearing rather than cosmetic: after a run of quiet
    batches the baseline median is zero, every count is trivially at or above
    ``spike_factor * 0``, and the floor is the only thing standing between the rule and
    calling one new code a spike.
    """
    window = max(1, int(policy.spike_window))
    counts = curve.new_code_counts()
    spikes: list[Spike] = []

    for index, point in enumerate(curve.points):
        if index < window:
            # No baseline, so no ratio, so no spike. `handover.new_codes` is the rule
            # that speaks about an early batch, and it does not need this one saying
            # the same thing beside it (R1 Minor).
            continue

        baseline = float(median(counts[index - window : index]))
        if point.new_codes < policy.spike_min_new_codes:
            continue
        if point.new_codes < policy.spike_factor * baseline:
            continue
        ratio = round(point.new_codes / baseline, 6) if baseline > 0 else None
        against = (
            f"{ratio}x the median of the previous {window} batches ({baseline})"
            if ratio is not None
            else (
                f"a baseline of zero — the previous {window} batches admitted no new "
                "code at all"
            )
        )
        spikes.append(
            Spike(
                batch=point.batch,
                new_codes=point.new_codes,
                baseline=baseline,
                ratio=ratio,
                rule=RULE_RATIO,
                window=window,
                reason=(
                    f"batch {point.batch} admitted {point.new_codes} new codes, "
                    f"{against}, at or above the {policy.spike_factor}x spike factor "
                    f"and the {policy.spike_min_new_codes}-code floor."
                ),
            )
        )
    return spikes


def spike_at(
    curve: GrowthCurve | None,
    policy: CheckpointPolicy,
    *,
    batch: int | None = None,
) -> Spike | None:
    """The spike at one batch of this curve, or `None`.

    Selection, not decision: both `gaf.pipeline.slow_loop.should_checkpoint` and
    `gaf.pipeline.decision_matrix.evaluate_handover` ask the same question — "did *this*
    batch spike" — and asking it in one place is what stops the two from reading the
    same curve differently. ``batch`` defaults to the curve's last batch, which is the
    batch a checkpoint decision is being taken at.
    """
    if curve is None or not curve.points:
        return None
    wanted = batch if batch is not None else curve.points[-1].batch
    for spike in detect_spikes(curve, policy):
        if spike.batch == wanted:
            return spike
    return None
