"""Toy codebooks: one valid, one with a planted S6 violation of each kind, one with
near-duplicate leaves for M4.

Ids are readable slugs rather than hashes so that a failing assertion names something
a person can find. Evidence points at ids that exist in the synthetic corpus, except
in `broken_codebook`, where one deliberately does not.

Validation principle: **reliability**.
"""

from __future__ import annotations

from gaf.models import Code, Codebook, Evidence

__all__ = [
    "MISSING_RESPONSE_ID",
    "ORPHAN_PARENT_ID",
    "SEED_SNAPSHOT",
    "broken_codebook",
    "near_duplicate_codebook",
    "toy_codebook",
]

SEED_SNAPSHOT = "snap-seed"
ORPHAN_PARENT_ID = "c-does_not_exist"
#: Not present in `tests.fixtures.corpus` — trips the S6 corpus-reference check.
MISSING_RESPONSE_ID = 9999


def _code(
    name: str,
    description: str,
    parent_id: str | None = None,
    evidence: list[tuple[int, str]] | None = None,
    code_id: str | None = None,
) -> Code:
    return Code(
        id=code_id or f"c-{name}",
        name=name,
        description=description,
        parent_id=parent_id,
        created_in_snapshot=SEED_SNAPSHOT,
        evidence=[
            Evidence(response_id=rid, quote=q, verified=True, score=1.0)
            for rid, q in (evidence or [])
        ],
    )


def toy_codebook() -> Codebook:
    """A well-formed two-level codebook: three families, evidence only at the leaves."""
    codes = [
        _code("positive_impacts", "Ways respondents expect AI to improve life."),
        _code(
            "positive_impacts-healthcare",
            "AI improves diagnosis, monitoring or access to medical care.",
            parent_id="c-positive_impacts",
            evidence=[(203, "Rural clinics get diagnostic support"), (234, "Containers routed by a system")],
        ),
        _code(
            "positive_impacts-problem-solving",
            "AI solves problems respondents believe people cannot solve alone.",
            parent_id="c-positive_impacts",
            evidence=[(244, "problems too large to hold in one head")],
        ),
        _code("negative_impacts", "Harms respondents expect from AI."),
        _code(
            "negative_impacts-job_destruction",
            "Existing categories of paid work disappear.",
            parent_id="c-negative_impacts",
            evidence=[(207, "Firms will hand ticket triage"), (239, "the whole line runs without a shift supervisor")],
        ),
        _code(
            "negative_impacts-misuse",
            "AI is used against people's interests by whoever controls it.",
            parent_id="c-negative_impacts",
            evidence=[(245, "how narrow the door has become")],
        ),
        _code("future", "How respondents characterise the future as such."),
        _code(
            "future-inevitability",
            "AI's arrival is treated as unavoidable rather than chosen.",
            parent_id="c-future",
            evidence=[(258, "Quality of life improves on average")],
        ),
    ]
    return Codebook(codes={c.id: c for c in codes})


def broken_codebook() -> Codebook:
    """One planted violation of each S6 invariant.

    * duplicate name, case-insensitively (``future-hazard`` twice)  -> ERROR
    * ``parent_id`` pointing at a code that does not exist          -> ERROR
    * a parent chain three deep                                     -> WARN
    * a parent that carries evidence while having children          -> INFO
    * an empty description                                          -> WARN
    * evidence referencing a response id absent from the corpus     -> ERROR
    """
    codes = [
        # duplicate names differing only in case
        _code("future-hazard", "Risk characterisation.", code_id="c-dup-1"),
        _code("future-hazard", "Risk characterisation, again.", code_id="c-Dup-2"),
        # orphan parent
        _code("adoption-global", "AI adoption spreads worldwide.", parent_id=ORPHAN_PARENT_ID),
        # depth-3 chain: root -> mid -> deep
        _code("concern", "Concerns about AI.", code_id="c-depth-root"),
        _code("concern-ethics", "Ethical concerns.", parent_id="c-depth-root", code_id="c-depth-mid"),
        _code(
            "concern-ethics-consent",
            "Consent specifically.",
            parent_id="c-depth-mid",
            code_id="c-depth-deep",
        ),
        # a parent that carries its own evidence
        _code(
            "applications",
            "Concrete uses of AI.",
            evidence=[(234, "drivers dispatched to the yard")],
            code_id="c-parent-with-evidence",
        ),
        _code(
            "applications-predictive",
            "Predictive and preventive uses.",
            parent_id="c-parent-with-evidence",
        ),
        # empty description
        _code("adoption-workplace", "", code_id="c-no-description"),
        # evidence pointing outside the corpus
        _code(
            "future-unknown",
            "Uncertainty about what comes next.",
            evidence=[(MISSING_RESPONSE_ID, "a quote from a response that does not exist")],
            code_id="c-bad-evidence-ref",
        ),
    ]
    return Codebook(codes={c.id: c for c in codes})


def near_duplicate_codebook() -> Codebook:
    """Two near-synonymous leaves in one family, plus an unrelated leaf as a control.

    Under `StubEmbedder` the duplicate pair scores ~0.85 and each control pair ~0.15-0.22,
    so the case sits well clear of both tau_high (0.80) and tau_low (0.45) rather than on
    a boundary. M4 must WARN on the pair and stay silent on the controls. It must never
    merge them: near-duplicate detection feeds the slow-loop refactor proposal, and
    merging is a human-gated decision.
    """
    codes = [
        _code("negative_impacts", "Harms respondents expect from AI."),
        _code(
            "negative_impacts-job_destruction",
            "Paid work disappears as AI replaces human workers in existing jobs.",
            parent_id="c-negative_impacts",
            evidence=[(207, "Firms will hand ticket triage")],
        ),
        _code(
            "negative_impacts-job_loss",
            "Paid work disappears as AI replaces human workers and existing jobs are lost.",
            parent_id="c-negative_impacts",
            evidence=[(239, "Those households had one wage between four people")],
        ),
        _code(
            "negative_impacts-dependence",
            "People lose the ability to do the work without the system.",
            parent_id="c-negative_impacts",
            evidence=[(253, "nobody in the depot will remember how the rota used to be built")],
        ),
    ]
    return Codebook(codes={c.id: c for c in codes})
