"""The LLM client protocol and the shared safety net around every model call.

FROZEN CONTRACT (Wave 0). No Wave 1+ agent may change this module.

One method, `complete_json`, returning parsed JSON. Around it sit the four things that
must behave identically for every provider and every role:

* **markdown-fence stripping** — models wrap JSON in ``` fences regardless of instruction;
* **whitelist validation of enum-valued fields** — a verdict outside the whitelist is
  not a verdict;
* **a fail-safe default per task type** — a malformed reply must never destroy data.
  Every default in `FAIL_SAFE_DEFAULTS` is the *non-destructive* option: an unparseable
  fit ruling keeps the quote, an unparseable dispute keeps both candidates, an
  unparseable route creates rather than merges (a spurious new code is visible to M4
  and recoverable at the human gate; a spurious merge silently destroys a distinction),
  an unparseable coding returns nothing rather than inventing codes, and an unparseable
  refactor is an empty edit script;
* **retry with deterministic jitter** and **per-call cost/latency accounting**.

Every prompt is built from a versioned template, and its version id is recorded with
the call, so a change of wording is a visible event rather than silent drift.

Validation principle: **transparency** — every call is a row with a prompt version, a
token count, a cost and a latency; **reliability** — no reply, however malformed, can
change state in a way the audit log does not explain.
"""

from __future__ import annotations

import json
import random
import re
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, runtime_checkable

from gaf.config import ModelSpec

__all__ = [
    "FAIL_SAFE_DEFAULTS",
    "CallLog",
    "LLMClient",
    "LLMError",
    "LLMRequest",
    "LLMResult",
    "MalformedReplyError",
    "TaskType",
    "fail_safe_for",
    "parse_json_object",
    "retry_with_jitter",
    "strip_fences",
    "validate_enum",
]


class TaskType(Enum):
    """What a call is for. Determines the fail-safe default and the accounting bucket."""

    CODE = "code"  # Coder: propose candidates for one response
    JUDGE_DISPUTE = "judge_dispute"  # M1: coders disagree — keep or drop
    JUDGE_ROUTE = "judge_route"  # M2: grey-zone integration — merge or create
    JUDGE_FIT = "judge_fit"  # M3: does this code fit this quote
    REFACTOR = "refactor"  # Slow loop: propose an edit script

    def __str__(self) -> str:
        return self.value


class LLMError(RuntimeError):
    """Transport-level failure after retries are exhausted."""


class MalformedReplyError(ValueError):
    """The reply was not a JSON object, even after fence stripping."""


# --------------------------------------------------------------------------- #
# Request / result
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class LLMRequest:
    """One stateless call. `prompt_version` identifies the template that built it."""

    task: TaskType
    system: str
    user: str
    prompt_version: str
    #: Stable identifier of what the call is about (response id, pair, code id) —
    #: written to the audit log so a call can be traced back to its subject.
    subject: str = ""
    max_output_tokens: int | None = None
    temperature: float | None = None

    def cache_key_parts(self) -> tuple[str, ...]:
        """The parts a content-addressed cache must hash. No timestamps, no run ids."""
        return (
            self.task.value,
            self.prompt_version,
            self.system,
            self.user,
            str(self.max_output_tokens),
            str(self.temperature),
        )


@dataclass(frozen=True, slots=True)
class LLMResult:
    """A parsed reply plus everything the audit log needs about how it was obtained."""

    data: dict[str, Any]
    task: TaskType
    provider: str
    model: str
    prompt_version: str
    raw_text: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    cache_hit: bool = False
    #: True when parsing failed and `data` is the fail-safe default for the task.
    fail_safe: bool = False
    attempts: int = 1

    def to_json(self) -> dict[str, Any]:
        return {
            "task": self.task.value,
            "provider": self.provider,
            "model": self.model,
            "prompt_version": self.prompt_version,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost_usd": self.cost_usd,
            "latency_ms": self.latency_ms,
            "cache_hit": self.cache_hit,
            "fail_safe": self.fail_safe,
            "attempts": self.attempts,
        }


@runtime_checkable
class LLMClient(Protocol):
    """One method. Everything else is shared machinery in this module."""

    spec: ModelSpec

    def complete_json(self, request: LLMRequest) -> LLMResult:
        """Send `request`, return a parsed JSON object.

        Implementations must never raise on a malformed reply: they fall back to
        `fail_safe_for(request.task)` and set `LLMResult.fail_safe = True`.
        """
        ...


# --------------------------------------------------------------------------- #
# Parsing helpers
# --------------------------------------------------------------------------- #

_FENCE_RE = re.compile(r"^\s*```(?:json|JSON)?\s*\n?(.*?)\n?\s*```\s*$", re.DOTALL)


def strip_fences(text: str) -> str:
    """Remove a surrounding markdown code fence, if present. Idempotent."""
    match = _FENCE_RE.match(text)
    return match.group(1).strip() if match else text.strip()


def parse_json_object(text: str) -> dict[str, Any]:
    """Parse a JSON object out of a model reply.

    Tries the whole (fence-stripped) string first, then the outermost ``{...}`` span,
    which rescues replies with a leading apology or a trailing explanation. Raises
    `MalformedReplyError` rather than returning a partial object.
    """
    cleaned = strip_fences(text)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start == -1 or end <= start:
            raise MalformedReplyError(f"no JSON object in reply: {cleaned[:200]!r}") from None
        try:
            parsed = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError as exc:
            raise MalformedReplyError(f"unparseable JSON in reply: {exc}") from None
    if not isinstance(parsed, dict):
        raise MalformedReplyError(f"expected a JSON object, got {type(parsed).__name__}")
    return parsed


def validate_enum(value: Any, allowed: Sequence[str], default: str) -> str:
    """Coerce `value` to one of `allowed`, falling back to `default`.

    Case-insensitive and whitespace-tolerant, because the failure this guards against
    is a model writing ``"applies"`` or ``" APPLIES "``. Anything genuinely outside the
    whitelist becomes `default` — a verdict the system does not recognise is not a
    verdict, and must not be allowed to act.
    """
    if isinstance(value, str):
        needle = value.strip().upper()
        for option in allowed:
            if option.upper() == needle:
                return option
    return default


# --------------------------------------------------------------------------- #
# Fail-safe defaults — a malformed reply must never destroy data
# --------------------------------------------------------------------------- #

#: Whitelists for the judge's enum-valued replies. They live here, beside the
#: fail-safe defaults, so that every client and every check validates against one
#: definition — the alternative is a copy per provider module, which is how a
#: whitelist quietly drifts. `FIT_VERDICTS` lives in `gaf.checks.contracts`, next to
#: the taxonomy it mirrors.
DISPUTE_VERDICTS: tuple[str, ...] = ("KEEP", "DROP")
ROUTE_VERDICTS: tuple[str, ...] = ("MERGE", "CREATE")

FAIL_SAFE_DEFAULTS: dict[TaskType, dict[str, Any]] = {
    # Invent nothing: an unreadable coding contributes no candidates.
    TaskType.CODE: {"candidates": [], "_fail_safe": True},
    # Keep both sides of the dispute; the human gate sees the WARN.
    TaskType.JUDGE_DISPUTE: {"verdict": "KEEP", "reasoning": "fail-safe: unparseable reply"},
    # Create rather than merge: a spurious code is recoverable, a spurious merge is not.
    TaskType.JUDGE_ROUTE: {"route": "CREATE", "reasoning": "fail-safe: unparseable reply"},
    # Keep the quote. Never lose evidence to a parse error.
    TaskType.JUDGE_FIT: {"verdict": "APPLIES", "reasoning": "fail-safe: unparseable reply"},
    # An unreadable refactor proposal is a no-op edit script.
    TaskType.REFACTOR: {"operations": [], "reasoning": "fail-safe: unparseable reply"},
}


def fail_safe_for(task: TaskType) -> dict[str, Any]:
    """A fresh copy of the non-destructive default for `task`."""
    return json.loads(json.dumps(FAIL_SAFE_DEFAULTS[task]))


# --------------------------------------------------------------------------- #
# Retry and accounting
# --------------------------------------------------------------------------- #

def retry_with_jitter[T](
    call: Callable[[], T],
    *,
    attempts: int = 3,
    base_delay_s: float = 0.5,
    seed: int = 0,
    sleep: Callable[[float], None] = time.sleep,
) -> tuple[T, int]:
    """Call `call`, retrying transient failures with seeded exponential backoff.

    The jitter is drawn from a `random.Random(seed)` rather than the global RNG so a
    retry storm cannot make a run non-reproducible. Offline runs never retry: mock
    clients do not fail. Returns `(result, attempts_used)`.
    """
    if attempts < 1:
        raise ValueError("attempts must be >= 1")
    rng = random.Random(seed)
    last: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return call(), attempt
        except Exception as exc:
            last = exc
            if attempt == attempts:
                break
            sleep(base_delay_s * (2 ** (attempt - 1)) * (1.0 + rng.random()))
    raise LLMError(f"call failed after {attempts} attempts: {last}") from last


@dataclass
class CallLog:
    """Per-run accounting for model calls. Printed in the run report, stored in SQLite."""

    results: list[LLMResult] = field(default_factory=list)

    def record(self, result: LLMResult) -> LLMResult:
        self.results.append(result)
        return result

    @property
    def calls(self) -> int:
        return len(self.results)

    @property
    def cost_usd(self) -> float:
        return sum(r.cost_usd for r in self.results)

    @property
    def cache_hits(self) -> int:
        return sum(1 for r in self.results if r.cache_hit)

    @property
    def fail_safes(self) -> int:
        return sum(1 for r in self.results if r.fail_safe)

    def by_task(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for result in self.results:
            counts[result.task.value] = counts.get(result.task.value, 0) + 1
        return {k: counts[k] for k in sorted(counts)}

    def summary(self) -> dict[str, Any]:
        return {
            "calls": self.calls,
            "by_task": self.by_task(),
            "cache_hits": self.cache_hits,
            "fail_safes": self.fail_safes,
            "input_tokens": sum(r.input_tokens for r in self.results),
            "output_tokens": sum(r.output_tokens for r in self.results),
            "cost_usd": round(self.cost_usd, 6),
            "latency_ms_total": round(sum(r.latency_ms for r in self.results), 3),
        }
