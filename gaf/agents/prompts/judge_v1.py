"""Judge prompts, version 1: three questions, one frontier role, one version id.

What this module does. It renders the only three questions the judge is ever asked, and
it is deliberate that there are three and no more: the judge is consulted where the
deterministic layers are genuinely ambiguous, and nowhere else.

* **fit** (M3) — does this code apply to this quote? Four verdicts, mirroring the PI's
  own negative-example taxonomy in `docs/CODING_RULES.md`, rendered from
  `gaf.checks.contracts.FIT_VERDICTS` so the prompt and the whitelist cannot drift
  apart. This prompt is deliberately the shortest of the three: ADR-0019 measured M3's
  offline fit scores at a median of 0.000, so in a live run this is the method most
  likely to be called at volume, and its length is a cost line.
* **dispute** (M1) — two coders disagreed inside the grey band; keep both readings or
  drop the second?
* **route** (M2) — a candidate sits between tau_low and tau_high against its nearest
  neighbour; is it that code under another name, or a new distinction?

**The fit prompt does not invite a replacement code, and must never be changed to.** On
an IMPRECISE or INCOMPLETE verdict the deliverable is the verdict and the reasoning:
refinement is slow-loop and human work. A prompt that asked "what code would be better?"
would push the fast loop into inventing codes, which is the thing the architecture
forbids (`docs/CODING_RULES.md`, "the one category with no check").

Every verdict list is rendered from the shared whitelist that validates the reply, and
both defaults stated in the prompts are the non-destructive ones from
`gaf.llm.base.FAIL_SAFE_DEFAULTS`: keep the candidate, create rather than merge.

Validation principles: **interpretive depth** — the prompts instruct keep-and-flag over
auto-resolution; **epistemic diversity** — a third provider adjudicates where two
coders and one geometry could not.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from gaf.agents.prompts.base import JudgeRenderers, PromptTemplate, RenderedPrompt
from gaf.checks.contracts import FIT_VERDICTS
from gaf.config import CodingRules
from gaf.llm.base import DISPUTE_VERDICTS, ROUTE_VERDICTS
from gaf.textnorm import normalise

__all__ = [
    "DISPUTE_SYSTEM",
    "DISPUTE_VERDICT_GLOSS",
    "FIT_SYSTEM",
    "FIT_TEXT",
    "FIT_VERDICT_GLOSS",
    "RENDERERS",
    "ROLE",
    "ROUTE_SYSTEM",
    "ROUTE_VERDICT_GLOSS",
    "TEMPLATE",
    "TEXTS",
    "VERSION",
    "render_dispute",
    "render_fit",
    "render_route",
]

ROLE = "judge"
VERSION = "judge-v1"

_MAX_RESPONSE_CHARS = 1400
_MAX_QUOTES_PER_CANDIDATE = 3


def _clip(text: str, limit: int) -> str:
    """Trim long context deterministically. A judge call is a cost line, not an essay."""
    clean = normalise(text)
    return clean if len(clean) <= limit else clean[:limit].rstrip() + " [...]"


def _verdict_menu(verdicts: tuple[str, ...], gloss: Mapping[str, str]) -> str:
    """The verdict list, rendered from the whitelist that validates the reply."""
    width = max(len(v) for v in verdicts)
    return "\n".join(f"  {v.ljust(width)}  {gloss[v]}" for v in verdicts)


# --------------------------------------------------------------------------- #
# M3 — code-to-evidence fit
# --------------------------------------------------------------------------- #

#: One gloss per verdict in `FIT_VERDICTS`, each a restatement of the PI's own
#: negative-example category. Keyed by verdict so the menu is rendered from the
#: whitelist rather than typed out beside it.
FIT_VERDICT_GLOSS: dict[str, str] = {
    "APPLIES": "the code explains this quote.",
    "IMPRECISE": "the code is about this quote but is not precise enough about it.",
    "INCOMPLETE": "the code is accurate but does not describe the whole of this quote.",
    "UNNECESSARY": "the code did not have to be applied to this quote at all.",
}

FIT_SYSTEM = """\
You adjudicate one code-to-evidence pairing at a time for an inductive grounded-theory
study. You are shown a code, the quote it was applied to, and the response the quote
came from. Answer with a single JSON object and nothing else.
"""

FIT_NO_REPLACEMENT = """\
Do not propose a different code, a better name, a rewrite or a refinement. None of those
is wanted here and any of them would be discarded: the verdict and one sentence of
reasoning are the whole of the answer. Refining a code is a later, human step.
"""

FIT_OUTPUT_HEADER = """\
Return:

{"verdict": "<one of the verdicts above>", "reasoning": "one sentence"}
"""


def render_fit(
    *,
    candidate_name: str,
    candidate_description: str,
    quote: str,
    response_text: str,
) -> RenderedPrompt:
    """The M3 prompt. Kept short on purpose - it is the one called at volume."""
    description = candidate_description.strip() or "(no description recorded)"
    user = (
        f"Code: {candidate_name}\n"
        f"Meaning: {description}\n\n"
        f"Quote it was applied to:\n{_clip(quote, _MAX_RESPONSE_CHARS)}\n\n"
        f"The response the quote came from:\n"
        f"{_clip(response_text, _MAX_RESPONSE_CHARS)}\n\n"
        "Choose exactly one verdict:\n\n"
        f"{_verdict_menu(FIT_VERDICTS, FIT_VERDICT_GLOSS)}\n\n"
        f"{FIT_NO_REPLACEMENT}\n"
        f"{FIT_OUTPUT_HEADER}"
    )
    return RenderedPrompt(system=FIT_SYSTEM, user=user, version=VERSION)


# --------------------------------------------------------------------------- #
# M1 — cross-coder dispute
# --------------------------------------------------------------------------- #

DISPUTE_VERDICT_GLOSS: dict[str, str] = {
    "KEEP": "the two candidates name different things, and the difference is worth keeping.",
    "DROP": "the second candidate restates the first and adds no distinction.",
}

DISPUTE_SYSTEM = """\
You adjudicate disagreements between two independent coders in an inductive
grounded-theory study. Two researchers read the same survey response without seeing each
other's work and proposed codes that a similarity measure could call neither the same nor
different. Answer with a single JSON object and nothing else.
"""

DISPUTE_GUIDANCE = """\
Default to KEEP. Two readings a measure could not separate are usually two readings, and
this study keeps and flags rather than resolving automatically. A distinction kept here
can still be merged later by a human reviewing the whole codebook; a distinction dropped
here leaves no trace to review.

Judge the candidates as readings of the response. Do not propose a third code, do not
rename either candidate, and do not try to merge them into a new one.
"""

DISPUTE_OUTPUT = """\
Return:

{"verdict": "KEEP" or "DROP", "reasoning": "one sentence naming what the second candidate adds, or fails to add"}
"""


def _candidate_block(label: str, candidate: Mapping[str, Any]) -> str:
    """Render a `Candidate.to_json()` dict down to what the judgement needs."""
    name = str(candidate.get("name", ""))
    description = str(candidate.get("description", "")).strip() or "(no description recorded)"
    raw_evidence = candidate.get("evidence") or []
    quotes = [
        str(item.get("quote", ""))
        for item in raw_evidence
        if isinstance(item, Mapping) and item.get("quote")
    ][:_MAX_QUOTES_PER_CANDIDATE]
    lines = [f"{label}:", f"  name: {name}", f"  meaning: {description}"]
    if quotes:
        lines.append("  quotes it was applied to:")
        lines += [f'    - "{_clip(quote, 300)}"' for quote in quotes]
    else:
        lines.append("  quotes it was applied to: (none recorded)")
    return "\n".join(lines)


def render_dispute(
    *,
    candidate_a: Mapping[str, Any],
    candidate_b: Mapping[str, Any],
    response_text: str,
    rules: CodingRules,
) -> RenderedPrompt:
    """The M1 prompt. Both candidates, the response, and a bias towards keeping."""
    user = (
        "Two coders read this response independently.\n\n"
        f"The response:\n{_clip(response_text, _MAX_RESPONSE_CHARS)}\n\n"
        f"{_candidate_block('Coder A candidate', candidate_a)}\n\n"
        f"{_candidate_block('Coder B candidate', candidate_b)}\n\n"
        "Decide whether the second candidate is kept alongside the first or dropped:\n\n"
        f"{_verdict_menu(DISPUTE_VERDICTS, DISPUTE_VERDICT_GLOSS)}\n\n"
        f"{DISPUTE_GUIDANCE}\n"
        "Bear in mind the rule this study codes under: the same piece of text can carry a "
        f"maximum of {rules.max_codes_per_segment} codes.\n\n"
        f"{DISPUTE_OUTPUT}"
    )
    return RenderedPrompt(system=DISPUTE_SYSTEM, user=user, version=VERSION)


# --------------------------------------------------------------------------- #
# M2 — grey-zone integration routing
# --------------------------------------------------------------------------- #

ROUTE_VERDICT_GLOSS: dict[str, str] = {
    "MERGE": "the candidate restates the existing code; fold it in.",
    "CREATE": "the candidate names something the existing code does not; admit it.",
}

ROUTE_SYSTEM = """\
You decide whether a newly proposed code belongs in an inductive grounded-theory
codebook, or is an existing code under another name. Answer with a single JSON object
and nothing else.
"""

ROUTE_GUIDANCE = """\
When you cannot tell, choose CREATE. A spurious new code is visible to the duplicate
check and repairable by a human reviewing the codebook; a spurious merge destroys a
distinction silently, and the predecessor of this study collapsed exactly that way -
it merged concepts that shared vocabulary rather than meaning.

Ask whether the two names would ever be applied to different segments of text. If they
would, they are two codes.
"""

ROUTE_OUTPUT = """\
Return:

{"route": "MERGE" or "CREATE", "reasoning": "one sentence naming the distinction, or its absence"}
"""


def render_route(
    *,
    candidate_name: str,
    candidate_description: str,
    neighbour_name: str,
    neighbour_description: str,
    score: float,
    rules: CodingRules,
) -> RenderedPrompt:
    """The M2 prompt. The band comes from `CodingRules`, so the numbers cannot drift."""
    candidate_meaning = candidate_description.strip() or "(no description recorded)"
    neighbour_meaning = neighbour_description.strip() or "(no description recorded)"
    user = (
        "A coder proposed a new code. Its nearest neighbour in the existing codebook is "
        f"at cosine similarity {score:.3f}, inside the band between {rules.tau_low:.2f} "
        f"and {rules.tau_high:.2f} where the measure cannot decide. That is why you are "
        "being asked.\n\n"
        f"Proposed code:\n  name: {candidate_name}\n  meaning: {candidate_meaning}\n\n"
        f"Nearest existing code:\n  name: {neighbour_name}\n"
        f"  meaning: {neighbour_meaning}\n\n"
        "Decide:\n\n"
        f"{_verdict_menu(ROUTE_VERDICTS, ROUTE_VERDICT_GLOSS)}\n\n"
        f"{ROUTE_GUIDANCE}\n"
        f"{ROUTE_OUTPUT}"
    )
    return RenderedPrompt(system=ROUTE_SYSTEM, user=user, version=VERSION)


RENDERERS = JudgeRenderers(fit=render_fit, dispute=render_dispute, route=render_route)

TEXTS: dict[str, str] = {
    "fit_system": FIT_SYSTEM,
    "fit_verdicts": _verdict_menu(FIT_VERDICTS, FIT_VERDICT_GLOSS),
    "fit_no_replacement": FIT_NO_REPLACEMENT,
    "fit_output": FIT_OUTPUT_HEADER,
    "dispute_system": DISPUTE_SYSTEM,
    "dispute_verdicts": _verdict_menu(DISPUTE_VERDICTS, DISPUTE_VERDICT_GLOSS),
    "dispute_guidance": DISPUTE_GUIDANCE,
    "dispute_output": DISPUTE_OUTPUT,
    "route_system": ROUTE_SYSTEM,
    "route_verdicts": _verdict_menu(ROUTE_VERDICTS, ROUTE_VERDICT_GLOSS),
    "route_guidance": ROUTE_GUIDANCE,
    "route_output": ROUTE_OUTPUT,
}

TEMPLATE = PromptTemplate(role=ROLE, version=VERSION, texts=TEXTS)

#: The fit prompt's static text, as one string. `tests/test_agents.py` asserts against
#: it directly that no wording here invites a replacement code.
FIT_TEXT = "\n".join(
    TEXTS[key] for key in ("fit_system", "fit_verdicts", "fit_no_replacement", "fit_output")
)


def _self_check() -> None:
    """Every whitelisted verdict has a gloss, and no gloss names a verdict that is gone.

    Called at import: a whitelist that gains a verdict without gaining a line in the
    prompt would silently ask the model to choose from three options and then validate
    its answer against four.
    """
    for verdicts, gloss, label in (
        (FIT_VERDICTS, FIT_VERDICT_GLOSS, "FIT_VERDICTS"),
        (DISPUTE_VERDICTS, DISPUTE_VERDICT_GLOSS, "DISPUTE_VERDICTS"),
        (ROUTE_VERDICTS, ROUTE_VERDICT_GLOSS, "ROUTE_VERDICTS"),
    ):
        if set(verdicts) != set(gloss):
            raise RuntimeError(
                f"{VERSION} is out of step with {label}: the prompt offers "
                f"{sorted(gloss)} but the whitelist validates {sorted(verdicts)}. "
                "Bump the template version rather than editing this one in place."
            )


_self_check()
