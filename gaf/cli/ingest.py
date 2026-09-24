"""`gaf ingest` — read a raw-response workbook or CSV into the canonical corpus JSON.

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

#: What the survey's own file names say about which prompt version produced them. The
#: State sample ("in 2050, what kind of roles") is v3; the Process sample ("from now to
#: 2050, what impacts") is v2. The default variant is v2, which is a trap for a State
#: file ingested without the flag: the State sample was once coded under the Process
#: question that way (ADR-0029). The name is a hint, not an authority, so a mismatch is
#: reported on the ingest line and never silently corrected.
_FILENAME_HINTS: tuple[tuple[str, str], ...] = (("state", "v3"), ("process", "v2"))


def variant_hint(source: Path, variant: str) -> str | None:
    """One sentence if the file name suggests a different question than ``variant``."""
    name = source.name.casefold()
    for token, expected in _FILENAME_HINTS:
        if token in name and expected != variant:
            return (
                f"the file name says '{token}', which is the {expected} question, but "
                f"--question-variant is {variant}; pass --question-variant {expected} if "
                "this is that survey"
            )
    return None


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
    if report.trimmed_disagreements:
        _out(
            "  Trimmed vs All      "
            + ", ".join(str(r) for r in report.trimmed_disagreements)
            + "  (the two columns disagree by more than whitespace; Trimmed used)"
        )
    question = QUESTION_VARIANTS[args.question_variant]
    _out(f"  question            {args.question_variant}: {question[:60]}...")
    hint = variant_hint(source, args.question_variant)
    if hint:
        _out(f"  WARNING             {hint}")
    _out(f"  written             {out}")
    return EXIT_OK


def add_ingest_parser(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    ingest = sub.add_parser(
        "ingest",
        help="read a raw-response workbook or CSV into the canonical corpus JSON",
        description=(
            "Read a corpus in any shape the PI's files arrive in -- a headed workbook, "
            "a numbered single-column workbook, or a numbered CSV -- attach the survey "
            "question, repair encoding damage at the boundary, and write a deterministic "
            "corpus JSON. The shape is detected, never declared."
        ),
    )
    # `--input` is the preferred spelling now that the argument is not always a
    # workbook; `--xlsx` is kept working because it is in the runbook and in scripts.
    ingest.add_argument(
        "--input",
        "--xlsx",
        dest="xlsx",
        required=True,
        metavar="PATH",
        help="the corpus file: a .xlsx/.xlsm workbook or a .csv (--xlsx is the old spelling)",
    )
    ingest.add_argument(
        "--question-variant",
        choices=sorted(QUESTION_VARIANTS),
        default=_DEFAULTS.question_variant,
        help="which survey question generated these responses (default: %(default)s)",
    )
    ingest.add_argument("--out", required=True, help="where to write corpus.json")
    ingest.set_defaults(handler=cmd_ingest)
