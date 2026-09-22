"""The numbered corpus as CSV: ``All`` carries ``NN. <the response text>``.

The principal investigator's full Process corpus arrived as a CSV rather than a
workbook, in a shape neither existing reader knew: a header ``All,,Trimmed``, a
byte-order mark, an unnamed and entirely empty middle column, and every response
number folded into the front of the ``All`` cell. ``Trimmed`` is the same text with
the number removed.

The rules here are the ones ADR-0029 settled for the workbook of the same shape, so a
corpus ingests identically whichever file type it arrives in:

* **detected, not declared** — `gaf ingest` takes either file from one command, and
  `sniff_numbered_csv` answers the same question `sniff_numbered_column` answers for a
  sheet. A CSV in neither shape raises and names what was found, because a reader that
  guesses a column silently mis-ingests a whole corpus;
* **the number comes from the prefix**, and a repeated number keeps both responses
  (ADR-0029 §1) — the offsetting lives in `gaf.ingest.xlsx.assign_numbered_ids`, which
  both paths call, so they cannot drift apart;
* **`Trimmed` wins** where the two columns disagree after whitespace normalisation,
  because it is the PI's own cleaning pass — but every such row is *reported*, in the
  `IngestReport` and on the ingest line, including the row where ``Trimmed`` is blank
  and ``All`` has to stand in for it. A silent preference between two spellings of
  a respondent's words is exactly the invisible transformation this project forbids;
* **encoding damage is repaired and flagged**, as in the workbook path.

A CSV holding only the numbered column, with or without a header, is the same shape
with one column and reads the same way.

Validation principle: **transparency** — ingestion is a documented, replayable
transformation from a named file to content-hashed records, including every place it
chooses between two things the source says.
"""

from __future__ import annotations

import csv
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from gaf.ingest.xlsx import (
    RawResponseRow,
    SpreadsheetFormatError,
    assign_numbered_ids,
    parse_numbered_cell,
)
from gaf.textnorm import normalise

__all__ = [
    "CSV_SUFFIXES",
    "NUMBERED_HEADERS",
    "TRIMMED_HEADERS",
    "read_csv_rows",
    "read_numbered_csv",
    "sniff_numbered_csv",
]

CSV_SUFFIXES: tuple[str, ...] = (".csv",)

#: The header of the column holding ``NN. <the response text>``. Deliberately not a
#: list of plausible synonyms: a reader that accepts "Response" would claim a headed
#: `Number | Response` CSV it cannot read. Detection is narrow on purpose.
NUMBERED_HEADERS: tuple[str, ...] = ("all",)
#: The header of the column holding the same text without its number.
TRIMMED_HEADERS: tuple[str, ...] = ("trimmed",)


def read_csv_rows(path: Path | str, *, encoding: str = "utf-8-sig") -> list[tuple[Any, ...]]:
    """Every row of a CSV as a tuple of cell strings.

    ``utf-8-sig`` is the default because the PI's exports carry a byte-order mark: read
    as plain UTF-8 the first header would be ``\\ufeffAll`` and would resolve to no
    known column, which is a mis-ingest that looks like a format error.
    """
    path = Path(path)
    if not path.exists():
        raise SpreadsheetFormatError(f"{path}: no such spreadsheet")
    with path.open("r", encoding=encoding, newline="") as handle:
        return [tuple(row) for row in csv.reader(handle)]


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _header_key(value: Any) -> str:
    return "" if value is None else str(value).strip().casefold()


def _layout(rows: Sequence[tuple[Any, ...]], path: Path) -> tuple[int, int | None, int]:
    """``(numbered column, trimmed column or None, first data row index)``.

    Two shapes are accepted and nothing else. A header row is one whose first non-blank
    cell does not open with ``NN.``; ``All``/``Trimmed`` then name the columns. With no
    header, every row must be a single numbered cell — the same rule
    `looks_like_numbered_column` applies to a sheet, so a second populated column is
    refused rather than guessed at.
    """
    header_index = next((i for i, row in enumerate(rows) if not all(map(_is_blank, row))), None)
    if header_index is None:
        raise SpreadsheetFormatError(f"{path}: the file is empty")

    first = rows[header_index]
    leading = next((c for c in first if not _is_blank(c)), None)
    if leading is not None and parse_numbered_cell(_text(leading)) is not None:
        # Headerless: one numbered column and nothing else.
        for index, row in enumerate(rows):
            cells = [c for c in row if not _is_blank(c)]
            if len(cells) > 1:
                raise SpreadsheetFormatError(
                    f"{path} row {index + 1}: a headerless numbered corpus is one column, "
                    f"but this row has {len(cells)}; add an 'All' / 'Trimmed' header row "
                    "to say what the other columns are -- this reader never identifies a "
                    "column by position."
                )
        return 0, None, 0

    keys = [_header_key(cell) for cell in first]
    numbered = next((i for i, key in enumerate(keys) if key in NUMBERED_HEADERS), None)
    trimmed = next((i for i, key in enumerate(keys) if key in TRIMMED_HEADERS), None)
    if numbered is None:
        found = [key for key in keys if key] or ["<no headers at all>"]
        raise SpreadsheetFormatError(
            f"{path}: not a numbered corpus. Expected either a header naming one of "
            f"{list(NUMBERED_HEADERS)} (optionally beside one of {list(TRIMMED_HEADERS)}), "
            'or every row to be one cell opening with "NN. ". '
            f"Found headers {found} and no numbered cell on the first row."
        )

    # An unnamed column is not addressable, so it must be empty -- the real file's
    # middle column is. One carrying data is ambiguous input and raises.
    for index, key in enumerate(keys):
        if key:
            continue
        occupied = [
            header_index + 1 + n
            for n, row in enumerate(rows[header_index + 1 :])
            if index < len(row) and not _is_blank(row[index])
        ]
        if occupied:
            raise SpreadsheetFormatError(
                f"{path}: column {index + 1} has no header but carries data on row(s) "
                f"{occupied[:5]}; name the column or empty it -- this reader never "
                "identifies a column by position."
            )
    return numbered, trimmed, header_index + 1


def sniff_numbered_csv(path: Path | str, *, encoding: str = "utf-8-sig") -> bool:
    """True when this CSV is a numbered corpus in either accepted shape.

    Detection rather than declaration is what lets `gaf ingest` take the workbook and
    the CSV from one command. Answers False — never raises — so a caller can try the
    next reader; `read_numbered_csv` is the one that explains a refusal.
    """
    path = Path(path)
    try:
        rows = read_csv_rows(path, encoding=encoding)
        numbered, _, start = _layout(rows, path)
    except SpreadsheetFormatError:
        return False
    seen = 0
    for row in rows[start:]:
        if all(map(_is_blank, row)):
            continue
        if parse_numbered_cell(_text(row[numbered] if numbered < len(row) else "")) is None:
            return False
        seen += 1
    return seen > 0


def read_numbered_csv(
    path: Path | str, *, encoding: str = "utf-8-sig"
) -> tuple[list[RawResponseRow], tuple[int, ...]]:
    """Read a numbered CSV corpus in file order.

    Returns the rows and the **response ids whose two columns disagreed**. A
    disagreement is compared after `gaf.textnorm.normalise`, so a difference of
    whitespace alone is not one; where the two genuinely differ, ``Trimmed`` wins and
    the id is reported upward into the `IngestReport`.

    A **blank** ``Trimmed`` beside a populated ``All`` is a disagreement too — the
    largest one the two columns can have — and is reported as such before ``All`` is
    used. ``Trimmed`` cannot win when it says nothing, but the substitution is never
    silent.
    """
    path = Path(path)
    rows = read_csv_rows(path, encoding=encoding)
    numbered_col, trimmed_col, start = _layout(rows, path)

    entries: list[tuple[int, int, str]] = []
    disagreeing: list[int] = []  # positions within `entries`
    for offset, row in enumerate(rows[start:]):
        row_number = start + offset + 1
        if all(map(_is_blank, row)):
            continue
        cell = _text(row[numbered_col]) if numbered_col < len(row) else ""
        parsed = parse_numbered_cell(cell)
        if parsed is None:
            raise SpreadsheetFormatError(
                f"{path} row {row_number}: expected a cell opening with \"NN. \", "
                f"found {cell[:40]!r}"
            )
        number, from_prefix = parsed
        body = from_prefix
        if trimmed_col is not None:
            trimmed = _text(row[trimmed_col]).strip() if trimmed_col < len(row) else ""
            if trimmed:
                if normalise(trimmed) != normalise(from_prefix):
                    disagreeing.append(len(entries))
                body = trimmed
            elif from_prefix.strip():
                # A blank `Trimmed` beside a populated `All` is the largest
                # disagreement the two columns can have, not the absence of one.
                # Falling back to `All` in silence would let the report claim the
                # columns agree everywhere while one of them is empty.
                disagreeing.append(len(entries))
        entries.append((row_number, number, body))

    out = assign_numbered_ids(entries, path=path)
    return out, tuple(out[i].response_id for i in disagreeing)
