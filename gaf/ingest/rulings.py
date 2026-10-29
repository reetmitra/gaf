"""The PI's rulings on his own coding export, as one small JSON file.

`gaf codebook organise` turns code-text pairings into a codebook by arithmetic that has
no opinions: it flags what looks odd and merges only trivial variants (ADR-0031 and the
module docstring of `gaf.ingest.tagged`). Four things the principal investigator has
since *decided* are opinions, and they live here, in one file he can read and overrule,
rather than in code:

``top_level``
    Labels that are deliberately single-level top-level codes -- a family with no
    parent and no subcodes. The organiser would otherwise note each one as a bare
    top-level code "that may want splitting"; a ruled one is recorded as ruled instead.
``label_merges``
    Labels to rewrite onto a canonical spelling (a typo and its correction). Each one
    carries a ``provisional`` flag, because the PI may overrule it, and is recorded as a
    consolidation with ``ruling: true`` so a reader can tell it from a trivial one.
``label_merges_held``
    Near-miss pairs the PI has *not* ruled on, listed so the file records that they were
    seen and left alone. Nothing here is applied.
``multi_place_ambiguous``
    Opt-in. A highlight whose text sits verbatim in several responses is placed in
    **every** candidate that is in the coded set (outcome ``multi_placed``), provided at
    least two are. Off unless this file turns it on.
``manual_placements`` / ``manual_placements_file``
    Highlight id -> response id, applied after both placement passes with outcome
    ``manual``. The inline mapping and the file are merged (the file wins on a clash).
    The real mapping holds ids only, no text, but it is the PI's own answer to a
    question and lives in a gitignored path by convention.

A rulings file names **labels and ids, never respondent text**, so it may be tracked.
Unknown keys are refused: a mistyped key in a file that changes a coding must not be
read as "no ruling".

Validation principle: **transparency** -- every decision that moves a count is written
down in a file a person can read, and every one that is applied is recorded in the
output beside the count it moved.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from gaf.ids import content_hash

__all__ = [
    "HeldMerge",
    "LabelMerge",
    "Rulings",
    "RulingsError",
    "load_manual_placements",
    "load_rulings",
    "parse_manual_placements",
    "parse_rulings",
]

_KNOWN_KEYS = frozenset(
    {
        "description",
        "top_level",
        "label_merges",
        "label_merges_held",
        "multi_place_ambiguous",
        "manual_placements",
        "manual_placements_file",
    }
)


class RulingsError(ValueError):
    """A rulings file does not have the shape the organiser requires."""


@dataclass(frozen=True, slots=True)
class LabelMerge:
    """One label rewritten onto a canonical spelling, by the PI's ruling.

    ``source`` is the label as the export writes it (after trivial consolidation);
    ``target`` is the label it becomes. The target need not appear in the export: a
    misspelling of a label that was never written correctly is renamed, not folded.
    """

    source: str
    target: str
    provisional: bool = True
    reason: str = ""

    def to_json(self) -> dict[str, Any]:
        return {
            "from": self.source,
            "to": self.target,
            "provisional": self.provisional,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class HeldMerge:
    """A near-miss pair the PI has not ruled on: recorded, never applied."""

    labels: tuple[str, str]
    level: str = "label"
    reason: str = ""

    def to_json(self) -> dict[str, Any]:
        return {"labels": list(self.labels), "level": self.level, "reason": self.reason}


@dataclass(frozen=True, slots=True)
class Rulings:
    """Everything the PI has decided about the export, loaded and validated."""

    description: str = ""
    top_level: tuple[str, ...] = ()
    label_merges: tuple[LabelMerge, ...] = ()
    label_merges_held: tuple[HeldMerge, ...] = ()
    multi_place_ambiguous: bool = False
    manual_placements: Mapping[str, int] = field(default_factory=dict)
    manual_placements_file: str = ""
    #: Where this came from and what it hashed to; empty for a `Rulings` built in code.
    path: str = ""
    content_hash: str = ""

    def merge_map(self) -> dict[str, LabelMerge]:
        """The label merges keyed by the label they rewrite."""
        return {merge.source: merge for merge in self.label_merges}

    def to_json(self) -> dict[str, Any]:
        """The file's own shape, so a rulings object round-trips through `parse_rulings`."""
        return {
            "description": self.description,
            "top_level": list(self.top_level),
            "label_merges": [m.to_json() for m in self.label_merges],
            "label_merges_held": [h.to_json() for h in self.label_merges_held],
            "multi_place_ambiguous": self.multi_place_ambiguous,
            "manual_placements": dict(sorted(self.manual_placements.items())),
            "manual_placements_file": self.manual_placements_file,
        }


# --------------------------------------------------------------------------- #
# Reading
# --------------------------------------------------------------------------- #


def _string_list(value: Any, key: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise RulingsError(f"rulings: {key!r} must be a list of non-empty label strings")
    if len(set(value)) != len(value):
        raise RulingsError(f"rulings: {key!r} lists the same label twice")
    return tuple(value)


def _merges(value: Any) -> tuple[LabelMerge, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise RulingsError("rulings: 'label_merges' must be a list of {from, to} objects")
    merges: list[LabelMerge] = []
    for item in value:
        if not isinstance(item, dict):
            raise RulingsError("rulings: every 'label_merges' entry must be an object")
        extra = set(item) - {"from", "to", "provisional", "reason"}
        if extra:
            raise RulingsError(f"rulings: unknown key(s) in a label merge: {sorted(extra)}")
        source, target = item.get("from"), item.get("to")
        if not isinstance(source, str) or not source or not isinstance(target, str) or not target:
            raise RulingsError("rulings: a label merge needs a non-empty 'from' and 'to'")
        if source == target:
            raise RulingsError(f"rulings: label merge {source!r} rewrites a label onto itself")
        provisional = item.get("provisional", True)
        if not isinstance(provisional, bool):
            raise RulingsError(f"rulings: 'provisional' on {source!r} must be true or false")
        merges.append(
            LabelMerge(
                source=source,
                target=target,
                provisional=provisional,
                reason=str(item.get("reason") or ""),
            )
        )
    sources = [m.source for m in merges]
    if len(set(sources)) != len(sources):
        raise RulingsError("rulings: two label merges rewrite the same label")
    chained = sorted(set(sources) & {m.target for m in merges})
    if chained:
        raise RulingsError(
            f"rulings: {chained[0]!r} is both rewritten and the target of another merge; "
            "write the merge straight onto its final spelling"
        )
    return tuple(merges)


def _held(value: Any) -> tuple[HeldMerge, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise RulingsError("rulings: 'label_merges_held' must be a list of objects")
    held: list[HeldMerge] = []
    for item in value:
        if not isinstance(item, dict):
            raise RulingsError("rulings: every 'label_merges_held' entry must be an object")
        extra = set(item) - {"labels", "level", "reason"}
        if extra:
            raise RulingsError(f"rulings: unknown key(s) in a held merge: {sorted(extra)}")
        labels = item.get("labels")
        if (
            not isinstance(labels, list)
            or len(labels) != 2
            or not all(isinstance(x, str) and x for x in labels)
        ):
            raise RulingsError("rulings: a held merge needs 'labels': [a, b]")
        held.append(
            HeldMerge(
                labels=(labels[0], labels[1]),
                level=str(item.get("level") or "label"),
                reason=str(item.get("reason") or ""),
            )
        )
    return tuple(held)


def parse_manual_placements(value: Any, *, where: str = "manual placements") -> dict[str, int]:
    """A ``{highlight id: response id}`` mapping, checked.

    Highlight ids are strings (a JSON object key is one however it was written); a
    response id must be a whole number, and a boolean is refused rather than read as 0
    or 1. An empty or missing mapping is a no-op, which is what "absent" means.
    """
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise RulingsError(f"{where}: must be an object mapping highlight id -> response id")
    out: dict[str, int] = {}
    for key, target in value.items():
        if isinstance(target, bool) or not isinstance(target, int):
            raise RulingsError(f"{where}: highlight {key!r} must map to a whole response id")
        out[str(key)] = target
    return out


def parse_rulings(payload: Any, *, path: str = "", digest: str = "") -> Rulings:
    """Validate a parsed rulings document. Unknown keys and wrong types are refused."""
    if not isinstance(payload, dict):
        raise RulingsError("rulings: the file must hold one JSON object")
    unknown = sorted(set(payload) - _KNOWN_KEYS)
    if unknown:
        raise RulingsError(
            f"rulings: unknown key(s) {unknown}; known keys are {sorted(_KNOWN_KEYS)}"
        )
    multi = payload.get("multi_place_ambiguous", False)
    if not isinstance(multi, bool):
        raise RulingsError("rulings: 'multi_place_ambiguous' must be true or false")
    file_ref = payload.get("manual_placements_file", "")
    if not isinstance(file_ref, str):
        raise RulingsError("rulings: 'manual_placements_file' must be a path string")
    return Rulings(
        description=str(payload.get("description") or ""),
        top_level=_string_list(payload.get("top_level"), "top_level"),
        label_merges=_merges(payload.get("label_merges")),
        label_merges_held=_held(payload.get("label_merges_held")),
        multi_place_ambiguous=multi,
        manual_placements=parse_manual_placements(
            payload.get("manual_placements"), where="rulings: 'manual_placements'"
        ),
        manual_placements_file=file_ref,
        path=path,
        content_hash=digest,
    )


def load_rulings(path: Path | str) -> Rulings:
    """Read a rulings file. Raises `RulingsError` naming the file when it cannot be used."""
    path = Path(path)
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise RulingsError(f"{path}: cannot read the rulings file: {exc}") from exc
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RulingsError(f"{path}: not valid JSON: {exc}") from exc
    try:
        return parse_rulings(payload, path=str(path), digest=content_hash(raw))
    except RulingsError as exc:
        raise RulingsError(f"{path}: {exc}") from exc


def load_manual_placements(path: Path | str) -> tuple[dict[str, int], bool]:
    """Read a manual-placement file: ``(mapping, found)``.

    A file that is not there is a no-op -- ``({}, False)`` -- which is how the real
    mapping stays optional. A file that *is* there but is malformed raises: silently
    ignoring a placement the PI made would be worse than stopping.
    """
    path = Path(path)
    if not path.is_file():
        return {}, False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RulingsError(f"{path}: cannot read the manual placements: {exc}") from exc
    return parse_manual_placements(payload, where=str(path)), True
