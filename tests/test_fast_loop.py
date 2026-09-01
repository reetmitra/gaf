"""Wave 2 gate for the fast loop (B2): prep, the router, and the loop that joins them.

Ten claims, and every one of them is a property the rest of the project leans on:

1. **The loop runs offline, end to end**, over the synthetic corpus with mock clients,
   and produces a codebook, assignments, findings and a snapshot sequence.
2. **Determinism.** Two runs produce byte-identical codebook JSON and an identical
   snapshot-id sequence. This is acceptance criterion 3 and it is asserted, not hoped.
3. **Order independence.** Re-running one batch against the snapshot frozen at its start
   reproduces that batch's output exactly, which is what frozen snapshots are *for*.
4. **Both coders receive identical context.** Their two `LLMRequest`s are byte-identical,
   so cross-coder disagreement measures the models rather than the prompt.
5. **A fabricated quote is dropped by S2, and the drop is in the audit log.**
6. **A grey-zone disagreement reaches the judge when one is supplied, and becomes a WARN
   when it is not.** Nothing is dropped on a meaning judgment that could not be made.
7. **The fast loop never splits, re-parents or renames.** Asserted across every snapshot
   the run wrote, and on the router's own integration function.
8. **Every routing decision is recorded** with its score, its route, its action and the
   snapshot it was made against.
9. **`llm_calls` accounting is populated** — every model call is a row with a role.
10. **Segmentation handles the real corpus's shapes**: a response with no sentence
    terminator at all, and one of twenty-eight words.

No key, no network, no provider SDK, no real data: every client is a deterministic mock
and every corpus is `tests.fixtures.corpus`.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import replace
from itertools import pairwise
from typing import Any

import numpy as np
import pytest

from gaf.checks.contracts import Severity
from gaf.checks.semantic import BAND_GREY, check_cross_coder_agreement
from gaf.checks.structural import MARKER_KEY
from gaf.config import QUESTION_V2, CheckpointPolicy, CodingRules, RunConfig
from gaf.embed.protocol import Route, code_text
from gaf.llm.base import CallLog
from gaf.models import Candidate, Code, Codebook, Evidence, Response
from gaf.pipeline import prep, router
from gaf.pipeline.fast_loop import (
    FastLoopResult,
    LoopComponents,
    batches,
    offline_components,
    run_fast_loop,
)
from gaf.store.blackboard import Blackboard
from gaf.store.snapshot import freeze
from gaf.textnorm import normalise
from tests.fixtures.corpus import FABRICATED_QUOTE, SOURCE, synthetic_corpus

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

#: 110 words and not one full stop — the shape three of the twenty real seed responses
#: have (ADR-0015). Invented here; no respondent's words appear in this repository.
NO_TERMINATOR = (
    "these systems are only as good as the records we bothered to keep so a district "
    "that never digitised its registers gets a worse answer than one that did and the "
    "output looks equally confident either way which is the part that worries me "
    "because nobody reading it can tell the difference and the people who built it are "
    "not in the room when it is used on somebody's loan or somebody's job and by the "
    "time anyone notices the pattern the decision has been made a hundred thousand "
    "times over and there is no register of who was turned away or why"
)

#: Twenty-eight words: shorter than the survey's own 100-word minimum, which five of the
#: twenty real responses also are.
VERY_SHORT = (
    "Society will become dependent. If the whole system goes down for a week "
    "nobody will remember how to do the work manually. We should be careful about that."
)


def config_for(run_id: str, **changes: Any) -> RunConfig:
    """An offline run config with the disk cache off, so tests share no state."""
    settings: dict[str, Any] = {"offline": True, "cache_dir": None, "batch_size": 10}
    settings.update(changes)
    return RunConfig(run_id=run_id, **settings)


def run_loop(
    run_id: str,
    responses: Sequence[Response] | None = None,
    *,
    codebook: Codebook | None = None,
    components: LoopComponents | None = None,
    board: Blackboard | None = None,
    **changes: Any,
) -> tuple[FastLoopResult, Blackboard]:
    """Run the loop on an in-memory blackboard and hand back both the result and the store."""
    config = config_for(run_id, **changes)
    store = board or Blackboard()
    result = run_fast_loop(
        list(responses if responses is not None else synthetic_corpus()),
        config=config,
        board=store,
        components=components or offline_components(config),
        codebook=codebook,
    )
    return result, store


class GreyEmbedder:
    """A deterministic embedder that puts every *distinct* pair in the grey zone.

    Identical texts score 1.0; any two different texts score exactly 0.60, which sits
    between tau_low (0.45) and tau_high (0.80). That is the one geometry the offline
    lexical space never produces (ADR-0019: M2's grey zone is empty offline), and it is
    the geometry the escalation path exists for — so the loop's judge branch is
    exercised here rather than left untested until a live run.
    """

    _SHARED = 0.6

    def __init__(self, dim: int = 512, space_id: str = "grey-v1-512") -> None:
        self._dim = dim
        self._space_id = space_id

    @property
    def space_id(self) -> str:
        return self._space_id

    @property
    def dim(self) -> int:
        return self._dim

    def embed_one(self, text: str) -> np.ndarray:
        vector = np.zeros(self._dim, dtype=np.float64)
        vector[0] = self._SHARED**0.5
        digest = hashlib.blake2b(text.encode("utf-8"), digest_size=8).digest()
        vector[1 + int.from_bytes(digest, "big") % (self._dim - 1)] += (1.0 - self._SHARED) ** 0.5
        return vector / float(np.linalg.norm(vector))

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self._dim), dtype=np.float64)
        return np.vstack([self.embed_one(text) for text in texts])


class RecordingJudge:
    """A judge that answers deterministically and remembers every question it was asked."""

    def __init__(self, *, dispute: str = "KEEP", route: str = "MERGE", fit: str = "APPLIES"):
        self.dispute, self.route, self.fit = dispute, route, fit
        self.calls: list[tuple[str, str]] = []

    def rule_on_fit(
        self, *, candidate_name: str, candidate_description: str, quote: str, response_text: str
    ) -> dict:
        self.calls.append(("fit", candidate_name))
        return {"verdict": self.fit, "reasoning": "stub"}

    def rule_on_dispute(
        self, *, candidate_a: dict, candidate_b: dict, response_text: str
    ) -> dict:
        self.calls.append(("dispute", f"{candidate_a['name']}<->{candidate_b['name']}"))
        return {"verdict": self.dispute, "reasoning": "stub"}

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
        return {"route": self.route, "reasoning": "stub"}


def candidate(name: str, quote: str, *, coder: str, span: tuple[int, int] = (0, 4)) -> Candidate:
    """A structurally complete candidate whose single quote is already S2-verified."""
    return Candidate(
        name=name,
        description=f"what {name} means",
        evidence=[Evidence(response_id=1, quote=quote, span=span, verified=True, score=1.0)],
        coder=coder,
    )


# --------------------------------------------------------------------------- #
# 1. The loop runs, end to end
# --------------------------------------------------------------------------- #


def test_offline_run_produces_a_codebook_assignments_findings_and_snapshots() -> None:
    result, board = run_loop("full")
    with board:
        assert len(result.codebook) > 0
        assert result.assignments
        assert len(result.report) > 0
        assert len(result.snapshot_ids) >= 2  # a seed snapshot and a closing one
        assert result.stats.n_responses == len(synthetic_corpus())

        # Every assignment names a code that is actually in the codebook, and a segment
        # that is verbatim in the normalised response. That is the whole provenance
        # claim of the row-oriented output.
        by_id = {response.id: response for response in synthetic_corpus()}
        names = set(result.codebook.names())
        for assignment in result.assignments:
            assert assignment.code in names
            assert assignment.segment in normalise(by_id[assignment.response_id].content)

        # The store holds what the result claims.
        assert board.assignments_for_run("full") == result.assignments
        assert board.read_report("full").summary() == result.report.summary()
        assert {s.snapshot_id for s in board.read_snapshots(run_id="full")} == set(
            result.snapshot_ids
        )


def test_the_run_result_serialises_cleanly() -> None:
    """Agent C2 builds the run report from this object, so it must survive JSON."""
    result, board = run_loop("serialise")
    with board:
        payload = json.loads(json.dumps(result.to_json()))
        assert payload["run_id"] == "serialise"
        assert payload["codebook"]["codes"]
        assert payload["stats"]["n_responses"] == len(result.outcomes)
        assert payload["stats"]["snapshot_ids"] == result.snapshot_ids
        assert len(payload["responses"]) == len(result.outcomes)
        assert payload["stats"]["caveats"], "an offline run must carry the ADR-0019 caveat"
        # Every outcome round-trips too, including its per-check finding summary.
        for outcome, row in zip(result.outcomes, payload["responses"], strict=True):
            assert row["response_id"] == outcome.response_id
            assert row["findings"] == outcome.report.summary()


def test_an_empty_corpus_still_produces_a_well_formed_run() -> None:
    """The degenerate case must not be a special case: a run with nothing in it."""
    result, board = run_loop("empty", [])
    with board:
        assert len(result.codebook) == 0
        assert result.assignments == []
        assert result.outcomes == []
        assert result.stats.n_responses == 0
        assert result.stats.agreement_rate == 0.0
        assert len(result.snapshot_ids) == 2  # the seed snapshot, and the closing one
        assert result.snapshot_ids[0] == result.snapshot_ids[-1]  # content-addressed
        assert result.passed()
        json.dumps(result.to_json())


def test_batches_cover_the_corpus_exactly() -> None:
    responses = synthetic_corpus()
    assert [len(batch) for batch in batches(responses, 10)] == [10, 4]
    assert [response.id for batch in batches(responses, 10) for response in batch] == [
        response.id for response in responses
    ]
    assert batches(responses, 0) == [responses]


# --------------------------------------------------------------------------- #
# 2. Determinism — the acceptance criterion
# --------------------------------------------------------------------------- #


def test_two_runs_produce_byte_identical_codebook_json_and_snapshot_sequence() -> None:
    first, board_a = run_loop("det-a")
    second, board_b = run_loop("det-b")
    with board_a, board_b:
        assert first.codebook_json() == second.codebook_json()
        assert first.snapshot_ids == second.snapshot_ids
        assert [a.to_json() for a in first.assignments] == [
            a.to_json() for a in second.assignments
        ]
        assert first.report.to_json() == second.report.to_json()
        # The snapshot id is the hash of the codebook JSON, so the last snapshot of the
        # run must be the codebook the run returned. No wall clock anywhere in between.
        assert first.snapshot_ids[-1] == freeze(first.codebook).snapshot_id
        assert "created_at" not in first.codebook_json()


def test_the_corpus_order_the_caller_used_does_not_reach_the_codebook() -> None:
    """Processing order is by (source, id), so a shuffled corpus is the same run."""
    corpus = synthetic_corpus()
    shuffled = [corpus[index] for index in (9, 2, 13, 0, 5, 11, 1, 7, 3, 12, 4, 8, 6, 10)]
    ordered_result, board_a = run_loop("order-a")
    shuffled_result, board_b = run_loop("order-b", shuffled)
    with board_a, board_b:
        assert ordered_result.codebook_json() == shuffled_result.codebook_json()
        assert ordered_result.snapshot_ids == shuffled_result.snapshot_ids


# --------------------------------------------------------------------------- #
# 3. Order independence — what frozen snapshots are for
# --------------------------------------------------------------------------- #


def test_rerunning_one_batch_against_its_frozen_snapshot_reproduces_it() -> None:
    corpus = sorted(synthetic_corpus(), key=lambda response: (response.source, response.id))
    full, board = run_loop("replay-full")
    with board:
        # snapshot_ids[1] is the snapshot frozen at the start of the second batch: the
        # exact codebook that batch's coders read.
        start_of_batch_two = board.read_snapshot(full.snapshot_ids[1]).codebook

    replay, replay_board = run_loop("replay-again", corpus[10:], codebook=start_of_batch_two)
    with replay_board:
        assert replay.codebook.to_json_str() == full.codebook.to_json_str()
        assert replay.snapshot_ids == full.snapshot_ids[1:]
        in_batch_two = {response.id for response in corpus[10:]}
        assert [a.to_json() for a in replay.assignments] == [
            a.to_json() for a in full.assignments if a.response_id in in_batch_two
        ]


# --------------------------------------------------------------------------- #
# 4. Both coders receive identical context
# --------------------------------------------------------------------------- #


def test_the_two_coders_are_handed_byte_identical_requests() -> None:
    config = config_for("identical")
    components = offline_components(config)
    snapshot = freeze(Codebook())
    prepared = prep.prepare(synthetic_corpus()[0], snapshot, components.embedder, config=config)

    request_a = components.coder_a.build_request(prepared.context)
    request_b = components.coder_b.build_request(prepared.context)
    assert request_a == request_b
    assert request_a.system == request_b.system
    assert request_a.user == request_b.user
    assert request_a.subject == request_b.subject
    # ...and the clients they go to are what differ, which is the epistemic diversity.
    assert components.coder_a.coder != components.coder_b.coder


def test_prep_retrieval_and_segmentation_are_pure_functions_of_their_inputs() -> None:
    config = config_for("pure")
    components = offline_components(config)
    codebook = Codebook(
        codes={
            code.id: code
            for code in (
                Code(id="code-1", name="negative_impacts-job_loss", description="jobs go"),
                Code(id="code-2", name="applications-healthcare", description="doctors use it"),
            )
        }
    )
    snapshot = freeze(codebook)
    response = synthetic_corpus()[1]
    first = prep.prepare(response, snapshot, components.embedder, config=config)
    second = prep.prepare(response, snapshot, components.embedder, config=config)
    assert [s.to_json() for s in first.segments] == [s.to_json() for s in second.segments]
    assert [r.to_json() for r in first.retrieved] == [r.to_json() for r in second.retrieved]
    assert first.context == second.context
    assert first.context.snapshot_id == snapshot.snapshot_id
    assert len(first.retrieved) <= config.retrieval_top_k


# --------------------------------------------------------------------------- #
# 5. A fabricated quote is dropped by S2, and the drop is in the audit log
# --------------------------------------------------------------------------- #


def test_a_fabricated_quote_is_dropped_by_s2_and_the_drop_is_audited() -> None:
    result, board = run_loop("fabricated")
    with board:
        s2_errors = [
            finding
            for finding in result.report.by_check("S2")
            if finding.severity is Severity.ERROR
        ]
        assert s2_errors, "the mock coder plants fabricated quotes; S2 must drop them"
        assert all(
            finding.data[MARKER_KEY] == "no_verified_evidence" for finding in s2_errors
        )

        drops = board.audit("fabricated").events(event="candidate_dropped")
        s2_drops = [event for event in drops if event.payload["check_id"] == "S2"]
        assert {event.subject for event in s2_drops} == {f.subject for f in s2_errors}
        for event in s2_drops:
            assert event.payload["coder"]
            assert event.payload["marker"] == "no_verified_evidence"
            assert event.snapshot_id in result.snapshot_ids

        # A dropped candidate never reaches the codebook, and the store says why.
        dropped_names = {event.subject for event in s2_drops}
        resolutions = {
            record.candidate.name: record.resolution
            for record in board.read_candidates(run_id="fabricated")
            if record.status == "dropped"
        }
        for name in dropped_names:
            assert resolutions.get(name, "").startswith("S2:")


def test_a_fabricated_quote_never_becomes_an_assignment() -> None:
    result, board = run_loop("fabricated-rows")
    with board:
        fabricated = normalise(FABRICATED_QUOTE)
        assert all(fabricated not in assignment.segment for assignment in result.assignments)
        for code in result.codebook.sorted_codes():
            assert all(fabricated not in evidence.quote for evidence in code.evidence)


# --------------------------------------------------------------------------- #
# 6. The grey zone reaches the judge, or becomes a WARN
# --------------------------------------------------------------------------- #


def _grey_components(config: RunConfig, judge: RecordingJudge | None) -> LoopComponents:
    log = CallLog()
    offline = offline_components(config, call_log=log)
    return LoopComponents(
        coder_a=offline.coder_a,
        coder_b=offline.coder_b,
        embedder=GreyEmbedder(),
        judge=judge,
        call_log=log,
    )


def test_a_grey_zone_pair_reaches_the_judge_when_one_is_supplied() -> None:
    config = config_for("grey-judge")
    judge = RecordingJudge(dispute="KEEP", route="MERGE")
    result, board = run_loop(
        "grey-judge", components=_grey_components(config, judge), **{}
    )
    with board:
        assert any(kind == "dispute" for kind, _ in judge.calls), "M1's grey zone must escalate"
        assert any(kind == "route" for kind, _ in judge.calls), "M2's grey zone must escalate"

        judged = [
            finding
            for finding in result.report.by_check("M1")
            if finding.data.get(MARKER_KEY) == "grey_zone_judged"
        ]
        assert judged and all(finding.data["band"] == BAND_GREY for finding in judged)

        consulted = board.audit("grey-judge").events(event="judge_consulted")
        assert consulted, "every escalation must be an audit row"
        assert {event.payload["check_id"] for event in consulted} <= {"M1", "M2"}
        for event in consulted:
            assert event.payload["verdict"] in {"KEEP", "DROP", "MERGE", "CREATE"}
            assert "score" in event.payload
        assert result.stats.escalations > 0


def test_the_same_grey_zone_becomes_a_warn_and_drops_nothing_without_a_judge() -> None:
    config = config_for("grey-offline")
    result, board = run_loop("grey-offline", components=_grey_components(config, None))
    with board:
        unresolved = [
            finding
            for finding in result.report.by_check("M1")
            if finding.data.get(MARKER_KEY) == "grey_zone_unresolved_offline"
        ]
        assert unresolved, "an unresolvable grey zone must be visible to the human gate"
        assert all(finding.severity is Severity.WARN for finding in unresolved)

        # Nothing is dropped on a meaning judgment that could not be made.
        assert result.stats.candidates_dropped["dispute"] == 0
        assert not board.audit("grey-offline").events(event="judge_consulted")
        assert result.stats.escalations == 0
        # ...and the run still finishes with a codebook.
        assert len(result.codebook) > 0


def test_the_router_keeps_both_sides_of_a_grey_pair_and_drops_only_on_an_explicit_drop() -> None:
    """The acceptance rule, at the level a methods reviewer would check it."""
    embedder = GreyEmbedder()
    rules = CodingRules()
    a = [candidate("impacts-jobs", "jobs go", coder="coder_a")]
    b = [candidate("impacts-work", "work changes", coder="coder_b")]

    offline = check_cross_coder_agreement(a, b, embedder, rules, judge=None)
    assert [match.band for match in offline.matches] == [BAND_GREY]
    kept = router.accept_candidates(offline, a, b, judge_available=False)
    assert len(kept.accepted) == 2 and not kept.dropped
    assert not kept.escalated(), "no judge ran, so nothing was escalated"

    keeper = RecordingJudge(dispute="KEEP")
    judged = check_cross_coder_agreement(a, b, embedder, rules, judge=keeper)
    accepted = router.accept_candidates(judged, a, b, judge_available=True)
    assert len(accepted.accepted) == 2 and not accepted.dropped
    assert len(accepted.escalated()) == 2

    dropper = RecordingJudge(dispute="DROP")
    ruled = check_cross_coder_agreement(a, b, embedder, rules, judge=dropper)
    resolved = router.accept_candidates(ruled, a, b, judge_available=True)
    assert [item.name for item in resolved.accepted] == ["impacts-jobs"]
    assert [item.name for item in resolved.dropped] == ["impacts-work"]


def test_agreement_folds_both_coders_evidence_into_one_accepted_candidate() -> None:
    """Agreement is the cheap case: one candidate, two coders' quotes, no model call."""
    embedder = GreyEmbedder()
    a = [candidate("impacts-jobs", "jobs go", coder="coder_a", span=(0, 7))]
    b = [candidate("impacts-jobs", "work changes", coder="coder_b", span=(9, 21))]
    agreement = check_cross_coder_agreement(a, b, embedder, CodingRules(), judge=None)
    accepted = router.accept_candidates(agreement, a, b, judge_available=True)
    assert len(accepted.accepted) == 1
    item = accepted.accepted[0]
    assert item.origin == "agreed" and not item.escalated
    assert [evidence.quote for evidence in item.candidate.evidence] == [
        "jobs go",
        "work changes",
    ]


# --------------------------------------------------------------------------- #
# 7. The fast loop never splits, re-parents or renames
# --------------------------------------------------------------------------- #


def test_no_snapshot_ever_splits_reparents_or_renames_a_code() -> None:
    result, board = run_loop("no-restructure")
    with board:
        snapshots = [board.read_snapshot(sid) for sid in result.snapshot_ids]
        for earlier, later in pairwise(snapshots):
            for code in earlier.codebook.sorted_codes():
                successor = later.codebook.codes.get(code.id)
                assert successor is not None, f"{code.name} disappeared: a split or a delete"
                assert successor.name == code.name, "a rename happened in the fast loop"
                assert successor.parent_id == code.parent_id, "a re-parent happened"
                assert successor.description == code.description
                assert len(successor.evidence) >= len(code.evidence), "evidence only grows"

        events = set(board.audit("no-restructure").event_names())
        assert not events & {"code_split", "code_reparented", "code_renamed", "operation_applied"}
        assert {"code_created", "code_merged"} & events


def test_integrate_has_exactly_two_outcomes_and_never_invents_a_parent() -> None:
    empty = Codebook()
    decision = router.IntegrationDecision(
        candidate_name="impacts-jobs", action=Route.CREATE, route=Route.CREATE
    )
    created_book, code, action = router.integrate(
        empty, decision, candidate("impacts-jobs", "jobs go", coder="coder_a"), snapshot_id="snap-x"
    )
    assert action is Route.CREATE
    assert code.created_in_snapshot == "snap-x"
    assert code.parent_id is None, "the fast loop does not invent a family node"
    assert len(empty) == 0, "the input codebook is never mutated"

    # A CREATE whose name is already taken is integrated as a MERGE: names identify
    # codes, and S6 would report a duplicate as an ERROR.
    merged_book, merged_code, merged_action = router.integrate(
        created_book,
        decision,
        candidate("impacts-jobs", "other quote", coder="coder_b", span=(9, 20)),
        snapshot_id="snap-y",
    )
    assert merged_action is Route.MERGE
    assert len(merged_book) == 1
    assert merged_code.id == code.id and merged_code.name == code.name
    assert merged_code.created_in_snapshot == "snap-x", "provenance is not rewritten"
    assert len(merged_code.evidence) == 2


def test_integrate_links_a_child_to_an_existing_family_node() -> None:
    family = Code(id="code-family", name="impacts", description="the family")
    codebook = Codebook(codes={family.id: family})
    decision = router.IntegrationDecision(
        candidate_name="impacts-jobs", action=Route.CREATE, route=Route.CREATE
    )
    updated, code, _ = router.integrate(
        codebook, decision, candidate("impacts-jobs", "jobs go", coder="coder_a"), snapshot_id="s"
    )
    assert code.parent_id == family.id
    assert updated.codes[family.id] == family, "the parent itself is untouched"


def test_merge_evidence_is_content_ordered_and_deduplicated() -> None:
    """Evidence order is part of the snapshot id, so it must not follow iteration order."""
    early = Evidence(response_id=203, quote="a", span=(0, 1), verified=True)
    late = Evidence(response_id=212, quote="b", span=(10, 11), verified=True)
    assert router.merge_evidence([late, early], [early]) == [early, late]
    assert router.merge_evidence([late], [late]) == [late]


# --------------------------------------------------------------------------- #
# 8. Every routing decision is recorded
# --------------------------------------------------------------------------- #


def test_every_routing_decision_is_in_the_audit_log_with_its_inputs() -> None:
    result, board = run_loop("routed")
    with board:
        events = board.audit("routed").events(event="route_chosen")
        decisions = [decision for outcome in result.outcomes for decision in outcome.decisions]
        assert len(events) == len(decisions)
        for event in events:
            payload = event.payload
            assert payload["action"] in {"MERGE", "CREATE"}
            assert payload["route"] in {"MERGE", "CREATE", "JUDGE"}
            assert isinstance(payload["score"], float)
            assert payload["space_id"] == result.stats.space_id
            assert payload["code_id"] and payload["code_name"]
            assert event.snapshot_id in result.snapshot_ids
            assert "neighbours" in payload
        assert result.stats.actions["MERGE"] + result.stats.actions["CREATE"] == len(events)


def test_the_router_never_reports_a_finding_of_its_own() -> None:
    """Checks report; the router decides; the audit log records. Asserted structurally."""
    # The router cannot emit a finding because it does not have the vocabulary to.
    assert not hasattr(router, "CheckReport")
    assert not hasattr(router, "Severity")
    a = [candidate("impacts-jobs", "jobs go", coder="coder_a")]
    b = [candidate("impacts-work", "work changes", coder="coder_b")]
    agreement = check_cross_coder_agreement(a, b, GreyEmbedder(), CodingRules(), judge=None)
    accepted = router.accept_candidates(agreement, a, b, judge_available=False)
    assert not hasattr(accepted, "report")
    # The findings about that pair exist — M1 wrote them, and they are WARNs.
    assert [finding.check_id for finding in agreement.report] == ["M1"]


# --------------------------------------------------------------------------- #
# 9. Accounting
# --------------------------------------------------------------------------- #


def test_every_model_call_is_an_llm_calls_row_with_a_role() -> None:
    config = config_for("accounting")
    components = offline_components(config)
    result, board = run_loop("accounting", components=components)
    with board:
        rows = board.read_llm_calls("accounting")
        assert len(rows) == components.call_log.calls > 0
        assert {row.role for row in rows} == {"coder_a", "coder_b", "judge"}
        assert all(row.subject.startswith("response:") for row in rows)
        assert all(row.input_tokens > 0 and row.output_tokens > 0 for row in rows)
        assert all(not row.fail_safe for row in rows), "mocks never fail to parse"
        coder_rows = [row for row in rows if row.role.startswith("coder")]
        assert len(coder_rows) == 2 * result.stats.n_responses
        assert result.stats.llm["calls"] == len(rows)


def test_a_call_log_the_agents_do_not_share_is_refused() -> None:
    config = config_for("mismatched-log")
    components = offline_components(config)
    stray = replace(components, call_log=CallLog())
    with Blackboard() as board, pytest.raises(ValueError, match="same CallLog"):
        run_fast_loop(synthetic_corpus(), config=config, board=board, components=stray)


def test_offline_components_refuses_to_build_a_live_run() -> None:
    with pytest.raises(ValueError, match="live run"):
        offline_components(config_for("live", offline=False))


# --------------------------------------------------------------------------- #
# 10. Segmentation on the real corpus's shapes
# --------------------------------------------------------------------------- #


def _check_segments(response: Response, rules: CodingRules) -> list[str]:
    normalised = normalise(response.content)
    segments = prep.segment_response(response, rules)
    assert segments, "every non-empty response must yield at least one segment"
    for segment in segments:
        assert normalised[segment.start : segment.end] == segment.text
        assert segment.response_id == response.id
        assert len(segment.text.split()) <= rules.max_quote_words
    starts = [segment.start for segment in segments]
    assert starts == sorted(starts), "segments are returned in reading order"
    for earlier, later in pairwise(segments):
        assert earlier.end <= later.start, "segments never overlap"
    return [segment.text for segment in segments]


def test_segmentation_handles_a_response_with_no_sentence_terminator() -> None:
    rules = CodingRules()
    response = Response(id=21, question=QUESTION_V2, content=NO_TERMINATOR, source=SOURCE)
    assert "." not in NO_TERMINATOR and "?" not in NO_TERMINATOR
    assert len(NO_TERMINATOR.split()) > 100
    texts = _check_segments(response, rules)
    assert len(texts) > 1, "an unpunctuated response must not be one enormous segment"


def test_segmentation_handles_a_twenty_eight_word_response_without_padding_it() -> None:
    rules = CodingRules()
    response = Response(id=53, question=QUESTION_V2, content=VERY_SHORT, source=SOURCE)
    assert len(VERY_SHORT.split()) == 28
    texts = _check_segments(response, rules)
    assert 1 <= len(texts) <= 6, "a short answer yields the phrases it has, not a quota"
    # Nothing is invented: the segments together are no longer than the response itself.
    assert sum(len(text.split()) for text in texts) <= len(normalise(VERY_SHORT).split())


def test_segment_ids_are_content_addressed_and_stable() -> None:
    response = Response(id=7, question=QUESTION_V2, content=VERY_SHORT, source=SOURCE)
    first = prep.segment_response(response)
    second = prep.segment_response(response)
    assert [segment.id for segment in first] == [segment.id for segment in second]
    assert len({segment.id for segment in first}) == len(first)
    # A different response with the same span is a different segment.
    other = prep.segment_response(replace(response, id=8))
    assert {s.id for s in first}.isdisjoint({s.id for s in other})


def test_a_quote_span_maps_back_to_the_segment_it_sits_in() -> None:
    config = config_for("spans")
    components = offline_components(config)
    response = synthetic_corpus()[0]
    prepared = prep.prepare(response, freeze(Codebook()), components.embedder, config=config)
    first = prepared.segments[0]
    assert prepared.segment_for((first.start, first.start + 4)) == first
    assert prepared.segment_for(None) is None


# --------------------------------------------------------------------------- #
# The dedup pre-check
# --------------------------------------------------------------------------- #


def test_the_dedup_precheck_names_the_earlier_response_and_drops_nothing() -> None:
    original = synthetic_corpus()[0]
    # The loop orders by (source, id), so the echo needs an id above the original's for
    # the original to be the one "seen first" and the echo the one reported.
    echo = Response(
        id=299, question=original.question, content=original.content, source=original.source
    )
    seen = {prep.dedup_precheck(original).content_hash: original.id}
    verdict = prep.dedup_precheck(echo, seen)
    assert verdict.is_duplicate and verdict.duplicate_of == original.id
    assert prep.dedup_precheck(original, seen).duplicate_of is None, "a response is not its own echo"

    result, board = run_loop("dedup", [original, echo])
    with board:
        assert result.stats.n_duplicate_responses == 1
        events = board.audit("dedup").events(event="duplicate_response")
        assert [event.subject for event in events] == ["299"]
        # Reported, never dropped: both responses are still coded.
        assert {outcome.response_id for outcome in result.outcomes} == {original.id, 299}
        assert {assignment.response_id for assignment in result.assignments} == {original.id, 299}


# --------------------------------------------------------------------------- #
# The closing checks
# --------------------------------------------------------------------------- #


def test_the_run_closes_with_s6_and_m4_over_the_final_codebook() -> None:
    result, board = run_loop("closing")
    with board:
        # S6 must have been given the final codebook: a duplicate name or a dangling
        # parent would be an ERROR here, and the run must not produce either.
        s6 = result.report.by_check("S6")
        assert all(finding.severity is not Severity.ERROR for finding in s6)
        closing = board.audit("closing").events(event="findings_recorded")[-1]
        assert closing.scope == "codebook"
        assert closing.snapshot_id in result.snapshot_ids
        assert set(closing.payload["summary"]) <= {"S6", "M4"}


def test_the_stats_reconcile_with_the_codebook_and_the_rows() -> None:
    result, board = run_loop("stats")
    with board:
        stats = result.stats
        assert stats.codes_final == len(result.codebook)
        assert stats.families_final == len(result.codebook.families())
        assert stats.assignments == len(result.assignments)
        assert stats.findings == result.report.summary()
        assert stats.severities == result.report.totals()
        assert stats.snapshot_ids == result.snapshot_ids
        assert 0.0 <= stats.agreement_rate <= 1.0
        assert sum(stats.acceptance_by_origin.values()) == stats.candidates_accepted
        proposed = sum(stats.candidates_proposed.values())
        survived = sum(stats.candidates_survived.values())
        assert proposed - survived == stats.candidates_dropped["structural"]
        assert stats.codes_created <= sum(len(o.created) for o in result.outcomes)


def test_a_seeded_codebook_is_extended_rather_than_rebuilt() -> None:
    """A run can continue from an earlier codebook; existing codes keep their identity."""
    seed = Code(
        id="code-seed",
        name="applications-healthcare",
        description="AI used in medicine",
        created_in_snapshot="snap-seed",
    )
    result, board = run_loop("seeded", codebook=Codebook(codes={seed.id: seed}))
    with board:
        kept = result.codebook.codes[seed.id]
        assert kept.name == seed.name
        assert kept.description == seed.description
        assert kept.created_in_snapshot == "snap-seed"
        assert len(result.codebook) >= 1
        # The seeded code is what the first batch's coders retrieved against.
        assert result.snapshot_ids[0] == freeze(Codebook(codes={seed.id: seed})).snapshot_id


def test_code_text_rendering_is_the_only_one_prep_uses() -> None:
    """Retrieval must measure the same object the dedup gate does (ADR-0003)."""
    config = config_for("render")
    components = offline_components(config)
    code = Code(id="code-1", name="impacts-jobs", description="jobs go")
    snapshot = freeze(Codebook(codes={code.id: code}))
    retrieved = prep.retrieve(
        synthetic_corpus()[1], snapshot, components.embedder, top_k=config.retrieval_top_k
    )
    assert [scored.code_id for scored in retrieved] == [code.id]
    assert retrieved[0].space_id == components.embedder.space_id
    expected = float(
        components.embedder.embed_one(normalise(synthetic_corpus()[1].content))
        @ components.embedder.embed_one(code_text(code.name, code.description))
    )
    assert retrieved[0].score == pytest.approx(expected)


def test_the_run_reports_whether_the_slow_loop_is_due() -> None:
    """The documented checkpoint cadence must be computed, not merely available.

    `should_checkpoint` and `checkpoint_signals` existed and were tested, but nothing in
    the pipeline ever called them: a 200-response run fired zero checkpoints and never
    told the operator one was owed. The second adversarial review called the mechanism
    decorative, and it was right.

    The fast loop now computes the signal at the end of a run and **reports** it. It
    deliberately does not act on it: opening the gate needs a human at a terminal, and a
    batch run must not block for one. `gaf checkpoint` is how the operator acts.
    """
    config = RunConfig(run_id="due")
    with Blackboard(":memory:") as board:
        board.register_run(config)
        responses = synthetic_corpus()
        board.write_responses(responses)
        result = run_fast_loop(
            responses, config=config, board=board, components=offline_components(config)
        )

    due = result.stats.checkpoint_due
    assert set(due) >= {"fires", "trigger", "reason"}
    assert isinstance(due["fires"], bool)
    assert due["trigger"] != "unavailable", f"health metrics failed: {due['reason']}"
    # and it survives serialisation, because the run report is built from the JSON
    assert result.stats.to_json()["checkpoint_due"] == due


def test_the_hard_floor_fires_the_slow_loop_signal() -> None:
    """A quiet codebook still owes the human a look every `hard_floor_responses`.

    Set the floor to 1 so a fourteen-response fixture crosses it; the point is that the
    policy is consulted at all, which is what was missing.
    """
    policy = replace(CheckpointPolicy(), hard_floor_responses=1, min_responses_between_checkpoints=0)
    config = RunConfig(run_id="floor", checkpoints=policy)
    with Blackboard(":memory:") as board:
        board.register_run(config)
        responses = synthetic_corpus()
        board.write_responses(responses)
        result = run_fast_loop(
            responses, config=config, board=board, components=offline_components(config)
        )

    assert result.stats.checkpoint_due["fires"] is True, result.stats.checkpoint_due
    assert result.stats.checkpoint_due["reason"], "a firing trigger must say why"
