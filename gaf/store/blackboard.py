"""The blackboard — the repository API over `gaf.store.schema`.

All state lives here. Every model call in the pipeline is stateless and re-grounds
from this store, and every handoff between stages carries ids rather than prose: that
is the mechanism against the context loss the predecessor design suffered when state
lived in the text passed along an agent chain.

Three properties this module is responsible for holding up:

* **Deterministic ordering on every read.** Every query below carries an `ORDER BY`
  over a total, stable key. A read that returned rows in whatever order the b-tree
  offered would silently break byte-identical output downstream, and would do so
  intermittently, which is the worst kind of broken.
* **Content-addressed writes.** Ids come from `gaf.ids`, never from a counter, with
  the single exception of `audit.event_id`, which the database assigns because the
  log's ordering *is* its insertion order.
* **Immutable rows stay immutable.** Snapshots and audit rows are protected by
  database triggers; responses and codings are written with "already there means
  already the same" semantics, and a genuine content conflict raises rather than
  being reconciled.

This module writes to every table except `audit`, which only `gaf.store.audit` writes
to; `blackboard.audit(run_id)` hands out the log for a run.

Validation principle: **transparency** — every artefact is a row with the ids that
produced it; **reliability** — the same inputs write the same rows with the same ids,
and read back in the same order.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from types import TracebackType
from typing import Any

from gaf import __version__
from gaf.checks.contracts import CheckFinding, CheckReport, Severity
from gaf.config import RunConfig
from gaf.ids import (
    assignment_id as mint_assignment_id,
)
from gaf.ids import (
    candidate_id as mint_candidate_id,
)
from gaf.ids import (
    checkpoint_id as mint_checkpoint_id,
)
from gaf.ids import (
    coding_id as mint_coding_id,
)
from gaf.ids import (
    content_hash,
)
from gaf.ids import (
    finding_id as mint_finding_id,
)
from gaf.ids import (
    llm_call_id as mint_llm_call_id,
)
from gaf.llm.base import LLMResult
from gaf.models import Assignment, Candidate, Codebook, Evidence, Operation, Response
from gaf.store.audit import AuditLog, utc_now_iso
from gaf.store.schema import apply_schema
from gaf.store.snapshot import Snapshot
from gaf.store.snapshot import freeze as freeze_snapshot
from gaf.store.snapshot import latest_snapshot as _latest_snapshot
from gaf.store.snapshot import read_snapshot as _read_snapshot
from gaf.store.snapshot import read_snapshots as _read_snapshots
from gaf.store.snapshot import snapshot_exists as _snapshot_exists
from gaf.store.snapshot import write_snapshot as _write_snapshot
from gaf.textnorm import NORMALISATION_VERSION

__all__ = [
    "AssignmentRecord",
    "Blackboard",
    "CandidateRecord",
    "CheckpointRecord",
    "CodingRecord",
    "HealthMetric",
    "LLMCallRecord",
    "RunRecord",
    "StoreConflictError",
]


class StoreConflictError(ValueError):
    """A row that is supposed to be immutable was re-written with different content."""


def _dumps(obj: Any) -> str:
    """Canonical JSON for a stored column: sorted keys, no ASCII escaping."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False)


# --------------------------------------------------------------------------- #
# Row records
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class RunRecord:
    """One execution of the pipeline, with the full config that produced it."""

    run_id: str
    created_at: str
    gaf_version: str
    offline: bool
    config: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CodingRecord:
    """One coder's pass over one response, against one snapshot."""

    coding_id: str
    run_id: str
    response_id: int
    source: str
    coder: str
    snapshot_id: str
    prompt_version: str
    created_at: str
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CandidateRecord:
    """A proposed candidate and what became of it.

    `candidate.raw` is **not** round-tripped: the model's original object is stored
    once, on the parent coding's `raw_json`, rather than copied onto every candidate
    it produced. `candidate.coder` is recovered by joining the coding.
    """

    candidate_id: str
    coding_id: str
    candidate: Candidate
    status: str
    resolution: str
    code_id: str | None
    created_at: str


@dataclass(frozen=True, slots=True)
class AssignmentRecord:
    """One row of the occurrence table, with the provenance the flat form drops."""

    assignment_id: str
    run_id: str
    response_id: int
    source: str
    code_id: str
    code_name: str
    segment_text: str
    span: tuple[int, int] | None
    norm_version: str
    snapshot_id: str
    created_at: str

    def to_assignment(self) -> Assignment:
        """The flat `gaf.models.Assignment` the analysis tail and agreement work on."""
        return Assignment(
            response_id=self.response_id, segment=self.segment_text, code=self.code_name
        )


@dataclass(frozen=True, slots=True)
class LLMCallRecord:
    """Per-call model accounting, as read back for the run report."""

    call_id: str
    run_id: str
    role: str
    task: str
    provider: str
    model: str
    prompt_version: str
    subject: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: float
    cache_hit: bool
    fail_safe: bool
    created_at: str


@dataclass(frozen=True, slots=True)
class CheckpointRecord:
    """One slow-loop checkpoint: the proposal, the human decision, the result."""

    checkpoint_id: str
    run_id: str
    at_response_count: int
    trigger: str
    base_snapshot_id: str
    proposal: dict[str, Any]
    decisions: list[dict[str, Any]]
    status: str
    result_snapshot_id: str | None
    created_at: str
    decided_at: str | None

    def operations(self) -> list[Operation]:
        """The proposed edit script, validated against `gaf.models.OPERATION_TYPES`."""
        return [Operation.from_json(op) for op in self.proposal.get("operations", [])]


@dataclass(frozen=True, slots=True)
class HealthMetric:
    """One codebook-health or saturation sample, taken at a response count."""

    run_id: str
    at_response_count: int
    metric: str
    value: float
    created_at: str


# --------------------------------------------------------------------------- #
# The store
# --------------------------------------------------------------------------- #


class Blackboard:
    """A connection to one blackboard database, with the repository API over it.

    Use as a context manager::

        with Blackboard(path) as store:
            store.register_run(config)

    `path` may be a filesystem path or ``":memory:"``. Parent directories of a file
    path are created; `apply_schema` (which also applies the pragmas, including the
    `foreign_keys` one that SQLite leaves off by default) runs on every connect and is
    idempotent, so opening an existing database is the same call as creating one.
    """

    __slots__ = ("_conn", "path")

    def __init__(self, path: Path | str = ":memory:") -> None:
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path)
        apply_schema(self._conn)

    # -- lifecycle -------------------------------------------------------- #

    @property
    def conn(self) -> sqlite3.Connection:
        """The underlying connection. Read-only use, please: writes go through the API."""
        return self._conn

    def close(self) -> None:
        self._conn.commit()
        self._conn.close()

    def __enter__(self) -> Blackboard:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    def audit(self, run_id: str) -> AuditLog:
        """The append-only log for `run_id`. The only writer to the `audit` table."""
        return AuditLog(self._conn, run_id)

    # -- runs ------------------------------------------------------------- #

    def register_run(
        self,
        config: RunConfig,
        *,
        gaf_version: str = __version__,
        created_at: str | None = None,
    ) -> RunRecord:
        """Register a run from its `RunConfig`, storing the config verbatim.

        Idempotent for an identical config — re-opening a store and re-registering the
        same run is a no-op. A *different* config under the same run id raises: two
        different configurations sharing a run id would make the run report a lie.
        """
        config_json = _dumps(config.to_json())
        existing = self._conn.execute(
            "SELECT run_id, created_at, gaf_version, offline, config_json FROM runs WHERE run_id = ?",
            (config.run_id,),
        ).fetchone()
        if existing is not None:
            if str(existing[4]) != config_json:
                raise StoreConflictError(
                    f"run {config.run_id!r} is already registered with a different "
                    "config; use a new run_id rather than re-defining an existing run."
                )
            return _row_to_run(existing)
        stamp = created_at or utc_now_iso()
        self._conn.execute(
            "INSERT INTO runs(run_id, created_at, gaf_version, offline, config_json) "
            "VALUES (?, ?, ?, ?, ?)",
            (config.run_id, stamp, gaf_version, int(config.offline), config_json),
        )
        self._conn.commit()
        return RunRecord(
            run_id=config.run_id,
            created_at=stamp,
            gaf_version=gaf_version,
            offline=config.offline,
            config=json.loads(config_json),
        )

    def read_run(self, run_id: str) -> RunRecord | None:
        row = self._conn.execute(
            "SELECT run_id, created_at, gaf_version, offline, config_json FROM runs WHERE run_id = ?",
            (run_id,),
        ).fetchone()
        return None if row is None else _row_to_run(row)

    def runs(self) -> list[RunRecord]:
        """Every run, oldest first; `run_id` breaks ties so the order is total."""
        rows = self._conn.execute(
            "SELECT run_id, created_at, gaf_version, offline, config_json FROM runs "
            "ORDER BY created_at, run_id"
        )
        return [_row_to_run(row) for row in rows]

    # -- responses -------------------------------------------------------- #

    def write_response(self, response: Response) -> str:
        """Persist one response and return its content hash.

        `meta` is stored, and is read back only by the analysis tail: respondent
        metadata is joined after coding and is never passed to a model.
        """
        digest = content_hash(response.content)
        row = self._conn.execute(
            "SELECT content_hash FROM responses WHERE response_id = ? AND source = ?",
            (response.id, response.source),
        ).fetchone()
        if row is not None:
            if str(row[0]) != digest:
                raise StoreConflictError(
                    f"response {response.id} of source {response.source!r} is already "
                    "stored with different content; a corpus is immutable within a store."
                )
            return digest
        self._conn.execute(
            "INSERT INTO responses(response_id, source, question, content, content_hash, meta_json) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                response.id,
                response.source,
                response.question,
                response.content,
                digest,
                _dumps(response.meta),
            ),
        )
        self._conn.commit()
        return digest

    def write_responses(self, responses: Iterable[Response]) -> int:
        """Persist a corpus. Returns the number of records written or confirmed."""
        count = 0
        for response in responses:
            self.write_response(response)
            count += 1
        return count

    def read_responses(self, *, source: str | None = None) -> list[Response]:
        """The corpus, ordered by source then response id — never by insertion order."""
        sql = (
            "SELECT response_id, source, question, content, meta_json FROM responses"
        )
        params: tuple[Any, ...] = ()
        if source is not None:
            sql += " WHERE source = ?"
            params = (source,)
        sql += " ORDER BY source, response_id"
        return [_row_to_response(row) for row in self._conn.execute(sql, params)]

    def read_response(self, response_id: int, source: str) -> Response | None:
        row = self._conn.execute(
            "SELECT response_id, source, question, content, meta_json FROM responses "
            "WHERE response_id = ? AND source = ?",
            (response_id, source),
        ).fetchone()
        return None if row is None else _row_to_response(row)

    def response_count(self, *, source: str | None = None) -> int:
        if source is None:
            row = self._conn.execute("SELECT COUNT(*) FROM responses").fetchone()
        else:
            row = self._conn.execute(
                "SELECT COUNT(*) FROM responses WHERE source = ?", (source,)
            ).fetchone()
        return int(row[0])

    # -- snapshots -------------------------------------------------------- #

    def freeze_codebook(
        self,
        codebook: Codebook,
        *,
        run_id: str | None = None,
        parent_id: str | None = None,
        reason: str = "batch",
        created_at: str | None = None,
    ) -> Snapshot:
        """Freeze `codebook` and persist the resulting snapshot in one step."""
        snapshot = freeze_snapshot(codebook, parent_id=parent_id, reason=reason)
        return self.write_snapshot(snapshot, run_id=run_id, created_at=created_at)

    def write_snapshot(
        self,
        snapshot: Snapshot,
        *,
        run_id: str | None = None,
        created_at: str | None = None,
    ) -> Snapshot:
        """Persist a frozen snapshot; writing an identical one again is a no-op."""
        return _write_snapshot(
            self._conn, snapshot, run_id=run_id, created_at=created_at or utc_now_iso()
        )

    def read_snapshot(self, snapshot_id: str, *, verify: bool = True) -> Snapshot:
        """Load a snapshot, verifying by default that its content hashes to its id."""
        return _read_snapshot(self._conn, snapshot_id, verify=verify)

    def read_snapshots(self, *, run_id: str | None = None, verify: bool = True) -> list[Snapshot]:
        return _read_snapshots(self._conn, run_id=run_id, verify=verify)

    def latest_snapshot(self, run_id: str, *, verify: bool = True) -> Snapshot | None:
        """The snapshot a coder should read next, or None if the run has none yet."""
        return _latest_snapshot(self._conn, run_id, verify=verify)

    def snapshot_exists(self, snapshot_id: str) -> bool:
        return _snapshot_exists(self._conn, snapshot_id)

    # -- codings ---------------------------------------------------------- #

    def write_coding(
        self,
        *,
        run_id: str,
        response_id: int,
        source: str,
        coder: str,
        snapshot_id: str,
        prompt_version: str,
        raw: Mapping[str, Any] | None = None,
        created_at: str | None = None,
    ) -> CodingRecord:
        """Record one coder's pass. The id is a hash of everything that shaped it."""
        coding_id = mint_coding_id(
            run_id=run_id,
            response_id=response_id,
            source=source,
            coder=coder,
            snapshot_id=snapshot_id,
            prompt_version=prompt_version,
        )
        stamp = created_at or utc_now_iso()
        payload = dict(raw or {})
        self._conn.execute(
            "INSERT INTO codings(coding_id, run_id, response_id, source, coder, snapshot_id, "
            "prompt_version, created_at, raw_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(coding_id) DO NOTHING",
            (
                coding_id,
                run_id,
                response_id,
                source,
                coder,
                snapshot_id,
                prompt_version,
                stamp,
                _dumps(payload),
            ),
        )
        self._conn.commit()
        return CodingRecord(
            coding_id=coding_id,
            run_id=run_id,
            response_id=response_id,
            source=source,
            coder=coder,
            snapshot_id=snapshot_id,
            prompt_version=prompt_version,
            created_at=stamp,
            raw=payload,
        )

    def read_codings(
        self, run_id: str, *, response_id: int | None = None, coder: str | None = None
    ) -> list[CodingRecord]:
        """Codings for a run, ordered by response then coder then id."""
        sql = (
            "SELECT coding_id, run_id, response_id, source, coder, snapshot_id, "
            "prompt_version, created_at, raw_json FROM codings WHERE run_id = ?"
        )
        params: list[Any] = [run_id]
        if response_id is not None:
            sql += " AND response_id = ?"
            params.append(response_id)
        if coder is not None:
            sql += " AND coder = ?"
            params.append(coder)
        sql += " ORDER BY response_id, coder, coding_id"
        return [_row_to_coding(row) for row in self._conn.execute(sql, params)]

    def coded_response_count(self, run_id: str) -> int:
        """How many distinct responses this run has coded so far."""
        row = self._conn.execute(
            "SELECT COUNT(DISTINCT response_id) FROM codings WHERE run_id = ?", (run_id,)
        ).fetchone()
        return int(row[0])

    # -- candidates ------------------------------------------------------- #

    def write_candidate(
        self,
        coding_id: str,
        candidate: Candidate,
        *,
        ordinal: int = 0,
        status: str = "proposed",
        resolution: str = "",
        code_id: str | None = None,
        created_at: str | None = None,
    ) -> CandidateRecord:
        """Record one proposed candidate.

        `ordinal` distinguishes a coder proposing the same name twice in one pass —
        two rows, because that is two proposals and S6 has to be able to see both.
        """
        candidate_id = mint_candidate_id(coding_id=coding_id, name=candidate.name, ordinal=ordinal)
        stamp = created_at or utc_now_iso()
        self._conn.execute(
            "INSERT INTO candidates(candidate_id, coding_id, name, description, parent_hint, "
            "status, resolution, code_id, evidence_json, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(candidate_id) DO NOTHING",
            (
                candidate_id,
                coding_id,
                candidate.name,
                candidate.description,
                candidate.parent_hint,
                status,
                resolution,
                code_id,
                _dumps([e.to_json() for e in candidate.evidence]),
                stamp,
            ),
        )
        self._conn.commit()
        return CandidateRecord(
            candidate_id=candidate_id,
            coding_id=coding_id,
            candidate=candidate,
            status=status,
            resolution=resolution,
            code_id=code_id,
            created_at=stamp,
        )

    def write_candidates(
        self,
        coding_id: str,
        candidates: Sequence[Candidate],
        *,
        status: str = "proposed",
        created_at: str | None = None,
    ) -> list[CandidateRecord]:
        """Record a coder's whole proposal list, ordinals following list position."""
        return [
            self.write_candidate(
                coding_id, candidate, ordinal=index, status=status, created_at=created_at
            )
            for index, candidate in enumerate(candidates)
        ]

    def update_candidate(
        self,
        candidate_id: str,
        *,
        status: str,
        resolution: str = "",
        code_id: str | None = None,
    ) -> None:
        """Record what became of a candidate: the router's decision, not a checker's."""
        self._conn.execute(
            "UPDATE candidates SET status = ?, resolution = ?, code_id = ? WHERE candidate_id = ?",
            (status, resolution, code_id, candidate_id),
        )
        self._conn.commit()

    def read_candidates(
        self, *, coding_id: str | None = None, run_id: str | None = None
    ) -> list[CandidateRecord]:
        """Candidates for one coding or one whole run, deterministically ordered.

        The coder is recovered by joining `codings`, so the reconstructed
        `Candidate` carries the coder that proposed it.
        """
        sql = (
            "SELECT c.candidate_id, c.coding_id, c.name, c.description, c.parent_hint, "
            "c.status, c.resolution, c.code_id, c.evidence_json, c.created_at, "
            "g.coder, g.response_id FROM candidates c "
            "JOIN codings g ON g.coding_id = c.coding_id"
        )
        clauses: list[str] = []
        params: list[Any] = []
        if coding_id is not None:
            clauses.append("c.coding_id = ?")
            params.append(coding_id)
        if run_id is not None:
            clauses.append("g.run_id = ?")
            params.append(run_id)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY g.response_id, g.coder, c.name, c.candidate_id"
        return [_row_to_candidate(row) for row in self._conn.execute(sql, params)]

    # -- assignments ------------------------------------------------------ #

    def write_assignment(
        self,
        *,
        run_id: str,
        response_id: int,
        source: str,
        code_id: str,
        code_name: str,
        segment_text: str,
        snapshot_id: str,
        span: tuple[int, int] | None = None,
        norm_version: str = NORMALISATION_VERSION,
        created_at: str | None = None,
    ) -> AssignmentRecord:
        """Record that `code_name` was applied to this span of this response.

        `norm_version` is stored with the span because a span only means something
        against the normalisation that produced it (`gaf.textnorm`).
        """
        assignment_id = mint_assignment_id(
            run_id=run_id,
            response_id=response_id,
            source=source,
            code_id=code_id,
            segment_text=segment_text,
            snapshot_id=snapshot_id,
        )
        stamp = created_at or utc_now_iso()
        self._conn.execute(
            "INSERT INTO assignments(assignment_id, run_id, response_id, source, code_id, "
            "code_name, segment_text, span_start, span_end, norm_version, snapshot_id, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(assignment_id) DO NOTHING",
            (
                assignment_id,
                run_id,
                response_id,
                source,
                code_id,
                code_name,
                segment_text,
                None if span is None else span[0],
                None if span is None else span[1],
                norm_version,
                snapshot_id,
                stamp,
            ),
        )
        self._conn.commit()
        return AssignmentRecord(
            assignment_id=assignment_id,
            run_id=run_id,
            response_id=response_id,
            source=source,
            code_id=code_id,
            code_name=code_name,
            segment_text=segment_text,
            span=span,
            norm_version=norm_version,
            snapshot_id=snapshot_id,
            created_at=stamp,
        )

    def read_assignments(
        self, run_id: str, *, response_id: int | None = None
    ) -> list[AssignmentRecord]:
        """Assignments for a run, in occurrence-matrix order.

        Ordered by response, then code name, then span start, then id: a content
        ordering rather than an insertion ordering, so the matrix built from it is
        byte-identical whatever order the fast loop happened to finish responses in.
        """
        sql = (
            "SELECT assignment_id, run_id, response_id, source, code_id, code_name, "
            "segment_text, span_start, span_end, norm_version, snapshot_id, created_at "
            "FROM assignments WHERE run_id = ?"
        )
        params: list[Any] = [run_id]
        if response_id is not None:
            sql += " AND response_id = ?"
            params.append(response_id)
        sql += " ORDER BY response_id, code_name, COALESCE(span_start, -1), assignment_id"
        return [_row_to_assignment(row) for row in self._conn.execute(sql, params)]

    def assignments_for_run(self, run_id: str) -> list[Assignment]:
        """The flat rows the occurrence matrix and the agreement report consume."""
        return [record.to_assignment() for record in self.read_assignments(run_id)]

    # -- findings --------------------------------------------------------- #

    def write_report(
        self,
        report: CheckReport,
        *,
        run_id: str,
        response_id: int | None = None,
        snapshot_id: str | None = None,
        created_at: str | None = None,
    ) -> list[str]:
        """Persist a `CheckReport` as `findings` rows, in order. Returns the ids.

        The ordinal in each id is the finding's position among this run's findings, so
        emitting the same finding twice writes two rows — which is correct: it was
        found twice.
        """
        stamp = created_at or utc_now_iso()
        base = int(
            self._conn.execute(
                "SELECT COUNT(*) FROM findings WHERE run_id = ?", (run_id,)
            ).fetchone()[0]
        )
        ids: list[str] = []
        for offset, finding in enumerate(report.findings):
            finding_id = mint_finding_id(
                run_id=run_id,
                check_id=finding.check_id,
                severity=finding.severity.value,
                scope=finding.scope,
                subject=finding.subject,
                message=finding.message,
                ordinal=base + offset,
            )
            self._conn.execute(
                "INSERT INTO findings(finding_id, run_id, response_id, check_id, severity, "
                "scope, subject, message, data_json, snapshot_id, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    finding_id,
                    run_id,
                    response_id,
                    finding.check_id,
                    finding.severity.value,
                    finding.scope,
                    finding.subject,
                    finding.message,
                    _dumps(finding.data),
                    snapshot_id,
                    stamp,
                ),
            )
            ids.append(finding_id)
        self._conn.commit()
        return ids

    def read_report(
        self,
        run_id: str,
        *,
        check_id: str | None = None,
        severity: Severity | None = None,
        response_id: int | None = None,
    ) -> CheckReport:
        """Read findings back as a `CheckReport`, in the order they were written.

        `rowid` is the ordering because a `CheckReport` is an ordered accumulation:
        reading it back in any other order would not be the same report.
        """
        sql = (
            "SELECT check_id, severity, scope, subject, message, data_json "
            "FROM findings WHERE run_id = ?"
        )
        params: list[Any] = [run_id]
        if check_id is not None:
            sql += " AND check_id = ?"
            params.append(check_id)
        if severity is not None:
            sql += " AND severity = ?"
            params.append(severity.value)
        if response_id is not None:
            sql += " AND response_id = ?"
            params.append(response_id)
        sql += " ORDER BY rowid"
        findings = [
            CheckFinding(
                check_id=str(row[0]),
                severity=Severity(row[1]),
                scope=str(row[2]),
                subject=str(row[3]),
                message=str(row[4]),
                data=json.loads(row[5]),
            )
            for row in self._conn.execute(sql, params)
        ]
        return CheckReport(findings=findings)

    def findings_summary(self, run_id: str) -> dict[str, dict[str, int]]:
        """Counts by check id x severity, check-sorted — the run report's CHECKS block.

        Matches `CheckReport.summary()` in shape so the stored and in-memory views of
        a run's checks are directly comparable.
        """
        rows = self._conn.execute(
            "SELECT check_id, severity, COUNT(*) FROM findings WHERE run_id = ? "
            "GROUP BY check_id, severity ORDER BY check_id, severity",
            (run_id,),
        )
        out: dict[str, dict[str, int]] = {}
        for check_id, severity, count in rows:
            out.setdefault(str(check_id), {})[str(severity)] = int(count)
        return out

    # -- model calls ------------------------------------------------------ #

    def write_llm_call(
        self,
        result: LLMResult,
        *,
        run_id: str,
        role: str,
        subject: str = "",
        ordinal: int | None = None,
        created_at: str | None = None,
    ) -> LLMCallRecord:
        """Persist an `LLMResult` as one accounting row.

        `ordinal` defaults to the number of calls already recorded for the run, which
        makes a retry, a cache hit and a live call on the same subject three rows
        rather than one silently overwritten row.
        """
        if ordinal is None:
            ordinal = int(
                self._conn.execute(
                    "SELECT COUNT(*) FROM llm_calls WHERE run_id = ?", (run_id,)
                ).fetchone()[0]
            )
        call_id = mint_llm_call_id(
            run_id=run_id,
            task=result.task.value,
            provider=result.provider,
            model=result.model,
            prompt_version=result.prompt_version,
            subject=subject,
            ordinal=ordinal,
        )
        stamp = created_at or utc_now_iso()
        self._conn.execute(
            "INSERT INTO llm_calls(call_id, run_id, role, task, provider, model, prompt_version, "
            "subject, input_tokens, output_tokens, cost_usd, latency_ms, cache_hit, fail_safe, "
            "created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(call_id) DO NOTHING",
            (
                call_id,
                run_id,
                role,
                result.task.value,
                result.provider,
                result.model,
                result.prompt_version,
                subject,
                result.input_tokens,
                result.output_tokens,
                result.cost_usd,
                result.latency_ms,
                int(result.cache_hit),
                int(result.fail_safe),
                stamp,
            ),
        )
        self._conn.commit()
        return LLMCallRecord(
            call_id=call_id,
            run_id=run_id,
            role=role,
            task=result.task.value,
            provider=result.provider,
            model=result.model,
            prompt_version=result.prompt_version,
            subject=subject,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            cost_usd=result.cost_usd,
            latency_ms=result.latency_ms,
            cache_hit=result.cache_hit,
            fail_safe=result.fail_safe,
            created_at=stamp,
        )

    def read_llm_calls(self, run_id: str, *, task: str | None = None) -> list[LLMCallRecord]:
        """Model calls for a run, in the order they were made."""
        sql = (
            "SELECT call_id, run_id, role, task, provider, model, prompt_version, subject, "
            "input_tokens, output_tokens, cost_usd, latency_ms, cache_hit, fail_safe, created_at "
            "FROM llm_calls WHERE run_id = ?"
        )
        params: list[Any] = [run_id]
        if task is not None:
            sql += " AND task = ?"
            params.append(task)
        sql += " ORDER BY rowid"
        return [_row_to_llm_call(row) for row in self._conn.execute(sql, params)]

    # -- checkpoints ------------------------------------------------------ #

    def write_checkpoint(
        self,
        *,
        run_id: str,
        at_response_count: int,
        trigger: str,
        base_snapshot_id: str,
        proposal: Mapping[str, Any],
        status: str = "proposed",
        created_at: str | None = None,
    ) -> CheckpointRecord:
        """Record a slow-loop proposal, before the human gate sees it."""
        checkpoint_id = mint_checkpoint_id(
            run_id=run_id,
            at_response_count=at_response_count,
            trigger=trigger,
            base_snapshot_id=base_snapshot_id,
        )
        stamp = created_at or utc_now_iso()
        payload = dict(proposal)
        self._conn.execute(
            "INSERT INTO checkpoints(checkpoint_id, run_id, at_response_count, trigger, "
            "base_snapshot_id, proposal_json, decisions_json, status, result_snapshot_id, "
            "created_at, decided_at) VALUES (?, ?, ?, ?, ?, ?, '[]', ?, NULL, ?, NULL) "
            "ON CONFLICT(checkpoint_id) DO NOTHING",
            (
                checkpoint_id,
                run_id,
                at_response_count,
                trigger,
                base_snapshot_id,
                _dumps(payload),
                status,
                stamp,
            ),
        )
        self._conn.commit()
        return CheckpointRecord(
            checkpoint_id=checkpoint_id,
            run_id=run_id,
            at_response_count=at_response_count,
            trigger=trigger,
            base_snapshot_id=base_snapshot_id,
            proposal=payload,
            decisions=[],
            status=status,
            result_snapshot_id=None,
            created_at=stamp,
            decided_at=None,
        )

    def decide_checkpoint(
        self,
        checkpoint_id: str,
        *,
        status: str,
        decisions: Sequence[Mapping[str, Any]],
        result_snapshot_id: str | None = None,
        decided_at: str | None = None,
    ) -> CheckpointRecord:
        """Record the human gate's per-operation decisions and the resulting snapshot."""
        stamp = decided_at or utc_now_iso()
        self._conn.execute(
            "UPDATE checkpoints SET status = ?, decisions_json = ?, result_snapshot_id = ?, "
            "decided_at = ? WHERE checkpoint_id = ?",
            (status, _dumps([dict(d) for d in decisions]), result_snapshot_id, stamp, checkpoint_id),
        )
        self._conn.commit()
        record = self.read_checkpoint(checkpoint_id)
        if record is None:
            raise KeyError(f"no checkpoint {checkpoint_id!r} in this store")
        return record

    def read_checkpoint(self, checkpoint_id: str) -> CheckpointRecord | None:
        row = self._conn.execute(
            f"{_CHECKPOINT_SELECT} WHERE checkpoint_id = ?", (checkpoint_id,)
        ).fetchone()
        return None if row is None else _row_to_checkpoint(row)

    def read_checkpoints(self, run_id: str) -> list[CheckpointRecord]:
        """Checkpoints for a run, in the order they fired."""
        rows = self._conn.execute(
            f"{_CHECKPOINT_SELECT} WHERE run_id = ? ORDER BY at_response_count, checkpoint_id",
            (run_id,),
        )
        return [_row_to_checkpoint(row) for row in rows]

    # -- health metrics --------------------------------------------------- #

    def write_health_metric(
        self,
        *,
        run_id: str,
        at_response_count: int,
        metric: str,
        value: float,
        created_at: str | None = None,
    ) -> HealthMetric:
        """Record one health or saturation sample.

        Re-sampling the same metric at the same response count overwrites, because it
        is the same measurement of the same state, not a second observation.
        """
        stamp = created_at or utc_now_iso()
        self._conn.execute(
            "INSERT INTO health_metrics(run_id, at_response_count, metric, value, created_at) "
            "VALUES (?, ?, ?, ?, ?) ON CONFLICT(run_id, at_response_count, metric) "
            "DO UPDATE SET value = excluded.value, created_at = excluded.created_at",
            (run_id, at_response_count, metric, float(value), stamp),
        )
        self._conn.commit()
        return HealthMetric(
            run_id=run_id,
            at_response_count=at_response_count,
            metric=metric,
            value=float(value),
            created_at=stamp,
        )

    def write_health_metrics(
        self,
        *,
        run_id: str,
        at_response_count: int,
        metrics: Mapping[str, float],
        created_at: str | None = None,
    ) -> list[HealthMetric]:
        """Record a whole sample, metric-name sorted so the write order is stable."""
        return [
            self.write_health_metric(
                run_id=run_id,
                at_response_count=at_response_count,
                metric=name,
                value=metrics[name],
                created_at=created_at,
            )
            for name in sorted(metrics)
        ]

    def read_health_metrics(
        self, run_id: str, *, metric: str | None = None
    ) -> list[HealthMetric]:
        """Health samples for a run, ordered by response count then metric name."""
        sql = (
            "SELECT run_id, at_response_count, metric, value, created_at "
            "FROM health_metrics WHERE run_id = ?"
        )
        params: list[Any] = [run_id]
        if metric is not None:
            sql += " AND metric = ?"
            params.append(metric)
        sql += " ORDER BY at_response_count, metric"
        return [
            HealthMetric(
                run_id=str(row[0]),
                at_response_count=int(row[1]),
                metric=str(row[2]),
                value=float(row[3]),
                created_at=str(row[4]),
            )
            for row in self._conn.execute(sql, params)
        ]

    def __iter__(self) -> Iterator[RunRecord]:
        return iter(self.runs())


# --------------------------------------------------------------------------- #
# Row mappers
# --------------------------------------------------------------------------- #

_CHECKPOINT_SELECT = (
    "SELECT checkpoint_id, run_id, at_response_count, trigger, base_snapshot_id, "
    "proposal_json, decisions_json, status, result_snapshot_id, created_at, decided_at "
    "FROM checkpoints"
)


def _row_to_run(row: tuple[Any, ...]) -> RunRecord:
    return RunRecord(
        run_id=str(row[0]),
        created_at=str(row[1]),
        gaf_version=str(row[2]),
        offline=bool(row[3]),
        config=json.loads(row[4]),
    )


def _row_to_response(row: tuple[Any, ...]) -> Response:
    return Response(
        id=int(row[0]),
        question=str(row[2]),
        content=str(row[3]),
        source=str(row[1]),
        meta=json.loads(row[4]),
    )


def _row_to_coding(row: tuple[Any, ...]) -> CodingRecord:
    return CodingRecord(
        coding_id=str(row[0]),
        run_id=str(row[1]),
        response_id=int(row[2]),
        source=str(row[3]),
        coder=str(row[4]),
        snapshot_id=str(row[5]),
        prompt_version=str(row[6]),
        created_at=str(row[7]),
        raw=json.loads(row[8]),
    )


def _row_to_candidate(row: tuple[Any, ...]) -> CandidateRecord:
    candidate = Candidate(
        name=str(row[2]),
        description=str(row[3]),
        evidence=[Evidence.from_json(e) for e in json.loads(row[8])],
        coder=str(row[10]),
        parent_hint=row[4],
    )
    return CandidateRecord(
        candidate_id=str(row[0]),
        coding_id=str(row[1]),
        candidate=candidate,
        status=str(row[5]),
        resolution=str(row[6]),
        code_id=row[7],
        created_at=str(row[9]),
    )


def _row_to_assignment(row: tuple[Any, ...]) -> AssignmentRecord:
    span = None if row[7] is None or row[8] is None else (int(row[7]), int(row[8]))
    return AssignmentRecord(
        assignment_id=str(row[0]),
        run_id=str(row[1]),
        response_id=int(row[2]),
        source=str(row[3]),
        code_id=str(row[4]),
        code_name=str(row[5]),
        segment_text=str(row[6]),
        span=span,
        norm_version=str(row[9]),
        snapshot_id=str(row[10]),
        created_at=str(row[11]),
    )


def _row_to_llm_call(row: tuple[Any, ...]) -> LLMCallRecord:
    return LLMCallRecord(
        call_id=str(row[0]),
        run_id=str(row[1]),
        role=str(row[2]),
        task=str(row[3]),
        provider=str(row[4]),
        model=str(row[5]),
        prompt_version=str(row[6]),
        subject=str(row[7]),
        input_tokens=int(row[8]),
        output_tokens=int(row[9]),
        cost_usd=float(row[10]),
        latency_ms=float(row[11]),
        cache_hit=bool(row[12]),
        fail_safe=bool(row[13]),
        created_at=str(row[14]),
    )


def _row_to_checkpoint(row: tuple[Any, ...]) -> CheckpointRecord:
    return CheckpointRecord(
        checkpoint_id=str(row[0]),
        run_id=str(row[1]),
        at_response_count=int(row[2]),
        trigger=str(row[3]),
        base_snapshot_id=str(row[4]),
        proposal=json.loads(row[5]),
        decisions=json.loads(row[6]),
        status=str(row[7]),
        result_snapshot_id=row[8],
        created_at=str(row[9]),
        decided_at=row[10],
    )
