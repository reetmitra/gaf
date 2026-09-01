"""The embedding service — the one place a string becomes a vector.

Implements `gaf.embed.protocol.Embedder` in two modes, selected by
`EmbeddingSpaceConfig.mode`:

* **``"lexical"``** (the default, and the only mode tests and CI ever touch) — a
  deterministic offline fallback: hashed, stop-listed, lightly stemmed, sublinear-tf
  bag of words, L2-normalised. This is a **stand-in for the embedding space, not a
  return to lexical matching** (ADR-0003). The system's claim is that *one* versioned
  space serves retrieval, the dedup gate, cross-coder matching and code<->evidence fit;
  the fallback exists so that claim is testable from a clean clone with no key and no
  network, not because word overlap is meaning. When the space is live, every score in
  the system moves to the live space at once and the space id changes with it.
* **``"openai"``** — live embeddings. The SDK is an optional extra, imported lazily and
  never touched on the offline path.

**Space versioning is load-bearing.** `space_id` is *derived* from the mode, the model
and the dimensionality, so changing any of them changes the id by construction rather
than by remembering to edit a string. The id is recorded with every score written, and
scores from different spaces are never comparable — which is what makes tau_high,
tau_low and tau_fit meaningful numbers rather than floating constants.

Validation principles: **reliability** — the same text yields the same vector in the
same space, across runs, processes and platforms (hashlib, never `hash()`);
**transparency** — the space a score was computed in is part of the score.
"""

from __future__ import annotations

import hashlib
import importlib
import math
import re
from collections.abc import Iterable, Sequence
from typing import Any

import numpy as np

from gaf.config import EmbeddingSpaceConfig

__all__ = [
    "DEFAULT_OPENAI_MODEL",
    "LEXICAL_ALGORITHM_VERSION",
    "OPENAI_INSTALL_HINT",
    "STOPWORDS",
    "EmbeddingService",
    "MissingEmbeddingSDKError",
    "derive_space_id",
    "lexical_tokens",
    "lexical_vector",
]

#: Bumped whenever the lexical tokenisation or weighting changes. It is part of the
#: space id, so a change to the algorithm invalidates comparability with older scores
#: instead of silently shifting every threshold underneath them.
LEXICAL_ALGORITHM_VERSION = "v1"

#: Used when `EmbeddingSpaceConfig.model` is None and the mode is "openai".
DEFAULT_OPENAI_MODEL = "text-embedding-3-small"

OPENAI_INSTALL_HINT = "uv sync --extra openai"

#: The declared default of `EmbeddingSpaceConfig.space_id`. Read from an instance
#: because the config is a `slots=True` dataclass and has no class-level attribute.
_DEFAULT_SPACE_LABEL = EmbeddingSpaceConfig().space_id

#: Texts sent per live embedding request.
_OPENAI_BATCH_SIZE = 128

_TOKEN_RE = re.compile(r"[a-z0-9]+")


class MissingEmbeddingSDKError(RuntimeError):
    """The optional SDK for a live embedding mode is not installed."""


# --------------------------------------------------------------------------- #
# Lexical tokenisation
# --------------------------------------------------------------------------- #

#: Function words carry no topical signal, and because *every* code text contains some
#: of them they inflate the similarity of unrelated pairs — exactly the failure mode
#: ADR-0003 records for the predecessor's TF-IDF/Jaccard blend. Dropping them widens
#: the gap between the near-duplicate band and the unrelated band, which is what makes
#: a two-threshold router (tau_high / tau_low) behave sensibly offline.
STOPWORDS: frozenset[str] = frozenset(
    (
        "a", "an", "the", "and", "or", "but", "if", "then", "than", "that", "this", "these",
        "those", "there", "here", "is", "are", "was", "were", "be", "been", "being", "am", "to",
        "of", "in", "on", "at", "by", "for", "with", "without", "within", "from", "into", "onto",
        "over", "under", "about", "as", "it", "its", "they", "them", "their", "he", "she", "his",
        "her", "we", "us", "our", "you", "your", "i", "my", "me", "do", "does", "did", "done",
        "doing", "have", "has", "had", "having", "will", "would", "shall", "should", "can",
        "could", "may", "might", "must", "not", "no", "nor", "so", "such", "very", "more", "most",
        "much", "many", "some", "any", "all", "every", "each", "one", "two", "other", "another",
        "same", "also", "just", "even", "only"
    )
)

#: Applied in order; the first match wins. Deliberately a light plural/participle fold
#: (Porter step 1a/1b without the measure test), not a linguistics engine: it exists so
#: "job"/"jobs" and "replace"/"replaces" land on the same feature.
_SUFFIX_RULES: tuple[tuple[str, str], ...] = (
    ("sses", "ss"),
    ("ies", "y"),
    ("ing", ""),
    ("ed", ""),
    ("s", ""),
)

#: A stem shorter than this is left alone — folding "was"/"war" together would be worse
#: than leaving the plural in.
_MIN_STEM_LENGTH = 3


def _stem(token: str) -> str:
    """Fold a token's plural / participle suffix. Deterministic and documented."""
    if len(token) <= _MIN_STEM_LENGTH or token.endswith("ss"):
        return token
    for suffix, replacement in _SUFFIX_RULES:
        if token.endswith(suffix):
            stem = token[: len(token) - len(suffix)] + replacement
            if len(stem) >= _MIN_STEM_LENGTH:
                return stem
            return token
    return token


def lexical_tokens(text: str) -> list[str]:
    """Case-folded, stop-listed, lightly stemmed tokens, in order of appearance.

    Exported because a similarity that cannot be explained is a similarity a methods
    reviewer cannot audit: this is the whole feature extraction of the offline space.
    """
    return [
        _stem(token)
        for token in _TOKEN_RE.findall(text.casefold())
        if token not in STOPWORDS
    ]


def lexical_vector(text: str, dim: int) -> np.ndarray:
    """Hashed sublinear-tf bag of words, L2-normalised.

    Feature indices come from blake2b rather than `hash()`, whose salt differs between
    processes; sublinear tf (``1 + log(count)``) keeps a repeated word from dominating
    a short code description. All weights are non-negative, so cosine similarity stays
    in ``[0, 1]`` and a score reads the same way everywhere in the run report.
    """
    counts: dict[str, int] = {}
    for token in lexical_tokens(text):
        counts[token] = counts.get(token, 0) + 1
    vector = np.zeros(dim, dtype=np.float64)
    for token, count in counts.items():
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        vector[int.from_bytes(digest, "big") % dim] += 1.0 + math.log(count)
    norm = float(np.linalg.norm(vector))
    return vector if norm == 0.0 else vector / norm


# --------------------------------------------------------------------------- #
# Space identity
# --------------------------------------------------------------------------- #


def derive_space_id(config: EmbeddingSpaceConfig) -> str:
    """The identifier of the space `config` actually describes.

    The id is *derived*, never simply copied from `EmbeddingSpaceConfig.space_id`, so
    that changing the mode, the model or the dimensionality changes the id by
    construction. The canonical forms are ``lexical-<algorithm>-<dim>`` and
    ``openai-<model>-<dim>``; the default `EmbeddingSpaceConfig` yields
    ``"lexical-v1-512"``, which is exactly its declared default.

    An explicit non-default `config.space_id` is honoured as a **label** and kept as a
    prefix (``"<label>+<derived>"``), because a project may want to name a space for a
    calibration run — but the derived part still guarantees distinctness, so a label
    can never make two different spaces share an id.
    """
    if config.mode == "lexical":
        core = f"lexical-{LEXICAL_ALGORITHM_VERSION}-{config.dim}"
    else:
        core = f"{config.mode}-{config.model or DEFAULT_OPENAI_MODEL}-{config.dim}"
    label = (config.space_id or "").strip()
    if label and label != core and label != _DEFAULT_SPACE_LABEL:
        return f"{label}+{core}"
    return core


# --------------------------------------------------------------------------- #
# The service
# --------------------------------------------------------------------------- #


class EmbeddingService:
    """One versioned embedding space. Implements `gaf.embed.protocol.Embedder`.

    Memoised per instance: the same string is embedded many times in a run (a code
    appears in retrieval, in the dedup gate and in cross-coder matching), and the
    memo makes that free. The memo is keyed by the exact string, never normalised
    behind the caller's back — `gaf.embed.protocol.code_text` is the single rendering
    function and rendering is the caller's job.
    """

    def __init__(
        self,
        config: EmbeddingSpaceConfig | None = None,
        *,
        api_key: str | None = None,
    ) -> None:
        self.config = config or EmbeddingSpaceConfig()
        if self.config.dim < 1:
            raise ValueError(f"embedding dim must be >= 1, got {self.config.dim}")
        self._space_id = derive_space_id(self.config)
        self._memo: dict[str, np.ndarray] = {}
        self._api_key = api_key
        self._live_client: Any = None
        if self.config.mode == "openai":
            # Fail at construction, not halfway through a paid run.
            self._live_client = self._build_openai_client()
        elif self.config.mode != "lexical":  # pragma: no cover - guarded by the Literal
            raise ValueError(f"unknown embedding mode {self.config.mode!r}")

    # -- identity --------------------------------------------------------- #

    @property
    def space_id(self) -> str:
        """Derived id of this space. Recorded with every score written to the store."""
        return self._space_id

    @property
    def dim(self) -> int:
        return self.config.dim

    @property
    def model(self) -> str:
        """The live model name, or the algorithm version when running offline."""
        if self.config.mode == "lexical":
            return f"lexical-{LEXICAL_ALGORITHM_VERSION}"
        return self.config.model or DEFAULT_OPENAI_MODEL

    def __repr__(self) -> str:
        return f"EmbeddingService(space_id={self._space_id!r}, dim={self.config.dim})"

    # -- embedding -------------------------------------------------------- #

    def embed_one(self, text: str) -> np.ndarray:
        """Embed a single string. Returns a ``(dim,)`` float64 L2-normalised vector."""
        return self.embed([text])[0]

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        """Embed a batch. Returns a ``(len(texts), dim)`` float64 L2-normalised array.

        Only strings not already memoised reach the backend, and live calls are sent in
        batches — the same code text is embedded many times per response.
        """
        if not texts:
            return np.zeros((0, self.config.dim), dtype=np.float64)
        missing = self._uncached(texts)
        if missing:
            self._fill(missing)
        return np.vstack([self._memo[t] for t in texts])

    def _uncached(self, texts: Iterable[str]) -> list[str]:
        """Distinct texts not yet in the memo, in first-seen order (deterministic)."""
        seen: dict[str, None] = {}
        for text in texts:
            if text not in self._memo:
                seen.setdefault(text, None)
        return list(seen)

    def _fill(self, texts: list[str]) -> None:
        if self.config.mode == "lexical":
            for text in texts:
                self._memo[text] = lexical_vector(text, self.config.dim)
            return
        for start in range(0, len(texts), _OPENAI_BATCH_SIZE):
            chunk = texts[start : start + _OPENAI_BATCH_SIZE]
            for text, vector in zip(chunk, self._openai_embed(chunk), strict=True):
                self._memo[text] = vector

    # -- memo ------------------------------------------------------------- #

    @property
    def memo_size(self) -> int:
        """How many distinct strings this instance has embedded. Reported per run."""
        return len(self._memo)

    def clear_memo(self) -> None:
        self._memo.clear()

    # -- live backend ----------------------------------------------------- #

    def _build_openai_client(self) -> Any:
        """Import the optional SDK lazily and construct a client.

        `importlib.import_module` rather than a top-level ``import openai`` with a
        `# type: ignore[import-not-found]`: the ignore would be *correct* while the
        extra is uninstalled and *an error* the moment someone runs
        ``uv sync --extra openai``, because the project sets
        ``warn_unused_ignores = true``. Going through importlib types the module as
        `Any` in every configuration, so the offline default and the live extra both
        type-check without a comment that has to be maintained in two directions.
        """
        try:
            module = importlib.import_module("openai")
        except ImportError as exc:
            raise MissingEmbeddingSDKError(
                "the 'openai' package is required for EmbeddingSpaceConfig(mode='openai') "
                f"and is not installed; run `{OPENAI_INSTALL_HINT}`"
            ) from exc
        return module.OpenAI(api_key=self._api_key) if self._api_key else module.OpenAI()

    def _openai_embed(self, texts: list[str]) -> list[np.ndarray]:
        client = self._live_client
        kwargs: dict[str, object] = {"model": self.model, "input": list(texts)}
        # Only the text-embedding-3 family accepts a target dimensionality.
        if self.model.startswith("text-embedding-3"):
            kwargs["dimensions"] = self.config.dim
        response = client.embeddings.create(**kwargs)
        ordered = sorted(response.data, key=lambda item: item.index)
        vectors: list[np.ndarray] = []
        for item in ordered:
            vector = np.asarray(item.embedding, dtype=np.float64)
            if vector.shape != (self.config.dim,):
                raise ValueError(
                    f"space {self._space_id!r} expects dim {self.config.dim}, "
                    f"provider returned {vector.shape[0]}"
                )
            norm = float(np.linalg.norm(vector))
            vectors.append(vector if norm == 0.0 else vector / norm)
        return vectors
