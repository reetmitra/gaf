"""Run configuration, coding rules, thresholds and the model registry.

FROZEN CONTRACT (Wave 0). No Wave 1+ agent may change this module.

**Every threshold in the system is a named field here.** A magic number in a module
body is a bug: it cannot be swept during calibration, cannot be recorded with a run,
and cannot be defended in a methods appendix.

`CodingRules` transcribes the PI's own coding instructions (`GPTPrompts.docx`); each
field cites the rule it encodes, and `docs/CODING_RULES.md` carries the verbatim
quotation. Severities follow his phrasing: rules he states as absolutes are ERRORs,
rules he qualifies with "usually" are WARNs.

Validation principle: **transparency** — a reader can see the entire behavioural
surface of the pipeline in one file, and every run report can print it.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any, Literal

__all__ = [
    "DEFAULT_LIVE_REGISTRY",
    "DEFAULT_QUESTION_VARIANT",
    "LIVE_REGISTRY_PRICED_ON",
    "MOCK_REGISTRY",
    "QUESTION_V2",
    "QUESTION_V3",
    "QUESTION_VARIANTS",
    "AnalysisConfig",
    "CheckpointPolicy",
    "CodingRules",
    "EmbeddingSpaceConfig",
    "LexicalConfig",
    "ModelRegistry",
    "ModelSpec",
    "RunConfig",
]

# --------------------------------------------------------------------------- #
# Survey question variants
# --------------------------------------------------------------------------- #
#
# Transcribed verbatim from `GPTPrompts.docx` (surrounding quotation marks and the
# stray leading space in the v3 heading removed; wording otherwise untouched).
#
# OPEN ITEM (brief §16.3): which variant generated NarrativeState(IndiaSample1-20).
# `DEFAULT_QUESTION_VARIANT` is "v2" per the brief. Note the counter-evidence, which
# has not been used to override the brief: the sample file's header column is
# "Number", and Prompt Version 3 is the version that names a "Number" column, while
# Prompt Version 2 does not name its columns at all; the negative examples headed
# "Negative examples for NarrativeState(India)" also directly follow Prompt Version 3
# and cite responses 26, 50 and 57, all of which are present in this sample.
# To be confirmed with the PI before any live coding run.

QUESTION_V2 = (
    "From now to 2050, what impacts do you think AI will have in shaping your society? "
    "Please answer the question by describing one specific scenario that feels most vivid "
    "and realistic to you. Please write at least 100 words, focus on one scenario only, "
    "and provide as much detail as possible."
)

QUESTION_V3 = (
    "In 2050, what kind of roles do you think AI will play in your society? "
    "Please answer the question by describing one specific scenario that feels most vivid "
    "and realistic to you. Please write at least 100 words, focus on one scenario only, "
    "and provide as much detail as possible."
)

QUESTION_VARIANTS: dict[str, str] = {"v2": QUESTION_V2, "v3": QUESTION_V3}

DEFAULT_QUESTION_VARIANT = "v2"


# --------------------------------------------------------------------------- #
# Coding rules — the PI's instructions, as data
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class CodingRules:
    """The PI's coding constraints. See `docs/CODING_RULES.md` for the quotations."""

    # S5 — "One response can correspond to multiple codes: usually between 2 and 12."
    # "usually" => advisory => WARN, never a drop.
    min_codes_per_response: int = 2
    max_codes_per_response: int = 12

    # S4 — "The same piece of text can be coded with a maximum of two codes." Absolute.
    max_codes_per_segment: int = 2
    #: Char-span Jaccard at or above which two quotes count as "the same piece of text".
    segment_overlap_threshold: float = 0.5

    # S2b — "Coding is applied on the level of phrase or sentence."
    max_quote_sentences: int = 2
    #: S2b, second condition. Three of the twenty real seed responses contain NO
    #: sentence terminator at all (ids 18, 21, 56 — 102 to 115 words each), so a
    #: terminator count alone cannot enforce the PI's phrase/sentence rule: a quote of
    #: an entire unpunctuated response counts as one sentence and passes. This bound is
    #: the word-equivalent of the two-sentence one (this corpus averages ~20 words per
    #: sentence), not a new rule. See ADR-0015.
    max_quote_words: int = 40

    # S3 / S6 — "a codebook with two levels of codes".
    hierarchy_depth: int = 2

    # S1 — a code is "an explanation of a segment of text's key meaning", so a code
    # without a description is not yet a code.
    require_description: bool = True

    # S3 — name grammar, and "Consider adding a second level code first before adding
    # a top-level code."
    check_name_grammar: bool = True
    prefer_subcode_first: bool = True

    #: S2 — similarity at or above which a fuzzy window counts as locating the quote.
    fuzzy_threshold: float = 0.85

    #: M2/M4 — auto-merge / near-duplicate band.
    tau_high: float = 0.80
    #: M2 — auto-create band.
    tau_low: float = 0.45
    #: M3 — code<->evidence fit floor. PROVISIONAL: set against the lexical fallback
    #: embedder and never calibrated against human judgment. See `gaf.checks.health`
    #: calibration and brief §11 — change it through a calibration report, not by hand.
    tau_fit: float = 0.30

    def to_json(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_json(cls, obj: dict[str, Any]) -> CodingRules:
        known = set(cls.__dataclass_fields__)
        return cls(**{k: v for k, v in obj.items() if k in known})


# --------------------------------------------------------------------------- #
# Models
# --------------------------------------------------------------------------- #

Provider = Literal["mock", "openai", "gemini", "anthropic"]
Role = Literal["coder_a", "coder_b", "judge", "refactorer"]


@dataclass(frozen=True, slots=True)
class ModelSpec:
    """One model binding. Prices live here so no module body carries a rate."""

    provider: Provider
    model: str
    role: Role
    temperature: float = 0.0
    max_output_tokens: int = 4096
    input_usd_per_mtok: float = 0.0
    output_usd_per_mtok: float = 0.0
    #: ISO date the two rates above were read from the provider's own page, or "" where
    #: there is nothing to date (every mock spec). A rate with no date cannot be checked,
    #: only believed — and these decay: see ADR-0048 for the four sources and the one
    #: rate with a known step on 1 January 2027.
    priced_on: str = ""

    def cost_usd(self, input_tokens: int, output_tokens: int) -> float:
        return (
            input_tokens * self.input_usd_per_mtok + output_tokens * self.output_usd_per_mtok
        ) / 1_000_000

    def to_json(self) -> dict[str, Any]:
        data = asdict(self)
        if not self.priced_on:
            # An unpriced spec emits no date, so `RunConfig.to_json()` — which the store
            # compares verbatim and the golden manifest commits in full — is unchanged
            # for every offline run. ADR-0048.
            del data["priced_on"]
        return data


@dataclass(frozen=True, slots=True)
class ModelRegistry:
    """The provider triple plus the Refactorer.

    Three LLM roles run inside the loops (Coder, Judge, Refactorer); the Definer is a
    fourth, outside both and with no binding here (ADR-0034). Four bindings, because the two
    coders must come from *different providers* — that difference is the epistemic
    diversity mechanism and, because only a grey-zone score between the two coders
    escalates to the judge, also the cost-control mechanism. Nothing is hard-coded anywhere else in the package.
    """

    coder_a: ModelSpec
    coder_b: ModelSpec
    judge: ModelSpec
    refactorer: ModelSpec

    def triple(self) -> tuple[ModelSpec, ModelSpec, ModelSpec]:
        return (self.coder_a, self.coder_b, self.judge)

    def all_specs(self) -> tuple[ModelSpec, ...]:
        return (self.coder_a, self.coder_b, self.judge, self.refactorer)

    def for_role(self, role: str) -> ModelSpec:
        try:
            return {
                "coder_a": self.coder_a,
                "coder_b": self.coder_b,
                "judge": self.judge,
                "refactorer": self.refactorer,
            }[role]
        except KeyError:
            raise ValueError(f"unknown role {role!r}") from None

    def distinct_coder_providers(self) -> bool:
        return self.coder_a.provider != self.coder_b.provider

    def to_json(self) -> dict[str, Any]:
        return {
            "coder_a": self.coder_a.to_json(),
            "coder_b": self.coder_b.to_json(),
            "judge": self.judge.to_json(),
            "refactorer": self.refactorer.to_json(),
        }


#: The offline registry. Every test, `make demo` and CI run uses this one.
MOCK_REGISTRY = ModelRegistry(
    coder_a=ModelSpec(provider="mock", model="mock-coder-a", role="coder_a"),
    coder_b=ModelSpec(provider="mock", model="mock-coder-b", role="coder_b"),
    judge=ModelSpec(provider="mock", model="mock-judge", role="judge"),
    refactorer=ModelSpec(provider="mock", model="mock-refactorer", role="refactorer"),
)

#: The date every rate below was read from the provider's own published page (ADR-0048).
LIVE_REGISTRY_PRICED_ON = "2026-09-23"

#: A suggested live triple — two mid-tier coders from different providers and one
#: frontier judge from a third (brief §16.8). Never reached unless `offline=False`;
#: override wholesale in a RunConfig rather than editing this constant.
#:
#: `--live` reads this constant and no other (`gaf/cli/_common.py`), so a retired id or a
#: stale rate here is a run that fails, or a `cost_usd` nobody can reconstruct. Every id
#: and both of its rates were read on `LIVE_REGISTRY_PRICED_ON` from:
#:   openai     https://developers.openai.com/api/docs/pricing
#:   gemini     https://ai.google.dev/gemini-api/docs/pricing  (and .../docs/deprecations)
#:   anthropic  https://platform.claude.com/docs/en/about-claude/pricing
#: `gemini-3.6-flash` is the replacement Google itself names for `gemini-2.0-flash`, which
#: it shut down on 1 June 2026; its 0.75/3.75 is an introductory rate that becomes
#: 1.50/7.50 on 1 January 2027. Re-pricing any line is an ADR, not an edit: ADR-0048, and
#: the pinned test in `tests/test_contracts.py`.
DEFAULT_LIVE_REGISTRY = ModelRegistry(
    coder_a=ModelSpec(
        provider="openai", model="gpt-4o-mini", role="coder_a",
        input_usd_per_mtok=0.15, output_usd_per_mtok=0.60,
        priced_on=LIVE_REGISTRY_PRICED_ON,
    ),
    coder_b=ModelSpec(
        provider="gemini", model="gemini-3.6-flash", role="coder_b",
        input_usd_per_mtok=0.75, output_usd_per_mtok=3.75,
        priced_on=LIVE_REGISTRY_PRICED_ON,
    ),
    judge=ModelSpec(
        provider="anthropic", model="claude-sonnet-5", role="judge",
        input_usd_per_mtok=2.00, output_usd_per_mtok=10.00,
        priced_on=LIVE_REGISTRY_PRICED_ON,
    ),
    refactorer=ModelSpec(
        provider="anthropic", model="claude-opus-5", role="refactorer",
        max_output_tokens=8192, input_usd_per_mtok=5.00, output_usd_per_mtok=25.00,
        priced_on=LIVE_REGISTRY_PRICED_ON,
    ),
)


# --------------------------------------------------------------------------- #
# Embedding space
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class EmbeddingSpaceConfig:
    """One versioned embedding space, used for retrieval, dedup and matching alike.

    A space id is recorded with every similarity score written to the store. Scores
    from different spaces are never comparable, so the id is what makes a threshold
    (τ_high, τ_low, τ_fit) a meaningful number rather than a floating constant.
    """

    space_id: str = "lexical-v1-512"
    mode: Literal["lexical", "openai"] = "lexical"
    dim: int = 512
    model: str | None = None

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


# --------------------------------------------------------------------------- #
# Policies
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class CheckpointPolicy:
    """When the slow loop wakes up (brief §16.7).

    Default: event-driven on codebook health, with a hard floor so a quiet codebook
    still gets a human look every `hard_floor_responses` responses.
    """

    mode: Literal["event_driven", "fixed"] = "event_driven"
    hard_floor_responses: int = 50
    #: Used when mode == "fixed": Chan's cadence — first 10, then every 10, scan at 50.
    fixed_cadence: tuple[int, ...] = (10, 20, 30, 40, 50)
    #: Event triggers (mode == "event_driven").
    max_near_duplicate_pairs: int = 3
    max_new_codes_per_batch: int = 8
    min_responses_between_checkpoints: int = 10

    # -- the spike rule (ADR-0033) ------------------------------------------ #
    #
    # An absolute ceiling cannot tell a first batch, where every code is new, from a
    # late batch where eight new codes means the codebook has stopped converging. These
    # three fields add a *relative* rule beside the absolute one: a batch spikes when it
    # admits at least `spike_min_new_codes` codes AND at least `spike_factor` times the
    # median of the previous `spike_window` batches. The first `spike_window` batches
    # have no baseline and therefore do not spike at all: the absolute fallback they
    # once used was retired by ADR-0040, because it repeated the comparison
    # `gaf.checks.health` already makes under `handover.new_codes`, which is the rule
    # that speaks there. See `gaf.checks.growth.RULE_ABSOLUTE`.
    #
    # UNCALIBRATED. Like tau_fit, these are set by argument rather than against human
    # judgment: 2.0 is "twice the recent normal", 3 is the shortest window whose median
    # is not just the previous batch, and 4 is the floor below which a doubling is
    # noise at this corpus size. Move them through a calibration report, not by hand.
    #: Multiple of the recent median that counts as a spike.
    spike_factor: float = 2.0
    #: How many previous batches the baseline median is taken over.
    spike_window: int = 3
    #: A batch below this many new codes never spikes, whatever the ratio says.
    spike_min_new_codes: int = 4

    def to_json(self) -> dict[str, Any]:
        data = asdict(self)
        data["fixed_cadence"] = list(self.fixed_cadence)
        return data


@dataclass(frozen=True, slots=True)
class AnalysisConfig:
    """The deterministic analysis tail (Chan 2025)."""

    #: Drop codes occurring in fewer than this many responses. Brief default: 2.
    min_code_frequency: int = 2
    #: Chan's own rule is a fraction of the sample ("less than 5% ... three out of
    #: fifty"). Set this to 0.05 to reproduce his filter exactly; when both are set the
    #: stricter of the two applies. `None` means "use the absolute count only".
    min_code_frequency_fraction: float | None = None

    linkage_method: str = "ward"
    linkage_metric: str = "euclidean"
    #: `None` -> derive from the agglomeration schedule: n_clusters = n_samples - break_stage.
    n_clusters: int | None = None
    #: Cluster means at or above this are "prominent" and highlighted (Chan: 0.4).
    cluster_mean_highlight: float = 0.4
    #: Batch size for the saturation curve (new codes per batch).
    saturation_batch_size: int = 10

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class LexicalConfig:
    """The model-free lexical validation of brief §13."""

    top_k_features: int = 20
    review_top_n: int = 10
    excerpts_per_word: int = 3
    bootstrap: int = 50
    cv_folds: int = 5
    cs: int = 10
    max_iter: int = 5000
    min_df: int = 2
    ngram_max: int = 1
    sublinear_tf: bool = True
    max_features: int | None = None
    stop_words: str | None = "english"
    #: Refuse to fit a binarised cut with fewer than this many positives or negatives.
    min_class_count: int = 10
    #: Primary continuous model; "poisson" fits an L1-penalised PoissonRegressor.
    continuous_model: Literal["lasso", "poisson"] = "lasso"
    #: High overlap (>= this) means the continuous/binary framing does not change the
    #: extracted vocabulary. Reported, never enforced — low overlap is a finding.
    jaccard_agreement_floor: float = 0.5

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


# --------------------------------------------------------------------------- #
# RunConfig
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class RunConfig:
    """Everything a run needs, and everything a run report must print.

    `offline=True` is the default and the only mode tests and CI ever use: mock model
    clients, the lexical embedding fallback, no API keys, no network.
    """

    run_id: str = "dev"
    corpus_path: Path | None = None
    output_dir: Path = Path("runs/dev")
    db_path: Path | None = None

    offline: bool = True
    seed: int = 1729

    rules: CodingRules = field(default_factory=CodingRules)
    models: ModelRegistry = MOCK_REGISTRY
    embedding: EmbeddingSpaceConfig = field(default_factory=EmbeddingSpaceConfig)
    checkpoints: CheckpointPolicy = field(default_factory=CheckpointPolicy)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    lexical: LexicalConfig = field(default_factory=LexicalConfig)

    #: Snapshots are frozen per batch; coders read a snapshot id, only the slow loop writes.
    snapshot_policy: Literal["per_batch", "per_checkpoint"] = "per_batch"
    batch_size: int = 10

    #: How many codes retrieval puts in front of a coder (context assembly, M2).
    retrieval_top_k: int = 8

    #: Question variant assumed for records whose source file does not carry one.
    question_variant: str = DEFAULT_QUESTION_VARIANT

    #: Brief §16.6 — hold human corrections out of the coder prompt (independent
    #: verification) or recycle them as few-shot examples (within-run improvement).
    #: Default is held-out: recycling makes the golden set no longer independent.
    recycle_human_corrections: bool = False

    #: LLM response cache directory; `None` disables the cache.
    cache_dir: Path | None = Path(".gaf_cache")

    #: Retry policy for live calls. Never exercised offline.
    max_retries: int = 3
    retry_base_delay_s: float = 0.5

    def resolved_question(self) -> str:
        return QUESTION_VARIANTS[self.question_variant]

    def with_(self, **changes: Any) -> RunConfig:
        return replace(self, **changes)

    def to_json(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "corpus_path": str(self.corpus_path) if self.corpus_path else None,
            "output_dir": str(self.output_dir),
            "db_path": str(self.db_path) if self.db_path else None,
            "offline": self.offline,
            "seed": self.seed,
            "rules": self.rules.to_json(),
            "models": self.models.to_json(),
            "embedding": self.embedding.to_json(),
            "checkpoints": self.checkpoints.to_json(),
            "analysis": self.analysis.to_json(),
            "lexical": self.lexical.to_json(),
            "snapshot_policy": self.snapshot_policy,
            "batch_size": self.batch_size,
            "retrieval_top_k": self.retrieval_top_k,
            "question_variant": self.question_variant,
            "recycle_human_corrections": self.recycle_human_corrections,
            "cache_dir": str(self.cache_dir) if self.cache_dir else None,
            "max_retries": self.max_retries,
            "retry_base_delay_s": self.retry_base_delay_s,
        }
