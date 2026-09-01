"""The Judge: a frontier model consulted only where the deterministic layers cannot decide.

What this module does. It implements the `Judge` protocol that `gaf.checks.semantic`
declares — three methods, three questions, and no fourth. It is reached from exactly
three places, all of them after the deterministic pass has already run and failed to
resolve the case:

* **M3 fit** — a code-to-evidence pair scored below tau_fit;
* **M1 dispute** — two coders' candidates matched inside the grey band;
* **M2 route** — a candidate whose nearest neighbour sits between tau_low and tau_high.

The judge decides; it never edits. It cannot propose a code, rename one, or refine one:
each method returns a whitelisted verdict and one sentence of reasoning, and the callers
whitelist the verdict again on arrival. A reply this module cannot read becomes the
non-destructive default from `gaf.llm.base.FAIL_SAFE_DEFAULTS` — keep the quote, keep
both candidates, create rather than merge — with `fail_safe` recorded on the result, so
a bad reply is visible in the audit log rather than silently authoritative.

ADR-0019 is the reason the fit path is built the way it is: in the offline lexical space
M3's fit scores have a median of 0.000 and 95% of pairs fall below tau_fit, so in a live
run this method may be called far more often than the cost model assumes. The fit prompt
is therefore the shortest of the three and clips its context; length here is a budget
line, not a style choice.

Validation principles: **epistemic diversity** — a third provider adjudicates what two
coders and one geometry could not; **transparency** — every ruling carries the prompt
version, the subject and the reasoning into the store.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from gaf.agents.prompts.loader import get_template, judge_renderers
from gaf.checks.contracts import FIT_VERDICTS
from gaf.config import RunConfig
from gaf.llm.base import (
    DISPUTE_VERDICTS,
    ROUTE_VERDICTS,
    CallLog,
    LLMClient,
    LLMRequest,
    LLMResult,
    TaskType,
    validate_enum,
)

if TYPE_CHECKING:  # pragma: no cover - a type-level assertion, not runtime behaviour
    from gaf.checks.semantic import Judge

__all__ = [
    "JudgeAgent",
    "JudgeRuling",
    "dispute_subject",
    "fit_subject",
    "route_subject",
]

#: The non-destructive default per question, mirroring `gaf.llm.base.FAIL_SAFE_DEFAULTS`.
#: Read from there in spirit and restated here as the *validation* default: an
#: unparseable fit keeps the quote, an unparseable dispute keeps both candidates, an
#: unparseable route creates rather than merges.
_FIT_DEFAULT = "APPLIES"
_DISPUTE_DEFAULT = "KEEP"
_ROUTE_DEFAULT = "CREATE"


def fit_subject(candidate_name: str, response_id: int | None = None) -> str:
    """`LLMRequest.subject` for an M3 fit ruling."""
    return f"fit:{candidate_name}" if response_id is None else f"fit:{candidate_name}@{response_id}"


def dispute_subject(name_a: str, name_b: str) -> str:
    """`LLMRequest.subject` for an M1 dispute ruling, in the shape M1 uses for pairs."""
    return f"dispute:{name_a}<->{name_b}"


def route_subject(candidate_name: str, neighbour_name: str) -> str:
    """`LLMRequest.subject` for an M2 routing ruling."""
    return f"route:{candidate_name}<->{neighbour_name}"


@dataclass(frozen=True, slots=True)
class JudgeRuling:
    """One adjudication, with everything the audit log needs about how it was reached.

    `key` is ``"verdict"`` for fit and dispute rulings and ``"route"`` for routing ones,
    which is the difference between the two reply shapes the `Judge` protocol declares.
    `to_reply()` produces exactly the dict the protocol's callers expect.
    """

    key: str
    value: str
    reasoning: str
    request: LLMRequest
    result: LLMResult

    @property
    def prompt_version(self) -> str:
        return self.result.prompt_version

    @property
    def subject(self) -> str:
        return self.request.subject

    @property
    def fail_safe(self) -> bool:
        """True when the reply was unreadable and the value is the safe default."""
        return self.result.fail_safe

    def to_reply(self) -> dict[str, str]:
        """The protocol-shaped reply: ``{"verdict"|"route": ..., "reasoning": ...}``."""
        return {self.key: self.value, "reasoning": self.reasoning}

    def to_json(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "reasoning": self.reasoning,
            "subject": self.subject,
            "prompt_version": self.prompt_version,
            "fail_safe": self.fail_safe,
        }


def _reasoning(data: Mapping[str, Any]) -> str:
    """The reasoning sentence, or an empty string. Never a guess at one."""
    text = data.get("reasoning")
    return text if isinstance(text, str) else ""


class JudgeAgent:
    """The frontier judge, bound to one client and one prompt version.

    Satisfies `gaf.checks.semantic.Judge`, so it can be injected straight into M1, M2
    and M3. The three protocol methods return the plain dicts those checks whitelist;
    the three `*_ruling` methods return the same decision with the request and result
    attached, for callers that need to log cost, latency and `fail_safe`.
    """

    def __init__(
        self,
        client: LLMClient,
        *,
        config: RunConfig | None = None,
        prompt_version: str | None = None,
        call_log: CallLog | None = None,
    ) -> None:
        self.client = client
        self.config = config or RunConfig()
        self.template = get_template("judge", prompt_version)
        self._render = judge_renderers(self.template.version)
        self.call_log = call_log

    @property
    def prompt_version(self) -> str:
        return self.template.version

    def _ask(
        self,
        request: LLMRequest,
        *,
        key: str,
        allowed: tuple[str, ...],
        default: str,
    ) -> JudgeRuling:
        """Send one request and whitelist its answer. Never raises, never destroys data."""
        result = self.client.complete_json(request)
        if self.call_log is not None:
            self.call_log.record(result)
        data = result.data if isinstance(result.data, Mapping) else {}
        value = validate_enum(data.get(key), allowed, default)
        return JudgeRuling(
            key=key,
            value=value,
            reasoning=_reasoning(data),
            request=request,
            result=result,
        )

    # -- M3: code-to-evidence fit ----------------------------------------- #

    def fit_ruling(
        self,
        *,
        candidate_name: str,
        candidate_description: str,
        quote: str,
        response_text: str,
        response_id: int | None = None,
    ) -> JudgeRuling:
        """Adjudicate one code-to-evidence pairing (M3).

        The four verdicts mirror the PI's negative-example taxonomy exactly. Note what
        is *not* asked for: a replacement code. On IMPRECISE or INCOMPLETE the verdict
        and the reasoning are the entire deliverable, because refinement is slow-loop
        and human work.
        """
        prompt = self._render.fit(
            candidate_name=candidate_name,
            candidate_description=candidate_description,
            quote=quote,
            response_text=response_text,
        )
        request = prompt.to_request(
            TaskType.JUDGE_FIT, subject=fit_subject(candidate_name, response_id)
        )
        return self._ask(request, key="verdict", allowed=FIT_VERDICTS, default=_FIT_DEFAULT)

    # -- M1: cross-coder dispute ------------------------------------------ #

    def dispute_ruling(
        self,
        *,
        candidate_a: Mapping[str, Any],
        candidate_b: Mapping[str, Any],
        response_text: str,
    ) -> JudgeRuling:
        """Adjudicate a grey-zone disagreement between the two coders (M1)."""
        prompt = self._render.dispute(
            candidate_a=candidate_a,
            candidate_b=candidate_b,
            response_text=response_text,
            rules=self.config.rules,
        )
        request = prompt.to_request(
            TaskType.JUDGE_DISPUTE,
            subject=dispute_subject(
                str(candidate_a.get("name", "")), str(candidate_b.get("name", ""))
            ),
        )
        return self._ask(
            request, key="verdict", allowed=DISPUTE_VERDICTS, default=_DISPUTE_DEFAULT
        )

    # -- M2: grey-zone integration routing -------------------------------- #

    def route_ruling(
        self,
        *,
        candidate_name: str,
        candidate_description: str,
        neighbour_name: str,
        neighbour_description: str,
        score: float,
    ) -> JudgeRuling:
        """Decide whether a grey-zone candidate merges into its neighbour or is new (M2)."""
        prompt = self._render.route(
            candidate_name=candidate_name,
            candidate_description=candidate_description,
            neighbour_name=neighbour_name,
            neighbour_description=neighbour_description,
            score=score,
            rules=self.config.rules,
        )
        request = prompt.to_request(
            TaskType.JUDGE_ROUTE, subject=route_subject(candidate_name, neighbour_name)
        )
        return self._ask(request, key="route", allowed=ROUTE_VERDICTS, default=_ROUTE_DEFAULT)

    # -- the `Judge` protocol --------------------------------------------- #
    #
    # Signatures are copied from `gaf.checks.semantic.Judge` verbatim, down to the bare
    # `dict` annotations, so that conformance is structural rather than approximate.

    def rule_on_fit(
        self,
        *,
        candidate_name: str,
        candidate_description: str,
        quote: str,
        response_text: str,
    ) -> dict:
        """-> ``{"verdict": one of FIT_VERDICTS, "reasoning": str}`` (M3)."""
        return self.fit_ruling(
            candidate_name=candidate_name,
            candidate_description=candidate_description,
            quote=quote,
            response_text=response_text,
        ).to_reply()

    def rule_on_dispute(
        self,
        *,
        candidate_a: dict,
        candidate_b: dict,
        response_text: str,
    ) -> dict:
        """-> ``{"verdict": "KEEP" | "DROP", "reasoning": str}`` (M1 grey zone)."""
        return self.dispute_ruling(
            candidate_a=candidate_a,
            candidate_b=candidate_b,
            response_text=response_text,
        ).to_reply()

    def rule_on_route(
        self,
        *,
        candidate_name: str,
        candidate_description: str,
        neighbour_name: str,
        neighbour_description: str,
        score: float,
    ) -> dict:
        """-> ``{"route": "MERGE" | "CREATE", "reasoning": str}`` (M2 grey zone)."""
        return self.route_ruling(
            candidate_name=candidate_name,
            candidate_description=candidate_description,
            neighbour_name=neighbour_name,
            neighbour_description=neighbour_description,
            score=score,
        ).to_reply()


if TYPE_CHECKING:  # pragma: no cover - checked by mypy, never executed

    def _judge_conformance(agent: JudgeAgent) -> Judge:
        """Type-level proof that `JudgeAgent` satisfies the protocol M1-M3 inject.

        `tests/test_agents.py` asserts the same thing at runtime with `isinstance`; this
        makes a drifting signature a type error rather than a test failure one wave later.
        """
        return agent
