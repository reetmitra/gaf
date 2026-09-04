"""One versioned embedding space, used for retrieval, dedup gating and matching alike.

The predecessor study matched codes with TF-IDF cosine blended with word-set Jaccard
at a 0.3 threshold, and recovered only 21 matched pairs against 66 and 73 unmatched
codes (Ng & Chan 2026). Lexical overlap is not meaning. This package replaces that
arithmetic with a single embedding space in which every similarity in the system is
computed, so that one threshold means one thing everywhere.

Validation principle: **epistemic diversity** — cross-coder agreement is only evidence
of convergence if the two coders are compared in a space that measures meaning.
"""

from __future__ import annotations

from gaf.embed.matcher import ScoredCode, cosine_matrix, hungarian_match, top_k_codes

# `Route`, `code_text`, `cosine` and `route_similarity` are defined once, in the
# frozen `protocol` module; `matcher` and `service` both import them from there
# rather than redefining them, so this package re-exports that one copy.
from gaf.embed.protocol import Embedder, Route, code_text, cosine, route_similarity
from gaf.embed.service import (
    LEXICAL_ALGORITHM_VERSION,
    EmbeddingService,
    MissingEmbeddingSDKError,
    derive_space_id,
    lexical_tokens,
    lexical_vector,
)

__all__ = [
    "LEXICAL_ALGORITHM_VERSION",
    "Embedder",
    "EmbeddingService",
    "MissingEmbeddingSDKError",
    "Route",
    "ScoredCode",
    "code_text",
    "cosine",
    "cosine_matrix",
    "derive_space_id",
    "hungarian_match",
    "lexical_tokens",
    "lexical_vector",
    "route_similarity",
    "top_k_codes",
]
