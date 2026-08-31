"""A deterministic stub embedder implementing `gaf.embed.protocol.Embedder`.

Exists so the check layer (A4) can be written and tested against the *protocol*
without depending on A2's embedding service. It is not the production offline
fallback — it is the smallest thing that satisfies the contract and produces stable,
intuitive similarities: a hashed bag-of-words vector, L2-normalised, so two strings
sharing vocabulary are close and two sharing none are near-orthogonal.

Validation principle: **reliability** — same text, same vector, every run, no seed.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Sequence

import numpy as np

__all__ = ["StubEmbedder"]

_TOKEN_RE = re.compile(r"[a-z0-9]+")


class StubEmbedder:
    """Hashed bag-of-words. Deterministic across processes (hashlib, not `hash()`)."""

    def __init__(self, dim: int = 256, space_id: str = "stub-v1-256") -> None:
        self._dim = dim
        self._space_id = space_id

    @property
    def space_id(self) -> str:
        return self._space_id

    @property
    def dim(self) -> int:
        return self._dim

    def _tokens(self, text: str) -> list[str]:
        return _TOKEN_RE.findall(text.casefold())

    def embed_one(self, text: str) -> np.ndarray:
        vector = np.zeros(self._dim, dtype=np.float64)
        for token in self._tokens(text):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            index = int.from_bytes(digest, "big") % self._dim
            vector[index] += 1.0
        norm = float(np.linalg.norm(vector))
        return vector if norm == 0.0 else vector / norm

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self._dim), dtype=np.float64)
        return np.vstack([self.embed_one(t) for t in texts])
