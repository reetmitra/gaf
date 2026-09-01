"""The Refactorer: the slow loop's proposer of codebook edits.

What this module does. At a checkpoint it renders the **whole codebook plus its usage
statistics** into one prompt and asks a frontier model for an **edit script**: a list of
operations, each of which parses through `gaf.models.Operation.from_json`. It returns
that script. It applies nothing.

Applying is the human-gated slow loop. ADR-0004 puts the gate exactly here and nowhere
else: the Vaccaro et al. (2024) meta-analysis finds human-AI combinations average worse
than the better party alone on *decision* tasks and better on *creation* tasks, so
item-by-item verification of machine codings is the overlay to avoid, while restructuring
a hierarchy from a proposed diff is the generative task where the pairing pays. Every
operation therefore carries a rationale written for a person, and the prompt requires
that rationale to name the evidence it rests on.

The operation set is deliberately wide — create, merge, split, reparent, rename, noop —
and the prompt actively invites `split` and `reparent` rather than merely permitting
them. The predecessor study could only create, merge, rename or do nothing; unable to
restructure, it accreted parallel concepts, merged semantically different ideas on
lexical overlap, and its clustering collapsed. Those two operations exist because their
absence is the documented cause of that failure.

Parsing is fail-safe throughout: an operation with an unknown type or an unreadable
shape is dropped and the rest of the script survives, and a wholly unreadable reply is
an empty edit script, which is a no-op checkpoint rather than a crash.

Validation principles: **interpretive depth** — restructuring is what keeps a codebook
from flattening into generic patterns; **transparency** — the proposal, its rationales
and the human's per-operation verdicts are all rows.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from gaf.agents.prompts.loader import get_template, refactorer_renderer
from gaf.config import RunConfig
from gaf.llm.base import CallLog, LLMClient, LLMRequest, LLMResult, TaskType
from gaf.models import Codebook, Operation

__all__ = [
    "EditScript",
    "RefactorContext",
    "RefactorerAgent",
    "checkpoint_subject",
    "codebook_digest",
    "parse_operations",
    "usage_from_codebook",
    "usage_summary",
]

#: How many quotes per code the digest carries. Enough to see whether the evidence under
#: one code says two different things — which is the signal a split rests on — without
#: turning a checkpoint prompt into the whole corpus.
MAX_QUOTES_PER_CODE = 3
#: Longest quote the digest shows before clipping. Clipped deterministically.
MAX_QUOTE_CHARS = 220


def checkpoint_subject(snapshot_id: str) -> str:
    """`LLMRequest.subject` for a refactor proposal: the snapshot it was made against."""
    return f"checkpoint:{snapshot_id}"


def usage_from_codebook(codebook: Codebook) -> dict[str, int]:
    """Code id -> number of distinct responses carrying verified evidence for it.

    Derived from the codebook itself rather than taken on trust from a caller, so the
    usage the refactorer reasons about is the usage the codebook actually records.
    """
    return {code.id: len(code.response_ids()) for code in codebook.sorted_codes()}


def _clip(text: str, limit: int = MAX_QUOTE_CHARS) -> str:
    clean = " ".join(text.split())
    return clean if len(clean) <= limit else clean[:limit].rstrip() + " [...]"


def codebook_digest(
    codebook: Codebook,
    usage: Mapping[str, int] | None = None,
    *,
    max_quotes: int = MAX_QUOTES_PER_CODE,
) -> str:
    """The whole codebook as deterministic JSON: ids, structure, usage and sample quotes.

    Ids are carried verbatim because an edit script targets ids, never names — a
    rename in flight would otherwise make an operation ambiguous. Codes are in
    `Codebook.sorted_codes` order and keys are sorted, so two runs render the same bytes.
    """
    counts = dict(usage) if usage is not None else usage_from_codebook(codebook)
    rows = []
    for code in codebook.sorted_codes():
        verified = [e for e in code.evidence if e.verified]
        rows.append(
            {
                "id": code.id,
                "name": code.name,
                "family": code.family,
                "description": code.description,
                "parent_id": code.parent_id,
                "responses": counts.get(code.id, len(code.response_ids())),
                "sample_quotes": [_clip(e.quote) for e in verified[:max_quotes]],
            }
        )
    return json.dumps({"codes": rows}, indent=2, sort_keys=True, ensure_ascii=False)


def usage_summary(codebook: Codebook, usage: Mapping[str, int] | None = None) -> str:
    """A short, deterministic usage table: totals, the empty tail, the family balance."""
    counts = dict(usage) if usage is not None else usage_from_codebook(codebook)
    codes = codebook.sorted_codes()
    families = codebook.families()
    empty = [code.name for code in codes if counts.get(code.id, 0) == 0]
    lines = [
        f"codes: {len(codes)}",
        f"families: {len(families)}",
        f"codes with no verified evidence: {len(empty)}",
    ]
    if empty:
        lines.append("  " + ", ".join(sorted(empty)))
    lines.append("responses per code, most used first:")
    ranked = sorted(codes, key=lambda c: (-counts.get(c.id, 0), c.name))
    lines += [f"  {code.name}: {counts.get(code.id, 0)}" for code in ranked]
    lines.append("codes per family:")
    lines += [f"  {family}: {len(members)}" for family, members in families.items()]
    return "\n".join(lines)


@dataclass(frozen=True, slots=True)
class RefactorContext:
    """What the refactorer sees at a checkpoint: the whole codebook and its statistics.

    `health` is the JSON form of `gaf.checks.health.HealthMetrics` — passed as a plain
    mapping rather than as the dataclass so this agent does not drag the check layer,
    numpy and scipy into the coding path. `None` means the metrics were not computed;
    the prompt then simply omits that section.
    """

    codebook: Codebook
    snapshot_id: str
    usage: Mapping[str, int] = field(default_factory=dict)
    health: Mapping[str, Any] | None = None

    @classmethod
    def from_codebook(
        cls,
        codebook: Codebook,
        snapshot_id: str,
        *,
        health: Mapping[str, Any] | None = None,
    ) -> RefactorContext:
        """Build a context, deriving usage from the codebook's own verified evidence."""
        return cls(
            codebook=codebook,
            snapshot_id=snapshot_id,
            usage=usage_from_codebook(codebook),
            health=health,
        )


@dataclass(frozen=True, slots=True)
class EditScript:
    """A proposal, and nothing more. Applying it is the human gate's business.

    `operations` are already validated against `gaf.models.OPERATION_TYPES` — an
    operation this build cannot apply never reaches the human, because an unactionable
    row at the gate is wasted human attention.
    """

    operations: list[Operation]
    reasoning: str
    request: LLMRequest
    result: LLMResult

    def __len__(self) -> int:
        return len(self.operations)

    @property
    def prompt_version(self) -> str:
        return self.result.prompt_version

    @property
    def subject(self) -> str:
        return self.request.subject

    @property
    def fail_safe(self) -> bool:
        return self.result.fail_safe

    def types(self) -> list[str]:
        """The operation types proposed, in order. The shape of a checkpoint at a glance."""
        return [op.type for op in self.operations]

    def is_noop(self) -> bool:
        """True when nothing structural was proposed — a legitimate checkpoint outcome."""
        return all(op.type == "noop" for op in self.operations)

    def to_json(self) -> dict[str, Any]:
        return {
            "operations": [op.to_json() for op in self.operations],
            "reasoning": self.reasoning,
            "subject": self.subject,
            "prompt_version": self.prompt_version,
            "fail_safe": self.fail_safe,
        }


def parse_operations(data: Mapping[str, Any]) -> list[Operation]:
    """Parse an edit script. Never raises; drops what it cannot use and keeps the rest.

    `Operation.from_json` raises on an unknown type, which is the right behaviour for
    the slow loop's own validation but the wrong behaviour here: one hallucinated
    operation type must not discard five good operations beside it.
    """
    raw = data.get("operations")
    if not isinstance(raw, Sequence) or isinstance(raw, str | bytes):
        return []
    operations: list[Operation] = []
    for item in raw:
        if not isinstance(item, Mapping):
            continue
        try:
            operations.append(Operation.from_json(dict(item)))
        except (KeyError, TypeError, ValueError):
            continue
    return operations


class RefactorerAgent:
    """The slow loop's proposer. Frontier model, whole codebook, edit script out.

    Proposes only. There is no `apply` here and there must not be one: applying an
    operation is the human-gated step, and putting it on the proposer would put the
    machine on both sides of the gate.
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
        self.template = get_template("refactorer", prompt_version)
        self._render = refactorer_renderer(self.template.version)
        self.call_log = call_log

    @property
    def prompt_version(self) -> str:
        return self.template.version

    def build_request(self, context: RefactorContext) -> LLMRequest:
        """The request for one checkpoint. A pure function of the context and the config."""
        health_json = (
            json.dumps(dict(context.health), indent=2, sort_keys=True, ensure_ascii=False)
            if context.health
            else None
        )
        prompt = self._render(
            snapshot_id=context.snapshot_id,
            codebook_digest=codebook_digest(context.codebook, context.usage),
            usage_summary=usage_summary(context.codebook, context.usage),
            health_json=health_json,
            rules=self.config.rules,
        )
        return prompt.to_request(
            TaskType.REFACTOR, subject=checkpoint_subject(context.snapshot_id)
        )

    def propose(self, context: RefactorContext) -> EditScript:
        """Ask for an edit script. Never raises; an unreadable reply is an empty script."""
        request = self.build_request(context)
        result = self.client.complete_json(request)
        if self.call_log is not None:
            self.call_log.record(result)
        data = result.data if isinstance(result.data, Mapping) else {}
        reasoning = data.get("reasoning")
        return EditScript(
            operations=parse_operations(data),
            reasoning=reasoning if isinstance(reasoning, str) else "",
            request=request,
            result=result,
        )
