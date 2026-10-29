"""A spend cap for live model calls (ADR-0053).

`--max-usd` is a hard stop on money, and the one question it asks is the one asked
here: *before this call starts, has the billed spend already reached the cap?* If so the
call is not made and `BudgetExceededError` is raised for the caller to turn into a clean,
resumable halt. If not, the call is made and its `cost_usd` is added to the running
total. **The cap is checked before a call and never during one, so the overshoot is at
most the cost of the single call that was in flight when the total crossed the cap.**
That is stated in the help text and the ADR because it is the honest bound: nothing can
recall a request already sent.

Three properties make the guard safe to put in front of a paid run.

* **A cache replay never counts.** `BudgetedLLMClient` sits *inside*
  `CachingLLMClient`, so a hit is answered from disk and never reaches the guard; and a
  replay's `cost_usd` is zero anyway. A resumed run that re-asks questions it already
  paid for spends nothing, and the cap says so by not moving.
* **It counts the run, not the process.** The total starts at a `baseline_usd` the caller
  reads from the blackboard (`gaf.cli._budget.cumulative_spend`), so a run resumed with
  `--skip-coded`, or a checkpoint opened on a run that already spent money, continues
  the same budget instead of starting a fresh one.
* **Mock and local clients cost nothing**, so an offline run, or one on local models,
  never trips it. The converse is the trap: a *hosted* model with no price set would
  also cost "nothing" and make the cap decorative, so `unpriced_hosted_roles` lets the
  CLI refuse that configuration up front.

The exception is deliberately not an `LLMError`. `LLMError` means "the transport failed
after retries", and callers are entitled to treat that as a fault; a spend cap is a
decision, and nothing between the guard and the CLI may swallow it as a fault.

Validation principle: **reliability** — a run that cannot be stopped from spending is not
one anybody should start with a key in the environment.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from gaf.config import ModelRegistry, ModelSpec
from gaf.llm.base import LLMClient, LLMRequest, LLMResult
from gaf.llm.cache import CachingLLMClient

__all__ = [
    "BudgetExceededError",
    "BudgetedLLMClient",
    "SpendBudget",
    "guard_agents",
    "guard_client",
    "unpriced_hosted_roles",
]

#: Providers whose calls are legitimately free: a mock answers from arithmetic and a
#: local model runs on this machine. Any other provider with both rates at zero is a
#: misconfiguration, not a bargain.
_FREE_PROVIDERS = frozenset({"mock", "local"})


class BudgetExceededError(Exception):
    """The next model call would start with the spend cap already reached.

    Carries the numbers the halt message and the audit row need, so no caller has to
    reach back into the budget to describe what happened.
    """

    def __init__(self, *, cap_usd: float, cumulative_usd: float, role: str = "", task: str = ""):
        self.cap_usd = cap_usd
        self.cumulative_usd = cumulative_usd
        self.role = role
        self.task = task
        super().__init__(
            f"spend cap reached: ${cumulative_usd:.4f} billed against a cap of "
            f"${cap_usd:.4f}; no further model call was made"
        )


@dataclass(slots=True)
class SpendBudget:
    """A running total against a cap. One per command, shared by every client in it.

    `baseline_usd` is spend recorded *before* this process started (a previous run in the
    same chain, or this run's earlier commands); `run_usd` is what this process has
    billed since. Their sum is `cumulative_usd`, the number the cap is compared with.
    """

    cap_usd: float
    baseline_usd: float = 0.0
    run_usd: float = 0.0
    #: Where `baseline_usd` came from, as ``{"run": <directory>, "usd": <spend>}`` rows.
    #: Directories and amounts only; recorded so a reader can see what the cap counted.
    baseline_sources: list[dict[str, Any]] = field(default_factory=list)
    #: The first refusal this budget issued, or `None` while the cap has not been hit.
    tripped: BudgetExceededError | None = None

    def __post_init__(self) -> None:
        if not math.isfinite(self.cap_usd) or self.cap_usd <= 0:
            raise ValueError(f"the spend cap must be a positive amount, got {self.cap_usd!r}")
        if not math.isfinite(self.baseline_usd) or self.baseline_usd < 0:
            raise ValueError(f"the baseline spend cannot be negative, got {self.baseline_usd!r}")

    @property
    def cumulative_usd(self) -> float:
        return self.baseline_usd + self.run_usd

    @property
    def remaining_usd(self) -> float:
        return max(self.cap_usd - self.cumulative_usd, 0.0)

    @property
    def exhausted(self) -> bool:
        """Whether the cap has been reached. ``>=``: reaching it is enough to stop."""
        return self.cumulative_usd >= self.cap_usd

    def check(self, *, role: str = "", task: str = "") -> None:
        """Raise `BudgetExceededError` if no further call may start."""
        if self.exhausted:
            refusal = BudgetExceededError(
                cap_usd=self.cap_usd,
                cumulative_usd=self.cumulative_usd,
                role=role,
                task=task,
            )
            self.tripped = self.tripped or refusal
            raise refusal

    def charge(self, cost_usd: float) -> None:
        """Add one billed call's cost. A replay or a mock call adds nothing."""
        if cost_usd > 0:
            self.run_usd += cost_usd

    def to_json(self) -> dict[str, Any]:
        """The record that goes on the run's stats and, on a halt, its audit row."""
        return {
            "cap_usd": round(self.cap_usd, 6),
            "baseline_usd": round(self.baseline_usd, 6),
            "run_usd": round(self.run_usd, 6),
            "cumulative_usd": round(self.cumulative_usd, 6),
            "halted": self.tripped is not None,
            "baseline_sources": [dict(row) for row in self.baseline_sources],
        }


class BudgetedLLMClient:
    """An `LLMClient` that refuses to start a call once the cap has been reached.

    Delegates everything else — `spec` included — to the client it wraps. It must sit
    *below* `CachingLLMClient` (see `guard_client`), so that only a call that will
    really be made is ever checked or charged.
    """

    def __init__(self, inner: LLMClient, budget: SpendBudget) -> None:
        self.inner = inner
        self.budget = budget
        self.spec: ModelSpec = inner.spec

    def complete_json(self, request: LLMRequest) -> LLMResult:
        self.budget.check(role=self.spec.role, task=request.task.value)
        result = self.inner.complete_json(request)
        self.budget.charge(0.0 if result.cache_hit else result.cost_usd)
        return result


def guard_client(client: LLMClient, budget: SpendBudget) -> LLMClient:
    """Put the guard in front of the model, and behind the cache when there is one.

    A `CachingLLMClient` is returned as itself with its `inner` wrapped, so a hit is
    still answered from disk without a check; any other client is wrapped directly (the
    `--no-cache` case, where every call is a billed call). Idempotent: a client that is
    already guarded by this budget is returned unchanged.
    """
    if isinstance(client, CachingLLMClient):
        client.inner = guard_client(client.inner, budget)
        return client
    if isinstance(client, BudgetedLLMClient) and client.budget is budget:
        return client
    return BudgetedLLMClient(client, budget)


def guard_agents(budget: SpendBudget, agents: Iterable[Any]) -> None:
    """Guard the `client` of every agent given; ``None`` entries (no judge) are skipped.

    Agents expose their client as a public `.client`, and rebinding it here is what lets
    one function cover `gaf run`, `gaf checkpoint`, `gaf codebook define` and `gaf check`
    without each command's client factory knowing the cap exists.
    """
    for agent in agents:
        if agent is not None:
            agent.client = guard_client(agent.client, budget)


def unpriced_hosted_roles(models: ModelRegistry) -> list[ModelSpec]:
    """Hosted roles whose two rates are both zero, so a cap could not see their spend.

    A hosted model is billed. If its `ModelSpec` carries no price, `cost_usd` is zero for
    every call and `--max-usd` would never trip, which is the one way the cap can fail
    silently. Mock and local roles are free by construction and are not listed.
    """
    return [
        spec
        for spec in models.all_specs()
        if spec.provider not in _FREE_PROVIDERS
        and spec.input_usd_per_mtok == 0.0
        and spec.output_usd_per_mtok == 0.0
    ]
