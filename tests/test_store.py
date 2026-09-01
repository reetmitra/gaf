"""The blackboard: deterministic ids, frozen snapshots, an append-only log, and reads
that come back in the same order every time.

Three claims are load-bearing for the whole project and are asserted here:

1. **Ids are content-addressed.** The same content mints the same id, in this process
   and in any other, so a run is replayable.
2. **A snapshot is its codebook's hash.** Freezing twice gives one id; altering the
   codebook gives another; altering a stored row is detected on read.
3. **Every read is deterministically ordered.** A read that returned rows in an
   arbitrary order would break byte-identical output downstream, intermittently.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path

import pytest

from gaf.checks.contracts import CheckReport, Severity
from gaf.config import RunConfig
from gaf.ids import (
    HASH_LENGTH,
    assignment_id,
    candidate_id,
    checkpoint_id,
    code_id,
    coding_id,
    content_hash,
    digest_parts,
    finding_id,
    full_content_hash,
    llm_call_id,
    mint,
    snapshot_id,
)
from gaf.llm.base import LLMResult, TaskType
from gaf.models import Candidate, Code, Codebook, Evidence, Response
from gaf.store.audit import AuditEvent, AuditLog, utc_now_iso
from gaf.store.blackboard import Blackboard, StoreConflictError
from gaf.store.snapshot import (
    SNAPSHOT_REASONS,
    Snapshot,
    SnapshotIntegrityError,
    freeze,
    verify_codebook_json,
)
from gaf.textnorm import NORMALISATION_VERSION
from tests.fixtures.codebooks import near_duplicate_codebook, toy_codebook
from tests.fixtures.corpus import SOURCE, synthetic_corpus

RUN_ID = "test-run"


@pytest.fixture
def store() -> Iterator[Blackboard]:
    with Blackboard(":memory:") as blackboard:
        yield blackboard


@pytest.fixture
def config() -> RunConfig:
    return RunConfig().with_(run_id=RUN_ID)


# =========================================================================== #
# gaf.ids
# =========================================================================== #


def test_content_hash_is_deterministic_and_truncated() -> None:
    assert content_hash("hello") == content_hash("hello")
    assert len(content_hash("hello")) == HASH_LENGTH
    assert full_content_hash("hello").startswith(content_hash("hello"))
    assert len(full_content_hash("hello")) == 64


def test_content_hash_accepts_bytes_and_str_alike() -> None:
    assert content_hash("hello") == content_hash(b"hello")


def test_content_hash_separates_different_content() -> None:
    assert content_hash("hello") != content_hash("hell0")
    assert content_hash("") != content_hash(" ")


def test_content_hash_rejects_an_impossible_length() -> None:
    with pytest.raises(ValueError, match="between 1 and 64"):
        content_hash("x", length=65)


def test_digest_parts_cannot_be_confused_by_re_splitting() -> None:
    """("ab", "c") and ("a", "bc") are different tuples and must hash differently."""
    assert digest_parts("ab", "c") != digest_parts("a", "bc")
    assert digest_parts(None) != digest_parts("")
    assert digest_parts(True) != digest_parts("True ")
    assert mint("x", 1, 2) == f"x-{digest_parts(1, 2)}"


def test_snapshot_id_is_the_hash_of_the_codebook_serialisation() -> None:
    codebook = toy_codebook()
    assert snapshot_id(codebook.to_json_str()) == snapshot_id(codebook.to_json_str())
    assert snapshot_id(codebook.to_json_str()).startswith("snap-")
    assert snapshot_id(codebook.to_json_str()) != snapshot_id(
        near_duplicate_codebook().to_json_str()
    )


def test_code_id_follows_the_name() -> None:
    assert code_id("positive_impacts-healthcare") == code_id("positive_impacts-healthcare")
    assert code_id("positive_impacts-healthcare") != code_id("positive_impacts-health_care")


def test_every_minter_is_a_pure_function_of_its_inputs() -> None:
    kwargs = {
        "run_id": RUN_ID,
        "response_id": 9,
        "source": SOURCE,
        "coder": "coder_a",
        "snapshot_id": "snap-abc",
        "prompt_version": "coder-v1",
    }
    assert coding_id(**kwargs) == coding_id(**kwargs)
    assert coding_id(**kwargs) != coding_id(**{**kwargs, "coder": "coder_b"})
    assert coding_id(**kwargs) != coding_id(**{**kwargs, "snapshot_id": "snap-abd"})
    assert coding_id(**kwargs).startswith("coding-")

    assert candidate_id(coding_id="c1", name="n") == candidate_id(coding_id="c1", name="n")
    assert candidate_id(coding_id="c1", name="n", ordinal=0) != candidate_id(
        coding_id="c1", name="n", ordinal=1
    )

    asg = {
        "run_id": RUN_ID,
        "response_id": 9,
        "source": SOURCE,
        "code_id": "code-1",
        "segment_text": "a span",
        "snapshot_id": "snap-abc",
    }
    assert assignment_id(**asg) == assignment_id(**asg)
    assert assignment_id(**asg) != assignment_id(**{**asg, "segment_text": "another span"})

    find = {
        "run_id": RUN_ID,
        "check_id": "S2",
        "severity": "ERROR",
        "scope": "candidate",
        "subject": "x",
        "message": "m",
    }
    assert finding_id(**find) == finding_id(**find)
    assert finding_id(**find) != finding_id(**{**find, "severity": "WARN"})

    ckpt = {
        "run_id": RUN_ID,
        "at_response_count": 10,
        "trigger": "floor",
        "base_snapshot_id": "snap-abc",
    }
    assert checkpoint_id(**ckpt) == checkpoint_id(**ckpt)
    assert checkpoint_id(**ckpt) != checkpoint_id(**{**ckpt, "at_response_count": 20})

    call = {
        "run_id": RUN_ID,
        "task": "code",
        "provider": "mock",
        "model": "mock-coder-a",
        "prompt_version": "coder-v1",
    }
    assert llm_call_id(**call) == llm_call_id(**call)
    assert llm_call_id(**call) != llm_call_id(**{**call, "ordinal": 1})


def test_ids_do_not_collide_across_a_realistic_spread() -> None:
    minted = {
        coding_id(
            run_id=RUN_ID,
            response_id=rid,
            source=SOURCE,
            coder=coder,
            snapshot_id=f"snap-{n:04d}",
            prompt_version="coder-v1",
        )
        for rid in range(200)
        for coder in ("coder_a", "coder_b")
        for n in range(10)
    }
    assert len(minted) == 200 * 2 * 10


# =========================================================================== #
# gaf.store.snapshot
# =========================================================================== #


def test_freezing_the_same_codebook_twice_yields_the_same_id() -> None:
    first = freeze(toy_codebook(), reason="seed")
    second = freeze(toy_codebook(), reason="seed")
    assert first.snapshot_id == second.snapshot_id
    assert first.snapshot_id == snapshot_id(toy_codebook().to_json_str())
    assert first.code_count == len(toy_codebook())


def test_a_modified_codebook_yields_a_different_id() -> None:
    codebook = toy_codebook()
    base = freeze(codebook)
    mutated = Codebook(
        codes={
            **codebook.codes,
            "code-new": Code(id="code-new", name="future-uncertainty", description="new"),
        }
    )
    assert freeze(mutated).snapshot_id != base.snapshot_id


def test_snapshot_parent_and_reason_do_not_change_the_id() -> None:
    """The id is the hash of the codebook, and only of the codebook."""
    plain = freeze(toy_codebook(), reason="seed")
    child = freeze(toy_codebook(), parent_id="snap-parent", reason="checkpoint_apply")
    assert plain.snapshot_id == child.snapshot_id
    assert child.parent_id == "snap-parent"
    assert child.reason in SNAPSHOT_REASONS


def test_an_unknown_reason_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown snapshot reason"):
        freeze(toy_codebook(), reason="whenever")


def test_tampering_is_detected_by_integrity_verification() -> None:
    snapshot = freeze(toy_codebook())
    assert snapshot.is_intact()
    snapshot.verify()

    forged = replace(snapshot, snapshot_id="snap-0000000000000000")
    assert not forged.is_intact()
    with pytest.raises(SnapshotIntegrityError, match="does not match its codebook"):
        forged.verify()

    miscounted = replace(snapshot, code_count=99)
    with pytest.raises(SnapshotIntegrityError, match="claims 99 codes"):
        miscounted.verify()

    assert verify_codebook_json(snapshot.snapshot_id, snapshot.codebook_json)
    assert not verify_codebook_json(snapshot.snapshot_id, snapshot.codebook_json + " ")


def test_a_tampered_stored_row_is_detected_on_read(store: Blackboard, config: RunConfig) -> None:
    """Triggers stop UPDATE; content addressing catches a row written some other way."""
    store.register_run(config)
    forged_id = "snap-" + content_hash("something else entirely")
    store.conn.execute(
        "INSERT INTO snapshots(snapshot_id, parent_id, run_id, created_at, reason, "
        "code_count, codebook_json) VALUES (?, NULL, ?, ?, 'seed', 0, ?)",
        (forged_id, RUN_ID, utc_now_iso(), toy_codebook().to_json_str()),
    )
    store.conn.commit()
    with pytest.raises(SnapshotIntegrityError, match="has been altered"):
        store.read_snapshot(forged_id)
    # The row is still readable with verification off, so a repair tool can see it.
    assert store.read_snapshot(forged_id, verify=False).snapshot_id == forged_id


def test_snapshot_delegates_hierarchy_to_the_codebook() -> None:
    snapshot = freeze(toy_codebook())
    codebook = toy_codebook()
    assert snapshot.hierarchy_skeleton() == codebook.hierarchy_skeleton()
    assert [c.id for c in snapshot.leaves()] == [c.id for c in codebook.leaves()]
    assert list(snapshot.families()) == list(codebook.families())
    assert snapshot.names() == codebook.names()
    assert len(snapshot) == len(codebook)
    assert snapshot.by_name("future-inevitability") is not None
    assert "c-future" in snapshot


def test_snapshot_json_round_trips() -> None:
    snapshot = freeze(toy_codebook(), parent_id="snap-parent", reason="batch")
    restored = Snapshot.from_json(json.loads(json.dumps(snapshot.to_json())))
    assert restored == snapshot
    restored.verify()


def test_storing_the_same_snapshot_twice_is_a_no_op(
    store: Blackboard, config: RunConfig
) -> None:
    store.register_run(config)
    first = store.freeze_codebook(toy_codebook(), run_id=RUN_ID, reason="seed")
    second = store.freeze_codebook(toy_codebook(), run_id=RUN_ID, reason="seed")
    assert first.snapshot_id == second.snapshot_id
    assert len(store.read_snapshots(run_id=RUN_ID)) == 1


def test_snapshots_are_immutable_in_the_database(store: Blackboard, config: RunConfig) -> None:
    store.register_run(config)
    store.freeze_codebook(toy_codebook(), run_id=RUN_ID, reason="seed")
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        store.conn.execute("UPDATE snapshots SET code_count = 0")
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        store.conn.execute("DELETE FROM snapshots")


# =========================================================================== #
# gaf.store.audit
# =========================================================================== #


def test_audit_events_read_back_in_insertion_order(
    store: Blackboard, config: RunConfig
) -> None:
    store.register_run(config)
    log = store.audit(RUN_ID)
    for n in range(25):
        log.emit("coded", subject=str(n), scope="response", index=n)

    events = log.events()
    assert [e.payload["index"] for e in events] == list(range(25))
    assert [e.event_id for e in events] == sorted(e.event_id for e in events)
    assert log.events() == events  # the same order, read twice


def test_audit_filters_by_event_name_and_subject(store: Blackboard, config: RunConfig) -> None:
    store.register_run(config)
    log = store.audit(RUN_ID)
    log.emit("coded", subject="9", scope="response")
    log.emit("merged", subject="9", scope="candidate", route="MERGE")
    log.emit("coded", subject="12", scope="response")

    assert [e.subject for e in log.events(event="coded")] == ["9", "12"]
    assert [e.event for e in log.events(subject="9")] == ["coded", "merged"]
    assert log.event_names() == ["coded", "merged"]
    assert log.counts() == {"coded": 2, "merged": 1}
    assert log.count() == 3
    assert log.count("coded") == 2
    assert len(log) == 3
    assert [e.event for e in log] == ["coded", "merged", "coded"]


def test_audit_records_snapshot_and_payload(store: Blackboard, config: RunConfig) -> None:
    store.register_run(config)
    snapshot = store.freeze_codebook(toy_codebook(), run_id=RUN_ID, reason="seed")
    event = store.audit(RUN_ID).emit(
        "snapshot_frozen",
        subject=snapshot.snapshot_id,
        scope="codebook",
        snapshot_id=snapshot.snapshot_id,
        code_count=snapshot.code_count,
    )
    (stored,) = store.audit(RUN_ID).events()
    assert stored == event
    assert stored.snapshot_id == snapshot.snapshot_id
    assert stored.payload == {"code_count": snapshot.code_count}
    assert stored.created_at.endswith("Z")
    assert isinstance(stored, AuditEvent)


def test_audit_api_offers_no_way_to_update_or_delete(
    store: Blackboard, config: RunConfig
) -> None:
    store.register_run(config)
    log = store.audit(RUN_ID)
    log.emit("coded", subject="9")
    assert not any(
        hasattr(log, name) for name in ("update", "delete", "clear", "remove", "truncate")
    )
    # And the database refuses even if something bypassed the API.
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        store.conn.execute("UPDATE audit SET event = 'tampered'")
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        store.conn.execute("DELETE FROM audit")
    assert log.count() == 1


def test_audit_refuses_a_payload_it_cannot_serialise(
    store: Blackboard, config: RunConfig
) -> None:
    store.register_run(config)
    log = store.audit(RUN_ID)
    with pytest.raises(TypeError, match="JSON-serialisable"):
        log.emit("weird", offending={1, 2, 3})
    assert log.count() == 0  # nothing lossy was written


def test_audit_is_scoped_to_its_run(store: Blackboard) -> None:
    store.register_run(RunConfig().with_(run_id="run-a"))
    store.register_run(RunConfig().with_(run_id="run-b"))
    store.audit("run-a").emit("coded", subject="9")
    store.audit("run-b").emit("coded", subject="10")
    assert [e.subject for e in store.audit("run-a").events()] == ["9"]
    assert [e.subject for e in store.audit("run-b").events()] == ["10"]


def test_audit_log_can_be_constructed_directly_over_a_connection(
    store: Blackboard, config: RunConfig
) -> None:
    store.register_run(config)
    log = AuditLog(store.conn, RUN_ID)
    log.emit("started")
    assert log.count("started") == 1


# =========================================================================== #
# gaf.store.blackboard — runs, responses
# =========================================================================== #


def test_run_registration_stores_the_config(store: Blackboard, config: RunConfig) -> None:
    record = store.register_run(config)
    assert record.run_id == RUN_ID
    assert record.offline is True
    assert record.config == config.to_json()
    assert store.read_run(RUN_ID) == record
    assert store.read_run("absent") is None


def test_run_registration_is_idempotent_for_an_identical_config(
    store: Blackboard, config: RunConfig
) -> None:
    first = store.register_run(config)
    assert store.register_run(config) == first
    assert len(store.runs()) == 1


def test_re_registering_a_run_with_a_different_config_raises(
    store: Blackboard, config: RunConfig
) -> None:
    store.register_run(config)
    with pytest.raises(StoreConflictError, match="different config"):
        store.register_run(config.with_(batch_size=99))


def test_responses_round_trip_with_metadata(store: Blackboard, config: RunConfig) -> None:
    store.register_run(config)
    corpus = [replace(r, meta={"age": 34, "region": "south"}) for r in synthetic_corpus()]
    assert store.write_responses(corpus) == len(corpus)
    assert store.read_responses() == corpus
    assert store.response_count() == len(corpus)
    assert store.read_response(9999, SOURCE) is None
    one = store.read_response(corpus[0].id, SOURCE)
    assert one is not None and one.meta == {"age": 34, "region": "south"}


def test_response_content_hash_is_stored(store: Blackboard, config: RunConfig) -> None:
    store.register_run(config)
    response = synthetic_corpus()[0]
    assert store.write_response(response) == content_hash(response.content)


def test_rewriting_a_response_with_different_content_raises(
    store: Blackboard, config: RunConfig
) -> None:
    store.register_run(config)
    response = synthetic_corpus()[0]
    store.write_response(response)
    store.write_response(response)  # identical: a no-op
    with pytest.raises(StoreConflictError, match="different content"):
        store.write_response(replace(response, content="rewritten"))


def test_responses_read_back_in_a_stable_order(store: Blackboard, config: RunConfig) -> None:
    store.register_run(config)
    corpus = synthetic_corpus()
    store.write_responses(reversed(corpus))
    first = store.read_responses()
    second = store.read_responses()
    assert [r.id for r in first] == sorted(r.id for r in corpus)
    assert first == second


def test_responses_are_partitioned_by_source(store: Blackboard, config: RunConfig) -> None:
    store.register_run(config)
    store.write_response(Response(id=9, question="q", content="wave one", source="a"))
    store.write_response(Response(id=9, question="q", content="wave two", source="b"))
    assert [r.content for r in store.read_responses(source="b")] == ["wave two"]
    assert store.response_count() == 2


# =========================================================================== #
# gaf.store.blackboard — the full round trip
# =========================================================================== #


def _seeded(store: Blackboard, config: RunConfig) -> Snapshot:
    store.register_run(config)
    store.write_responses(synthetic_corpus())
    return store.freeze_codebook(toy_codebook(), run_id=config.run_id, reason="seed")


def test_full_round_trip(store: Blackboard, config: RunConfig) -> None:
    """Register a run, write everything, read it all back identically."""
    snapshot = _seeded(store, config)

    coding = store.write_coding(
        run_id=RUN_ID,
        response_id=203,
        source=SOURCE,
        coder="coder_a",
        snapshot_id=snapshot.snapshot_id,
        prompt_version="coder-v1",
        raw={"candidates": [{"name": "positive_impacts-healthcare"}]},
    )
    assert store.read_codings(RUN_ID) == [coding]
    assert store.read_codings(RUN_ID, coder="coder_b") == []
    assert store.coded_response_count(RUN_ID) == 1

    candidate = Candidate(
        name="positive_impacts-healthcare",
        description="AI improves diagnosis and access to care.",
        evidence=[
            Evidence(response_id=203, quote="Rural clinics get", span=(0, 17), verified=True, score=1.0)
        ],
        coder="coder_a",
        parent_hint="positive_impacts",
    )
    written = store.write_candidate(coding.coding_id, candidate)
    (read_back,) = store.read_candidates(coding_id=coding.coding_id)
    assert read_back == written
    assert read_back.candidate == candidate  # coder recovered by joining the coding
    assert read_back.status == "proposed"

    store.update_candidate(
        written.candidate_id, status="merged", resolution="MERGE", code_id="code-abc"
    )
    (updated,) = store.read_candidates(run_id=RUN_ID)
    assert (updated.status, updated.resolution, updated.code_id) == ("merged", "MERGE", "code-abc")

    assignment = store.write_assignment(
        run_id=RUN_ID,
        response_id=203,
        source=SOURCE,
        code_id="code-abc",
        code_name="positive_impacts-healthcare",
        segment_text="Rural clinics get",
        span=(0, 17),
        snapshot_id=snapshot.snapshot_id,
    )
    assert store.read_assignments(RUN_ID) == [assignment]
    assert assignment.norm_version == NORMALISATION_VERSION
    assert store.assignments_for_run(RUN_ID) == [
        assignment.to_assignment()
    ]

    report = CheckReport()
    report.add("S2", Severity.ERROR, "candidate", "x", "quote not in source", score=0.1)
    report.add("M2", Severity.INFO, "pair", "a<->b", "grey zone", similarity=0.6)
    store.write_report(report, run_id=RUN_ID, response_id=203, snapshot_id=snapshot.snapshot_id)
    assert store.read_report(RUN_ID).to_json() == report.to_json()

    assert store.latest_snapshot(RUN_ID) == snapshot
    assert store.read_snapshot(snapshot.snapshot_id) == snapshot
    assert store.snapshot_exists(snapshot.snapshot_id)


def test_check_report_persists_and_reloads_losslessly(
    store: Blackboard, config: RunConfig
) -> None:
    _seeded(store, config)
    report = CheckReport()
    report.add("S1", Severity.WARN, "candidate", "future-x", "no description")
    report.add("S2", Severity.ERROR, "candidate", "future-x", "quote absent", score=0.0, span=None)
    report.add("S4", Severity.WARN, "segment", "17", "three codes on one span", codes=["a", "b", "c"])
    report.add("M3", Severity.INFO, "candidate", "future-y", "fit ok", verdict="APPLIES")

    ids = store.write_report(report, run_id=RUN_ID)
    assert len(ids) == len(report) == 4
    assert len(set(ids)) == 4  # every finding is its own row

    reloaded = store.read_report(RUN_ID)
    assert reloaded.to_json() == report.to_json()
    assert [f.severity for f in reloaded] == [f.severity for f in report]
    assert reloaded.summary() == report.summary()
    assert reloaded.totals() == report.totals()
    assert reloaded.passed() is report.passed()

    assert [f.check_id for f in store.read_report(RUN_ID, check_id="S2")] == ["S2"]
    assert [f.check_id for f in store.read_report(RUN_ID, severity=Severity.WARN)] == ["S1", "S4"]
    assert store.findings_summary(RUN_ID) == report.summary()


def test_writing_the_same_report_twice_writes_two_sets_of_rows(
    store: Blackboard, config: RunConfig
) -> None:
    """Finding it twice is two findings; the ordinal in the id says so."""
    _seeded(store, config)
    report = CheckReport()
    report.add("S1", Severity.WARN, "candidate", "x", "no description")
    first = store.write_report(report, run_id=RUN_ID)
    second = store.write_report(report, run_id=RUN_ID)
    assert first != second
    assert len(store.read_report(RUN_ID)) == 2


def test_llm_result_persists_as_an_accounting_row(
    store: Blackboard, config: RunConfig
) -> None:
    _seeded(store, config)
    result = LLMResult(
        data={"candidates": []},
        task=TaskType.CODE,
        provider="mock",
        model="mock-coder-a",
        prompt_version="coder-v1",
        input_tokens=120,
        output_tokens=45,
        cost_usd=0.000123,
        latency_ms=12.5,
        cache_hit=True,
        fail_safe=False,
    )
    record = store.write_llm_call(result, run_id=RUN_ID, role="coder_a", subject="3")
    (stored,) = store.read_llm_calls(RUN_ID)
    assert stored == record
    assert stored.task == "code"
    assert stored.cache_hit is True
    assert stored.fail_safe is False
    assert stored.cost_usd == pytest.approx(0.000123)

    second = store.write_llm_call(result, run_id=RUN_ID, role="coder_a", subject="3")
    assert second.call_id != record.call_id  # a repeat call is a second row
    assert [c.call_id for c in store.read_llm_calls(RUN_ID)] == [record.call_id, second.call_id]
    assert store.read_llm_calls(RUN_ID, task="judge_fit") == []


def test_checkpoints_record_the_proposal_and_the_human_decision(
    store: Blackboard, config: RunConfig
) -> None:
    snapshot = _seeded(store, config)
    proposal = {
        "operations": [
            {
                "type": "split",
                "targets": ["c-negative_impacts-job_destruction"],
                "payload": {"into": ["a", "b"]},
                "rationale": "overloaded",
            },
            {"type": "noop", "targets": [], "payload": {}, "rationale": "nothing else"},
        ]
    }
    checkpoint = store.write_checkpoint(
        run_id=RUN_ID,
        at_response_count=10,
        trigger="floor",
        base_snapshot_id=snapshot.snapshot_id,
        proposal=proposal,
    )
    assert store.read_checkpoints(RUN_ID) == [checkpoint]
    assert [op.type for op in checkpoint.operations()] == ["split", "noop"]

    applied = store.freeze_codebook(
        near_duplicate_codebook(), run_id=RUN_ID, parent_id=snapshot.snapshot_id,
        reason="checkpoint_apply",
    )
    decided = store.decide_checkpoint(
        checkpoint.checkpoint_id,
        status="applied",
        decisions=[{"index": 0, "decision": "accept"}, {"index": 1, "decision": "reject"}],
        result_snapshot_id=applied.snapshot_id,
    )
    assert decided.status == "applied"
    assert decided.result_snapshot_id == applied.snapshot_id
    assert [d["decision"] for d in decided.decisions] == ["accept", "reject"]
    assert decided.decided_at is not None
    assert store.read_checkpoint("ckpt-absent") is None


def test_health_metrics_round_trip_and_resample(store: Blackboard, config: RunConfig) -> None:
    _seeded(store, config)
    store.write_health_metrics(
        run_id=RUN_ID, at_response_count=10, metrics={"orphan_rate": 0.1, "leaf_ratio": 0.8}
    )
    store.write_health_metrics(run_id=RUN_ID, at_response_count=20, metrics={"orphan_rate": 0.05})
    metrics = store.read_health_metrics(RUN_ID)
    assert [(m.at_response_count, m.metric) for m in metrics] == [
        (10, "leaf_ratio"),
        (10, "orphan_rate"),
        (20, "orphan_rate"),
    ]
    store.write_health_metric(run_id=RUN_ID, at_response_count=10, metric="orphan_rate", value=0.2)
    assert [m.value for m in store.read_health_metrics(RUN_ID, metric="orphan_rate")] == [0.2, 0.05]


def test_latest_snapshot_follows_the_chain(store: Blackboard, config: RunConfig) -> None:
    seed = _seeded(store, config)
    assert store.latest_snapshot(RUN_ID) == seed
    later = store.freeze_codebook(
        near_duplicate_codebook(), run_id=RUN_ID, parent_id=seed.snapshot_id, reason="batch"
    )
    assert store.latest_snapshot(RUN_ID) == later
    assert [s.snapshot_id for s in store.read_snapshots(run_id=RUN_ID)] == [
        seed.snapshot_id,
        later.snapshot_id,
    ]
    assert store.latest_snapshot("no-such-run") is None


# =========================================================================== #
# Deterministic ordering
# =========================================================================== #


def test_every_read_is_deterministically_ordered(store: Blackboard, config: RunConfig) -> None:
    """Written out of order on purpose; read back in content order, twice."""
    snapshot = _seeded(store, config)
    codings = {}
    # Corpus ids: `write_coding` has a foreign key to the responses table, so these
    # must be real. Written 239, 203, 217 to prove the read order is not insertion order.
    for response_id in (239, 203, 217):
        for coder in ("coder_b", "coder_a"):
            codings[(response_id, coder)] = store.write_coding(
                run_id=RUN_ID,
                response_id=response_id,
                source=SOURCE,
                coder=coder,
                snapshot_id=snapshot.snapshot_id,
                prompt_version="coder-v1",
            )
            store.write_candidates(
                codings[(response_id, coder)].coding_id,
                [
                    Candidate(name="zeta-last", description="z"),
                    Candidate(name="alpha-first", description="a"),
                ],
            )
    for response_id, code_name in ((239, "zeta"), (203, "alpha"), (217, "middle"), (203, "beta")):
        store.write_assignment(
            run_id=RUN_ID,
            response_id=response_id,
            source=SOURCE,
            code_id=f"code-{code_name}",
            code_name=code_name,
            segment_text=f"segment for {code_name}",
            snapshot_id=snapshot.snapshot_id,
        )

    def snapshot_of_reads() -> tuple[list[object], ...]:
        return (
            [(c.response_id, c.coder) for c in store.read_codings(RUN_ID)],
            [(c.candidate.name, c.coding_id) for c in store.read_candidates(run_id=RUN_ID)],
            [(a.response_id, a.code_name) for a in store.read_assignments(RUN_ID)],
            [r.id for r in store.read_responses()],
            [s.snapshot_id for s in store.read_snapshots()],
            [e.event_id for e in store.audit(RUN_ID).events()],
        )

    first = snapshot_of_reads()
    second = snapshot_of_reads()
    assert first == second

    assert first[0] == [
        (203, "coder_a"), (203, "coder_b"),
        (217, "coder_a"), (217, "coder_b"),
        (239, "coder_a"), (239, "coder_b"),
    ]
    assert [name for name, _ in first[1]] == ["alpha-first", "zeta-last"] * 6
    assert first[2] == [(203, "alpha"), (203, "beta"), (217, "middle"), (239, "zeta")]


def test_assignments_order_is_content_based_not_insertion_based(
    store: Blackboard, config: RunConfig
) -> None:
    snapshot = _seeded(store, config)
    pairs = [(39, "zeta"), (3, "alpha"), (17, "middle")]
    for response_id, code_name in pairs:
        store.write_assignment(
            run_id=RUN_ID, response_id=response_id, source=SOURCE, code_id=f"code-{code_name}",
            code_name=code_name, segment_text="s", snapshot_id=snapshot.snapshot_id,
        )
    forward = [(a.response_id, a.code_name) for a in store.read_assignments(RUN_ID)]

    with Blackboard(":memory:") as other:
        other.register_run(config)
        other.write_responses(synthetic_corpus())
        other_snapshot = other.freeze_codebook(toy_codebook(), run_id=RUN_ID, reason="seed")
        for response_id, code_name in reversed(pairs):
            other.write_assignment(
                run_id=RUN_ID, response_id=response_id, source=SOURCE, code_id=f"code-{code_name}",
                code_name=code_name, segment_text="s", snapshot_id=other_snapshot.snapshot_id,
            )
        assert [(a.response_id, a.code_name) for a in other.read_assignments(RUN_ID)] == forward


# =========================================================================== #
# Lifecycle
# =========================================================================== #


def test_store_persists_to_a_file_and_reopens(tmp_path: Path, config: RunConfig) -> None:
    path = tmp_path / "nested" / "run.sqlite"
    with Blackboard(path) as first:
        first.register_run(config)
        first.write_responses(synthetic_corpus())
        snapshot = first.freeze_codebook(toy_codebook(), run_id=RUN_ID, reason="seed")
        first.audit(RUN_ID).emit("started")

    assert path.exists()
    with Blackboard(path) as second:
        assert second.read_run(RUN_ID) is not None
        assert len(second.read_responses()) == len(synthetic_corpus())
        assert second.read_snapshot(snapshot.snapshot_id) == snapshot
        assert [e.event for e in second.audit(RUN_ID).events()] == ["started"]


def test_foreign_keys_are_enforced_through_the_api(
    store: Blackboard, config: RunConfig
) -> None:
    """A coding cannot name a snapshot or a response that is not in the store."""
    store.register_run(config)
    with pytest.raises(sqlite3.IntegrityError):
        store.write_coding(
            run_id=RUN_ID, response_id=203, source=SOURCE, coder="coder_a",
            snapshot_id="snap-nonexistent", prompt_version="coder-v1",
        )
