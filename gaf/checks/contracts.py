"""Check reporting contracts — Severity, CheckFinding, CheckReport, FitVerdict.

FROZEN CONTRACT (Wave 0). No Wave 1+ agent may change this module.

The one rule this module exists to enforce: **a checker reports, the router and the
audit log decide and record**. Every check in the system — structural, semantic,
health — returns a `CheckReport` and nothing else. There are no print-only diagnostics
buried in modules and no checker that mutates state.

Validation principle: **transparency** — a finding is a row with a check id, a
severity, a subject and machine-readable data, so a methods reviewer can audit the
run line by line rather than reading prose.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

__all__ = [
    "CHECK_IDS",
    "FIT_VERDICTS",
    "SCOPES",
    "SEMANTIC_CHECK_IDS",
    "STRUCTURAL_CHECK_IDS",
    "CheckFinding",
    "CheckReport",
    "FitVerdict",
    "Severity",
]


class Severity(Enum):
    """How much a finding is allowed to cost.

    ERROR is reserved for *structural certainty of invalidity* — a quote that is not
    in the source, a name that is not unique, a parent that does not exist. Anything
    that requires a judgment about meaning is at most a WARN, because the structural
    layer does not make meaning judgments.
    """

    ERROR = "ERROR"  # structural certainty of invalidity -> candidate dropped / CLI exit 1
    WARN = "WARN"  # rule violated but judgment-dependent -> kept, flagged for the human
    INFO = "INFO"  # observation (fuzzy match, band assignment, fit score)

    def __str__(self) -> str:
        return self.value


#: The four verdicts of the M3 code<->evidence fit ruling. They mirror the PI's own
#: negative-example taxonomy in `GPTPrompts.docx` — see `docs/CODING_RULES.md`:
#:   APPLIES     - keep (INFO)
#:   IMPRECISE   - "your code was not precise enough"       -> keep, WARN
#:   INCOMPLETE  - "did not describe the response segment completely" -> keep, WARN
#:   UNNECESSARY - "your code did not have to be applied"   -> remove that quote
FitVerdict = str
FIT_VERDICTS: tuple[str, ...] = ("APPLIES", "IMPRECISE", "INCOMPLETE", "UNNECESSARY")

STRUCTURAL_CHECK_IDS: tuple[str, ...] = ("S1", "S2", "S2b", "S3", "S4", "S5", "S6")
SEMANTIC_CHECK_IDS: tuple[str, ...] = ("M1", "M2", "M3", "M4")
CHECK_IDS: tuple[str, ...] = STRUCTURAL_CHECK_IDS + SEMANTIC_CHECK_IDS

#: Valid `CheckFinding.scope` values.
SCOPES: tuple[str, ...] = ("candidate", "segment", "response", "pair", "codebook")


@dataclass(frozen=True, slots=True)
class CheckFinding:
    """One observation about one subject, from one check."""

    check_id: str  # "S1".."S6", "M1".."M4"
    severity: Severity
    scope: str  # "candidate" | "segment" | "response" | "pair" | "codebook"
    subject: str  # candidate/code name, response id, or pair "A<->B"
    message: str  # one human-readable sentence
    data: dict[str, Any] = field(default_factory=dict)  # scores, spans, ids

    def to_json(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "severity": self.severity.value,
            "scope": self.scope,
            "subject": self.subject,
            "message": self.message,
            "data": dict(self.data),
        }

    @classmethod
    def from_json(cls, obj: dict[str, Any]) -> CheckFinding:
        return cls(
            check_id=str(obj["check_id"]),
            severity=Severity(obj["severity"]),
            scope=str(obj["scope"]),
            subject=str(obj["subject"]),
            message=str(obj["message"]),
            data=dict(obj.get("data") or {}),
        )

    def __str__(self) -> str:
        return f"[{self.severity}] {self.check_id} {self.scope}:{self.subject} — {self.message}"


@dataclass
class CheckReport:
    """An ordered accumulation of findings.

    Mutable by design — it is a growing log, not a value object — but it holds only
    findings. It has no reference to the codebook, the store or the router, which is
    what structurally prevents a checker from deciding anything.
    """

    findings: list[CheckFinding] = field(default_factory=list)

    def add(
        self,
        check_id: str,
        severity: Severity,
        scope: str,
        subject: str,
        message: str,
        **data: Any,
    ) -> CheckFinding:
        """Append one finding and return it."""
        finding = CheckFinding(
            check_id=check_id,
            severity=severity,
            scope=scope,
            subject=subject,
            message=message,
            data=data,
        )
        self.findings.append(finding)
        return finding

    def errors(self) -> list[CheckFinding]:
        return [f for f in self.findings if f.severity is Severity.ERROR]

    def warnings(self) -> list[CheckFinding]:
        return [f for f in self.findings if f.severity is Severity.WARN]

    def infos(self) -> list[CheckFinding]:
        return [f for f in self.findings if f.severity is Severity.INFO]

    def passed(self) -> bool:
        """True when no ERROR was found. This is the CLI's exit-code question."""
        return not any(f.severity is Severity.ERROR for f in self.findings)

    def extend(self, other: CheckReport) -> None:
        """Append every finding of `other`, preserving order."""
        self.findings.extend(other.findings)

    def by_check(self, check_id: str) -> list[CheckFinding]:
        return [f for f in self.findings if f.check_id == check_id]

    def summary(self) -> dict[str, dict[str, int]]:
        """Counts by check_id x severity, deterministically ordered.

        ``{"S2": {"ERROR": 1, "INFO": 3}, "M3": {"WARN": 2}}``
        """
        counter: Counter[tuple[str, str]] = Counter(
            (f.check_id, f.severity.value) for f in self.findings
        )
        out: dict[str, dict[str, int]] = {}
        for check_id, severity in sorted(counter):
            out.setdefault(check_id, {})[severity] = counter[(check_id, severity)]
        return out

    def totals(self) -> dict[str, int]:
        """Overall counts by severity, always with all three keys present."""
        counter: Counter[str] = Counter(f.severity.value for f in self.findings)
        return {s.value: counter.get(s.value, 0) for s in Severity}

    def to_json(self) -> list[dict[str, Any]]:
        return [f.to_json() for f in self.findings]

    @classmethod
    def from_json(cls, rows: list[dict[str, Any]]) -> CheckReport:
        return cls(findings=[CheckFinding.from_json(r) for r in rows])

    def __len__(self) -> int:
        return len(self.findings)

    def __iter__(self):  # type: ignore[no-untyped-def]
        return iter(self.findings)
