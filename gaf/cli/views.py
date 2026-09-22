"""`gaf views` — build `views.html` from whatever artefacts exist.

Eleven views of one coding in one self-contained page: the codebook tree, code
frequencies, the response-by-code heatmap, co-occurrence, the pattern map, the affinity
map, code growth beside the timeline, the loop handover, the reorganisation trail, the
crosswalk, and the clusters and saturation curve. `gaf report` writes the page as part
of rendering a run; this command builds it alone, which is what makes it usable on a
run that has been analysed since, or on a hand coding that has no run behind it at all.

Two shapes of input:

* ``--run <dir>`` — a run directory written by `gaf run`, plus the analysis directory
  beside it (``<run>/analysis`` by default, or ``--analysis``).
* ``--assignments`` with ``--codebook`` and ``--data`` — a human coding. Everything
  that needs no audit log is drawn; the decision trace and the reorganisation trail
  say plainly that only a run records them.

**A missing artefact is never an error.** Each view that depends on a file `gaf
analyse` or `gaf report` writes prints, when the file is absent, the command that
creates it. A page built from half a run is still a page, and telling the reader which
command to run next is more use than refusing to draw the other ten views.

No respondent text reaches the page: code names, family names, response numbers, counts
and scores only. The Mermaid codebook tree is written beside it, for the same reason.

Serves **transparency**, and **interpretive depth**: eleven views of one coding exist
so that a reader can disagree with it.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from gaf.cli._common import (
    EXIT_OK,
    EXIT_USAGE,
    CliError,
    _banner,
    _config_from_args,
    _load_run,
    _out,
    _write,
    load_artefact,
    load_codebook_arg,
    load_corpus_arg,
)
from gaf.report.views import (
    TREE_MMD_NAME,
    VIEWS,
    VIEWS_HTML_NAME,
    ViewsData,
    render_views_html,
    views_from_coding,
    views_from_run,
)

__all__ = ["add_views_parser", "cmd_views", "write_views_page"]


def write_views_page(out_path: Path, data: ViewsData) -> tuple[Path, Path | None]:
    """Write `views.html`, and the Mermaid codebook tree beside it.

    Returns ``(page, tree)``; `tree` is ``None`` when there is no codebook to draw one
    from. The two files always land in the same directory, because the page links to
    the tree by name and a relative link that pointed elsewhere would be a broken one.
    """
    page = _write(out_path, render_views_html(data))
    mermaid = data.mermaid()
    tree = _write(out_path.parent / TREE_MMD_NAME, mermaid) if mermaid else None
    return page, tree


def _describe(data: ViewsData) -> list[str]:
    available = data.available()
    lines = []
    for index, (anchor, title) in enumerate(VIEWS, start=1):
        mark = "drawn" if available[anchor] else "not available"
        lines.append(f"  {index:>2}. {title:<28} {mark}")
    return lines


def cmd_views(args: argparse.Namespace) -> int:
    """Build the views page from a run directory, or from a bare human coding."""
    if bool(args.run) == bool(args.assignments):
        raise CliError(
            "gaf views needs exactly one of --run (a run directory) or --assignments "
            "(a coding, with --codebook and --data).",
            EXIT_USAGE,
        )

    analysis_dir = Path(args.analysis) if args.analysis else None
    if args.run:
        run_dir = Path(args.run)
        artefact = _load_run(run_dir)
        data = views_from_run(artefact, run_dir, analysis_dir=analysis_dir)
        subject = str(run_dir)
        default_out = run_dir / VIEWS_HTML_NAME
    else:
        path = Path(args.assignments)
        artefact_in = load_artefact(path)
        config = _config_from_args(args, run_id="views", output_dir=path.parent)
        codebook = load_codebook_arg(Path(args.codebook) if args.codebook else None)
        if codebook is None:
            codebook = artefact_in.codebook
        corpus = load_corpus_arg(Path(args.data) if args.data else None, config=config)
        data = views_from_coding(
            artefact_in.assignments,
            codebook=codebook,
            responses=corpus,
            analysis=config.analysis,
            policy=config.checkpoints,
            batch_size=int(args.batch_size),
            source_label=f"human coding {path.name}",
            analysis_dir=analysis_dir,
        )
        subject = str(path)
        default_out = Path(VIEWS_HTML_NAME)

    out_path = Path(args.out) if args.out else default_out
    if out_path.is_dir():
        out_path = out_path / VIEWS_HTML_NAME

    _banner("gaf views", subject)
    _out(
        f"  {data.source_label} — {data.n_responses} response(s) carrying a code, "
        f"{len(data.frequencies)} code(s), {len(data.families)} famil(ies)"
    )
    _out("")
    for line in _describe(data):
        _out(line)

    page, tree = write_views_page(out_path, data)
    _out("")
    _out(f"Views page written to      {page}")
    if tree is not None:
        _out(f"Mermaid codebook tree      {tree}")
    _out(
        "  One self-contained file — no script, no network request, no external asset, "
        "and no respondent text. Open it in any browser."
    )
    return EXIT_OK


def add_views_parser(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    views = sub.add_parser(
        "views",
        help="build views.html: eleven views of one coded dataset",
        description=(
            "Build one self-contained HTML page with eleven views of a coding: the "
            "codebook tree, code frequencies, the response-by-code heatmap, "
            "co-occurrence, the pattern map, the affinity map, code growth and the "
            "timeline, the loop handover, the reorganisation trail, the crosswalk, and "
            "the clusters and saturation curve. A missing artefact produces a section "
            "naming the command that writes it, never an error."
        ),
    )
    views.add_argument("--run", help="a run directory written by `gaf run`")
    views.add_argument(
        "--assignments",
        help="a coding with no run behind it: assignments JSON/xlsx, or a codebook JSON",
    )
    views.add_argument("--codebook", help="codebook JSON, for the tree and the affinity map")
    views.add_argument("--data", help="corpus JSON or xlsx — fixes the row universe")
    views.add_argument(
        "--analysis",
        help="where `gaf analyse` wrote its artefacts (default: <run>/analysis when it exists)",
    )
    views.add_argument("--out", help=f"where to write the page (default: <run>/{VIEWS_HTML_NAME})")
    views.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="batch size for the growth curve and the timeline of a coding (default: %(default)s)",
    )
    views.set_defaults(handler=cmd_views, offline=True)
