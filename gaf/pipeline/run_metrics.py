"""The run statistics a reader asks for first: who agreed, whom the judge backed, how long
it took and what it cost (ADR-0053).

`RunStats` already holds the counts the loop needs to reconcile itself. This module adds
the four things the PI's questions are built from, and computes them from the blackboard
rather than from the loop, for two reasons. The blackboard is the one place that holds
*every* run, including the ones written before this module existed, so the same function
answers for `runs/process200` as for a live run. And the audit log is lossless where the
`findings` table is not: findings are content-addressed and collapse repeats, the audit
log keeps one row per decision.

* **Coder agreement (M1).** Of the places where coder A's and coder B's candidates were
  compared, how many matched outright (at or above tau_high), how many fell in the grey
  zone (the only band that costs a judge call), how many were disputed (below tau_low),
  and how many were proposed by one coder only. The unit is the *comparison*: a matched
  pair of candidates, or one candidate the other coder never proposed. Beside it, how
  M2 routed the accepted candidates (merge, create, or the judge).
* **Judge siding.** The one place a judge chooses between the coders is an M1 grey-zone
  ruling, and its two verdicts are KEEP (both readings stay) or DROP (the second
  candidate, which is always coder B's, goes). So "siding" has exactly two outcomes in
  practice: coder A's candidate stands alone, or neither side is preferred. Coder B can
  never be backed alone. That asymmetry is the prompt's, not the data's, and the report
  says so, because a reader who saw "B: 0%" without it would conclude something false.
  The share of A is flagged above 0.65: the judge shares a model with coder A and the
  prompt always shows A first (`judge_v1.py`), so a high share is self-preference or
  position bias. The prompt is not changed; this measures it.
* **Latency.** Per-call model time (`llm_calls.latency_ms`, which every live client
  records and which is zero for a mock call or a cache replay), summarised per call, per
  role and task, and per response. For a live run only, the wall-clock time per response
  from the audit log as well. An offline run reports none: its wall clock is the speed of
  this machine, not of any model, and printing it would make two identical runs differ.
* **Spend by role and task.** Calls, tokens in and out, dollars and cache hits, from
  `Blackboard.llm_usage`. The query the cost estimate was built from. With it, how many
  calls the model ended early (a refusal, a token limit), from `llm_calls.stop_reason`.

Everything here is a count, a share, an id or a code name. No respondent text, and no
judge reasoning (which paraphrases it), enters any of it.

Validation principle: **transparency** — the numbers a methods reviewer asks for are
computed from the record, by one function, for every run alike.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any

from gaf.store.audit import AuditEvent
from gaf.store.blackboard import Blackboard, LLMCallRecord

__all__ = [
    "METRICS_SCHEMA",
    "SIDING_FLAG_SHARE",
    "SIDING_MIN_DECISIONS",
    "coder_agreement",
    "compute_run_metrics",
    "judge_siding",
    "latency_summary",
    "spend_summary",
]

METRICS_SCHEMA = "gaf.run_metrics/1"

#: A coder-A share above this is flagged. The judge shares coder A's model and the
#: prompt shows A first, so a majority this clear is more likely the arrangement than
#: the coding (PLAN B5).
SIDING_FLAG_SHARE = 0.65

#: Below this many rulings a share is a headline about a handful. The flag is still
#: computed, and the block says it is unreliable.
SIDING_MIN_DECISIONS = 20

_SIDING_BASIS = (
    "M1 grey-zone rulings, the only judge decisions that arbitrate between coder A's and "
    "coder B's candidates. DROP removes the second candidate, which is always coder B's, "
    "so coder A's stands alone; KEEP keeps both readings, so neither side is preferred. "
    "judge-v1 cannot back coder B alone: its coder B share is zero by construction, and "
    "the coder A share is the DROP rate. The judge shares coder A's model and sees A "
    "first, so a high coder A share is self-preference or position bias, which the "
    "prompt cannot separate."
)


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #


def _share(count: int, whole: int) -> float | None:
    return round(count / whole, 4) if whole else None


def _tally(count: int, whole: int) -> dict[str, Any]:
    return {"count": count, "share": _share(count, whole)}


def _percentile(sorted_values: Sequence[float], fraction: float) -> float:
    """Linear-interpolated percentile of a sorted, non-empty sequence."""
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = fraction * (len(sorted_values) - 1)
    low = math.floor(position)
    high = math.ceil(position)
    weight = position - low
    return sorted_values[low] * (1.0 - weight) + sorted_values[high] * weight


def _distribution(values: Sequence[float], *, digits: int) -> dict[str, Any]:
    """``n``, mean, median, 90th percentile, maximum and total; ``None`` when empty."""
    if not values:
        return {"n": 0, "mean": None, "median": None, "p90": None, "max": None, "total": None}
    ordered = sorted(values)
    return {
        "n": len(ordered),
        "mean": round(sum(ordered) / len(ordered), digits),
        "median": round(_percentile(ordered, 0.5), digits),
        "p90": round(_percentile(ordered, 0.9), digits),
        "max": round(ordered[-1], digits),
        "total": round(sum(ordered), digits),
    }


def _items(payload: Mapping[str, Any], key: str) -> list[Mapping[str, Any]]:
    raw = payload.get(key) or []
    return [item for item in raw if isinstance(item, Mapping)]


# --------------------------------------------------------------------------- #
# (a) Coder agreement
# --------------------------------------------------------------------------- #


def _m1_counts(events: Sequence[AuditEvent]) -> dict[str, int]:
    """M1 comparisons by outcome, read back from the router's `candidates_accepted` rows.

    The router records both sides of a non-agreed pair (coder A's accepted, coder B's
    accepted or dropped), so a pair is two entries and a judge's DROP is one accepted
    and one dropped. The arithmetic below undoes that and nothing else.
    """
    accepted: Counter[tuple[str, bool]] = Counter()
    dropped: Counter[tuple[str, bool]] = Counter()
    for event in events:
        if event.event != "candidates_accepted":
            continue
        for item in _items(event.payload, "accepted"):
            accepted[(str(item.get("origin", "")), bool(item.get("escalated")))] += 1
        for item in _items(event.payload, "dropped"):
            dropped[(str(item.get("origin", "")), bool(item.get("escalated")))] += 1

    judged_kept = accepted[("grey", True)]
    judged_dropped = dropped[("grey", True)]
    return {
        "agreed": sum(n for (origin, _), n in accepted.items() if origin == "agreed"),
        "grey_judged": (judged_kept + judged_dropped) // 2,
        "grey_unresolved": accepted[("grey", False)] // 2,
        "disputed": sum(n for (origin, _), n in accepted.items() if origin == "disputed") // 2,
        "unmatched_a": sum(n for (origin, _), n in accepted.items() if origin == "unmatched_a"),
        "unmatched_b": sum(n for (origin, _), n in accepted.items() if origin == "unmatched_b"),
        "judge_drop": judged_dropped,
        "judge_keep": (judged_kept - judged_dropped) // 2,
    }


def _routing(events: Sequence[AuditEvent]) -> dict[str, Any]:
    """How M2 routed the accepted candidates: by geometry, or to the judge."""
    geometry: Counter[str] = Counter()
    judged: Counter[str] = Counter()
    for event in events:
        if event.event != "route_chosen":
            continue
        geometry[str(event.payload.get("route", ""))] += 1
        if event.payload.get("escalated"):
            judged[str(event.payload.get("applied", ""))] += 1
    total = sum(geometry.values())
    return {
        "candidates": total,
        "merge": _tally(geometry["MERGE"], total),
        "create": _tally(geometry["CREATE"], total),
        "grey_zone": _tally(geometry["JUDGE"], total),
        "judged_applied": {
            "MERGE": judged["MERGE"],
            "CREATE": judged["CREATE"],
        },
    }


def coder_agreement(events: Sequence[AuditEvent]) -> dict[str, Any]:
    """Shares of M1 comparisons that agreed outright, fell in the grey zone, or were disputed."""
    counts = _m1_counts(events)
    grey = counts["grey_judged"] + counts["grey_unresolved"]
    dispute = counts["disputed"] + counts["unmatched_a"] + counts["unmatched_b"]
    total = counts["agreed"] + grey + dispute
    return {
        "unit": (
            "M1 comparison: a matched pair of coder A and coder B candidates, or one "
            "candidate the other coder never proposed"
        ),
        "comparisons": total,
        "agreed_outright": _tally(counts["agreed"], total),
        "grey_zone": {
            **_tally(grey, total),
            "judged": counts["grey_judged"],
            "unresolved_no_judge": counts["grey_unresolved"],
        },
        "disputed_or_unmatched": {
            **_tally(dispute, total),
            "disputed": counts["disputed"],
            "unmatched_a": counts["unmatched_a"],
            "unmatched_b": counts["unmatched_b"],
        },
        "routing": _routing(events),
    }


# --------------------------------------------------------------------------- #
# (b) Judge siding
# --------------------------------------------------------------------------- #


def judge_siding(events: Sequence[AuditEvent]) -> dict[str, Any]:
    """Which coder the judge backed when it ruled between them, flagged above 0.65 for A."""
    counts = _m1_counts(events)
    a_count = counts["judge_drop"]
    neither = counts["judge_keep"]
    decisions = a_count + neither
    a_share = _share(a_count, decisions)
    return {
        "basis": _SIDING_BASIS,
        "decisions": decisions,
        "coder_a": _tally(a_count, decisions),
        "coder_b": _tally(0, decisions),
        "neither": _tally(neither, decisions),
        "threshold": SIDING_FLAG_SHARE,
        "flag": a_share is not None and a_share > SIDING_FLAG_SHARE,
        "reliable": decisions >= SIDING_MIN_DECISIONS,
    }


# --------------------------------------------------------------------------- #
# (c) Latency
# --------------------------------------------------------------------------- #


def _parse_time(stamp: str) -> datetime | None:
    try:
        return datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        return None


def _wall_clock(events: Sequence[AuditEvent]) -> dict[str, Any] | None:
    """Seconds per response, and for the whole run, from the audit log's own clock."""
    started: dict[str, datetime] = {}
    finished: dict[str, datetime] = {}
    run_start: datetime | None = None
    run_end: datetime | None = None
    for event in events:
        moment = _parse_time(event.created_at)
        if moment is None:
            continue
        if event.event == "response_prepared":
            started.setdefault(event.subject, moment)
        elif event.event == "assignments_written":
            finished[event.subject] = moment
        elif event.event == "run_started":
            run_start = moment
        elif event.event == "run_completed":
            run_end = moment
    seconds = [
        (finished[subject] - begin).total_seconds()
        for subject, begin in started.items()
        if subject in finished
    ]
    if not seconds:
        return None
    return {
        "per_response_s": _distribution(seconds, digits=2),
        "run_total_s": (
            round((run_end - run_start).total_seconds(), 2)
            if run_start is not None and run_end is not None
            else None
        ),
    }


def latency_summary(
    calls: Sequence[LLMCallRecord], events: Sequence[AuditEvent], *, offline: bool
) -> dict[str, Any]:
    """Per-call, per-role-and-task and per-response model time; wall clock when live.

    Only calls that reached a provider count: a cache replay is recorded at zero and
    would drag every mean towards nothing. A call with no recorded time (every mock
    call) is left out for the same reason, so an offline run says ``measured: false``
    rather than reporting a mean of zero.
    """
    timed = [call for call in calls if not call.cache_hit and call.latency_ms > 0]
    by_key: dict[tuple[str, str], list[float]] = defaultdict(list)
    by_response: dict[str, float] = defaultdict(float)
    for call in timed:
        by_key[(call.role, call.task)].append(call.latency_ms)
        if call.subject.startswith("response:"):
            by_response[call.subject] += call.latency_ms
    return {
        "measured": bool(timed),
        "per_call_ms": _distribution([call.latency_ms for call in timed], digits=1),
        "by_role_task_ms": [
            {"role": role, "task": task, **_distribution(values, digits=1)}
            for (role, task), values in sorted(by_key.items())
        ],
        "per_response_model_s": _distribution(
            [total / 1000.0 for total in by_response.values()], digits=2
        ),
        "wall_clock": None if offline else _wall_clock(events),
    }


# --------------------------------------------------------------------------- #
# (d) Spend by role and task
# --------------------------------------------------------------------------- #


def spend_summary(
    usage: Sequence[Mapping[str, Any]],
    *,
    responses: int,
    stop_reasons: Mapping[str, int] | None = None,
) -> dict[str, Any]:
    """Totals and per-role rows over `Blackboard.llm_usage`, and dollars per response.

    `stop_reasons` is `Blackboard.llm_stop_reasons`: how many calls ended in a refusal or
    a token limit rather than a finished reply, which `fail_safes` alone does not say.
    """
    totals = {
        key: sum(int(row.get(key, 0)) for row in usage)
        for key in (
            "calls",
            "billed_calls",
            "cache_hits",
            "fail_safes",
            "stopped_early",
            "input_tokens",
        )
    }
    output_tokens = sum(int(row["output_tokens"]) for row in usage)
    cost = round(sum(float(row["cost_usd"]) for row in usage), 6)
    by_role: dict[str, dict[str, Any]] = {}
    for row in usage:
        bucket = by_role.setdefault(
            str(row["role"]),
            {
                "role": str(row["role"]),
                "calls": 0,
                "billed_calls": 0,
                "cache_hits": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cost_usd": 0.0,
            },
        )
        for key in ("calls", "billed_calls", "cache_hits", "input_tokens", "output_tokens"):
            bucket[key] += int(row[key])
        bucket["cost_usd"] = round(bucket["cost_usd"] + float(row["cost_usd"]), 6)
    return {
        **totals,
        "output_tokens": output_tokens,
        "cost_usd": cost,
        "stop_reasons": dict(stop_reasons or {}),
        "responses": responses,
        "usd_per_response": round(cost / responses, 6) if responses else None,
        "by_role_task": [dict(row) for row in usage],
        "by_role": [by_role[role] for role in sorted(by_role)],
    }


# --------------------------------------------------------------------------- #
# The whole block
# --------------------------------------------------------------------------- #


def compute_run_metrics(board: Blackboard, run_id: str, *, offline: bool) -> dict[str, Any]:
    """Every run statistic of this module for one run, JSON-shaped and deterministic.

    Safe to call on a run that predates this module: it reads only tables and events
    that have existed since the store was written. A run with no `candidates_accepted`
    rows (a run the fast loop never reached) yields zero comparisons and ``None`` shares.
    """
    events = board.audit(run_id).events()
    responses = sum(1 for event in events if event.event == "assignments_written")
    return {
        "schema": METRICS_SCHEMA,
        "coder_agreement": coder_agreement(events),
        "judge_siding": judge_siding(events),
        "latency": latency_summary(board.read_llm_calls(run_id), events, offline=offline),
        "spend": spend_summary(
            board.llm_usage(run_id),
            responses=responses,
            stop_reasons=board.llm_stop_reasons(run_id),
        ),
    }
