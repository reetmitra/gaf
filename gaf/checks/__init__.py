"""The concurrent-validation layer: structural (S1-S6) and semantic (M1-M4) checks.

These two suites are this pipeline's implementation of the **concurrent validation**
step of the Alqazlan et al. HITL computational grounded theory framework — validation
folded into the analysis as a practice, not bolted on afterwards as correction.

Structural checks operationalise *reliability* and *transparency*: every violation is
a deterministic, replayable fact tied to a snapshot id. Semantic checks operationalise
*interpretive depth* and *epistemic diversity*: meaning is validated by model-vs-model
agreement in one versioned geometry, with a third-provider judge for genuine ambiguity.

A checker returns findings. A checker never mutates the codebook, never writes to the
store, and never calls the router.
"""

from __future__ import annotations

# `semantic` needs `gaf.llm.base` (for `validate_enum`) — deliberately not
# `gaf.embed.service`, so this package never depends on a concrete embedding provider,
# only on the frozen `gaf.embed.protocol.Embedder` protocol. `gaf.llm.mock` and the
# three provider clients need `gaf.checks.contracts` in turn; both directions resolve
# because `contracts.py` and `llm/base.py` are themselves leaves with no imports back
# into either package, so re-exporting here does not introduce an import cycle.
from gaf.checks.contracts import (
    CHECK_IDS,
    FIT_VERDICTS,
    SCOPES,
    CheckFinding,
    CheckReport,
    Severity,
)
from gaf.checks.health import (
    DEFAULT_TAU_FIT_GRID,
    CheckpointSignals,
    HealthMetrics,
    calibrate_thresholds,
    checkpoint_signals,
    codebook_health,
    saturation_curve,
    saturation_from_codebooks,
)
from gaf.checks.semantic import (
    BAND_AGREED,
    BAND_DISPUTED,
    BAND_GREY,
    DEFAULT_RULES,
    UNMATCHED,
    AgreementResult,
    Judge,
    RoutingResult,
    assign_optimal,
    check_code_evidence_fit,
    check_cross_coder_agreement,
    check_integration_routing,
    check_near_duplicate_leaves,
    compare_codebooks,
    cosine_matrix,
)
from gaf.checks.structural import (
    MARKER_KEY,
    check_candidates,
    check_codebook,
    check_s1,
    check_s2,
    check_s2b,
    check_s3,
    check_s4,
    check_s5,
    locate_quote,
)

__all__ = [
    "BAND_AGREED",
    "BAND_DISPUTED",
    "BAND_GREY",
    "CHECK_IDS",
    "DEFAULT_RULES",
    "DEFAULT_TAU_FIT_GRID",
    "FIT_VERDICTS",
    "MARKER_KEY",
    "SCOPES",
    "UNMATCHED",
    "AgreementResult",
    "CheckFinding",
    "CheckReport",
    "CheckpointSignals",
    "HealthMetrics",
    "Judge",
    "RoutingResult",
    "Severity",
    "assign_optimal",
    "calibrate_thresholds",
    "check_candidates",
    "check_code_evidence_fit",
    "check_codebook",
    "check_cross_coder_agreement",
    "check_integration_routing",
    "check_near_duplicate_leaves",
    "check_s1",
    "check_s2",
    "check_s2b",
    "check_s3",
    "check_s4",
    "check_s5",
    "checkpoint_signals",
    "codebook_health",
    "compare_codebooks",
    "cosine_matrix",
    "locate_quote",
    "saturation_curve",
    "saturation_from_codebooks",
]
