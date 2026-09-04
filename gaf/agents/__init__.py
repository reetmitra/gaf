"""The three LLM roles: Coder, Judge, Refactorer. There are no others.

Slicing, quote checking, comparison and change tracking are deterministic code, not
model calls. Every agent removed is a removed source of drift, cost and
non-reproducibility — which is why this package is small.

Validation principle: **epistemic diversity** — two coders from different providers
disagree about meaning, and that disagreement is both the escalation signal and the
evidence that the coding is not one model's idiosyncrasy.
"""

from __future__ import annotations

from gaf.agents.coder import CoderAgent, CoderContext, CodingProposal, parse_candidates, subject_for
from gaf.agents.judge import JudgeAgent, JudgeRuling
from gaf.agents.refactorer import (
    EditScript,
    RefactorContext,
    RefactorerAgent,
    codebook_digest,
    parse_operations,
    usage_from_codebook,
    usage_summary,
)

__all__ = [
    "CoderAgent",
    "CoderContext",
    "CodingProposal",
    "EditScript",
    "JudgeAgent",
    "JudgeRuling",
    "RefactorContext",
    "RefactorerAgent",
    "codebook_digest",
    "parse_candidates",
    "parse_operations",
    "subject_for",
    "usage_from_codebook",
    "usage_summary",
]
