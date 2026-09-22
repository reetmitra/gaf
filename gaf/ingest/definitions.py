"""The principal investigator's own code descriptions, read out of his codebook Markdown.

ADR-0029 recorded an input asymmetry that has blocked code-level comparison since the
golden set arrived: his export carries code *names* and no descriptions, the machine
codebook carries both, and in the lexical fallback space a name-plus-description vector
against a name-only vector scores the same concept anywhere from 0.4 to 0.7. This
module removes the asymmetry by importing his descriptions.

Section ``## 3. Descriptions`` of ``AI_Perceptions_Codebook1.md`` is the source. Its
shape, and nothing else, is what this reader knows:

* ``### <parent>  *(n=N)*`` opens a top-level category;
* ``**<parent>** <em dash> <description>`` gives that category its definition;
* ``- **<parent> > <sub>** *(n=N)* <em dash> <description>`` gives a subcode its own.
* A top-level **leaf** has the parent line and no bullets at all.

Keys are the pipeline's name form throughout -- ``parent-sub``, or ``parent`` for a
parent or a top-level leaf -- so a definition and a code are the same string or they
are not the same code. `attach_definitions` does **no fuzzy matching**: the only names
it will reconcile are ones the *same trivial consolidation* `gaf.ingest.tagged` applies
already brought together. A misspelt subcode stays undefined and is reported as such,
because deciding that two nearly-identical names mean one thing is a judgment about
meaning, and this layer does not make those.

These descriptions were drafted by a language model from the PI's own prompt
(``codebook/inductive-codebook-prompt2.md``) and are imported **as given** -- see
ADR-0032. They are grounded in respondent text and may echo it, so a codebook carrying
them belongs under ``runs/`` like any other output that touches the corpus.

Validation principle: **interpretive depth** -- a code compared by name alone is
compared on its label; a code compared with the definition its author wrote is compared
on what he meant by it.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, overload

from gaf.ingest.tagged import OrganisedCodebook, with_descriptions
from gaf.models import Codebook

__all__ = [
    "DEFINITION_SOURCE",
    "DESCRIPTIONS_HEADING",
    "ConsolidatedMatch",
    "DefinitionsMatch",
    "DefinitionsReport",
    "attach_definitions",
    "read_definitions_md",
]

#: What ``meta["description_source"]`` says about a description imported from here.
DEFINITION_SOURCE = "pi-codebook-md"

#: The section this reader takes descriptions from.
DESCRIPTIONS_HEADING = "3. Descriptions"

#: The separators the codebook uses between a name and its description: an em dash in
#: the real file, written as an escape so this module stays ASCII. An en dash and a
#: plain hyphen are accepted because a hand edit is likelier than a reformat.
_DASHES = "\u2014\u2013-"

_SECTION_RE = re.compile(r"^##\s+(?P<title>.+?)\s*$")
_PARENT_HEADING_RE = re.compile(r"^###\s+(?P<name>.+?)\s*(?:\*\(n=(?P<count>\d+)\)\*)?\s*$")
_PARENT_LINE_RE = re.compile(
    rf"^\*\*(?P<name>[^*]+?)\*\*\s*[{_DASHES}]\s*(?P<description>.+?)\s*$"
)
_SUB_LINE_RE = re.compile(
    r"^\s*[-*]\s+\*\*(?P<parent>[^*>]+?)\s*>\s*(?P<sub>[^*]+?)\*\*"
    r"\s*(?:\*\(n=(?P<count>\d+)\)\*)?"
    rf"\s*[{_DASHES}]\s*(?P<description>.+?)\s*$"
)


@dataclass(frozen=True, slots=True)
class DefinitionsReport:
    """Every description in section 3, keyed by the pipeline's name form.

    `unparsed_line_numbers` carries **numbers, never text**: section 4 of the same
    document is verbatim respondent quotation, and a reader that echoed what it could
    not parse would be one refactor away from carrying a quote into a report.
    """

    path: str
    definitions: dict[str, str]
    counts: dict[str, int]
    parents: tuple[str, ...]
    top_level_leaves: tuple[str, ...]
    unparsed_line_numbers: tuple[int, ...]

    def __len__(self) -> int:
        return len(self.definitions)

    @property
    def subcode_count(self) -> int:
        """Definitions that are not a top-level code's own.

        Derived from what was actually parsed rather than from
        ``len(definitions) - len(parents)``: a ``###`` heading with no ``**name**``
        line contributes a parent and no definition, which made the subtraction
        undercount, and a repeated heading drove it negative (R1 Minor).
        """
        top_level = set(self.parents)
        return sum(1 for name in self.definitions if name not in top_level)

    def summary(self) -> str:
        return (
            f"{len(self.definitions)} descriptions from {self.path}: "
            f"{len(self.parents)} top-level codes "
            f"({len(self.top_level_leaves)} of them leaves), "
            f"{self.subcode_count} subcodes; "
            f"{len(self.unparsed_line_numbers)} lines not parsed"
        )

    def to_json(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "definitions": dict(sorted(self.definitions.items())),
            "counts": dict(sorted(self.counts.items())),
            "parents": list(self.parents),
            "top_level_leaves": list(self.top_level_leaves),
            "unparsed_line_numbers": list(self.unparsed_line_numbers),
            "source": DEFINITION_SOURCE,
        }


@dataclass(frozen=True, slots=True)
class ConsolidatedMatch:
    """A defined name that exists only because a label was rewritten onto it.

    `from_labels` holds **every** spelling that folded onto `name`, sorted, because a
    many-to-one fold is several rewrites and reporting it as one understates how much
    tidying the coding needed (R1 I9).
    """

    name: str
    from_labels: tuple[str, ...]

    def to_json(self) -> dict[str, Any]:
        return {"name": self.name, "from_labels": list(self.from_labels)}


@dataclass(frozen=True, slots=True)
class DefinitionsMatch:
    """What attaching a set of definitions to a codebook reconciled, and what it did not."""

    matched: int
    defined_not_tagged: tuple[str, ...]
    tagged_not_defined: tuple[str, ...]
    #: Every defined name that the coding export never wrote out, and that exists only
    #: because `gaf.ingest.tagged` rewrote one or more labels onto it. A name the
    #: export *did* write is not here, however many variants also folded onto it: the
    #: definition would have matched it with no consolidation at all.
    matched_after_consolidation: tuple[ConsolidatedMatch, ...]

    def summary(self) -> str:
        spellings = sum(len(m.from_labels) for m in self.matched_after_consolidation)
        return (
            f"{self.matched} codes defined; "
            f"{len(self.defined_not_tagged)} defined but never tagged, "
            f"{len(self.tagged_not_defined)} tagged but undefined, "
            f"{len(self.matched_after_consolidation)} matched only after consolidation "
            f"({spellings} spelling(s) rewritten)"
        )

    def to_json(self) -> dict[str, Any]:
        return {
            "matched": self.matched,
            "defined_not_tagged": list(self.defined_not_tagged),
            "tagged_not_defined": list(self.tagged_not_defined),
            "matched_after_consolidation": [
                item.to_json() for item in self.matched_after_consolidation
            ],
        }


def read_definitions_md(path: Path | str) -> DefinitionsReport:
    """Read section 3 of the PI's codebook Markdown.

    Raises `ValueError` naming the heading when the document has no section 3: a file
    in another shape must refuse rather than return an empty set of definitions that a
    caller would read as "he defined nothing".
    """
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    start: int | None = None
    end = len(lines)
    for index, line in enumerate(lines):
        match = _SECTION_RE.match(line)
        if match is None:
            continue
        title = match.group("title").strip()
        if start is None and title.casefold().startswith(DESCRIPTIONS_HEADING.casefold()):
            start = index
        elif start is not None and index > start:
            end = index
            break
    if start is None:
        raise ValueError(
            f"{path}: no '## {DESCRIPTIONS_HEADING}' section; this reader takes code "
            "descriptions from that section and will not guess at another layout."
        )

    definitions: dict[str, str] = {}
    counts: dict[str, int] = {}
    parents: list[str] = []
    with_children: set[str] = set()
    unparsed: list[int] = []
    current: str | None = None

    for offset, line in enumerate(lines[start + 1 : end]):
        line_number = start + 2 + offset
        if not line.strip():
            continue
        heading = _PARENT_HEADING_RE.match(line)
        if heading is not None:
            current = heading.group("name").strip()
            # A heading repeated in the document names one code, not two: counting it
            # twice made `subcode_count` negative on the repeat (R1 Minor).
            if current not in parents:
                parents.append(current)
            if heading.group("count") is not None:
                counts[current] = int(heading.group("count"))
            continue
        sub = _SUB_LINE_RE.match(line)
        if sub is not None:
            name = f"{sub.group('parent').strip()}-{sub.group('sub').strip()}"
            definitions[name] = sub.group("description").strip()
            if sub.group("count") is not None:
                counts[name] = int(sub.group("count"))
            with_children.add(sub.group("parent").strip())
            continue
        parent = _PARENT_LINE_RE.match(line)
        if parent is not None:
            name = parent.group("name").strip()
            definitions[name] = parent.group("description").strip()
            continue
        unparsed.append(line_number)

    return DefinitionsReport(
        path=str(path),
        definitions=definitions,
        counts=counts,
        parents=tuple(parents),
        top_level_leaves=tuple(name for name in parents if name not in with_children),
        unparsed_line_numbers=tuple(unparsed),
    )


Definitions = DefinitionsReport | Mapping[str, str]


@overload
def attach_definitions(
    target: OrganisedCodebook, definitions: Definitions
) -> tuple[OrganisedCodebook, DefinitionsMatch]: ...


@overload
def attach_definitions(
    target: Codebook, definitions: Definitions
) -> tuple[Codebook, DefinitionsMatch]: ...


def attach_definitions(
    target: OrganisedCodebook | Codebook, definitions: Definitions
) -> tuple[OrganisedCodebook | Codebook, DefinitionsMatch]:
    """Set descriptions on a codebook and report both directions of absence.

    Returns a **new** codebook -- both shapes are frozen -- carrying the descriptions
    and ``meta["description_source"] = DEFINITION_SOURCE`` on every code that received
    one, together with a `DefinitionsMatch` naming the codes defined but never tagged,
    the codes tagged but never defined, and the names that met only after the trivial
    consolidation `gaf.ingest.tagged` already applied. No fuzzy matching: a name is
    either the same string or a trivial variant of it, or it does not match.
    """
    if isinstance(definitions, DefinitionsReport):
        described = dict(definitions.definitions)
    else:
        described = dict(definitions)

    folded_onto: dict[str, list[str]] = {}
    also_written: set[str] = set()
    if isinstance(target, OrganisedCodebook):
        names = set(target.names())
        for consolidation in target.consolidations:
            folded_onto.setdefault(consolidation.to, []).append(consolidation.from_label)
            if consolidation.target_also_written:
                also_written.add(consolidation.to)
    else:
        names = {code.name for code in target.codes.values()}

    resolved: dict[str, str] = {}
    after_consolidation: list[ConsolidatedMatch] = []
    unmatched: list[str] = []

    for name in sorted(described):
        if name in names:
            resolved[name] = described[name]
            # Only a name the export never wrote out matched *because of* the
            # consolidation. One that was also tagged plainly would have matched
            # anyway, and calling it otherwise overstates the tidying (R1 I9).
            if name in folded_onto and name not in also_written:
                after_consolidation.append(
                    ConsolidatedMatch(name=name, from_labels=tuple(sorted(folded_onto[name])))
                )
            continue
        unmatched.append(name)

    match = DefinitionsMatch(
        matched=len(resolved),
        defined_not_tagged=tuple(unmatched),
        tagged_not_defined=tuple(sorted(names - set(resolved))),
        matched_after_consolidation=tuple(
            sorted(after_consolidation, key=lambda item: item.name)
        ),
    )

    if isinstance(target, OrganisedCodebook):
        return with_descriptions(
            target, resolved, {"description_source": DEFINITION_SOURCE}
        ), match
    return _describe_codebook(target, resolved), match


def _describe_codebook(codebook: Codebook, described: Mapping[str, str]) -> Codebook:
    """A copy of `codebook` whose codes carry their descriptions and that provenance."""
    codes = dict(codebook.codes)
    for identifier, code in codebook.codes.items():
        description = described.get(code.name)
        if description is None:
            continue
        codes[identifier] = replace(
            code,
            description=description,
            meta={**code.meta, "description_source": DEFINITION_SOURCE},
        )
    return Codebook(codes=codes)
