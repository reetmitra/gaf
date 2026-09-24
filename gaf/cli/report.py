"""`gaf report` — render every reading artefact a finished run supports.

Reads a finished run directory (`run.json`, written by `gaf run`) and renders it as a
set of files a person can open without a database or a Python prompt:

* `report.txt` — the plain-text run report with its CHECKS section and caveats;
* `codebook.html` — the self-contained codebook explorer, quotes and all;
* `timeline.json` / `.md` / `.svg` — when each code was born, what it became, and what
  the coders saw at each batch boundary, with the growth curve's spikes marked;
* `reorganisation_trail.json` / `.md` — one entry per checkpoint the slow loop opened,
  and the lineage of every code name that no longer exists;
* `decision_matrix.md` — the static matrix of what each loop decides and where;
* `views.html` and `tree.mmd` — eleven views of the dataset in one self-contained
  page, and the codebook as a Mermaid tree.

The two HTML pages differ on purpose. `codebook.html` exists to be **audited against
the corpus**, so it carries the evidence quotes; it is a working artefact and is not
shareable. `views.html` carries no respondent text at all — code names, family names,
response numbers, counts and scores — so it is the one that can leave the machine.

The timeline and the trail are read from the run's own store; a run directory copied
without its `gaf.sqlite` still renders everything else, and the views page says which
command writes what is missing.

Serves **transparency**: every artefact here is rendered from the same `RunArtefact`
and the same audit log the run already grounds, never recomputed.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from gaf.cli._common import EXIT_OK, _load_run, _out, _write, _write_json
from gaf.cli.views import write_views_page
from gaf.report.html import render_codebook_html
from gaf.report.run_report import render_run_report, write_decision_matrix
from gaf.report.views import VIEWS_HTML_NAME, default_analysis_dir, views_from_run

#: What `gaf report` writes beside the two artefacts it has always written.
TIMELINE_JSON_NAME = "timeline.json"
TIMELINE_MD_NAME = "timeline.md"
TIMELINE_SVG_NAME = "timeline.svg"
TRAIL_JSON_NAME = "reorganisation_trail.json"
TRAIL_MD_NAME = "reorganisation_trail.md"


def cmd_report(args: argparse.Namespace) -> int:
    """Render the run report, the explorer, the timeline, the trail and the views page."""
    run_dir = Path(args.run)
    artefact = _load_run(run_dir)
    out = Path(args.out) if args.out else run_dir
    out.mkdir(parents=True, exist_ok=True)

    text = render_run_report(artefact)
    page = render_codebook_html(artefact)
    report_path = _write(out / "report.txt", text)
    html_path = _write(out / "codebook.html", page)

    analysis_dir = Path(args.analysis) if args.analysis else default_analysis_dir(run_dir)
    data = views_from_run(artefact, run_dir, analysis_dir=analysis_dir)

    written: list[tuple[str, Path]] = []
    if data.timeline is not None and data.timeline_figure is not None:
        written.append(
            ("Timeline", _write_json(out / TIMELINE_JSON_NAME, data.timeline.to_json()))
        )
        written.append(("  as Markdown", _write(out / TIMELINE_MD_NAME, data.timeline.to_markdown())))
        written.append(("  as SVG", _write(out / TIMELINE_SVG_NAME, data.timeline_figure)))
    if data.trail is not None:
        written.append(
            ("Reorganisation trail", _write_json(out / TRAIL_JSON_NAME, data.trail.to_json()))
        )
        written.append(
            ("  as Markdown", _write(out / TRAIL_MD_NAME, data.trail.to_markdown()))
        )
    matrix_path = write_decision_matrix(out, artefact)
    views_path, tree_path = write_views_page(out / VIEWS_HTML_NAME, data)

    _out(text.rstrip("\n"))
    _out("")
    _out(f"Run report written to      {report_path}")
    _out(f"Codebook explorer written  {html_path}")
    for label, path in written:
        _out(f"{label:<26} {path}")
    _out(f"{'Decision matrix':<26} {matrix_path}")
    _out(f"{'Views page':<26} {views_path}")
    if tree_path is not None:
        _out(f"{'Mermaid codebook tree':<26} {tree_path}")
    if data.timeline is None:
        _out(
            "  No timeline or reorganisation trail: this run directory has no readable "
            "gaf.sqlite, which is where the audit log lives."
        )
    _out(
        "  Both HTML pages are self-contained — no script, no network request, no "
        "external asset. codebook.html carries the evidence quotes and is a working "
        "artefact; views.html carries no respondent text at all."
    )
    return EXIT_OK


def add_report_parser(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    report = sub.add_parser(
        "report",
        help="render the run report, the explorer, the timeline, the trail and views.html",
        description=(
            "Render a finished run: the plain-text report with its CHECKS section, the "
            "self-contained HTML codebook explorer, the timeline of code generation and "
            "change, the reorganisation trail, the static decision matrix, and "
            "views.html — eleven views of the dataset with no respondent text in them."
        ),
    )
    report.add_argument("--run", required=True, help="a run directory written by `gaf run`")
    report.add_argument("--out", help="where to write the artefacts (default: the run directory)")
    report.add_argument(
        "--analysis",
        help="where `gaf analyse` wrote its artefacts (default: <run>/analysis when it exists)",
    )
    report.set_defaults(handler=cmd_report, offline=True)
