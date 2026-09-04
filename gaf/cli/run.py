"""`gaf run` — the fast loop over a corpus, with every artefact written to `--out`.

Two coders, the structural and semantic checks, the router, the store: this command
drives `gaf.pipeline.fast_loop.run_fast_loop` and writes everything it produces —
codebook, assignments, findings, the append-only audit log, the blackboard and the run
report — into one directory, so nothing about the run is only in memory once the
process exits.

**A run that completes exits 0 even when the coding produced ERROR findings.** `gaf
run` asks *"what did the coders propose and what did the checks find?"*, and findings
are its deliverable, not its verdict — that question belongs to `gaf check`. A dropped
fabricated quote is the check layer doing its job, not the run failing.

Serves **transparency**: every artefact a later `gaf report`, `gaf check`, `gaf
analyse` or `gaf checkpoint` reads is written here, in the open, including the
audit log that nothing else in the system is allowed to edit after the fact.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

import gaf
from gaf.cli._common import (
    EXIT_OK,
    CliError,
    _add_cache,
    _add_mode,
    _add_seed,
    _components,
    _config_from_args,
    _out,
    _write,
    _write_json,
)
from gaf.config import RunConfig
from gaf.ingest.corpus import corpus_content_hash, load_corpus_with_report
from gaf.ingest.xlsx import SpreadsheetFormatError
from gaf.models import Response
from gaf.pipeline.fast_loop import run_fast_loop
from gaf.report.run_report import RUN_JSON_NAME, RunArtefact, render_run_report
from gaf.store.blackboard import Blackboard


def _run_provenance(
    *, corpus_path: Path, responses: Sequence[Response], report: Any, config: RunConfig, out: Path
) -> dict[str, Any]:
    return {
        "gaf_version": gaf.__version__,
        "corpus_path": str(corpus_path),
        "corpus_source": report.source,
        "corpus_content_hash": corpus_content_hash(responses),
        "n_responses": len(responses),
        "question_variant": config.question_variant,
        "db_path": str(config.db_path) if config.db_path else None,
        "output_dir": str(out),
        "ingest": report.to_json(),
    }


def write_run_dir(out: Path, artefact: RunArtefact, board: Blackboard) -> None:
    """Everything a later `gaf report`, `gaf analyse` or `gaf checkpoint` needs."""
    out.mkdir(parents=True, exist_ok=True)
    _write(out / RUN_JSON_NAME, artefact.to_json_str())
    _write(out / "codebook.json", artefact.codebook.to_json_str())
    _write_json(out / "assignments.json", [a.to_json() for a in artefact.assignments])
    _write_json(out / "findings.json", artefact.report.to_json())
    _write_json(out / "stats.json", artefact.stats.to_json())
    events = board.audit(artefact.stats.run_id).events()
    _write(
        out / "audit.jsonl",
        "\n".join(
            json.dumps(event.to_json(), sort_keys=True, ensure_ascii=False) for event in events
        ),
    )


def cmd_run(args: argparse.Namespace) -> int:
    """The fast loop over a corpus, with every artefact written to --out."""
    corpus_path = Path(args.corpus)
    if not corpus_path.exists():
        raise CliError(f"{corpus_path} does not exist")
    run_id = args.run_id or corpus_path.stem
    out = Path(args.out) if args.out else Path("runs") / run_id
    out.mkdir(parents=True, exist_ok=True)

    config = _config_from_args(args, run_id=run_id, output_dir=out)
    config = config.with_(corpus_path=corpus_path, db_path=out / "gaf.sqlite")

    try:
        responses, ingest = load_corpus_with_report(corpus_path, config=config)
    except (SpreadsheetFormatError, ValueError, OSError) as exc:
        raise CliError(f"cannot read the corpus {corpus_path}: {exc}") from exc
    if not responses:
        raise CliError(f"{corpus_path} holds no responses")

    database = cast(Path, config.db_path)
    if database.exists():
        # A run directory is one run's output. Re-running must not append to the
        # previous run's append-only log, or two runs would share an audit trail.
        database.unlink()

    components = _components(config)
    with Blackboard(database) as board:
        result = run_fast_loop(responses, config=config, board=board, components=components)
        artefact = RunArtefact.from_result(
            result,
            config=config,
            provenance=_run_provenance(
                corpus_path=corpus_path, responses=responses, report=ingest, config=config, out=out
            ),
        )
        write_run_dir(out, artefact, board)

    text = render_run_report(artefact)
    _write(out / "report.txt", text)
    _out(text.rstrip("\n"))
    _out("")
    _out(f"Artefacts written to {out}:")
    for name in (
        RUN_JSON_NAME,
        "codebook.json",
        "assignments.json",
        "findings.json",
        "stats.json",
        "audit.jsonl",
        "report.txt",
        "gaf.sqlite",
    ):
        _out(f"  {out / name}")
    _out("")
    _out(f"Next: gaf report --run {out}")
    return EXIT_OK


def add_run_parser(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    run = sub.add_parser(
        "run",
        help="the fast loop: two coders, the checks, the router, the store",
        description=(
            "Code a corpus. Writes the codebook, the assignments, every finding, the "
            "audit log, the blackboard and the run report into --out. A run that "
            "completes exits 0 even when the coding produced ERROR findings: a dropped "
            "fabricated quote is the pipeline working."
        ),
    )
    run.add_argument("--corpus", required=True, help="corpus JSON or xlsx")
    run.add_argument("--out", help="run directory (default: runs/<run-id>)")
    run.add_argument("--run-id", help="run id (default: the corpus file stem)")
    run.add_argument("--batch-size", type=int, help="responses per frozen snapshot")
    _add_cache(run)
    _add_seed(run)
    _add_mode(run)
    run.set_defaults(handler=cmd_run)
