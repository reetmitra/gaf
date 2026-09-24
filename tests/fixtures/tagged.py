"""In-test builders for the four input shapes that arrived after the first two.

The real files are human survey data and are gitignored, so the suite constructs its
own. Every builder writes the *exact* header and layout the principal investigator's
files use -- the ``All,,Trimmed`` numbered CSV with its byte-order mark and empty
middle column, the two-column ``tag,content`` pairing, the four-column highlights
export, and the codebook Markdown's section-3 layout -- without reproducing a single
character of what those files contain. Every tag, segment and description below is
invented, and the segments are substrings of `tests.fixtures.corpus`, which is itself
invented.

``*.csv`` and ``*.xlsx`` are gitignored repository-wide, so files built here are
written into ``tmp_path`` at test time and never exist on disk between runs.

Validation principle: **reliability** -- the suite runs from a clean clone with no
real data present.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable, Sequence
from pathlib import Path

from openpyxl import Workbook

__all__ = [
    "DEFINITIONS_MD",
    "HIGHLIGHTS_HEADER",
    "NUMBERED_CSV_HEADER",
    "SAMPLE_NUMBERED",
    "SAMPLE_PAIRS",
    "TAGGED_HEADER",
    "write_definitions_md",
    "write_numbered_csv",
    "write_rows_csv",
    "write_tagged_csv",
    "write_tagged_xlsx",
]

#: The header of the numbered CSV corpus, verbatim: the middle column is unnamed and
#: empty in every row, and the file carries a UTF-8 byte-order mark.
NUMBERED_CSV_HEADER: tuple[str, str, str] = ("All", "", "Trimmed")

#: The header of the code-text pairing export.
TAGGED_HEADER: tuple[str, str] = ("tag", "content")

#: The header of the coding-tool highlights export.
HIGHLIGHTS_HEADER: tuple[str, str, str, str] = ("id", "document", "tag", "content")

#: Non-contiguous numbers, as the real corpus has: it starts above 1 and skips.
SAMPLE_NUMBERED: tuple[tuple[int, str], ...] = (
    (11, "Rural clinics get diagnostic support and the specialist stops being far away."),
    (14, "Clerical posts in the district office vanish quietly, and no scheme arrives."),
    (19, "By then the reservoirs will run themselves and the engineers argue with a model."),
)

#: Invented code-text pairings whose segments are substrings of the synthetic corpus,
#: so the placement path can be exercised. The shape mirrors the real export: two
#: levels split on the first hyphen, one bare top-level code, one family written with
#: a hyphen where its ten siblings use an underscore, one misspelling, one subcode
#: label that appears under two parents, and one segment carrying two codes.
SAMPLE_PAIRS: tuple[tuple[str, str], ...] = (
    ("positive_impacts-health", "Rural clinics get diagnostic support"),
    ("positive_impacts-health", "calling a doctor unprompted"),
    ("positive_impacts-general", "Quality of life improves on average"),
    ("negative_impacts-job_destruction", "Clerical posts in the district office vanish"),
    ("negative_impacts-job_destruction", "The port employs fewer people"),
    ("negative_impacts-dependency", "We will forget how to do it ourselves"),
    ("efficiency", "moves twice the tonnage"),
    ("efficiency", "drivers dispatched to the yard the moment a lorry is free"),
    ("key_sectors-transport", "Freight is where I notice it first"),
    ("key-sectors-water", "Municipal water boards will lean on forecasting engines"),
    ("applications-decision-making", "Rainfall models will set release schedules"),
    ("improvement-decision-making", "a real improvement in how that work is done"),
    ("safety-falls", "something watching for a fall"),
    ("saftey-falls", "nag them about the tablets they skip"),
)


def write_rows_csv(
    path: Path | str,
    rows: Iterable[Sequence[object]],
    *,
    encoding: str = "utf-8-sig",
) -> Path:
    """Write raw rows as CSV. The default encoding writes the byte-order mark."""
    path = Path(path)
    with path.open("w", encoding=encoding, newline="") as handle:
        writer = csv.writer(handle)
        for row in rows:
            writer.writerow(list(row))
    return path


def write_numbered_csv(
    path: Path | str,
    rows: Iterable[tuple[int, str]] = SAMPLE_NUMBERED,
    *,
    header: Sequence[str] | None = NUMBERED_CSV_HEADER,
    trimmed: Sequence[str] | None = None,
    encoding: str = "utf-8-sig",
) -> Path:
    """Write the ``All,,Trimmed`` corpus shape: ``NN. text`` beside the same text.

    `header` of ``None`` writes a headerless single column. A `header` of one name
    writes the numbered column alone. `trimmed` overrides the trimmed column cell by
    cell, which is how a disagreement between the two columns is staged.
    """
    rows = list(rows)
    overrides = list(trimmed) if trimmed is not None else None
    width = len(header) if header is not None else 1
    out: list[Sequence[object]] = []
    if header is not None:
        out.append(list(header))
    for index, (number, text) in enumerate(rows):
        numbered = f"{number}. {text}"
        if width >= 3:
            out.append([numbered, "", overrides[index] if overrides else text])
        elif width == 2:
            out.append([numbered, overrides[index] if overrides else text])
        else:
            out.append([numbered])
    return write_rows_csv(path, out, encoding=encoding)


def write_tagged_csv(
    path: Path | str,
    rows: Iterable[tuple[str, ...]] = SAMPLE_PAIRS,
    *,
    header: Sequence[str] = TAGGED_HEADER,
    encoding: str = "utf-8-sig",
) -> Path:
    """Write a code-text pairing export as CSV (``tag,content``, or the 4-column one)."""
    return write_rows_csv(path, [list(header), *(list(r) for r in rows)], encoding=encoding)


def write_tagged_xlsx(
    path: Path | str,
    rows: Iterable[tuple[str, ...]] = SAMPLE_PAIRS,
    *,
    header: Sequence[str] = TAGGED_HEADER,
    sheet_title: str = "codes",
) -> Path:
    """The same pairing export as a workbook, so both readers face the same content."""
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = sheet_title
    sheet.append(list(header))
    for row in rows:
        sheet.append(list(row))
    path = Path(path)
    workbook.save(path)
    return path


#: A codebook Markdown in the principal investigator's layout: five numbered sections,
#: descriptions under ``## 3.``, a ``###`` heading per top-level code, a bold line for
#: the parent, bullets for its subcodes, and one top-level leaf (``efficiency``) with
#: no bullets at all. The em dash is written as an escape so this file stays ASCII.
_EM = "\u2014"
DEFINITIONS_MD = f"""# Codebook

## 1. Tree Diagram

```
Codebook
```

## 2. Code and Subcode Listing

- `positive_impacts` {_EM} level 1 {_EM} parent {_EM} n=3

## 3. Descriptions

### positive_impacts  *(n=3)*

**positive_impacts** {_EM} Beneficial effects the respondent attributes to the technology.

- **positive_impacts > health** *(n=2)* {_EM} Better diagnosis, treatment or monitoring.
- **positive_impacts > general** *(n=1)* {_EM} Unspecified overall benefit.

### negative_impacts  *(n=3)*

**negative_impacts** {_EM} Harmful or undesirable effects the respondent attributes to it.

- **negative_impacts > job_destruction** *(n=2)* {_EM} Existing posts disappearing.
- **negative_impacts > dependency** *(n=1)* {_EM} Losing a skill the tool now performs.

### efficiency  *(n=2)*

**efficiency** {_EM} Doing the same work with less time, effort or cost. A top-level leaf.

### key_sectors  *(n=2)*

**key_sectors** {_EM} A named domain of activity the respondent expects to be reshaped.

- **key_sectors > transport** *(n=1)* {_EM} Moving people or goods.
- **key_sectors > water** *(n=1)* {_EM} Supply, storage and release of water.

### never_tagged  *(n=0)*

**never_tagged** {_EM} A code the descriptions define and the pairings never use.

## 4. Examples

## 5. Notes for the Researcher
"""


def write_definitions_md(path: Path | str, text: str = DEFINITIONS_MD) -> Path:
    """Write a codebook Markdown in the PI's layout. Returns the path."""
    path = Path(path)
    path.write_text(text, encoding="utf-8")
    return path
