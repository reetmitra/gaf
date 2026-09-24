"""Coder prompt, version 1: initial coding of one response against a frozen snapshot.

What this module does. It renders the whole context a coder is allowed to see — the
survey question, the response, the frozen codebook's hierarchy skeleton and the
retrieved codes, the PI's coding rules and his own worked corrections — into one
system/user pair whose version id is ``coder-v1``.

Three properties are load-bearing and are asserted in `tests/test_agents.py`:

* **The rules are rendered from `CodingRules`, never written out by hand.** Changing
  the config changes the prompt, so a threshold cannot drift away from the text that
  states it.
* **The response is wrapped in ``<response>...</response>`` and normalised through
  `gaf.textnorm.normalise`.** Spans are defined against the normalised text, and the
  offline mock reads the same tags the live model does, so one template drives both
  paths.
* **The prompt is a pure function of the context.** Two coders from two providers
  receive byte-identical prompts; the only difference between them is the model
  binding. Any asymmetry here would silently destroy the epistemic-diversity design,
  because cross-coder disagreement would then measure the prompt rather than the model.

The vocabulary is grounded theory's throughout (ADR-0005): codes, families, initial
coding, constant comparison.

Validation principles: **epistemic diversity** — identical context is what makes two
coders' disagreement evidence about meaning rather than about wording; **reliability**
— the same context renders the same bytes on every run.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from gaf.agents.prompts.base import PromptTemplate, RenderedPrompt
from gaf.config import CodingRules
from gaf.models import Assignment, Code, Response
from gaf.textnorm import normalise

__all__ = [
    "ROLE",
    "SYSTEM",
    "TEMPLATE",
    "TEXTS",
    "VERSION",
    "render",
]

ROLE = "coder"
VERSION = "coder-v1"


SYSTEM = """\
You are an experienced qualitative researcher performing initial coding for an
inductive grounded-theory study of how people picture AI in the year 2050.

You read one survey response at a time against a codebook that is being built up
response by response, and you propose codes for it. You propose only. You never edit
the codebook, never rename anything already in it and never remove anything from it; a
later stage decides what is admitted.

Work by constant comparison. Before you name anything new, compare the segment in front
of you against the codes you have been shown, and reuse an existing code whenever it
already explains the segment.

Answer with a single JSON object and nothing else: no preamble, no commentary, no
markdown fences.
"""


QUESTION_HEADER = """\
## The survey question

Every respondent was answering this question. Code the response as an answer to it, not
as free-standing text.
"""


RESPONSE_HEADER = """\
## The response to code

The text between the tags is the whole of the response, already normalised. Quote out of
it exactly as it appears there.
"""


CODEBOOK_HEADER = """\
## The codebook so far

This codebook is frozen for this batch. You are reading it; you are not writing to it.
"""


CODEBOOK_EMPTY = """\
The codebook is empty. This is the first pass over the corpus, so every code you propose
will be a new one, and you should still keep them at the two levels described below.
"""


QUOTE_RULES = """\
## Evidence

Every code you propose must cite at least one quote, and every quote must be copied
character for character out of the text between the response tags. A quote that is not
an exact substring of that text is dropped by a later check, and the code loses its
evidence with it. Do not tidy the respondent's spelling, punctuation or grammar, do not
join two separate phrases into one quote, and do not paraphrase.
"""


GRANULARITY = """\
## Granularity: the principal investigator's own corrections

Granularity is not an instruction to be more specific. The corrections below run in both
directions, which is why they are given as worked examples rather than as a rule.

The response text in each example is **paraphrased**, not quoted: the investigator's own
examples quote real survey respondents, and respondent text does not belong in a prompt
that is sent to a model provider. The code names, and the correction each example
teaches, are his. See ADR-0024.

1. Response: "it is a very fast calculator that can only work from whatever records we
   hand it"
   Proposed: technology-processing_power
   Corrected to: AI-data-driven
   The proposed code named a property of the machine. The correction names what the
   response is about: that the capability comes from the data it is given.

2. Response: "there will be very little it cannot turn its hand to"
   Proposed: technology-all_encompassing
   Corrected to: AI-multi-use
   Here the correction is the plainer and more abstract of the two. A grand label is not
   a better code than a simple one, and "all encompassing" says less than "multi-use".

3. Response: "we have to make sure these things are built and used responsibly"
   Proposed: concern-core_programming
   Corrected to: concern-ethical_development
   The proposed code guessed at a mechanism the respondent never mentions. Stay with
   what was actually said.

4. Proposed: impact-jobs
   Corrected to: negative_impacts-job_destruction
   Here the correction is the more specific of the two: the response said which way the
   impact ran, so the code should say so too.

5. Response: "one day it will understand the world better than any person could"
   Proposed: future-inevitability
   Corrected to: AI-superintelligence
   Nothing in the codebook fitted, and the right move was to name a new code rather than"""


CORRECTIONS_HEADER = """\
## Hand-coded examples from the principal investigator

These segments were coded by hand. Read them as calibration for granularity and naming,
not as a codebook: they are examples of the researcher's judgement, and the codebook
above is still the authority on what already exists.
"""


OUTPUT = """\
## What to return

Return exactly this shape, and nothing outside it:

{
  "candidates": [
    {
      "name": "toplevel-sub_level",
      "description": "One sentence explaining the key meaning this code names.",
      "evidence": [
        {"response_id": 0, "quote": "an exact substring of the response above"}
      ],
      "parent_hint": "toplevel"
    }
  ]
}

Use the response id printed above in every evidence entry. "parent_hint" is the
top-level family you believe the code belongs under; it is a hint, and the integration
step is free to ignore it.

If the response genuinely supports no code at all, return {"candidates": []}. An empty
answer is a legitimate answer; an invented one is not.
"""


def render_rules(rules: CodingRules) -> str:
    """The PI's coding rules, rendered from the config object that encodes them."""
    lines = [
        "## The coding rules",
        "",
        "These are the rules of this study, and later checks measure your output against",
        "them. They are transcribed from the principal investigator's own instructions.",
        "",
        "1. A code is an explanation of a segment of text's key meaning.",
    ]
    if rules.require_description:
        lines += [
            "   Give every code a one-sentence description that states that meaning in",
            "   your own words. A description that repeats its own quote explains nothing.",
        ]
    lines += [
        "",
        f"2. The codebook has {rules.hierarchy_depth} levels. Name a code",
        "   `toplevel-sub_level`: the part before the FIRST hyphen is the top-level",
        "   family and everything after it is the second level. Use lower case, and",
        "   underscores rather than spaces inside a level.",
        "",
        "3. One response usually corresponds to multiple codes:",
        f"   usually between {rules.min_codes_per_response} and"
        f" {rules.max_codes_per_response} codes."
        ' "Usually" is the word that matters:',
        "   this is advisory, not a quota. A short response supports fewer codes, and",
        f"   padding one out to reach {rules.min_codes_per_response} manufactures"
        " evidence. Propose the codes",
        "   the text actually carries, and never more than "
        f"{rules.max_codes_per_response}.",
        "",
        "4. One sentence can be coded with several codes. The same piece of text can be",
        f"   coded with a maximum of {rules.max_codes_per_segment} codes.",
        "",
        "5. Coding is applied at the level of a phrase or a sentence. A quote may span",
        f"   at most {rules.max_quote_sentences} sentences and at most"
        f" {rules.max_quote_words} words.",
        "   Some responses in this corpus contain no full stop anywhere: quote a clause",
        "   out of such a response, never the whole of it.",
    ]
    if rules.prefer_subcode_first:
        lines += [
            "",
            "6. Consider adding a second-level code under an existing top-level family",
            "   before you add a new top-level family.",
        ]
    lines += [
        "",
        "7. Add or change a code only if a code already in the codebook does not",
        "   adequately describe the response or a part of it.",
    ]
    return "\n".join(lines) + "\n"


def render_question(question: str) -> str:
    return f"{QUESTION_HEADER}\n<question>\n{normalise(question)}\n</question>\n"


def render_response(response: Response) -> str:
    """The response block. Normalised, tagged, and carrying its own id."""
    return (
        f"{RESPONSE_HEADER}\n"
        f"Response id: {response.id}\n\n"
        f"<response>\n{normalise(response.content)}\n</response>\n"
    )


def render_codebook(
    snapshot_id: str,
    skeleton: Mapping[str, Sequence[str]],
    retrieved: Sequence[Code],
) -> str:
    """The frozen snapshot's shape, plus the retrieved codes in full."""
    lines = [CODEBOOK_HEADER, f"Snapshot: {snapshot_id}", ""]
    if not skeleton and not retrieved:
        lines.append(CODEBOOK_EMPTY)
        return "\n".join(lines)

    lines.append("Hierarchy skeleton (top-level family, then its second-level codes):")
    lines.append("")
    for family in sorted(skeleton):
        lines.append(f"  {family}")
        subs = sorted(skeleton[family])
        if subs:
            lines += [f"    - {sub}" for sub in subs]
        else:
            lines.append("    (no second-level codes yet)")
    lines.append("")
    if retrieved:
        lines.append("The codes closest to this response, with their descriptions:")
        lines.append("")
        for code in retrieved:
            description = code.description.strip() or "(no description recorded)"
            lines.append(f"  - {code.name}: {description}")
    else:
        lines.append("No existing code was retrieved as close to this response.")
    lines.append("")
    return "\n".join(lines)


def render_corrections(corrections: Sequence[Assignment]) -> str:
    """Few-shot block. Empty when corrections are held out, which is the default."""
    if not corrections:
        return ""
    lines = [CORRECTIONS_HEADER]
    for item in corrections:
        lines.append(f'  [response {item.response_id}] "{item.segment}" -> {item.code}')
    lines.append("")
    return "\n".join(lines)


def render(
    *,
    response: Response,
    snapshot_id: str,
    skeleton: Mapping[str, Sequence[str]],
    retrieved: Sequence[Code],
    rules: CodingRules,
    corrections: Sequence[Assignment] = (),
) -> RenderedPrompt:
    """Assemble the coding prompt. A pure function of its arguments.

    The section order is fixed: question, response, codebook, rules, evidence,
    granularity, hand-coded examples, output contract. Fixed because two runs must
    produce the same bytes, and because the two coders must receive the same bytes.
    """
    sections = [
        render_question(response.question),
        render_response(response),
        render_codebook(snapshot_id, skeleton, retrieved),
        render_rules(rules),
        QUOTE_RULES,
        GRANULARITY,
        render_corrections(corrections),
        OUTPUT,
    ]
    user = "\n".join(section for section in sections if section)
    return RenderedPrompt(system=SYSTEM, user=user, version=VERSION)


TEXTS: dict[str, str] = {
    "system": SYSTEM,
    "question_header": QUESTION_HEADER,
    "response_header": RESPONSE_HEADER,
    "codebook_header": CODEBOOK_HEADER,
    "codebook_empty": CODEBOOK_EMPTY,
    "rules": render_rules(CodingRules()),
    "quote_rules": QUOTE_RULES,
    "granularity": GRANULARITY,
    "corrections_header": CORRECTIONS_HEADER,
    "output": OUTPUT,
}

TEMPLATE = PromptTemplate(role=ROLE, version=VERSION, texts=TEXTS)
