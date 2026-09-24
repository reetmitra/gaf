"""Assembles the whole `gaf` argparse tree from each subcommand module.

`build_parser` is the one place that knows every subcommand exists; every other
module in this package knows only its own. Reading this file top to bottom is
reading the whole CLI surface — one entry point, one command per line, nothing hidden
behind a dynamic registration mechanism.
"""

from __future__ import annotations

import argparse

import gaf
from gaf.cli.analyse import add_analyse_parser
from gaf.cli.check import add_check_parser
from gaf.cli.checkpoint import add_checkpoint_parser
from gaf.cli.codebook import add_codebook_parser
from gaf.cli.ingest import add_ingest_parser
from gaf.cli.report import add_report_parser
from gaf.cli.run import add_run_parser
from gaf.cli.validate import add_validate_parser
from gaf.cli.views import add_views_parser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gaf",
        description=(
            "Grounded AI Futures — a reproducible hybrid human-LLM grounded-theory "
            "coding pipeline. Every command runs offline by default: mock model "
            "clients, the lexical embedding fallback, no API key and no network."
        ),
        epilog=(
            "Exit codes: 0 success; 1 an ERROR finding or a refused fit; 2 usage; "
            "3 unreadable or unsupported input."
        ),
    )
    parser.add_argument("--version", action="version", version=f"gaf {gaf.__version__}")
    sub = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    add_ingest_parser(sub)
    add_run_parser(sub)
    add_check_parser(sub)
    add_analyse_parser(sub)
    add_validate_parser(sub)
    add_report_parser(sub)
    add_checkpoint_parser(sub)
    add_codebook_parser(sub)
    add_views_parser(sub)

    return parser
