"""Code-text pairings, and the organiser that turns them into a codebook.

The principal investigator's coding tool exports one row per coded segment: a code
label and the verbatim text it was applied to, with **no response number and no
highlight id**. `read_tagged_pairs` reads that shape from CSV or XLSX, and also the
four-column highlights export the earlier sample arrived in.

`organise_tagged` does everything `codebook/inductive-codebook-prompt2.md` asks for
that is not writing prose. That prompt was written for a language model; every step of
it that is a *counting* or *grouping* decision belongs in deterministic code, where it
is reproducible and auditable, and only the definitions themselves need a model. So:

* **hierarchy on the first hyphen only** (`gaf.models.split_name`), two levels
  maximum, a multi-hyphen remainder kept whole as the subcode;
* **consolidation of trivial variants only** — case, whitespace, and a family token
  that differs from an existing family by hyphen where that family uses underscore.
  Every consolidation is recorded with the rows it touched. Singular/plural and
  spelling near-misses are **flagged and never merged**: merging them is a judgment
  about meaning, and this layer does not make those;
* **frequencies and a total order** — by frequency descending, then name;
* **two verbatim examples per leaf**, chosen by a rule written down below;
* **researcher notes as data** rather than prose, so a later stage can act on them.

Output that carries examples carries respondents' words, so it belongs under ``runs/``
and nowhere else. `to_markdown` and `to_json` therefore **withhold examples by
default** and take ``include_examples=True`` to include them: the failure mode of the
safe default is a visibly incomplete document, and the failure mode of the unsafe one
is silent. `to_mermaid` never carries a segment at all.

Validation principle: **transparency** — the human coding becomes a codebook by a
documented, replayable transformation, with every consolidation, every exclusion and
every anomaly counted rather than absorbed.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import TYPE_CHECKING, Any

from gaf.config import CodingRules
from gaf.ids import code_id
from gaf.models import Code, Codebook, Evidence, split_name
from gaf.textnorm import normalise, normalise_for_match

if TYPE_CHECKING:
    from gaf.ingest.xlsx import HighlightsReport

__all__ = [
    "NEAR_MISS_MAX_DISTANCE",
    "NEAR_MISS_MIN_LENGTH",
    "TAGGED_SOURCE",
    "CodeNote",
    "Consolidation",
    "OrganisedCode",
    "OrganisedCodebook",
    "TaggedPair",
    "organise_tagged",
    "read_tagged_pairs",
    "to_codebook",
    "with_descriptions",
]

#: What `Code.meta["source"]` says about a code that came from the PI's own coding.
TAGGED_SOURCE = "human-tagged"

#: Two labels or two label tokens within this edit distance are a *near miss*: worth
#: the researcher's eye, never merged automatically.
NEAR_MISS_MAX_DISTANCE = 2
#: Below this length an edit distance of two is most of the word, so short tokens
#: ("now"/"no", "jobs"/"job") would swamp the notes with nothing. Five is the shortest
#: length at which two edits still leave a majority of the token intact.
NEAR_MISS_MIN_LENGTH = 5

#: Rule names recorded on a `Consolidation`, in the fixed order they compose in.
_RULE_ORDER: tuple[str, ...] = ("case", "whitespace", "family_separator")


# --------------------------------------------------------------------------- #
# The row shape
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class TaggedPair:
    """One exported row: this code was applied to this segment.

    `row` is the **source file's own row number**, the one a spreadsheet shows in its
    margin, so a consolidation or an anomaly names a row a researcher can open
    directly. `highlight_id` and `document` are empty unless the export carried them
    (the four-column shape does).
    """

    tag: str
    content: str
    row: int
    highlight_id: str = ""
    document: str = ""

    def to_json(self) -> dict[str, Any]:
        return {
            "tag": self.tag,
            "content": self.content,
            "row": self.row,
            "highlight_id": self.highlight_id,
            "document": self.document,
        }


def read_tagged_pairs(path: Path | str, *, sheet: str | None = None) -> list[TaggedPair]:
    """Read ``tag,content`` pairings, or the four-column highlights export, in file order.

    CSV or XLSX; the suffix decides. Columns are resolved by header name, never by
    position, so the extra columns the PI's later workbook grew (a count and two model
    columns beside ``tag`` and ``content``) are simply not read.

    Three kinds of row, and the difference matters:

    * **both pairing cells blank** — not a pairing row at all. The real workbook has
      fifteen of these, carrying values only in the columns this reader does not read.
      Skipped like a blank row, and visible afterwards as a gap in the row numbers;
    * **a segment with no tag** — raises. A segment that names no code cannot be
      placed in a codebook, and choosing one for it would be guessing;
    * **a tag with no segment** — kept. `organise_tagged` counts it as an
      ``empty_content`` note and does not count it as a segment, because a code that
      the PI applied to nothing is a fact about his coding, not a malformed row.
    """
    from gaf.ingest.xlsx import (
        HIGHLIGHT_CONTENT_HEADERS,
        HIGHLIGHT_ID_HEADERS,
        HIGHLIGHT_TAG_HEADERS,
        SpreadsheetFormatError,
        read_table,
        repair_mojibake,
    )

    table = read_table(path, sheet=sheet)
    tag_col = table.require(HIGHLIGHT_TAG_HEADERS)
    content_col = table.require(HIGHLIGHT_CONTENT_HEADERS)
    id_col = table.optional(HIGHLIGHT_ID_HEADERS)
    document_col = table.optional(("document",))

    out: list[TaggedPair] = []
    for offset, row in enumerate(table.data_rows):
        tag = _cell(table.cell(row, tag_col))
        content = _cell(table.cell(row, content_col))
        if not tag.strip() and not content.strip():
            continue
        if not tag.strip():
            raise SpreadsheetFormatError(
                f"{table.path} row {table.row_number(offset)}: a segment with no tag "
                "names no code; a pairing needs both a tag and content"
            )
        out.append(
            TaggedPair(
                # The tag is kept **verbatim**, not stripped: surrounding whitespace is
                # one of the trivial variants `organise_tagged` consolidates, and it
                # can only record a consolidation it was allowed to see.
                tag=repair_mojibake(tag),
                content=repair_mojibake(content),
                row=table.row_number(offset),
                highlight_id=_cell(table.cell(row, id_col)).strip(),
                document=_cell(table.cell(row, document_col)).strip(),
            )
        )
    return out


def _cell(value: Any) -> str:
    return "" if value is None else str(value)


# --------------------------------------------------------------------------- #
# What the organiser produces
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class Consolidation:
    """One label rewritten onto another, and why.

    `from_label` is spelled that way because ``from`` is a keyword; `to_json` emits it
    under the key ``"from"``, which is what a reader of the artefact expects.
    """

    from_label: str
    to: str
    rule: str
    rows: tuple[int, ...]
    #: True when the canonical spelling was *also* written out as a label of its own,
    #: so this rewrite added nothing a reader could not already see. A consumer asking
    #: "did this name exist only because of a consolidation?" needs that difference;
    #: `gaf.ingest.definitions.attach_definitions` is the one that does.
    target_also_written: bool = False

    def to_json(self) -> dict[str, Any]:
        return {
            "from": self.from_label,
            "to": self.to,
            "rule": self.rule,
            "rows": list(self.rows),
            "target_also_written": self.target_also_written,
        }


@dataclass(frozen=True, slots=True)
class CodeNote:
    """One observation for the researcher, as data rather than as prose.

    `category` is a stable machine name (see `organise_tagged` for the list), `subject`
    is what the note is about, `message` is the sentence a human reads, and `data`
    carries the ids, labels and counts a later stage needs.
    """

    category: str
    subject: str
    message: str
    data: dict[str, Any]

    def to_json(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "subject": self.subject,
            "message": self.message,
            "data": dict(self.data),
        }


@dataclass(frozen=True, slots=True)
class OrganisedCode:
    """One code, with its children when it has any. Never more than two levels deep.

    `examples` and `example_note` are populated on any code that carries segments of
    its **own**: a leaf, and also a family that was tagged directly as well as through
    its subcodes. A top-level code with no subcodes is both a parent and a leaf, and
    carries both.

    `count` is the code and everything beneath it; `own_count` is the segments tagged
    on this name itself. They differ only for a family the coder used both ways, and
    keeping that difference is what stops those segments from vanishing (R1 C3).
    """

    name: str
    sub: str
    count: int
    rows: tuple[int, ...]
    children: tuple[OrganisedCode, ...] = ()
    examples: tuple[str, ...] = ()
    example_note: str = ""
    description: str = ""

    @property
    def is_leaf(self) -> bool:
        return not self.children

    @property
    def own_count(self) -> int:
        """Segments tagged on this name itself, excluding its children's.

        Exact rather than approximate: `_build_tree` sets a parent's `count` to its own
        segments plus its children's, so subtracting the children recovers the former.
        """
        return self.count - sum(child.count for child in self.children)

    @property
    def carries_own_segments(self) -> bool:
        """True when this code was applied to text directly, children or not."""
        return self.own_count > 0

    @property
    def parent(self) -> str:
        return split_name(self.name)[0]

    @property
    def level(self) -> int:
        return 2 if self.sub else 1

    def to_json(self, *, include_examples: bool = False) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": self.name,
            "sub": self.sub,
            "level": self.level,
            "count": self.count,
            "own_count": self.own_count,
            "rows": list(self.rows),
            "description": self.description,
            "leaf": self.is_leaf,
            "children": [c.to_json(include_examples=include_examples) for c in self.children],
        }
        if self.is_leaf or self.carries_own_segments:
            payload["example_count"] = len(self.examples)
            payload["example_note"] = self.example_note
            if include_examples:
                payload["examples"] = list(self.examples)
        return payload


@dataclass(frozen=True, slots=True)
class OrganisedCodebook:
    """The PI's pairings as a two-level codebook, plus everything the reader noticed.

    `parents` is the whole structure, ordered by frequency descending then name;
    `consolidations` and `notes` are the audit trail of what was rewritten and what a
    human should look at. `meta` carries provenance — the source path, and the
    description source once `gaf.ingest.definitions.attach_definitions` has run.
    """

    parents: tuple[OrganisedCode, ...]
    consolidations: tuple[Consolidation, ...]
    notes: tuple[CodeNote, ...]
    pair_count: int
    segment_count: int
    meta: dict[str, Any]

    # -- lookups ---------------------------------------------------------- #

    def parent(self, name: str) -> OrganisedCode | None:
        return next((p for p in self.parents if p.name == name), None)

    def leaf(self, name: str) -> OrganisedCode | None:
        """The leaf with this full name, whether it is a subcode or a bare top-level code."""
        for code in self.parents:
            if code.is_leaf and code.name == name:
                return code
            for child in code.children:
                if child.name == name:
                    return child
        return None

    def leaves(self) -> list[OrganisedCode]:
        """Every leaf, in the codebook's own order."""
        out: list[OrganisedCode] = []
        for code in self.parents:
            if code.is_leaf:
                out.append(code)
            out.extend(code.children)
        return out

    def codes_with_segments(self) -> list[OrganisedCode]:
        """Every code that carries segments of its own, in the codebook's own order.

        `leaves` answers a question about *structure*; this answers one about *data*.
        The two differ by exactly one thing: a family the coder applied both directly
        and through its subcodes, whose own segments belong to no leaf and would
        otherwise be rendered nowhere (R1 C3).
        """
        out: list[OrganisedCode] = []
        for code in self.parents:
            if code.is_leaf or code.carries_own_segments:
                out.append(code)
            out.extend(code.children)
        return out

    def names(self) -> list[str]:
        """Every code name, parents included, sorted."""
        return sorted({p.name for p in self.parents} | {c.name for c in self.leaves()})

    def canonical(self, label: str) -> str:
        """The label this raw label was consolidated onto, or the label itself.

        Falls back to the trivial key, so a caller holding a tidied-up spelling of the
        label (a stripped one, say) still reaches the same code. Never guesses beyond
        that: an unknown label comes back unchanged.
        """
        for consolidation in self.consolidations:
            if consolidation.from_label == label:
                return consolidation.to
        key = _trivial_key(label)
        for consolidation in self.consolidations:
            if _trivial_key(consolidation.from_label) == key:
                return consolidation.to
        return label

    def notes_by_category(self) -> dict[str, list[CodeNote]]:
        grouped: dict[str, list[CodeNote]] = {}
        for note in self.notes:
            grouped.setdefault(note.category, []).append(note)
        return {key: grouped[key] for key in sorted(grouped)}

    # -- renderers -------------------------------------------------------- #

    def to_json(self, *, include_examples: bool = False) -> dict[str, Any]:
        """Deterministic dict form. Examples are withheld unless asked for."""
        return {
            "pair_count": self.pair_count,
            "segment_count": self.segment_count,
            "parent_count": len(self.parents),
            "leaf_count": len(self.leaves()),
            "includes_examples": include_examples,
            "meta": dict(sorted(self.meta.items())),
            "codes": [p.to_json(include_examples=include_examples) for p in self.parents],
            "consolidations": [c.to_json() for c in self.consolidations],
            "notes": [n.to_json() for n in self.notes],
        }

    def to_markdown(self, *, include_examples: bool = False) -> str:
        """The PI's five-section layout: tree, listing, descriptions, examples, notes."""
        return _render_markdown(self, include_examples=include_examples)

    def to_mermaid(self) -> str:
        """A ``flowchart LR`` in the shape of the PI's own ``codebook_tree1.mmd``.

        Carries names and counts only, never a segment, so it is safe to share.
        """
        return _render_mermaid(self)


# --------------------------------------------------------------------------- #
# Trivial consolidation
# --------------------------------------------------------------------------- #


def _trivial_key(label: str) -> str:
    """Case-folded, whitespace-free form. Two labels sharing it are trivial variants."""
    return "".join(label.split()).casefold()


def _squash(label: str) -> str:
    return "".join(label.split())


def _variant_rules(label: str, canonical: str) -> list[str]:
    """Which trivial differences separate `label` from `canonical`.

    Only ever called on two labels that already share `_trivial_key`, so exactly one
    of the two differences below must hold, and both may.
    """
    rules: list[str] = []
    if _squash(label) != _squash(canonical):
        rules.append("case")
    if label.casefold() != canonical.casefold():
        rules.append("whitespace")
    return [rule for rule in _RULE_ORDER if rule in rules]


def _edit_distance(left: str, right: str, *, limit: int) -> int:
    """Levenshtein distance, giving up once it exceeds `limit`.

    Returns ``limit + 1`` for anything further apart, which is all a near-miss test
    needs to know and keeps the sweep over a hundred labels cheap.
    """
    if abs(len(left) - len(right)) > limit:
        return limit + 1
    previous = list(range(len(right) + 1))
    for i, left_char in enumerate(left, start=1):
        current = [i]
        for j, right_char in enumerate(right, start=1):
            current.append(
                min(
                    previous[j] + 1,
                    current[j - 1] + 1,
                    previous[j - 1] + (left_char != right_char),
                )
            )
        if min(current) > limit:
            return limit + 1
        previous = current
    return previous[-1]


def _consolidate(
    counts: dict[str, int], rows: dict[str, list[int]]
) -> tuple[dict[str, str], list[Consolidation]]:
    """Map every raw label onto its canonical spelling, and say why for each rewrite.

    Two stages, in this order. **Case and whitespace** first: labels sharing
    `_trivial_key` are one code, and the canonical spelling is chosen by a rule that
    does not depend on file order — a spelling carrying stray whitespace never wins,
    because whitespace in a code name is an export artefact rather than a choice;
    otherwise the most frequent spelling wins, and a tie goes to the plainer spelling
    (fewest capitals) and then alphabetically.

    Then the **family separator**: a label whose first hyphen could be an underscore is
    rewritten when that reading names a family some *other* label already belongs to.
    The real coding has ``key-sectors-...`` beside ten ``key_sectors-...``; the bare
    token ``key-sectors`` is the same typo with one hyphen, and is rewritten on the
    same evidence. ``applications-decision-making`` deliberately is not, because no
    family ``applications_decision`` exists. The rewrite only ever turns a hyphen into
    an underscore: the reverse would have to *split* an underscore, which would make
    ``positive_impacts-general`` a member of a family ``positive``.
    """
    by_key: dict[str, list[str]] = {}
    for label in sorted(counts):
        by_key.setdefault(_trivial_key(label), []).append(label)

    canonical_of: dict[str, str] = {}
    rules_of: dict[str, list[str]] = {}
    def tidiness(name: str) -> tuple[bool, int, int, str]:
        return (
            _squash(name) != name,
            -counts[name],
            sum(1 for char in name if char.isupper()),
            name,
        )

    for key in sorted(by_key):
        group = by_key[key]
        winner = sorted(group, key=tidiness)[0]
        for label in group:
            canonical_of[label] = winner
            rules_of[label] = _variant_rules(label, winner) if label != winner else []

    # Stage two needs the families as stage one left them.
    stage_one = {canonical_of[label] for label in canonical_of}
    families: dict[str, set[str]] = {}
    for label in sorted(stage_one):
        families.setdefault(split_name(label)[0], set()).add(label)

    rewritten: dict[str, str] = {}
    for label in sorted(stage_one):
        # Any label carrying a hyphen can have its *first* one read as the family
        # separator, including a bare family token such as ``key-sectors`` beside ten
        # ``key_sectors-...`` siblings. Gating this on a hyphen inside the *subcode*
        # left exactly that case both unmerged and unflagged (R1 I10). A label with no
        # hyphen has nothing to rewrite, and skipping it keeps `family_separator` off
        # the rule string of a consolidation that did not use it.
        if "-" not in label:
            continue
        alternative = label.replace("-", "_", 1)
        alt_family = split_name(alternative)[0]
        members = families.get(alt_family, set())
        if members - {label}:
            rewritten[label] = alternative

    consolidations: list[Consolidation] = []
    for label in sorted(counts):
        target = canonical_of[label]
        applied = list(rules_of[label])
        if target in rewritten:
            target = rewritten[target]
            applied.append("family_separator")
        canonical_of[label] = target
        if target != label:
            consolidations.append(
                Consolidation(
                    from_label=label,
                    to=target,
                    rule="+".join(rule for rule in _RULE_ORDER if rule in applied) or "exact",
                    rows=tuple(sorted(rows[label])),
                    target_also_written=target in counts,
                )
            )
    consolidations.sort(key=lambda c: (c.to, c.from_label))
    return canonical_of, consolidations


# --------------------------------------------------------------------------- #
# Example selection
# --------------------------------------------------------------------------- #


def _choose_examples(segments: Sequence[tuple[int, str]]) -> tuple[tuple[str, ...], str]:
    """Two distinct verbatim examples for one leaf, and a note when only one exists.

    **The rule**, written down so it can be checked rather than inferred: segments are
    made distinct by `gaf.textnorm.normalise`, so two rows carrying the same words in
    different whitespace are one example. The distinct segments are then ordered by
    **length descending**, ties broken by the normalised text ascending, and the first
    two are taken. Longest-first because a longer segment carries more of the context a
    reader needs to judge whether the definition fits its data; the tie-break makes the
    choice independent of the order the rows happened to arrive in. The raw text kept
    is that of the earliest row carrying that normalised form.
    """
    first_raw: dict[str, str] = {}
    for _row, text in sorted(segments):
        key = normalise(text)
        if key:
            first_raw.setdefault(key, text)
    ordered = sorted(first_raw, key=lambda key: (-len(key), key))
    chosen = tuple(first_raw[key] for key in ordered[:2])
    if len(ordered) == 1:
        return chosen, "only one segment is associated with this code"
    return chosen, ""


# --------------------------------------------------------------------------- #
# The organiser
# --------------------------------------------------------------------------- #


def organise_tagged(
    pairs: Iterable[TaggedPair], *, rules: CodingRules | None = None
) -> OrganisedCodebook:
    """Turn code-text pairings into a two-level codebook, counting everything excluded.

    `rules` supplies the PI's own coding constraints (`gaf.config.CodingRules`); only
    ``max_codes_per_segment`` is consulted here, for the S4 note. Nothing is dropped
    silently: an empty segment is a note, a consolidated label is a record, and a code
    with one segment says so.

    Note categories, all of them data rather than prose:

    ``shared_subcode``              the same subcode label under two or more parents
    ``single_segment_leaf``         a leaf with exactly one segment
    ``multi_hyphen_subcode``        a subcode that itself contains a hyphen
    ``label_near_miss``             two labels or tokens within `NEAR_MISS_MAX_DISTANCE`
    ``segment_under_several_codes`` one identical segment carrying more than one code
    ``segment_over_code_limit``     more codes on one segment than S4 allows
    ``empty_content``               a pairing whose segment is blank
    ``bare_top_level_code``         a top-level code with no subcodes, beside families that have them
    ``family_with_own_segments``    a family tagged directly as well as through its subcodes
    """
    resolved = rules or CodingRules()
    pairs = list(pairs)

    counts: dict[str, int] = {}
    rows_of: dict[str, list[int]] = {}
    segments_of: dict[str, list[tuple[int, str]]] = {}
    notes: list[CodeNote] = []
    empty_rows: list[tuple[int, str]] = []

    for pair in pairs:
        # Verbatim, so that a label differing only in surrounding whitespace is
        # consolidated *and recorded* rather than silently normalised at the door.
        label = pair.tag
        if not label.strip():
            raise ValueError(
                f"row {pair.row}: a pairing with an empty tag names no code; "
                "fix the export rather than guessing which code it meant"
            )
        rows_of.setdefault(label, []).append(pair.row)
        counts.setdefault(label, 0)
        if not pair.content.strip():
            empty_rows.append((pair.row, label))
            continue
        counts[label] += 1
        segments_of.setdefault(label, []).append((pair.row, pair.content))

    canonical_of, consolidations = _consolidate(counts, rows_of)

    merged_counts: dict[str, int] = {}
    merged_rows: dict[str, list[int]] = {}
    merged_segments: dict[str, list[tuple[int, str]]] = {}
    for label in sorted(counts):
        target = canonical_of[label]
        merged_counts[target] = merged_counts.get(target, 0) + counts[label]
        merged_rows.setdefault(target, []).extend(rows_of[label])
        merged_segments.setdefault(target, []).extend(segments_of.get(label, []))

    parents = _build_tree(merged_counts, merged_rows, merged_segments)
    notes.extend(_structure_notes(parents))
    notes.extend(_near_miss_notes(sorted(merged_counts)))
    notes.extend(_segment_notes(merged_segments, limit=resolved.max_codes_per_segment))
    notes.extend(
        CodeNote(
            category="empty_content",
            subject=label,
            message=f"Row {row} tags {label!r} with an empty segment; it is not counted.",
            data={"row": row, "code": label},
        )
        for row, label in sorted(empty_rows)
    )
    notes.sort(key=lambda note: (note.category, note.subject, note.message))

    return OrganisedCodebook(
        parents=tuple(parents),
        consolidations=tuple(consolidations),
        notes=tuple(notes),
        pair_count=len(pairs),
        segment_count=sum(merged_counts.values()),
        meta={"source": TAGGED_SOURCE},
    )


def _build_tree(
    counts: dict[str, int],
    rows: dict[str, list[int]],
    segments: dict[str, list[tuple[int, str]]],
) -> list[OrganisedCode]:
    """Group canonical labels into families and order everything by frequency then name."""
    families: dict[str, list[str]] = {}
    for label in sorted(counts):
        families.setdefault(split_name(label)[0], []).append(label)

    parents: list[OrganisedCode] = []
    for family in sorted(families):
        members = families[family]
        children: list[OrganisedCode] = []
        own_count = 0
        own_rows: list[int] = []
        own_segments: list[tuple[int, str]] = []
        for label in members:
            sub = split_name(label)[1]
            if not sub:
                own_count = counts[label]
                own_rows = rows[label]
                own_segments = segments.get(label, [])
                continue
            examples, note = _choose_examples(segments.get(label, []))
            children.append(
                OrganisedCode(
                    name=label,
                    sub=sub,
                    count=counts[label],
                    rows=tuple(sorted(rows[label])),
                    examples=examples,
                    example_note=note,
                )
            )
        children.sort(key=lambda code: (-code.count, code.name))
        total = own_count + sum(child.count for child in children)
        # A family's own segments are its own, children or not. Discarding them
        # whenever `children` was non-empty lost every one of them silently (R1 C3);
        # `_choose_examples` already answers with nothing when there are none.
        examples, note = _choose_examples(own_segments)
        parents.append(
            OrganisedCode(
                name=family,
                sub="",
                count=total,
                rows=tuple(sorted(own_rows)),
                children=tuple(children),
                examples=examples,
                example_note=note,
            )
        )
    parents.sort(key=lambda code: (-code.count, code.name))
    return parents


def _structure_notes(parents: Sequence[OrganisedCode]) -> list[CodeNote]:
    """Shared subcodes, single-segment leaves, multi-hyphen subcodes, bare top levels."""
    notes: list[CodeNote] = []
    by_sub: dict[str, list[str]] = {}
    for parent in parents:
        for child in parent.children:
            by_sub.setdefault(child.sub, []).append(parent.name)
    for sub in sorted(by_sub):
        owners = sorted(by_sub[sub])
        if len(owners) > 1:
            notes.append(
                CodeNote(
                    category="shared_subcode",
                    subject=sub,
                    message=(
                        f"The subcode {sub!r} appears under {len(owners)} parents "
                        f"({', '.join(owners)}); they may be one code or genuinely different."
                    ),
                    data={"sub": sub, "parents": owners},
                )
            )

    any_children = any(parent.children for parent in parents)
    for parent in parents:
        if any_children and parent.is_leaf:
            notes.append(
                CodeNote(
                    category="bare_top_level_code",
                    subject=parent.name,
                    message=(
                        f"{parent.name!r} is a top-level code with no subcodes while other "
                        "families have them; it may want splitting, or it may be a "
                        "deliberate single-level category."
                    ),
                    data={"code": parent.name, "count": parent.count},
                )
            )
        if parent.children and parent.carries_own_segments:
            notes.append(
                CodeNote(
                    category="family_with_own_segments",
                    subject=parent.name,
                    message=(
                        f"{parent.name!r} was applied to text directly as well as through "
                        f"its subcodes ({parent.own_count} segment(s) of its own); those "
                        "segments belong to the family itself and are counted there."
                    ),
                    data={"code": parent.name, "own_count": parent.own_count},
                )
            )
        for code in (parent, *parent.children):
            if code.is_leaf and code.count == 1:
                notes.append(
                    CodeNote(
                        category="single_segment_leaf",
                        subject=code.name,
                        message=f"{code.name!r} rests on one segment, so it is not yet saturated.",
                        data={"code": code.name, "rows": list(code.rows)},
                    )
                )
            if "-" in code.sub:
                notes.append(
                    CodeNote(
                        category="multi_hyphen_subcode",
                        subject=code.name,
                        message=(
                            f"The subcode of {code.name!r} contains a hyphen; it is kept whole, "
                            "because the hierarchy splits on the first hyphen only."
                        ),
                        data={"code": code.name, "sub": code.sub},
                    )
                )
    return notes


def _near_miss_notes(labels: Sequence[str]) -> list[CodeNote]:
    """Labels and tokens close enough to be a typo, reported and never merged."""
    notes: list[CodeNote] = []
    seen: set[tuple[str, str]] = set()

    def record(left: str, right: str, distance: int, level: str, **extra: Any) -> None:
        key = (left, right)
        if key in seen:
            return
        seen.add(key)
        notes.append(
            CodeNote(
                category="label_near_miss",
                subject=f"{left} ~ {right}",
                message=(
                    f"{left!r} and {right!r} differ by {distance} character "
                    f"{'edit' if distance == 1 else 'edits'} ({level} level); flagged for "
                    "the researcher, never merged -- a near miss is a judgment about meaning."
                ),
                data={"left": left, "right": right, "distance": distance, "level": level, **extra},
            )
        )

    for i, left in enumerate(labels):
        for right in labels[i + 1 :]:
            if min(len(left), len(right)) < NEAR_MISS_MIN_LENGTH:
                continue
            distance = _edit_distance(left, right, limit=NEAR_MISS_MAX_DISTANCE)
            if distance <= NEAR_MISS_MAX_DISTANCE:
                record(left, right, distance, "label")

    tokens: dict[str, set[str]] = {}
    for label in labels:
        for token in _tokens(label):
            if len(token) >= NEAR_MISS_MIN_LENGTH:
                tokens.setdefault(token, set()).add(label)
    ordered = sorted(tokens)
    for i, left in enumerate(ordered):
        for right in ordered[i + 1 :]:
            distance = _edit_distance(left, right, limit=NEAR_MISS_MAX_DISTANCE)
            if distance <= NEAR_MISS_MAX_DISTANCE:
                record(
                    left,
                    right,
                    distance,
                    "token",
                    labels=sorted(tokens[left] | tokens[right]),
                )
    notes.sort(key=lambda note: note.subject)
    return notes


def _tokens(label: str) -> list[str]:
    return [token for token in label.replace("-", " ").replace("_", " ").split() if token]


def _segment_notes(
    segments: Mapping[str, Sequence[tuple[int, str]]], *, limit: int
) -> list[CodeNote]:
    """One identical segment under several codes, and the S4 limit when it is exceeded."""
    by_segment: dict[str, set[str]] = {}
    for label in sorted(segments):
        for _row, text in segments[label]:
            key = normalise_for_match(text)
            if key:
                by_segment.setdefault(key, set()).add(label)

    notes: list[CodeNote] = []
    for key in sorted(by_segment):
        codes = sorted(by_segment[key])
        if len(codes) < 2:
            continue
        # The segment itself is never put in a note: notes travel further than runs/.
        subject = " + ".join(codes)
        notes.append(
            CodeNote(
                category="segment_under_several_codes",
                subject=subject,
                message=(
                    f"One identical segment carries {len(codes)} codes ({', '.join(codes)}); "
                    "constant comparison should say whether they are distinct."
                ),
                data={"codes": codes, "code_count": len(codes)},
            )
        )
        if len(codes) > limit:
            notes.append(
                CodeNote(
                    category="segment_over_code_limit",
                    subject=subject,
                    message=(
                        f"One identical segment carries {len(codes)} codes; the coding rules "
                        f"allow {limit} on one piece of text (S4)."
                    ),
                    data={"codes": codes, "code_count": len(codes), "limit": limit},
                )
            )
    return notes


# --------------------------------------------------------------------------- #
# The codebook
# --------------------------------------------------------------------------- #


def to_codebook(
    organised: OrganisedCodebook,
    *,
    placements: HighlightsReport | None = None,
    descriptions: Mapping[str, str] | None = None,
    description_source: str = "",
) -> Codebook:
    """A `gaf.models.Codebook`: parents as family codes, leaves beneath them.

    With `placements` (a `gaf.ingest.xlsx.HighlightsReport`) each leaf's evidence is
    the segments that were **placed on a response**, carrying the response id and the
    span the S2 locator verified. A segment that could not be placed is not evidence —
    an unlocatable quote is exactly what S2 exists to refuse — and is counted on the
    code's metadata as ``unplaced_segments`` beside ``placed_segments``, so the
    proportion of a code that survived placement is readable from the artefact.

    `descriptions` maps a code name to its definition; see
    `gaf.ingest.definitions.attach_definitions` for the PI's own, and note that a code
    left without one is a WARN from S6, not an error.

    **A description never travels without its source** (D2, ADR-0032). The source is
    `description_source`, or ``organised.meta["description_source"]`` when every
    description came from one document, or ``organised.meta["description_sources"]``
    when they came from several and are keyed by code name. A description with none of
    those raises rather than being attached unattributed — a model-drafted
    sentence that outlives the record of who drafted it is the exact failure ADR-0032
    exists to prevent (R1 I12).
    """
    described = dict(descriptions or {})
    per_code = organised.meta.get("description_sources")
    per_code_sources: Mapping[str, str] = per_code if isinstance(per_code, Mapping) else {}
    one_source = description_source or str(organised.meta.get("description_source") or "")
    if described and not one_source:
        missing = sorted(name for name in described if not per_code_sources.get(name))
        if missing:
            raise ValueError(
                "to_codebook was given descriptions with no description_source for "
                f"{len(missing)} code(s) (first: {missing[0]!r}). Pass "
                "description_source=, or set organised.meta['description_source'] / "
                "['description_sources'] -- a description that outlives the record of "
                "where it came from is what ADR-0032 forbids."
            )
    placed: dict[str, list[Evidence]] = {}
    placed_counts: dict[str, int] = {}
    if placements is not None:
        for mapping in placements.mappings:
            name = organised.canonical(mapping.tag)
            if mapping.response_id is None or mapping.span is None:
                continue
            placed_counts[name] = placed_counts.get(name, 0) + 1
            placed.setdefault(name, []).append(
                Evidence(
                    response_id=mapping.response_id,
                    quote=mapping.content,
                    span=mapping.span,
                    verified=True,
                    score=mapping.score,
                )
            )

    codes: dict[str, Code] = {}
    for parent in organised.parents:
        parent_id = code_id(parent.name)
        codes[parent_id] = _code(
            parent,
            code_id_value=parent_id,
            parent_id=None,
            described=described,
            placed=placed,
            placed_counts=placed_counts,
            one_source=one_source,
            per_code_sources=per_code_sources,
        )
        for child in parent.children:
            child_id = code_id(child.name)
            codes[child_id] = _code(
                child,
                code_id_value=child_id,
                parent_id=parent_id,
                described=described,
                placed=placed,
                placed_counts=placed_counts,
                one_source=one_source,
                per_code_sources=per_code_sources,
            )
    return Codebook(codes=codes)


def _code(
    code: OrganisedCode,
    *,
    code_id_value: str,
    parent_id: str | None,
    described: Mapping[str, str],
    placed: Mapping[str, list[Evidence]],
    placed_counts: Mapping[str, int],
    one_source: str,
    per_code_sources: Mapping[str, str],
) -> Code:
    """One `Code`, with evidence and placement counts only where segments live.

    "Where segments live" is `OrganisedCode.own_count`, not `is_leaf`: a family tagged
    directly as well as through its subcodes holds segments of its own, and gating on
    leafhood dropped every one of them from the evidence and from the accounting
    (R1 C3). A code's own segments are keyed by its full name throughout, so a parent
    never collects its children's.
    """
    meta: dict[str, Any] = {"source": TAGGED_SOURCE}
    evidence: list[Evidence] = []
    if code.is_leaf or code.carries_own_segments:
        total = code.own_count
        found = placed.get(code.name, [])
        seen: set[tuple[int, str]] = set()
        for item in sorted(found, key=lambda e: (e.response_id, e.quote)):
            key = (item.response_id, item.quote)
            if key in seen:
                continue
            seen.add(key)
            evidence.append(item)
        meta["segment_count"] = total
        meta["placed_segments"] = min(placed_counts.get(code.name, 0), total)
        meta["unplaced_segments"] = total - meta["placed_segments"]
    if code.example_note:
        meta["example_note"] = code.example_note
    description = described.get(code.name, code.description)
    source = per_code_sources.get(code.name, "") or one_source
    if source and description:
        meta["description_source"] = source
    return Code(
        id=code_id_value,
        name=code.name,
        description=description,
        parent_id=parent_id,
        evidence=evidence,
        meta=meta,
    )


# --------------------------------------------------------------------------- #
# Renderers
# --------------------------------------------------------------------------- #

_TREE_BRANCH = "\u251c\u2500\u2500 "  # box drawings light vertical and right + horizontals
_TREE_LAST = "\u2514\u2500\u2500 "
_TREE_PIPE = "\u2502   "
_EM_DASH = "\u2014"


def _render_markdown(book: OrganisedCodebook, *, include_examples: bool) -> str:
    lines: list[str] = [
        "# Codebook",
        "",
        f"{len(book.parents)} top-level codes, {len(book.leaves())} leaves, "
        f"{book.segment_count} coded segments from {book.pair_count} rows.",
        "",
        "## 1. Tree Diagram",
        "",
        "```",
        "Codebook",
    ]
    for index, parent in enumerate(book.parents):
        last_parent = index == len(book.parents) - 1
        lines.append(f"{_TREE_LAST if last_parent else _TREE_BRANCH}{parent.name}")
        indent = "    " if last_parent else _TREE_PIPE
        for child_index, child in enumerate(parent.children):
            last_child = child_index == len(parent.children) - 1
            lines.append(f"{indent}{_TREE_LAST if last_child else _TREE_BRANCH}{child.sub}")
    lines += ["```", "", "## 2. Code and Subcode Listing", ""]
    for parent in book.parents:
        kind = "leaf" if parent.is_leaf else "parent"
        lines.append(f"- `{parent.name}` {_EM_DASH} level 1 {_EM_DASH} {kind} {_EM_DASH} n={parent.count}")
        for child in parent.children:
            lines.append(
                f"  - `{parent.name} > {child.sub}` {_EM_DASH} level 2 {_EM_DASH} leaf "
                f"{_EM_DASH} n={child.count}"
            )
    lines += ["", "## 3. Descriptions", ""]
    for parent in book.parents:
        lines += [f"### {parent.name}  *(n={parent.count})*", ""]
        lines += [f"**{parent.name}** {_EM_DASH} {parent.description or '(no description yet)'}", ""]
        for child in parent.children:
            lines.append(
                f"- **{parent.name} > {child.sub}** *(n={child.count})* {_EM_DASH} "
                f"{child.description or '(no description yet)'}"
            )
        if parent.children:
            lines.append("")
    lines += ["## 4. Examples", ""]
    if not include_examples:
        lines += [
            "Examples are verbatim respondent text and are withheld from this rendering.",
            "Render with `include_examples=True`, into `runs/` and nowhere else.",
            "",
        ]
    else:
        for leaf in book.codes_with_segments():
            lines.append(f"### {leaf.name}  *(n={leaf.own_count})*")
            lines.append("")
            for example in leaf.examples:
                lines.append(f"> {example}")
                lines.append("")
            if leaf.example_note:
                lines += [f"*{leaf.example_note}.*", ""]
    lines += ["## 5. Notes for the Researcher", ""]
    grouped = book.notes_by_category()
    if not grouped:
        lines += ["Nothing to flag.", ""]
    for category in grouped:
        lines += [f"**{category}** ({len(grouped[category])})", ""]
        for note in grouped[category]:
            lines.append(f"- {note.message}")
        lines.append("")
    if book.consolidations:
        lines += [f"**consolidations** ({len(book.consolidations)})", ""]
        for consolidation in book.consolidations:
            lines.append(
                f"- `{consolidation.from_label}` -> `{consolidation.to}` "
                f"({consolidation.rule}; rows {', '.join(str(r) for r in consolidation.rows)})"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _render_mermaid(book: OrganisedCodebook) -> str:
    lines = ["flowchart LR", '    ROOT(["Codebook"]):::root']
    child_index = 0
    for parent_index, parent in enumerate(book.parents, start=1):
        node = f"P{parent_index}"
        lines.append(f'    {node}["{parent.name}<br/>n={parent.count}"]:::l1')
        lines.append(f"    ROOT --> {node}")
        for child in parent.children:
            child_index += 1
            child_node = f"S{child_index}"
            lines.append(f'    {child_node}["{child.sub}<br/>n={child.count}"]:::l2')
            lines.append(f"    {node} --> {child_node}")
    lines += [
        "    classDef root fill:#0f172a,stroke:#0f172a,color:#ffffff,font-weight:bold;",
        "    classDef l1 fill:#2563eb,stroke:#1e40af,color:#ffffff,font-weight:bold;",
        "    classDef l2 fill:#eef2ff,stroke:#6366f1,color:#111827;",
    ]
    return "\n".join(lines) + "\n"


def with_descriptions(
    book: OrganisedCodebook, described: Mapping[str, str], meta: Mapping[str, Any]
) -> OrganisedCodebook:
    """A copy of `book` carrying `described` and the extra `meta`.

    Separate from `organise_tagged` because a description is not something the pairings
    contain: it arrives from the PI's own codebook, through
    `gaf.ingest.definitions.attach_definitions`, which is the only caller.
    """
    parents = tuple(
        replace(
            parent,
            description=described.get(parent.name, parent.description),
            children=tuple(
                replace(child, description=described.get(child.name, child.description))
                for child in parent.children
            ),
        )
        for parent in book.parents
    )
    return replace(book, parents=parents, meta={**book.meta, **meta})
