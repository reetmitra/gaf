"""Reading the PI's spreadsheets into the canonical corpus.

The survey question is absent from the source files and must be attached to every
record, because it travels with every coding call: a coder that cannot see the
question cannot code the response in context.

Validation principle: **transparency** — ingestion is a documented, replayable
transformation from a named file to content-hashed records, not a manual step.
"""

from __future__ import annotations

from gaf.ingest.corpus import (
    META_ENCODING_REPAIRED,
    IngestReport,
    attach_question,
    corpus_content_hash,
    load_corpus,
    load_corpus_with_report,
    read_corpus_json,
    response_content_hash,
    source_from_path,
    write_corpus_json,
)

# `repair_mojibake` is defined once, in `xlsx`; `corpus` imports it from there rather
# than redefining it, so this package re-exports that one copy.
from gaf.ingest.xlsx import (
    RawResponseRow,
    SpreadsheetFormatError,
    read_coded_xlsx,
    read_narrative_state_xlsx,
    repair_mojibake,
)

__all__ = [
    "META_ENCODING_REPAIRED",
    "IngestReport",
    "RawResponseRow",
    "SpreadsheetFormatError",
    "attach_question",
    "corpus_content_hash",
    "load_corpus",
    "load_corpus_with_report",
    "read_coded_xlsx",
    "read_corpus_json",
    "read_narrative_state_xlsx",
    "repair_mojibake",
    "response_content_hash",
    "source_from_path",
    "write_corpus_json",
]
