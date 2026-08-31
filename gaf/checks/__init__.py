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
