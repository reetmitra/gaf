"""Readers for the two spreadsheet shapes this project ingests, and the encoding
repair that has to happen before either becomes text the pipeline reasons about.

Two readers:

1. **Raw responses** — the shape of ``NarrativeState(IndiaSample1-20).xlsx``:
   a ``Number | Response`` header and one row per response, with **non-contiguous
   ids** (the real file starts at 9 and skips). ``No`` is accepted as an alternative
   spelling of the id header because the PI's prompt versions disagree about it.
   The question is *not* attached here; that is `gaf.ingest.corpus`'s job.
2. **Coded workbooks** — the golden set: ``No``/``Number | Response | Code``, one row
   per assignment, where the "Response" column holds **the segment coded**, not the
   whole response. Returns `gaf.models.Assignment` rows.

Both readers resolve columns **by header name, never by position**. That is not
fastidiousness: the real file's used range is A1:D21, so every row arrives as a
4-tuple with two trailing empty columns, and anything unpacking by position breaks on
it. Blank trailing columns and blank trailing rows are dropped; a required column that
is genuinely absent raises an error naming the file and the headers that were found,
because a guessed column silently mis-ingests a whole corpus.

**Encoding repair.** The real sample contains text that was written as UTF-8 and
decoded once as a legacy Mac/Windows codepage, so a curly quote arrives as a
three-character sequence of accented Latin letters. `repair_mojibake` undoes exactly
one such round, and only when doing so *strictly reduces* the number of suspicious
characters — so genuine punctuation that merely happens to be in the suspect set is
left alone. The repair happens here, before the text becomes `Response.content`,
because `gaf.textnorm` is a frozen contract and every persisted span, embedding,
evidence quote and explorer highlight indexes into `normalise(content)`: repairing
later would mean spans that point at characters that no longer exist. Repairs are
reported, never silent — `RawResponseRow.encoding_repaired` carries the fact upward to
`gaf.ingest.corpus`, which puts it in the record's metadata and in its ingest report.

Validation principle: **transparency** — ingestion is a documented, replayable
transformation from a named file to content-hashed records, including the one place it
alters the bytes it was given.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import TYPE_CHECKING, Any

from openpyxl import load_workbook

from gaf.models import Assignment, Response
from gaf.textnorm import normalise

__all__ = [
    "CODE_HEADERS",
    "RESPONSE_HEADERS",
    "RESPONSE_ID_HEADERS",
    "RawResponseRow",
    "SpreadsheetFormatError",
    "Table",
    "assign_numbered_ids",
    "parse_numbered_cell",
    "place_highlights",
    "read_coded_xlsx",
    "read_narrative_state_xlsx",
    "read_table",
    "repair_mojibake",
]

if TYPE_CHECKING:  # a type only: importing it at runtime would close an import cycle
    from gaf.ingest.tagged import TaggedPair

#: Accepted spellings of the id column. The PI's prompt versions disagree: Prompt
#: Version 3 names a "Number" column, and the coded workbooks say "No".
RESPONSE_ID_HEADERS: tuple[str, ...] = ("number", "no")
#: Accepted spellings of the text column (the whole response, or the coded segment).
RESPONSE_HEADERS: tuple[str, ...] = ("response",)
#: Accepted spellings of the code column in a coded workbook.
CODE_HEADERS: tuple[str, ...] = ("code",)


class SpreadsheetFormatError(ValueError):
    """A workbook does not have the shape the reader requires.

    Always names the file and what was actually found, because the person who has to
    act on it is looking at a spreadsheet, not at a traceback.
    """


# --------------------------------------------------------------------------- #
# Encoding repair
# --------------------------------------------------------------------------- #
#
# Written as escapes rather than literal glyphs so this source file stays ASCII and
# the set is unambiguous to read: these are the accented Latin letters and the
# punctuation marks that dominate UTF-8-decoded-as-a-codepage damage. U+201C ("left
# double quotation mark") is UTF-8 E2 80 9C, which read as MacRoman becomes
# U+201A U+00C4 U+00FA -- three characters from this set, in place of one quote.

_SUSPECT_CHARS = frozenset(
    "ÄÅÇÉÑÖÜ"  # A-diaeresis, A-ring, C-cedilla, E-acute, N-tilde, O/U-diaeresis
    "áàâäãåç"  # a-acute, a-grave, a-circumflex, a-diaeresis, a-tilde, a-ring, c-cedilla
    "éèêë"  # e-acute, e-grave, e-circumflex, e-diaeresis
    "íìîïñ"  # i-acute, i-grave, i-circumflex, i-diaeresis, n-tilde
    "óòôöõ"  # o-acute, o-grave, o-circumflex, o-diaeresis, o-tilde
    "úùûü"  # u-acute, u-grave, u-circumflex, u-diaeresis
    # Written as escapes because the low-9 quote is visually a comma: U+201A, U+201E
    # (low-9 quotes), U+2020 / U+2021 (daggers), U+2022 (bullet), U+2026 (ellipsis),
    # U+2030 (per-mille) -- the punctuation that dominates codepage damage.
    "\u201a\u201e\u2020\u2021\u2022\u2026\u2030"
)

#: Tried in order; the first candidate that improves the text wins on merit, not order.
_LEGACY_CODEPAGES: tuple[str, ...] = ("mac_roman", "cp1252", "latin-1")


def _suspect_count(text: str) -> int:
    return sum(1 for char in text if char in _SUSPECT_CHARS)


def repair_mojibake(text: str) -> str:
    """Undo one round of UTF-8 decoded as a legacy codepage, when it round-trips cleanly.

    The guard that makes this safe is that a candidate repair is accepted **only when
    it strictly reduces** the number of suspicious characters. Text containing a
    genuine ellipsis, or a lone low quote that no re-decoding improves, is returned
    unchanged; so is any text that cannot be encoded to the codepage at all.

    Idempotent by construction: repaired text has fewer suspicious characters, and a
    second pass can only be accepted if it reduces the count again.
    """
    if not any(char in _SUSPECT_CHARS for char in text):
        return text
    best = text
    best_score = _suspect_count(text)
    for encoding in _LEGACY_CODEPAGES:
        try:
            candidate = text.encode(encoding).decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
        score = _suspect_count(candidate)
        if score < best_score:
            best, best_score = candidate, score
    return best


# --------------------------------------------------------------------------- #
# Row shape
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class RawResponseRow:
    """One row of a raw-response workbook, after column resolution and repair.

    `encoding_repaired` is True when `repair_mojibake` changed this row's text. It
    travels upward so the fact appears in the corpus metadata and the run report
    rather than being a silent mutation of the PI's data.
    """

    response_id: int
    content: str
    encoding_repaired: bool = False
    #: The number as written in the source file. Equal to `response_id` except for a
    #: duplicate, where `response_id` has been offset to stay unique (see
    #: `read_numbered_column_xlsx`). Carried so the PI's own numbering is never lost.
    source_number: int | None = None
    #: 0 for a normal row; k for the k-th *extra* row that repeats an earlier number.
    duplicate_ordinal: int = 0


# --------------------------------------------------------------------------- #
# Sheet plumbing
# --------------------------------------------------------------------------- #


def _read_sheet_rows(path: Path, sheet: str | None) -> list[tuple[Any, ...]]:
    """Every row of one sheet as a tuple of cell values, including padding columns."""
    if not path.exists():
        raise SpreadsheetFormatError(f"{path}: no such spreadsheet")
    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        if sheet is None:
            worksheet = workbook.worksheets[0]
        elif sheet in workbook.sheetnames:
            worksheet = workbook[sheet]
        else:
            raise SpreadsheetFormatError(
                f"{path}: no sheet named {sheet!r}; sheets present: {workbook.sheetnames}"
            )
        return [tuple(row) for row in worksheet.iter_rows(values_only=True)]
    finally:
        workbook.close()


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _header_key(value: Any) -> str:
    """Case-folded, whitespace-stripped header name; blank for an unlabelled column."""
    return "" if value is None else str(value).strip().casefold()


def _resolve_columns(
    rows: Sequence[tuple[Any, ...]], path: Path
) -> tuple[dict[str, int], list[tuple[Any, ...]], list[str], int]:
    """Split a sheet into columns, data rows, raw headers, and the header's row number.

    The first row that is not entirely blank is the header. Columns whose header is
    blank are not addressable by name and are therefore dropped -- but only if they
    are also entirely empty. A blank-headed column carrying data is ambiguous input
    and raises, because the alternative is guessing what it means.
    """
    header_index = next((i for i, row in enumerate(rows) if not all(map(_is_blank, row))), None)
    if header_index is None:
        raise SpreadsheetFormatError(f"{path}: the sheet is empty")
    header_row = rows[header_index]
    data_rows = list(rows[header_index + 1 :])
    raw_headers = [("" if value is None else str(value)) for value in header_row]

    columns: dict[str, int] = {}
    for index, value in enumerate(header_row):
        key = _header_key(value)
        if not key:
            occupied = [
                header_index + 1 + n
                for n, row in enumerate(data_rows)
                if index < len(row) and not _is_blank(row[index])
            ]
            if occupied:
                raise SpreadsheetFormatError(
                    f"{path}: column {index + 1} has no header but carries data on "
                    f"row(s) {occupied[:5]}; name the column or remove it -- this "
                    "reader never identifies a column by position."
                )
            continue
        columns.setdefault(key, index)
    return columns, data_rows, raw_headers, header_index + 1


def _require_column(
    columns: dict[str, int], accepted: Sequence[str], *, path: Path, raw_headers: Sequence[str]
) -> int:
    for name in accepted:
        if name in columns:
            return columns[name]
    found = [h for h in raw_headers if h.strip()] or ["<no headers at all>"]
    raise SpreadsheetFormatError(
        f"{path}: required column missing. Expected one of "
        f"{list(accepted)}, found headers {found}."
    )


def _cell_text(value: Any) -> str:
    return "" if value is None else str(value)


# --------------------------------------------------------------------------- #
# One named table, whatever file it came out of
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class Table:
    """A header row resolved into named columns, plus the data rows beneath it.

    The same abstraction over a workbook sheet and a CSV, so a reader written once
    accepts both — which is what the PI's later files require: he sent the same
    pairing export as ``.csv`` and as ``.xlsx``. Columns are addressed **by header
    name, never by position**, exactly as the workbook readers already insist.
    """

    path: Path
    columns: dict[str, int]
    data_rows: tuple[tuple[Any, ...], ...]
    raw_headers: tuple[str, ...]
    #: 1-based source row the header was found on; the first data row is the next one.
    header_row: int

    def require(self, accepted: Sequence[str]) -> int:
        """Index of the first present column among `accepted`, or raise by name."""
        return _require_column(
            self.columns, accepted, path=self.path, raw_headers=self.raw_headers
        )

    def optional(self, accepted: Sequence[str]) -> int | None:
        """Index of the first present column among `accepted`, or ``None``."""
        return next((self.columns[name] for name in accepted if name in self.columns), None)

    def cell(self, row: tuple[Any, ...], index: int | None) -> Any:
        """The cell at `index`, or ``None`` when the row is short or `index` is None."""
        if index is None or index >= len(row):
            return None
        return row[index]

    def row_number(self, offset: int) -> int:
        """Source row number of the data row at 0-based `offset`."""
        return self.header_row + 1 + offset


def read_table(path: Path | str, *, sheet: str | None = None) -> Table:
    """Read a named table from a workbook sheet or a CSV, resolving its columns.

    The suffix decides which parser runs; everything downstream sees one shape. The
    CSV reader lives in `gaf.ingest.csv_corpus` and is imported here lazily, so the
    two modules can depend on each other's public surface without an import cycle.
    """
    path = Path(path)
    if path.suffix.lower() in (".csv",):
        from gaf.ingest.csv_corpus import read_csv_rows

        rows: Sequence[tuple[Any, ...]] = read_csv_rows(path)
    else:
        rows = _read_sheet_rows(path, sheet)
    columns, data_rows, raw_headers, header_row = _resolve_columns(rows, path)
    return Table(
        path=path,
        columns=columns,
        data_rows=tuple(data_rows),
        raw_headers=tuple(raw_headers),
        header_row=header_row,
    )


def _coerce_response_id(value: Any, *, path: Path, row_number: int) -> int:
    if isinstance(value, bool):
        raise SpreadsheetFormatError(
            f"{path} row {row_number}: response id is a boolean, not a number"
        )
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    text = str(value).strip()
    try:
        return int(text)
    except ValueError:
        raise SpreadsheetFormatError(
            f"{path} row {row_number}: response id {value!r} is not a whole number"
        ) from None


# --------------------------------------------------------------------------- #
# The two readers
# --------------------------------------------------------------------------- #


def read_narrative_state_xlsx(
    path: Path | str, *, sheet: str | None = None
) -> list[RawResponseRow]:
    """Read a raw-response workbook in file order, repairing encoding damage.

    Returns enough to build `gaf.models.Response` objects; the survey question is
    attached by `gaf.ingest.corpus`, because it is a property of the run's
    configuration rather than of the file.

    Ids are returned exactly as they appear, so the real file's non-contiguous
    9, 10, 12, 16, ... survives ingest untouched. Duplicate ids raise: two rows
    claiming the same respondent cannot both be that respondent.
    """
    path = Path(path)
    rows = _read_sheet_rows(path, sheet)
    columns, data_rows, raw_headers, header_row = _resolve_columns(rows, path)
    id_col = _require_column(columns, RESPONSE_ID_HEADERS, path=path, raw_headers=raw_headers)
    text_col = _require_column(columns, RESPONSE_HEADERS, path=path, raw_headers=raw_headers)

    out: list[RawResponseRow] = []
    seen: dict[int, int] = {}
    for offset, row in enumerate(data_rows):
        row_number = header_row + 1 + offset  # 1-based, counted from the header row
        if all(map(_is_blank, row)):
            continue  # blank trailing (or interior) row
        id_value = row[id_col] if id_col < len(row) else None
        text_value = row[text_col] if text_col < len(row) else None
        if _is_blank(id_value):
            raise SpreadsheetFormatError(
                f"{path} row {row_number}: the row has content but no response id"
            )
        if _is_blank(text_value):
            raise SpreadsheetFormatError(
                f"{path} row {row_number}: response {id_value!r} has an empty Response cell"
            )
        response_id = _coerce_response_id(id_value, path=path, row_number=row_number)
        if response_id in seen:
            raise SpreadsheetFormatError(
                f"{path} row {row_number}: response id {response_id} already appeared on "
                f"row {seen[response_id]}; ids must be unique within a file"
            )
        seen[response_id] = row_number
        raw_text = _cell_text(text_value)
        repaired = repair_mojibake(raw_text)
        out.append(
            RawResponseRow(
                response_id=response_id,
                content=repaired,
                encoding_repaired=repaired != raw_text,
            )
        )
    return out


def read_coded_xlsx(path: Path | str, *, sheet: str | None = None) -> list[Assignment]:
    """Read a hand-coded workbook (the golden set) as `gaf.models.Assignment` rows.

    One row is one assignment: the "Response" column holds the *segment* that was
    coded, not the whole response, and the same response id therefore appears once per
    code applied to it. Duplicate ids are expected here and are not an error.

    Segment text goes through the same `repair_mojibake` as response text does, so a
    human quote and the response it was taken from remain byte-comparable -- quote
    provenance (S2) is a string-containment question and would fail on an
    encoding mismatch that has nothing to do with the coding.
    """
    path = Path(path)
    rows = _read_sheet_rows(path, sheet)
    columns, data_rows, raw_headers, header_row = _resolve_columns(rows, path)
    id_col = _require_column(columns, RESPONSE_ID_HEADERS, path=path, raw_headers=raw_headers)
    segment_col = _require_column(columns, RESPONSE_HEADERS, path=path, raw_headers=raw_headers)
    code_col = _require_column(columns, CODE_HEADERS, path=path, raw_headers=raw_headers)

    out: list[Assignment] = []
    for offset, row in enumerate(data_rows):
        row_number = header_row + 1 + offset
        if all(map(_is_blank, row)):
            continue
        cells = {
            "id": row[id_col] if id_col < len(row) else None,
            "segment": row[segment_col] if segment_col < len(row) else None,
            "code": row[code_col] if code_col < len(row) else None,
        }
        missing = [name for name, value in cells.items() if _is_blank(value)]
        if missing:
            raise SpreadsheetFormatError(
                f"{path} row {row_number}: incomplete assignment, missing {missing}; "
                "every coded row needs an id, a segment and a code"
            )
        out.append(
            Assignment(
                response_id=_coerce_response_id(cells["id"], path=path, row_number=row_number),
                segment=repair_mojibake(_cell_text(cells["segment"])),
                code=repair_mojibake(_cell_text(cells["code"])),
            )
        )
    return out


# --------------------------------------------------------------------------- #
# Numbered single-column corpus:  "11. <the response text> ..."
# --------------------------------------------------------------------------- #

#: Matches a cell whose text opens with the response number: "11. text", "11) text".
_NUMBERED_CELL = re.compile(r"^\s*(\d+)\s*[.)]\s*(.+)$", re.S)

#: Offset applied to the k-th extra occurrence of a repeated source number, so two
#: responses the PI numbered identically both survive with distinct ids. 1000 is far
#: above any response number a study of this size will reach; a collision with a
#: genuine later number raises rather than being absorbed.
DUPLICATE_ID_STRIDE = 1000


def parse_numbered_cell(text: str) -> tuple[int, str] | None:
    """``"11. text"`` -> ``(11, "text")``; ``None`` when the cell carries no number.

    The one place the ``NN.`` prefix grammar is written. Both the workbook reader and
    the CSV reader ask this function, so the two shapes cannot drift apart.
    """
    match = _NUMBERED_CELL.match(text)
    if match is None:
        return None
    return int(match.group(1)), match.group(2).strip()


def assign_numbered_ids(
    entries: Sequence[tuple[int, int, str]], *, path: Path
) -> list[RawResponseRow]:
    """Turn ``(source row, number, text)`` triples into rows, applying ADR-0029 §1.

    A repeated number does **not** raise: the first occurrence keeps its number and
    the k-th extra gets ``number + DUPLICATE_ID_STRIDE * k``, with the number as
    written kept on `RawResponseRow.source_number` and ``duplicate_ordinal = k``. Two
    responses the principal investigator numbered identically are both genuine
    respondents; dropping one or silently renumbering hides a fact about his file.

    Encoding damage is repaired here too, so a CSV corpus and a workbook corpus of the
    same responses produce byte-identical records.
    """
    out: list[RawResponseRow] = []
    occurrences: dict[int, int] = {}
    assigned: set[int] = set()
    for row_number, number, body in entries:
        if not body:
            raise SpreadsheetFormatError(f"{path} row {row_number}: response {number} has no text")
        ordinal = occurrences.get(number, 0)
        occurrences[number] = ordinal + 1
        response_id = number + DUPLICATE_ID_STRIDE * ordinal
        if response_id in assigned:
            raise SpreadsheetFormatError(
                f"{path} row {row_number}: the duplicate offset for repeated number {number} "
                f"collides with an existing id {response_id}; renumber the source file"
            )
        assigned.add(response_id)
        repaired = repair_mojibake(body)
        out.append(
            RawResponseRow(
                response_id=response_id,
                content=repaired,
                encoding_repaired=repaired != body,
                source_number=number,
                duplicate_ordinal=ordinal,
            )
        )
    return out


def looks_like_numbered_column(rows: Sequence[tuple[Any, ...]]) -> bool:
    """True when every non-blank row is a single cell that opens with "NN. ".

    This is the shape the principal investigator's corpus samples arrive in: no header,
    one column, the response number folded into the text. It is detected rather than
    declared so `load_corpus` can accept either shape from one command.
    """
    seen = 0
    for row in rows:
        cells = [c for c in row if not _is_blank(c)]
        if not cells:
            continue
        if len(cells) != 1 or not _NUMBERED_CELL.match(_cell_text(cells[0])):
            return False
        seen += 1
    return seen > 0


def sniff_numbered_column(path: Path | str, *, sheet: str | None = None) -> bool:
    """`looks_like_numbered_column` for a path, so callers need no private helper."""
    return looks_like_numbered_column(_read_sheet_rows(Path(path), sheet))


def read_numbered_column_xlsx(
    path: Path | str, *, sheet: str | None = None
) -> list[RawResponseRow]:
    """Read a corpus whose only column holds "NN. response text", in file order.

    The number is split off and becomes the response id. **A repeated number does not
    raise here**, unlike `read_narrative_state_xlsx`: the real file numbers two
    different responses 44, and both are genuine respondents. The first keeps its
    number; the k-th extra occurrence is given ``number + DUPLICATE_ID_STRIDE * k`` and
    the original number is kept on `RawResponseRow.source_number` with
    `duplicate_ordinal = k`, so the fact is reported rather than silently repaired or
    silently dropped.
    """
    path = Path(path)
    rows = _read_sheet_rows(path, sheet)
    if not looks_like_numbered_column(rows):
        raise SpreadsheetFormatError(
            f"{path}: not a numbered single-column corpus (expected every row to be one "
            'cell opening with "NN. ")'
        )
    entries: list[tuple[int, int, str]] = []
    for index, row in enumerate(rows):
        cells = [c for c in row if not _is_blank(c)]
        if not cells:
            continue
        parsed = parse_numbered_cell(_cell_text(cells[0]))
        assert parsed is not None  # guaranteed by looks_like_numbered_column
        entries.append((index + 1, parsed[0], parsed[1]))
    return assign_numbered_ids(entries, path=path)


# --------------------------------------------------------------------------- #
# A coding-tool "highlights" export:  id | document | tag | content
# --------------------------------------------------------------------------- #

HIGHLIGHT_TAG_HEADERS: tuple[str, ...] = ("tag", "code")
HIGHLIGHT_CONTENT_HEADERS: tuple[str, ...] = ("content", "text", "segment", "highlight")
HIGHLIGHT_ID_HEADERS: tuple[str, ...] = ("id", "highlight_id", "highlight id")


#: The outcomes of placing one highlight, in the order a report prints them.
HIGHLIGHT_OUTCOMES: tuple[str, ...] = ("exact", "fuzzy", "resolved", "ambiguous", "unlocated")


@dataclass(frozen=True, slots=True)
class HighlightMapping:
    """Where one highlight landed, and how confidently.

    ``span`` indexes ``normalise(response.content)``, like every other offset in this
    project, and is ``None`` exactly when the highlight was not placed. It is recorded
    here so a later stage can build `gaf.models.Evidence` without re-locating the quote
    against the corpus.
    """

    highlight_id: str
    tag: str
    content: str
    response_id: int | None
    outcome: str  # one of HIGHLIGHT_OUTCOMES
    score: float
    candidates: tuple[int, ...]
    span: tuple[int, int] | None = None

    def to_json(self) -> dict[str, Any]:
        return {
            "highlight_id": self.highlight_id,
            "tag": self.tag,
            "content": self.content,
            "response_id": self.response_id,
            "outcome": self.outcome,
            "score": self.score,
            "candidates": list(self.candidates),
            "span": list(self.span) if self.span is not None else None,
        }


@dataclass(frozen=True, slots=True)
class HighlightsReport:
    """What mapping a highlights export onto a corpus did, as countable facts.

    An export names no response; every highlight is placed by locating its text. The
    counts here are the evidence for that placement, and the unlocated list is the
    first thing to read: on the real sample it is the highlights that belong to
    responses the corpus file does not contain.
    """

    path: str
    total: int
    exact: int
    fuzzy: int
    ambiguous: int
    unlocated: int
    per_response: dict[int, int]
    mappings: tuple[HighlightMapping, ...]
    #: Highlights placed by the coded-set rule (ADR-0031): the text fits more than one
    #: response, but only one of those responses is coded at all. Counted apart from
    #: `exact` and `fuzzy` because it rests on a different kind of evidence -- the
    #: coding's own coverage rather than the text -- and included in `mapped`.
    resolved: int = 0
    #: How many responses hold at least one exact or fuzzy highlight. This is the set
    #: `resolved` was decided against, and the denominator a reader needs to judge it.
    coded_response_count: int = 0

    @property
    def mapped(self) -> int:
        return self.exact + self.fuzzy + self.resolved

    def summary(self) -> str:
        return (
            f"{self.total} highlights: {self.mapped} mapped to a response "
            f"({self.exact} exact, {self.fuzzy} fuzzy, {self.resolved} resolved against "
            f"the {self.coded_response_count} responses already coded), "
            f"{self.ambiguous} ambiguous (excluded), "
            f"{self.unlocated} unlocated (not in this corpus)"
        )

    def to_json(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "total": self.total,
            "mapped": self.mapped,
            "exact": self.exact,
            "fuzzy": self.fuzzy,
            "resolved": self.resolved,
            "ambiguous": self.ambiguous,
            "unlocated": self.unlocated,
            "coded_response_count": self.coded_response_count,
            "per_response": {str(k): v for k, v in sorted(self.per_response.items())},
            "mappings": [m.to_json() for m in self.mappings],
        }


def place_highlights(
    pairs: Sequence[TaggedPair],
    corpus: Sequence[Response],
    *,
    fuzzy_threshold: float = 0.85,
    path: str = "",
) -> tuple[list[Assignment], HighlightsReport]:
    """Place code-text pairings onto a corpus by locating their text. Source-agnostic.

    An export names no response, so each segment is placed by where its text occurs:
    an exact substring of exactly one normalised response, else the single response
    scoring at or above `fuzzy_threshold` under the same locator S2 uses.

    **Two passes, and the second one is the only rule that is new** (ADR-0031). On 200
    responses a short segment sits verbatim in more than one of them, and first-pass
    ambiguity is no longer rare. After the first pass the **coded set** is every
    response holding at least one ``exact`` or ``fuzzy`` highlight — the responses this
    coding demonstrably covers. An ambiguous highlight with exactly one candidate in
    that set is placed there, with outcome ``resolved``. Everything else stays
    ``ambiguous`` and is excluded, as is everything ``unlocated``; both are counted and
    listed, never guessed at.

    The coded set is computed from the whole first pass, so the outcome does not depend
    on the order the rows arrive in. Nothing here consults the export's own highlight
    ids: ADR-0029 §2 measured them and found they follow the order the codes were
    *applied* in, not document order.

    Returns the placed highlights as `Assignment` rows — the row-oriented shape every
    downstream comparison consumes — plus the report. The same segment coded twice
    becomes two rows, which is how the PI's "at most two codes on one piece of text"
    shows up in the data.
    """
    from gaf.checks.structural import locate_quote  # one quote locator in the codebase

    texts = {r.id: normalise(r.content) for r in corpus}
    first_pass: list[HighlightMapping] = []

    for index, pair in enumerate(pairs):
        content = pair.content
        needle = normalise(content)
        highlight_id = pair.highlight_id or str(index)
        # Verbatim on the mapping (it is a record of the export), stripped only where
        # it becomes an `Assignment.code` that downstream comparison consumes.
        tag = pair.tag

        hits = [rid for rid, text in texts.items() if needle and needle in text]
        outcome, score, response_id = "unlocated", 0.0, None
        span: tuple[int, int] | None = None
        if len(hits) == 1:
            start = texts[hits[0]].find(needle)
            outcome, score, response_id = "exact", 1.0, hits[0]
            span = (start, start + len(needle))
        elif len(hits) > 1:
            outcome = "ambiguous"
        elif needle:
            scored = sorted(
                (
                    (locate_quote(needle, text, fuzzy_threshold)[1], rid)
                    for rid, text in texts.items()
                ),
                reverse=True,
            )
            best, best_rid = scored[0] if scored else (0.0, None)
            above = [rid for s, rid in scored if s >= fuzzy_threshold]
            score = float(best)
            if len(above) == 1 and best_rid is not None:
                outcome, response_id = "fuzzy", best_rid
                hits = above
                span = locate_quote(needle, texts[best_rid], fuzzy_threshold)[2]
            elif len(above) > 1:
                outcome, hits = "ambiguous", above
        first_pass.append(
            HighlightMapping(
                highlight_id=highlight_id,
                tag=tag,
                content=content,
                response_id=response_id,
                outcome=outcome,
                score=score,
                candidates=tuple(sorted(hits)),
                span=span,
            )
        )

    coded_set = {
        m.response_id
        for m in first_pass
        if m.outcome in ("exact", "fuzzy") and m.response_id is not None
    }

    assignments: list[Assignment] = []
    mappings: list[HighlightMapping] = []
    per_response: dict[int, int] = {}
    counts = dict.fromkeys(HIGHLIGHT_OUTCOMES, 0)

    for mapping in first_pass:
        if mapping.outcome == "ambiguous":
            inside = sorted(set(mapping.candidates) & coded_set)
            if len(inside) == 1:
                target = inside[0]
                needle = normalise(mapping.content)
                # The candidates may have come from the fuzzy branch, where the text is
                # not a substring of any response; ask the locator for the span rather
                # than resolving a highlight nothing can point at. A highlight with no
                # span stays ambiguous, so `mapped` and the evidence always agree.
                #
                # The score is recomputed **at the chosen response**. The first pass
                # left 0.0 on the exact-substring branch and, on the fuzzy branch, the
                # best score across every response rather than the score here; either
                # one travels into `Evidence(verified=True, score=...)` and is rendered
                # as "locator score 0.000" on a verbatim match (R1, brief Important).
                _found, target_score, span = locate_quote(
                    needle, texts[target], fuzzy_threshold
                )
                if span is not None:
                    mapping = replace(
                        mapping,
                        outcome="resolved",
                        response_id=target,
                        span=span,
                        score=float(target_score),
                    )
        counts[mapping.outcome] += 1
        if mapping.response_id is not None:
            assignments.append(
                Assignment(
                    response_id=mapping.response_id,
                    segment=mapping.content,
                    code=mapping.tag.strip(),
                )
            )
            per_response[mapping.response_id] = per_response.get(mapping.response_id, 0) + 1
        mappings.append(mapping)

    report = HighlightsReport(
        path=path,
        total=len(mappings),
        exact=counts["exact"],
        fuzzy=counts["fuzzy"],
        ambiguous=counts["ambiguous"],
        unlocated=counts["unlocated"],
        per_response=per_response,
        mappings=tuple(mappings),
        resolved=counts["resolved"],
        coded_response_count=len(coded_set),
    )
    return assignments, report


def read_highlights_xlsx(
    path: Path | str,
    corpus: Sequence[Response],
    *,
    sheet: str | None = None,
    fuzzy_threshold: float = 0.85,
) -> tuple[list[Assignment], HighlightsReport]:
    """Read a coding-tool highlights export and place every highlight onto the corpus.

    Kept as the named entry point for the four-column export; the reading is
    `gaf.ingest.tagged.read_tagged_pairs` and the placing is `place_highlights`, so a
    CSV export and a workbook export take exactly the same path.
    """
    from gaf.ingest.tagged import read_tagged_pairs

    pairs = read_tagged_pairs(path, sheet=sheet)
    return place_highlights(
        pairs, corpus, fuzzy_threshold=fuzzy_threshold, path=str(Path(path))
    )
