"""`gaf validate` — concurrent validation against the golden set, and the lexical check.

Two deterministic validations, no model consulted by either.

`gaf validate agreement` is Alqazlan-style concurrent validation: precision, recall,
F1 and Cohen's kappa at code level, span-overlap agreement at segment level, and —
the interpretive output the headline rate hides — the two unmatched lists, over-coding
and blind spots. Serves **interpretive depth**: the unmatched lists are reported
rather than folded into one number, so a reviewer sees where the machine and the human
diverged, not just how often they agreed.

`gaf validate lexical` is the model-free L1 vocabulary check: it fits the pooled table
under a continuous target and two binarised cuts and compares the vocabularies each
recovers. Low overlap is a finding to report, never a failure — this command exits
non-zero only on a malformed table or a cut the data cannot support (`RefusedFitError`).
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from gaf.analysis.agreement import concurrent_validation, descriptions_from_codebook
from gaf.analysis.lexical import (
    LexicalInputError,
    RefusedFitError,
    ScoredResponse,
    run_lexical_validation,
    scored_table,
)
from gaf.analysis.matrix import assignments_from_codebook
from gaf.cli._common import (
    _DEFAULTS,
    EXIT_FINDINGS,
    EXIT_OK,
    EXIT_USAGE,
    CliError,
    _add_seed,
    _banner,
    _config_from_args,
    _embedder_for,
    _out,
    _read_json,
    _write,
    load_artefact,
    load_codebook_arg,
    load_corpus_arg,
)
from gaf.config import LexicalConfig


def cmd_validate_agreement(args: argparse.Namespace) -> int:
    """Concurrent validation of a machine coding against the human golden set."""
    human = load_artefact(Path(args.human))
    machine = load_artefact(Path(args.machine))
    config = _config_from_args(args, run_id="validate", output_dir=Path("."))
    corpus = load_corpus_arg(Path(args.data) if args.data else None, config=config)
    codebook = load_codebook_arg(Path(args.codebook) if args.codebook else None)
    if codebook is None and machine.codebook is not None:
        codebook = machine.codebook
    embedder = _embedder_for(config)

    report = concurrent_validation(
        human.assignments,
        machine.assignments,
        embedder=embedder,
        rules=config.rules,
        corpus=None if corpus is None else {r.id: r for r in corpus},
        descriptions=None if codebook is None else descriptions_from_codebook(codebook),
    )

    _banner("gaf validate agreement", f"{args.human} vs {args.machine}")
    _out(f"  human    {len(human.assignments)} row(s), {len(human.code_names)} code(s)")
    _out(f"  machine  {len(machine.assignments)} row(s), {len(machine.code_names)} code(s)")
    _out(
        "  corpus   "
        + (f"{args.data} — span-level comparison" if corpus is not None else "not supplied — segment level degrades to string containment")
    )
    _out("")
    _out(report.to_markdown())

    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        _write(out / "agreement.json", report.to_json_str())
        _write(out / "agreement.md", report.to_markdown())
        _out("")
        _out(f"Artefacts written to {out}")
    return EXIT_OK


def _lexical_rows(path: Path) -> list[dict[str, Any]]:
    """Read the pooled table, tolerating the corpus shape a scored corpus arrives in."""
    raw = _read_json(path)
    if isinstance(raw, dict):
        rows = raw.get("rows") or raw.get("responses")
        if rows is None:
            raise CliError(f'{path}: expected a list of rows, or {{"rows": [...]}}.')
    else:
        rows = raw
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise CliError(f"{path}: expected a list of row objects.")
    out: list[dict[str, Any]] = []
    for row in rows:
        record = dict(row)
        if "text" not in record and "content" in record:
            record["text"] = record["content"]
        if "response_id" not in record and "id" in record:
            record["response_id"] = record["id"]
        out.append(record)
    return out


def _scored_rows(args: argparse.Namespace, rows: list[dict[str, Any]]) -> list[ScoredResponse]:
    source = args.score_from
    codebook = load_codebook_arg(Path(args.codebook) if args.codebook else None)
    assignments = None if codebook is None else assignments_from_codebook(codebook)
    if source is None:
        return scored_table(rows, score_source="column", score_column=args.score_col)
    if source == "codes":
        if assignments is None:
            raise CliError(
                "--score-from codes derives the score from the codes applied to each "
                "response, so it needs --codebook.",
                EXIT_USAGE,
            )
        return scored_table(rows, score_source="code_count", assignments=assignments)
    if source.startswith("code-family:"):
        family = source.split(":", 1)[1].strip()
        if not family:
            raise CliError("--score-from code-family:<top_level> needs a family name.", EXIT_USAGE)
        if assignments is None:
            raise CliError(
                "--score-from code-family:<top_level> needs --codebook.", EXIT_USAGE
            )
        return scored_table(
            rows, score_source="family_code_count", assignments=assignments, family=family
        )
    raise CliError(
        f"unknown --score-from {source!r}; expected 'codes' or 'code-family:<top_level>'.",
        EXIT_USAGE,
    )


def cmd_validate_lexical(args: argparse.Namespace) -> int:
    """The model-free L1 vocabulary check. Low overlap is a finding, not a failure."""
    path = Path(args.table)
    if not path.exists():
        raise CliError(f"{path} does not exist")
    rows = _lexical_rows(path)
    config = _config_from_args(args, run_id="validate", output_dir=Path("."))

    _banner("gaf validate lexical", str(path))
    try:
        scored = _scored_rows(args, rows)
    except LexicalInputError as exc:
        raise CliError(f"{path}: {exc}") from exc

    lexical = config.lexical
    if args.bootstrap is not None:
        lexical = LexicalConfig(**{**lexical.to_json(), "bootstrap": int(args.bootstrap)})

    lines: list[str] = []
    try:
        result = run_lexical_validation(
            scored,
            config=lexical,
            seed=config.seed,
            codebook=load_codebook_arg(Path(args.codebook) if args.codebook else None),
            report=lines.append,
        )
    except RefusedFitError as exc:
        _out("")
        for line in lines:
            _out(line)
        _out("")
        _out("REFUSED — the fit was not attempted.")
        _out("")
        _out(str(exc))
        _out("")
        _out(
            "This is a verdict about the data, not a crash: a cut this unbalanced "
            "cannot support a stratified cross-validation, and an AUC from it would "
            "not mean anything. Pool more responses, or lower "
            "LexicalConfig.min_class_count deliberately and say so in the write-up."
        )
        return EXIT_FINDINGS
    except LexicalInputError as exc:
        raise CliError(f"{path}: {exc}") from exc

    _out("")
    for line in lines:
        _out(line)
    _out("")
    _out(result.to_markdown())
    _out("")
    _out(
        "Low overlap between the vocabularies is a finding to report, not a failed "
        "check: this command exits non-zero only on a malformed table or a refused fit."
    )
    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        _write(out / "lexical.json", result.to_json_str())
        _write(out / "lexical.md", result.to_markdown())
        _write(out / "lexical_methods.txt", result.methods_paragraph())
        _out("")
        _out(f"Artefacts written to {out}")
    return EXIT_OK


def add_validate_parser(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    validate = sub.add_parser(
        "validate",
        help="concurrent validation against the golden set, and the lexical check",
        description="The two deterministic validations. No model is consulted by either.",
    )
    validate_sub = validate.add_subparsers(dest="validate_kind", required=True, metavar="KIND")

    agreement = validate_sub.add_parser(
        "agreement",
        help="human-vs-machine agreement at code and segment level",
        description=(
            "Alqazlan-style concurrent validation. Reports precision, recall, F1 and "
            "Cohen's kappa at code level, span-overlap agreement at segment level, and "
            "the two unmatched lists — over-coding and blind spots — which are the "
            "interpretive output the headline rate hides."
        ),
    )
    agreement.add_argument("--human", required=True, help="the golden set (JSON or xlsx)")
    agreement.add_argument("--machine", required=True, help="the machine coding (JSON or xlsx)")
    agreement.add_argument("--data", help="corpus JSON or xlsx — makes the segment level a span comparison")
    agreement.add_argument("--codebook", help="codebook supplying code descriptions for the embedding")
    agreement.add_argument("--out", help="output directory")
    _add_seed(agreement)
    agreement.set_defaults(handler=cmd_validate_agreement, offline=True)

    lexical = validate_sub.add_parser(
        "lexical",
        help="the model-free L1 vocabulary check",
        description=(
            "Fit the pooled table under a continuous target and two binarised cuts, "
            "and compare the vocabularies each recovers. Low overlap is a finding to "
            "report; this command fails only on a malformed table or a refused fit."
        ),
    )
    lexical.add_argument("--table", required=True, help="the pooled scored table (JSON)")
    lexical.add_argument(
        "--score-col", default="score", help="column holding the score (default: %(default)s)"
    )
    lexical.add_argument(
        "--score-from",
        help="derive the score instead: 'codes' or 'code-family:<top_level>' (needs --codebook)",
    )
    lexical.add_argument("--codebook", help="codebook JSON, for a derived score and for the review sheet")
    lexical.add_argument(
        "--bootstrap",
        type=int,
        help=(
            "stratified bootstrap resamples per fit (default: LexicalConfig.bootstrap, "
            f"{_DEFAULTS.lexical.bootstrap}). L1 selection is unstable at this sample "
            "size, so this is what makes a selected word's stability readable."
        ),
    )
    lexical.add_argument("--out", help="output directory")
    _add_seed(lexical)
    lexical.set_defaults(handler=cmd_validate_lexical, offline=True)
