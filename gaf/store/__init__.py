"""The blackboard: one SQLite database holding every artefact the pipeline produces.

The predecessor design lost context across an agent chain because state lived in the
prose passed between agents. Here all state lives in one store, every model call is
stateless and re-grounds from it, and handoffs carry ids rather than prose.

Validation principle: **transparency** — a finding, a code, a merge, a judge ruling, a
dropped quote are each a row with an id, a timestamp, a snapshot reference and the
inputs that produced it.
"""

from __future__ import annotations

from gaf.store.audit import AuditEvent, AuditLog, utc_now_iso
from gaf.store.blackboard import AssignmentRecord, Blackboard, StoreConflictError
from gaf.store.schema import SCHEMA_VERSION, TABLES, apply_schema
from gaf.store.snapshot import (
    SNAPSHOT_REASONS,
    Snapshot,
    SnapshotIntegrityError,
    freeze,
    latest_snapshot,
    read_snapshot,
    read_snapshots,
    snapshot_exists,
    verify_codebook_json,
    write_snapshot,
)

__all__ = [
    "SCHEMA_VERSION",
    "SNAPSHOT_REASONS",
    "TABLES",
    "AssignmentRecord",
    "AuditEvent",
    "AuditLog",
    "Blackboard",
    "Snapshot",
    "SnapshotIntegrityError",
    "StoreConflictError",
    "apply_schema",
    "freeze",
    "latest_snapshot",
    "read_snapshot",
    "read_snapshots",
    "snapshot_exists",
    "utc_now_iso",
    "verify_codebook_json",
    "write_snapshot",
]
