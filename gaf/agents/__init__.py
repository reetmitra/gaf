"""The LLM roles: Coder, Judge and Refactorer in the loops, Definer outside them.

Slicing, quote checking, comparison and change tracking are deterministic code, not
model calls. Every agent removed is a removed source of drift, cost and
non-reproducibility — which is why this package is small.

Three of the four roles are the pipeline's: two Coders and a Judge in the fast loop, a
Refactorer at the human-gated checkpoint. The fourth, the **Definer**, is in neither
loop. It runs once over a coding a person has already finished and writes one thing —
the one-to-three-sentence description of a code — because that is the only part of
building a codebook from finished code-text pairings that is not arithmetic. It never
sees a response being coded and never proposes, renames, merges or splits anything: its
reply object has one key. See `gaf.agents.definer` and ADR-0034.

Validation principle: **epistemic diversity** — two coders from different providers
disagree about meaning, and that disagreement is both the escalation signal and the
evidence that the coding is not one model's idiosyncrasy.
"""

from __future__ import annotations

from gaf.agents.coder import CoderAgent, CoderContext, CodingProposal, parse_candidates, subject_for
from gaf.agents.definer import (
    ChildSummary,
    DefineContext,
    DefinerAgent,
    Definition,
    check_description,
    definition_subject,
    parse_description,
)
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
    "ChildSummary",
    "CoderAgent",
    "CoderContext",
    "CodingProposal",
    "DefineContext",
    "DefinerAgent",
    "Definition",
    "EditScript",
    "JudgeAgent",
    "JudgeRuling",
    "RefactorContext",
    "RefactorerAgent",
    "check_description",
    "codebook_digest",
    "definition_subject",
    "parse_candidates",
    "parse_description",
    "parse_operations",
    "subject_for",
    "usage_from_codebook",
    "usage_summary",
]
