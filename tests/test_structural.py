"""Structural checks S1-S6, driven by the planted cases in `tests/fixtures/candidates.py`.

Every check gets at least one violating case and one passing case, and the passing
cases are the point: `S3_good_names` is the regression guard on the PI's own
inconsistent naming (`AI-superintelligence`, `positive_impacts-problem-solving`), and
`S4_two_codes_one_segment` is the guard on his stated maximum being a maximum rather
than a limit of one.

Three properties are asserted across the whole suite rather than case by case, because
they are the properties the rest of the pipeline relies on:

* **no checker mutates its input** — the candidates handed in are unchanged afterwards;
* **findings are deterministically ordered** — two runs produce identical reports;
* **spans index the normalised text**, not the raw source.

Validation principle: **reliability**.
"""

from __future__ import annotations

import difflib

import pytest

from gaf.checks.contracts import CheckReport, Severity
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
from gaf.config import CodingRules
from gaf.models import Candidate, Code, Codebook, Response
from gaf.textnorm import normalise
from tests.fixtures.candidates import CASES, Case, cand, case, word_windows
from tests.fixtures.codebooks import (
    MISSING_RESPONSE_ID,
    ORPHAN_PARENT_ID,
    broken_codebook,
    toy_codebook,
)
from tests.fixtures.corpus import (
    FABRICATED_QUOTE,
    S2B_THREE_SENTENCES,
    S4_SHARED_SENTENCE,
    corpus_by_id,
    response_ids,
)

CORPUS = corpus_by_id()
RULES = CodingRules()

#: The order the gate runs its checks in. Every report must respect it.
CHECK_ORDER = {"S1": 0, "S2": 1, "S2b": 2, "S3": 3, "S4": 4, "S5": 5}

#: The planted cases this file owns; M3 belongs to the semantic suite.
GATE_CASES = sorted(name for name, planted in CASES.items() if planted.check_id != "M3")


def run_case(planted: Case) -> tuple[list[Candidate], CheckReport]:
    return check_candidates(
        planted.candidates, CORPUS[planted.response_id], planted.existing_names
    )


def markers(report: CheckReport, check_id: str) -> list[str]:
    return [f.data[MARKER_KEY] for f in report.by_check(check_id)]


def snapshot(candidates: list[Candidate]) -> list[dict[str, object]]:
    return [c.to_json() for c in candidates]


# --------------------------------------------------------------------------- #
# The planted cases, end to end
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("name", GATE_CASES)
def test_planted_case_produces_exactly_its_expected_finding(name: str) -> None:
    planted = case(name)
    _, report = run_case(planted)

    if planted.expect_severity is None:
        assert list(report) == [], f"{name} must be silent, got {[str(f) for f in report]}"
        return

    matching = [
        f
        for f in report.by_check(planted.check_id)
        if f.data[MARKER_KEY] == planted.expect_subcode
    ]
    assert len(matching) == 1, f"{name}: {[str(f) for f in report]}"
    assert matching[0].severity is planted.expect_severity


@pytest.mark.parametrize("name", GATE_CASES)
def test_findings_are_emitted_in_check_order(name: str) -> None:
    _, report = run_case(case(name))
    positions = [CHECK_ORDER[f.check_id] for f in report]
    assert positions == sorted(positions)


@pytest.mark.parametrize("name", GATE_CASES)
def test_no_checker_mutates_its_input(name: str) -> None:
    planted = case(name)
    before = snapshot(planted.candidates)
    survivors, _ = run_case(planted)
    assert snapshot(planted.candidates) == before
    # The surviving objects are new ones, so verification cannot have been written
    # back into the originals.
    for original in planted.candidates:
        assert all(not e.verified and e.span is None for e in original.evidence)
    for survivor in survivors:
        assert all(e.verified and e.span is not None for e in survivor.evidence)


@pytest.mark.parametrize("name", GATE_CASES)
def test_reports_are_deterministic(name: str) -> None:
    planted = case(name)
    first_survivors, first = run_case(planted)
    second_survivors, second = run_case(planted)
    assert first.to_json() == second.to_json()
    assert snapshot(first_survivors) == snapshot(second_survivors)


def test_every_finding_carries_a_marker_and_a_one_sentence_message() -> None:
    for name in GATE_CASES:
        _, report = run_case(case(name))
        for finding in report:
            assert finding.data.get(MARKER_KEY), f"{name}: {finding} has no marker"
            assert "\n" not in finding.message
            assert finding.message.endswith((".", "?", "!"))


# --------------------------------------------------------------------------- #
# S2 — the quote locator
# --------------------------------------------------------------------------- #

_R203_TEXT = normalise(CORPUS[203].content)
_R203_QUOTE = "the nearest specialist stops being four hours away"


def test_locate_quote_span_slices_back_to_the_quote() -> None:
    found, score, span = locate_quote(_R203_QUOTE, _R203_TEXT, RULES.fuzzy_threshold)
    assert found is True
    assert score == 1.0
    assert span is not None
    assert _R203_TEXT[span[0] : span[1]] == _R203_QUOTE


def test_locate_quote_spans_index_the_normalised_text_not_the_raw_source() -> None:
    """Response 244 carries curly quotes and an em dash, so raw and normalised differ."""
    raw = CORPUS[244].content
    text = normalise(raw)
    quote = 'People say "the machines will decide for us"'
    assert quote not in raw  # the raw source spells it with curly quotes

    found, score, span = locate_quote(quote, text, RULES.fuzzy_threshold)
    assert (found, score) == (True, 1.0)
    assert span is not None
    assert text[span[0] : span[1]] == quote
    # The same offsets sliced from the raw source would be wrong, which is the whole
    # reason gaf.textnorm exists.
    assert raw[span[0] : span[1]] != quote


def test_locate_quote_finds_a_near_match_above_threshold() -> None:
    typo = "the nearest speciallist stops being four hours away"
    found, score, span = locate_quote(typo, _R203_TEXT, RULES.fuzzy_threshold)
    assert found is True
    assert RULES.fuzzy_threshold <= score < 1.0
    assert span is not None
    assert _R203_TEXT[span[0] : span[1]].startswith("the nearest specialist stops")


def test_locate_quote_is_indifferent_to_whitespace_because_the_text_is_normalised() -> None:
    spaced = "the  nearest specialist stops being\nfour   hours away"
    found, score, span = locate_quote(spaced, _R203_TEXT, RULES.fuzzy_threshold)
    assert (found, score) == (True, 1.0)
    assert span is not None
    assert _R203_TEXT[span[0] : span[1]] == _R203_QUOTE


def test_locate_quote_rejects_a_fabricated_quote() -> None:
    found, score, span = locate_quote(FABRICATED_QUOTE, _R203_TEXT, RULES.fuzzy_threshold)
    assert found is False
    assert span is None
    assert score < RULES.fuzzy_threshold
    # The best score is still reported, so a fabrication is legible in the audit log.
    assert score > 0.0


def test_locate_quote_rejects_a_quote_belonging_to_another_response() -> None:
    other = "the whole line runs without a shift supervisor"  # response 239, not 203
    found, _, span = locate_quote(other, _R203_TEXT, RULES.fuzzy_threshold)
    assert (found, span) == (False, None)


def test_locate_quote_handles_empty_input() -> None:
    assert locate_quote("", _R203_TEXT, RULES.fuzzy_threshold) == (False, 0.0, None)
    assert locate_quote(_R203_QUOTE, "", RULES.fuzzy_threshold) == (False, 0.0, None)


def test_locate_quote_is_deterministic() -> None:
    runs = [locate_quote(_R203_QUOTE + " x", _R203_TEXT, RULES.fuzzy_threshold) for _ in range(5)]
    assert len(set(runs)) == 1


# --------------------------------------------------------------------------- #
# S1 — schema
# --------------------------------------------------------------------------- #


def test_s1_drops_a_candidate_with_no_evidence() -> None:
    planted = case("S1_no_evidence")
    survivors, report = check_s1(planted.candidates, RULES)
    assert survivors == []
    assert markers(report, "S1") == ["missing_evidence"]
    assert report.errors()[0].severity is Severity.ERROR


def test_s1_drops_a_candidate_with_no_name() -> None:
    planted = case("S1_empty_name")
    survivors, report = check_s1(planted.candidates, RULES)
    assert survivors == []
    assert markers(report, "S1") == ["missing_name"]
    # An unnamed candidate still needs a subject a human can find.
    assert report.findings[0].subject == "<unnamed candidate 0>"


def test_s1_keeps_a_candidate_with_no_description() -> None:
    planted = case("S1_no_description")
    survivors, report = check_s1(planted.candidates, RULES)
    assert len(survivors) == 1
    assert markers(report, "S1") == ["missing_description"]
    assert report.passed() is True


def test_s1_keeps_a_description_that_copies_its_own_quote() -> None:
    planted = case("S1_description_copies_quote")
    survivors, report = check_s1(planted.candidates, RULES)
    assert len(survivors) == 1
    assert markers(report, "S1") == ["description_copies_quote"]
    assert report.warnings()[0].severity is Severity.WARN  # ADR-0013: never an ERROR


def test_s1_is_silent_on_well_formed_candidates() -> None:
    planted = case("clean")
    survivors, report = check_s1(planted.candidates, RULES)
    assert len(survivors) == len(planted.candidates)
    assert list(report) == []


# --------------------------------------------------------------------------- #
# S2 / S2b — provenance and quote length
# --------------------------------------------------------------------------- #


def test_s2_drops_the_fabricated_quote_and_keeps_the_candidate() -> None:
    planted = case("S2_fabricated_quote")
    survivors, report = check_s2(planted.candidates, CORPUS[planted.response_id], RULES)
    assert len(survivors) == 1
    assert [e.quote for e in survivors[0].evidence] == [word_windows(203, 1)[0]]
    assert markers(report, "S2") == ["quote_unverified"]
    assert report.findings[0].severity is Severity.INFO
    assert report.findings[0].data["quote"] == FABRICATED_QUOTE


def test_s2_drops_a_candidate_with_nothing_verifiable_left() -> None:
    planted = case("S2_all_quotes_fabricated")
    survivors, report = check_s2(planted.candidates, CORPUS[planted.response_id], RULES)
    assert survivors == []
    assert markers(report, "S2") == ["quote_unverified", "no_verified_evidence"]
    assert report.errors()[0].data[MARKER_KEY] == "no_verified_evidence"


def test_s2_attaches_verification_score_and_span_to_surviving_evidence() -> None:
    planted = case("clean")
    response = CORPUS[planted.response_id]
    text = normalise(response.content)
    survivors, report = check_s2(planted.candidates, response, RULES)
    assert list(report) == []
    for survivor in survivors:
        for evidence in survivor.evidence:
            assert evidence.verified is True
            assert evidence.score == 1.0
            assert evidence.span is not None
            assert text[evidence.span[0] : evidence.span[1]] == evidence.quote


def test_s2b_warns_on_a_quote_spanning_three_sentences() -> None:
    """LEFT FAILING DELIBERATELY — it has caught a contract violation in `gaf`.

    `gaf.checks.structural` documents, on `_EXCERPT_CHARS`, that the 120-character
    excerpt is "used in a subject or a message; full text always goes into ``data``".
    S4 honours that (its subject is `_excerpt(segment_text)` while
    ``data["segment_text"]`` is the full span), but `check_s1`, `check_s2`,
    `check_s2b` and `check_s4` all store `_excerpt(...)` under ``data["quote"]`` /
    ``data["quotes"]`` — so a flagged quote longer than 120 characters cannot be
    recovered from the audit log at all, which is exactly what the module's stated
    "transparency" principle promises.

    `S2B_THREE_SENTENCES` is 123 characters, so it is the first fixture that crosses
    the limit and makes the violation observable; every planted quote before the
    ADR-0024 rewrite was shorter, which is why this went unnoticed.

    The assertion below states the documented contract and is left as it is. Repairing
    it by asserting `_excerpt(S2B_THREE_SENTENCES)` would pin the bug rather than the
    behaviour, and the fix belongs in `gaf/`, which this task may not touch.
    """
    planted = case("S2b_long_quote")
    survivors, _ = check_s2(planted.candidates, CORPUS[planted.response_id], RULES)
    report = check_s2b(survivors, RULES)
    assert markers(report, "S2b") == ["quote_too_long"]
    finding = report.findings[0]
    assert finding.severity is Severity.WARN
    assert finding.data["sentences"] == 3
    assert finding.data["quote"] == S2B_THREE_SENTENCES


def test_s2b_is_silent_on_phrase_level_quotes() -> None:
    planted = case("clean")
    survivors, _ = check_s2(planted.candidates, CORPUS[planted.response_id], RULES)
    assert list(check_s2b(survivors, RULES)) == []


def test_s2b_word_bound_binds_on_a_response_with_no_sentence_terminator() -> None:
    """ADR-0015: three of the twenty real responses contain no `.`, `?` or `!` at all.

    A quote of such a response in full counts as one sentence, so the terminator count
    alone cannot enforce phrase-level coding on it. The word bound is what binds.
    """
    content = " ".join(f"word{i:02d}" for i in range(60))
    response = Response(id=901, question="q", content=content, source="test")
    candidate = cand("future-ubiquity", "Everything, at length.", [content], 901)

    survivors, s2_report = check_s2([candidate], response, RULES)
    assert list(s2_report) == []
    report = check_s2b(survivors, RULES)

    assert markers(report, "S2b") == ["quote_too_long_words"]
    finding = report.findings[0]
    assert finding.severity is Severity.WARN
    assert finding.data["words"] == 60
    assert finding.data["sentences"] == 1  # no terminator anywhere in the response
    assert finding.data["max_quote_words"] == RULES.max_quote_words


def test_s2b_word_bound_is_exclusive_at_the_configured_maximum() -> None:
    """Response 234 is exactly 40 words, which is the bound and therefore not over it.

    Its three sentences still trip the sentence bound, so the word bound staying
    silent at exactly `max_quote_words` is what this asserts: 40 is not *more than* 40.
    """
    response = CORPUS[234]
    whole = normalise(response.content)
    assert len(whole.split(" ")) == RULES.max_quote_words
    survivors, _ = check_s2([cand("future-ubiquity", "All of it.", [whole], 234)], response, RULES)
    assert markers(check_s2b(survivors, RULES), "S2b") == ["quote_too_long"]


def test_s2b_can_fire_on_both_bounds_at_once() -> None:
    response = CORPUS[207]
    whole = normalise(response.content)  # 51 words, three sentences
    survivors, _ = check_s2([cand("future-ubiquity", "All of it.", [whole], 207)], response, RULES)
    assert markers(check_s2b(survivors, RULES), "S2b") == [
        "quote_too_long",
        "quote_too_long_words",
    ]


# --------------------------------------------------------------------------- #
# S3 — name grammar and hierarchy discipline
# --------------------------------------------------------------------------- #


def test_s3_warns_on_a_prose_code_name() -> None:
    planted = case("S3_bad_grammar")
    report = check_s3(planted.candidates, planted.existing_names, RULES)
    assert markers(report, "S3") == ["name_grammar"]
    finding = report.findings[0]
    assert finding.severity is Severity.WARN  # never an ERROR: the PI's names vary
    assert finding.data["reasons"] == ["whitespace", "part_pattern"]


def test_s3_is_silent_on_the_names_the_pi_actually_uses() -> None:
    """The regression guard: a capitalised family and a hyphen inside a sub-code pass."""
    planted = case("S3_good_names")
    report = check_s3(planted.candidates, planted.existing_names, RULES)
    assert list(report) == []
    _, gate_report = run_case(planted)
    assert gate_report.by_check("S3") == []
    assert {c.name for c in planted.candidates} >= {
        "AI-superintelligence",
        "positive_impacts-problem-solving",
    }


def test_s3_flags_a_top_level_code_where_a_sub_code_would_do() -> None:
    planted = case("S3_subcode_first")
    report = check_s3(planted.candidates, planted.existing_names, RULES)
    assert markers(report, "S3") == ["sub_code_first"]
    finding = report.findings[0]
    assert finding.severity is Severity.WARN
    assert finding.data["family"] == "negative_impacts"
    assert finding.data["existing"] == ["negative_impacts-job_destruction"]


def test_s3_does_not_flag_a_top_level_code_in_an_unknown_family() -> None:
    candidates = [cand("brand_new_family", "Nothing like it yet.", word_windows(203, 1), 3)]
    report = check_s3(candidates, ["negative_impacts-job_destruction"], RULES)
    assert list(report) == []


def test_s3_grammar_can_be_switched_off_by_the_rules() -> None:
    planted = case("S3_bad_grammar")
    relaxed = CodingRules(check_name_grammar=False)
    assert list(check_s3(planted.candidates, planted.existing_names, relaxed)) == []


# --------------------------------------------------------------------------- #
# S4 — segment discipline
# --------------------------------------------------------------------------- #


def test_s4_errors_on_three_codes_for_one_segment_and_keeps_all_three() -> None:
    planted = case("S4_three_codes_one_segment")
    survivors, report = run_case(planted)

    assert len(survivors) == 3, "keep-and-flag: the structural layer drops nothing here"
    assert {c.name for c in survivors} == {c.name for c in planted.candidates}

    findings = report.by_check("S4")
    assert len(findings) == 1
    finding = findings[0]
    assert finding.severity is Severity.ERROR
    assert finding.scope == "segment"
    assert finding.data[MARKER_KEY] == "too_many_codes_on_segment"
    assert finding.data["codes"] == [
        "adoption-workplace",
        "applications-assistant",
        "future-ubiquity",
    ]
    assert finding.data["segment_text"] == S4_SHARED_SENTENCE
    assert all(name in finding.message for name in finding.data["codes"])
    assert report.passed() is False  # this is what drives the CLI exit code


def test_s4_is_silent_at_the_stated_maximum_of_two() -> None:
    planted = case("S4_two_codes_one_segment")
    survivors, report = run_case(planted)
    assert len(survivors) == 2
    assert list(report) == []


def test_s4_does_not_fire_on_non_overlapping_quotes() -> None:
    planted = case("S5_too_many")
    _, report = run_case(planted)
    assert report.by_check("S4") == []
    assert markers(report, "S5") == ["too_many_codes"]


def _overlap_candidates(first: tuple[int, int], second: tuple[int, int]) -> list[Candidate]:
    """Two candidates on word window `first`, one on `second`, all in response 203."""
    words = normalise(CORPUS[203].content).split(" ")
    shared = " ".join(words[first[0] : first[1]])
    shifted = " ".join(words[second[0] : second[1]])
    return [
        cand("future-one", "One.", [shared], 203),
        cand("future-two", "Two.", [shared], 203),
        cand("future-three", "Three.", [shifted], 203),
    ]


def test_s4_clusters_quotes_that_overlap_above_the_threshold() -> None:
    """Windows 0-8 and 2-10 share 38 of 69 characters: Jaccard 0.551, one segment.

    Hand-derived from response 203's normalised word spans, which run
    ``Rural``=[0,5), ``clinics``=[6,13), ``get``=[14,17) ... ``nearest``=[45,52),
    ``specialist``=[53,63), ``stops``=[64,69):

    * words 0-8 span characters [0, 52)  -> length 52
    * words 2-10 span characters [14, 69) -> length 55
    * intersection = min(52, 69) - max(0, 14) = 38
    * union = 52 + 55 - 38 = 69
    * Jaccard = 38 / 69 = 0.551 >= segment_overlap_threshold (0.5), so one segment
      whose union span is [0, 69).
    """
    response = CORPUS[203]
    survivors, _ = check_s2(_overlap_candidates((0, 8), (2, 10)), response, RULES)
    report = check_s4(survivors, response, RULES)
    assert markers(report, "S4") == ["too_many_codes_on_segment"]
    finding = report.findings[0]
    assert finding.data["span"] == [0, 69]  # the union of the clustered spans
    assert finding.data["segment_text"] == normalise(response.content)[0:69]


def test_s4_leaves_quotes_that_overlap_below_the_threshold_apart() -> None:
    """Windows 0-4 and 3-12 share 10 of 80 characters: Jaccard 0.125, two segments.

    Same spans as above: words 0-4 cover [0, 28) (length 28) and words 3-12 cover
    [18, 80) (length 62). Intersection = 28 - 18 = 10, union = 28 + 62 - 10 = 80,
    Jaccard = 10 / 80 = 0.125, below the 0.5 threshold.
    """
    response = CORPUS[203]
    survivors, _ = check_s2(_overlap_candidates((0, 4), (3, 12)), response, RULES)
    assert list(check_s4(survivors, response, RULES)) == []


def test_s4_ignores_a_candidate_whose_evidence_never_verified() -> None:
    response = CORPUS[217]
    candidates = [
        cand("adoption-workplace", "Offices.", [S4_SHARED_SENTENCE], 217),
        cand("applications-assistant", "Assistants.", [S4_SHARED_SENTENCE], 217),
        cand("future-ubiquity", "Everywhere.", [FABRICATED_QUOTE], 217),
    ]
    survivors, _ = check_s2(candidates, response, RULES)
    assert list(check_s4(survivors, response, RULES)) == []


# --------------------------------------------------------------------------- #
# S5 — response-level counts
# --------------------------------------------------------------------------- #


def test_s5_warns_when_a_response_carries_too_few_codes() -> None:
    planted = case("S5_too_few")
    _, report = run_case(planted)
    assert markers(report, "S5") == ["too_few_codes"]
    finding = report.by_check("S5")[0]
    assert finding.severity is Severity.WARN  # "usually" — advisory, never a drop
    assert finding.scope == "response"
    assert finding.subject == "203"
    assert finding.data["count"] == 1


def test_s5_warns_when_a_response_carries_too_many_codes() -> None:
    planted = case("S5_too_many")
    survivors, report = run_case(planted)
    assert len(survivors) == 13, "advisory only: nothing is dropped"
    assert markers(report, "S5") == ["too_many_codes"]
    assert report.by_check("S5")[0].data["count"] == 13


def test_s5_is_silent_inside_the_range() -> None:
    planted = case("S5_in_range")
    _, report = run_case(planted)
    assert report.by_check("S5") == []


def test_s5_counts_each_coder_separately() -> None:
    # Response 218 is the corpus's longest at 55 words, so it is the only one that
    # holds thirteen non-overlapping four-word windows (52 words) plus a further
    # window for the second coder.
    response = CORPUS[218]
    candidates = [
        cand(f"future-aspect_{i:02d}", f"Aspect {i}.", [quote], 218, coder="coder_a")
        for i, quote in enumerate(word_windows(218, 13, width=4))
    ]
    candidates.append(
        cand(
            "future-inevitability",
            "Given.",
            word_windows(218, 1, width=3, start=52),
            218,
            coder="coder_b",
        )
    )
    _, report = check_candidates(candidates, response)
    findings = report.by_check("S5")
    assert [(f.data["coder"], f.data[MARKER_KEY]) for f in findings] == [
        ("coder_a", "too_many_codes"),
        ("coder_b", "too_few_codes"),
    ]
    assert report.by_check("S4") == []


def test_s5_reports_a_coder_whose_every_candidate_was_dropped() -> None:
    planted = case("S1_no_evidence")
    survivors, report = run_case(planted)
    assert survivors == []
    finding = report.by_check("S5")[0]
    assert finding.data[MARKER_KEY] == "too_few_codes"
    assert finding.data["count"] == 0


def test_s5_defaults_to_the_coders_still_present() -> None:
    planted = case("clean")
    survivors, _ = check_s2(planted.candidates, CORPUS[203], RULES)
    assert list(check_s5(survivors, CORPUS[203], RULES)) == []


# --------------------------------------------------------------------------- #
# The gate as a whole
# --------------------------------------------------------------------------- #


def test_the_gate_runs_every_check_in_order_on_one_response() -> None:
    """One batch that trips S1, S2, S2b, S3, S4 and S5 at once.

    Response 217 has only two sentences, so quoting it whole cannot trip S2b's
    sentence bound; at 47 words it trips the word bound instead. Both markers are
    S2b findings of the same severity — which of the two fires is a property of the
    response, and each has its own dedicated test above.
    """
    response = CORPUS[217]
    whole = normalise(response.content)
    candidates = [
        cand("future-inevitability", "Given.", [], 217),
        cand("Bad Name", "Prose.", [FABRICATED_QUOTE, S4_SHARED_SENTENCE, whole], 217),
        cand("adoption-workplace", "Offices automate.", [S4_SHARED_SENTENCE], 217),
        cand("applications-assistant", "An assistant.", [S4_SHARED_SENTENCE], 217),
        cand(
            "future-ubiquity",
            "Judgement work remains.",
            ["the engineers will spend their days arguing with the forecast"], 217,
            coder="coder_b",
        ),
    ]
    survivors, report = check_candidates(candidates, response)

    assert [f.check_id for f in report] == ["S1", "S2", "S2b", "S3", "S4", "S5"]
    assert [f.data[MARKER_KEY] for f in report] == [
        "missing_evidence",
        "quote_unverified",
        "quote_too_long_words",
        "name_grammar",
        "too_many_codes_on_segment",
        "too_few_codes",
    ]
    assert [c.name for c in survivors] == [
        "Bad Name",
        "adoption-workplace",
        "applications-assistant",
        "future-ubiquity",
    ]
    assert report.totals() == {"ERROR": 2, "WARN": 3, "INFO": 1}


def test_the_gate_is_silent_on_a_clean_batch() -> None:
    planted = case("clean")
    survivors, report = run_case(planted)
    assert list(report) == []
    assert report.passed() is True
    assert len(survivors) == 4


def test_the_gate_honours_relaxed_rules() -> None:
    planted = case("S5_too_many")
    relaxed = CodingRules(max_codes_per_response=20)
    _, report = check_candidates(planted.candidates, CORPUS[planted.response_id], (), relaxed)
    assert list(report) == []


# --------------------------------------------------------------------------- #
# S6 — codebook invariants
# --------------------------------------------------------------------------- #


def test_s6_is_silent_on_a_well_formed_codebook() -> None:
    report = check_codebook(toy_codebook(), set(response_ids()), RULES)
    assert list(report) == []
    assert report.passed() is True


def test_s6_finds_every_planted_violation_at_the_right_severity() -> None:
    report = check_codebook(broken_codebook(), set(response_ids()), RULES)
    found = {f.data[MARKER_KEY]: (f.severity, f.subject) for f in report}
    assert found == {
        "duplicate_name": (Severity.ERROR, "future-hazard"),
        "orphan_parent": (Severity.ERROR, "adoption-global"),
        "hierarchy_too_deep": (Severity.WARN, "concern-ethics-consent"),
        "evidence_on_parent": (Severity.INFO, "applications"),
        "missing_description": (Severity.WARN, "adoption-workplace"),
        "evidence_response_missing": (Severity.ERROR, "future-unknown"),
    }
    assert len(report) == 6, "one finding per planted violation, no double reporting"
    assert report.totals() == {"ERROR": 3, "WARN": 2, "INFO": 1}


def test_s6_duplicate_names_are_matched_case_insensitively() -> None:
    finding = next(
        f for f in check_codebook(broken_codebook(), rules=RULES) if f.data[MARKER_KEY] == "duplicate_name"
    )
    assert sorted(finding.data["ids"]) == ["c-Dup-2", "c-dup-1"]


def test_s6_names_the_orphan_parent_and_the_missing_response() -> None:
    report = check_codebook(broken_codebook(), set(response_ids()), RULES)
    orphan = next(f for f in report if f.data[MARKER_KEY] == "orphan_parent")
    assert orphan.data["parent_id"] == ORPHAN_PARENT_ID
    missing = next(f for f in report if f.data[MARKER_KEY] == "evidence_response_missing")
    assert missing.data["missing_response_ids"] == [MISSING_RESPONSE_ID]


def test_s6_checks_corpus_references_only_when_a_corpus_is_supplied() -> None:
    report = check_codebook(broken_codebook(), None, RULES)
    assert "evidence_response_missing" not in {f.data[MARKER_KEY] for f in report}
    assert len(report) == 5


def test_s6_warns_on_a_leaf_name_that_fails_the_grammar() -> None:
    codes = [
        Code(id="c-root", name="future", description="The future."),
        Code(id="c-leaf", name="Some Vague Topic", description="Unclear.", parent_id="c-root"),
    ]
    report = check_codebook(Codebook(codes={c.id: c for c in codes}), rules=RULES)
    findings = [f for f in report if f.data[MARKER_KEY] == "name_grammar"]
    assert len(findings) == 1
    assert findings[0].severity is Severity.WARN
    assert findings[0].subject == "Some Vague Topic"


def test_s6_terminates_on_a_parent_cycle() -> None:
    codes = [
        Code(id="c-a", name="alpha-one", description="A.", parent_id="c-b"),
        Code(id="c-b", name="beta-one", description="B.", parent_id="c-a"),
    ]
    report = check_codebook(Codebook(codes={c.id: c for c in codes}), rules=RULES)
    assert markers(report, "S6") == ["parent_cycle", "parent_cycle"]
    assert all(f.severity is Severity.ERROR for f in report)


def test_s6_is_deterministic() -> None:
    corpus = set(response_ids())
    first = check_codebook(broken_codebook(), corpus, RULES)
    second = check_codebook(broken_codebook(), corpus, RULES)
    assert first.to_json() == second.to_json()


def test_s6_does_not_mutate_the_codebook() -> None:
    codebook = broken_codebook()
    before = codebook.to_json_str()
    check_codebook(codebook, set(response_ids()), RULES)
    assert codebook.to_json_str() == before


def test_s6_description_check_follows_the_rules_flag() -> None:
    relaxed = CodingRules(require_description=False)
    report = check_codebook(broken_codebook(), set(response_ids()), relaxed)
    assert "missing_description" not in {f.data[MARKER_KEY] for f in report}


# --------------------------------------------------------------------------- #
# Cross-cutting: the whole suite over the whole synthetic corpus
# --------------------------------------------------------------------------- #


def test_the_gate_is_stable_across_the_whole_corpus() -> None:
    """Every response, coded with two four-word windows, is silent and repeatable."""
    for response in CORPUS.values():
        candidates = [
            cand(f"future-window_{i}", f"Window {i}.", [quote], response.id)
            for i, quote in enumerate(word_windows(response.id, 2, width=4))
        ]
        first_survivors, first = check_candidates(candidates, response)
        _, second = check_candidates(candidates, response)
        assert list(first) == [], f"response {response.id}: {[str(f) for f in first]}"
        assert first.to_json() == second.to_json()
        assert len(first_survivors) == 2


def test_a_fuzzy_match_lands_on_the_best_window_not_the_first_plausible_one() -> None:
    """Response 245 says "the ... you are ..." twice; a fuzzy quote must pick the right one.

    The decoy clause comes first in the text, so a locator that stopped at the first
    plausible window would return it. The assertions below pin the *global* maximum:
    the winning score must equal the similarity of the window actually returned, and
    must beat the decoy's.
    """
    text = normalise(CORPUS[245].content)
    decoy = "the course you are advised to take"
    assert decoy in text
    quote = "the treatment you are offerred"  # the real clause spells it "offered"
    assert text.find(decoy) < text.find("the treatment you are")

    found, score, span = locate_quote(quote, text, RULES.fuzzy_threshold)
    assert found is True
    assert span is not None
    located = text[span[0] : span[1]]
    assert located.startswith("the treatment you are")
    assert score == difflib.SequenceMatcher(None, located, quote).ratio()
    assert score > difflib.SequenceMatcher(None, decoy, quote).ratio()
