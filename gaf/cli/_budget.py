"""The CLI side of `--max-usd` (ADR-0053): reading the cap, counting what a run has spent.

`gaf.llm.budget` knows how to stop a call. This module knows where the money already
spent is written down, so that a cap means *this work* and not *this process*.

**What a cap counts.** The billed dollars in the blackboard's `llm_calls` table for the
run (`Blackboard.llm_spend`), plus those of every run it was resumed from. A resumed
run (`gaf run --skip-coded DIR`) is a new run directory with a new blackboard, so the
chain is followed through the ``skipped_from`` link the resumed run already records in
its `run.json` provenance; a `gaf checkpoint` on a run adds its Refactorer spend to the
same database and so to the same total. Nothing here writes to a database.

**What it cannot count.** A run directory that has been moved or deleted has no ledger
to read. That is reported as a warning and counted as unknown, not silently as zero.

**Exit code 4** means a command stopped because of the cap. `gaf run` itself exits 0
when it halts, as it does for a checkpoint halt (ADR-0035): it closes normally with every
artefact written, and the halt is its designed behaviour. The commands that have nothing
to show when stopped part-way (`gaf checkpoint`, `gaf codebook define`, `gaf check`)
exit 4 so a script cannot mistake an unfinished command for a finished one.
"""

from __future__ import annotations

import argparse
import json
import math
from collections.abc import Callable
from pathlib import Path
from typing import Any

from gaf.cli._common import EXIT_USAGE, CliError
from gaf.config import RunConfig
from gaf.llm.budget import BudgetExceededError, SpendBudget, guard_agents, unpriced_hosted_roles
from gaf.store.blackboard import Blackboard

__all__ = [
    "EXIT_BUDGET",
    "add_max_usd",
    "apply_cap",
    "budget_from_args",
    "capped",
    "cumulative_spend",
    "spend_cap_error",
]

EXIT_BUDGET = 4

#: How many `--skip-coded` links are followed before the chain is declared a loop.
_MAX_CHAIN = 50


def add_max_usd(parser: argparse.ArgumentParser) -> None:
    """Register `--max-usd` on a parser that does not take it from `_add_mode`."""
    parser.add_argument(
        "--max-usd",
        type=float,
        metavar="USD",
        help=(
            "stop before the first model call that would start once the billed spend of "
            "this run has reached USD. Counts the dollars recorded for this run, including "
            "earlier runs it was resumed from; cache replays are free and never count. "
            "Overshoots by at most the one call in flight when the cap was crossed"
        ),
    )


def _spend_in(run_dir: Path) -> tuple[float | None, str | None]:
    """``(billed dollars recorded in run_dir's blackboard, the run's skip-coded parent)``.

    ``None`` for the dollars when the ledger cannot be read. The parent is the directory
    this run was resumed from, as its own `run.json` recorded it.
    """
    run_id: str | None = None
    parent: str | None = None
    try:
        document = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        run_id = str(document["result"]["run_id"])
        skipped = (document.get("provenance") or {}).get("skipped_from") or {}
        parent = str(skipped["run"]) if skipped.get("run") else None
    except (OSError, ValueError, KeyError, TypeError):
        pass
    database = run_dir / "gaf.sqlite"
    if not database.exists():
        return None, parent
    try:
        with Blackboard(database) as board:
            ids = [run_id] if run_id else [record.run_id for record in board.runs()]
            return sum(board.llm_spend(each) for each in ids), parent
    except Exception:
        return None, parent


def cumulative_spend(run_dir: Path) -> tuple[float, list[dict[str, Any]]]:
    """Billed dollars recorded for the run in `run_dir` and for every run it resumed.

    Returns the total and one ``{"run", "usd"}`` row per directory read, newest first;
    ``usd`` is ``None`` (and ``"unreadable"`` is true) for a directory with no ledger.
    """
    total = 0.0
    sources: list[dict[str, Any]] = []
    seen: set[Path] = set()
    current: Path | None = run_dir
    while current is not None and len(sources) < _MAX_CHAIN:
        resolved = current.resolve()
        if resolved in seen:
            break
        seen.add(resolved)
        spent, parent = _spend_in(current)
        if spent is None:
            sources.append({"run": str(current), "usd": None, "unreadable": True})
        else:
            total += spent
            sources.append({"run": str(current), "usd": round(spent, 6)})
        current = Path(parent) if parent else None
    return total, sources


def budget_from_args(
    args: argparse.Namespace,
    *,
    config: RunConfig,
    baseline: tuple[float, list[dict[str, Any]]] | None = None,
) -> SpendBudget | None:
    """The `SpendBudget` the command line asked for, or ``None`` when it asked for none.

    Refuses, before any model is touched: a cap that is not a positive number; a live
    run with a hosted model whose price is zero (the cap could never trip, which is the
    one way it fails silently); and a cap already reached by the spend `baseline`
    carries, because starting a command that will be refused at its first call only
    wastes the setup in front of it.
    """
    cap = getattr(args, "max_usd", None)
    if cap is None:
        return None
    if not math.isfinite(cap) or cap <= 0:
        raise CliError(f"--max-usd must be a positive amount of dollars, got {cap!r}", EXIT_USAGE)
    if not config.offline:
        unpriced = unpriced_hosted_roles(config.models)
        if unpriced:
            roles = ", ".join(f"{spec.role} ({spec.provider}:{spec.model})" for spec in unpriced)
            raise CliError(
                "--max-usd needs a price for every hosted model, and these have none "
                f"(input_usd_per_mtok and output_usd_per_mtok are both 0): {roles}. Without "
                "one the cap would never see their spend. Set the rates in the profile or "
                "the registry.",
                EXIT_USAGE,
            )
    total, sources = baseline if baseline is not None else (0.0, [])
    budget = SpendBudget(cap_usd=float(cap), baseline_usd=total, baseline_sources=sources)
    if budget.exhausted:
        raise spend_cap_error(
            BudgetExceededError(cap_usd=budget.cap_usd, cumulative_usd=budget.cumulative_usd),
            before="starting",
        )
    return budget


def spend_cap_error(refusal: BudgetExceededError, *, before: str = "finishing") -> CliError:
    """The error a command raises when the cap stopped it. Exit code 4."""
    return CliError(
        f"{refusal} (--max-usd, before {before}). Completed calls are in the response "
        "cache and cost nothing to repeat; raise --max-usd to continue.",
        EXIT_BUDGET,
    )


def apply_cap(args: argparse.Namespace, config: RunConfig, *agents: Any) -> SpendBudget | None:
    """Read `--max-usd` and, when it was given, guard every agent's client with it.

    For the commands that make live calls but keep no run ledger of their own
    (`gaf check`, `gaf codebook define`): the cap counts what this one invocation bills.
    """
    budget = budget_from_args(args, config=config)
    if budget is not None:
        guard_agents(budget, agents)
    return budget


def capped[T](call: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """Call `call`, turning a spend-cap refusal into the CLI's own error (exit code 4)."""
    try:
        return call(*args, **kwargs)
    except BudgetExceededError as refusal:
        raise spend_cap_error(refusal) from refusal
