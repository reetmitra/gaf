"""The Definer: a fourth LLM role, and the only one outside both loops.

What this module does. Given one code — its name, its parent, its sibling names and
**all** of the segments a researcher assigned to it — it asks a model for a description
of one to three sentences saying what the code captures and how it differs from its
siblings, and then checks that description deterministically. It writes nothing and
decides nothing else.

**Why a fourth role, and why outside both loops.** Everything else in the researcher's
own prompt for building a codebook inductively from code-text pairings is arithmetic on
a finished human coding: the tree, the listing, the counts, the two verbatim examples
per leaf, the near-duplicate notes. `gaf.ingest.tagged` does all of it in Python. The
one thing left that a model is actually for is prose. The Definer runs once, over a
coding a person has already finished, before or beside a run; it never sees a response
being coded, never proposes a code and never touches a snapshot. It is therefore not a
third loop and not a new stage of either existing one — the architecture's "two loops"
is unchanged; only "three LLM roles" becomes four. See ADR-0034.

**What it cannot do, structurally.** The reply object holds one key. Renaming, merging,
splitting, creating and choosing an example are not expressible in it, so the role
cannot express them — a reply that tries is discarded unread, because the parser reads
one key and no other.

**The guards.** Four deterministic checks run after every call, each one a
`gaf.checks.contracts.CheckFinding`, and none of them repairs anything:

===  =====================================================  ========  ==============
id   what it catches                                        severity  effect
===  =====================================================  ========  ==============
D1   an empty description                                   ERROR     refused
D2   more than `MAX_SENTENCES` sentences                    ERROR     refused
D3   a verbatim copy of one of the code's own segments      ERROR     refused
D4   a run of >= `MAX_SHARED_WORD_RUN` words from a segment  ERROR     refused
===  =====================================================  ========  ==============

D3 and D4 are both ERROR, and both are about shareability rather than quality. ADR-0013
ruled WARN on the same defect in **S1**, where the reasoning was that dropping a
*candidate* would destroy evidence over a formatting complaint; nothing is destroyed
here — a refused description leaves the code undescribed, which S6 already reports as
a WARN of its own. The question D3 asks is D4's: not "is this a good definition" but
"is this string shareable". A description travels into documents the corpus does not,
and a whole segment reproduced verbatim is a quote whatever its length. D4 catches a
run of eight words or more; D3 catches the whole of a shorter one, which D4 cannot see
and which used to reach `organised_shareable.md` with no finding at all once a full
stop had been added to it (R1 I3, ADR-0039).

A refused description is not written back, and is not recorded in its own finding
either — the guard that catches a quote must not become the thing that publishes it. The
findings carry counts.

**Offline.** `gaf.llm.mock.MockDefinerClient` writes an extractive stand-in from the
most frequent content words of the code's own segments. It is a placeholder, not a
definition, so every artefact carrying one is labelled `description_source:
"definer-mock"`. As with the other three roles, the live path is unexercised by the test
suite and by CI.

Validation principles: **interpretive depth** — a description that says how a code
differs from its siblings is what keeps a codebook from flattening into a list of
labels; **transparency** — every description carries the source that produced it, and
every refusal is a row.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from gaf.agents.prompts import definer_v1, loader
from gaf.agents.prompts.base import PromptTemplate
from gaf.agents.prompts.definer_v1 import DefinerRenderer
from gaf.checks.contracts import CheckFinding, CheckReport, Severity
from gaf.config import RunConfig
from gaf.llm.base import CallLog, LLMClient, LLMRequest, LLMResult, TaskType
from gaf.textnorm import normalise, normalise_for_match

__all__ = [
    "DEFINER_CHECK_IDS",
    "DEFINER_LATEST",
    "DEFINER_RENDERERS",
    "DEFINER_TEMPLATES",
    "MAX_SENTENCES",
    "MAX_SHARED_WORD_RUN",
    "SOURCES",
    "SOURCE_LIVE",
    "SOURCE_MOCK",
    "ChildSummary",
    "DefineContext",
    "DefinerAgent",
    "Definition",
    "check_description",
    "count_sentences",
    "definer_renderer",
    "definition_subject",
    "get_definer_template",
    "longest_shared_word_run",
    "parse_description",
    "word_tokens",
]

#: The researcher's own bound: "a concise definition (1-3 sentences)". It lives here
#: rather than in `gaf.config` because `config.py` is a frozen contract and because this
#: is a transcription of a stated instruction, not a threshold a calibration sweep could
#: move. ADR-0034.
MAX_SENTENCES = 3

#: A run of this many consecutive words shared with one of the code's own segments makes
#: the description a quote rather than a description. Eight is the word-side counterpart
#: of the repository's character provenance shingle (`make provenance`): at this
#: corpus's ~5.5 characters per word, eight words is about 44 characters, which cleared
#: that guard's original 30 with headroom and clears its present 20 (ADR-0047) with
#: more. It is also short enough that a description would have to be reproducing a
#: phrase rather than reusing a term to reach it. ADR-0034.
MAX_SHARED_WORD_RUN = 8

#: What produced a description. Recorded on every artefact that carries one, so a
#: stand-in written offline is never read as a definition.
SOURCE_MOCK = "definer-mock"
SOURCE_LIVE = "definer-live"
SOURCES: tuple[str, ...] = (SOURCE_LIVE, SOURCE_MOCK)

#: The guards, in the order they are evaluated. Deliberately outside
#: `gaf.checks.contracts.CHECK_IDS`, which is frozen and enumerates the fast loop's
#: structural and semantic checks: the Definer runs in neither loop, and its findings
#: land in `definer_findings.json`, never in a run's `findings.json`.
DEFINER_CHECK_IDS: tuple[str, ...] = ("D1", "D2", "D3", "D4")

#: Mirrors `gaf.checks.structural._sentence_count`, which is the project's definition of
#: a sentence. A test asserts the two agree; they must, or "three sentences" would mean
#: two different things in two places.
_SENTENCE_END_RE = re.compile(r"[.?!]+")

#: Words for the shared-run comparison: letters and digits only, so punctuation and case
#: cannot be used to slip a quote past the guard.
_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


# --------------------------------------------------------------------------- #
# The Definer's own template registry
# --------------------------------------------------------------------------- #
#
# The Definer resolves through `gaf.agents.prompts.loader` like the other three. It did
# not, once, on the reasoning that `loader.all_templates()` is *the prompt surface of a
# run* — the wording whose hash the golden manifest records as having produced a coding
# — and that the Definer, which never sees a response being coded, does not belong in
# that record. The reasoning is right about the *manifest* and was wrong about the
# *loader*, whose own first sentence is that it is the one place that knows which prompt
# versions exist (R1 N7a). So: registered here, and `tests/test_golden.py` filters the
# manifest to `loader.LOOP_ROLES`, which is where the claim about a coding actually
# lives. ADR-0034, ADR-0039.
#
# The three names below are kept as views onto the loader's registries, because they
# are what this module's callers already import.

DEFINER_TEMPLATES: dict[str, PromptTemplate] = loader.TEMPLATES[definer_v1.ROLE]
DEFINER_RENDERERS: dict[str, DefinerRenderer] = loader.DEFINER_RENDERERS
DEFINER_LATEST: str = loader.LATEST[definer_v1.ROLE]


def get_definer_template(version: str | None = None) -> PromptTemplate:
    """Resolve a definer prompt version; `None` means the build's latest."""
    return loader.get_template(definer_v1.ROLE, version)


def definer_renderer(version: str | None = None) -> DefinerRenderer:
    """The definer render function for `version`; `None` means the build's latest."""
    return loader.definer_renderer(version)


def definition_subject(code_name: str) -> str:
    """`LLMRequest.subject` for a definition: the code it is about."""
    return f"define:{code_name}"


# --------------------------------------------------------------------------- #
# Text helpers — one definition each, shared by the guards and the mock
# --------------------------------------------------------------------------- #


def count_sentences(text: str) -> int:
    """Sentences in `text`, counted by runs of ``.?!``, never less than one.

    The same rule as `gaf.checks.structural._sentence_count`, so a bound of three
    sentences means one thing across the build. An unpunctuated string is one sentence,
    which is why D2 is not the only guard.
    """
    return max(1, len(_SENTENCE_END_RE.findall(normalise(text))))


def word_tokens(text: str) -> list[str]:
    """Case-folded word tokens, punctuation discarded. The unit the run guard counts."""
    return _TOKEN_RE.findall(normalise_for_match(text))


def longest_shared_word_run(description: str, segments: Sequence[str]) -> int:
    """Longest run of consecutive words `description` shares with any one segment.

    Zero when there is no shared word at all. Computed over `word_tokens`, so a
    description cannot dodge the guard with a comma or a capital letter.
    """
    words = word_tokens(description)
    if not words:
        return 0
    longest = 0
    for segment in segments:
        tokens = word_tokens(segment)
        if not tokens:
            continue
        # Row-wise longest common substring over the two token sequences. The corpus is
        # one code's segments against one short description, so this stays small.
        previous = [0] * (len(tokens) + 1)
        for word in words:
            current = [0] * (len(tokens) + 1)
            for index, token in enumerate(tokens, start=1):
                if word == token:
                    current[index] = previous[index - 1] + 1
                    longest = max(longest, current[index])
            previous = current
    return longest


def parse_description(data: Mapping[str, Any]) -> str:
    """The one key this role's reply has. Anything else in the object is discarded.

    Never raises: a reply carrying an operation, a rename or a list of examples parses
    to the empty string, which D1 then reports as an undescribed code.
    """
    raw = data.get("description")
    return normalise(raw) if isinstance(raw, str) else ""


# --------------------------------------------------------------------------- #
# The guards
# --------------------------------------------------------------------------- #


def check_description(
    description: str,
    segments: Sequence[str],
    *,
    code: str,
    max_sentences: int = MAX_SENTENCES,
    max_shared_run: int = MAX_SHARED_WORD_RUN,
) -> CheckReport:
    """Run every guard over one description. Reports; repairs nothing.

    `segments` are the code's *own* segments — for a parent, the segments beneath its
    children, which it was never shown but must still not reproduce.
    """
    report = CheckReport()
    text = normalise(description)
    if not text:
        report.add(
            "D1",
            Severity.ERROR,
            "codebook",
            code,
            "The definer returned no description, so the code is left undescribed.",
            code=code,
        )
        return report

    sentences = count_sentences(text)
    if sentences > max_sentences:
        report.add(
            "D2",
            Severity.ERROR,
            "codebook",
            code,
            f"Description spans {sentences} sentences; a definition is at most "
            f"{max_sentences}.",
            code=code,
            sentences=sentences,
            max_sentences=max_sentences,
        )

    # Compared on **word tokens**, not on the normalised string.
    # `gaf.textnorm.normalise_for_match` folds case and whitespace and leaves
    # punctuation alone, so a copy with a full stop added, or capitalised, slipped past
    # D3 entirely; and below `MAX_SHARED_WORD_RUN` words D4 does not fire either, so a
    # short segment reached the description field with no finding at all (R1 I3).
    tokens = word_tokens(text)
    if tokens and any(tokens == word_tokens(segment) for segment in segments):
        report.add(
            "D3",
            Severity.ERROR,
            "codebook",
            code,
            "Description is a verbatim copy of one of this code's own segments: it "
            "explains nothing (ADR-0013), and a description is shareable where a quote "
            "is not, at any length.",
            code=code,
            words=len(tokens),
        )

    run = longest_shared_word_run(text, segments)
    if run >= max_shared_run:
        report.add(
            "D4",
            Severity.ERROR,
            "codebook",
            code,
            f"Description carries a run of {run} consecutive words from one of this "
            "code's segments; a description is shareable, a quote is not.",
            code=code,
            run_length=run,
            max_shared_run=max_shared_run,
        )
    return report


# --------------------------------------------------------------------------- #
# Context and result
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class ChildSummary:
    """One subcode of a parent being described: its name, its definition, its count."""

    name: str
    description: str
    count: int

    def as_line(self) -> definer_v1.ChildLine:
        return (self.name, self.description, self.count)

    def to_json(self) -> dict[str, Any]:
        return {"name": self.name, "description": self.description, "count": self.count}


@dataclass(frozen=True, slots=True)
class DefineContext:
    """Everything one definition call sees, and the segments its guards run against.

    `segments` is always the code's own text. For a **leaf** it is what the prompt shows.
    For a **parent** it is the union of the segments beneath its children: the prompt
    does not show it — a parent is described from its subcodes — but the guards still
    run against it, because a parent description that reproduces a segment is a quote
    however it came to be written.
    """

    name: str
    parent: str
    siblings: tuple[str, ...]
    segments: tuple[str, ...]
    children: tuple[ChildSummary, ...] = ()
    count: int = 0

    @property
    def is_parent(self) -> bool:
        return bool(self.children)

    def to_json(self) -> dict[str, Any]:
        """Counts and names only. The segments are respondent text and stay out."""
        return {
            "name": self.name,
            "parent": self.parent,
            "siblings": list(self.siblings),
            "segment_count": len(self.segments),
            "count": self.count,
            "children": [child.name for child in self.children],
            "is_parent": self.is_parent,
        }


@dataclass(frozen=True, slots=True)
class Definition:
    """One description, its source, and what the guards said about it.

    `accepted` is "no ERROR finding": a WARN is kept and flagged, exactly as everywhere
    else in this build.
    """

    code: str
    description: str
    source: str
    findings: tuple[CheckFinding, ...]
    request: LLMRequest
    result: LLMResult

    @property
    def accepted(self) -> bool:
        return not any(f.severity is Severity.ERROR for f in self.findings)

    @property
    def prompt_version(self) -> str:
        return self.result.prompt_version

    @property
    def fail_safe(self) -> bool:
        return self.result.fail_safe

    def to_json(self) -> dict[str, Any]:
        """The audit row. **It never carries the description text.**

        An accepted description is written once, into the codebook; a refused one may be
        the very quote the guard caught, and writing it into the findings file would
        publish exactly what the guard exists to stop. Lengths and counts are enough to
        act on, and they are what is here.
        """
        return {
            "code": self.code,
            "source": self.source,
            "accepted": self.accepted,
            "prompt_version": self.prompt_version,
            "fail_safe": self.fail_safe,
            "sentences": count_sentences(self.description) if self.description else 0,
            "words": len(word_tokens(self.description)),
            "findings": [finding.to_json() for finding in self.findings],
        }


# --------------------------------------------------------------------------- #
# The agent
# --------------------------------------------------------------------------- #


class DefinerAgent:
    """Asks for one description per code, and checks every one. Writes nothing.

    Built exactly like the other three roles: a versioned template resolved once, a
    request that carries the version id, an `LLMClient` (so the on-disk response cache
    wraps it unchanged), and the run's shared `CallLog`.

    The role reuses `TaskType.REFACTOR` and the `refactorer` slot of `ModelRegistry`,
    because `gaf.llm.base` and `gaf.config` are frozen contracts and this build adds the
    fourth role without amending either. Both are the frontier, whole-codebook,
    outside-the-fast-loop binding, which is the right shape for this work; the fail-safe
    that comes with the task type is an empty object, which parses to no description and
    is therefore already the non-destructive default. A definer call is still
    distinguishable in the call log by its prompt version and its `define:` subject.
    See ADR-0034.
    """

    def __init__(
        self,
        client: LLMClient,
        *,
        config: RunConfig | None = None,
        prompt_version: str | None = None,
        call_log: CallLog | None = None,
        max_sentences: int = MAX_SENTENCES,
    ) -> None:
        self.client = client
        self.config = config or RunConfig()
        self.template = get_definer_template(prompt_version)
        self._render = definer_renderer(self.template.version)
        self.call_log = call_log
        self.max_sentences = max_sentences
        self.source = SOURCE_MOCK if client.spec.provider == "mock" else SOURCE_LIVE

    @property
    def prompt_version(self) -> str:
        return self.template.version

    def build_request(self, context: DefineContext) -> LLMRequest:
        """The request for one code. A pure function of the context and the template."""
        prompt = self._render(
            code_name=context.name,
            parent=context.parent,
            siblings=context.siblings,
            segments=context.segments,
            children=tuple(child.as_line() for child in context.children),
            count=context.count,
            max_sentences=self.max_sentences,
        )
        return prompt.to_request(TaskType.REFACTOR, subject=definition_subject(context.name))

    def define(self, context: DefineContext) -> Definition:
        """Ask for one description and check it. Never raises."""
        request = self.build_request(context)
        result = self.client.complete_json(request)
        if self.call_log is not None:
            self.call_log.record(result)
        data = result.data if isinstance(result.data, Mapping) else {}
        return self._definition_for(
            context, parse_description(data), request=request, result=result
        )

    def _definition_for(
        self,
        context: DefineContext,
        description: str,
        *,
        request: LLMRequest | None = None,
        result: LLMResult | None = None,
    ) -> Definition:
        """Attach the guards to a description. The seam the guards are tested through."""
        resolved_request = request if request is not None else self.build_request(context)
        resolved_result = (
            result
            if result is not None
            else LLMResult(
                data={"description": description},
                task=TaskType.REFACTOR,
                provider=self.client.spec.provider,
                model=self.client.spec.model,
                prompt_version=self.template.version,
            )
        )
        report = check_description(
            description,
            context.segments,
            code=context.name,
            max_sentences=self.max_sentences,
        )
        return Definition(
            code=context.name,
            description=description,
            source=self.source,
            findings=tuple(report.findings),
            request=resolved_request,
            result=resolved_result,
        )
