"""Model clients: one protocol, three live providers, deterministic mocks, a disk cache.

No agent framework, no cross-call memory, no fine-tuning. Every call is stateless and
re-grounded from canonical sources; handoffs between stages carry ids, not prose. The
offline path (mock clients) is the default and the only path tests and CI use.

Validation principle: **reliability** — a stateless, content-addressed, cached call is
a replayable fact; a conversation with a model is not.
"""
