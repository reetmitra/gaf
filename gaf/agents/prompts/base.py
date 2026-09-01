"""The shapes every versioned prompt template shares, and nothing else.

What this module does. It defines `RenderedPrompt` — a system/user pair that carries
its own version id and can only be turned into an `LLMRequest` with that id attached —
and `PromptTemplate`, the small record a loader resolves a role and a version to. It
also declares the call signatures of the four render functions (one coder, three judge,
one refactorer) as protocols, so a new template version is type-checked against the
agents that drive it rather than discovered at runtime.

It holds no wording of its own. The words live in the per-version modules beside it,
one file per role and version, and a change to any of them is a new version id.

Validation principle: **transparency** — the version id travels with every call the
template produces, so it lands in the `llm_calls` table and a change of wording becomes
a visible event rather than silent drift between runs.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from gaf.config import CodingRules
from gaf.llm.base import LLMRequest, TaskType
from gaf.models import Assignment, Code, Response

__all__ = [
    "ROLES",
    "CoderRenderer",
    "DisputeRenderer",
    "FitRenderer",
    "JudgeRenderers",
    "PromptTemplate",
    "RefactorerRenderer",
    "RenderedPrompt",
    "RouteRenderer",
]

#: The three LLM roles. There are no others: slicing, quote checking, comparison and
#: change tracking are deterministic code, not model calls.
ROLES: tuple[str, ...] = ("coder", "judge", "refactorer")


@dataclass(frozen=True, slots=True)
class RenderedPrompt:
    """One prompt, ready to send, with the id of the template that produced it.

    `to_request` is the only supported way to turn a prompt into a call, which is what
    makes "every request records its prompt version" a structural property rather than
    a convention an agent could forget.
    """

    system: str
    user: str
    version: str

    def to_request(
        self,
        task: TaskType,
        *,
        subject: str = "",
        max_output_tokens: int | None = None,
        temperature: float | None = None,
    ) -> LLMRequest:
        """Bind this prompt to a task and a subject, carrying the version id along."""
        return LLMRequest(
            task=task,
            system=self.system,
            user=self.user,
            prompt_version=self.version,
            subject=subject,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
        )


@dataclass(frozen=True, slots=True)
class PromptTemplate:
    """The metadata of one role-and-version template, plus its static text.

    `texts` holds every fixed fragment the template is built from, keyed by section
    name. The render functions read the same constants, so the mapping is the whole
    static surface of the template: it is what the vocabulary check scans, and what a
    methods appendix can print without running the pipeline.
    """

    role: str
    version: str
    texts: Mapping[str, str]

    def all_text(self) -> str:
        """Every static fragment, section-sorted — the string a scan reads."""
        return "\n".join(f"{key}\n{self.texts[key]}" for key in sorted(self.texts))

    def to_json(self) -> dict[str, Any]:
        return {"role": self.role, "version": self.version, "sections": sorted(self.texts)}


# --------------------------------------------------------------------------- #
# Render signatures
# --------------------------------------------------------------------------- #
#
# Declared as protocols rather than as bare `Callable` aliases so that a version's
# render function is checked against the agent that calls it, keyword by keyword.


class CoderRenderer(Protocol):
    """Builds one coding prompt from a response and a frozen snapshot's context."""

    def __call__(
        self,
        *,
        response: Response,
        snapshot_id: str,
        skeleton: Mapping[str, Sequence[str]],
        retrieved: Sequence[Code],
        rules: CodingRules,
        corrections: Sequence[Assignment] = (),
    ) -> RenderedPrompt: ...


class FitRenderer(Protocol):
    """Builds the M3 code-to-evidence fit prompt. Kept short: it is called at volume."""

    def __call__(
        self,
        *,
        candidate_name: str,
        candidate_description: str,
        quote: str,
        response_text: str,
    ) -> RenderedPrompt: ...


class DisputeRenderer(Protocol):
    """Builds the M1 cross-coder dispute prompt."""

    def __call__(
        self,
        *,
        candidate_a: Mapping[str, Any],
        candidate_b: Mapping[str, Any],
        response_text: str,
        rules: CodingRules,
    ) -> RenderedPrompt: ...


class RouteRenderer(Protocol):
    """Builds the M2 grey-zone integration prompt."""

    def __call__(
        self,
        *,
        candidate_name: str,
        candidate_description: str,
        neighbour_name: str,
        neighbour_description: str,
        score: float,
        rules: CodingRules,
    ) -> RenderedPrompt: ...


@dataclass(frozen=True, slots=True)
class JudgeRenderers:
    """The judge's three render functions. One role, three questions, one version id."""

    fit: FitRenderer
    dispute: DisputeRenderer
    route: RouteRenderer


class RefactorerRenderer(Protocol):
    """Builds the slow loop's edit-script proposal prompt."""

    def __call__(
        self,
        *,
        snapshot_id: str,
        codebook_digest: str,
        usage_summary: str,
        health_json: str | None,
        rules: CodingRules,
    ) -> RenderedPrompt: ...
