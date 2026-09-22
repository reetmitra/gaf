"""Definer prompt, version 1: the 1-3 sentence description of one code.

What this module does. It renders one code — its name, its parent, its sibling names
and **all** of the text segments a researcher assigned to it — into a prompt that asks
for a description, and for nothing else.

Three things in the wording are not decoration.

* **The output object holds one key.** The role cannot rename, merge, split, create or
  choose an example, because none of those is expressible in what it returns. That is a
  stronger guarantee than an instruction not to do them, and it is why the schema is
  stated as the whole of the reply rather than as one section among several.
* **A parent is described from its children**, their descriptions and their segment
  counts — never from raw text. The researcher's own instruction is that a code with
  subcodes gets a description and no examples; describing a parent from the text under
  its children would be describing the children twice.
* **The prompt forbids quoting, and says what happens if it quotes anyway.** A
  description is shared with readers who never see the corpus; a quote is not shareable.
  `gaf.agents.definer.check_description` enforces this deterministically after the call,
  and the prompt states the rule so a live model is not surprised by a refusal.

The wording of the task follows the researcher's own prompt for building a codebook
inductively from code-text pairings: a definition of one to three sentences, in the
model's own words, grounded strictly in the associated text, making clear what the code
captures and how it differs from its siblings.

`DefinerRenderer` is declared here rather than in `gaf.agents.prompts.base` beside the
other three render protocols: `base.py` is a Wave-0 shape module, and this build adds
the fourth role additively without touching it (ADR-0034).

Validation principles: **transparency** — the version id travels with every call, so a
change of wording is a visible event; **interpretive depth** — a description that says
how a code differs from its siblings is what keeps a codebook from flattening into a
list of labels.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from gaf.agents.prompts.base import PromptTemplate, RenderedPrompt

__all__ = [
    "CHILDREN_CLOSE",
    "CHILDREN_HEADER",
    "CHILDREN_OPEN",
    "OUTPUT",
    "ROLE",
    "SEGMENTS_CLOSE",
    "SEGMENTS_HEADER",
    "SEGMENTS_OPEN",
    "SIBLINGS_HEADER",
    "SYSTEM",
    "TEMPLATE",
    "TEXTS",
    "VERSION",
    "ChildLine",
    "DefinerRenderer",
    "render",
    "render_children",
    "render_placement",
    "render_segments",
    "render_siblings",
    "render_task",
]

ROLE = "definer"
VERSION = "definer-v1"

#: One child of a parent code: its name, its description and how many segments it holds.
ChildLine = tuple[str, str, int]

#: The block delimiters. They are literal strings rather than a template mechanism for
#: the same reason `<response>` is in the coder prompt: the offline persona in
#: `gaf.llm.mock` finds the text it works from by looking for them, and a test asserts
#: that a rendered prompt and that persona still agree.
SEGMENTS_OPEN = "<segments>"
SEGMENTS_CLOSE = "</segments>"
CHILDREN_OPEN = "<children>"
CHILDREN_CLOSE = "</children>"


SYSTEM = """\
You are writing the definition of one code in an inductive grounded-theory codebook.

A researcher has already assigned every text segment you will see to this code. The
codebook's organisation is settled and is not yours to change: you are not asked whether
this code should exist, whether it should be renamed, merged, split or moved, or which
of its segments is a good example. You write one definition.

Answer with a single JSON object and nothing else: no preamble, no commentary, no
markdown fences.
"""


PLACEMENT_HEADER = """\
## The code

Where it sits, and how much text is under it.
"""


SIBLINGS_HEADER = """\
## Its siblings

These codes sit beside it under the same parent. Your definition has to make clear what
belongs to this code rather than to one of them.
"""


SEGMENTS_HEADER = """\
## Its segments

Every text segment the researcher assigned to this code. Your definition is grounded in
these and in nothing else. Do not speculate past them.
"""


CHILDREN_HEADER = """\
## Its subcodes

This code has subcodes, so it is described from them: their definitions and how much
text each one holds. You are not shown the text itself, because describing a parent from
the segments under its children would describe the children a second time.
"""


TASK = """\
## What to write

One definition of one to three sentences, in your own words. It must say **what content
this code captures** and **how it differs from its siblings**. Nothing else.

Do not quote. A definition is read by people who will never see the source text, and it
travels into documents the text itself may not: a description is shareable, a quote is
not. Write about what the segments have in common, not about what any one of them says.

Two rules are checked deterministically after you answer, and a definition that breaks
either is discarded, leaving the code undescribed:

- a definition that is a verbatim copy of one of the segments above;
- a definition carrying a run of eight or more consecutive words from any of them.

Write plainly. The reader is a researcher reading a hundred and thirty of these in a row.
"""


OUTPUT = """\
## What to return

Return exactly this object, and nothing outside it:

{
  "description": "One to three sentences: what this code captures, and how it differs from its siblings."
}

No other key is read. There is no key for a name, a parent, a merge, a split or an
example, because none of those decisions is yours.
"""


def render_placement(*, code_name: str, parent: str, count: int, is_parent: bool) -> str:
    """Name, level, parent and segment count — four lines, deterministically ordered."""
    level = 2 if parent else 1
    lines = [
        PLACEMENT_HEADER,
        f"Code: {code_name}",
        f"Level: {level}",
        f"Parent: {parent}" if parent else "Parent: none — this is a top-level code",
    ]
    if is_parent:
        lines.append(f"Segments beneath it, across its subcodes: {count}")
    else:
        lines.append(f"Segments carrying this code: {count}")
    return "\n".join(lines) + "\n"


def render_siblings(siblings: Sequence[str]) -> str:
    """The sibling names, sorted. An empty list says so rather than printing nothing."""
    if not siblings:
        return (
            f"{SIBLINGS_HEADER}\n"
            "It has no siblings: nothing else sits under the same parent. Define it "
            "against the codebook as a whole instead.\n"
        )
    listed = "\n".join(f"  - {name}" for name in sorted(siblings))
    return f"{SIBLINGS_HEADER}\n{listed}\n"


def render_segments(segments: Sequence[str]) -> str:
    """Every segment, in the order it was given, one bullet per line inside the block."""
    if not segments:
        return (
            f"{SEGMENTS_HEADER}\n"
            f"{SEGMENTS_OPEN}\n{SEGMENTS_CLOSE}\n\n"
            "No segment is associated with this code. Say so in the definition rather "
            "than inventing what it might cover.\n"
        )
    body = "\n".join(f"- {segment}" for segment in segments)
    return f"{SEGMENTS_HEADER}\n{SEGMENTS_OPEN}\n{body}\n{SEGMENTS_CLOSE}\n"


def render_children(children: Sequence[ChildLine]) -> str:
    """The subcodes, sorted by name: each one's name, its count and its definition."""
    lines = []
    for name, description, count in sorted(children):
        gloss = description.strip() or "(not yet defined)"
        lines.append(f"- {name} (n={count}) - {gloss}")
    body = "\n".join(lines)
    return f"{CHILDREN_HEADER}\n{CHILDREN_OPEN}\n{body}\n{CHILDREN_CLOSE}\n"


def render_task(max_sentences: int) -> str:
    """The task section. `max_sentences` is rendered so the bound and the guard agree."""
    if max_sentences == 3:
        return TASK
    spelled = {1: "one", 2: "two", 4: "four", 5: "five"}.get(max_sentences, str(max_sentences))
    return TASK.replace("one to three sentences", f"one to {spelled} sentences")


def render(
    *,
    code_name: str,
    parent: str,
    siblings: Sequence[str],
    segments: Sequence[str],
    children: Sequence[ChildLine] = (),
    count: int = 0,
    max_sentences: int = 3,
) -> RenderedPrompt:
    """Assemble the definition prompt. A pure function of its arguments.

    `children` non-empty means this is a parent code: the segments are used by the
    deterministic guards afterwards but are never rendered, because a parent is
    described from its subcodes.
    """
    is_parent = bool(children)
    sections = [
        render_placement(
            code_name=code_name, parent=parent, count=count, is_parent=is_parent
        ),
        render_siblings(siblings),
        render_children(children) if is_parent else render_segments(segments),
        render_task(max_sentences),
        OUTPUT,
    ]
    return RenderedPrompt(system=SYSTEM, user="\n".join(sections), version=VERSION)


class DefinerRenderer(Protocol):
    """Builds the definition prompt for one code. The fourth render signature."""

    def __call__(
        self,
        *,
        code_name: str,
        parent: str,
        siblings: Sequence[str],
        segments: Sequence[str],
        children: Sequence[ChildLine] = (),
        count: int = 0,
        max_sentences: int = 3,
    ) -> RenderedPrompt: ...


TEXTS: dict[str, str] = {
    "system": SYSTEM,
    "placement_header": PLACEMENT_HEADER,
    "siblings_header": SIBLINGS_HEADER,
    "segments_header": SEGMENTS_HEADER,
    "children_header": CHILDREN_HEADER,
    "task": TASK,
    "output": OUTPUT,
}

TEMPLATE = PromptTemplate(role=ROLE, version=VERSION, texts=TEXTS)


def _self_check() -> None:
    """The reply schema offers one key, and the block delimiters are still paired."""
    if OUTPUT.count('"') != 4 or '"description"' not in OUTPUT:
        raise RuntimeError(
            f"{VERSION} must offer exactly one output key, and it must be "
            '"description": anything else would let the role express a decision it is '
            "not allowed to take. Bump the template version rather than editing this one."
        )
    for opener, closer in ((SEGMENTS_OPEN, SEGMENTS_CLOSE), (CHILDREN_OPEN, CHILDREN_CLOSE)):
        if not closer.startswith("</") or closer[2:] != opener[1:]:
            raise RuntimeError(f"{VERSION}: {opener!r} and {closer!r} are not a pair")


_self_check()
