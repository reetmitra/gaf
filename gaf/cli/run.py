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

Three flags exist for the handover between the two loops (ADR-0035).

``--seed-codebook`` starts the fast loop from an existing codebook rather than from
nothing, so a run codes into an organisation a person already built. **The seed's own
evidence is held out**: a seeded run's codebook, assignments, occurrence matrix and
saturation curve describe *this* run's coding and no other. What the seed supplies is
structure — names, families, descriptions — which is what retrieval and the hierarchy
skeleton in the coder's prompt are built from; its evidence would only be a second,
older coding wearing this run's label. The run records the seed's content hash, and the
run report's CAVEATS section says in plain words what a seeded run costs.

``--halt-on-checkpoint`` stops after the first batch whose handover evaluation says a
checkpoint is due, and prints the two commands that continue the work. **Exit code 0**:
a halt is the designed behaviour, not a failure. The run still closes normally, because
a half-written run directory is worse than a short one.

``--skip-coded`` takes a run directory and leaves its responses alone, which is how a
halted run is resumed without coding anything twice. It also reads out of that
directory **how many responses have been coded since the last checkpoint** and carries
the number forward, so the hard floor keeps measuring how long it has been since a
human looked rather than how far into this particular process it is (R1 I1). When the
previous run's store is not there to say whether a checkpoint was taken, the command
says so on stdout and in ``run.json``, and counts every response that run coded as
still owed a look.

Serves **transparency**: every artefact a later `gaf report`, `gaf check`, `gaf
analyse` or `gaf checkpoint` reads is written here, in the open, including the
audit log that nothing else in the system is allowed to edit after the fact.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from dataclasses import replace
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
    _load_run,
    _out,
    _write,
    _write_json,
    load_codebook_arg,
)
from gaf.config import RunConfig
from gaf.ids import content_hash
from gaf.ingest.corpus import corpus_content_hash, load_corpus_with_report
from gaf.ingest.xlsx import SpreadsheetFormatError
from gaf.models import Code, Codebook, Response
from gaf.pipeline.fast_loop import run_fast_loop
from gaf.report.run_report import RUN_JSON_NAME, RunArtefact, render_run_report
from gaf.store.blackboard import Blackboard

#: How many response ids a skip line prints before it stops listing them.
_MAX_LISTED_IDS = 20


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


# --------------------------------------------------------------------------- #
# --seed-codebook
# --------------------------------------------------------------------------- #


def seed_from(path: Path) -> tuple[Codebook, dict[str, Any]]:
    """Load a seed codebook, hold its evidence out, and describe where it came from.

    **Why the evidence is held out.** A seed's evidence is a previous coding's
    occurrences. Carried into this run's codebook it would reach `assignments.json`
    through nothing (those rows come only from responses this run coded) but would reach
    the occurrence matrix, the saturation curve and every count derived from the
    codebook through `gaf.analysis.matrix.assignments_from_codebook`, which projects
    *every* verified quote a codebook holds. The same coding would then be counted
    twice: once in the run that produced it and once in the run that was seeded from it.
    Holding it out makes "this run's outputs describe this run's coding" true by
    construction rather than by a caveat nobody reads. The seed file still holds it, and
    `gaf validate agreement` is where two codings are meant to meet. ADR-0035.

    Each seeded code keeps its name, its family, its description and its own metadata,
    and gains `meta["seeded_from"]` (the seed's content hash) and
    `meta["seed_evidence_held_out"]` (how many rows it arrived with), so the run's
    codebook says which of its codes it did not discover.
    """
    codebook = load_codebook_arg(path)
    if codebook is None:  # pragma: no cover - load_codebook_arg raises first
        raise CliError(f"{path} holds no codebook")
    digest = content_hash(codebook.to_json_str())
    held_out = 0
    codes: dict[str, Code] = {}
    for code_id, code in codebook.codes.items():
        meta = dict(code.meta)
        meta["seeded_from"] = digest
        meta["seed_evidence_held_out"] = len(code.evidence)
        held_out += len(code.evidence)
        codes[code_id] = replace(code, evidence=[], meta=meta)
    sources = sorted(
        {
            str(value)
            for code in codebook.codes.values()
            for key in ("source", "description_source")
            if (value := code.meta.get(key))
        }
    )
    seeded_from = {
        "path": str(path),
        "content_hash": digest,
        "codes": len(codebook),
        "families": len(codebook.families()),
        "described": sum(1 for code in codebook.codes.values() if code.description),
        "evidence_held_out": held_out,
        "sources": sources,
    }
    return Codebook(codes=codes), seeded_from


# --------------------------------------------------------------------------- #
# --skip-coded
# --------------------------------------------------------------------------- #


def coded_response_ids(run_dir: Path) -> list[int]:
    """Every response id a previous run coded, from its own `run.json`.

    The per-response outcomes are the authority rather than `assignments.json`: a
    response the loop prepared and coded may legitimately have produced no assignment
    row at all — a duplicate, or one whose every candidate was dropped — and re-coding
    it would be coding it twice.
    """
    artefact = _load_run(run_dir)
    ids = {int(outcome["response_id"]) for outcome in artefact.outcomes if "response_id" in outcome}
    ids |= {assignment.response_id for assignment in artefact.assignments}
    return sorted(ids)


def responses_since_checkpoint(run_dir: Path) -> tuple[int, str]:
    """``(responses coded since the last checkpoint, how that was established)``.

    The hard floor asks how long it has been since a human looked at the codebook
    (R1 I1), and a resumed run has to carry that forward: a run halted at response 50
    and resumed without anybody opening the gate is still fifty responses overdue, and
    restarting the count at zero would postpone the floor by another fifty.

    Three cases, all reported rather than assumed:

    * the previous run's store records a **decided checkpoint** — the count is the
      responses that run coded after it, and whatever it had carried forward is
      cleared, because the look happened;
    * the store records **none** — the count is everything that run coded plus
      whatever *it* carried forward, so the chain survives any number of resumes;
    * the store is **absent or unreadable** — nothing can be established, so the
      count is the responses that run coded and the caller says so. Assuming a
      checkpoint that may not have happened would suppress the one trigger that exists
      for the run where nothing else ever fires; assuming one did not is the safe
      direction.
    """
    artefact = _load_run(run_dir)
    coded = sum(1 for outcome in artefact.outcomes if "response_id" in outcome)
    carried = int(artefact.stats.responses_since_checkpoint or 0)
    inherited = max(carried - coded, 0)

    database = run_dir / "gaf.sqlite"
    if not database.exists():
        return coded + inherited, (
            f"{database} is not there, so whether a checkpoint was taken cannot be "
            "established; counting every response that run coded as still owed a look"
        )
    try:
        with Blackboard(database) as board:
            checkpoints = board.read_checkpoints(artefact.stats.run_id)
    except Exception as exc:  # pragma: no cover - a store an older build wrote
        return coded + inherited, (
            f"{database} could not be read ({type(exc).__name__}), so whether a "
            "checkpoint was taken cannot be established; counting every response that "
            "run coded as still owed a look"
        )
    decided = [record for record in checkpoints if record.status != "proposed"]
    if not decided:
        return coded + inherited, (
            f"no checkpoint was taken in {run_dir}, so its {coded} coded response(s)"
            + (f" and {inherited} carried into it" if inherited else "")
            + " are still owed a human look"
        )
    last = max(record.at_response_count for record in decided)
    since = max(coded - last, 0)
    return since, (
        f"a checkpoint was taken in {run_dir} at {last} response(s) coded; "
        f"{since} response(s) have been coded since"
    )


def _describe_skip(skipped: Sequence[int], run_dir: Path) -> None:
    listed = ", ".join(str(response_id) for response_id in skipped[:_MAX_LISTED_IDS])
    if len(skipped) > _MAX_LISTED_IDS:
        listed += f", ... (+{len(skipped) - _MAX_LISTED_IDS} more)"
    _out(f"Resuming: skipped {len(skipped)} response(s) already coded in {run_dir}.")
    _out(f"  ids: {listed}")
    _out(
        "  This run's report describes only what it coded itself; the two runs together "
        "cover the corpus."
    )
    _out("")


# --------------------------------------------------------------------------- #
# Writing
# --------------------------------------------------------------------------- #


def write_run_dir(out: Path, artefact: RunArtefact, board: Blackboard) -> None:
    """Everything a later `gaf report`, `gaf analyse` or `gaf checkpoint` needs."""
    out.mkdir(parents=True, exist_ok=True)
    _write(out / RUN_JSON_NAME, artefact.to_json_str())
    _write(out / "codebook.json", artefact.codebook.to_json_str())
    _write_json(out / "assignments.json", [a.to_json() for a in artefact.assignments])
    _write_json(out / "findings.json", artefact.report.to_json())
    stats = artefact.stats.to_json()
    seeded_from = artefact.provenance.get("seeded_from")
    if seeded_from is not None:
        # `RunStats` is the loop's own shape and carries no seed field; the seed is a
        # fact about how this command was invoked, so it is recorded beside the stats
        # rather than smuggled into them.
        stats["seeded_from"] = seeded_from
    _write_json(out / "stats.json", stats)
    events = board.audit(artefact.stats.run_id).events()
    _write(
        out / "audit.jsonl",
        "\n".join(
            json.dumps(event.to_json(), sort_keys=True, ensure_ascii=False) for event in events
        ),
    )


def _report_halt(artefact: RunArtefact, *, out: Path, corpus_path: Path) -> None:
    """What stopped, where, and the two commands that continue the work."""
    stats = artefact.stats
    trace = stats.decision_trace
    last = trace[-1] if trace else {}
    fired = ", ".join(last.get("fired") or ()) or last.get("trigger", "unknown")
    _out("")
    _out("=" * 78)
    _out(f"HALTED at batch {stats.halted_at_batch} — a checkpoint is due.")
    _out("=" * 78)
    _out("")
    _out(f"  rule(s) fired        {fired}")
    _out(f"  trigger              {last.get('trigger', 'unknown')}")
    _out(f"  reason               {last.get('reason', '')}")
    _out(f"  responses coded      {stats.n_responses}")
    _out(f"  responses remaining  {stats.responses_uncoded} still to code")
    _out("")
    _out("  This is the designed behaviour, not an error. Two commands continue the work:")
    _out("")
    _out(f"    gaf checkpoint --run {out}")
    _out(
        f"    gaf run --corpus {corpus_path} --seed-codebook {out / 'codebook.json'} "
        f"--skip-coded {out}"
    )
    _out("")
    _out(
        "  The first opens the slow loop behind the human gate. The second resumes the "
        "coding from the codebook the gate left behind, without coding anything twice."
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

    provenance = _run_provenance(
        corpus_path=corpus_path, responses=responses, report=ingest, config=config, out=out
    )

    seed: Codebook | None = None
    if args.seed_codebook:
        seed_path = Path(args.seed_codebook)
        if not seed_path.exists():
            raise CliError(f"{seed_path} does not exist")
        seed, seeded_from = seed_from(seed_path)
        provenance["seeded_from"] = seeded_from
        _out(
            f"Seeded from {seed_path}: {seeded_from['codes']} code(s) in "
            f"{seeded_from['families']} famil(ies), {seeded_from['described']} described. "
            f"{seeded_from['evidence_held_out']} evidence row(s) held out of this run."
        )
        _out("")

    carried_forward = 0
    if args.skip_coded:
        previous = Path(args.skip_coded)
        already = set(coded_response_ids(previous))
        skipped = sorted(response.id for response in responses if response.id in already)
        responses = [response for response in responses if response.id not in already]
        if not responses:
            raise CliError(
                f"every response in {corpus_path} was already coded in {previous}; there "
                "is nothing left to code."
            )
        provenance["skipped_from"] = {
            "run": str(previous),
            "skipped": len(skipped),
            "response_ids": skipped,
        }
        provenance["n_responses"] = len(responses)
        carried_forward, basis = responses_since_checkpoint(previous)
        provenance["skipped_from"]["responses_since_checkpoint"] = carried_forward
        provenance["skipped_from"]["responses_since_checkpoint_basis"] = basis
        _describe_skip(skipped, previous)
        _out(f"  responses since the last checkpoint, carried forward: {carried_forward}")
        _out(f"  ({basis})")
        _out("")

    database = cast(Path, config.db_path)
    if database.exists():
        # A run directory is one run's output. Re-running must not append to the
        # previous run's append-only log, or two runs would share an audit trail.
        database.unlink()

    components = _components(config)
    with Blackboard(database) as board:
        if "seeded_from" in provenance:
            # Its own row, written before the run begins so the log reads in the order
            # the work happened. `run_started` now carries the same facts (they belong
            # with the run's own numbers, not beside them), and this row stays because
            # it is what a reader looking for "was this run seeded" already greps for.
            board.register_run(config)
            board.audit(config.run_id).emit(
                "run_seeded", scope="run", subject=config.run_id, **provenance["seeded_from"]
            )
        result = run_fast_loop(
            responses,
            config=config,
            board=board,
            components=components,
            codebook=seed,
            halt_on_checkpoint=bool(args.halt_on_checkpoint),
            seeded_from=provenance.get("seeded_from"),
            responses_since_checkpoint_at_start=carried_forward,
        )
        artefact = RunArtefact.from_result(result, config=config, provenance=provenance)
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
    if artefact.stats.halted_at_batch is not None:
        _report_halt(artefact, out=out, corpus_path=corpus_path)
        return EXIT_OK
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
    run.add_argument(
        "--seed-codebook",
        help=(
            "start the fast loop from this codebook instead of from nothing. Its "
            "evidence is held out, so this run's outputs describe this run's coding "
            "only; the report says what a seeded run costs (ADR-0035)"
        ),
    )
    run.add_argument(
        "--halt-on-checkpoint",
        action="store_true",
        help=(
            "stop after the first batch that says a checkpoint is due, and print the "
            "two commands that continue the work. A halt exits 0"
        ),
    )
    run.add_argument(
        "--skip-coded",
        help="a run directory whose responses were already coded; they are not coded again",
    )
    _add_cache(run)
    _add_seed(run)
    _add_mode(run)
    run.set_defaults(handler=cmd_run)
