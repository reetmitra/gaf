"""Semantic checks M1-M4, codebook health, saturation and threshold calibration.

Everything here runs offline against `tests.fixtures.embedding.StubEmbedder` and an
in-test `FakeJudge`, because A4's layer is written against
`gaf.embed.protocol.Embedder` and the `Judge` protocol rather than against any
implementation of either (ADR-0014).

The four claims this file exists to hold down:

1. **optimality** — cross-coder matching is Hungarian, not greedy, which is the specific
   failure (21 matched pairs against 66 and 73 unmatched) that ADR-0003 replaces;
2. **the dedup gate** — no candidate is ever reported as creatable while a near
   neighbour sits at or above tau_high;
3. **the fast loop invents nothing** — IMPRECISE and INCOMPLETE keep the candidate and
   produce a WARN, a malformed judge reply fails safe to APPLIES, and only UNNECESSARY
   removes anything;
4. **checks report** — no checker mutates its input, nothing is auto-merged, calibration
   does not touch `CodingRules`, and identical input yields byte-identical findings.

A note on threshold calibration after the ADR-0024 corpus rewrite. `StubEmbedder` scores
a code against a segment by shared whole tokens, and the synthetic corpus is written in
deliberately different vocabulary from the code names, so every tau_fit unit now scores
0.0 and the sweep separates nothing. The pre-rewrite fixture produced a non-zero curve
only because the real respondents happened to use the code names' own words — that is,
the "calibration signal" this file used to assert was lexical coincidence in real
survey text, not evidence about code<->evidence fit. The calibration tests below now
assert the honest no-signal outcome (the threshold is kept, and the report says the
golden set barely discriminates it). Consequence worth naming: nothing in the suite
currently exercises `_sweep`'s ``changed=True`` branch.
"""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, asdict, replace
from typing import Any

import numpy as np
import pytest

from gaf.checks.contracts import FIT_VERDICTS, Severity
from gaf.checks.health import (
    DEFAULT_TAU_FIT_GRID,
    calibrate_thresholds,
    checkpoint_signals,
    codebook_health,
    saturation_curve,
    saturation_from_codebooks,
)
from gaf.checks.semantic import (
    BAND_AGREED,
    BAND_GREY,
    MARKER_KEY,
    UNMATCHED,
    assign_optimal,
    check_code_evidence_fit,
    check_cross_coder_agreement,
    check_integration_routing,
    check_near_duplicate_leaves,
    compare_codebooks,
    cosine_matrix,
)
from gaf.config import CheckpointPolicy, CodingRules
from gaf.embed.protocol import Route, code_text
from gaf.models import Candidate, Code, Codebook
from tests.fixtures.assignments import human_assignments, machine_assignments
from tests.fixtures.candidates import CASES, cand, clean_candidates
from tests.fixtures.codebooks import near_duplicate_codebook, toy_codebook
from tests.fixtures.corpus import MOCKFIT_UNNECESSARY, corpus_by_id
from tests.fixtures.embedding import StubEmbedder

RULES = CodingRules()


@pytest.fixture
def embedder() -> StubEmbedder:
    return StubEmbedder()


# --------------------------------------------------------------------------- #
# An in-test judge. Wave 2 owns the real one; this is the protocol, deterministic.
# --------------------------------------------------------------------------- #


class FakeJudge:
    """Deterministic stand-in for `gaf.agents.judge`, satisfying the `Judge` protocol.

    Rules UNNECESSARY on any quote carrying the corpus sentinel, so the M3 removal path
    is exercised offline exactly as `tests/fixtures/corpus.py` documents. `fit_reply`
    overrides the whole reply, which is how the malformed-reply cases are built.
    """

    def __init__(
        self,
        *,
        fit_verdict: str = "APPLIES",
        dispute_verdict: str = "KEEP",
        route_verdict: str = "MERGE",
        fit_reply: Any = None,
    ) -> None:
        self.fit_verdict = fit_verdict
        self.dispute_verdict = dispute_verdict
        self.route_verdict = route_verdict
        self.fit_reply = fit_reply
        self.calls: list[tuple[str, str]] = []

    def rule_on_fit(
        self,
        *,
        candidate_name: str,
        candidate_description: str,
        quote: str,
        response_text: str,
    ) -> dict:
        self.calls.append(("fit", candidate_name))
        if self.fit_reply is not None:
            return self.fit_reply
        verdict = "UNNECESSARY" if MOCKFIT_UNNECESSARY in quote else self.fit_verdict
        return {"verdict": verdict, "reasoning": f"fake judge on {candidate_name}"}

    def rule_on_dispute(
        self, *, candidate_a: dict, candidate_b: dict, response_text: str
    ) -> dict:
        self.calls.append(("dispute", f"{candidate_a['name']}<->{candidate_b['name']}"))
        return {"verdict": self.dispute_verdict, "reasoning": "fake judge on a dispute"}

    def rule_on_route(
        self,
        *,
        candidate_name: str,
        candidate_description: str,
        neighbour_name: str,
        neighbour_description: str,
        score: float,
    ) -> dict:
        self.calls.append(("route", candidate_name))
        return {"route": self.route_verdict, "reasoning": "fake judge on a route"}


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

#: Coder A and coder B on one response: two identical codes, one near-synonym that
#: lands in the grey zone, and one code with nothing on the other side to match.
_A_ENTRIES = [
    ("positive_impacts-healthcare", "AI improves diagnosis and access to medical care."),
    ("negative_impacts-job_destruction", "AI removes existing categories of paid work."),
    ("future-inevitability", "AI is treated as an unavoidable feature of the future."),
    ("concern-ethical_development", "AI must be developed and used responsibly."),
]
_B_ENTRIES = [
    ("positive_impacts-healthcare", "AI improves diagnosis and access to medical care."),
    ("negative_impacts-job_destruction", "AI removes existing categories of paid work."),
    ("future-inevitability", "AI's arrival is unavoidable rather than chosen."),
    ("adoption-workplace", "Every office runs on some kind of automated assistant."),
]


def _coder_set(entries: list[tuple[str, str]], coder: str) -> list[Candidate]:
    return [cand(name, desc, ["a quote"], 203, coder=coder) for name, desc in entries]


def _verified(candidate: Candidate) -> Candidate:
    """S2's ruling, applied by hand: the shared fixtures ship evidence unverified on
    purpose, and M3 only ever looks at verified quotes."""
    return replace(
        candidate,
        evidence=[replace(e, verified=True, score=1.0) for e in candidate.evidence],
    )


def _greedy_pairs(similarity: np.ndarray) -> list[tuple[int, int]]:
    """The matching Hungarian assignment replaces: take the best remaining pair, repeat."""
    order = sorted(
        (
            (float(similarity[i, j]), i, j)
            for i in range(similarity.shape[0])
            for j in range(similarity.shape[1])
        ),
        key=lambda item: (-item[0], item[1], item[2]),
    )
    pairs: list[tuple[int, int]] = []
    used_a: set[int] = set()
    used_b: set[int] = set()
    for _, i, j in order:
        if i in used_a or j in used_b:
            continue
        pairs.append((i, j))
        used_a.add(i)
        used_b.add(j)
    return sorted(pairs)


def _markers(report: Any) -> list[str]:
    return [f.data.get(MARKER_KEY, "") for f in report.findings]


def _code(name: str, description: str = "A code.", parent_id: str | None = None) -> Code:
    return Code(id=f"c-{name}", name=name, description=description, parent_id=parent_id)


def _codebook(*names: str) -> Codebook:
    codes = [_code(n) for n in names]
    return Codebook(codes={c.id: c for c in codes})


# --------------------------------------------------------------------------- #
# M1 — cross-coder agreement
# --------------------------------------------------------------------------- #


def test_m1_agreeing_coders_produce_an_info_per_pair_with_the_band_recorded(embedder):
    coder_a = _coder_set(_A_ENTRIES[:3], "coder_a")
    coder_b = _coder_set(_A_ENTRIES[:3], "coder_b")

    result = check_cross_coder_agreement(coder_a, coder_b, embedder, RULES)

    assert result.agreement_rate == 1.0
    assert len(result.matches) == 3
    assert result.unmatched_a == [] and result.unmatched_b == []
    assert len(result.report.infos()) == 3
    assert result.report.warnings() == []
    for finding in result.report.findings:
        assert finding.check_id == "M1"
        assert finding.severity is Severity.INFO
        assert finding.scope == "pair"
        assert finding.data["band"] == BAND_AGREED
        assert finding.data["score"] == 1.0
        assert finding.data["space_id"] == embedder.space_id
        assert "<->" in finding.subject
    assert result.stats()["n_agreed"] == 3


def test_m1_an_unmatched_candidate_is_a_warn_scoped_to_the_pair(embedder):
    coder_a = _coder_set(_A_ENTRIES[:3], "coder_a")
    coder_b = _coder_set([*_A_ENTRIES[:3], _B_ENTRIES[3]], "coder_b")

    result = check_cross_coder_agreement(coder_a, coder_b, embedder, RULES)

    assert [c.name for c in result.unmatched_b] == ["adoption-workplace"]
    assert result.unmatched_a == []
    assert result.agreement_rate == 0.75  # 3 agreed of the larger set's 4
    unmatched = [f for f in result.report.findings if f.data.get(MARKER_KEY) == "coder_unmatched"]
    assert len(unmatched) == 1
    assert unmatched[0].severity is Severity.WARN
    assert unmatched[0].scope == "pair"
    assert unmatched[0].subject == f"{UNMATCHED}<->adoption-workplace"
    assert unmatched[0].data["side"] == "b"


def test_m1_grey_zone_reaches_the_judge(embedder):
    judge = FakeJudge(dispute_verdict="KEEP")
    result = check_cross_coder_agreement(
        _coder_set(_A_ENTRIES, "coder_a"),
        _coder_set(_B_ENTRIES, "coder_b"),
        embedder,
        RULES,
        judge=judge,
        response_text="a response",
    )

    grey = result.grey()
    assert [m.name_a for m in grey] == ["future-inevitability"]
    assert RULES.tau_low <= grey[0].score < RULES.tau_high
    assert grey[0].verdict == "KEEP"
    assert ("dispute", "future-inevitability<->future-inevitability") in judge.calls
    judged = [f for f in result.report.findings if f.data.get(MARKER_KEY) == "grey_zone_judged"]
    assert len(judged) == 1
    assert judged[0].severity is Severity.WARN
    assert judged[0].data["verdict"] == "KEEP"
    assert judged[0].data["fail_safe"] is False


def test_m1_offline_warns_instead_of_escalating(embedder):
    result = check_cross_coder_agreement(
        _coder_set(_A_ENTRIES, "coder_a"),
        _coder_set(_B_ENTRIES, "coder_b"),
        embedder,
        RULES,
        judge=None,
    )

    offline = [
        f for f in result.report.findings
        if f.data.get(MARKER_KEY) == "grey_zone_unresolved_offline"
    ]
    assert len(offline) == 1
    assert offline[0].severity is Severity.WARN
    assert offline[0].data["band"] == BAND_GREY
    assert "grey_zone_judged" not in _markers(result.report)


def test_m1_a_pair_below_tau_low_is_disputed(embedder):
    result = check_cross_coder_agreement(
        _coder_set(_A_ENTRIES, "coder_a"),
        _coder_set(_B_ENTRIES, "coder_b"),
        embedder,
        RULES,
    )

    disputed = result.disputed()
    assert [(m.name_a, m.name_b) for m in disputed] == [
        ("concern-ethical_development", "adoption-workplace")
    ]
    assert disputed[0].score < RULES.tau_low
    finding = next(f for f in result.report.findings if f.data.get(MARKER_KEY) == "coders_dispute")
    assert finding.severity is Severity.WARN
    assert finding.scope == "pair"
    assert finding.subject == "concern-ethical_development<->adoption-workplace"
    assert result.agreement_rate == 0.5


def test_m1_uses_optimal_assignment_where_greedy_would_pair_wrongly():
    # Greedy takes 0.90 first and is then forced onto 0.10 (total 1.00);
    # the optimal assignment takes 0.80 + 0.85 (total 1.65).
    similarity = np.array([[0.90, 0.80], [0.85, 0.10]])

    optimal = assign_optimal(similarity)
    greedy = _greedy_pairs(similarity)

    assert optimal == [(0, 1), (1, 0)]
    assert greedy == [(0, 0), (1, 1)]
    assert optimal != greedy
    assert sum(similarity[i, j] for i, j in optimal) > sum(similarity[i, j] for i, j in greedy)


def test_m1_assignment_is_one_to_one_where_greedy_would_double_assign(embedder):
    coder_a = _coder_set(
        [
            ("positive_impacts-healthcare", "AI improves diagnosis and access to medical care."),
            (
                "positive_impacts-healthcare_access",
                "AI improves access to medical care and diagnosis.",
            ),
        ],
        "coder_a",
    )
    coder_b = _coder_set(
        [
            ("positive_impacts-healthcare", "AI improves diagnosis and access to medical care."),
            ("negative_impacts-job_destruction", "AI removes existing categories of paid work."),
        ],
        "coder_b",
    )
    texts_a = [code_text(c.name, c.description) for c in coder_a]
    texts_b = [code_text(c.name, c.description) for c in coder_b]
    similarity = cosine_matrix(embedder.embed(texts_a), embedder.embed(texts_b))
    assert list(similarity.argmax(axis=1)) == [0, 0]  # row-wise greedy double-assigns B[0]

    result = check_cross_coder_agreement(coder_a, coder_b, embedder, RULES)

    assigned_b = [m.index_b for m in result.matches]
    assert sorted(assigned_b) == [0, 1]
    assert len(set(assigned_b)) == len(assigned_b)


# --------------------------------------------------------------------------- #
# M2 — integration routing
# --------------------------------------------------------------------------- #


def test_m2_routes_merge_create_and_judge(embedder):
    judge = FakeJudge(route_verdict="MERGE")
    result = check_integration_routing(
        clean_candidates(203), toy_codebook(), embedder, RULES, judge=judge
    )

    routes = {d.candidate_name: d.route for d in result.decisions}
    assert routes["positive_impacts-healthcare"] is Route.MERGE
    assert routes["positive_impacts-agriculture"] is Route.CREATE
    assert routes["future-inevitability"] is Route.JUDGE

    merge = next(f for f in result.report.findings if f.data.get(MARKER_KEY) == "route_merge")
    assert merge.severity is Severity.INFO
    assert merge.data["best_name"] == "positive_impacts-healthcare"
    assert merge.data["best_score"] >= RULES.tau_high

    create = next(f for f in result.report.findings if f.data.get(MARKER_KEY) == "route_create")
    assert create.severity is Severity.INFO
    assert create.data["best_score"] < RULES.tau_low

    judged = next(f for f in result.report.findings if f.data.get(MARKER_KEY) == "route_judge")
    assert judged.severity is Severity.WARN
    assert judged.data["verdict"] == "MERGE"
    assert ("route", "future-inevitability") in judge.calls


def test_m2_dedup_gate_never_reports_create_beside_a_near_neighbour(embedder):
    candidates = [
        *clean_candidates(203),
        cand(
            "positive_impacts-healthcare_v2",
            "AI improves diagnosis and access to medical care.",
            ["a quote"], 203,
        ),
    ]
    result = check_integration_routing(candidates, toy_codebook(), embedder, RULES)

    for decision in result.decisions:
        if decision.best_score >= RULES.tau_high:
            assert decision.route is Route.MERGE, decision.candidate_name
        if decision.route is Route.CREATE:
            assert decision.best_score < RULES.tau_low, decision.candidate_name
    created = result.by_route()["CREATE"]
    assert "positive_impacts-healthcare" not in created
    assert "positive_impacts-healthcare_v2" not in created
    assert "positive_impacts-agriculture" in created


def test_m2_grey_zone_offline_warns(embedder):
    result = check_integration_routing(clean_candidates(203), toy_codebook(), embedder, RULES)

    offline = [
        f for f in result.report.findings
        if f.data.get(MARKER_KEY) == "route_judge_unresolved_offline"
    ]
    assert len(offline) == 1
    assert offline[0].severity is Severity.WARN
    assert offline[0].subject == "future-inevitability"


def test_m2_empty_codebook_creates_everything(embedder):
    result = check_integration_routing(clean_candidates(203), Codebook(), embedder, RULES)

    assert {d.route for d in result.decisions} == {Route.CREATE}
    assert all(d.best is None for d in result.decisions)


# --------------------------------------------------------------------------- #
# M3 — code <-> evidence fit
# --------------------------------------------------------------------------- #


def test_m3_unnecessary_removes_the_quote_and_drops_the_now_unsupported_candidate(embedder):
    candidates = [_verified(c) for c in CASES["M3_unnecessary"].candidates]
    judge = FakeJudge()

    result = check_code_evidence_fit(candidates, corpus_by_id(), embedder, RULES, judge=judge)

    assert result.candidates == []
    assert result.dropped == ["positive_impacts-healthcare"]
    assert [r.verdict for r in result.rulings] == ["UNNECESSARY"]
    assert [r.quote for r in result.removed_quotes] == [MOCKFIT_UNNECESSARY]

    removal = next(
        f for f in result.report.findings if f.data.get(MARKER_KEY) == "quote_removed_unnecessary"
    )
    assert removal.severity is Severity.WARN
    dropped = next(
        f
        for f in result.report.findings
        if f.data.get(MARKER_KEY) == "candidate_dropped_no_evidence"
    )
    assert dropped.severity is Severity.ERROR
    assert dropped.scope == "candidate"
    assert dropped.data["removed_quotes"] == [MOCKFIT_UNNECESSARY]
    assert result.report.passed() is False


def test_m3_a_supported_quote_is_kept_with_an_info(embedder):
    candidates = [_verified(c) for c in CASES["M3_applies"].candidates]

    result = check_code_evidence_fit(
        candidates, corpus_by_id(), embedder, RULES, judge=FakeJudge()
    )

    assert [c.name for c in result.candidates] == ["positive_impacts-healthcare"]
    assert result.dropped == []
    fit_ok = [f for f in result.report.findings if f.data.get(MARKER_KEY) == "fit_ok"]
    assert len(fit_ok) == 1
    assert fit_ok[0].severity is Severity.INFO
    assert fit_ok[0].data["verdict"] == "APPLIES"
    assert result.report.errors() == []


@pytest.mark.parametrize("verdict", ["IMPRECISE", "INCOMPLETE"])
def test_m3_imprecise_and_incomplete_keep_the_candidate_and_invent_nothing(embedder, verdict):
    candidates = [_verified(c) for c in CASES["M3_applies"].candidates]
    before = [c.name for c in candidates]

    result = check_code_evidence_fit(
        candidates, corpus_by_id(), embedder, RULES, judge=FakeJudge(fit_verdict=verdict)
    )

    # membership unchanged: the fast loop never proposes a replacement code
    assert [c.name for c in result.candidates] == before
    assert result.candidates[0].evidence == candidates[0].evidence
    assert result.dropped == []
    finding = next(f for f in result.report.findings if f.data["verdict"] == verdict)
    assert finding.severity is Severity.WARN
    assert finding.data[MARKER_KEY] == f"fit_{verdict.lower()}"
    assert "no replacement code invented" in finding.message


@pytest.mark.parametrize(
    "reply",
    [
        {"verdict": "BANANA", "reasoning": "nonsense"},
        {"reasoning": "no verdict at all"},
        {},
        "not even a JSON object",
        ["a", "list"],
    ],
)
def test_m3_fails_safe_to_applies_on_a_malformed_judge_reply(embedder, reply):
    candidates = [_verified(c) for c in CASES["M3_unnecessary"].candidates]

    result = check_code_evidence_fit(
        candidates, corpus_by_id(), embedder, RULES, judge=FakeJudge(fit_reply=reply)
    )

    assert [r.verdict for r in result.rulings] == ["APPLIES"]
    assert result.rulings[0].fail_safe is True
    assert result.removed_quotes == []
    assert result.dropped == []
    assert [c.name for c in result.candidates] == ["positive_impacts-healthcare"]
    assert result.candidates[0].evidence == candidates[0].evidence
    assert result.report.errors() == []


def test_m3_offline_warns_instead_of_escalating(embedder):
    candidates = [_verified(c) for c in CASES["M3_unnecessary"].candidates]

    result = check_code_evidence_fit(candidates, corpus_by_id(), embedder, RULES, judge=None)

    assert _markers(result.report) == ["fit_unresolved_offline"]
    assert result.report.findings[0].severity is Severity.WARN
    assert result.candidates == candidates  # nothing removed for want of a judge
    assert result.dropped == []


def test_m3_returns_new_objects_and_leaves_its_input_alone(embedder):
    keep = _verified(CASES["M3_applies"].candidates[0])
    drop = _verified(CASES["M3_unnecessary"].candidates[0])
    both = replace(keep, evidence=list(keep.evidence) + list(drop.evidence))
    before = json.dumps(both.to_json(), sort_keys=True)

    result = check_code_evidence_fit([both], corpus_by_id(), embedder, RULES, judge=FakeJudge())

    assert json.dumps(both.to_json(), sort_keys=True) == before
    revised = result.candidates[0]
    assert revised is not both
    assert len(revised.evidence) == 1
    assert MOCKFIT_UNNECESSARY not in revised.evidence[0].quote
    assert len(both.evidence) == 2


def test_m3_ignores_unverified_evidence(embedder):
    candidates = CASES["M3_unnecessary"].candidates  # fixtures ship unverified evidence

    result = check_code_evidence_fit(
        candidates, corpus_by_id(), embedder, RULES, judge=FakeJudge()
    )

    assert result.candidates == list(candidates)
    assert result.rulings == []
    assert len(result.report) == 0


def test_m3_verdicts_stay_inside_the_frozen_whitelist(embedder):
    candidates = [_verified(c) for c in CASES["M3_applies"].candidates]

    for verdict in FIT_VERDICTS:
        result = check_code_evidence_fit(
            candidates, corpus_by_id(), embedder, RULES, judge=FakeJudge(fit_verdict=verdict)
        )
        assert [r.verdict for r in result.rulings] == [verdict]


# --------------------------------------------------------------------------- #
# M4 — codebook semantic health
# --------------------------------------------------------------------------- #


def test_m4_near_duplicate_leaves_warn_once_and_the_controls_stay_silent(embedder):
    codebook = near_duplicate_codebook()

    result = check_near_duplicate_leaves(codebook, embedder, RULES)

    assert result.compared == 3  # three leaf pairs inside one family
    assert len(result.pairs) == 1
    pair = result.pairs[0]
    assert {pair.a_name, pair.b_name} == {
        "negative_impacts-job_destruction",
        "negative_impacts-job_loss",
    }
    assert pair.score >= RULES.tau_high
    assert pair.family == "negative_impacts"
    assert len(result.report.findings) == 1
    finding = result.report.findings[0]
    assert finding.check_id == "M4"
    assert finding.severity is Severity.WARN
    assert finding.scope == "pair"
    assert finding.data[MARKER_KEY] == "near_duplicate_leaves"
    assert "nothing is merged" in finding.message


def test_m4_merges_nothing(embedder):
    codebook = near_duplicate_codebook()
    before = codebook.to_json_str()

    check_near_duplicate_leaves(codebook, embedder, RULES)

    assert codebook.to_json_str() == before
    assert len(codebook) == 4
    assert "negative_impacts-job_loss" in codebook.names()


def test_m4_a_clean_codebook_is_silent(embedder):
    result = check_near_duplicate_leaves(toy_codebook(), embedder, RULES)

    assert result.pairs == []
    assert len(result.report) == 0


def test_m4_compares_two_codebooks_and_names_what_only_one_holds(embedder):
    result = compare_codebooks(
        toy_codebook(), near_duplicate_codebook(), embedder, RULES, label_a="human", label_b="machine"
    )

    assert result.label_a == "human" and result.label_b == "machine"
    agreed = [m for m in result.matches if m.band == BAND_AGREED]
    assert ("negative_impacts", "negative_impacts") in [(m.name_a, m.name_b) for m in agreed]
    assert "positive_impacts-healthcare" in result.only_in_a
    assert result.only_in_b == []
    assert 0.0 <= result.agreement_rate <= 1.0
    only = [f for f in result.report.findings if f.data.get(MARKER_KEY) == "codebook_only_in_one"]
    assert only and all(f.severity is Severity.WARN for f in only)
    assert all(f.check_id == "M4" for f in result.report.findings)


# --------------------------------------------------------------------------- #
# Codebook health, saturation, checkpoint signals
# --------------------------------------------------------------------------- #


def test_codebook_health_metrics(embedder):
    metrics = codebook_health(toy_codebook(), embedder, RULES)

    assert metrics.n_codes == 8
    assert metrics.n_families == 3
    assert metrics.n_leaves == 5
    assert metrics.n_parents == 3
    assert metrics.n_orphans == 0
    assert metrics.orphan_ratio == 0.0
    assert metrics.family_balance == {"future": 2, "negative_impacts": 3, "positive_impacts": 3}
    assert metrics.near_duplicate_pairs == 0
    assert metrics.evidence_per_code.total == 7
    assert metrics.evidence_per_code.zero_evidence_codes == 3
    assert metrics.space_id == embedder.space_id
    assert json.loads(json.dumps(metrics.to_json()))["n_codes"] == 8


def test_codebook_health_counts_near_duplicates_and_growth(embedder):
    previous = near_duplicate_codebook()

    metrics = codebook_health(toy_codebook(), embedder, RULES, previous=previous)

    assert metrics.new_codes == 6  # 8 codes, 2 of which the previous snapshot already held
    assert metrics.previous_n_codes == 4
    assert metrics.growth_rate == 1.5
    assert codebook_health(previous, embedder, RULES).near_duplicate_pairs == 1


def test_saturation_counts_and_growth_rate_on_a_sequence_of_codebooks():
    first = _codebook("a-one", "a-two", "b-one")
    second = _codebook("a-one", "a-two", "b-one", "b-two", "c-one")
    third = _codebook("a-one", "a-two", "b-one", "b-two", "c-one")

    table = saturation_from_codebooks([first, second, third])

    assert [p.new_codes for p in table.points] == [3, 2, 0]
    assert [p.cumulative_unique for p in table.points] == [3, 5, 5]
    assert [p.growth_rate for p in table.points] == [1.0, 0.4, 0.0]
    assert [p.new_codes_delta for p in table.points] == [3, -1, -2]
    assert table.total_unique == 5
    assert table.points[1].new_names == ["b-two", "c-one"]
    assert len(table.rows()) == 3 and len(table.headers) == len(table.rows()[0])
    assert json.loads(json.dumps(table.to_json()))["total_unique"] == 5


def test_saturation_curve_handles_repeated_and_empty_batches():
    table = saturation_curve([["x"], [], ["x", "y"]])

    assert [p.new_codes for p in table.points] == [1, 0, 1]
    assert [p.codes_seen for p in table.points] == [1, 0, 2]
    assert table.total_unique == 2


def test_checkpoint_signals_report_the_policy_triggers(embedder):
    metrics = codebook_health(near_duplicate_codebook(), embedder, RULES)
    policy = CheckpointPolicy(max_near_duplicate_pairs=0, min_responses_between_checkpoints=10)

    fired = checkpoint_signals(metrics, policy, responses_coded=12, responses_since_checkpoint=10)
    held = checkpoint_signals(metrics, policy, responses_coded=12, responses_since_checkpoint=2)
    quiet = checkpoint_signals(
        codebook_health(toy_codebook(), embedder, RULES),
        CheckpointPolicy(),
        responses_coded=12,
        responses_since_checkpoint=12,
    )

    assert fired.near_duplicates_exceeded is True
    assert fired.recommend_checkpoint is True
    assert any("near-duplicate pairs" in reason for reason in fired.reasons)
    assert held.recommend_checkpoint is False
    assert any("held" in reason for reason in held.reasons)
    assert quiet.recommend_checkpoint is False
    assert json.loads(json.dumps(fired.to_json()))["recommend_checkpoint"] is True


def test_checkpoint_hard_floor_fires_on_its_own(embedder):
    metrics = codebook_health(toy_codebook(), embedder, RULES)

    signals = checkpoint_signals(
        metrics, CheckpointPolicy(hard_floor_responses=50), responses_coded=50,
        responses_since_checkpoint=0,
    )

    assert signals.hard_floor_reached is True
    assert signals.recommend_checkpoint is True


# --------------------------------------------------------------------------- #
# Threshold calibration (brief §11)
# --------------------------------------------------------------------------- #


def test_calibration_returns_a_full_curve_and_a_recommendation(embedder):
    """The tau_fit sweep, hand-derived against the 200-range assignment fixture.

    `StubEmbedder` is a hashed bag-of-words over ``[a-z0-9]+`` tokens, so the cosine
    between a code and a segment is zero unless they share a whole token. Under the
    synthetic corpus no machine assignment does — for example
    `positive_impacts-healthcare` tokenises to {positive, impacts, healthcare} and its
    segment "Rural clinics get diagnostic support" to {rural, clinics, get, diagnostic,
    support} — so **all eight fit scores are exactly 0.0**. (The pre-rewrite fixture
    scored non-zero only because the real respondents happened to use the code names'
    own words; that lexical coincidence, not code<->evidence fit, is what used to move
    this threshold. See the note in this module's docstring.)

    The sweep predicts "escalate to the judge" when ``fit < threshold``, so with every
    score at 0.0 the curve has exactly two shapes:

        threshold 0.00        nothing is below 0.0 -> tp 0, fp 0, fn 2, tn 6
                              precision 0.0, recall 0/2 = 0.0, F1 0.0
        thresholds 0.05..1.00 everything is below  -> tp 2, fp 6, fn 0, tn 0
                              precision 2/8 = 0.25, recall 2/2 = 1.0
                              F1 = 2(0.25)(1.0)/1.25 = 0.4

    So best_f1 = 0.4 and it is attained at all twenty grid values from 0.05 to 1.00 —
    plateau (0.05, 1.0). The provisional 0.30 is inside that plateau, so it is kept:
    `recommended` is 0.30 and `changed` is False. A golden set that separates nothing
    must not move a threshold, and that is what this now asserts.
    """
    report = calibrate_thresholds(human_assignments(), machine_assignments(), embedder, RULES)

    assert sorted(report.sweeps) == ["tau_fit", "tau_high", "tau_low"]
    fit = report.sweeps["tau_fit"]
    assert len(fit.curve) == len(DEFAULT_TAU_FIT_GRID)
    assert [p.threshold for p in fit.curve] == [round(v, 6) for v in DEFAULT_TAU_FIT_GRID]
    assert all(0.0 <= p.precision <= 1.0 and 0.0 <= p.recall <= 1.0 for p in fit.curve)
    assert fit.n_positive == 2  # the two over-coded machine rows
    assert fit.current == RULES.tau_fit
    assert [p.f1 for p in fit.curve] == [0.0] + [0.4] * 20
    assert fit.best_f1 == max(p.f1 for p in fit.curve) == fit.f1_at_current == 0.4
    assert fit.plateau == (0.05, 1.0)
    assert fit.recommended == RULES.tau_fit
    assert fit.changed is False
    # the routing thresholds are not discriminated by this golden set either, so they stand
    assert report.sweeps["tau_high"].recommended == RULES.tau_high
    assert report.sweeps["tau_high"].changed is False
    assert report.sweeps["tau_low"].recommended == RULES.tau_low
    assert report.sweeps["tau_low"].changed is False
    assert report.recommended["tau_low"] <= report.recommended["tau_high"]


def test_calibration_does_not_modify_coding_rules(embedder):
    rules = CodingRules()
    before = asdict(rules)

    report = calibrate_thresholds(human_assignments(), machine_assignments(), embedder, rules)

    assert asdict(rules) == before
    assert asdict(CodingRules()) == before
    assert rules.tau_fit == 0.30
    # This golden set does not discriminate tau_fit (see the sweep test's derivation),
    # so the recommendation is to keep the provisional value. What makes it a
    # recommendation rather than an edit is the two assertions above and the one below:
    # the report is a separate artefact, and `CodingRules` cannot be written to at all.
    assert report.recommended["tau_fit"] == rules.tau_fit
    with pytest.raises(FrozenInstanceError):
        rules.tau_fit = report.recommended["tau_fit"]  # frozen: the edit cannot happen here


def test_calibration_report_is_json_shaped_and_carries_a_paragraph(embedder):
    report = calibrate_thresholds(human_assignments(), machine_assignments(), embedder, RULES)

    payload = json.loads(json.dumps(report.to_json()))
    assert set(payload) == {
        "space_id",
        "generated_from",
        "current",
        "recommended",
        "changed",
        "sweeps",
        "notes",
        "narrative",
    }
    assert payload["space_id"] == embedder.space_id
    assert payload["generated_from"]["n_machine_assignments"] == len(machine_assignments())
    assert payload["sweeps"]["tau_fit"]["curve"][0]["threshold"] == 0.0

    paragraph = report.paragraph()
    assert "tau_fit stays at 0.30" in paragraph
    assert "tau_high stays at 0.80" in paragraph
    assert "CodingRules is not modified" in paragraph
    assert embedder.space_id in paragraph
    assert any("too few to move a threshold" in note for note in report.notes)


# --------------------------------------------------------------------------- #
# Cross-cutting: no mutation, and determinism
# --------------------------------------------------------------------------- #


def test_no_checker_mutates_its_input(embedder):
    coder_a = _coder_set(_A_ENTRIES, "coder_a")
    coder_b = _coder_set(_B_ENTRIES, "coder_b")
    candidates = [_verified(c) for c in CASES["M3_unnecessary"].candidates] + list(
        clean_candidates(203)
    )
    codebook = toy_codebook()
    duplicates = near_duplicate_codebook()
    snapshot = {
        "coder_a": [c.to_json() for c in coder_a],
        "coder_b": [c.to_json() for c in coder_b],
        "candidates": [c.to_json() for c in candidates],
        "codebook": codebook.to_json_str(),
        "duplicates": duplicates.to_json_str(),
    }
    before = json.dumps(snapshot, sort_keys=True)

    judge = FakeJudge()
    check_cross_coder_agreement(coder_a, coder_b, embedder, RULES, judge=judge)
    check_integration_routing(candidates, codebook, embedder, RULES, judge=judge)
    check_code_evidence_fit(candidates, corpus_by_id(), embedder, RULES, judge=judge)
    check_near_duplicate_leaves(duplicates, embedder, RULES)
    compare_codebooks(codebook, duplicates, embedder, RULES)
    codebook_health(codebook, embedder, RULES, previous=duplicates)

    after = json.dumps(
        {
            "coder_a": [c.to_json() for c in coder_a],
            "coder_b": [c.to_json() for c in coder_b],
            "candidates": [c.to_json() for c in candidates],
            "codebook": codebook.to_json_str(),
            "duplicates": duplicates.to_json_str(),
        },
        sort_keys=True,
    )
    assert after == before


def test_identical_input_produces_identical_ordered_findings(embedder):
    def run() -> list[dict]:
        judge = FakeJudge()
        coder_a = _coder_set(_A_ENTRIES, "coder_a")
        coder_b = _coder_set(_B_ENTRIES, "coder_b")
        candidates = [_verified(c) for c in CASES["M3_unnecessary"].candidates] + list(
            clean_candidates(203)
        )
        rows: list[dict] = []
        rows += check_cross_coder_agreement(
            coder_a, coder_b, StubEmbedder(), RULES, judge=judge
        ).report.to_json()
        rows += check_integration_routing(
            candidates, toy_codebook(), StubEmbedder(), RULES, judge=judge
        ).report.to_json()
        rows += check_code_evidence_fit(
            candidates, corpus_by_id(), StubEmbedder(), RULES, judge=judge
        ).report.to_json()
        rows += check_near_duplicate_leaves(
            near_duplicate_codebook(), StubEmbedder(), RULES
        ).report.to_json()
        rows += compare_codebooks(
            toy_codebook(), near_duplicate_codebook(), StubEmbedder(), RULES
        ).report.to_json()
        return rows

    first, second = run(), run()

    assert first == second
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert [row["check_id"] for row in first][:1] == ["M1"]


def test_calibration_is_deterministic(embedder):
    first = calibrate_thresholds(human_assignments(), machine_assignments(), StubEmbedder(), RULES)
    second = calibrate_thresholds(
        human_assignments(), machine_assignments(), StubEmbedder(), RULES
    )

    assert json.dumps(first.to_json(), sort_keys=True) == json.dumps(
        second.to_json(), sort_keys=True
    )
