"""`gaf checkpoint` — open a slow-loop checkpoint behind the human gate.

The Refactorer proposes an edit script over the whole codebook — split, re-parent,
merge, batch-rename — and a human accepts, rejects or edits each operation.  Without a
terminal the gate is `RejectAllGate` and the checkpoint is a no-op: **never an
auto-accept**. Accepting a restructuring without a human present is exactly the
decision-task overlay ADR-0004 exists to avoid, so this command refuses to guess at
consent it cannot obtain.

Serves **interpretive depth**: the human gate sits at codebook-refactor level, where
the task is generative and the division of labour — machine proposes, human decides —
is fixed in advance, rather than at the per-item decision level the Vaccaro et al.
meta-analysis finds harmful.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from gaf.agents.refactorer import RefactorerAgent
from gaf.cli._common import (
    EXIT_OK,
    CliError,
    _banner,
    _cached,
    _embedder_for,
    _live_client,
    _load_run,
    _out,
    _run_config_from_json,
)
from gaf.llm.base import CallLog
from gaf.llm.mock import MockRefactorerClient
from gaf.store.blackboard import Blackboard


def _slow_loop() -> Any:
    """Import the slow loop, or explain precisely what is missing.

    The module is a fixed contract — `run_checkpoint`, `Gate`, `ConsoleGate`,
    `RejectAllGate` — so this dispatch is written against those names whether or not
    the module is present in a given checkout.
    """
    try:
        import gaf.pipeline.slow_loop as slow_loop
    except ImportError as exc:
        raise CliError(
            "gaf.pipeline.slow_loop is not available in this checkout, so a checkpoint "
            f"cannot be opened ({exc}). Every other command is unaffected."
        ) from exc
    missing = [
        name
        for name in ("run_checkpoint", "Gate", "ConsoleGate", "RejectAllGate")
        if not hasattr(slow_loop, name)
    ]
    if missing:
        raise CliError(
            "gaf.pipeline.slow_loop is present but does not export "
            f"{', '.join(missing)}; this build expects run_checkpoint, Gate, "
            "ConsoleGate and RejectAllGate."
        )
    return slow_loop


def _interactive(requested: bool) -> bool:
    """A checkpoint may only prompt when there is genuinely a human at the terminal."""
    return bool(requested and sys.stdin.isatty() and sys.stdout.isatty())


def cmd_checkpoint(args: argparse.Namespace) -> int:
    """Open a slow-loop checkpoint: the Refactorer proposes, a human decides.

    Non-interactive sessions get `RejectAllGate`, so a checkpoint with nobody present
    is a no-op that changes nothing. It is never an auto-accept: accepting a refactor
    without a human is exactly the decision-task overlay ADR-0004 exists to avoid.
    """
    slow_loop = _slow_loop()
    run_dir = Path(args.run)
    artefact = _load_run(run_dir)
    database = run_dir / "gaf.sqlite"
    if not database.exists():
        raise CliError(f"{database} does not exist; a checkpoint continues a finished run.")

    config = _run_config_from_json(artefact.config)
    if not artefact.snapshot_ids:
        raise CliError(f"{run_dir}: the run recorded no snapshot to continue from.")
    snapshot_id = artefact.snapshot_ids[-1]

    client = (
        _cached(MockRefactorerClient(config.models.refactorer), config)
        if config.offline
        else _cached(_live_client(config.models.refactorer, config), config)
    )
    agent = RefactorerAgent(client, config=config, call_log=CallLog())
    embedder = _embedder_for(config)

    interactive = _interactive(args.interactive)
    gate = slow_loop.ConsoleGate() if interactive else slow_loop.RejectAllGate()

    _banner("gaf checkpoint", str(run_dir))
    _out(f"  snapshot     {snapshot_id}")
    _out(f"  codebook     {len(artefact.codebook)} code(s)")
    _out(f"  gate         {'ConsoleGate (interactive)' if interactive else 'RejectAllGate'}")
    if not interactive:
        _out(
            "  A checkpoint with no human present is a no-op, never an auto-accept. "
            "Re-run with --interactive from a terminal to review the proposal."
        )
    _out("")

    with Blackboard(database) as board:
        result = slow_loop.run_checkpoint(
            board=board,
            config=config,
            codebook=artefact.codebook,
            snapshot_id=snapshot_id,
            agent=agent,
            embedder=embedder,
            gate=gate,
            trigger=args.trigger,
        )
    _out(_describe_checkpoint(result))
    return EXIT_OK


def _describe_checkpoint(result: Any) -> str:
    """Render whatever the slow loop returned, without assuming its private shape."""
    to_json = getattr(result, "to_json", None)
    if callable(to_json):
        return json.dumps(to_json(), sort_keys=True, ensure_ascii=False, indent=2)
    return str(result)


def add_checkpoint_parser(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    checkpoint = sub.add_parser(
        "checkpoint",
        help="open a slow-loop checkpoint behind the human gate",
        description=(
            "The Refactorer proposes an edit script over the whole codebook; a human "
            "accepts, rejects or edits each operation. Without a terminal the gate is "
            "RejectAllGate and the checkpoint is a no-op — never an auto-accept."
        ),
    )
    checkpoint.add_argument("--run", required=True, help="a run directory written by `gaf run`")
    checkpoint.add_argument(
        "--interactive",
        action="store_true",
        help="review the proposal at the terminal (ConsoleGate)",
    )
    checkpoint.add_argument(
        "--trigger", default="manual", help="why this checkpoint opened (default: %(default)s)"
    )
    checkpoint.set_defaults(handler=cmd_checkpoint)
