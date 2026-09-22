"""`gaf` — the single entry point.

One `argparse` tree over the whole pipeline: ingest a spreadsheet, run the fast loop,
check an artefact, run the analysis tail, validate against the golden set, render the
run report and the codebook explorer, open a slow-loop checkpoint behind the human
gate, and build a codebook from a coding a person has already finished. This package
owns `main`, the dispatch loop that turns a parsed command into an exit code; each
subcommand — its logic, its help text and its own docstring naming the validation
principle it serves — lives in its own module (`ingest.py`, `run.py`, `check.py`,
`analyse.py`, `validate.py`, `report.py`, `checkpoint.py`, `codebook.py`), assembled
into one parser by `parser.py`. `_common.py` holds what more than one of them needs.

Three rules hold everywhere in this package.

**Offline is the default.** Every command runs with mock model clients, the lexical
embedding fallback, no API key and no network. `--live` is opt-in and builds provider
clients from `RunConfig.models`; nothing in the test suite or CI ever takes that path.

**The two command families have different exit-code semantics, deliberately.**
`gaf check` asks *"is this artefact valid?"*, so it exits 1 if and only if a check
emitted an ERROR — ERROR being reserved for structural certainty of invalidity — and a
CI pipeline should fail on that. `gaf run` and `gaf analyse` ask *"what did the coders
propose and what did the checks find?"*, and findings are their deliverable: they exit
0 whenever the work completes, and non-zero only on an actual failure — bad arguments,
an unreadable corpus, an exception. Conflating the two would mean the pipeline could
never be demonstrated on a corpus containing a single unverifiable quote, which is
every real corpus. A WARN never fails anything anywhere: it is a judgment about
meaning, kept and flagged and carried to the human gate.

**Nothing here recomputes a check.** Commands call the check functions, collect
`CheckReport`s and hand them to one renderer. There are no print-only diagnostics.

Exit codes::

    0   success — and, for `gaf check`, no ERROR finding
    1   the artefact failed: an ERROR finding, or a refused lexical fit
    2   usage error (argparse)
    3   input error: unreadable, malformed or unsupported input; a missing provider SDK

Vocabulary is grounded theory's throughout (ADR-0005).
"""

from __future__ import annotations

import sys
from collections.abc import Sequence

from gaf.analysis.hca import DegenerateMatrixError
from gaf.cli._common import (
    EXIT_FINDINGS,
    EXIT_INPUT,
    EXIT_OK,
    EXIT_USAGE,
    CliError,
    live_components,
    load_artefact,
)
from gaf.cli.parser import build_parser
from gaf.ingest.xlsx import SpreadsheetFormatError

__all__ = [
    "EXIT_FINDINGS",
    "EXIT_INPUT",
    "EXIT_OK",
    "EXIT_USAGE",
    "CliError",
    "build_parser",
    "live_components",
    "load_artefact",
    "main",
]


def main(argv: Sequence[str] | None = None) -> int:
    """The console script. Returns the process exit code; never raises for the user."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        return int(args.handler(args))
    except CliError as exc:
        print(f"gaf: {exc}", file=sys.stderr)
        return exc.code
    except (SpreadsheetFormatError, DegenerateMatrixError) as exc:
        print(f"gaf: {exc}", file=sys.stderr)
        return EXIT_INPUT
    except KeyboardInterrupt:  # pragma: no cover - interactive only
        print("gaf: interrupted", file=sys.stderr)
        return EXIT_INPUT
