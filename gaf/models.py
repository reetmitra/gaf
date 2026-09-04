"""The shared vocabulary — frozen dataclasses passed between every stage.

FROZEN CONTRACT (Wave 0). No Wave 1+ agent may change this module.

Every type here is a frozen dataclass with an explicit id and no mutable
class-level defaults (mutable fields use ``field(default_factory=...)``). Frozen-ness
is load-bearing rather than decorative: the design law says a checker *reports* and
never mutates state, so a stage that needs to alter a candidate must construct a new
one (``dataclasses.replace``) and the change becomes visible in the audit log.

Two-level codebook. Codes are named ``toplevel-sub_level``; the *family* of a code is
the part before the first hyphen. Family membership is derived from the name (the S3
grammar is canonical); ``parent_id`` is the explicit structural link that S6 validates
for consistency against the name.

Validation principles: **transparency** (every artefact carries the ids that produced
it) and **reliability** (JSON round-trips are lossless and deterministically ordered).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Literal

__all__ = [
    "OPERATION_TYPES",
    "Assignment",
    "Candidate",
    "Code",
    "Codebook",
    "Evidence",
    "Operation",
    "OperationType",
    "Response",
    "Segment",
    "family_of",
    "split_name",
    "sub_of",
]

OperationType = Literal["create", "merge", "split", "reparent", "rename", "noop"]

#: Runtime-checkable mirror of :data:`OperationType`. The slow loop validates an
#: incoming edit script against this tuple before anything is applied.
OPERATION_TYPES: tuple[str, ...] = ("create", "merge", "split", "reparent", "rename", "noop")


# --------------------------------------------------------------------------- #
# Name grammar helpers (shared by S3, S6, Codebook.families and the reports)
# --------------------------------------------------------------------------- #


def split_name(name: str) -> tuple[str, str]:
    """Split a code name on the **first** hyphen only.

    ``"positive_impacts-problem-solving"`` -> ``("positive_impacts", "problem-solving")``.
    A bare top-level name yields an empty sub-code: ``"future"`` -> ``("future", "")``.
    """
    top, _, sub = name.partition("-")
    return top, sub


def family_of(name: str) -> str:
    """Top-level family of a code name (the part before the first hyphen)."""
    return split_name(name)[0]


def sub_of(name: str) -> str:
    """Sub-code of a code name (everything after the first hyphen; "" if top-level)."""
    return split_name(name)[1]


# --------------------------------------------------------------------------- #
# Corpus
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class Response:
    """One open-ended survey response, with the question that generated it.

    ``question`` travels with every record and with every coding call: the survey
    question is absent from the source spreadsheet, and a coder that cannot see it
    cannot code the response in context.

    ``meta`` holds respondent metadata (age, region, wave, …). It is joined to the
    analysis **only** in the analysis tail and is **never** passed to a model.
    """

    id: int
    question: str
    content: str
    source: str
    meta: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "question": self.question,
            "content": self.content,
            "source": self.source,
            "meta": dict(self.meta),
        }

    @classmethod
    def from_json(cls, obj: dict[str, Any]) -> Response:
        return cls(
            id=int(obj["id"]),
            question=str(obj["question"]),
            content=str(obj["content"]),
            source=str(obj.get("source", "")),
            meta=dict(obj.get("meta") or {}),
        )


@dataclass(frozen=True, slots=True)
class Segment:
    """A character span of one response, in ``normalise(response.content)``.

    See :mod:`gaf.textnorm`: ``start``/``end`` index the *normalised* text, never the
    raw source. ``text`` is the slice itself, carried so that a segment survives being
    written to JSON and read back without the corpus at hand.
    """

    id: str
    response_id: int
    start: int
    end: int
    text: str

    def overlaps(self, other: Segment) -> bool:
        """True when the two spans intersect at all (same response, non-empty overlap)."""
        if self.response_id != other.response_id:
            return False
        return min(self.end, other.end) > max(self.start, other.start)

    def to_json(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "response_id": self.response_id,
            "start": self.start,
            "end": self.end,
            "text": self.text,
        }

    @classmethod
    def from_json(cls, obj: dict[str, Any]) -> Segment:
        return cls(
            id=str(obj["id"]),
            response_id=int(obj["response_id"]),
            start=int(obj["start"]),
            end=int(obj["end"]),
            text=str(obj["text"]),
        )


# --------------------------------------------------------------------------- #
# Coder output
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class Evidence:
    """One quote supporting one code, with its provenance verdict from S2.

    ``verified`` and ``score`` are set by the S2 quote locator, never by a model.
    ``span`` is ``None`` exactly when the quote could not be located.
    """

    response_id: int
    quote: str
    span: tuple[int, int] | None = None
    verified: bool = False
    score: float = 0.0

    def to_json(self) -> dict[str, Any]:
        return {
            "response_id": self.response_id,
            "quote": self.quote,
            "span": list(self.span) if self.span is not None else None,
            "verified": self.verified,
            "score": self.score,
        }

    @classmethod
    def from_json(cls, obj: dict[str, Any]) -> Evidence:
        span = obj.get("span")
        return cls(
            response_id=int(obj["response_id"]),
            quote=str(obj["quote"]),
            span=(int(span[0]), int(span[1])) if span else None,
            verified=bool(obj.get("verified", False)),
            score=float(obj.get("score", 0.0)),
        )


@dataclass(frozen=True, slots=True)
class Candidate:
    """What a coder *proposes*, before admission to the codebook.

    A candidate is not a code. The fast loop never *restructures* the codebook; it
    accepts, routes and integrates candidates. ``parent_hint`` is the coder's suggestion of a
    family, honoured only by the integration router, never trusted as structure.
    ``raw`` keeps the model's original object so a decision can be replayed.
    """

    name: str
    description: str
    evidence: list[Evidence] = field(default_factory=list)
    coder: str = ""
    parent_hint: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def family(self) -> str:
        return family_of(self.name)

    def verified_evidence(self) -> list[Evidence]:
        return [e for e in self.evidence if e.verified]

    def to_json(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "evidence": [e.to_json() for e in self.evidence],
            "coder": self.coder,
            "parent_hint": self.parent_hint,
            "raw": dict(self.raw),
        }

    @classmethod
    def from_json(cls, obj: dict[str, Any]) -> Candidate:
        return cls(
            name=str(obj["name"]),
            description=str(obj.get("description", "")),
            evidence=[Evidence.from_json(e) for e in obj.get("evidence") or []],
            coder=str(obj.get("coder", "")),
            parent_hint=obj.get("parent_hint"),
            raw=dict(obj.get("raw") or {}),
        )


# --------------------------------------------------------------------------- #
# Codebook
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class Code:
    """An admitted code. Two-level by convention: ``toplevel-sub_level``.

    ``created_in_snapshot`` replaces the wall-clock ``created_at`` of the predecessor
    codebase: a code's provenance is the snapshot that admitted it, which is
    content-addressed and therefore reproducible. Codebook JSON carries no timestamps,
    which is what makes two runs byte-identical.
    """

    id: str
    name: str
    description: str
    parent_id: str | None = None
    created_in_snapshot: str = ""
    evidence: list[Evidence] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def family(self) -> str:
        return family_of(self.name)

    def response_ids(self) -> list[int]:
        """Sorted distinct response ids this code has verified evidence in."""
        return sorted({e.response_id for e in self.evidence if e.verified})

    def to_json(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "parent_id": self.parent_id,
            "created_in_snapshot": self.created_in_snapshot,
            "evidence": [e.to_json() for e in self.evidence],
            "meta": dict(self.meta),
        }

    @classmethod
    def from_json(cls, obj: dict[str, Any]) -> Code:
        return cls(
            id=str(obj["id"]),
            name=str(obj["name"]),
            description=str(obj.get("description", "")),
            parent_id=obj.get("parent_id"),
            created_in_snapshot=str(obj.get("created_in_snapshot", "")),
            evidence=_evidence_from_json(obj.get("evidence")),
            meta=dict(obj.get("meta") or {}),
        )


def _evidence_from_json(raw: Any) -> list[Evidence]:
    """Parse evidence from either supported shape.

    Canonical shape — a list of Evidence objects::

        [{"response_id": 9, "quote": "...", "span": [3, 20], "verified": true, "score": 1.0}]

    Legacy / spreadsheet shape — a mapping of response id to quotes, where JSON
    round-trips have stringified the integer keys::

        {"9": ["...", "..."], "10": ["..."]}

    Both str and int keys are accepted, per the frozen contract.
    """
    if raw is None:
        return []
    if isinstance(raw, dict):
        out: list[Evidence] = []
        for key in sorted(raw, key=lambda k: int(k)):
            quotes = raw[key]
            if isinstance(quotes, str):
                quotes = [quotes]
            for quote in quotes:
                out.append(Evidence(response_id=int(key), quote=str(quote)))
        return out
    parsed: list[Evidence] = []
    for item in raw:
        if isinstance(item, dict):
            parsed.append(Evidence.from_json(item))
        else:  # a bare string cannot name its response; rejected loudly, never guessed
            raise ValueError(
                "evidence entries must be objects or a {response_id: [quote]} mapping; "
                f"got a bare {type(item).__name__}"
            )
    return parsed


@dataclass(frozen=True, slots=True)
class Codebook:
    """A set of codes keyed by id.

    All accessors return deterministically ordered results — sorted by code name, then
    id — because the codebook is serialised into prompts and into artefacts that must
    be byte-identical across runs.
    """

    codes: dict[str, Code] = field(default_factory=dict)

    # -- lookups ---------------------------------------------------------- #

    def __len__(self) -> int:
        return len(self.codes)

    def __contains__(self, code_id: object) -> bool:
        return code_id in self.codes

    def sorted_codes(self) -> list[Code]:
        return sorted(self.codes.values(), key=lambda c: (c.name, c.id))

    def by_name(self, name: str) -> Code | None:
        """First code with this exact name (names are unique — S6 enforces it)."""
        for code in self.sorted_codes():
            if code.name == name:
                return code
        return None

    def names(self) -> list[str]:
        return [c.name for c in self.sorted_codes()]

    # -- structure -------------------------------------------------------- #

    def children_of(self, code_id: str) -> list[Code]:
        return sorted(
            (c for c in self.codes.values() if c.parent_id == code_id),
            key=lambda c: (c.name, c.id),
        )

    def leaves(self) -> list[Code]:
        """Codes that are no other code's parent."""
        parents = {c.parent_id for c in self.codes.values() if c.parent_id}
        return [c for c in self.sorted_codes() if c.id not in parents]

    def families(self) -> dict[str, list[Code]]:
        """Top-level family name -> its codes, both keys and values sorted.

        Family membership is derived from the code *name* (first-hyphen split), which
        is the canonical grammar. S6 separately checks that ``parent_id`` agrees.
        """
        grouped: dict[str, list[Code]] = {}
        for code in self.sorted_codes():
            grouped.setdefault(code.family, []).append(code)
        return {family: grouped[family] for family in sorted(grouped)}

    def hierarchy_skeleton(self) -> dict[str, list[str]]:
        """Compact structure for a coder prompt: family -> sorted sub-code names.

        Descriptions and evidence are deliberately excluded — the skeleton shows the
        *shape* of the codebook; retrieval supplies the top-k codes in full.
        """
        return {
            family: sorted(sub_of(c.name) for c in members if sub_of(c.name))
            for family, members in self.families().items()
        }

    # -- serialisation ---------------------------------------------------- #

    def to_json(self) -> dict[str, Any]:
        """Deterministic dict form: codes as a name-sorted list, no timestamps."""
        return {"codes": [c.to_json() for c in self.sorted_codes()]}

    def to_json_str(self) -> str:
        """Canonical serialisation — the exact bytes hashed into a snapshot id."""
        return json.dumps(self.to_json(), sort_keys=True, ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, obj: dict[str, Any] | list[Any]) -> Codebook:
        """Load from ``{"codes": [...]}``, a bare list of codes, or ``{id: code}``."""
        if isinstance(obj, list):
            raw_codes: list[Any] = obj
        elif "codes" in obj:
            container = obj["codes"]
            raw_codes = list(container.values()) if isinstance(container, dict) else list(container)
        else:
            raw_codes = list(obj.values())
        codes = [Code.from_json(c) for c in raw_codes]
        return cls(codes={c.id: c for c in codes})


# --------------------------------------------------------------------------- #
# Row-oriented coding (the PI's spreadsheet shape) and slow-loop edits
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class Assignment:
    """One row of a coding spreadsheet: this code was applied to this segment.

    The lingua franca between the PI's hand-codings (the golden set), the standalone
    check CLI, and the analysis tail. Deliberately flat — it is the shape a human can
    produce in Excel without any tooling.
    """

    response_id: int
    segment: str
    code: str

    def to_json(self) -> dict[str, Any]:
        return {"response_id": self.response_id, "segment": self.segment, "code": self.code}

    @classmethod
    def from_json(cls, obj: dict[str, Any]) -> Assignment:
        return cls(
            response_id=int(obj["response_id"]),
            segment=str(obj["segment"]),
            code=str(obj["code"]),
        )


@dataclass(frozen=True, slots=True)
class Operation:
    """One unit of a slow-loop edit script.

    The operation set is deliberately wider than the predecessor study's
    create/merge/rename/no-op, whose narrowness is the documented cause of codebook
    flattening (Ng & Chan 2026): ``split`` and ``reparent`` are what let the
    Refactorer restructure rather than only accrete.

    ``targets`` are code **ids**; ``payload`` carries operation-specific arguments;
    ``rationale`` is the sentence shown to the human at the gate.
    """

    type: OperationType
    targets: list[str] = field(default_factory=list)
    payload: dict[str, Any] = field(default_factory=dict)
    rationale: str = ""

    def to_json(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "targets": list(self.targets),
            "payload": dict(self.payload),
            "rationale": self.rationale,
        }

    @classmethod
    def from_json(cls, obj: dict[str, Any]) -> Operation:
        op_type = str(obj["type"])
        if op_type not in OPERATION_TYPES:
            raise ValueError(f"unknown operation type {op_type!r}; expected one of {OPERATION_TYPES}")
        return cls(
            type=op_type,  # type: ignore[arg-type]
            targets=[str(t) for t in obj.get("targets") or []],
            payload=dict(obj.get("payload") or {}),
            rationale=str(obj.get("rationale", "")),
        )
