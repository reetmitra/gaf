"""The append-only event log — the only writer to the `audit` table.

The design law says *checks report; the router and the audit log decide and record*.
This module is the recording half. Nothing else in the package inserts into `audit`,
and this module offers no way to update or delete a row: `gaf.store.schema` installs
triggers that abort `UPDATE` and `DELETE` there, so an API that attempted either would
raise, and the API therefore does not attempt either.

An event is a fact about a run: what happened, to which subject, in which scope,
against which snapshot, with a JSON payload of whatever the reader of the run report
will need. Payloads must be JSON-serialisable; a payload that is not raises here
rather than being silently flattened with `str()`, because a lossy audit row is worse
than a missing one — it looks like evidence and is not.

Wall-clock time lives here (and in `snapshots.created_at` / `runs.created_at`) and
nowhere else that is claimed to be byte-identical: codebook JSON carries no timestamps
(ADR-0007), so a run's artefacts stay reproducible while its log stays honest about
when it ran.

Validation principle: **transparency** — a merge, a judge ruling, a dropped quote and
a human decision are each a row a methods reviewer can read in the order it happened.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

__all__ = ["AuditEvent", "AuditLog", "utc_now_iso"]


def utc_now_iso() -> str:
    """Current UTC time as an ISO-8601 string, e.g. ``2026-09-01T06:15:42.123456Z``.

    The single clock reading in the store, so that every `created_at` in the database
    has one format and sorts lexicographically in time order.
    """
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class AuditEvent:
    """One row of the append-only log, as read back."""

    event_id: int
    run_id: str
    created_at: str
    event: str
    scope: str = ""
    subject: str = ""
    snapshot_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "run_id": self.run_id,
            "created_at": self.created_at,
            "event": self.event,
            "scope": self.scope,
            "subject": self.subject,
            "snapshot_id": self.snapshot_id,
            "payload": dict(self.payload),
        }

    def __str__(self) -> str:
        where = f" {self.scope}:{self.subject}" if self.subject or self.scope else ""
        return f"[{self.created_at}] {self.event}{where}"


def _encode_payload(payload: dict[str, Any]) -> str:
    """Serialise a payload, refusing anything lossy.

    `sort_keys` keeps two identical payloads byte-identical in the database, which is
    what lets a reviewer diff two runs' logs.
    """
    try:
        return json.dumps(payload, sort_keys=True, ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        offenders = ", ".join(sorted(payload)) or "<empty>"
        raise TypeError(
            "audit payloads must be JSON-serialisable; refusing to write a lossy "
            f"str() of it. Keys offered: {offenders}. Underlying error: {exc}"
        ) from exc


class AuditLog:
    """Append-only event log for one run.

    Bound to a run id at construction because every event belongs to a run — the
    `audit.run_id` column is a foreign key into `runs`, so the run must be registered
    before the first event is emitted.
    """

    __slots__ = ("_conn", "run_id")

    def __init__(self, conn: sqlite3.Connection, run_id: str) -> None:
        self._conn = conn
        self.run_id = run_id

    # -- writing ---------------------------------------------------------- #

    def emit(
        self,
        event: str,
        *,
        subject: str = "",
        scope: str = "",
        snapshot_id: str | None = None,
        **payload: Any,
    ) -> AuditEvent:
        """Append one event and return it, with the `event_id` the database assigned.

        `event_id` is not minted by `gaf.ids`: the log's ordering is its insertion
        order, and `INTEGER PRIMARY KEY AUTOINCREMENT` is the database's own statement
        of that order.
        """
        created_at = utc_now_iso()
        payload_json = _encode_payload(payload)
        cursor = self._conn.execute(
            "INSERT INTO audit(run_id, created_at, event, scope, subject, snapshot_id, payload_json) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (self.run_id, created_at, event, scope, subject, snapshot_id, payload_json),
        )
        self._conn.commit()
        return AuditEvent(
            event_id=int(cursor.lastrowid or 0),
            run_id=self.run_id,
            created_at=created_at,
            event=event,
            scope=scope,
            subject=subject,
            snapshot_id=snapshot_id,
            payload=dict(payload),
        )

    # -- reading ---------------------------------------------------------- #

    def events(self, *, event: str | None = None, subject: str | None = None) -> list[AuditEvent]:
        """Every event for this run, in insertion order, optionally filtered.

        Ordered by `event_id`, which is the insertion order and the only ordering the
        log has: two events emitted in the same microsecond still read back in the
        order they happened.
        """
        sql = "SELECT event_id, run_id, created_at, event, scope, subject, snapshot_id, payload_json FROM audit WHERE run_id = ?"
        params: list[Any] = [self.run_id]
        if event is not None:
            sql += " AND event = ?"
            params.append(event)
        if subject is not None:
            sql += " AND subject = ?"
            params.append(subject)
        sql += " ORDER BY event_id"
        return [_row_to_event(row) for row in self._conn.execute(sql, params)]

    def event_names(self) -> list[str]:
        """Distinct event names seen in this run, sorted — the run report's index."""
        rows = self._conn.execute(
            "SELECT DISTINCT event FROM audit WHERE run_id = ? ORDER BY event", (self.run_id,)
        )
        return [str(row[0]) for row in rows]

    def counts(self) -> dict[str, int]:
        """Event name -> number of occurrences, name-sorted."""
        rows = self._conn.execute(
            "SELECT event, COUNT(*) FROM audit WHERE run_id = ? GROUP BY event ORDER BY event",
            (self.run_id,),
        )
        return {str(name): int(count) for name, count in rows}

    def count(self, event: str | None = None) -> int:
        """How many events this run has logged, optionally of one name."""
        if event is None:
            row = self._conn.execute(
                "SELECT COUNT(*) FROM audit WHERE run_id = ?", (self.run_id,)
            ).fetchone()
        else:
            row = self._conn.execute(
                "SELECT COUNT(*) FROM audit WHERE run_id = ? AND event = ?", (self.run_id, event)
            ).fetchone()
        return int(row[0])

    def __len__(self) -> int:
        return self.count()

    def __iter__(self) -> Iterator[AuditEvent]:
        return iter(self.events())


def _row_to_event(row: tuple[Any, ...]) -> AuditEvent:
    return AuditEvent(
        event_id=int(row[0]),
        run_id=str(row[1]),
        created_at=str(row[2]),
        event=str(row[3]),
        scope=str(row[4]),
        subject=str(row[5]),
        snapshot_id=row[6],
        payload=json.loads(row[7]),
    )
