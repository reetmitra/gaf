"""The SQLite schema — the blackboard's frozen shape.

FROZEN CONTRACT (Wave 0). No Wave 1+ agent may change this module. A1 owns the
repository API in `blackboard.py`; the DDL lives here so that the store, the reports,
the CLI and the tests all agree on the shape without depending on A1's implementation.

Two properties are enforced *by the database*, not by convention:

* **the audit log is append-only** — triggers abort any UPDATE or DELETE on `audit`;
* **snapshots are immutable** — a snapshot id is the content hash of its codebook, so
  a mutable snapshot would be a lie. Triggers abort UPDATE and DELETE there too.

That is what makes "content-addressed and replayable" a checkable claim rather than a
description of intent.

Validation principle: **transparency** and **reliability**.
"""

from __future__ import annotations

import sqlite3

__all__ = ["PRAGMAS", "SCHEMA_SQL", "SCHEMA_VERSION", "TABLES", "apply_schema"]

SCHEMA_VERSION = 1

#: Applied on every connection. `foreign_keys` is off by default in SQLite and must be
#: switched on per-connection or the references below are decorative.
PRAGMAS: tuple[str, ...] = (
    "PRAGMA foreign_keys = ON",
    "PRAGMA journal_mode = WAL",
    "PRAGMA synchronous = NORMAL",
)

TABLES: tuple[str, ...] = (
    "meta",
    "runs",
    "responses",
    "snapshots",
    "codings",
    "candidates",
    "assignments",
    "findings",
    "audit",
    "llm_calls",
    "checkpoints",
    "health_metrics",
)

SCHEMA_SQL = """
-- Schema bookkeeping ------------------------------------------------------- --
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- A run: one execution of the pipeline, with the full config that produced it. --
CREATE TABLE IF NOT EXISTS runs (
    run_id      TEXT PRIMARY KEY,
    created_at  TEXT NOT NULL,
    gaf_version TEXT NOT NULL,
    offline     INTEGER NOT NULL,
    config_json TEXT NOT NULL
);

-- The corpus. `meta_json` holds respondent metadata and is NEVER read by a coder. --
CREATE TABLE IF NOT EXISTS responses (
    response_id  INTEGER NOT NULL,
    source       TEXT NOT NULL,
    question     TEXT NOT NULL,
    content      TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    meta_json    TEXT NOT NULL DEFAULT '{}',
    PRIMARY KEY (response_id, source)
);

-- Frozen, content-addressed codebook snapshots. Coders read one; only the slow    --
-- loop writes one. Immutability is enforced by the triggers below.                --
CREATE TABLE IF NOT EXISTS snapshots (
    snapshot_id   TEXT PRIMARY KEY,     -- content hash of codebook_json
    parent_id     TEXT REFERENCES snapshots(snapshot_id),
    run_id        TEXT REFERENCES runs(run_id),
    created_at    TEXT NOT NULL,
    reason        TEXT NOT NULL,        -- 'seed' | 'batch' | 'checkpoint_apply'
    code_count    INTEGER NOT NULL,
    codebook_json TEXT NOT NULL
);

-- One coder's pass over one response, against one snapshot. --
CREATE TABLE IF NOT EXISTS codings (
    coding_id      TEXT PRIMARY KEY,
    run_id         TEXT NOT NULL REFERENCES runs(run_id),
    response_id    INTEGER NOT NULL,
    source         TEXT NOT NULL,
    coder          TEXT NOT NULL,       -- 'coder_a' | 'coder_b'
    snapshot_id    TEXT NOT NULL REFERENCES snapshots(snapshot_id),
    prompt_version TEXT NOT NULL,
    created_at     TEXT NOT NULL,
    raw_json       TEXT NOT NULL,
    FOREIGN KEY (response_id, source) REFERENCES responses(response_id, source)
);

-- What a coder proposed, and what became of it. --
CREATE TABLE IF NOT EXISTS candidates (
    candidate_id  TEXT PRIMARY KEY,
    coding_id     TEXT NOT NULL REFERENCES codings(coding_id),
    name          TEXT NOT NULL,
    description   TEXT NOT NULL,
    parent_hint   TEXT,
    status        TEXT NOT NULL,        -- 'proposed'|'accepted'|'dropped'|'merged'|'created'
    resolution    TEXT NOT NULL DEFAULT '',  -- route or drop reason
    code_id       TEXT,                 -- set once integrated
    evidence_json TEXT NOT NULL DEFAULT '[]',
    created_at    TEXT NOT NULL
);

-- The row-oriented result: this code was applied to this span of this response. --
CREATE TABLE IF NOT EXISTS assignments (
    assignment_id TEXT PRIMARY KEY,
    run_id        TEXT NOT NULL REFERENCES runs(run_id),
    response_id   INTEGER NOT NULL,
    source        TEXT NOT NULL,
    code_id       TEXT NOT NULL,
    code_name     TEXT NOT NULL,
    segment_text  TEXT NOT NULL,
    span_start    INTEGER,
    span_end      INTEGER,
    norm_version  TEXT NOT NULL,        -- gaf.textnorm.NORMALISATION_VERSION
    snapshot_id   TEXT NOT NULL REFERENCES snapshots(snapshot_id),
    created_at    TEXT NOT NULL
);

-- Every CheckFinding ever emitted, structural and semantic alike. --
CREATE TABLE IF NOT EXISTS findings (
    finding_id  TEXT PRIMARY KEY,
    run_id      TEXT NOT NULL REFERENCES runs(run_id),
    response_id INTEGER,
    check_id    TEXT NOT NULL,
    severity    TEXT NOT NULL,          -- 'ERROR' | 'WARN' | 'INFO'
    scope       TEXT NOT NULL,
    subject     TEXT NOT NULL,
    message     TEXT NOT NULL,
    data_json   TEXT NOT NULL DEFAULT '{}',
    snapshot_id TEXT,
    created_at  TEXT NOT NULL
);

-- The append-only event log. --
CREATE TABLE IF NOT EXISTS audit (
    event_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id       TEXT NOT NULL REFERENCES runs(run_id),
    created_at   TEXT NOT NULL,
    event        TEXT NOT NULL,
    scope        TEXT NOT NULL DEFAULT '',
    subject      TEXT NOT NULL DEFAULT '',
    snapshot_id  TEXT,
    payload_json TEXT NOT NULL DEFAULT '{}'
);

-- Per-call model accounting. --
CREATE TABLE IF NOT EXISTS llm_calls (
    call_id        TEXT PRIMARY KEY,
    run_id         TEXT NOT NULL REFERENCES runs(run_id),
    role           TEXT NOT NULL,
    task           TEXT NOT NULL,
    provider       TEXT NOT NULL,
    model          TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    subject        TEXT NOT NULL DEFAULT '',
    input_tokens   INTEGER NOT NULL DEFAULT 0,
    output_tokens  INTEGER NOT NULL DEFAULT 0,
    cost_usd       REAL NOT NULL DEFAULT 0.0,
    latency_ms     REAL NOT NULL DEFAULT 0.0,
    cache_hit      INTEGER NOT NULL DEFAULT 0,
    fail_safe      INTEGER NOT NULL DEFAULT 0,
    created_at     TEXT NOT NULL
);

-- Slow-loop checkpoints: the proposal, the human decision, the resulting snapshot. --
CREATE TABLE IF NOT EXISTS checkpoints (
    checkpoint_id      TEXT PRIMARY KEY,
    run_id             TEXT NOT NULL REFERENCES runs(run_id),
    at_response_count  INTEGER NOT NULL,
    trigger            TEXT NOT NULL,   -- 'floor' | 'health' | 'manual'
    base_snapshot_id   TEXT NOT NULL REFERENCES snapshots(snapshot_id),
    proposal_json      TEXT NOT NULL,   -- the edit script as proposed
    decisions_json     TEXT NOT NULL DEFAULT '[]',  -- per-operation accept/reject/edit
    status             TEXT NOT NULL,   -- 'proposed' | 'accepted' | 'rejected' | 'applied'
    result_snapshot_id TEXT REFERENCES snapshots(snapshot_id),
    created_at         TEXT NOT NULL,
    decided_at         TEXT
);

-- Codebook health and saturation, sampled over the run. --
CREATE TABLE IF NOT EXISTS health_metrics (
    run_id            TEXT NOT NULL REFERENCES runs(run_id),
    at_response_count INTEGER NOT NULL,
    metric            TEXT NOT NULL,
    value             REAL NOT NULL,
    created_at        TEXT NOT NULL,
    PRIMARY KEY (run_id, at_response_count, metric)
);

-- Indices ------------------------------------------------------------------ --
CREATE INDEX IF NOT EXISTS idx_codings_response ON codings(run_id, response_id, coder);
CREATE INDEX IF NOT EXISTS idx_candidates_coding ON candidates(coding_id);
CREATE INDEX IF NOT EXISTS idx_assignments_response ON assignments(run_id, response_id);
CREATE INDEX IF NOT EXISTS idx_assignments_code ON assignments(run_id, code_id);
CREATE INDEX IF NOT EXISTS idx_findings_check ON findings(run_id, check_id, severity);
CREATE INDEX IF NOT EXISTS idx_audit_run ON audit(run_id, event_id);
CREATE INDEX IF NOT EXISTS idx_llm_calls_run ON llm_calls(run_id, task);
CREATE INDEX IF NOT EXISTS idx_snapshots_run ON snapshots(run_id, created_at);

-- Append-only / immutability, enforced by the database ---------------------- --
CREATE TRIGGER IF NOT EXISTS audit_no_update
BEFORE UPDATE ON audit
BEGIN
    SELECT RAISE(ABORT, 'audit log is append-only: UPDATE is not permitted');
END;

CREATE TRIGGER IF NOT EXISTS audit_no_delete
BEFORE DELETE ON audit
BEGIN
    SELECT RAISE(ABORT, 'audit log is append-only: DELETE is not permitted');
END;

CREATE TRIGGER IF NOT EXISTS snapshots_no_update
BEFORE UPDATE ON snapshots
BEGIN
    SELECT RAISE(ABORT, 'snapshots are content-addressed and immutable: UPDATE is not permitted');
END;

CREATE TRIGGER IF NOT EXISTS snapshots_no_delete
BEFORE DELETE ON snapshots
BEGIN
    SELECT RAISE(ABORT, 'snapshots are content-addressed and immutable: DELETE is not permitted');
END;
"""


def apply_schema(conn: sqlite3.Connection) -> None:
    """Apply pragmas and DDL to `conn`, and stamp the schema version.

    Idempotent: every statement is ``IF NOT EXISTS``, so opening an existing database
    is the same call as creating a new one.
    """
    for pragma in PRAGMAS:
        conn.execute(pragma)
    conn.executescript(SCHEMA_SQL)
    conn.execute(
        "INSERT INTO meta(key, value) VALUES('schema_version', ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (str(SCHEMA_VERSION),),
    )
    conn.commit()
