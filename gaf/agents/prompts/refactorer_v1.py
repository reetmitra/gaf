"""Refactorer prompt, version 1: the slow loop's edit-script proposal.

What this module does. It renders the whole codebook, its usage statistics and its
deterministic health metrics into one prompt that asks for an **edit script**: a list of
operations, each of which parses through `gaf.models.Operation.from_json`.

Two things in the wording are not decoration.

* **The operation menu is rendered from `gaf.models.OPERATION_TYPES`**, so an operation
  the slow loop can apply is an operation the prompt offers, and the two cannot drift.
* **The prompt actively invites `split` and `reparent` rather than merely permitting
  them.** The predecessor study's fast loop could only create, merge, rename or do
  nothing; unable to restructure, it accreted parallel concepts, then merged
  semantically different ideas on lexical overlap, and the downstream clustering
  collapsed to two clusters where three were expected. Those two operations exist in
  this project because their absence is the documented cause of that failure, and a
  prompt that lists them last and unexplained would reproduce it.

The refactorer **proposes only**. Applying an edit script is the human-gated slow loop,
and the prompt says so, because the rationale on each operation is written for a person
who will accept, reject or edit it one operation at a time (ADR-0004: the gate sits here,
at codebook-refactor level, because that is a generative task rather than a decision
overlay).

Validation principles: **interpretive depth** — restructuring is what keeps nuance out
of a flattened codebook; **transparency** — every operation carries a rationale naming
the evidence it rests on, and that sentence is the audit trail the human reads.
"""

from __future__ import annotations

from gaf.agents.prompts.base import PromptTemplate, RenderedPrompt
from gaf.config import CodingRules
from gaf.models import OPERATION_TYPES

__all__ = [
    "OPERATION_GLOSS",
    "RESTRUCTURE",
    "ROLE",
    "SYSTEM",
    "TEMPLATE",
    "TEXTS",
    "VERSION",
    "render",
    "render_operations",
]

ROLE = "refactorer"
VERSION = "refactorer-v1"


SYSTEM = """\
You are restructuring the codebook of an inductive grounded-theory study at a review
checkpoint. You see the whole codebook and how much evidence each code carries.

You propose an edit script. You do not apply it. Every operation you write is read by a
researcher who accepts, rejects or edits it one at a time, so write each one for that
reader.

Answer with a single JSON object and nothing else: no preamble, no commentary, no
markdown fences.
"""


#: One gloss and one payload shape per operation in `OPERATION_TYPES`. Keyed by type so
#: the menu is rendered from the whitelist that `Operation.from_json` validates against.
OPERATION_GLOSS: dict[str, tuple[str, str]] = {
    "create": (
        "add a code the evidence needs and the codebook lacks.",
        '{"name": "toplevel-sub_level", "description": "...", "parent_id": "<code id>" or null}',
    ),
    "merge": (
        "fold two or more codes into one. List every code being folded in as a target.",
        '{"into": "<code id that survives>"}',
    ),
    "split": (
        "separate one overloaded code into two or more. The target is the code to split.",
        '{"into": [{"name": "...", "description": "..."}, {"name": "...", "description": "..."}]}',
    ),
    "reparent": (
        "move a code under a different top-level family, or promote it to the top level.",
        '{"new_parent_id": "<code id>" or null to promote}',
    ),
    "rename": (
        "change a code's name or description without changing what it covers.",
        '{"name": "...", "description": "..."}',
    ),
    "noop": (
        "nothing to change here. Use this rather than inventing work.",
        "{}",
    ),
}


RESTRUCTURE = """\
## What to look for, in this order

Split and reparent are the two operations this review exists for, and they are the two a
codebook review usually fails to use. Look for them first.

1. SPLIT an overloaded code. Read the quotes under each code and ask whether they all say
   the same thing. A code whose evidence covers two different ideas is overloaded: it will
   look like one concept in the analysis and behave like two. Split it, and give each part
   a description that says which of the quotes belong to it. Do not leave it alone because
   it is large, and do not merge it with something else to tidy it up.

2. REPARENT a misplaced code. A code whose name puts it in one family while its meaning
   belongs in another distorts every family-level count downstream. Move it. Promote a
   second-level code to the top level when it has become a family in its own right.

3. Only then consider MERGE. Merging is the operation that flattened this study's
   predecessor: it merged codes that shared vocabulary rather than meaning, and the
   clustering that followed collapsed. Merge two codes only when they name the same idea
   and would never be applied to different segments of text.

4. CREATE only where the evidence shows a concept the codebook cannot express at all.

5. RENAME where a name misdescribes what the code actually covers.

Propose NOOP, and only NOOP, if the codebook needs no change. An empty checkpoint is a
real and reportable outcome; invented work is not.
"""


RATIONALE = """\
## Rationales

Every operation must carry a rationale, and the rationale must name the evidence it rests
on: which codes, how many responses, and what the quotes under them actually said. "These
are similar" is not a rationale and will be rejected at the gate. The researcher reads
that one sentence and nothing else before deciding, so it has to carry the argument.
"""


OUTPUT = """\
## What to return

Return exactly this shape, and nothing outside it:

{
  "operations": [
    {
      "type": "split",
      "targets": ["<code id>"],
      "payload": {"into": [{"name": "...", "description": "..."}, {"name": "...", "description": "..."}]},
      "rationale": "One sentence naming the evidence: which quotes, under which code, split which way."
    }
  ],
  "reasoning": "A short paragraph on what you changed overall and what you deliberately left alone."
}

Targets are code ids exactly as they appear above, never code names. An operation whose
type is not in the list above is discarded unread.
"""


CODEBOOK_HEADER = """\
## The codebook

Every code, with its id, its family, its description, how many responses carry it, and a
sample of the quotes coded to it.
"""


USAGE_HEADER = """\
## Usage

How the evidence is distributed. A long tail of codes with little or no evidence is the
signal that the codebook has accreted rather than grown.
"""


HEALTH_HEADER = """\
## Deterministic health metrics

Measured, not estimated. Near-duplicate pairs are computed in the study's embedding space
and are a starting point for your reading, not a verdict.
"""


def render_operations() -> str:
    """The operation menu, rendered from `gaf.models.OPERATION_TYPES`."""
    lines = ["## The operations available to you", ""]
    width = max(len(op) for op in OPERATION_TYPES)
    for op_type in OPERATION_TYPES:
        gloss, payload = OPERATION_GLOSS[op_type]
        lines.append(f"  {op_type.ljust(width)}  {gloss}")
        lines.append(f"  {' ' * width}  payload: {payload}")
        lines.append("")
    return "\n".join(lines)


def render_rules(rules: CodingRules) -> str:
    """The structural constraints any proposal has to respect, from `CodingRules`."""
    lines = [
        "## Constraints on any proposal",
        "",
        f"- The codebook has {rules.hierarchy_depth} levels. Names are",
        "  `toplevel-sub_level`, split on the FIRST hyphen only, so a second-level name",
        "  may itself contain one.",
        f"- A response usually carries between {rules.min_codes_per_response} and"
        f" {rules.max_codes_per_response} codes, and the same",
        f"  piece of text at most {rules.max_codes_per_segment}. A split that pushes many"
        " responses past those bounds",
        "  is a split into the wrong parts.",
    ]
    if rules.prefer_subcode_first:
        lines.append(
            "- Prefer a second-level code under an existing family to a new top-level one."
        )
    lines += [
        "- The final codebook should describe the responses completely, hold discrete",
        "  codes, use no more codes than necessary, and be parsimonious. Those four goals",
        "  pull against each other; say in your reasoning which you traded for which.",
        "",
    ]
    return "\n".join(lines)


def render(
    *,
    snapshot_id: str,
    codebook_digest: str,
    usage_summary: str,
    health_json: str | None,
    rules: CodingRules,
) -> RenderedPrompt:
    """Assemble the refactor prompt. A pure function of its arguments."""
    sections = [
        f"Checkpoint on snapshot: {snapshot_id}\n",
        f"{CODEBOOK_HEADER}\n{codebook_digest}\n",
        f"{USAGE_HEADER}\n{usage_summary}\n",
        f"{HEALTH_HEADER}\n{health_json}\n" if health_json else "",
        render_operations(),
        RESTRUCTURE,
        render_rules(rules),
        RATIONALE,
        OUTPUT,
    ]
    user = "\n".join(section for section in sections if section)
    return RenderedPrompt(system=SYSTEM, user=user, version=VERSION)


TEXTS: dict[str, str] = {
    "system": SYSTEM,
    "codebook_header": CODEBOOK_HEADER,
    "usage_header": USAGE_HEADER,
    "health_header": HEALTH_HEADER,
    "operations": render_operations(),
    "restructure": RESTRUCTURE,
    "rules": render_rules(CodingRules()),
    "rationale": RATIONALE,
    "output": OUTPUT,
}

TEMPLATE = PromptTemplate(role=ROLE, version=VERSION, texts=TEXTS)


def _self_check() -> None:
    """Every applicable operation is offered, and nothing is offered that cannot apply."""
    if set(OPERATION_TYPES) != set(OPERATION_GLOSS):
        raise RuntimeError(
            f"{VERSION} is out of step with OPERATION_TYPES: the prompt offers "
            f"{sorted(OPERATION_GLOSS)} but the edit script accepts {sorted(OPERATION_TYPES)}. "
            "Bump the template version rather than editing this one in place."
        )


_self_check()
