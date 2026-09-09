"""Canonical corpus assembly: a named file becomes content-hashed `Response` records.

The one thing this module exists to guarantee is that **the survey question travels
with every record**. The question is absent from the source spreadsheet, and a coder
that cannot see it cannot code the response in context, so it is attached here, once,
from `RunConfig.question_variant` (`gaf.config.QUESTION_VARIANTS`, default ``"v2"``).

`gaf/config.py` records an open item: which variant generated
``NarrativeState(IndiaSample1-20).xlsx`` is unconfirmed, and the counter-evidence
noted there has deliberately not been used to override the brief. This module does not
resolve that question -- it uses the configured value and records which variant it
used in the ingest report, so a later correction is a config change and a re-run
rather than an archaeology exercise.

Everything else here follows from that:

* `source` names the sample or wave (``"india_sample_1_20"``), derived from the file
  name so two waves cannot collide in the store's ``(response_id, source)`` key;
* a content hash is computed per response from the repaired text, so a record's
  identity is its content and re-ingesting the same file is a no-op in the store;
* encoding damage in the source is repaired at ingest by
  `gaf.ingest.xlsx.repair_mojibake`, and every repair is *reported* -- it appears in
  the record's `meta` and is counted in the `IngestReport`, because a silent
  correction of the PI's data would be exactly the kind of invisible transformation
  this project's transparency principle forbids;
* the corpus is deterministically ordered (by source, then response id) and JSON
  round-trips losslessly, so an ingest is replayable.

`Response.meta` holds respondent metadata (age, region, wave, ...) together with the
ingest provenance flags written here. **It is never passed to a model.** Metadata is
joined to the analysis only in the analysis tail, after coding is finished; nothing in
`gaf/agents/` or `gaf/pipeline/` may read it.

Validation principle: **transparency** -- ingestion is a documented, replayable
transformation from a named file to content-hashed records, including the two places
it changes what it was given (encoding repair, question attachment).
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from gaf.config import RunConfig
from gaf.ids import content_hash
from gaf.ingest.xlsx import RawResponseRow, read_narrative_state_xlsx, repair_mojibake
from gaf.models import Response

__all__ = [
    "JSON_SUFFIXES",
    "META_ENCODING_REPAIRED",
    "XLSX_SUFFIXES",
    "IngestReport",
    "attach_question",
    "corpus_content_hash",
    "load_corpus",
    "load_corpus_with_report",
    "read_corpus_json",
    "repair_mojibake",
    "response_content_hash",
    "source_from_path",
    "write_corpus_json",
]

#: Key set on `Response.meta` when `repair_mojibake` changed the source text.
META_ENCODING_REPAIRED = "encoding_repaired"
#: The number as written in the source file, when the file carries one inline.
META_SOURCE_NUMBER = "source_number"
#: Set on the k-th extra response that repeats an earlier source number.
META_DUPLICATE_OF_NUMBER = "duplicate_of_number"
META_DUPLICATE_ORDINAL = "duplicate_ordinal"

XLSX_SUFFIXES: tuple[str, ...] = (".xlsx", ".xlsm")
JSON_SUFFIXES: tuple[str, ...] = (".json",)

#: Splits a file stem into words: acronyms, CamelCase words, lowercase runs, digits.
_TOKEN_RE = re.compile(r"[A-Z]+(?![a-z])|[A-Z][a-z]*|[a-z]+|[0-9]+")
_PARENTHESISED_RE = re.compile(r"\(([^)]*)\)")


# --------------------------------------------------------------------------- #
# Ingest report
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class IngestReport:
    """What one ingest did, in a form the run report can print.

    Exists so that the two transformations ingest performs -- attaching a question and
    repairing encoding damage -- are countable facts rather than assumptions.
    """

    path: str
    source: str
    question_variant: str
    record_count: int
    repaired_response_ids: tuple[int, ...] = ()
    #: (number as written, id assigned) for every response that repeated an earlier
    #: number in a numbered single-column file. Empty for a headed workbook.
    duplicate_numbers: tuple[tuple[int, int], ...] = ()

    @property
    def repaired_count(self) -> int:
        return len(self.repaired_response_ids)

    def summary(self) -> str:
        """One line for the run report."""
        return (
            f"{self.record_count} responses from {self.source} "
            f"(question {self.question_variant}); "
            f"{self.repaired_count} of {self.record_count} required encoding repair"
            + (
                "; " + ", ".join(f"number {n} appears again -> id {i}" for n, i in self.duplicate_numbers)
                if self.duplicate_numbers
                else ""
            )
        )

    def to_json(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "source": self.source,
            "question_variant": self.question_variant,
            "record_count": self.record_count,
            "repaired_response_ids": list(self.repaired_response_ids),
            "duplicate_numbers": [list(pair) for pair in self.duplicate_numbers],
        }


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def source_from_path(path: Path | str) -> str:
    """Derive a sample/wave name from a file name.

    ``NarrativeState(IndiaSample1-20).xlsx`` -> ``india_sample_1_20``. The
    parenthesised part names the sample when there is one; otherwise the whole stem is
    used. The result is lowercase snake_case, which is what goes in the store's
    ``source`` column and what distinguishes one wave's response 9 from another's.
    """
    stem = Path(path).stem
    match = _PARENTHESISED_RE.search(stem)
    text = match.group(1) if match and match.group(1).strip() else stem
    tokens = _TOKEN_RE.findall(text)
    return "_".join(token.lower() for token in tokens) or "unknown"


def response_content_hash(response: Response) -> str:
    """Content hash of one response's text -- the same value the store writes."""
    return content_hash(response.content)


def corpus_content_hash(responses: Sequence[Response]) -> str:
    """Content hash of a whole corpus, over its canonical serialisation."""
    return content_hash(_corpus_json_str(responses))


def attach_question(responses: Iterable[Response], question: str) -> list[Response]:
    """Return copies of `responses` carrying `question`, order preserved.

    Used when a corpus is loaded from a source that does not know the question --
    which is all of them.
    """
    return [replace(response, question=question) for response in responses]


def _resolve_question(config: RunConfig | None, question: str | None) -> tuple[str, str]:
    """(question text, variant label). An explicit question is labelled ``custom``."""
    if question is not None:
        return question, "custom"
    resolved = config or RunConfig()
    return resolved.resolved_question(), resolved.question_variant


def _ordered(responses: Iterable[Response]) -> list[Response]:
    """Canonical corpus order: by source, then response id.

    A total order over content, not over insertion, so two ingests of the same file
    produce the same list whatever order the rows arrived in.
    """
    return sorted(responses, key=lambda r: (r.source, r.id))


def _corpus_json_str(responses: Sequence[Response]) -> str:
    return json.dumps(
        {"responses": [r.to_json() for r in _ordered(responses)]},
        sort_keys=True,
        ensure_ascii=False,
        indent=2,
    )


def _record_from_row(row: RawResponseRow, *, question: str, source: str) -> Response:
    meta: dict[str, Any] = {}
    if row.encoding_repaired:
        # Observable, not silent: the run report counts these and the audit trail can
        # name the responses whose bytes ingest altered.
        meta[META_ENCODING_REPAIRED] = True
    if row.source_number is not None:
        meta[META_SOURCE_NUMBER] = row.source_number
    if row.duplicate_ordinal:
        # Two responses numbered identically in the source file. Both are kept; the
        # later one has an offset id, and this records what the PI actually wrote.
        meta[META_DUPLICATE_OF_NUMBER] = row.source_number
        meta[META_DUPLICATE_ORDINAL] = row.duplicate_ordinal
    return Response(
        id=row.response_id, question=question, content=row.content, source=source, meta=meta
    )


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #


def load_corpus(
    path: Path | str,
    *,
    config: RunConfig | None = None,
    question: str | None = None,
    source: str | None = None,
) -> list[Response]:
    """Load a corpus from an xlsx or JSON path. **The** public entry point.

    Every returned record carries `id`, `question` and `content`; ids are the source
    file's own, so non-contiguous ids survive. Use `load_corpus_with_report` when the
    caller needs the ingest counts as well.
    """
    responses, _ = load_corpus_with_report(
        path, config=config, question=question, source=source
    )
    return responses


def load_corpus_with_report(
    path: Path | str,
    *,
    config: RunConfig | None = None,
    question: str | None = None,
    source: str | None = None,
) -> tuple[list[Response], IngestReport]:
    """`load_corpus`, plus the `IngestReport` describing what the ingest did."""
    path = Path(path)
    question_text, variant = _resolve_question(config, question)
    source_name = source or source_from_path(path)
    suffix = path.suffix.lower()
    if suffix in XLSX_SUFFIXES:
        records = _load_xlsx(path, question=question_text, source=source_name)
    elif suffix in JSON_SUFFIXES:
        records = read_corpus_json(
            path, config=config, question=question, source=source_name
        )
    else:
        raise ValueError(
            f"{path}: unsupported corpus format {suffix!r}; "
            f"expected one of {XLSX_SUFFIXES + JSON_SUFFIXES}"
        )
    ordered = _ordered(records)
    # A JSON corpus carries its own source per record; report what the records say
    # when they agree, and fall back to the name derived from the path when they do
    # not (a merged, multi-wave file).
    sources = {r.source for r in ordered}
    report = IngestReport(
        path=str(path),
        source=sources.pop() if len(sources) == 1 else source_name,
        question_variant=variant,
        record_count=len(ordered),
        repaired_response_ids=tuple(
            r.id for r in ordered if r.meta.get(META_ENCODING_REPAIRED)
        ),
        duplicate_numbers=tuple(
            (int(r.meta[META_DUPLICATE_OF_NUMBER]), r.id)
            for r in ordered
            if META_DUPLICATE_OF_NUMBER in r.meta
        ),
    )
    return ordered, report


def _load_xlsx(path: Path, *, question: str, source: str) -> list[Response]:
    """Read either workbook shape the PI's samples arrive in.

    The headed shape (`Number | Response`) is tried first. If its required columns are
    absent and the sheet is a single numbered column ("11. text ..."), that reader is
    used instead. Any other shape re-raises the original, named error — the reader
    never guesses a column by position.
    """
    from gaf.ingest.xlsx import (
        SpreadsheetFormatError,
        read_numbered_column_xlsx,
        sniff_numbered_column,
    )

    try:
        rows = read_narrative_state_xlsx(path)
    except SpreadsheetFormatError:
        if not sniff_numbered_column(path):
            raise
        rows = read_numbered_column_xlsx(path)
    return [_record_from_row(row, question=question, source=source) for row in rows]


def read_corpus_json(
    path: Path | str,
    *,
    config: RunConfig | None = None,
    question: str | None = None,
    source: str | None = None,
) -> list[Response]:
    """Read a corpus written by `write_corpus_json` (or a bare list of records).

    A record's own question and source are kept when it has them -- a written corpus
    is already a complete record. The configured question fills in only where a record
    has none, so a record can never reach a coder without one. An explicit `question`
    argument overrides every record, which is how a variant is switched after the fact.
    """
    path = Path(path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    rows = raw["responses"] if isinstance(raw, dict) else raw
    question_text, _ = _resolve_question(config, question)
    fallback_source = source or source_from_path(path)
    out: list[Response] = []
    for obj in rows:
        record = Response.from_json(obj)
        content = repair_mojibake(record.content)
        meta = dict(record.meta)
        if content != record.content:
            meta[META_ENCODING_REPAIRED] = True
        out.append(
            replace(
                record,
                content=content,
                meta=meta,
                question=question_text if (question is not None or not record.question) else record.question,
                source=record.source or fallback_source,
            )
        )
    return out


# --------------------------------------------------------------------------- #
# Writing
# --------------------------------------------------------------------------- #


def write_corpus_json(responses: Sequence[Response], path: Path | str) -> Path:
    """Write a corpus as canonical JSON and return the path.

    Sorted keys, source/id order, a trailing newline: two writes of the same corpus
    are byte-identical, which is what makes `corpus_content_hash` meaningful.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_corpus_json_str(responses) + "\n", encoding="utf-8")
    return path
