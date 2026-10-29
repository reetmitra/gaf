"""Shared infrastructure for every `gaf` subcommand: nothing here is a command itself.

Four things live here because more than one subcommand module needs them, and
duplicating them per module would be the kind of drift the audit log exists to
prevent elsewhere:

* **Exit codes and `CliError`** — the vocabulary every command raises failure in.
* **Artefact loading** — `load_artefact` accepts both on-disk shapes admissible
  everywhere a coded artefact is asked for (the pipeline's codebook JSON and a
  hand-coding spreadsheet), which is what lets `gaf check` audit a hand-coding with
  the same code that audits a machine one. `load_corpus_arg` and `load_codebook_arg`
  are the `--data` / `--codebook` counterparts, and `_load_run` reads a finished run
  directory back into a `RunArtefact` for `gaf report` and `gaf checkpoint` alike.
* **The run-config reader** — `_config_from_args` turns argparse flags into a
  `RunConfig`; `_run_config_from_json` is its inverse, rebuilding one from
  `RunConfig.to_json()` field for field so that `gaf checkpoint` continues a run
  under an *exactly* reproduced configuration (`Blackboard.register_run` compares the
  stored config verbatim and refuses a run id whose configuration drifted).
* **Live and offline model components** — `live_components` builds real provider
  clients from `RunConfig.models`, wrapped in the on-disk response cache; nothing in
  the test suite or CI ever takes that path. `_embedder_for` and `_judge_for` build
  the pieces `gaf check` and `gaf checkpoint` need without running the full loop.

This serves **reliability**: one reader, one writer, one config round-trip, so that a
config or artefact rebuilt here is never a slightly-different reimplementation living
in whichever command happened to need it first.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, cast

from gaf.agents.coder import CoderAgent
from gaf.agents.judge import JudgeAgent
from gaf.analysis.matrix import assignments_from_codebook
from gaf.config import (
    DEFAULT_LIVE_REGISTRY,
    EFFORT_LEVELS,
    AnalysisConfig,
    CheckpointPolicy,
    CodingRules,
    EmbeddingSpaceConfig,
    LexicalConfig,
    ModelRegistry,
    ModelSpec,
    RunConfig,
)
from gaf.embed.service import EmbeddingService, MissingEmbeddingSDKError, derive_space_id
from gaf.ingest.corpus import load_corpus_with_report
from gaf.ingest.xlsx import SpreadsheetFormatError, read_coded_xlsx
from gaf.llm import anthropic_client, compat_client, gemini_client, local_client, openai_client
from gaf.llm.base import CallLog, LLMClient
from gaf.llm.cache import CachingLLMClient
from gaf.llm.mock import MockJudgeClient
from gaf.local_endpoint import LocalEndpointError, local_base_url, require_model
from gaf.models import Assignment, Codebook, Response
from gaf.pipeline.fast_loop import LoopComponents, offline_components
from gaf.report.run_report import RUN_JSON_NAME, RunArtefact

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_USAGE = 2
EXIT_INPUT = 3


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


# --------------------------------------------------------------------------- #
# `RunConfig` is a slots dataclass, so its defaults are not readable off the class.
# One instance carries them for the argparse defaults and the echo fallbacks.
# --------------------------------------------------------------------------- #

_DEFAULTS = RunConfig()


# --------------------------------------------------------------------------- #
# Live components — never executed by the test suite
# --------------------------------------------------------------------------- #

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
    "local": (local_client.LocalClient, local_client.INSTALL_HINT, "GAF_LOCAL_BASE_URL"),
    # A hosted endpoint: respondent text leaves the machine, so never "local" (ADR-0052).
    "openai_compatible": (
        compat_client.OpenAICompatibleClient,
        compat_client.INSTALL_HINT,
        "GAF_COMPAT_BASE_URL and GAF_COMPAT_API_KEY",
    ),
}

_MISSING_SDK_ERRORS = (
    openai_client.MissingProviderSDKError,
    gemini_client.MissingProviderSDKError,
    anthropic_client.MissingProviderSDKError,
)


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
        install = f" and install the provider extra with `{install_hint}`" if install_hint else ""
        raise CliError(
            f"role {spec.role!r}: could not build a {spec.provider} client for model "
            f"{spec.model!r}: {exc}. Set {env_var} in the environment (see .env.example)"
            f"{install}."
        ) from exc


def model_family(model: str) -> str:
    """The maker's family of a model id served locally or by a hosted endpoint.

    ``"qwen3.5:9b"`` → ``"qwen"``, ``"gemma4:12b"`` → ``"gemma"``, ``"gpt-oss:20b"`` →
    ``"gpt"``, ``"hf.co/org/Llama-3.1-8B-GGUF"`` → ``"llama"``, ``"qwen/qwen3.8-max"`` →
    ``"qwen"``: the leading run of letters of the last path segment. Two sizes or
    versions of one family share a family. Used by the coder-diversity rule.
    """
    tail = model.rsplit("/", 1)[-1].lower()
    match = re.match(r"[a-z]+", tail)
    return match.group(0) if match else tail


#: Providers that name a server rather than a maker: ``"local"`` (ADR-0049) and the
#: hosted ``"openai_compatible"`` (ADR-0052). A model reached through one is told apart
#: by its model family, not by the provider name.
_SERVER_PROVIDERS = frozenset({"local", "openai_compatible"})

#: The family behind each provider that is also a maker, so a model reached through a
#: server provider can be compared with it (``anthropic/claude-...`` on OpenRouter is
#: still Claude).
_PROVIDER_FAMILIES = {"openai": "gpt", "gemini": "gemini", "anthropic": "claude"}


def coder_family(spec: ModelSpec) -> str:
    """The model family `spec` binds: its id's family for a server provider, else the maker's."""
    if spec.provider in _SERVER_PROVIDERS:
        return model_family(spec.model)
    return _PROVIDER_FAMILIES.get(spec.provider, spec.provider)


def coders_are_distinct(models: ModelRegistry) -> bool:
    """The two coders come from different makers.

    For hosted models the provider *is* the maker, so the providers must differ. A
    ``"local"`` or ``"openai_compatible"`` provider is a server, not a maker, so whenever
    either coder is bound to one the two coders must instead come from different model
    families (ADR-0049, ADR-0052): two Qwen sizes, or a local Qwen beside a hosted one,
    are one family. Opus beside a hosted Qwen is distinct.
    """
    a, b = models.coder_a, models.coder_b
    if a.provider in _SERVER_PROVIDERS or b.provider in _SERVER_PROVIDERS:
        return coder_family(a) != coder_family(b)
    return models.distinct_coder_providers()


def check_local_models(config: RunConfig) -> None:
    """Before a run starts, confirm the local server is up and has every local model.

    A no-op when nothing in the run is local. Failing here costs a second; failing on
    the first coder call after the corpus has been segmented and stored costs a run.
    """
    local_models = [s.model for s in config.models.all_specs() if s.provider == "local"]
    if config.embedding.mode == "local" and config.embedding.model:
        local_models.append(config.embedding.model)
    if not local_models:
        return
    try:
        base = local_base_url()
        for model in dict.fromkeys(local_models):
            require_model(base, model)
    except LocalEndpointError as exc:
        raise CliError(str(exc)) from exc


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
    if not coders_are_distinct(config.models):
        a, b = config.models.coder_a, config.models.coder_b
        raise CliError(
            "the two coders must come from different providers — epistemic diversity "
            "and the cost argument are the same mechanism (docs/ARCHITECTURE.md). "
            + (
                f"Both are bound to {a.provider!r}."
                if a.provider == b.provider and a.provider not in _SERVER_PROVIDERS
                else f"Both are the model family {coder_family(a)!r} ({a.provider} "
                f"{a.model!r}, {b.provider} {b.model!r}); ADR-0049, ADR-0052."
            )
        )
    check_local_models(config)
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
    profile = getattr(args, "profile", None)
    if profile and config.offline:
        raise CliError("--profile names live models; add --live to use it", code=EXIT_USAGE)
    if not config.offline:
        if profile:
            models, embedding = load_profile(Path(profile))
            config = config.with_(models=models)
            if embedding is not None:
                config = config.with_(embedding=embedding)
        else:
            config = config.with_(models=DEFAULT_LIVE_REGISTRY)
    return config


_ROLES = ("coder_a", "coder_b", "judge", "refactorer")


def load_profile(path: Path) -> tuple[ModelRegistry, EmbeddingSpaceConfig | None]:
    """Read a model profile: the four role bindings and, optionally, an embedding space.

    The shape is the ``models`` and ``embedding`` blocks of a run's echoed config, so a
    profile can be copied out of any run directory. Each role's ``role`` field is filled
    from its key. A profile replaces `DEFAULT_LIVE_REGISTRY` for one run and is recorded
    in that run's config echo like any other registry (ADR-0049).
    """
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CliError(f"cannot read profile {str(path)!r}: {exc}") from exc
    models_raw = raw.get("models") if isinstance(raw, dict) else None
    if not isinstance(models_raw, dict) or set(models_raw) != set(_ROLES):
        raise CliError(
            f"profile {str(path)!r} must have a 'models' object with exactly the roles "
            f"{', '.join(_ROLES)}"
        )
    known_spec = set(ModelSpec.__dataclass_fields__)
    specs: dict[str, ModelSpec] = {}
    for role in _ROLES:
        entry = models_raw[role]
        if not isinstance(entry, dict) or not {"provider", "model"} <= set(entry):
            raise CliError(f"profile {str(path)!r}: role {role!r} needs a provider and a model")
        unknown = set(entry) - known_spec
        if unknown:
            raise CliError(
                f"profile {str(path)!r}: role {role!r} has unknown field(s) "
                f"{', '.join(sorted(unknown))}"
            )
        fields = {**entry, "role": role}
        if fields["provider"] not in _LIVE_PROVIDERS:
            raise CliError(
                f"profile {str(path)!r}: role {role!r} names provider "
                f"{fields['provider']!r}; known: {', '.join(sorted(_LIVE_PROVIDERS))}"
            )
        effort = fields.get("effort")
        if effort is not None:
            # `output_config.effort` exists on the Anthropic API only (ADR-0051); on any
            # other provider the field would be recorded in the echo and do nothing.
            if fields["provider"] != "anthropic":
                raise CliError(
                    f"profile {str(path)!r}: role {role!r} sets 'effort', which only the "
                    f"anthropic provider has; {fields['provider']!r} would ignore it"
                )
            if effort not in EFFORT_LEVELS:
                raise CliError(
                    f"profile {str(path)!r}: role {role!r} has effort {effort!r}; "
                    f"one of {', '.join(EFFORT_LEVELS)}"
                )
        specs[role] = ModelSpec(**fields)
    embedding: EmbeddingSpaceConfig | None = None
    embedding_raw = raw.get("embedding")
    if embedding_raw is not None:
        if not isinstance(embedding_raw, dict):
            raise CliError(f"profile {str(path)!r}: 'embedding' must be an object")
        known = set(EmbeddingSpaceConfig.__dataclass_fields__)
        unknown = set(embedding_raw) - known
        if unknown:
            raise CliError(
                f"profile {str(path)!r}: 'embedding' has unknown field(s) "
                f"{', '.join(sorted(unknown))}"
            )
        try:
            embedding = EmbeddingSpaceConfig(**embedding_raw)
            if "space_id" not in embedding_raw:
                # Echo the space the run is actually in, not the lexical default label.
                embedding = replace(embedding, space_id=derive_space_id(embedding))
        except ValueError as exc:
            raise CliError(f"profile {str(path)!r}: 'embedding': {exc}") from exc
    return ModelRegistry(**specs), embedding


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
# Shared argparse fragments
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
    parser.add_argument(
        "--max-usd",
        type=float,
        metavar="USD",
        help=(
            "with --live: stop before the first model call that would start once the billed "
            "spend of this run has reached USD. Counts the dollars recorded for this run, "
            "including earlier runs it was resumed from; cache replays are free and never "
            "count. Overshoots by at most the one call in flight when the cap was crossed "
            "(ADR-0053)"
        ),
    )
    parser.add_argument(
        "--profile",
        metavar="JSON",
        help=(
            "with --live: a model profile (four role bindings and, optionally, an embedding "
            "space) to use instead of the default live registry; see profiles/"
        ),
    )


def _add_cache(parser: argparse.ArgumentParser) -> None:
    """The on-disk model response cache. Present wherever a model may be consulted."""
    parser.add_argument("--cache-dir", help="on-disk model response cache")
    parser.add_argument("--no-cache", action="store_true", help="disable the response cache")


def _add_seed(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--seed", type=int, default=_DEFAULTS.seed, help="deterministic seed (default: %(default)s)"
    )
