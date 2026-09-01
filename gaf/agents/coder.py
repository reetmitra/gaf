"""The Coder: one stateless call that proposes candidates for one response.

What this module does. It assembles the context deterministic prep has already gathered
— the survey question, the normalised response, a frozen snapshot's hierarchy skeleton
and its retrieved codes, the PI's rules — into one versioned prompt, sends it through an
injected `LLMClient`, and parses the reply into `Candidate` objects. It writes nothing,
retrieves nothing and decides nothing: a coder proposes, and the fast loop's checks and
router dispose.

Two coders from **different providers** run over the same response. The design demands
that they receive *identical* context, because their disagreement is simultaneously the
epistemic-diversity mechanism and the router's escalation signal — any asymmetry in the
prompt would make cross-coder agreement a measurement of the wording rather than of the
models. So `build_request` is a pure function of `CoderContext` and the config: for one
response the two coders' `LLMRequest` objects are byte-identical, and the only thing
that differs between them is which client they are handed to. `tests/test_agents.py`
asserts that equality.

Three further properties this module is responsible for:

* **Quotes are verbatim.** The prompt instructs it and S2 verifies it; nothing here
  repairs a quote, because a silently repaired quote is a fabricated span.
* **Nothing is invented on a bad reply.** A malformed candidate is skipped and a
  malformed reply yields no candidates at all, per `FAIL_SAFE_DEFAULTS[TaskType.CODE]`.
  Parsing never raises.
* **Human corrections are held out by default** (`RunConfig.recycle_human_corrections`,
  brief §16.6). They can be recycled as few-shot examples, but recycling the golden set
  into the prompt is what stops it being an independent verification set, so the
  default is off and turning it on is a config event recorded with the run.

Validation principles: **epistemic diversity** — identical context for two providers;
**transparency** — every call carries its prompt version and its subject into the
`llm_calls` table.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from gaf.agents.prompts.base import RenderedPrompt
from gaf.agents.prompts.loader import coder_renderer, get_template
from gaf.config import RunConfig
from gaf.llm.base import CallLog, LLMClient, LLMRequest, LLMResult, TaskType
from gaf.models import Assignment, Candidate, Code, Response
from gaf.store.snapshot import Snapshot
from gaf.textnorm import normalise

__all__ = [
    "CoderAgent",
    "CoderContext",
    "CodingProposal",
    "parse_candidates",
    "subject_for",
]


def subject_for(response_id: int) -> str:
    """`LLMRequest.subject` for a coding call.

    The response id is the first integer in the string, which is the convention the
    offline mock reads it back with. It carries no coder label: the two coders differ in
    their model binding, not in what the call is about, and the provider and model are
    already recorded on the result.
    """
    return f"response:{response_id}"


@dataclass(frozen=True, slots=True)
class CoderContext:
    """Everything a coder is allowed to see, assembled by deterministic prep.

    `snapshot_id` is read, never written: the codebook is frozen for the batch, and the
    coder's job is to propose against it. `retrieved` is the top-k the matcher already
    chose — the agent does no retrieval of its own, because two notions of "nearest"
    would be two geometries.
    """

    response: Response
    snapshot_id: str
    skeleton: Mapping[str, Sequence[str]] = field(default_factory=dict)
    retrieved: tuple[Code, ...] = ()

    @classmethod
    def from_snapshot(
        cls,
        response: Response,
        snapshot: Snapshot,
        retrieved_ids: Sequence[str] = (),
    ) -> CoderContext:
        """Build the context from a frozen snapshot and the ids retrieval ranked.

        Handoffs carry ids, not prose: the caller passes code ids in rank order and the
        codes themselves are re-grounded from the snapshot here. An id that is not in
        the snapshot is skipped rather than raising — a stale retrieval result is a
        thinner prompt, not a failed run.
        """
        codes = tuple(
            snapshot.codebook.codes[code_id]
            for code_id in retrieved_ids
            if code_id in snapshot.codebook.codes
        )
        return cls(
            response=response,
            snapshot_id=snapshot.snapshot_id,
            skeleton=snapshot.hierarchy_skeleton(),
            retrieved=codes,
        )


@dataclass(frozen=True, slots=True)
class CodingProposal:
    """One coder's pass over one response: the candidates, and how they were obtained.

    `request` and `result` are both returned so the caller can write the `codings` row
    and the `llm_calls` row without re-deriving either — `request.subject` and
    `result.prompt_version` are exactly what those tables want.
    """

    candidates: list[Candidate]
    request: LLMRequest
    result: LLMResult

    @property
    def coder(self) -> str:
        """The role binding that produced these candidates ("coder_a" / "coder_b")."""
        return self.candidates[0].coder if self.candidates else ""

    @property
    def prompt_version(self) -> str:
        return self.result.prompt_version

    @property
    def subject(self) -> str:
        return self.request.subject

    @property
    def fail_safe(self) -> bool:
        """True when the reply could not be parsed and no candidate was proposed."""
        return self.result.fail_safe

    def raw(self) -> dict[str, Any]:
        """The model's own object, for `CodingRecord.raw` — a decision can be replayed."""
        return dict(self.result.data)


def parse_candidates(
    data: Mapping[str, Any],
    *,
    response_id: int,
    coder: str = "",
) -> list[Candidate]:
    """Parse a coder reply into candidates. Never raises; skips what it cannot read.

    A candidate without a usable name is dropped, because a nameless code cannot be
    matched, routed or reported. Evidence entries without a quote are dropped for the
    same reason; an entry whose `response_id` is missing or unreadable is attributed to
    the response actually being coded, which is the only response the coder was shown.

    Nothing here validates a quote against the source text — that is S2's job, and doing
    it twice in two places is how two answers to one question appear.
    """
    raw_candidates = data.get("candidates")
    if not isinstance(raw_candidates, Sequence) or isinstance(raw_candidates, str | bytes):
        return []

    parsed: list[Candidate] = []
    for item in raw_candidates:
        if not isinstance(item, Mapping):
            continue
        name = str(item.get("name", "")).strip()
        if not name:
            continue
        parent_hint = item.get("parent_hint")
        parsed.append(
            Candidate.from_json(
                {
                    "name": name,
                    "description": str(item.get("description", "")).strip(),
                    "evidence": _parse_evidence(item.get("evidence"), response_id),
                    "coder": coder,
                    "parent_hint": str(parent_hint) if parent_hint else None,
                    "raw": dict(item),
                }
            )
        )
    return parsed


def _parse_evidence(raw: Any, response_id: int) -> list[dict[str, Any]]:
    """Coerce an evidence list into the shape `Evidence.from_json` accepts."""
    if not isinstance(raw, Sequence) or isinstance(raw, str | bytes):
        return []
    entries: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, Mapping):
            continue
        quote = str(item.get("quote", ""))
        if not quote.strip():
            continue
        entries.append(
            {
                "response_id": _as_response_id(item.get("response_id"), response_id),
                "quote": quote,
            }
        )
    return entries


def _as_response_id(value: Any, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


class CoderAgent:
    """One coder binding: a client, a prompt version, and the rules it renders.

    Stateless between calls by construction — nothing is carried from one response to
    the next, and every call re-grounds from the snapshot and the response it is given.
    Two instances differing only in their client are the two coders of the fast loop.
    """

    def __init__(
        self,
        client: LLMClient,
        *,
        config: RunConfig | None = None,
        prompt_version: str | None = None,
        corrections: Sequence[Assignment] = (),
        call_log: CallLog | None = None,
    ) -> None:
        self.client = client
        self.config = config or RunConfig()
        self.template = get_template("coder", prompt_version)
        self._render = coder_renderer(self.template.version)
        self.call_log = call_log
        #: Held out unless the run explicitly asks for them (brief §16.6). Recycling the
        #: PI's corrections as few-shot examples makes the golden set no longer an
        #: independent check on the machine coding, so the default is to hold them out.
        self.corrections: tuple[Assignment, ...] = (
            tuple(corrections) if self.config.recycle_human_corrections else ()
        )

    @property
    def prompt_version(self) -> str:
        return self.template.version

    @property
    def coder(self) -> str:
        """The role this binding codes as: "coder_a" or "coder_b"."""
        return self.client.spec.role

    def render(self, context: CoderContext) -> str:
        """The user half of the prompt. Exposed so a run report can print what was sent."""
        return self._prompt(context).user

    def _prompt(self, context: CoderContext) -> RenderedPrompt:
        return self._render(
            response=context.response,
            snapshot_id=context.snapshot_id,
            skeleton=context.skeleton,
            retrieved=context.retrieved,
            rules=self.config.rules,
            corrections=self.corrections,
        )

    def build_request(self, context: CoderContext) -> LLMRequest:
        """The request for this context. A pure function of the context and the config.

        Deliberately free of any coder-specific token: for one response, both coders
        build the identical request and only the client they send it to differs.
        """
        prompt = self._prompt(context)
        return prompt.to_request(TaskType.CODE, subject=subject_for(context.response.id))

    def code(self, context: CoderContext) -> CodingProposal:
        """Propose candidates for one response. Never raises on a malformed reply."""
        request = self.build_request(context)
        result = self.client.complete_json(request)
        if self.call_log is not None:
            self.call_log.record(result)
        candidates = parse_candidates(
            result.data, response_id=context.response.id, coder=self.coder
        )
        return CodingProposal(candidates=candidates, request=request, result=result)

    def normalised_text(self, context: CoderContext) -> str:
        """The exact string the prompt showed, and the string every span indexes into."""
        return normalise(context.response.content)
