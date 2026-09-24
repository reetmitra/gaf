"""In-test builders for the two spreadsheet shapes the pipeline ingests.

The real workbooks are human survey data and are gitignored, so the suite must be able
to construct its own. These builders write the *exact* header shapes the PI's files
use, including the header-name variation between his prompt versions ("No" vs
"Number"), so the ingest readers are tested against the variation rather than against
one tidy assumption.

Validation principle: **reliability** — the suite runs from a clean clone with no real
data present.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from pathlib import Path

from openpyxl import Workbook

__all__ = [
    "CODED_HEADER_VARIANTS",
    "NARRATIVE_STATE_HEADER",
    "SAMPLE_ROWS",
    "write_coded_xlsx",
    "write_narrative_state_xlsx",
]

#: The header of `NarrativeState(IndiaSample1-20).xlsx`, verbatim.
NARRATIVE_STATE_HEADER: tuple[str, str] = ("Number", "Response")

#: Header spellings a coded workbook may use; the PI's prompt versions disagree.
CODED_HEADER_VARIANTS: tuple[tuple[str, str, str], ...] = (
    ("No", "Response", "Code"),
    ("Number", "Response", "Code"),
)

#: Non-contiguous ids, as in the real file (which starts at 9 and skips).
SAMPLE_ROWS: tuple[tuple[int, str], ...] = (
    (9, "AI is likely to ease routine chores and reduce the effort needed for daily work."),
    (10, "Everyday life grows steadily richer because AI is used in every technical field."),
    (12, "AI leans on machine learning under the hood and it will keep improving."),
)


def write_narrative_state_xlsx(
    path: Path | str,
    rows: Iterable[tuple[int, str]] = SAMPLE_ROWS,
    header: Sequence[str] = NARRATIVE_STATE_HEADER,
    sheet_title: str = "Sheet1",
) -> Path:
    """Write a raw-response workbook: ``Number | Response``. Returns the path."""
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = sheet_title
    sheet.append(list(header))
    for number, response in rows:
        sheet.append([number, response])
    path = Path(path)
    workbook.save(path)
    return path


def write_coded_xlsx(
    path: Path | str,
    rows: Iterable[tuple[int, str, str]],
    header: Sequence[str] = CODED_HEADER_VARIANTS[0],
    sheet_title: str = "Sheet1",
) -> Path:
    """Write a hand-coding workbook: ``No | Response | Code``, one row per assignment.

    This is the shape the PI's golden set arrives in: the segment coded goes in the
    "Response" column, not the whole response.
    """
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = sheet_title
    sheet.append(list(header))
    for number, segment, code in rows:
        sheet.append([number, segment, code])
    path = Path(path)
    workbook.save(path)
    return path
