"""The prompt loader: resolve a role and a version to a template and its renderer.

What this module does. It is the one place that knows which prompt versions exist. An
agent names a version string; the loader hands back the `PromptTemplate` (metadata plus
static text) and the typed render function that builds a prompt from it. Nothing here
renders anything itself.

Why a registry rather than an import in each agent: a version id is recorded with every
call in the `llm_calls` table, so "which templates does this build contain" has to be
answerable without running the pipeline — for the run report, and for a reader checking
that the wording behind a recorded version id is the wording that produced the coding.

Prompts are data. There is no template engine here and none is wanted: a render function
is a documented Python function over plain strings, which is greppable, diffable and
does not fail at runtime on a missing placeholder.

Validation principle: **transparency** — every prompt version in the build is
enumerable, and an unknown version is an error at resolution rather than a silent
fallback to whatever happened to be newest.
"""

from __future__ import annotations

from gaf.agents.prompts import coder_v1, judge_v1, refactorer_v1
from gaf.agents.prompts.base import (
    ROLES,
    CoderRenderer,
    JudgeRenderers,
    PromptTemplate,
    RefactorerRenderer,
)

__all__ = [
    "CODER_RENDERERS",
    "JUDGE_RENDERERS",
    "LATEST",
    "REFACTORER_RENDERERS",
    "ROLES",
    "TEMPLATES",
    "UnknownTemplateError",
    "all_templates",
    "coder_renderer",
    "get_template",
    "judge_renderers",
    "refactorer_renderer",
    "versions_for",
]


class UnknownTemplateError(KeyError):
    """A role or version that this build does not contain.

    A `KeyError`, and deliberately not a silent fallback to the newest version: a run
    that asks for `coder-v2` and is quietly given `coder-v1` would record a version id
    that never produced the text it names.
    """


#: role -> version -> template. The whole prompt surface of the build.
TEMPLATES: dict[str, dict[str, PromptTemplate]] = {
    "coder": {coder_v1.VERSION: coder_v1.TEMPLATE},
    "judge": {judge_v1.VERSION: judge_v1.TEMPLATE},
    "refactorer": {refactorer_v1.VERSION: refactorer_v1.TEMPLATE},
}

#: The default each agent uses when its caller names no version.
LATEST: dict[str, str] = {
    "coder": coder_v1.VERSION,
    "judge": judge_v1.VERSION,
    "refactorer": refactorer_v1.VERSION,
}

#: The render functions, one registry per role because their signatures differ. A new
#: version is one entry in `TEMPLATES` and one here, and is then type-checked against
#: the protocols in `gaf.agents.prompts.base`.
CODER_RENDERERS: dict[str, CoderRenderer] = {coder_v1.VERSION: coder_v1.render}
JUDGE_RENDERERS: dict[str, JudgeRenderers] = {judge_v1.VERSION: judge_v1.RENDERERS}
REFACTORER_RENDERERS: dict[str, RefactorerRenderer] = {
    refactorer_v1.VERSION: refactorer_v1.render
}


def versions_for(role: str) -> list[str]:
    """Every prompt version this build carries for `role`, sorted."""
    if role not in TEMPLATES:
        raise UnknownTemplateError(f"unknown prompt role {role!r}; expected one of {ROLES}")
    return sorted(TEMPLATES[role])


def get_template(role: str, version: str | None = None) -> PromptTemplate:
    """Resolve `role` and `version` to a template; `None` means the build's latest."""
    if role not in TEMPLATES:
        raise UnknownTemplateError(f"unknown prompt role {role!r}; expected one of {ROLES}")
    resolved = version or LATEST[role]
    try:
        return TEMPLATES[role][resolved]
    except KeyError:
        raise UnknownTemplateError(
            f"unknown {role} prompt version {resolved!r}; this build has "
            f"{versions_for(role)}"
        ) from None


def all_templates() -> list[PromptTemplate]:
    """Every template in the build, ordered by role then version."""
    return [
        TEMPLATES[role][version]
        for role in sorted(TEMPLATES)
        for version in sorted(TEMPLATES[role])
    ]


def _resolve[T](registry: dict[str, T], role: str, version: str | None) -> T:
    resolved = version or LATEST[role]
    try:
        return registry[resolved]
    except KeyError:
        raise UnknownTemplateError(
            f"unknown {role} prompt version {resolved!r}; this build has "
            f"{sorted(registry)}"
        ) from None


def coder_renderer(version: str | None = None) -> CoderRenderer:
    """The coder render function for `version`; `None` means the build's latest."""
    return _resolve(CODER_RENDERERS, "coder", version)


def judge_renderers(version: str | None = None) -> JudgeRenderers:
    """The judge's three render functions for `version`; one version id covers all three."""
    return _resolve(JUDGE_RENDERERS, "judge", version)


def refactorer_renderer(version: str | None = None) -> RefactorerRenderer:
    """The refactorer render function for `version`; `None` means the build's latest."""
    return _resolve(REFACTORER_RENDERERS, "refactorer", version)
