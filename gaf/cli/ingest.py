"""`gaf ingest` — read a raw-response workbook into the canonical corpus JSON.

Attaches the survey question, repairs encoding damage at the boundary, and writes a
deterministic corpus JSON that every other command reads as `--data` or `--corpus`.
An encoding repair is recorded on the response metadata rather than applied silently
(`report.repaired_response_ids`), so the record of what changed travels with the data.

Serves **reliability**: this is the one place raw survey text becomes the pipeline's
canonical shape, and `corpus_content_hash` gives every downstream artefact something
fixed to cite as provenance.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from gaf.cli._common import _DEFAULTS, EXIT_OK, CliError, _banner, _out
from gaf.config import QUESTION_VARIANTS, RunConfig
from gaf.ingest.corpus import corpus_content_hash, load_corpus_with_report, write_corpus_json
from gaf.ingest.xlsx import SpreadsheetFormatError


def cmd_ingest(args: argparse.Namespace) -> int:
    """Read a raw-response workbook into the canonical corpus JSON."""
    source = Path(args.xlsx)
    if not source.exists():
        raise CliError(f"{source} does not exist")
    config = RunConfig(question_variant=args.question_variant)
    try:
        responses, report = load_corpus_with_report(source, config=config)
    except (SpreadsheetFormatError, ValueError, OSError) as exc:
        raise CliError(f"cannot ingest {source}: {exc}") from exc
    out = Path(args.out)
    write_corpus_json(responses, out)

    _banner("gaf ingest", str(source))
    _out(f"  {report.summary()}")
    _out(f"  content hash        {corpus_content_hash(responses)}")
    _out(f"  response ids        {', '.join(str(r.id) for r in responses)}")
    if report.repaired_response_ids:
        _out(
            "  encoding repaired   "
            + ", ".join(str(r) for r in report.repaired_response_ids)
            + "  (recorded on the response metadata, never applied silently)"
        )
    _out(f"  written             {out}")
    return EXIT_OK


def add_ingest_parser(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    ingest = sub.add_parser(
        "ingest",
        help="read a raw-response workbook into the canonical corpus JSON",
        description=(
            "Read a NarrativeState-style workbook, attach the survey question, repair "
            "encoding damage at the boundary, and write a deterministic corpus JSON."
        ),
    )
    ingest.add_argument("--xlsx", required=True, help="the raw-response workbook")
    ingest.add_argument(
        "--question-variant",
        choices=sorted(QUESTION_VARIANTS),
        default=_DEFAULTS.question_variant,
        help="which survey question generated these responses (default: %(default)s)",
    )
    ingest.add_argument("--out", required=True, help="where to write corpus.json")
    ingest.set_defaults(handler=cmd_ingest)
