"""Frozen, content-addressed codebook snapshots.

A snapshot is an immutable codebook whose id *is* the hash of its serialisation. A
coder reads a snapshot id; only the slow loop writes a new one. That is the mechanism
against **order dependence**: re-running a batch against the same snapshot has to
reproduce the same output, and "the same snapshot" is a checkable claim rather than a
promise, because the id is recomputable from the bytes.

Immutability is enforced in two places, deliberately:

* by the database — `gaf.store.schema` installs triggers that abort `UPDATE` and
  `DELETE` on `snapshots`, so nothing in the process can rewrite one;
* by content addressing — `verify()` recomputes the hash from the stored JSON, so a
  snapshot altered outside the process (a hand-edited file, a restored backup) is
  detectable rather than merely improbable.

What this module does **not** do: embeddings, retrieval, top-k search. A snapshot
exposes its codebook; the matcher (`gaf.embed`) and the fast loop's prep are what
search it. Keeping retrieval out of here is what stops the store from acquiring a
second, divergent notion of code similarity.

Hierarchy questions are delegated to `gaf.models.Codebook` rather than reimplemented,
because the two-level name grammar is canonical in exactly one place.

Validation principle: **reliability** — one codebook, one serialisation, one id;
and **transparency** — a coding row names the exact codebook the coder could see.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from typing import Any, Literal

from gaf.ids import snapshot_id as mint_snapshot_id
from gaf.models import Code, Codebook

__all__ = [
    "SNAPSHOT_REASONS",
    "Snapshot",
    "SnapshotIntegrityError",
    "SnapshotReason",
    "freeze",
    "latest_snapshot",
    "read_snapshot",
    "read_snapshots",
    "snapshot_exists",
    "verify_codebook_json",
    "write_snapshot",
]

SnapshotReason = Literal["seed", "batch", "checkpoint_apply"]

#: Runtime-checkable mirror of :data:`SnapshotReason`, in the spirit of ADR-0009.
SNAPSHOT_REASONS: tuple[str, ...] = ("seed", "batch", "checkpoint_apply")


class SnapshotIntegrityError(ValueError):
    """A snapshot's stored content does not hash to its id.

    Raised on read, never swallowed: a snapshot whose id no longer describes its
    content invalidates every coding that names it.
    """


def verify_codebook_json(snapshot_id: str, codebook_json: str) -> bool:
    """True when `codebook_json` hashes to `snapshot_id`.

    The bytes are hashed exactly as stored, so any alteration — including one that
    parses to the same codebook — is visible.
    """
    return mint_snapshot_id(codebook_json) == snapshot_id


@dataclass(frozen=True, slots=True)
class Snapshot:
    """An immutable, content-addressed codebook.

    `code_count` is stored rather than derived so that a row whose count disagrees
    with its codebook is *reportable* by `verify()` instead of unrepresentable. The
    checker reports; it does not repair.
    """

    snapshot_id: str
    codebook: Codebook = field(default_factory=Codebook)
    parent_id: str | None = None
    reason: SnapshotReason = "seed"
    code_count: int = 0

    # -- content ---------------------------------------------------------- #

    @property
    def codebook_json(self) -> str:
        """The canonical serialisation this snapshot's id is the hash of."""
        return self.codebook.to_json_str()

    def is_intact(self) -> bool:
        """True when the codebook still hashes to the id and the count still agrees."""
        return (
            verify_codebook_json(self.snapshot_id, self.codebook_json)
            and self.code_count == len(self.codebook)
        )

    def verify(self) -> Snapshot:
        """Return self if intact, else raise `SnapshotIntegrityError`."""
        recomputed = mint_snapshot_id(self.codebook_json)
        if recomputed != self.snapshot_id:
            raise SnapshotIntegrityError(
                f"snapshot {self.snapshot_id} does not match its codebook: the stored "
                f"codebook hashes to {recomputed}. The snapshot has been tampered with "
                "or was written by something other than freeze()."
            )
        if self.code_count != len(self.codebook):
            raise SnapshotIntegrityError(
                f"snapshot {self.snapshot_id} claims {self.code_count} codes but its "
                f"codebook holds {len(self.codebook)}."
            )
        return self

    # -- delegated codebook views ----------------------------------------- #
    #
    # Delegation, never reimplementation: the two-level name grammar lives in
    # `gaf.models.Codebook` and in no second place.

    def __len__(self) -> int:
        return len(self.codebook)

    def __contains__(self, code_id: object) -> bool:
        return code_id in self.codebook

    def codes(self) -> list[Code]:
        return self.codebook.sorted_codes()

    def names(self) -> list[str]:
        return self.codebook.names()

    def by_name(self, name: str) -> Code | None:
        return self.codebook.by_name(name)

    def leaves(self) -> list[Code]:
        return self.codebook.leaves()

    def families(self) -> dict[str, list[Code]]:
        return self.codebook.families()

    def hierarchy_skeleton(self) -> dict[str, list[str]]:
        return self.codebook.hierarchy_skeleton()

    # -- serialisation ---------------------------------------------------- #

    def to_json(self) -> dict[str, Any]:
        """Metadata plus the codebook — the shape a run report exports."""
        return {
            "snapshot_id": self.snapshot_id,
            "parent_id": self.parent_id,
            "reason": self.reason,
            "code_count": self.code_count,
            "codebook": self.codebook.to_json(),
        }

    @classmethod
    def from_json(cls, obj: dict[str, Any]) -> Snapshot:
        codebook = Codebook.from_json(obj.get("codebook") or {"codes": []})
        return cls(
            snapshot_id=str(obj["snapshot_id"]),
            codebook=codebook,
            parent_id=obj.get("parent_id"),
            reason=_validated_reason(str(obj.get("reason", "seed"))),
            code_count=int(obj.get("code_count", len(codebook))),
        )


def _validated_reason(reason: str) -> SnapshotReason:
    if reason not in SNAPSHOT_REASONS:
        raise ValueError(f"unknown snapshot reason {reason!r}; expected one of {SNAPSHOT_REASONS}")
    return reason  # type: ignore[return-value]


def freeze(
    codebook: Codebook,
    *,
    parent_id: str | None = None,
    reason: str = "batch",
) -> Snapshot:
    """Freeze `codebook` into a content-addressed snapshot.

    ``freeze(cb).snapshot_id == gaf.ids.snapshot_id(cb.to_json_str())`` by
    construction, so freezing the same codebook twice yields the same id — including
    across processes and across runs, because the serialisation carries no timestamps
    (ADR-0007).
    """
    return Snapshot(
        snapshot_id=mint_snapshot_id(codebook.to_json_str()),
        codebook=codebook,
        parent_id=parent_id,
        reason=_validated_reason(reason),
        code_count=len(codebook),
    )


# --------------------------------------------------------------------------- #
# Persistence
# --------------------------------------------------------------------------- #

_SELECT = (
    "SELECT snapshot_id, parent_id, reason, code_count, codebook_json FROM snapshots"
)


def write_snapshot(
    conn: sqlite3.Connection,
    snapshot: Snapshot,
    *,
    run_id: str | None,
    created_at: str,
) -> Snapshot:
    """Persist `snapshot`, or confirm the stored copy is identical.

    Writing a snapshot that is already stored is a no-op rather than an error: the id
    is the hash of the content, so "already there" means "already the same". If the
    stored bytes differ from what is being written, that is a hash collision or
    tampering, and it raises.
    """
    snapshot.verify()
    row = conn.execute(
        "SELECT codebook_json FROM snapshots WHERE snapshot_id = ?", (snapshot.snapshot_id,)
    ).fetchone()
    if row is not None:
        if str(row[0]) != snapshot.codebook_json:
            raise SnapshotIntegrityError(
                f"snapshot {snapshot.snapshot_id} is already stored with different "
                "content; refusing to reconcile a content-addressed row."
            )
        return snapshot
    conn.execute(
        "INSERT INTO snapshots(snapshot_id, parent_id, run_id, created_at, reason, "
        "code_count, codebook_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            snapshot.snapshot_id,
            snapshot.parent_id,
            run_id,
            created_at,
            snapshot.reason,
            snapshot.code_count,
            snapshot.codebook_json,
        ),
    )
    conn.commit()
    return snapshot


def _row_to_snapshot(row: tuple[Any, ...], *, verify: bool) -> Snapshot:
    stored_id, parent_id, reason, code_count, codebook_json = (
        str(row[0]),
        row[1],
        str(row[2]),
        int(row[3]),
        str(row[4]),
    )
    if verify and not verify_codebook_json(stored_id, codebook_json):
        raise SnapshotIntegrityError(
            f"stored codebook for snapshot {stored_id} hashes to "
            f"{mint_snapshot_id(codebook_json)}; the row has been altered."
        )
    snapshot = Snapshot(
        snapshot_id=stored_id,
        codebook=Codebook.from_json(json.loads(codebook_json)),
        parent_id=parent_id,
        reason=_validated_reason(reason),
        code_count=code_count,
    )
    return snapshot.verify() if verify else snapshot


def read_snapshot(conn: sqlite3.Connection, snapshot_id: str, *, verify: bool = True) -> Snapshot:
    """Load one snapshot, verifying by default that its content still hashes to its id."""
    row = conn.execute(f"{_SELECT} WHERE snapshot_id = ?", (snapshot_id,)).fetchone()
    if row is None:
        raise KeyError(f"no snapshot {snapshot_id!r} in this store")
    return _row_to_snapshot(row, verify=verify)


def read_snapshots(
    conn: sqlite3.Connection, *, run_id: str | None = None, verify: bool = True
) -> list[Snapshot]:
    """Every snapshot (optionally for one run), oldest first.

    Ordered by `created_at` then `rowid`: two snapshots written in the same
    microsecond still read back in the order they were written, so the ordering is
    total and stable rather than merely usually-right.
    """
    sql = _SELECT
    params: tuple[Any, ...] = ()
    if run_id is not None:
        sql += " WHERE run_id = ?"
        params = (run_id,)
    sql += " ORDER BY created_at, rowid"
    return [_row_to_snapshot(row, verify=verify) for row in conn.execute(sql, params)]


def latest_snapshot(
    conn: sqlite3.Connection, run_id: str, *, verify: bool = True
) -> Snapshot | None:
    """The most recently written snapshot of `run_id`, or None if the run has none."""
    row = conn.execute(
        f"{_SELECT} WHERE run_id = ? ORDER BY created_at DESC, rowid DESC LIMIT 1", (run_id,)
    ).fetchone()
    return None if row is None else _row_to_snapshot(row, verify=verify)


def snapshot_exists(conn: sqlite3.Connection, snapshot_id: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM snapshots WHERE snapshot_id = ?", (snapshot_id,)
    ).fetchone()
    return row is not None
