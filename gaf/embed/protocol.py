"""The embedding contract: what an embedder must provide, and how codes are rendered.

FROZEN CONTRACT (Wave 0). No Wave 1+ agent may change this module.

A2 implements this protocol (`gaf/embed/service.py`); A4's semantic checks are written
against *this module* and tested with a stub, so the check layer never depends on a
particular embedding backend. `code_text` and `Route` live here rather than in either
implementation because M1, M2, M3 and the matcher must render and route identically —
a code embedded one way for retrieval and another way for dedup would silently break
every threshold in `CodingRules`.

Validation principle: **reliability** — one geometry, one rendering, one set of bands.
"""

from __future__ import annotations

from collections.abc import Sequence
from enum import Enum
from typing import Protocol, runtime_checkable

import numpy as np

__all__ = ["Embedder", "Route", "code_text", "cosine", "route_similarity"]


class Route(Enum):
    """The M2 integration decision, and the only three outcomes that exist."""

    MERGE = "MERGE"  # >= tau_high: fold into the existing code (the dedup gate)
    CREATE = "CREATE"  # < tau_low: genuinely new, admit it
    JUDGE = "JUDGE"  # in between: the grey zone, and the only case that costs a call

    def __str__(self) -> str:
        return self.value


def code_text(name: str, description: str = "") -> str:
    """Canonical string form of a code or candidate for embedding.

    ``"name: description"``, or just the name when there is no description (S1 emits a
    WARN in that case and the embedder falls back to the name alone). Every stage that
    embeds a code must call this — never `f"{name} {description}"` by hand.
    """
    name = name.strip()
    description = description.strip()
    return f"{name}: {description}" if description else name


def route_similarity(score: float, tau_high: float, tau_low: float) -> Route:
    """Map a cosine score to an integration route.

    The two-threshold band is the mechanism that replaces the predecessor's single
    0.3 cut: above `tau_high` the geometry is certain enough to merge, below `tau_low`
    certain enough to create, and only the band between them is genuinely ambiguous
    and therefore worth a frontier call.
    """
    if score >= tau_high:
        return Route.MERGE
    if score < tau_low:
        return Route.CREATE
    return Route.JUDGE


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity of two 1-D vectors, safe on zero vectors (returns 0.0)."""
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0.0:
        return 0.0
    return float(np.dot(a, b) / denom)


@runtime_checkable
class Embedder(Protocol):
    """What every embedding backend must provide.

    Implementations must be **deterministic**: the same text in the same space id
    always yields the same vector, within a run and across runs. Vectors are returned
    L2-normalised, so cosine similarity is a dot product and `cosine` is exact.
    """

    @property
    def space_id(self) -> str:
        """Identifier of the versioned space, recorded with every score written."""
        ...

    @property
    def dim(self) -> int:
        """Dimensionality of the returned vectors."""
        ...

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        """Embed a batch. Returns a ``(len(texts), dim)`` float64 array, L2-normalised."""
        ...

    def embed_one(self, text: str) -> np.ndarray:
        """Embed a single string. Returns a ``(dim,)`` float64 vector, L2-normalised."""
        ...
