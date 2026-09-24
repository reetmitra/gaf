"""Reading the PI's spreadsheets and codebook documents into the pipeline's shapes.

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
from gaf.ingest.csv_corpus import read_numbered_csv, sniff_numbered_csv
from gaf.ingest.definitions import (
    DefinitionsMatch,
    DefinitionsReport,
    attach_definitions,
    read_definitions_md,
)
from gaf.ingest.tagged import (
    OrganisedCodebook,
    TaggedPair,
    organise_tagged,
    read_tagged_pairs,
    to_codebook,
)

# `repair_mojibake` is defined once, in `xlsx`; `corpus` imports it from there rather
# than redefining it, so this package re-exports that one copy.
from gaf.ingest.xlsx import (
    HighlightsReport,
    RawResponseRow,
    SpreadsheetFormatError,
    place_highlights,
    read_coded_xlsx,
    read_highlights_xlsx,
    read_narrative_state_xlsx,
    repair_mojibake,
)

__all__ = [
    "META_ENCODING_REPAIRED",
    "DefinitionsMatch",
    "DefinitionsReport",
    "HighlightsReport",
    "IngestReport",
    "OrganisedCodebook",
    "RawResponseRow",
    "SpreadsheetFormatError",
    "TaggedPair",
    "attach_definitions",
    "attach_question",
    "corpus_content_hash",
    "load_corpus",
    "load_corpus_with_report",
    "organise_tagged",
    "place_highlights",
    "read_coded_xlsx",
    "read_corpus_json",
    "read_definitions_md",
    "read_highlights_xlsx",
    "read_narrative_state_xlsx",
    "read_numbered_csv",
    "read_tagged_pairs",
    "repair_mojibake",
    "response_content_hash",
    "sniff_numbered_csv",
    "source_from_path",
    "to_codebook",
    "write_corpus_json",
]
