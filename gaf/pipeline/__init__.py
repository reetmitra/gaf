"""The two loops — the only control flow a reader has to follow.

Fast loop, per response: deterministic prep, two independent coders against a frozen
snapshot, structural then semantic checks, a deterministic router, integration.
Slow loop, per checkpoint: health metrics, a refactor proposal as an edit script, a
human gate, a new snapshot.

If this cannot be printed in a methods appendix on one page, it is wrong.

Validation principle: **interpretive depth** — the human gate sits at the level of
codebook structure, where a person's judgment changes the analysis, and not on
item-by-item verification, which the Vaccaro et al. meta-analysis finds actively
harmful (see `docs/METHODS.md`).
"""

from __future__ import annotations

from gaf.pipeline.fast_loop import (
    FastLoopResult,
    LoopComponents,
    RunStats,
    batches,
    offline_components,
    run_fast_loop,
)
from gaf.pipeline.prep import PreparedResponse
from gaf.pipeline.router import ORIGINS, AcceptanceResult, IntegrationDecision, merge_evidence
from gaf.pipeline.slow_loop import (
    ACCEPT,
    CHECK_ID,
    EDIT,
    REJECT,
    ConsoleGate,
    EvidenceLossError,
    Gate,
    GateDecision,
    RefactorProposal,
    RejectAllGate,
    ScriptedGate,
    apply_operations,
    build_diff,
    evidence_pairs,
    render_diff,
    run_checkpoint,
    should_checkpoint,
    validate_script,
)

__all__ = [
    "ACCEPT",
    "CHECK_ID",
    "EDIT",
    "ORIGINS",
    "REJECT",
    "AcceptanceResult",
    "ConsoleGate",
    "EvidenceLossError",
    "FastLoopResult",
    "Gate",
    "GateDecision",
    "IntegrationDecision",
    "LoopComponents",
    "PreparedResponse",
    "RefactorProposal",
    "RejectAllGate",
    "RunStats",
    "ScriptedGate",
    "apply_operations",
    "batches",
    "build_diff",
    "evidence_pairs",
    "merge_evidence",
    "offline_components",
    "render_diff",
    "run_checkpoint",
    "run_fast_loop",
    "should_checkpoint",
    "validate_script",
]
