"""Content hashing and deterministic id minting.

Every id in this system is a pure function of the content it identifies. There is no
randomness here, no wall-clock reading and no counter that depends on the order in
which rows happen to be written: an id is minted by hashing the fields that identify
the thing, so two runs over the same inputs mint the same ids and a snapshot can be
replayed byte for byte.

The one id this module deliberately does **not** mint is ``audit.event_id``, which is
``INTEGER PRIMARY KEY AUTOINCREMENT`` in `gaf.store.schema` — the database assigns it,
because the audit log's ordering *is* its insertion order.

Where an id must distinguish two otherwise identical things (the same finding emitted
twice, two candidates with the same name under one coding), the caller passes an
``ordinal``. That keeps the id a pure function of its inputs while still being unique:
"the same finding, emitted a second time" is genuinely a different row.

Validation principle: **reliability** — content-addressed ids are what make
"re-running a batch against the same snapshot reproduces the same output" a checkable
claim rather than an aspiration; and **transparency** — every id carries a prefix, so
a log line says what kind of thing it names.
"""

from __future__ import annotations

import hashlib

__all__ = [
    "HASH_LENGTH",
    "assignment_id",
    "candidate_id",
    "checkpoint_id",
    "code_id",
    "coding_id",
    "content_hash",
    "digest_parts",
    "finding_id",
    "full_content_hash",
    "llm_call_id",
    "mint",
    "snapshot_id",
]

#: Hex characters kept from the SHA-256 digest.
#:
#: 16 hex characters is 64 bits. The birthday bound puts the chance of any collision
#: among *n* ids at roughly ``n^2 / 2^65``: at this corpus size (tens of thousands of
#: rows across every run this project will ever do, so n < 10^6) that is below 1 in
#: 10^7. Short ids are read by humans in the audit log, the run report and the HTML
#: explorer, which is what the truncation buys. `full_content_hash` is exported for
#: anywhere the full digest is wanted.
HASH_LENGTH = 16

#: ASCII unit separator. Joins the parts of a composite id so that ``("ab", "c")`` and
#: ``("a", "bc")`` cannot hash to the same value.
_FIELD_SEP = "\x1f"

#: Stands in for ``None`` so that a missing part and an empty string differ.
_NONE = "\x00"


def _as_bytes(payload: str | bytes) -> bytes:
    return payload if isinstance(payload, bytes) else payload.encode("utf-8")


def _render(part: object) -> str:
    """Unambiguous string form of one id part.

    ``None`` becomes a control character that cannot occur in a name, a quote or a
    run id, so ``None`` and ``""`` never hash alike. Booleans are spelled out rather
    than left to `str`, so a change of Python's repr could not move an id.
    """
    if part is None:
        return _NONE
    if isinstance(part, bool):
        return "true" if part else "false"
    return str(part)


def full_content_hash(payload: str | bytes) -> str:
    """Full 64-character SHA-256 hex digest of `payload`."""
    return hashlib.sha256(_as_bytes(payload)).hexdigest()


def content_hash(payload: str | bytes, *, length: int = HASH_LENGTH) -> str:
    """SHA-256 hex digest of `payload`, truncated to `length` characters.

    Strings are hashed as UTF-8. See `HASH_LENGTH` for why 16 is enough here.
    """
    if not 1 <= length <= 64:
        raise ValueError(f"length must be between 1 and 64 hex characters, got {length}")
    return full_content_hash(payload)[:length]


def digest_parts(*parts: object) -> str:
    """Content hash of an ordered tuple of identifying parts."""
    return content_hash(_FIELD_SEP.join(_render(p) for p in parts))


def mint(prefix: str, *parts: object) -> str:
    """``"<prefix>-<hash of parts>"`` — the one place an id string is assembled."""
    return f"{prefix}-{digest_parts(*parts)}"


# --------------------------------------------------------------------------- #
# The id-bearing rows
# --------------------------------------------------------------------------- #


def snapshot_id(codebook_json_str: str) -> str:
    """Id of the snapshot holding this exact codebook serialisation.

    The argument is `gaf.models.Codebook.to_json_str()` — sorted keys, name-sorted
    codes, no timestamps (ADR-0007). Freezing the same codebook twice therefore yields
    the same id, which is the whole mechanism against order dependence.
    """
    return f"snap-{content_hash(codebook_json_str)}"


def code_id(name: str) -> str:
    """Id of a code, derived from its name alone.

    Identity follows the name deterministically, so the same code name minted in two
    runs is the same code id and a codebook can be compared across runs without a
    lookup table. A rename is therefore a new id — which is correct: the slow loop's
    ``rename`` operation records the mapping in the changelog.
    """
    return f"code-{content_hash(name)}"


def coding_id(
    *,
    run_id: str,
    response_id: int,
    source: str,
    coder: str,
    snapshot_id: str,
    prompt_version: str,
) -> str:
    """Id of one coder's pass over one response against one snapshot.

    Everything that could change the output is in the hash: which run, which response,
    which coder, which frozen codebook it read and which prompt template produced it.
    """
    return mint("coding", run_id, response_id, source, coder, snapshot_id, prompt_version)


def candidate_id(*, coding_id: str, name: str, ordinal: int = 0) -> str:
    """Id of one proposed candidate within one coding.

    `ordinal` disambiguates a coder proposing the same name twice in one pass, which
    is a thing a model does and which S6 must be able to see as two rows.
    """
    return mint("cand", coding_id, name, ordinal)


def assignment_id(
    *,
    run_id: str,
    response_id: int,
    source: str,
    code_id: str,
    segment_text: str,
    snapshot_id: str,
) -> str:
    """Id of one row of the occurrence table: this code, on this span, in this run."""
    return mint("asg", run_id, response_id, source, code_id, segment_text, snapshot_id)


def finding_id(
    *,
    run_id: str,
    check_id: str,
    severity: str,
    scope: str,
    subject: str,
    message: str,
    ordinal: int = 0,
) -> str:
    """Id of one persisted `gaf.checks.contracts.CheckFinding`."""
    return mint("find", run_id, check_id, severity, scope, subject, message, ordinal)


def checkpoint_id(
    *, run_id: str, at_response_count: int, trigger: str, base_snapshot_id: str
) -> str:
    """Id of one slow-loop checkpoint: where it fired, why, and from which snapshot."""
    return mint("ckpt", run_id, at_response_count, trigger, base_snapshot_id)


def llm_call_id(
    *,
    run_id: str,
    task: str,
    provider: str,
    model: str,
    prompt_version: str,
    subject: str = "",
    ordinal: int = 0,
) -> str:
    """Id of one model call row.

    `ordinal` is required because a retry, a second judge call on the same pair, or a
    cache hit followed by a live call are separate accounting rows with identical
    identifying fields.
    """
    return mint("call", run_id, task, provider, model, prompt_version, subject, ordinal)
