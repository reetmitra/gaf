"""Candidate sets with a planted violation for every structural and semantic check.

Each case is a `Case`: the check it targets, the response it belongs to, the
candidates, and what the check is expected to say. A3, A4 and B2 assert against these
rather than inventing their own inputs, so "S4 fires on three codes for one segment"
means the same thing in every test file in the repo.

Evidence here is deliberately **unverified** (``verified=False``, ``span=None``):
provenance is S2's job, and a fixture that pre-verified its own quotes would let a
broken locator pass.

Two Wave-0 rulings, recorded so no agent has to guess:

* a description that is present but a **verbatim copy of one of its own quotes** is a
  WARN, not an ERROR. The description is not *missing*, and the brief reserves ERROR
  for structural certainty of invalidity; dropping a candidate over a formatting
  complaint would destroy data that the human gate can repair.
* ``AI-superintelligence`` must produce **no** S3 grammar finding: the pattern is
  applied after lowercasing, exactly as the brief specifies, because the PI's own
  codes are capitalised inconsistently.

Validation principle: **reliability**.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gaf.checks.contracts import Severity
from gaf.models import Candidate, Evidence
from tests.fixtures.corpus import (
    FABRICATED_QUOTE,
    MOCKFIT_UNNECESSARY,
    S2B_THREE_SENTENCES,
    S4_SHARED_SENTENCE,
    corpus_by_id,
)

__all__ = ["CASES", "Case", "cand", "case", "clean_candidates", "word_windows"]

_CORPUS = corpus_by_id()


def cand(
    name: str,
    description: str,
    quotes: list[str],
    response_id: int,
    coder: str = "coder_a",
    parent_hint: str | None = None,
) -> Candidate:
    """Build a candidate with unverified evidence — S2 decides provenance, not fixtures."""
    return Candidate(
        name=name,
        description=description,
        evidence=[Evidence(response_id=response_id, quote=q) for q in quotes],
        coder=coder,
        parent_hint=parent_hint,
    )


def word_windows(response_id: int, count: int, width: int = 4, start: int = 0) -> list[str]:
    """`count` non-overlapping `width`-word quotes from a response, in order.

    Non-overlapping by construction so a fixture built for S5 (counts) does not also
    trip S4 (segment discipline).
    """
    from gaf.textnorm import normalise

    words = normalise(_CORPUS[response_id].content).split(" ")
    windows: list[str] = []
    cursor = start
    for _ in range(count):
        if cursor + width > len(words):
            raise ValueError(f"response {response_id} is too short for {count} windows")
        windows.append(" ".join(words[cursor : cursor + width]))
        cursor += width
    return windows


@dataclass(frozen=True, slots=True)
class Case:
    """One planted scenario and the finding it is expected to produce."""

    check_id: str
    description: str
    response_id: int
    candidates: list[Candidate]
    expect_severity: Severity | None  # None => the check must stay silent
    expect_subcode: str = ""  # e.g. "sub_code_first", "too_many_codes"
    notes: str = ""
    #: Codebook names assumed to already exist (S3's sub-code-first rule needs them).
    existing_names: list[str] = field(default_factory=list)


def clean_candidates(response_id: int = 3, coder: str = "coder_a") -> list[Candidate]:
    """Four well-formed candidates that must produce no ERROR and no WARN."""
    quotes = word_windows(response_id, 4, width=5)
    names = [
        ("positive_impacts-healthcare", "AI improves diagnosis and access to medical care."),
        ("positive_impacts-agriculture", "AI supports farming decisions such as planting times."),
        ("negative_impacts-job_destruction", "AI removes existing categories of paid work."),
        ("future-inevitability", "AI is treated as an unavoidable feature of the future."),
    ]
    return [
        cand(name, desc, [quote], response_id, coder=coder)
        for (name, desc), quote in zip(names, quotes, strict=True)
    ]


# --------------------------------------------------------------------------- #
# The planted cases
# --------------------------------------------------------------------------- #

_R203 = 203
_R212 = 212
_R217 = 217
_R231 = 231
_R218 = 218
_R239 = 239

CASES: dict[str, Case] = {
    "clean": Case(
        check_id="-",
        description="Four well-formed candidates on one response.",
        response_id=_R203,
        candidates=clean_candidates(_R203),
        expect_severity=None,
    ),
    # -- S1 schema ---------------------------------------------------------- #
    "S1_no_evidence": Case(
        check_id="S1",
        description="Candidate with no evidence at all.",
        response_id=_R203,
        candidates=[cand("future-inevitability", "AI is taken as given.", [], _R203)],
        expect_severity=Severity.ERROR,
        expect_subcode="missing_evidence",
        notes="Dropped: a code without evidence cannot be traced to the corpus.",
    ),
    "S1_empty_name": Case(
        check_id="S1",
        description="Candidate with an empty name.",
        response_id=_R203,
        candidates=[cand("", "Something about the future.", word_windows(_R203, 1), _R203)],
        expect_severity=Severity.ERROR,
        expect_subcode="missing_name",
    ),
    "S1_no_description": Case(
        check_id="S1",
        description="Candidate with an empty description — kept, embedder falls back to the name.",
        response_id=_R203,
        candidates=[cand("positive_impacts-healthcare", "", word_windows(_R203, 1), _R203)],
        expect_severity=Severity.WARN,
        expect_subcode="missing_description",
    ),
    "S1_description_copies_quote": Case(
        check_id="S1",
        description="Description is a verbatim copy of its own quote.",
        response_id=_R203,
        candidates=[
            cand(
                "positive_impacts-healthcare",
                word_windows(_R203, 1)[0],
                word_windows(_R203, 1),
                _R203,
            )
        ],
        expect_severity=Severity.WARN,
        expect_subcode="description_copies_quote",
        notes="WARN, not ERROR — see this module's docstring.",
    ),
    # -- S2 provenance ------------------------------------------------------ #
    "S2_fabricated_quote": Case(
        check_id="S2",
        description="One fabricated quote alongside one genuine quote.",
        response_id=_R203,
        candidates=[
            cand(
                "positive_impacts-healthcare",
                "AI improves diagnosis and access to care.",
                [word_windows(_R203, 1)[0], FABRICATED_QUOTE],
                _R203,
            )
        ],
        expect_severity=Severity.INFO,
        expect_subcode="quote_unverified",
        notes="The fabricated quote is dropped; the candidate survives on the genuine one.",
    ),
    "S2_all_quotes_fabricated": Case(
        check_id="S2",
        description="Every quote fabricated — nothing left to stand on.",
        response_id=_R203,
        candidates=[
            cand("future-inevitability", "AI is taken as given.", [FABRICATED_QUOTE], _R203)
        ],
        expect_severity=Severity.ERROR,
        expect_subcode="no_verified_evidence",
    ),
    "S2b_long_quote": Case(
        check_id="S2b",
        description="A verified quote spanning three sentences.",
        response_id=_R212,
        candidates=[
            cand(
                "future-ubiquity",
                "Machine learning becomes pervasive in everyday decisions.",
                [S2B_THREE_SENTENCES],
                _R212,
            )
        ],
        expect_severity=Severity.WARN,
        expect_subcode="quote_too_long",
        notes="Coding is applied at the level of phrase or sentence.",
    ),
    # -- S3 name grammar and hierarchy discipline --------------------------- #
    "S3_bad_grammar": Case(
        check_id="S3",
        description="A prose code name with spaces and capitals.",
        response_id=_R203,
        candidates=[cand("Some Vague Topic", "Unclear.", word_windows(_R203, 1), _R203)],
        expect_severity=Severity.WARN,
        expect_subcode="name_grammar",
    ),
    "S3_good_names": Case(
        check_id="S3",
        description="Names the PI actually uses, including his inconsistent ones.",
        response_id=_R203,
        candidates=[
            cand("negative_impacts-job_destruction", "Paid work disappears.", w, _R203)
            for w in [[q] for q in word_windows(_R203, 1)]
        ]
        + [
            cand(
                "positive_impacts-problem-solving",
                "AI solves problems people cannot.",
                [word_windows(_R203, 2, start=4)[1]],
                _R203,
            ),
            cand(
                "AI-superintelligence",
                "AI exceeds human capability in general.",
                [word_windows(_R203, 3, start=12)[2]],
                _R203,
            ),
        ],
        expect_severity=None,
        notes=(
            "Hyphen inside a sub-code and a capitalised family must both pass: the "
            "first-hyphen split and the lowercased pattern are what make that true."
        ),
    ),
    "S3_subcode_first": Case(
        check_id="S3",
        description="A bare top-level name proposed while that family already exists.",
        response_id=_R203,
        candidates=[
            cand("negative_impacts", "Bad things happen.", word_windows(_R203, 1), _R203)
        ],
        expect_severity=Severity.WARN,
        expect_subcode="sub_code_first",
        existing_names=["negative_impacts-job_destruction", "positive_impacts-healthcare"],
    ),
    # -- S4 segment discipline ---------------------------------------------- #
    "S4_three_codes_one_segment": Case(
        check_id="S4",
        description="Three distinct codes attached to the same sentence.",
        response_id=_R217,
        candidates=[
            cand("adoption-workplace", "AI enters every workplace.", [S4_SHARED_SENTENCE], _R217),
            cand("applications-assistant", "AI acts as an assistant.", [S4_SHARED_SENTENCE], _R217),
            cand("future-ubiquity", "AI is everywhere.", [S4_SHARED_SENTENCE], _R217),
        ],
        expect_severity=Severity.ERROR,
        expect_subcode="too_many_codes_on_segment",
        notes="Keep-and-flag: all three survive, the finding goes to the human gate.",
    ),
    "S4_two_codes_one_segment": Case(
        check_id="S4",
        description="Two codes on one segment — the PI's stated maximum, so silent.",
        response_id=_R217,
        candidates=[
            cand("adoption-workplace", "AI enters every workplace.", [S4_SHARED_SENTENCE], _R217),
            cand("applications-assistant", "AI acts as an assistant.", [S4_SHARED_SENTENCE], _R217),
        ],
        expect_severity=None,
    ),
    # -- S5 response-level counts ------------------------------------------- #
    "S5_too_few": Case(
        check_id="S5",
        description="A single code on a whole response.",
        response_id=_R203,
        candidates=[
            cand("positive_impacts-healthcare", "AI improves care.", word_windows(_R203, 1), _R203)
        ],
        expect_severity=Severity.WARN,
        expect_subcode="too_few_codes",
    ),
    "S5_too_many": Case(
        check_id="S5",
        description="Thirteen codes on one response — above the PI's usual maximum of 12.",
        response_id=_R218,
        candidates=[
            cand(f"future-aspect_{i:02d}", f"Aspect {i} of the imagined future.", [quote], _R218)
            for i, quote in enumerate(word_windows(_R218, 13, width=4))
        ],
        expect_severity=Severity.WARN,
        expect_subcode="too_many_codes",
        notes="Windows are non-overlapping so this case does not also trip S4.",
    ),
    "S5_in_range": Case(
        check_id="S5",
        description="Five codes — comfortably inside 2..12.",
        response_id=_R239,
        candidates=[
            cand(f"negative_impacts-strand_{i}", f"Strand {i}.", [quote], _R239)
            for i, quote in enumerate(word_windows(_R239, 5, width=4))
        ],
        expect_severity=None,
    ),
    # -- M3 code<->evidence fit --------------------------------------------- #
    "M3_unnecessary": Case(
        check_id="M3",
        description="A quote the mock judge rules UNNECESSARY, and it is the only evidence.",
        response_id=_R231,
        candidates=[
            cand(
                "positive_impacts-healthcare",
                "AI supports personal health monitoring.",
                [MOCKFIT_UNNECESSARY],
                _R231,
            )
        ],
        expect_severity=Severity.ERROR,
        expect_subcode="candidate_dropped_no_evidence",
        notes="Quote removed by M3; the candidate then has nothing left and is dropped.",
    ),
    "M3_applies": Case(
        check_id="M3",
        description="A quote that plainly supports its code.",
        response_id=_R231,
        candidates=[
            cand(
                "positive_impacts-healthcare",
                "AI supports personal health monitoring.",
                ["It will track the medicine cabinet"],
                _R231,
            )
        ],
        expect_severity=Severity.INFO,
        expect_subcode="fit_ok",
    ),
}


def case(name: str) -> Case:
    """Look up a planted case, with a helpful error listing the available ones."""
    try:
        return CASES[name]
    except KeyError:
        raise KeyError(f"unknown case {name!r}; available: {sorted(CASES)}") from None
