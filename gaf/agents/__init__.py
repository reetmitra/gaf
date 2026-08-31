"""The three LLM roles: Coder, Judge, Refactorer. There are no others.

Slicing, quote checking, comparison and change tracking are deterministic code, not
model calls. Every agent removed is a removed source of drift, cost and
non-reproducibility — which is why this package is small.

Validation principle: **epistemic diversity** — two coders from different providers
disagree about meaning, and that disagreement is both the escalation signal and the
evidence that the coding is not one model's idiosyncrasy.
"""
