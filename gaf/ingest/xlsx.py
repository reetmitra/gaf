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

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openpyxl import load_workbook

from gaf.models import Assignment

__all__ = [
    "CODE_HEADERS",
    "RESPONSE_HEADERS",
    "RESPONSE_ID_HEADERS",
    "RawResponseRow",
    "SpreadsheetFormatError",
    "read_coded_xlsx",
    "read_narrative_state_xlsx",
    "repair_mojibake",
]

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
