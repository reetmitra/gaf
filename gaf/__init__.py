"""Grounded AI Futures (gaf) — a reproducible hybrid human-LLM grounded-theory coding pipeline.

Research question: *What are the constituent elements of global AI futures?*

The package implements two loops and three LLM roles, and nothing else:

* a **fast loop** (per response) — deterministic prep, two independent coders,
  structural + semantic checks, a router, integration into the codebook;
* a **slow loop** (per checkpoint) — health metrics, a refactor proposal as an
  edit script, a human gate, a new frozen snapshot;
* a **deterministic analysis tail** — binary occurrence matrix, Ward's HCA,
  agglomeration schedule, cluster means;
* a **deterministic validation layer** — concurrent validation against the
  human golden set, and a model-free lexical check on the driving vocabulary.

Design law: complexity may live in infrastructure (deterministic code, one
versioned embedding space, a SQLite blackboard, routing rules). It may not live
in the control flow.

Validation principles served by the package as a whole (Ng & Chan 2026):
transparency, reliability, interpretive depth, epistemic diversity.
"""

__version__ = "0.1.0"
