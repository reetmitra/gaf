"""One versioned embedding space, used for retrieval, dedup gating and matching alike.

The predecessor study matched codes with TF-IDF cosine blended with word-set Jaccard
at a 0.3 threshold, and recovered only 21 matched pairs against 66 and 73 unmatched
codes (Ng & Chan 2026). Lexical overlap is not meaning. This package replaces that
arithmetic with a single embedding space in which every similarity in the system is
computed, so that one threshold means one thing everywhere.

Validation principle: **epistemic diversity** — cross-coder agreement is only evidence
of convergence if the two coders are compared in a space that measures meaning.
"""
