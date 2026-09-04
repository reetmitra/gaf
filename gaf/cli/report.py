"""`gaf report` — render the run report and the HTML codebook explorer.

Reads a finished run directory (`run.json`, written by `gaf run`) and renders it
twice: the plain-text run report with its CHECKS section and caveats, and a single
self-contained HTML page for reading the codebook — no script, no network request, no
external asset, so it opens in any browser exactly as written.

Serves **transparency**: an HTML codebook explorer and a run report with a CHECKS
section are this build's answer to the black-box problem, and both are rendered from
the same `RunArtefact` the audit log already grounds, never recomputed here.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from gaf.cli._common import EXIT_OK, _load_run, _out, _write
from gaf.report.html import render_codebook_html
from gaf.report.run_report import render_run_report


def cmd_report(args: argparse.Namespace) -> int:
    """Render the run report and the HTML codebook explorer from a finished run."""
    run_dir = Path(args.run)
    artefact = _load_run(run_dir)
    out = Path(args.out) if args.out else run_dir
    out.mkdir(parents=True, exist_ok=True)

    text = render_run_report(artefact)
    page = render_codebook_html(artefact)
    report_path = _write(out / "report.txt", text)
    html_path = _write(out / "codebook.html", page)

    _out(text.rstrip("\n"))
    _out("")
    _out(f"Run report written to      {report_path}")
    _out(f"Codebook explorer written  {html_path}")
    _out(
        "  The explorer is one self-contained file — no script, no network request, "
        "no external asset. Open it in any browser."
    )
    return EXIT_OK


def add_report_parser(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    report = sub.add_parser(
        "report",
        help="render the run report and the HTML codebook explorer",
        description=(
            "Render a finished run: the plain-text report with its CHECKS section, and "
            "a single self-contained HTML page for reading the codebook."
        ),
    )
    report.add_argument("--run", required=True, help="a run directory written by `gaf run`")
    report.add_argument("--out", help="where to write the artefacts (default: the run directory)")
    report.set_defaults(handler=cmd_report, offline=True)
