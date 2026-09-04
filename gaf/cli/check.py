"""`gaf check` — audit a codebook or a coding spreadsheet against S1-S6 and M3-M4.

Both on-disk shapes are admissible everywhere: the pipeline's codebook JSON and a
row-oriented coding spreadsheet, so the same code audits a machine coding and a hand
coding. This is this build's clearest instance of the design law "checks report; the
router and the audit log decide and record" — nothing here recomputes a check, and a
checker never mutates state; `structural_report` and `semantic_report` only collect
`CheckReport`s and hand them to one renderer, `render_checks_section`.

**The exit-code semantics are deliberate.** `gaf check` asks *"is this artefact
valid?"*, so it exits 1 if and only if a check emitted an ERROR — ERROR being reserved
for structural certainty of invalidity — and a CI pipeline should fail on that. A WARN
never fails this command anywhere: it is a judgment about meaning, kept and flagged
and carried to the human gate, never auto-resolved here.

Serves **transparency**: "every check in the pipeline emits through one contract, so
this table is the whole of what the run observed" is true of `gaf check` by
construction, not by convention.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from gaf.agents.judge import JudgeAgent
from gaf.checks.contracts import CheckReport
from gaf.checks.semantic import (
    check_code_evidence_fit,
    check_near_duplicate_leaves,
    compare_codebooks,
)
from gaf.checks.structural import (
    check_candidates,
    check_codebook,
    check_s1,
    check_s2,
    check_s2b,
    check_s3,
)
from gaf.cli._common import (
    EXIT_FINDINGS,
    EXIT_OK,
    EXIT_USAGE,
    Artefact,
    CliError,
    _add_cache,
    _add_mode,
    _add_seed,
    _banner,
    _config_from_args,
    _embedder_for,
    _judge_for,
    _out,
    _write_json,
    load_artefact,
    load_codebook_arg,
    load_corpus_arg,
)
from gaf.config import CodingRules, RunConfig
from gaf.embed.service import EmbeddingService
from gaf.ids import content_hash
from gaf.models import Assignment, Candidate, Code, Codebook, Evidence, Response
from gaf.report.run_report import render_checks_section

_CODER_LABEL = "spreadsheet"

#: The offline caveat printed by any command that consults the stand-in judge or the
#: lexical embedding fallback. ADR-0019 and ADR-0022.
_OFFLINE_SEMANTIC_CAVEAT = (
    "Offline: M3's code-to-evidence fit does not discriminate in the lexical fallback "
    "space (median fit 0.000) and M2's grey zone is empty, so fit scores and judge "
    "rulings below are artefacts of the stand-in embedder rather than findings about "
    "the coding. See ADR-0019 and ADR-0022."
)


# --------------------------------------------------------------------------- #
# Candidates derived from an artefact
# --------------------------------------------------------------------------- #


def candidates_by_response(artefact: Artefact) -> dict[int, list[Candidate]]:
    """Project an artefact into the per-response candidate batches the checks read.

    One candidate per (response, code) pair, carrying that pair's quotes as evidence.
    A codebook contributes the description it already holds and its S2 verdicts; a
    spreadsheet has neither, so its evidence arrives unverified and the quote-level
    checks stay silent until a corpus is supplied.
    """
    descriptions: dict[str, str] = {}
    verified: dict[tuple[int, str, str], Evidence] = {}
    if artefact.codebook is not None:
        for code in artefact.codebook.sorted_codes():
            descriptions[code.name] = code.description
            for evidence in code.evidence:
                verified[(evidence.response_id, code.name, evidence.quote)] = evidence

    grouped: dict[tuple[int, str], list[Evidence]] = {}
    for assignment in sorted(
        artefact.assignments, key=lambda a: (a.response_id, a.code, a.segment)
    ):
        key = (assignment.response_id, assignment.code)
        existing = verified.get((assignment.response_id, assignment.code, assignment.segment))
        grouped.setdefault(key, []).append(
            existing
            if existing is not None
            else Evidence(response_id=assignment.response_id, quote=assignment.segment)
        )

    out: dict[int, list[Candidate]] = {}
    for (response_id, code_name), quotes in sorted(grouped.items()):
        out.setdefault(response_id, []).append(
            Candidate(
                name=code_name,
                description=descriptions.get(code_name, ""),
                evidence=quotes,
                coder=_CODER_LABEL,
            )
        )
    return out


def _corpus_index(corpus: Sequence[Response] | None) -> dict[int, Response]:
    return {} if corpus is None else {r.id: r for r in corpus}


# --------------------------------------------------------------------------- #
# The check commands
# --------------------------------------------------------------------------- #

_STRUCTURAL_WITH_CORPUS = ("S1", "S2", "S2b", "S3", "S4", "S5")
_STRUCTURAL_WITHOUT_CORPUS = ("S1", "S2b", "S3")
_NEEDS_RESPONSE_TEXT = ("S2", "S4", "S5")


def structural_report(
    artefact: Artefact,
    corpus: Sequence[Response] | None,
    rules: CodingRules,
) -> tuple[CheckReport, dict[int, list[Candidate]], list[int]]:
    """S1-S6 over an artefact, the surviving candidates, and the responses it could not see.

    With a corpus the full per-response gate runs. Without one, only the checks that do
    not need the response text can run — S2 provenance, S4 segment discipline and S5
    code counts all reason about the response, and a check that cannot see its subject
    must not pretend to have passed.

    A coded response that is absent from the corpus is **reported, not raised**: S6
    already owns "this evidence names a response the corpus does not have", and turning
    a finding into a crash would put the CLI in the business of deciding, which is the
    one thing the design law forbids it.
    """
    report = CheckReport()
    index = _corpus_index(corpus)
    batches = candidates_by_response(artefact)
    existing = artefact.code_names
    survivors: dict[int, list[Candidate]] = {}
    unseen: list[int] = []

    for response_id in sorted(batches):
        candidates = batches[response_id]
        response = None if corpus is None else index.get(response_id)
        if response is None:
            if corpus is not None:
                unseen.append(response_id)
            kept, s1 = check_s1(candidates, rules)
            report.extend(s1)
            report.extend(check_s2b(kept, rules))
            report.extend(check_s3(kept, existing, rules))
            survivors[response_id] = kept
            continue
        kept, batch_report = check_candidates(candidates, response, existing, rules)
        report.extend(batch_report)
        survivors[response_id] = kept

    if artefact.codebook is not None:
        corpus_ids = None if corpus is None else [r.id for r in corpus]
        report.extend(check_codebook(artefact.codebook, corpus_ids, rules))
    return report, survivors, unseen


def _verified_candidates(
    artefact: Artefact,
    corpus: Sequence[Response] | None,
    rules: CodingRules,
) -> dict[int, list[Candidate]]:
    """Candidates with their quotes located, so M3 has verified evidence to score.

    S2 owns provenance and M3 owns fit; running the locator here is what keeps that
    division intact when the semantic checks are asked for on their own. The structural
    findings it produces belong to `gaf check structural` and are not reported twice.
    """
    index = _corpus_index(corpus)
    out: dict[int, list[Candidate]] = {}
    for response_id, candidates in sorted(candidates_by_response(artefact).items()):
        response = index.get(response_id)
        if response is None:
            out[response_id] = candidates
            continue
        kept, _ = check_s1(candidates, rules)
        located, _ = check_s2(kept, response, rules)
        out[response_id] = located
    return out


def semantic_report(
    artefact: Artefact,
    corpus: Sequence[Response] | None,
    *,
    config: RunConfig,
    other: Codebook | None,
    embedder: EmbeddingService,
    judge: JudgeAgent | None,
) -> tuple[CheckReport, dict[str, Any]]:
    """M3 and M4 over an artefact. M1 and M2 belong to the loop, not to a static file.

    M1 compares two coders on one response and M2 routes a candidate against the
    working codebook: both are decisions taken while coding, and neither has a subject
    in a finished artefact. What a finished artefact can still be asked is whether its
    quotes fit their codes (M3) and whether two of its leaves say the same thing (M4).
    """
    report = CheckReport()
    scope: dict[str, Any] = {}

    codebook = artefact.codebook or _codebook_from_assignments(artefact.assignments)
    near = check_near_duplicate_leaves(codebook, embedder, config.rules)
    report.extend(near.report)
    scope["M4 near-duplicate leaves"] = (
        f"{near.compared} leaf pair(s) compared, {len(near.pairs)} at or above "
        f"tau_high {config.rules.tau_high:g}"
    )

    if other is not None:
        comparison = compare_codebooks(
            codebook, other, embedder, config.rules, label_a="A", label_b="B"
        )
        report.extend(comparison.report)
        scope["M4 codebook comparison"] = (
            f"{len(comparison.matches)} matched pair(s); {len(comparison.only_in_a)} only "
            f"in A, {len(comparison.only_in_b)} only in B; agreement rate "
            f"{comparison.agreement_rate:.3f}"
        )
    else:
        scope["M4 codebook comparison"] = "not requested (--codebook2)"

    if corpus is None:
        scope["M3 code-to-evidence fit"] = "skipped — needs the response text (--data)"
        return report, scope

    batches = _verified_candidates(artefact, corpus, config.rules)
    index = _corpus_index(corpus)
    quotes = 0
    dropped = 0
    for response_id in sorted(batches):
        candidates = batches[response_id]
        if not candidates:
            continue
        response = index.get(response_id)
        result = check_code_evidence_fit(
            candidates,
            [response] if response is not None else None,
            embedder,
            config.rules,
            judge=judge,
        )
        report.extend(result.report)
        quotes += len(result.rulings)
        dropped += len(result.dropped)
    scope["M3 code-to-evidence fit"] = (
        f"{quotes} verified quote(s) scored at tau_fit {config.rules.tau_fit:g}; "
        f"{dropped} candidate(s) left with no supported evidence"
        + ("" if judge is not None else "; no judge wired, low fit reported as WARN")
    )
    return report, scope


def _codebook_from_assignments(assignments: Sequence[Assignment]) -> Codebook:
    """A codebook view of a spreadsheet, for the checks that need one.

    Descriptions are genuinely absent from a coding spreadsheet, so they are left
    empty rather than invented; `code_text` falls back to the name.
    """
    grouped: dict[str, list[Evidence]] = {}
    for assignment in sorted(assignments, key=lambda a: (a.code, a.response_id, a.segment)):
        grouped.setdefault(assignment.code, []).append(
            Evidence(
                response_id=assignment.response_id,
                quote=assignment.segment,
                verified=True,
                score=1.0,
            )
        )
    codes = [
        Code(
            id=f"code-{content_hash(name)}",
            name=name,
            description="",
            evidence=evidence,
        )
        for name, evidence in sorted(grouped.items())
    ]
    return Codebook(codes={c.id: c for c in codes})


def _check_scope(title: str, rows: dict[str, Any]) -> None:
    _out("")
    _out("SCOPE")
    _out("-----")
    width = max((len(key) for key in rows), default=0)
    for key, value in rows.items():
        _out(f"  {key.ljust(width)}  {value}")
    _out("")
    _out(f"({title})")


def cmd_check(args: argparse.Namespace) -> int:
    """Run the structural gate, the semantic checks, or both, over one artefact."""
    if bool(args.codebook) == bool(args.assignments):
        raise CliError(
            "give exactly one of --codebook or --assignments.", EXIT_USAGE
        )
    path = Path(args.codebook or args.assignments)
    artefact = load_artefact(path)
    config = _config_from_args(args, run_id="check", output_dir=Path("."))
    corpus = load_corpus_arg(Path(args.data) if args.data else None, config=config)

    kind = args.check_kind
    _banner(f"gaf check {kind}", str(path))

    scope: dict[str, Any] = {
        "artefact": artefact.describe(),
        "corpus": (
            f"{args.data} — {len(corpus)} response(s)" if corpus is not None else "not supplied (--data)"
        ),
    }
    report = CheckReport()

    if kind in {"structural", "all"}:
        structural, _, unseen = structural_report(artefact, corpus, config.rules)
        report.extend(structural)
        ran = list(_STRUCTURAL_WITH_CORPUS if corpus is not None else _STRUCTURAL_WITHOUT_CORPUS)
        if artefact.codebook is not None:
            ran.append("S6")
        scope["structural checks run"] = ", ".join(ran)
        if corpus is None:
            scope["structural skipped"] = (
                ", ".join(_NEEDS_RESPONSE_TEXT)
                + " — they reason about the response text; supply --data"
            )
        if unseen:
            scope["responses not in the corpus"] = (
                ", ".join(str(rid) for rid in unseen)
                + " — coded, but absent from --data, so their quotes have no provenance"
            )

    if kind in {"semantic", "all"}:
        embedder = _embedder_for(config)
        other = load_codebook_arg(Path(args.codebook2) if args.codebook2 else None)
        judge = _judge_for(config) if corpus is not None else None
        semantic, semantic_scope = semantic_report(
            artefact, corpus, config=config, other=other, embedder=embedder, judge=judge
        )
        report.extend(semantic)
        scope["embedding space"] = embedder.space_id
        scope.update(semantic_scope)

    _check_scope(
        "A WARN is kept and flagged; only an ERROR fails this command.", scope
    )
    if config.offline and kind in {"semantic", "all"}:
        _out("")
        _out(f"! {_OFFLINE_SEMANTIC_CAVEAT}")
    _out("")
    _out(render_checks_section(report, offline=config.offline))

    if args.out:
        target = _write_json(Path(args.out), report.to_json())
        _out("")
        _out(f"Findings written to {target}")
    return EXIT_OK if report.passed() else EXIT_FINDINGS


def add_check_parser(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    check = sub.add_parser(
        "check",
        help="run the checks over a codebook or a coding spreadsheet",
        description=(
            "Audit an artefact. Both shapes are accepted everywhere: the pipeline's "
            "codebook JSON and a row-oriented assignments file. Exits 1 if and only if "
            "a check emitted an ERROR; a WARN is kept, flagged and never fatal."
        ),
    )
    check_sub = check.add_subparsers(dest="check_kind", required=True, metavar="KIND")
    for kind, blurb in (
        ("structural", "S1-S6: schema, provenance, quote length, name grammar, segments, counts"),
        ("semantic", "M3 and M4: code-to-evidence fit, near-duplicate leaves, codebook comparison"),
        ("all", "the structural gate followed by the semantic checks"),
    ):
        node = check_sub.add_parser(kind, help=blurb, description=blurb)
        node.add_argument("--codebook", help="codebook JSON")
        node.add_argument("--assignments", help="row-oriented assignments JSON or xlsx")
        node.add_argument("--data", help="corpus JSON or xlsx (quote provenance and fit need it)")
        node.add_argument(
            "--codebook2", help="a second codebook to compare against (semantic only)"
        )
        node.add_argument("--out", help="write findings.json here")
        _add_cache(node)
        _add_seed(node)
        _add_mode(node)
        node.set_defaults(handler=cmd_check, check_kind=kind)
