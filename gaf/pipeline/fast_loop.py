"""The fast loop — the one control flow the whole design exists to keep simple.

Per response, in this exact order::

    response + its survey question
      -> deterministic prep: segmentation, dedup check, context assembly
         (top-k codes by embedding + hierarchy skeleton, from a FROZEN snapshot)
      -> Coder A and Coder B, independently, on IDENTICAL context
      -> STRUCTURAL checks S1-S6   (deterministic; S1/S2 drop, the rest flag)
      -> SEMANTIC checks M1-M4     (embedding-first; judge only in the grey zone)
      -> agree? accept | disagree / grey zone? -> Judge
      -> integrate (auto-merge / auto-create / judge-decided)
      -> write to the blackboard

That is the whole of `_code_response`, and it is meant to be read straight through.
Everything else in this module is infrastructure — batching, the store writes, the
audit log, the accounting — which is where the design law says complexity may live.

Four properties this module is responsible for holding up.

**Frozen snapshots.** The coders read a snapshot id and never the working codebook, so
what a coder can see for a given batch is fixed before the batch starts. Integration
accumulates into the working codebook *within* the batch, and the loop freezes a new
snapshot at each batch boundary (`RunConfig.snapshot_policy`, `batch_size`). Re-running
a batch from the same starting codebook therefore reproduces the same output, which is
the mechanism against order dependence.

**Both coders get identical context.** Prep builds one `CoderContext` and both agents
are handed that same object; B1 guarantees the two `LLMRequest`s are then byte-identical.
No retrieval, ordering or wording differs between them, because their disagreement is
the router's escalation signal and any asymmetry would make it a measurement of the
prompt instead.

**Integration is not restructuring.** `gaf.pipeline.router.integrate` is the only
function here that changes the codebook, and it has two branches: attach evidence to an
existing code, or admit a new one. Splitting, re-parenting and batch-renaming are
slow-loop operations behind the human gate and have no implementation in this module.

**Determinism is an acceptance criterion.** Responses are processed in a total order,
ids are content hashes, evidence is content-ordered, codebook JSON carries no wall clock
(ADR-0007), and the mock clients and the lexical embedder are pure functions of their
input. Two runs over the same corpus with the same config produce byte-identical
codebook JSON and an identical snapshot-id sequence; `tests/test_fast_loop.py` asserts
exactly that.

Reading the offline numbers: ADR-0019. In the lexical fallback space M3 escalates
almost every quote and M2's grey zone is empty, so an offline run's routing and fit
statistics describe the stand-in embedder rather than the coding. `RunStats.caveats`
carries that sentence into the run report rather than leaving it to be rediscovered.

Validation principles: **reliability** — one deterministic order, frozen snapshots and
content-addressed ids make a run replayable; **transparency** — every decision, drop,
escalation and merge is an audit row carrying the inputs that produced it.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from gaf.agents.coder import CoderAgent, CodingProposal, subject_for
from gaf.agents.judge import JudgeAgent
from gaf.checks.contracts import CheckFinding, CheckReport, Severity
from gaf.checks.semantic import (
    Judge,
    check_code_evidence_fit,
    check_cross_coder_agreement,
    check_integration_routing,
    check_near_duplicate_leaves,
)
from gaf.checks.structural import MARKER_KEY, check_candidates, check_codebook
from gaf.config import RunConfig
from gaf.embed.protocol import Embedder, Route
from gaf.embed.service import EmbeddingService
from gaf.llm.base import CallLog, LLMClient
from gaf.llm.cache import CachingLLMClient
from gaf.llm.mock import MockCoderClient, MockJudgeClient
from gaf.models import Assignment, Candidate, Code, Codebook, Response
from gaf.pipeline import prep, router
from gaf.pipeline.prep import PreparedResponse
from gaf.pipeline.router import ORIGINS, AcceptanceResult, IntegrationDecision
from gaf.store.blackboard import AssignmentRecord, Blackboard
from gaf.store.snapshot import Snapshot

__all__ = [
    "FastLoopResult",
    "LoopComponents",
    "ResponseOutcome",
    "RunStats",
    "batches",
    "offline_components",
    "run_fast_loop",
]

#: The checks whose ERROR findings *drop* a candidate. S4's ERROR is keep-and-flag, so
#: it is deliberately absent: "dropped" in the audit log means dropped.
_DROPPING_CHECKS: tuple[str, ...] = ("S1", "S2")

#: ADR-0019, carried into the run report so that a wall of offline M3 warnings is never
#: read as a wall of findings about the coding.
_OFFLINE_CAVEAT = (
    "Offline run: M3's code-to-evidence fit does not discriminate in the lexical "
    "fallback space (median fit 0.000) and M2's grey zone is empty, so the fit and "
    "routing statistics are artefacts of the stand-in embedder rather than findings "
    "about the coding. See ADR-0019."
)


# --------------------------------------------------------------------------- #
# Components
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class LoopComponents:
    """The four things the loop needs from outside itself, wired to one call log.

    Injected rather than constructed inside the loop, so a test can supply a stub judge
    or a stub embedder without a factory. `call_log` must be the same object the agents
    were built with — `run_fast_loop` checks that — because the loop drains that log
    after each call site to write the `llm_calls` accounting rows.
    """

    coder_a: CoderAgent
    coder_b: CoderAgent
    embedder: Embedder
    judge: Judge | None = None
    call_log: CallLog = field(default_factory=CallLog)

    @property
    def judge_available(self) -> bool:
        """Whether a frontier call is possible at all. Offline runs answer False."""
        return self.judge is not None


def offline_components(config: RunConfig, *, call_log: CallLog | None = None) -> LoopComponents:
    """Build the offline triple: two mock coders, a mock judge, the lexical embedder.

    The offline path is the default path and the only one tests and CI ever take. A
    live run injects its own `LoopComponents`: provider clients are opt-in extras, and
    this module does not import them, so a clean clone runs the whole loop with no key,
    no network and no provider SDK.
    """
    if not config.offline:
        raise ValueError(
            "offline_components builds the mock triple; a live run must construct its "
            "own LoopComponents with real clients and inject them."
        )
    log = call_log or CallLog()
    coder_a = _cached(MockCoderClient(config.models.coder_a, rules=config.rules), config)
    coder_b = _cached(MockCoderClient(config.models.coder_b, rules=config.rules), config)
    judge = _cached(MockJudgeClient(config.models.judge), config)
    return LoopComponents(
        coder_a=CoderAgent(coder_a, config=config, call_log=log),
        coder_b=CoderAgent(coder_b, config=config, call_log=log),
        embedder=EmbeddingService(config.embedding),
        judge=JudgeAgent(judge, config=config, call_log=log),
        call_log=log,
    )


def _cached(client: LLMClient, config: RunConfig) -> LLMClient:
    """Wrap a client in the on-disk cache when the run asks for one."""
    return client if config.cache_dir is None else CachingLLMClient(client, config.cache_dir)


def _check_shared_call_log(components: LoopComponents) -> None:
    """Every agent must record into `components.call_log`, or accounting silently lies.

    Checked rather than documented: an agent wired to a different log would produce a
    run whose `llm_calls` table is empty while its cost is real, and a cost that is not
    in the store is a cost the run report cannot defend.
    """
    for agent in (components.coder_a, components.coder_b, components.judge):
        log = getattr(agent, "call_log", None)
        if log is not None and log is not components.call_log:
            raise ValueError(
                "every agent in LoopComponents must be constructed with "
                "LoopComponents.call_log; use offline_components(), or pass the same "
                "CallLog to each agent."
            )


# --------------------------------------------------------------------------- #
# Result surface — what agent C2 builds the run report from
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class ResponseOutcome:
    """What the loop did with one response. Serialisable, and one row of the report."""

    response_id: int
    snapshot_id: str
    content_hash: str
    n_segments: int
    duplicate_of: int | None
    proposed: dict[str, int]
    survived: dict[str, int]
    agreement_rate: float
    acceptance: dict[str, Any]
    fit: dict[str, Any]
    routing: dict[str, Any]
    decisions: list[dict[str, Any]]
    created: list[str]
    merged: list[str]
    assignments: list[AssignmentRecord] = field(default_factory=list)
    report: CheckReport = field(default_factory=CheckReport)

    def to_json(self) -> dict[str, Any]:
        """The row form. The findings themselves live once, on the run's report."""
        return {
            "response_id": self.response_id,
            "snapshot_id": self.snapshot_id,
            "content_hash": self.content_hash,
            "n_segments": self.n_segments,
            "duplicate_of": self.duplicate_of,
            "proposed": dict(self.proposed),
            "survived": dict(self.survived),
            "agreement_rate": self.agreement_rate,
            "acceptance": dict(self.acceptance),
            "fit": dict(self.fit),
            "routing": dict(self.routing),
            "decisions": list(self.decisions),
            "created": list(self.created),
            "merged": list(self.merged),
            "n_assignments": len(self.assignments),
            "findings": self.report.summary(),
        }


@dataclass(frozen=True, slots=True)
class RunStats:
    """Every number the run report prints about a fast-loop run.

    Flat and JSON-shaped on purpose: `gaf.report` reads this, never the loop's internals.
    """

    run_id: str
    offline: bool
    space_id: str
    n_responses: int
    n_duplicate_responses: int
    n_segments: int
    candidates_proposed: dict[str, int]
    candidates_survived: dict[str, int]
    candidates_dropped: dict[str, int]
    candidates_accepted: int
    acceptance_by_origin: dict[str, int]
    agreement_rate: float
    routes: dict[str, int]
    actions: dict[str, int]
    escalations: int
    judge_calls: dict[str, int]
    codes_created: int
    codes_final: int
    families_final: int
    assignments: int
    findings: dict[str, dict[str, int]]
    severities: dict[str, int]
    llm: dict[str, Any]
    snapshot_ids: list[str]
    caveats: list[str]

    def to_json(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "offline": self.offline,
            "space_id": self.space_id,
            "n_responses": self.n_responses,
            "n_duplicate_responses": self.n_duplicate_responses,
            "n_segments": self.n_segments,
            "candidates_proposed": dict(self.candidates_proposed),
            "candidates_survived": dict(self.candidates_survived),
            "candidates_dropped": dict(self.candidates_dropped),
            "candidates_accepted": self.candidates_accepted,
            "acceptance_by_origin": dict(self.acceptance_by_origin),
            "agreement_rate": self.agreement_rate,
            "routes": dict(self.routes),
            "actions": dict(self.actions),
            "escalations": self.escalations,
            "judge_calls": dict(self.judge_calls),
            "codes_created": self.codes_created,
            "codes_final": self.codes_final,
            "families_final": self.families_final,
            "assignments": self.assignments,
            "findings": {check: dict(counts) for check, counts in self.findings.items()},
            "severities": dict(self.severities),
            "llm": dict(self.llm),
            "snapshot_ids": list(self.snapshot_ids),
            "caveats": list(self.caveats),
        }


@dataclass(frozen=True, slots=True)
class FastLoopResult:
    """The fast loop's whole output: the codebook, the rows, the findings, the numbers."""

    run_id: str
    codebook: Codebook
    assignments: list[Assignment]
    report: CheckReport
    snapshot_ids: list[str]
    stats: RunStats
    outcomes: list[ResponseOutcome] = field(default_factory=list)

    def codebook_json(self) -> str:
        """The canonical codebook serialisation — the bytes two runs must agree on."""
        return self.codebook.to_json_str()

    def passed(self) -> bool:
        """True when the run produced no ERROR finding. The CLI's exit-code question."""
        return self.report.passed()

    def to_json(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "codebook": self.codebook.to_json(),
            "assignments": [assignment.to_json() for assignment in self.assignments],
            "findings": self.report.to_json(),
            "snapshot_ids": list(self.snapshot_ids),
            "stats": self.stats.to_json(),
            "responses": [outcome.to_json() for outcome in self.outcomes],
        }


# --------------------------------------------------------------------------- #
# The recorder — every write the loop makes, in one place
# --------------------------------------------------------------------------- #


class _Recorder:
    """The store, the audit log and the call accounting behind one small surface.

    The loop decides; this writes. Keeping the writes here is what lets
    `_code_response` read as the flow diagram rather than as bookkeeping, and it is the
    only object in the fast loop that touches the database.
    """

    __slots__ = ("_board", "_config", "_cursor", "log")

    def __init__(self, board: Blackboard, config: RunConfig) -> None:
        self._board = board
        self._config = config
        self.log = board.audit(config.run_id)
        self._cursor = 0

    @property
    def run_id(self) -> str:
        return self._config.run_id

    def emit(self, event: str, **kwargs: Any) -> None:
        self.log.emit(event, **kwargs)

    # -- model-call accounting -------------------------------------------- #

    def drain(self, call_log: CallLog, *, role: str, subject: str) -> int:
        """Write every model call made since the last drain; return how many.

        `LLMResult` carries no subject of its own, so the caller supplies the one the
        run report wants — the response the call was made about.
        """
        pending = call_log.results[self._cursor :]
        self._cursor = len(call_log.results)
        for result in pending:
            self._board.write_llm_call(result, run_id=self.run_id, role=role, subject=subject)
        return len(pending)

    # -- snapshots -------------------------------------------------------- #

    def snapshot(self, codebook: Codebook, *, parent_id: str | None, reason: str) -> Snapshot:
        snapshot = self._board.freeze_codebook(
            codebook, run_id=self.run_id, parent_id=parent_id, reason=reason
        )
        self.emit(
            "snapshot_frozen",
            scope="codebook",
            subject=snapshot.snapshot_id,
            snapshot_id=snapshot.snapshot_id,
            parent_id=parent_id,
            reason=reason,
            code_count=snapshot.code_count,
        )
        return snapshot

    # -- prep, codings, candidates ---------------------------------------- #

    def prepared(self, prepared: PreparedResponse) -> None:
        self.emit(
            "response_prepared",
            scope="response",
            subject=str(prepared.response.id),
            snapshot_id=prepared.snapshot_id,
            **_payload(prepared.to_json()),
        )
        if prepared.dedup.is_duplicate:
            self.emit(
                "duplicate_response",
                scope="response",
                subject=str(prepared.response.id),
                snapshot_id=prepared.snapshot_id,
                duplicate_of=prepared.dedup.duplicate_of,
                content_hash=prepared.dedup.content_hash,
            )

    def coding(
        self,
        prepared: PreparedResponse,
        agent: CoderAgent,
        proposal: CodingProposal,
    ) -> dict[str, str]:
        """Record one coder's pass and its candidates; return ``name -> candidate_id``.

        Every proposed candidate becomes a row, including the ones S1 and S2 are about
        to drop: what a coder proposed is a fact about the run, and the router's later
        verdict is written onto the same row rather than replacing it.
        """
        response = prepared.response
        record = self._board.write_coding(
            run_id=self.run_id,
            response_id=response.id,
            source=response.source,
            coder=agent.coder,
            snapshot_id=prepared.snapshot_id,
            prompt_version=proposal.prompt_version,
            raw=proposal.raw(),
        )
        rows = self._board.write_candidates(record.coding_id, proposal.candidates)
        self.emit(
            "coding_proposed",
            scope="response",
            subject=str(response.id),
            snapshot_id=prepared.snapshot_id,
            coder=agent.coder,
            coding_id=record.coding_id,
            prompt_version=proposal.prompt_version,
            n_candidates=len(proposal.candidates),
            candidates=[candidate.name for candidate in proposal.candidates],
            fail_safe=proposal.fail_safe,
        )
        index: dict[str, str] = {}
        for row in rows:
            index.setdefault(row.candidate.name, row.candidate_id)
        return index

    def resolve(
        self,
        index: Mapping[str, str],
        name: str,
        *,
        status: str,
        resolution: str,
        code_id: str | None = None,
    ) -> None:
        """Write what became of one proposed candidate. The router's verdict, not a check's."""
        candidate_id = index.get(name)
        if candidate_id is not None:
            self._board.update_candidate(
                candidate_id, status=status, resolution=resolution, code_id=code_id
            )

    def dropped(
        self,
        prepared: PreparedResponse,
        name: str,
        *,
        coder: str,
        check_id: str,
        marker: str,
        message: str,
    ) -> None:
        self.emit(
            "candidate_dropped",
            scope="candidate",
            subject=name,
            snapshot_id=prepared.snapshot_id,
            response_id=prepared.response.id,
            coder=coder,
            check_id=check_id,
            marker=marker,
            message=message,
        )

    def dispute_drops(
        self,
        prepared: PreparedResponse,
        acceptance: AcceptanceResult,
        indexes: Mapping[str, Mapping[str, str]],
    ) -> None:
        """Audit and resolve the candidates a judge ruled DROP on. The only M1 removal."""
        for item in acceptance.dropped:
            self.dropped(
                prepared,
                item.name,
                coder=item.candidate.coder,
                check_id="M1",
                marker="judge_dispute_drop",
                message=item.reasoning or "the judge ruled DROP on a grey-zone disagreement",
            )
            self.resolve(
                indexes.get(item.candidate.coder, {}),
                item.name,
                status="dropped",
                resolution="M1:judge_dispute_drop",
            )

    def fit_drops(self, prepared: PreparedResponse, dropped: Sequence[str]) -> None:
        """Audit the candidates M3 emptied of evidence. No coder owns these: the ruling
        is about the code-to-quote pairing, not about who proposed it."""
        for name in dropped:
            self.dropped(
                prepared,
                name,
                coder="",
                check_id="M3",
                marker="candidate_dropped_no_evidence",
                message="every verified quote was ruled UNNECESSARY",
            )

    def resolve_all(
        self,
        indexes: Mapping[str, Mapping[str, str]],
        proposers: Sequence[tuple[str, str]],
        *,
        status: str,
        resolution: str,
        code_id: str | None = None,
    ) -> None:
        """Write one outcome onto every proposed row behind one accepted candidate."""
        for coder, name in proposers:
            self.resolve(
                indexes.get(coder, {}), name, status=status, resolution=resolution, code_id=code_id
            )

    def structural_drops(
        self, prepared: PreparedResponse, report: CheckReport, *, coder: str, index: Mapping[str, str]
    ) -> None:
        """Audit and resolve every candidate S1 or S2 removed, and why."""
        for finding in _drop_findings(report):
            self.dropped(
                prepared,
                finding.subject,
                coder=coder,
                check_id=finding.check_id,
                marker=str(finding.data.get(MARKER_KEY, "")),
                message=finding.message,
            )
            self.resolve(
                index,
                finding.subject,
                status="dropped",
                resolution=f"{finding.check_id}:{finding.data.get(MARKER_KEY, '')}",
            )

    # -- router decisions -------------------------------------------------- #

    def acceptance(self, prepared: PreparedResponse, acceptance: AcceptanceResult) -> None:
        self.emit(
            "candidates_accepted",
            scope="response",
            subject=str(prepared.response.id),
            snapshot_id=prepared.snapshot_id,
            **acceptance.stats(),
            accepted=[item.to_json() for item in acceptance.accepted],
            dropped=[item.to_json() for item in acceptance.dropped],
        )
        for item in acceptance.escalated():
            self.emit(
                "judge_consulted",
                scope="pair",
                subject=f"{item.name}<->{item.counterpart}",
                snapshot_id=prepared.snapshot_id,
                check_id="M1",
                score=item.score,
                band=item.band,
                verdict=item.verdict,
                reasoning=item.reasoning,
            )

    def integrated(
        self,
        prepared: PreparedResponse,
        decision: IntegrationDecision,
        code: Code,
        action: Route,
    ) -> None:
        if decision.escalated:
            self.emit(
                "judge_consulted",
                scope="candidate",
                subject=decision.candidate_name,
                snapshot_id=prepared.snapshot_id,
                check_id="M2",
                score=decision.score,
                band=decision.route.value,
                verdict=decision.verdict,
                reasoning=decision.reasoning,
            )
        self.emit(
            "route_chosen",
            scope="candidate",
            subject=decision.candidate_name,
            snapshot_id=prepared.snapshot_id,
            response_id=prepared.response.id,
            code_id=code.id,
            code_name=code.name,
            applied=action.value,
            **_payload(decision.to_json()),
        )
        self.emit(
            "code_created" if action is Route.CREATE else "code_merged",
            scope="codebook",
            subject=code.name,
            snapshot_id=prepared.snapshot_id,
            response_id=prepared.response.id,
            code_id=code.id,
            candidate_name=decision.candidate_name,
            score=decision.score,
            route=decision.route.value,
            n_evidence=len(code.evidence),
        )

    # -- rows -------------------------------------------------------------- #

    def assignment(
        self,
        prepared: PreparedResponse,
        code: Code,
        segment_text: str,
        span: tuple[int, int] | None,
    ) -> AssignmentRecord:
        """Write one occurrence row and return it with the provenance the flat form drops."""
        response = prepared.response
        return self._board.write_assignment(
            run_id=self.run_id,
            response_id=response.id,
            source=response.source,
            code_id=code.id,
            code_name=code.name,
            segment_text=segment_text,
            snapshot_id=prepared.snapshot_id,
            span=span,
        )

    def assignments_written(
        self, prepared: PreparedResponse, records: Sequence[AssignmentRecord]
    ) -> None:
        self.emit(
            "assignments_written",
            scope="response",
            subject=str(prepared.response.id),
            snapshot_id=prepared.snapshot_id,
            n_assignments=len(records),
            codes=sorted({record.code_name for record in records}),
        )

    def findings(
        self, report: CheckReport, *, response_id: int | None, snapshot_id: str
    ) -> None:
        ids = self._board.write_report(
            report, run_id=self.run_id, response_id=response_id, snapshot_id=snapshot_id
        )
        self.emit(
            "findings_recorded",
            scope="response" if response_id is not None else "codebook",
            subject=str(response_id) if response_id is not None else snapshot_id,
            snapshot_id=snapshot_id,
            summary=report.summary(),
            n_findings=len(ids),
            finding_ids=ids,
        )


def _payload(data: dict[str, Any]) -> dict[str, Any]:
    """An audit payload from a `to_json()` dict, minus the keys `emit` names itself.

    `AuditLog.emit` takes `snapshot_id` as a column rather than as payload, so spreading
    a serialisation that carries one would be a duplicate keyword. Dropped here rather
    than omitted from `to_json`, because a serialisation that hides its own snapshot id
    would be worse for every other reader.
    """
    return {key: value for key, value in data.items() if key != "snapshot_id"}


def _drop_findings(report: CheckReport) -> list[CheckFinding]:
    """The ERROR findings that actually removed a candidate (S1, S2)."""
    return [
        finding
        for finding in report.findings
        if finding.severity is Severity.ERROR and finding.check_id in _DROPPING_CHECKS
    ]


# --------------------------------------------------------------------------- #
# The loop
# --------------------------------------------------------------------------- #


def _code_response(
    response: Response,
    snapshot: Snapshot,
    codebook: Codebook,
    *,
    config: RunConfig,
    components: LoopComponents,
    recorder: _Recorder,
    seen: Mapping[str, int],
) -> tuple[ResponseOutcome, Codebook]:
    """One turn of the fast loop. Read this function top to bottom; it is the diagram."""
    rules, judge, embedder = config.rules, components.judge, components.embedder
    subject = subject_for(response.id)

    # 1 — deterministic prep: segmentation, dedup check, context assembly.
    prepared = prep.prepare(response, snapshot, embedder, config=config, seen=seen)
    recorder.prepared(prepared)

    # 2 — two coders, independently, on identical context.
    context = prepared.context
    proposal_a = components.coder_a.code(context)
    index_a = recorder.coding(prepared, components.coder_a, proposal_a)
    recorder.drain(components.call_log, role=components.coder_a.coder, subject=subject)
    proposal_b = components.coder_b.code(context)
    index_b = recorder.coding(prepared, components.coder_b, proposal_b)
    recorder.drain(components.call_log, role=components.coder_b.coder, subject=subject)

    # 3 — structural checks: S1 and S2 drop, S2b/S3/S4/S5 flag.
    existing = codebook.names()
    survivors_a, structural_a = check_candidates(proposal_a.candidates, response, existing, rules)
    survivors_b, structural_b = check_candidates(proposal_b.candidates, response, existing, rules)
    report = CheckReport()
    report.extend(structural_a)
    report.extend(structural_b)
    recorder.structural_drops(prepared, structural_a, coder=components.coder_a.coder, index=index_a)
    recorder.structural_drops(prepared, structural_b, coder=components.coder_b.coder, index=index_b)

    # 4 — M1: cross-coder agreement. The judge sees the grey zone and nothing else.
    agreement = check_cross_coder_agreement(
        survivors_a, survivors_b, embedder, rules, judge=judge, response_text=prepared.normalised
    )
    report.extend(agreement.report)
    recorder.drain(components.call_log, role="judge", subject=subject)

    # 5 — the router: what is accepted, and what reached the judge.
    acceptance = router.accept_candidates(
        agreement, survivors_a, survivors_b, judge_available=components.judge_available
    )
    indexes = {components.coder_a.coder: index_a, components.coder_b.coder: index_b}
    recorder.acceptance(prepared, acceptance)
    recorder.dispute_drops(prepared, acceptance, indexes)

    # 6 — M3: code<->evidence fit over the accepted set.
    fit = check_code_evidence_fit(
        acceptance.candidates(), [response], embedder, rules, judge=judge
    )
    report.extend(fit.report)
    recorder.drain(components.call_log, role="judge", subject=subject)
    recorder.fit_drops(prepared, fit.dropped)

    # 7 — M2: integration routing, against the working codebook of this batch.
    routing = check_integration_routing(
        fit.candidates, codebook, embedder, rules, judge=judge, top_k=config.retrieval_top_k
    )
    report.extend(routing.report)
    recorder.drain(components.call_log, role="judge", subject=subject)
    decisions = router.integration_actions(
        routing,
        snapshot_id=snapshot.snapshot_id,
        judge_available=components.judge_available,
    )

    # 8 — integrate: auto-merge or auto-create. Nothing splits, re-parents or renames.
    codebook, created, merged, rows = _integrate(
        codebook,
        decisions,
        fit.candidates,
        prepared=prepared,
        proposers=_proposers(acceptance),
        indexes=indexes,
        recorder=recorder,
    )

    # 9 — write to the blackboard.
    recorder.assignments_written(prepared, rows)
    recorder.findings(report, response_id=response.id, snapshot_id=snapshot.snapshot_id)

    outcome = ResponseOutcome(
        response_id=response.id,
        snapshot_id=snapshot.snapshot_id,
        content_hash=prepared.dedup.content_hash,
        n_segments=len(prepared.segments),
        duplicate_of=prepared.dedup.duplicate_of,
        proposed=_by_coder(components, proposal_a.candidates, proposal_b.candidates),
        survived=_by_coder(components, survivors_a, survivors_b),
        agreement_rate=agreement.agreement_rate,
        acceptance=acceptance.stats(),
        fit=fit.stats(),
        routing=routing.stats(),
        decisions=[decision.to_json() for decision in decisions],
        created=created,
        merged=merged,
        assignments=rows,
        report=report,
    )
    return outcome, codebook


def _by_coder(
    components: LoopComponents, left: Sequence[Any], right: Sequence[Any]
) -> dict[str, int]:
    """``{coder role: count}`` — the per-coder columns of the run report."""
    return {
        components.coder_a.coder: len(left),
        components.coder_b.coder: len(right),
    }


def _integrate(
    codebook: Codebook,
    decisions: Sequence[IntegrationDecision],
    candidates: Sequence[Candidate],
    *,
    prepared: PreparedResponse,
    proposers: Mapping[str, Sequence[tuple[str, str]]],
    indexes: Mapping[str, Mapping[str, str]],
    recorder: _Recorder,
) -> tuple[Codebook, list[str], list[str], list[AssignmentRecord]]:
    """Apply one response's integration decisions and emit its occurrence rows.

    Every codebook change goes through `gaf.pipeline.router.integrate`, whose two
    branches are the only two the fast loop has. One assignment row is written per
    verified quote of an integrated candidate, keyed by its content-addressed id so
    that two accepted candidates folding into one code do not double-count a span.
    """
    created: list[str] = []
    merged: list[str] = []
    rows: dict[str, AssignmentRecord] = {}
    for decision, candidate in zip(decisions, candidates, strict=True):
        codebook, code, action = router.integrate(
            codebook, decision, candidate, snapshot_id=prepared.snapshot_id
        )
        (created if action is Route.CREATE else merged).append(code.name)
        recorder.integrated(prepared, decision, code, action)
        recorder.resolve_all(
            indexes,
            proposers.get(candidate.name, ()),
            status="integrated",
            resolution=action.value,
            code_id=code.id,
        )
        for evidence in candidate.verified_evidence():
            text = _segment_text(prepared, evidence.span, evidence.quote)
            record = recorder.assignment(prepared, code, text, evidence.span)
            rows.setdefault(record.assignment_id, record)
    return codebook, created, merged, list(rows.values())


def _assignment_order(records: Iterable[AssignmentRecord]) -> list[AssignmentRecord]:
    """Occurrence-matrix order, matching `Blackboard.read_assignments` exactly.

    The in-memory rows and the stored rows must be the same list in the same order, or
    a caller reading one and a caller reading the other would build two different
    occurrence matrices from one run (ADR-0017).
    """
    return sorted(
        records,
        key=lambda record: (
            record.response_id,
            record.code_name,
            record.span[0] if record.span else -1,
            record.assignment_id,
        ),
    )


def _segment_text(prepared: PreparedResponse, span: tuple[int, int] | None, quote: str) -> str:
    """The assignment's segment: the located span of the **normalised** text.

    Not the coder's own string. S2 may have located a quote fuzzily, and the row that
    reaches the occurrence matrix and the golden-set comparison must be the text that is
    actually in the response — the same characters every span in the store indexes.
    """
    return quote if span is None else prepared.normalised[span[0] : span[1]]


def _proposers(acceptance: AcceptanceResult) -> dict[str, list[tuple[str, str]]]:
    """Accepted candidate name -> the ``(coder, proposed name)`` pairs behind it.

    An agreed candidate has two proposers and both rows are resolved with the same
    outcome; a disputed or unmatched one has a single proposer. Without this the
    agreeing coder's own row would be left saying "proposed" for a code that was
    admitted, and the store would understate the agreement it recorded.
    """
    proposers: dict[str, list[tuple[str, str]]] = {}
    for item in acceptance.accepted:
        entries = [(item.coders[0], item.candidate.name)]
        if item.origin == "agreed" and len(item.coders) > 1:
            entries.append((item.coders[1], item.counterpart))
        proposers.setdefault(item.candidate.name, []).extend(entries)
    return proposers


def batches(responses: Sequence[Response], size: int) -> list[list[Response]]:
    """Cut the corpus into snapshot batches. `size <= 0` means one batch."""
    if size <= 0:
        return [list(responses)]
    return [list(responses[start : start + size]) for start in range(0, len(responses), size)]


def _ordered(responses: Iterable[Response]) -> list[Response]:
    """The total processing order: by source, then by response id (ADR-0017).

    Deliberately not the caller's order. Two runs that read the corpus in different
    orders must still produce the same codebook, and the only way to promise that is to
    stop depending on the order the corpus arrived in.
    """
    return sorted(responses, key=lambda response: (response.source, response.id))


def run_fast_loop(
    responses: Sequence[Response],
    *,
    config: RunConfig,
    board: Blackboard,
    components: LoopComponents,
    codebook: Codebook | None = None,
) -> FastLoopResult:
    """Code a corpus: prep, two coders, checks, the router, integration, the store.

    Responses are processed in a total order and in batches of `config.batch_size`; a
    snapshot is frozen at the start of the run, at each batch boundary when
    `config.snapshot_policy` is ``"per_batch"``, and once more over the final codebook.
    The coders read those frozen snapshots; integration accumulates into the working
    codebook between them.

    `codebook` seeds the run — an empty one for a cold start, or the codebook a previous
    run or a slow-loop checkpoint left behind. It is never mutated: every integration
    step returns a new `Codebook`.

    The run ends with S6 over the final codebook and M4 over its leaves, folded into the
    same report, so that "the codebook this run produced is well formed" is answered by
    the same mechanism as everything else.
    """
    _check_shared_call_log(components)
    ordered = _ordered(responses)
    board.register_run(config)
    board.write_responses(ordered)
    recorder = _Recorder(board, config)
    recorder.emit(
        "run_started",
        scope="run",
        subject=config.run_id,
        n_responses=len(ordered),
        batch_size=config.batch_size,
        snapshot_policy=config.snapshot_policy,
        offline=config.offline,
        space_id=components.embedder.space_id,
        judge_available=components.judge_available,
        retrieval_top_k=config.retrieval_top_k,
    )

    working = codebook if codebook is not None else Codebook()
    report = CheckReport()
    outcomes: list[ResponseOutcome] = []
    rows: dict[str, AssignmentRecord] = {}
    seen: dict[str, int] = {}
    snapshot = recorder.snapshot(working, parent_id=None, reason="seed")
    snapshot_ids = [snapshot.snapshot_id]

    for number, batch in enumerate(batches(ordered, config.batch_size)):
        if number and config.snapshot_policy == "per_batch":
            snapshot = recorder.snapshot(working, parent_id=snapshot.snapshot_id, reason="batch")
            snapshot_ids.append(snapshot.snapshot_id)
        for response in batch:
            outcome, working = _code_response(
                response,
                snapshot,
                working,
                config=config,
                components=components,
                recorder=recorder,
                seen=seen,
            )
            seen.setdefault(outcome.content_hash, response.id)
            outcomes.append(outcome)
            report.extend(outcome.report)
            for record in outcome.assignments:
                rows.setdefault(record.assignment_id, record)

    closing = CheckReport()
    closing.extend(check_codebook(working, [response.id for response in ordered], config.rules))
    closing.extend(check_near_duplicate_leaves(working, components.embedder, config.rules).report)
    report.extend(closing)
    recorder.findings(closing, response_id=None, snapshot_id=snapshot.snapshot_id)

    snapshot = recorder.snapshot(working, parent_id=snapshot.snapshot_id, reason="batch")
    snapshot_ids.append(snapshot.snapshot_id)

    ordered_assignments = [record.to_assignment() for record in _assignment_order(rows.values())]
    stats = _stats(
        config=config,
        components=components,
        outcomes=outcomes,
        report=report,
        codebook=working,
        assignments=ordered_assignments,
        snapshot_ids=snapshot_ids,
    )
    recorder.emit(
        "run_completed",
        scope="run",
        subject=config.run_id,
        snapshot_id=snapshot.snapshot_id,
        **stats.to_json(),
    )
    return FastLoopResult(
        run_id=config.run_id,
        codebook=working,
        assignments=ordered_assignments,
        report=report,
        snapshot_ids=snapshot_ids,
        stats=stats,
        outcomes=outcomes,
    )


# --------------------------------------------------------------------------- #
# Statistics
# --------------------------------------------------------------------------- #


def _stats(
    *,
    config: RunConfig,
    components: LoopComponents,
    outcomes: Sequence[ResponseOutcome],
    report: CheckReport,
    codebook: Codebook,
    assignments: Sequence[Assignment],
    snapshot_ids: Sequence[str],
) -> RunStats:
    """Fold the per-response outcomes into the run report's numbers. Pure."""
    proposed: Counter[str] = Counter()
    survived: Counter[str] = Counter()
    origins = dict.fromkeys(ORIGINS, 0)
    routes = {route.value: 0 for route in Route}
    actions = {Route.MERGE.value: 0, Route.CREATE.value: 0}
    dropped = {"structural": 0, "dispute": 0, "fit": 0}
    escalations = 0
    accepted = 0
    created = 0

    for outcome in outcomes:
        proposed.update(outcome.proposed)
        survived.update(outcome.survived)
        for origin, count in outcome.acceptance["by_origin"].items():
            origins[origin] = origins.get(origin, 0) + count
        for route, count in outcome.routing["counts"].items():
            routes[route] = routes.get(route, 0) + count
        for decision in outcome.decisions:
            actions[decision["action"]] += 1
            escalations += int(decision["escalated"])
        escalations += int(outcome.acceptance["n_escalated"]) + int(outcome.fit["n_escalated"])
        accepted += int(outcome.acceptance["n_accepted"])
        created += len(outcome.created)
        dropped["structural"] += sum(outcome.proposed.values()) - sum(outcome.survived.values())
        dropped["dispute"] += int(outcome.acceptance["n_dropped"])
        dropped["fit"] += len(outcome.fit["dropped"])

    rates = [outcome.agreement_rate for outcome in outcomes]
    calls = components.call_log.by_task()
    return RunStats(
        run_id=config.run_id,
        offline=config.offline,
        space_id=components.embedder.space_id,
        n_responses=len(outcomes),
        n_duplicate_responses=sum(1 for o in outcomes if o.duplicate_of is not None),
        n_segments=sum(o.n_segments for o in outcomes),
        candidates_proposed=dict(sorted(proposed.items())),
        candidates_survived=dict(sorted(survived.items())),
        candidates_dropped=dropped,
        candidates_accepted=accepted,
        acceptance_by_origin=origins,
        agreement_rate=round(sum(rates) / len(rates), 6) if rates else 0.0,
        routes=routes,
        actions=actions,
        escalations=escalations,
        judge_calls={
            task: count for task, count in calls.items() if task.startswith("judge_")
        },
        codes_created=created,
        codes_final=len(codebook),
        families_final=len(codebook.families()),
        assignments=len(assignments),
        findings=report.summary(),
        severities=report.totals(),
        llm=components.call_log.summary(),
        snapshot_ids=list(snapshot_ids),
        caveats=[_OFFLINE_CAVEAT] if config.offline else [],
    )
