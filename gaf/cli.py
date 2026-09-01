"""`gaf` — the single entry point.

One `argparse` tree over the whole pipeline: ingest a spreadsheet, run the fast loop,
check an artefact, run the analysis tail, validate against the golden set, render the
run report and the codebook explorer, and open a slow-loop checkpoint behind the human
gate.

Three rules hold everywhere in this module.

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

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import gaf
from gaf.agents.coder import CoderAgent
from gaf.agents.judge import JudgeAgent
from gaf.agents.refactorer import RefactorerAgent
from gaf.analysis.agreement import concurrent_validation, descriptions_from_codebook
from gaf.analysis.hca import (
    DegenerateMatrixError,
    cluster_responses,
    dendrogram_svg,
    saturation_curve,
    saturation_svg,
)
from gaf.analysis.lexical import (
    LexicalInputError,
    RefusedFitError,
    ScoredResponse,
    run_lexical_validation,
    scored_table,
)
from gaf.analysis.matrix import assignments_from_codebook, build_matrix
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
from gaf.config import (
    DEFAULT_LIVE_REGISTRY,
    QUESTION_VARIANTS,
    AnalysisConfig,
    CheckpointPolicy,
    CodingRules,
    EmbeddingSpaceConfig,
    LexicalConfig,
    ModelRegistry,
    ModelSpec,
    RunConfig,
)
from gaf.embed.service import EmbeddingService, MissingEmbeddingSDKError
from gaf.ids import content_hash
from gaf.ingest.corpus import (
    corpus_content_hash,
    load_corpus_with_report,
    write_corpus_json,
)
from gaf.ingest.xlsx import SpreadsheetFormatError, read_coded_xlsx
from gaf.llm import anthropic_client, gemini_client, openai_client
from gaf.llm.base import CallLog, LLMClient
from gaf.llm.cache import CachingLLMClient
from gaf.llm.mock import MockJudgeClient, MockRefactorerClient
from gaf.models import Assignment, Candidate, Code, Codebook, Evidence, Response
from gaf.pipeline.fast_loop import LoopComponents, offline_components, run_fast_loop
from gaf.report.html import render_codebook_html
from gaf.report.run_report import (
    RUN_JSON_NAME,
    RunArtefact,
    render_checks_section,
    render_run_report,
)
from gaf.store.blackboard import Blackboard

__all__ = ["CliError", "build_parser", "live_components", "main"]

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_USAGE = 2
EXIT_INPUT = 3

#: Where a live run gets each provider's credentials, and what installs its SDK.
#: Read only when `--live` is passed; the offline path needs none of them.
_LIVE_PROVIDERS: dict[str, tuple[Any, str, str]] = {
    "openai": (openai_client.OpenAIClient, openai_client.INSTALL_HINT, "OPENAI_API_KEY"),
    "gemini": (gemini_client.GeminiClient, gemini_client.INSTALL_HINT, "GOOGLE_API_KEY"),
    "anthropic": (
        anthropic_client.AnthropicClient,
        anthropic_client.INSTALL_HINT,
        "ANTHROPIC_API_KEY",
    ),
}

_MISSING_SDK_ERRORS = (
    openai_client.MissingProviderSDKError,
    gemini_client.MissingProviderSDKError,
    anthropic_client.MissingProviderSDKError,
)

#: The offline caveat printed by any command that consults the stand-in judge or the
#: lexical embedding fallback. ADR-0019 and ADR-0022.
_OFFLINE_SEMANTIC_CAVEAT = (
    "Offline: M3's code-to-evidence fit does not discriminate in the lexical fallback "
    "space (median fit 0.000) and M2's grey zone is empty, so fit scores and judge "
    "rulings below are artefacts of the stand-in embedder rather than findings about "
    "the coding. See ADR-0019 and ADR-0022."
)

_CODER_LABEL = "spreadsheet"

#: `RunConfig` is a slots dataclass, so its defaults are not readable off the class.
#: One instance carries them for the argparse defaults and the echo fallbacks.
_DEFAULTS = RunConfig()


class CliError(Exception):
    """A message for the user and the exit code that goes with it."""

    def __init__(self, message: str, code: int = EXIT_INPUT) -> None:
        super().__init__(message)
        self.code = code


# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #


def _out(text: str = "") -> None:
    print(text, file=sys.stdout)


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
    return path


def _write_json(path: Path, payload: Any) -> Path:
    return _write(path, json.dumps(payload, sort_keys=True, ensure_ascii=False, indent=2))


def _banner(title: str, subject: str = "") -> None:
    line = f"{title}{f' — {subject}' if subject else ''}"
    _out(line)
    _out("=" * min(len(line), 78))


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #


def _read_json(path: Path) -> Any:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CliError(f"cannot read {path}: {exc}") from exc
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise CliError(f"{path} is not valid JSON: {exc}") from exc


def _is_assignment_row(row: Any) -> bool:
    return isinstance(row, dict) and {"response_id", "segment", "code"} <= set(row)


def _is_code_row(row: Any) -> bool:
    return isinstance(row, dict) and "name" in row and "segment" not in row


@dataclass(frozen=True, slots=True)
class Artefact:
    """One coded artefact, in whichever of the two on-disk shapes it arrived.

    The pipeline writes a codebook; the PI writes a coding spreadsheet. Both are
    admissible everywhere a coded artefact is asked for, which is what lets the check
    commands audit a hand-coding with the same code that audits a machine one.
    """

    kind: str  # "codebook" | "assignments"
    path: Path
    assignments: list[Assignment]
    codebook: Codebook | None = None

    @property
    def code_names(self) -> list[str]:
        if self.codebook is not None:
            return self.codebook.names()
        return sorted({a.code for a in self.assignments})

    def describe(self) -> str:
        if self.kind == "codebook":
            assert self.codebook is not None
            return (
                f"codebook JSON — {len(self.codebook)} code(s) in "
                f"{len(self.codebook.families())} famil(ies)"
            )
        return f"assignments (row-oriented) — {len(self.assignments)} row(s)"


def load_artefact(path: Path) -> Artefact:
    """Load a codebook JSON or a row-oriented assignments file, detecting which.

    Accepted shapes: ``{"codes": [...]}``, a bare list of code objects, ``{id: code}``,
    a list of ``{"response_id", "segment", "code"}`` rows, and a hand-coded ``.xlsx``
    workbook. Anything else is refused by name rather than guessed at.
    """
    if not path.exists():
        raise CliError(f"{path} does not exist")
    if path.suffix.lower() in {".xlsx", ".xlsm"}:
        try:
            rows = read_coded_xlsx(path)
        except SpreadsheetFormatError as exc:
            raise CliError(str(exc)) from exc
        return Artefact(kind="assignments", path=path, assignments=rows)

    raw = _read_json(path)
    try:
        if isinstance(raw, list):
            if raw and all(_is_assignment_row(row) for row in raw):
                return Artefact(
                    kind="assignments",
                    path=path,
                    assignments=[Assignment.from_json(row) for row in raw],
                )
            if all(_is_code_row(row) for row in raw):
                codebook = Codebook.from_json(raw)
                return Artefact(
                    kind="codebook",
                    path=path,
                    assignments=assignments_from_codebook(codebook),
                    codebook=codebook,
                )
        elif isinstance(raw, dict):
            if "rows" in raw and isinstance(raw["rows"], list):
                return load_artefact_rows(path, raw["rows"])
            if "codes" in raw or all(_is_code_row(v) for v in raw.values()):
                codebook = Codebook.from_json(raw)
                return Artefact(
                    kind="codebook",
                    path=path,
                    assignments=assignments_from_codebook(codebook),
                    codebook=codebook,
                )
    except (KeyError, TypeError, ValueError) as exc:
        raise CliError(f"{path}: cannot read this artefact: {exc}") from exc
    raise CliError(
        f"{path}: unrecognised artefact shape. Expected a codebook "
        '({"codes": [...]}) or a list of {"response_id", "segment", "code"} rows.'
    )


def load_artefact_rows(path: Path, rows: list[Any]) -> Artefact:
    """A ``{"rows": [...]}`` wrapper around assignment rows."""
    if not all(_is_assignment_row(row) for row in rows):
        raise CliError(
            f'{path}: "rows" must hold {{"response_id", "segment", "code"}} objects.'
        )
    return Artefact(
        kind="assignments",
        path=path,
        assignments=[Assignment.from_json(row) for row in rows],
    )


def load_corpus_arg(path: Path | None, *, config: RunConfig) -> list[Response] | None:
    """Load `--data`, or return None when it was not supplied."""
    if path is None:
        return None
    if not path.exists():
        raise CliError(f"{path} does not exist")
    try:
        responses, _ = load_corpus_with_report(path, config=config)
    except (SpreadsheetFormatError, ValueError, OSError) as exc:
        raise CliError(f"cannot read the corpus {path}: {exc}") from exc
    return responses


def load_codebook_arg(path: Path | None) -> Codebook | None:
    if path is None:
        return None
    artefact = load_artefact(path)
    if artefact.codebook is None:
        raise CliError(f"{path} holds assignments, not a codebook.")
    return artefact.codebook


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


# --------------------------------------------------------------------------- #
# Live components — never executed by the test suite
# --------------------------------------------------------------------------- #


def _cached(client: LLMClient, config: RunConfig) -> LLMClient:
    return client if config.cache_dir is None else CachingLLMClient(client, config.cache_dir)


def _live_client(spec: ModelSpec, config: RunConfig) -> LLMClient:
    """One provider client for one role, or a message naming what is missing.

    Constructed lazily and per role, so a run fails before it spends anything rather
    than halfway through a paid batch.
    """
    if spec.provider == "mock":
        raise CliError(
            f"role {spec.role!r} is bound to the mock provider, but this is a live run. "
            "Set RunConfig.models to a real registry — gaf.config.DEFAULT_LIVE_REGISTRY "
            "is the suggested triple — before running with --live."
        )
    entry = _LIVE_PROVIDERS.get(spec.provider)
    if entry is None:
        raise CliError(
            f"role {spec.role!r} names provider {spec.provider!r}, which has no client. "
            f"Known providers: {', '.join(sorted(_LIVE_PROVIDERS))}."
        )
    factory, install_hint, env_var = entry
    try:
        return cast(
            LLMClient,
            factory(
                spec,
                max_attempts=config.max_retries,
                base_delay_s=config.retry_base_delay_s,
                seed=config.seed,
            ),
        )
    except _MISSING_SDK_ERRORS as exc:
        raise CliError(f"role {spec.role!r}: {exc}") from exc
    except Exception as exc:  # the SDK's own credential and configuration errors
        raise CliError(
            f"role {spec.role!r}: could not build a {spec.provider} client for model "
            f"{spec.model!r}: {exc}. Set {env_var} in the environment (see .env.example) "
            f"and install the provider extra with `{install_hint}`."
        ) from exc


def live_components(config: RunConfig, *, call_log: CallLog | None = None) -> LoopComponents:
    """Build `LoopComponents` from `RunConfig.models` with real provider clients.

    The counterpart of `gaf.pipeline.fast_loop.offline_components`, which deliberately
    refuses `offline=False`. Every client is wrapped in the on-disk response cache when
    the run configures one, and all four agents share the run's single `CallLog` so the
    accounting the run report prints is the accounting the store holds.

    Nothing in the test suite calls this with a real provider: a missing SDK, a missing
    key or a mock-bound registry each raise before any client is constructed.
    """
    if config.offline:
        raise CliError(
            "live_components builds real provider clients; this run is configured "
            "offline. Use gaf.pipeline.fast_loop.offline_components, or pass --live."
        )
    mock_roles = [spec.role for spec in config.models.all_specs() if spec.provider == "mock"]
    if mock_roles:
        raise CliError(
            f"role(s) {', '.join(mock_roles)} are bound to the mock provider, but this "
            "is a live run. Set RunConfig.models to a real registry — "
            "gaf.config.DEFAULT_LIVE_REGISTRY is the suggested triple — before running "
            "with --live."
        )
    if not config.models.distinct_coder_providers():
        raise CliError(
            "the two coders must come from different providers — epistemic diversity "
            "and the cost argument are the same mechanism (docs/ARCHITECTURE.md). "
            f"Both are bound to {config.models.coder_a.provider!r}."
        )
    log = call_log or CallLog()
    coder_a = _cached(_live_client(config.models.coder_a, config), config)
    coder_b = _cached(_live_client(config.models.coder_b, config), config)
    judge = _cached(_live_client(config.models.judge, config), config)
    try:
        embedder = EmbeddingService(config.embedding)
    except MissingEmbeddingSDKError as exc:
        raise CliError(f"embedding space {config.embedding.space_id!r}: {exc}") from exc
    except Exception as exc:
        raise CliError(
            f"could not build the embedding space {config.embedding.space_id!r}: {exc}. "
            "Set OPENAI_API_KEY in the environment (see .env.example), or keep "
            "EmbeddingSpaceConfig.mode at 'lexical'."
        ) from exc
    return LoopComponents(
        coder_a=CoderAgent(coder_a, config=config, call_log=log),
        coder_b=CoderAgent(coder_b, config=config, call_log=log),
        embedder=embedder,
        judge=JudgeAgent(judge, config=config, call_log=log),
        call_log=log,
    )


def _components(config: RunConfig) -> LoopComponents:
    return offline_components(config) if config.offline else live_components(config)


def _offline_judge(config: RunConfig) -> JudgeAgent:
    return JudgeAgent(
        _cached(MockJudgeClient(config.models.judge), config), config=config, call_log=CallLog()
    )


def _judge_for(config: RunConfig) -> JudgeAgent:
    if config.offline:
        return _offline_judge(config)
    return JudgeAgent(
        _cached(_live_client(config.models.judge, config), config),
        config=config,
        call_log=CallLog(),
    )


def _embedder_for(config: RunConfig) -> EmbeddingService:
    try:
        return EmbeddingService(config.embedding)
    except (MissingEmbeddingSDKError, RuntimeError, ValueError) as exc:
        raise CliError(f"embedding space {config.embedding.space_id!r}: {exc}") from exc


# --------------------------------------------------------------------------- #
# Config assembly
# --------------------------------------------------------------------------- #


def _config_from_args(args: argparse.Namespace, *, run_id: str, output_dir: Path) -> RunConfig:
    rules = CodingRules()
    config = RunConfig(
        run_id=run_id,
        offline=bool(getattr(args, "offline", True)),
        seed=int(getattr(args, "seed", _DEFAULTS.seed)),
        output_dir=output_dir,
        rules=rules,
        question_variant=str(getattr(args, "question_variant", None) or _DEFAULTS.question_variant),
    )
    if getattr(args, "batch_size", None):
        config = config.with_(batch_size=int(args.batch_size))
    if getattr(args, "no_cache", False):
        config = config.with_(cache_dir=None)
    elif getattr(args, "cache_dir", None):
        config = config.with_(cache_dir=Path(args.cache_dir))
    if not config.offline:
        config = config.with_(models=DEFAULT_LIVE_REGISTRY)
    return config


def _run_config_from_json(echo: dict[str, Any]) -> RunConfig:
    """Rebuild a `RunConfig` from `RunConfig.to_json()`, field for field.

    `gaf.config` is a frozen contract and offers serialisation but no reader, so the
    reader lives here. It must be exact: `Blackboard.register_run` compares the stored
    config JSON verbatim and refuses a run id whose configuration has changed, so a
    checkpoint that continued a run under a *nearly* identical config would be rejected
    by the store — which is the behaviour that caught this and is worth keeping.
    """

    def _sub(key: str, factory: Any) -> Any:
        raw = echo.get(key)
        if not isinstance(raw, dict):
            return factory()
        known = set(factory.__dataclass_fields__)
        return factory(**{k: v for k, v in raw.items() if k in known})

    models = _DEFAULTS.models
    models_raw = echo.get("models")
    if isinstance(models_raw, dict) and set(models_raw) >= {
        "coder_a",
        "coder_b",
        "judge",
        "refactorer",
    }:
        known_spec = set(ModelSpec.__dataclass_fields__)
        models = ModelRegistry(
            **{
                role: ModelSpec(**{k: v for k, v in spec.items() if k in known_spec})
                for role, spec in models_raw.items()
            }
        )

    checkpoints = CheckpointPolicy()
    checkpoints_raw = echo.get("checkpoints")
    if isinstance(checkpoints_raw, dict):
        known = set(CheckpointPolicy.__dataclass_fields__)
        payload = {k: v for k, v in checkpoints_raw.items() if k in known}
        if isinstance(payload.get("fixed_cadence"), list):
            payload["fixed_cadence"] = tuple(payload["fixed_cadence"])
        checkpoints = CheckpointPolicy(**payload)

    corpus_path = echo.get("corpus_path")
    db_path = echo.get("db_path")
    cache_dir = echo.get("cache_dir")
    return RunConfig(
        run_id=str(echo.get("run_id", _DEFAULTS.run_id)),
        corpus_path=None if corpus_path is None else Path(str(corpus_path)),
        output_dir=Path(str(echo.get("output_dir", _DEFAULTS.output_dir))),
        db_path=None if db_path is None else Path(str(db_path)),
        offline=bool(echo.get("offline", True)),
        seed=int(echo.get("seed", _DEFAULTS.seed)),
        rules=_sub("rules", CodingRules),
        models=models,
        embedding=_sub("embedding", EmbeddingSpaceConfig),
        checkpoints=checkpoints,
        analysis=_sub("analysis", AnalysisConfig),
        lexical=_sub("lexical", LexicalConfig),
        snapshot_policy=cast(Any, echo.get("snapshot_policy", _DEFAULTS.snapshot_policy)),
        batch_size=int(echo.get("batch_size", _DEFAULTS.batch_size)),
        retrieval_top_k=int(echo.get("retrieval_top_k", _DEFAULTS.retrieval_top_k)),
        question_variant=str(echo.get("question_variant", _DEFAULTS.question_variant)),
        recycle_human_corrections=bool(echo.get("recycle_human_corrections", False)),
        cache_dir=None if cache_dir is None else Path(str(cache_dir)),
        max_retries=int(echo.get("max_retries", _DEFAULTS.max_retries)),
        retry_base_delay_s=float(echo.get("retry_base_delay_s", _DEFAULTS.retry_base_delay_s)),
    )


# --------------------------------------------------------------------------- #
# gaf ingest
# --------------------------------------------------------------------------- #


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


# --------------------------------------------------------------------------- #
# gaf run
# --------------------------------------------------------------------------- #


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


def write_run_dir(out: Path, artefact: RunArtefact, board: Blackboard) -> None:
    """Everything a later `gaf report`, `gaf analyse` or `gaf checkpoint` needs."""
    out.mkdir(parents=True, exist_ok=True)
    _write(out / RUN_JSON_NAME, artefact.to_json_str())
    _write(out / "codebook.json", artefact.codebook.to_json_str())
    _write_json(out / "assignments.json", [a.to_json() for a in artefact.assignments])
    _write_json(out / "findings.json", artefact.report.to_json())
    _write_json(out / "stats.json", artefact.stats.to_json())
    events = board.audit(artefact.stats.run_id).events()
    _write(
        out / "audit.jsonl",
        "\n".join(
            json.dumps(event.to_json(), sort_keys=True, ensure_ascii=False) for event in events
        ),
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

    database = cast(Path, config.db_path)
    if database.exists():
        # A run directory is one run's output. Re-running must not append to the
        # previous run's append-only log, or two runs would share an audit trail.
        database.unlink()

    components = _components(config)
    with Blackboard(database) as board:
        result = run_fast_loop(responses, config=config, board=board, components=components)
        artefact = RunArtefact.from_result(
            result,
            config=config,
            provenance=_run_provenance(
                corpus_path=corpus_path, responses=responses, report=ingest, config=config, out=out
            ),
        )
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
    _out("")
    _out(f"Next: gaf report --run {out}")
    return EXIT_OK


# --------------------------------------------------------------------------- #
# gaf check
# --------------------------------------------------------------------------- #


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


# --------------------------------------------------------------------------- #
# gaf analyse
# --------------------------------------------------------------------------- #


def cmd_analyse(args: argparse.Namespace) -> int:
    """The deterministic analysis tail: matrix, Ward's HCA, saturation."""
    path = Path(args.assignments)
    artefact = load_artefact(path)
    config = _config_from_args(args, run_id="analyse", output_dir=Path(args.out))
    corpus = load_corpus_arg(Path(args.data) if args.data else None, config=config)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    analysis = config.analysis
    if args.min_frequency is not None:
        analysis = AnalysisConfig(
            **{**analysis.to_json(), "min_code_frequency": int(args.min_frequency)}
        )
    if args.n_clusters is not None:
        analysis = AnalysisConfig(**{**analysis.to_json(), "n_clusters": int(args.n_clusters)})

    _banner("gaf analyse", str(path))
    _out(f"  {artefact.describe()}")

    try:
        matrix = build_matrix(artefact.assignments, config=analysis, responses=corpus)
    except ValueError as exc:
        raise CliError(f"cannot build the occurrence matrix: {exc}") from exc
    unfiltered = build_matrix(
        artefact.assignments,
        config=AnalysisConfig(
            **{
                **analysis.to_json(),
                "min_code_frequency": 1,
                "min_code_frequency_fraction": None,
            }
        ),
        responses=corpus,
    )

    _out("")
    _out(f"  {matrix.n_responses} response(s) x {matrix.n_codes} code(s) after filtering.")
    _out(f"  {matrix.filter.summary()}")
    matrix.write_csv(out / "occurrence_matrix.csv")
    _write(out / "occurrence_matrix.json", matrix.to_json_str())

    curve = saturation_curve(unfiltered, config=analysis)
    _write_json(out / "saturation.json", curve.to_json())
    _write(out / "saturation.md", curve.to_markdown())
    _write(out / "saturation.svg", saturation_svg(curve))
    _out("")
    _out(curve.to_markdown())

    try:
        clusters = cluster_responses(matrix, config=analysis)
    except DegenerateMatrixError as exc:
        _out("")
        _out(f"! Ward's HCA was refused: {exc}")
        _out(
            "  The matrix is too small or too degenerate to cluster. The occurrence "
            "matrix and the saturation curve above are still written."
        )
        _out("")
        _out(f"Artefacts written to {out}")
        return EXIT_OK

    _write(out / "clusters.json", clusters.to_json_str())
    _write(out / "clusters.md", clusters.to_markdown())
    _write(out / "dendrogram.svg", dendrogram_svg(clusters))
    _out("")
    _out(clusters.to_markdown())
    if clusters.warnings:
        _out("")
        for warning in clusters.warnings:
            _out(f"! {warning}")
        _out(
            "  ADR-0020: the cluster-count rule is applied literally and its degenerate "
            "results are reported, never silently repaired. Set --n-clusters to state "
            "the count explicitly; it is then recorded as an override."
        )

    _out("")
    _out(f"Artefacts written to {out}:")
    for name in (
        "occurrence_matrix.csv",
        "occurrence_matrix.json",
        "clusters.json",
        "clusters.md",
        "dendrogram.svg",
        "saturation.json",
        "saturation.md",
        "saturation.svg",
    ):
        _out(f"  {out / name}")
    return EXIT_OK


# --------------------------------------------------------------------------- #
# gaf validate
# --------------------------------------------------------------------------- #


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


# --------------------------------------------------------------------------- #
# gaf report
# --------------------------------------------------------------------------- #


def _load_run(run_dir: Path) -> RunArtefact:
    document = run_dir / RUN_JSON_NAME
    if not document.exists():
        raise CliError(
            f"{document} does not exist. Point --run at a directory written by "
            "`gaf run`."
        )
    try:
        return RunArtefact.from_json(_read_json(document))
    except (KeyError, TypeError, ValueError) as exc:
        raise CliError(f"{document}: {exc}") from exc


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


# --------------------------------------------------------------------------- #
# gaf checkpoint
# --------------------------------------------------------------------------- #


def _slow_loop() -> Any:
    """Import the slow loop, or explain precisely what is missing.

    The module is a fixed contract — `run_checkpoint`, `Gate`, `ConsoleGate`,
    `RejectAllGate` — so this dispatch is written against those names whether or not
    the module is present in a given checkout.
    """
    try:
        import gaf.pipeline.slow_loop as slow_loop
    except ImportError as exc:
        raise CliError(
            "gaf.pipeline.slow_loop is not available in this checkout, so a checkpoint "
            f"cannot be opened ({exc}). Every other command is unaffected."
        ) from exc
    missing = [
        name
        for name in ("run_checkpoint", "Gate", "ConsoleGate", "RejectAllGate")
        if not hasattr(slow_loop, name)
    ]
    if missing:
        raise CliError(
            "gaf.pipeline.slow_loop is present but does not export "
            f"{', '.join(missing)}; this build expects run_checkpoint, Gate, "
            "ConsoleGate and RejectAllGate."
        )
    return slow_loop


def _interactive(requested: bool) -> bool:
    """A checkpoint may only prompt when there is genuinely a human at the terminal."""
    return bool(requested and sys.stdin.isatty() and sys.stdout.isatty())


def cmd_checkpoint(args: argparse.Namespace) -> int:
    """Open a slow-loop checkpoint: the Refactorer proposes, a human decides.

    Non-interactive sessions get `RejectAllGate`, so a checkpoint with nobody present
    is a no-op that changes nothing. It is never an auto-accept: accepting a refactor
    without a human is exactly the decision-task overlay ADR-0004 exists to avoid.
    """
    slow_loop = _slow_loop()
    run_dir = Path(args.run)
    artefact = _load_run(run_dir)
    database = run_dir / "gaf.sqlite"
    if not database.exists():
        raise CliError(f"{database} does not exist; a checkpoint continues a finished run.")

    config = _run_config_from_json(artefact.config)
    if not artefact.snapshot_ids:
        raise CliError(f"{run_dir}: the run recorded no snapshot to continue from.")
    snapshot_id = artefact.snapshot_ids[-1]

    client = (
        _cached(MockRefactorerClient(config.models.refactorer), config)
        if config.offline
        else _cached(_live_client(config.models.refactorer, config), config)
    )
    agent = RefactorerAgent(client, config=config, call_log=CallLog())
    embedder = _embedder_for(config)

    interactive = _interactive(args.interactive)
    gate = slow_loop.ConsoleGate() if interactive else slow_loop.RejectAllGate()

    _banner("gaf checkpoint", str(run_dir))
    _out(f"  snapshot     {snapshot_id}")
    _out(f"  codebook     {len(artefact.codebook)} code(s)")
    _out(f"  gate         {'ConsoleGate (interactive)' if interactive else 'RejectAllGate'}")
    if not interactive:
        _out(
            "  A checkpoint with no human present is a no-op, never an auto-accept. "
            "Re-run with --interactive from a terminal to review the proposal."
        )
    _out("")

    with Blackboard(database) as board:
        result = slow_loop.run_checkpoint(
            board=board,
            config=config,
            codebook=artefact.codebook,
            snapshot_id=snapshot_id,
            agent=agent,
            embedder=embedder,
            gate=gate,
            trigger=args.trigger,
        )
    _out(_describe_checkpoint(result))
    return EXIT_OK


def _describe_checkpoint(result: Any) -> str:
    """Render whatever the slow loop returned, without assuming its private shape."""
    to_json = getattr(result, "to_json", None)
    if callable(to_json):
        return json.dumps(to_json(), sort_keys=True, ensure_ascii=False, indent=2)
    return str(result)


# --------------------------------------------------------------------------- #
# Parser
# --------------------------------------------------------------------------- #


def _add_mode(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--offline",
        dest="offline",
        action="store_true",
        default=True,
        help="mock model clients and the lexical embedding fallback (the default; no key, no network)",
    )
    group.add_argument(
        "--live",
        dest="offline",
        action="store_false",
        help="build real provider clients from RunConfig.models (needs the provider extras and keys)",
    )


def _add_cache(parser: argparse.ArgumentParser) -> None:
    """The on-disk model response cache. Present wherever a model may be consulted."""
    parser.add_argument("--cache-dir", help="on-disk model response cache")
    parser.add_argument("--no-cache", action="store_true", help="disable the response cache")


def _add_seed(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--seed", type=int, default=_DEFAULTS.seed, help="deterministic seed (default: %(default)s)"
    )


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

    # -- ingest ----------------------------------------------------------- #
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

    # -- run -------------------------------------------------------------- #
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
    _add_cache(run)
    _add_seed(run)
    _add_mode(run)
    run.set_defaults(handler=cmd_run)

    # -- check ------------------------------------------------------------ #
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

    # -- analyse ---------------------------------------------------------- #
    analyse = sub.add_parser(
        "analyse",
        help="the deterministic analysis tail: matrix, Ward's HCA, saturation",
        description=(
            "Build the binary occurrence matrix, apply the low-frequency filter, run "
            "Ward's hierarchical cluster analysis and the saturation curve. No model "
            "is consulted. Respondent metadata is joined here and nowhere else."
        ),
    )
    analyse.add_argument(
        "--assignments", required=True, help="assignments JSON/xlsx, or a codebook JSON"
    )
    analyse.add_argument("--data", help="corpus JSON or xlsx — fixes the row universe and metadata")
    analyse.add_argument("--out", required=True, help="output directory")
    analyse.add_argument("--min-frequency", type=int, help="override AnalysisConfig.min_code_frequency")
    analyse.add_argument(
        "--n-clusters",
        type=int,
        help="state the cluster count explicitly; recorded as an override (ADR-0020)",
    )
    _add_seed(analyse)
    analyse.set_defaults(handler=cmd_analyse, offline=True)

    # -- validate --------------------------------------------------------- #
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

    # -- report ----------------------------------------------------------- #
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

    # -- checkpoint ------------------------------------------------------- #
    checkpoint = sub.add_parser(
        "checkpoint",
        help="open a slow-loop checkpoint behind the human gate",
        description=(
            "The Refactorer proposes an edit script over the whole codebook; a human "
            "accepts, rejects or edits each operation. Without a terminal the gate is "
            "RejectAllGate and the checkpoint is a no-op — never an auto-accept."
        ),
    )
    checkpoint.add_argument("--run", required=True, help="a run directory written by `gaf run`")
    checkpoint.add_argument(
        "--interactive",
        action="store_true",
        help="review the proposal at the terminal (ConsoleGate)",
    )
    checkpoint.add_argument(
        "--trigger", default="manual", help="why this checkpoint opened (default: %(default)s)"
    )
    checkpoint.set_defaults(handler=cmd_checkpoint)

    return parser


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #


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


if __name__ == "__main__":  # pragma: no cover - exercised through the console script
    raise SystemExit(main())
