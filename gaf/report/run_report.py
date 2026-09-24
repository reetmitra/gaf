"""The run report — the plain-text account of one fast-loop run.

Rendered from :class:`gaf.pipeline.fast_loop.FastLoopResult`, or from the ``run.json``
the CLI writes beside it. **Nothing here recomputes a check.** Every check in the
system emits through ``CheckFinding`` / ``CheckReport``; this module renders those
findings and the run's own statistics, so that what a reader sees and what the audit
log holds cannot drift apart.

Two things the report is responsible for, both of them ADRs rather than taste.

**The caveats come first.** ADR-0019 established that M3's code-to-evidence fit does
not discriminate in the offline lexical space (median fit 0.000) and that M2's grey
zone is empty there; ADR-0022 measured the consequence — 84% of all model calls on the
real sample are M3 fit rulings. The M3 and M2 lines of an offline CHECKS table are
therefore artefacts of the stand-in embedder, not findings about the coding. A report
that printed 166 M3 warnings as substance would actively mislead the PI, so
``RunStats.caveats`` is printed above every number and the affected rows of the CHECKS
table are annotated where the reader's eye already is.

**The report is deterministic.** No wall-clock time is printed anywhere — not a
generation timestamp, not a duration — so two offline runs of the same corpus render
byte-identical text, exactly as ADR-0007 requires of the codebook itself. The only
numbers that could vary between two live runs are the ones the model provider reports
(tokens, cost, latency), and those are labelled as such.

Vocabulary is grounded theory's throughout (ADR-0005): codes, families, clusters,
themes, initial coding, constant comparison, theoretical saturation.

Validation principle: **transparency** — the run report and the audit log are the two
artefacts a methods reviewer reads instead of trusting a summary.
"""

from __future__ import annotations

import json
import textwrap
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from gaf.analysis.hca import SaturationCurve, saturation_curve
from gaf.analysis.matrix import build_matrix
from gaf.checks.contracts import CHECK_IDS, CheckReport
from gaf.checks.growth import GrowthCurve, code_growth, detect_spikes
from gaf.config import AnalysisConfig, CheckpointPolicy, CodingRules, RunConfig
from gaf.models import Assignment, Codebook, Response
from gaf.pipeline.decision_matrix import render_matrix_markdown
from gaf.pipeline.fast_loop import FastLoopResult, RunStats

__all__ = [
    "CHECK_ERROR_MEANS",
    "CHECK_NOTES",
    "DECISION_MATRIX_NAME",
    "RUN_ERROR_MEANS",
    "RUN_JSON_NAME",
    "RUN_SCHEMA",
    "RunArtefact",
    "render_checks_section",
    "render_run_report",
    "write_decision_matrix",
]

#: Version tag written into ``run.json`` so a later reader can refuse an older shape.
RUN_SCHEMA = "gaf.run/1"

#: The file the CLI writes and ``gaf report`` reads back.
RUN_JSON_NAME = "run.json"

#: The static decision matrix, written beside the run report. It is a page and a half
#: of table, which belongs in a file a reader can open rather than in the middle of a
#: report they are reading for this run's numbers.
DECISION_MATRIX_NAME = "decision_matrix.md"

#: One line per check id, so the CHECKS table explains itself to a reader who has not
#: read the source. Keys are exactly :data:`gaf.checks.contracts.CHECK_IDS`.
CHECK_NOTES: dict[str, str] = {
    "S1": "a candidate has a name, a description and at least one quote",
    "S2": "every quote really occurs in the response it cites (provenance)",
    "S2b": "a quote stays at the level of a phrase or a sentence",
    "S3": "the two-level name grammar, and sub-code before new top-level",
    "S4": "at most two codes on one piece of text",
    "S5": "the usual two to twelve codes per response",
    "S6": "codebook invariants: unique names, real parents, two levels",
    "M1": "cross-coder agreement, by Hungarian matching in one embedding space",
    "M2": "integration routing: merge, create, or ask the judge",
    "M3": "fit between a code and the quote offered as evidence for it",
    "M4": "near-duplicate leaves, and codebook-against-codebook comparison",
}

#: Checks whose offline behaviour is an artefact of the stand-in embedder (ADR-0019).
_OFFLINE_ARTEFACT_CHECKS: tuple[str, ...] = ("M2", "M3")

#: What an ERROR means to `gaf check`, whose question is "is this artefact valid?".
CHECK_ERROR_MEANS = (
    "The artefact is structurally invalid where they point, so this command exits 1. "
    "ERROR is reserved for structural certainty of invalidity; a WARN is a judgment "
    "about meaning and never fails a command."
)

#: What an ERROR means inside a run, whose question is "what did the checks find?".
RUN_ERROR_MEANS = (
    "In a run an ERROR is the check layer doing its job: a candidate whose quote is not "
    "in the corpus, or one whose every quote was ruled unnecessary, was dropped before "
    "it reached the codebook. That is the layer working, not the run failing. `gaf run` "
    "exits 0 whenever the run completes; only `gaf check` turns an ERROR into a "
    "non-zero exit, because only `gaf check` is asking whether an artefact is valid."
)

_WIDTH = 78
_INDENT = "  "

#: How much of a handover reason fits in the decision-matrix table before the report
#: stops being 78 columns wide. The full text is printed below the table for the
#: batches that came due, and `run.json` carries every one of them verbatim.
_REASON_WIDTH = 46

#: How many ERROR findings are printed in full before the tail is summarised.
_MAX_LISTED_ERRORS = 25


# --------------------------------------------------------------------------- #
# The artefact a report is rendered from
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class RunArtefact:
    """One run, in the shape both renderers read.

    Built either from a live :class:`FastLoopResult` or from the ``run.json`` the CLI
    wrote earlier, so that ``gaf run`` and ``gaf report`` render through one code path
    and cannot disagree. Everything it holds is already JSON-shaped or trivially
    serialisable; there is no reference to the store, the loop or a model client.
    """

    stats: RunStats
    codebook: Codebook
    assignments: list[Assignment]
    report: CheckReport
    snapshot_ids: list[str]
    provenance: dict[str, Any] = field(default_factory=dict)
    config: dict[str, Any] = field(default_factory=dict)
    outcomes: list[dict[str, Any]] = field(default_factory=list)

    # -- construction ----------------------------------------------------- #

    @classmethod
    def from_result(
        cls,
        result: FastLoopResult,
        *,
        config: RunConfig,
        provenance: dict[str, Any] | None = None,
    ) -> RunArtefact:
        return cls(
            stats=result.stats,
            codebook=result.codebook,
            assignments=list(result.assignments),
            report=result.report,
            snapshot_ids=list(result.snapshot_ids),
            provenance=dict(provenance or {}),
            config=config.to_json(),
            outcomes=[outcome.to_json() for outcome in result.outcomes],
        )

    @classmethod
    def from_json(cls, document: dict[str, Any]) -> RunArtefact:
        schema = str(document.get("schema", ""))
        if schema != RUN_SCHEMA:
            raise ValueError(
                f"unsupported run document schema {schema!r}; this build reads "
                f"{RUN_SCHEMA!r}. Re-run `gaf run` to regenerate {RUN_JSON_NAME}."
            )
        result = document["result"]
        return cls(
            stats=RunStats(**result["stats"]),
            codebook=Codebook.from_json(result["codebook"]),
            assignments=[Assignment.from_json(a) for a in result.get("assignments") or []],
            report=CheckReport.from_json(list(result.get("findings") or [])),
            snapshot_ids=[str(s) for s in result.get("snapshot_ids") or []],
            provenance=dict(document.get("provenance") or {}),
            config=dict(document.get("config") or {}),
            outcomes=list(result.get("responses") or []),
        )

    # -- serialisation ---------------------------------------------------- #

    def to_json(self) -> dict[str, Any]:
        return {
            "schema": RUN_SCHEMA,
            "provenance": dict(self.provenance),
            "config": dict(self.config),
            "result": {
                "run_id": self.stats.run_id,
                "codebook": self.codebook.to_json(),
                "assignments": [a.to_json() for a in self.assignments],
                "findings": self.report.to_json(),
                "snapshot_ids": list(self.snapshot_ids),
                "stats": self.stats.to_json(),
                "responses": list(self.outcomes),
            },
        }

    def to_json_str(self) -> str:
        return json.dumps(self.to_json(), sort_keys=True, ensure_ascii=False, indent=2)

    # -- derived ---------------------------------------------------------- #

    def analysis_config(self) -> AnalysisConfig:
        """The analysis settings this run used, or the defaults when unrecorded."""
        return _sub_config(self.config.get("analysis"), AnalysisConfig)

    def checkpoint_policy(self) -> CheckpointPolicy:
        """The checkpoint policy this run used, or the defaults when unrecorded."""
        raw = self.config.get("checkpoints")
        if isinstance(raw, dict) and isinstance(raw.get("fixed_cadence"), list):
            raw = {**raw, "fixed_cadence": tuple(raw["fixed_cadence"])}
        return _sub_config(raw, CheckpointPolicy)

    def run_config(self) -> RunConfig:
        """Enough of the run's configuration for the decision matrix's conditions.

        Only the parts a rendered condition names — the coding rules, the checkpoint
        policy, the batch size and the retrieval width. The full inverse of
        `RunConfig.to_json` lives in the CLI, where the store's byte-for-byte config
        comparison needs it; the report has no business importing the CLI, and a matrix
        condition has no business naming a model binding.
        """
        return RunConfig(
            run_id=self.stats.run_id,
            offline=self.stats.offline,
            rules=_sub_config(self.config.get("rules"), CodingRules),
            checkpoints=self.checkpoint_policy(),
            analysis=self.analysis_config(),
            batch_size=int(self.config.get("batch_size") or RunConfig().batch_size),
            retrieval_top_k=int(
                self.config.get("retrieval_top_k") or RunConfig().retrieval_top_k
            ),
        )

    def decision_trace(self) -> list[dict[str, Any]]:
        """The per-batch handover evaluations this run recorded, in batch order."""
        return [dict(row) for row in self.stats.decision_trace]

    def growth(self) -> GrowthCurve:
        """The code-growth curve over every response this run coded.

        Built in the run's own **processing order** — the order the outcomes are in,
        which is `(source, response id)` and not ascending id — because a growth curve
        cut on a different order is a curve of a run that did not happen.
        """
        order = [int(o["response_id"]) for o in self.outcomes if "response_id" in o]
        return code_growth(
            self.assignments,
            batch_size=int(self.config.get("batch_size") or RunConfig().batch_size),
            order=order or None,
            response_ids=order or None,
        )

    def spikes(self) -> list[dict[str, Any]]:
        """The spikes this run recorded, or — for a run.json written before the trace
        existed — the spikes its growth curve shows now.

        The trace is preferred because it is what the run *decided on*: the spike rule
        may have been re-tuned since, and a report that silently re-derived the spikes
        under today's policy would misreport why the gate came due.
        """
        trace = self.decision_trace()
        if trace:
            return [dict(row["spike"]) for row in trace if row.get("spike")]
        return [spike.to_json() for spike in detect_spikes(self.growth(), self.checkpoint_policy())]

    def saturation(self) -> SaturationCurve:
        """The saturation curve over every response this run coded.

        Built from the **unfiltered** matrix: the low-frequency filter removes exactly
        the rare codes whose first appearance is the interesting part of this curve.

        The row universe is every response the run *processed*, taken from the run's
        outcomes — not merely those that ended with an assignment. A response whose
        every candidate was dropped (an unverifiable quote, an UNNECESSARY fit ruling)
        still consumed a place in the batch, and omitting it silently re-cuts the
        batches and shifts the new-code counts. Theoretical saturation is a headline
        grounded-theory claim; it must describe the batches that actually ran.
        """
        analysis = self.analysis_config()
        unfiltered = replace(analysis, min_code_frequency=1, min_code_frequency_fraction=None)
        matrix = build_matrix(self.assignments, config=unfiltered, responses=self.coded_responses())
        return saturation_curve(matrix, config=analysis)

    def coded_responses(self) -> list[Response]:
        """Every response this run processed, as the row universe for the matrix.

        Reconstructed from the run outcomes rather than the corpus, so the report needs
        no second source of truth. Only the id is load-bearing here; the matrix uses it
        to fix the rows.
        """
        ids = sorted({int(o["response_id"]) for o in self.outcomes if "response_id" in o})
        return [Response(id=i, question="", content="", source="") for i in ids]


# --------------------------------------------------------------------------- #
# Small deterministic layout helpers
# --------------------------------------------------------------------------- #


def _sub_config(raw: Any, factory: Any) -> Any:
    """One sub-config from its JSON echo, unknown keys dropped, defaults otherwise.

    Unknown keys are dropped rather than raising so that a `run.json` written by a
    build that has since gained or lost a field still renders: a report that refused to
    open an older run would make the run directory unreadable by the only tool that
    reads it.
    """
    if not isinstance(raw, dict):
        return factory()
    known = set(factory.__dataclass_fields__)
    return factory(**{k: v for k, v in raw.items() if k in known})


def _heading(title: str) -> list[str]:
    return ["", title, "-" * len(title)]


def _field(label: str, value: Any, *, width: int = 22) -> str:
    return f"{_INDENT}{label.ljust(width)}{value}"


def _paragraph(text: str, *, indent: str = _INDENT) -> list[str]:
    return textwrap.wrap(
        text, width=_WIDTH, initial_indent=indent, subsequent_indent=indent
    ) or [indent.rstrip()]


def _clip(text: str, width: int) -> str:
    """One line, at most `width` characters, with an ellipsis where it was cut."""
    flat = " ".join(text.split())
    return flat if len(flat) <= width else flat[: width - 1].rstrip() + "…"


def _counts(mapping: dict[str, int]) -> str:
    """``{"a": 1, "b": 2}`` -> ``"a 1, b 2"``, in the mapping's own order."""
    return ", ".join(f"{key} {value}" for key, value in mapping.items()) or "none"


def _money(value: float) -> str:
    return f"${value:.4f}"


def _table(header: list[str], rows: list[list[str]], *, align_right: set[int]) -> list[str]:
    """A fixed-width table. Column widths come from the content, so output is stable."""
    widths = [len(cell) for cell in header]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    def render(cells: list[str]) -> str:
        parts = [
            cells[i].rjust(widths[i]) if i in align_right else cells[i].ljust(widths[i])
            for i in range(len(cells))
        ]
        return (_INDENT + "  ".join(parts)).rstrip()

    lines = [render(header), _INDENT + "  ".join("-" * w for w in widths)]
    lines.extend(render(row) for row in rows)
    return lines


# --------------------------------------------------------------------------- #
# The CHECKS section — shared with the standalone `gaf check` commands
# --------------------------------------------------------------------------- #


def render_checks_section(
    report: CheckReport,
    *,
    offline: bool = True,
    title: str = "CHECKS",
    max_listed_errors: int = _MAX_LISTED_ERRORS,
    error_means: str = CHECK_ERROR_MEANS,
) -> str:
    """Counts by check id x severity, the totals, the verdict, and every ERROR.

    The single renderer behind both the run report and the standalone `gaf check`
    commands, so "what the checks said" reads the same wherever a human meets it.
    ``offline`` annotates the rows ADR-0019 says are artefacts of the stand-in
    embedder rather than findings about the coding.

    ``error_means`` is the one thing the two callers must *not* share. The check
    commands answer "is this artefact valid?", so an ERROR there is a failure and the
    command exits 1. A run answers "what did the coders propose and what did the checks
    find?", so an ERROR there is the check layer dropping a candidate or a quote — the
    layer working — and the run still exits 0. Conflating the two would mean the
    pipeline could never be demonstrated on a corpus containing one unverifiable quote,
    which is every real corpus.
    """
    summary = report.summary()
    totals = report.totals()
    lines = _heading(title)
    lines.append("")
    lines.extend(
        _paragraph(
            "Every check in the pipeline emits through one contract, so this table is "
            "the whole of what the run observed. Counts are findings, not responses."
        )
    )
    lines.append("")

    order = [check for check in CHECK_IDS if check in summary]
    order += [check for check in sorted(summary) if check not in CHECK_IDS]

    rows: list[list[str]] = []
    for check in order:
        counts = summary[check]
        note = CHECK_NOTES.get(check, "")
        if offline and check in _OFFLINE_ARTEFACT_CHECKS:
            note = f"{note}  [offline artefact — see CAVEATS]" if note else "[offline artefact]"
        rows.append(
            [
                check,
                str(counts.get("ERROR", 0)),
                str(counts.get("WARN", 0)),
                str(counts.get("INFO", 0)),
                str(sum(counts.values())),
                note,
            ]
        )
    rows.append(
        [
            "TOTAL",
            str(totals["ERROR"]),
            str(totals["WARN"]),
            str(totals["INFO"]),
            str(len(report)),
            "",
        ]
    )
    if not order:
        rows.insert(0, ["(none)", "0", "0", "0", "0", "no check emitted a finding"])
    lines.extend(
        _table(
            ["check", "ERROR", "WARN", "INFO", "total", "what it checks"],
            rows,
            align_right={1, 2, 3, 4},
        )
    )

    lines.append("")
    if report.passed():
        lines.append(f"{_INDENT}RESULT: PASS — no ERROR finding.")
    else:
        lines.append(f"{_INDENT}RESULT: {totals['ERROR']} ERROR finding(s).")
        lines.append("")
        lines.extend(_paragraph(error_means, indent=_INDENT))

    errors = report.errors()
    if errors:
        lines.extend(["", f"{_INDENT}ERROR findings"])
        for finding in errors[:max_listed_errors]:
            lines.extend(_paragraph(str(finding), indent=_INDENT * 2))
        if len(errors) > max_listed_errors:
            lines.append(
                f"{_INDENT * 2}... and {len(errors) - max_listed_errors} more "
                "(all of them are in findings.json)."
            )

    warnings = report.warnings()
    if warnings:
        by_check: dict[str, int] = {}
        for finding in warnings:
            by_check[finding.check_id] = by_check.get(finding.check_id, 0) + 1
        lines.extend(["", f"{_INDENT}WARN findings by check: {_counts(by_check)}."])
        lines.extend(
            _paragraph(
                "A WARN is kept and flagged, never dropped: the structural layer does "
                "not make judgments about meaning. They are the slow loop's agenda.",
                indent=_INDENT * 2,
            )
        )
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Sections of the run report
# --------------------------------------------------------------------------- #


def _header(stats: RunStats) -> list[str]:
    mode = "offline (mock clients, lexical embedding fallback)" if stats.offline else "live"
    return [
        "=" * _WIDTH,
        f"GAF RUN REPORT — {stats.run_id}",
        "=" * _WIDTH,
        "",
        f"Grounded-theory coding run, {mode}.",
        f"Embedding space {stats.space_id}; {stats.n_responses} response(s) coded.",
    ]


def _seeded_caveat(seeded_from: Mapping[str, Any]) -> str:
    """What a seeded run costs, in the plainest words available (ADR-0035)."""
    return (
        f"This run was SEEDED from an existing codebook ({seeded_from.get('codes', 0)} "
        f"code(s), content hash {seeded_from.get('content_hash', '?')}). It coded into "
        "an organisation somebody had already built, so its agreement with the coding "
        "that produced that seed is NOT independent evidence about either of them: the "
        "machine was shown the shape of the answer before it started. A cold run — the "
        "same command with no --seed-codebook — is the validation path, and the "
        "agreement figures that belong in a methods appendix come from one of those. "
        "The seed's own evidence was held out of this run, so every number below "
        "describes this run's coding and no other."
    )


def _caveats(stats: RunStats, provenance: Mapping[str, Any] | None = None) -> list[str]:
    """Printed above every number, because ADR-0019 says a reader must meet it first."""
    recorded = list(stats.caveats)
    seeded_from = (provenance or {}).get("seeded_from")
    if isinstance(seeded_from, Mapping):
        recorded.insert(0, _seeded_caveat(seeded_from))
    lines = _heading("CAVEATS — read these before the numbers")
    lines.append("")
    if not recorded:
        lines.extend(
            _paragraph(
                "None recorded for this run. That is a claim about the run's inputs, "
                "not a guarantee about the coding."
            )
        )
        return lines
    for caveat in recorded:
        lines.extend(_paragraph(f"! {caveat}"))
        lines.append("")
    if stats.caveats:
        lines.extend(
            _paragraph(
                "In practice: treat the M3 and M2 rows of the CHECKS table as diagnostics "
                "of the stand-in embedder, not as findings about the codebook. The judge "
                "call counts below are dominated by the same effect (ADR-0022)."
            )
        )
    return lines


def _provenance(artefact: RunArtefact) -> list[str]:
    stats = artefact.stats
    provenance = artefact.provenance
    lines = _heading("PROVENANCE")
    lines.append("")
    lines.append(_field("run id", stats.run_id))
    for label, key in (
        ("corpus", "corpus_path"),
        ("corpus source", "corpus_source"),
        ("corpus hash", "corpus_content_hash"),
        ("question variant", "question_variant"),
        ("blackboard", "db_path"),
        ("output directory", "output_dir"),
        ("gaf version", "gaf_version"),
    ):
        if provenance.get(key) is not None:
            lines.append(_field(label, provenance[key]))
    lines.append(_field("responses ingested", provenance.get("n_responses", stats.n_responses)))
    lines.append(_field("embedding space", stats.space_id))
    seeded_from = provenance.get("seeded_from")
    if isinstance(seeded_from, Mapping):
        lines.append("")
        lines.append(_field("seeded from", seeded_from.get("path", "")))
        lines.append(_field("seed hash", seeded_from.get("content_hash", "")))
        lines.append(
            _field(
                "seed codes",
                f"{seeded_from.get('codes', 0)} in {seeded_from.get('families', 0)} "
                f"famil(ies), {seeded_from.get('described', 0)} described",
            )
        )
        lines.append(
            _field("seed evidence", f"{seeded_from.get('evidence_held_out', 0)} row(s) held out")
        )
        sources = seeded_from.get("sources") or []
        if sources:
            lines.append(_field("seed sources", ", ".join(str(s) for s in sources)))
    skipped_from = provenance.get("skipped_from")
    if isinstance(skipped_from, Mapping):
        lines.append("")
        lines.append(_field("resumed after", skipped_from.get("run", "")))
        lines.append(
            _field("responses skipped", f"{skipped_from.get('skipped', 0)} already coded there")
        )
    lines.append("")
    lines.append(
        f"{_INDENT}Snapshots frozen ({len(stats.snapshot_ids)}) — coders read these, "
        "only the slow loop writes them:"
    )
    for index, snapshot_id in enumerate(stats.snapshot_ids, start=1):
        lines.append(f"{_INDENT * 2}{index}. {snapshot_id}")
    return lines


def _configuration(artefact: RunArtefact) -> list[str]:
    config = artefact.config
    lines = _heading("CONFIGURATION — the thresholds this run actually used")
    lines.append("")
    if not config:
        lines.extend(_paragraph("Not recorded with this run."))
        return lines

    rules = config.get("rules") or {}
    lines.append(_field("offline", config.get("offline")))
    lines.append(_field("seed", config.get("seed")))
    lines.append(_field("batch size", config.get("batch_size")))
    lines.append(_field("snapshot policy", config.get("snapshot_policy")))
    lines.append(_field("retrieval top-k", config.get("retrieval_top_k")))
    lines.append(_field("question variant", config.get("question_variant")))
    lines.append(
        _field("human corrections", "recycled" if config.get("recycle_human_corrections") else "held out")
    )
    lines.append("")
    lines.append(
        f"{_INDENT}Similarity bands   tau_high {rules.get('tau_high')}  "
        f"tau_low {rules.get('tau_low')}  tau_fit {rules.get('tau_fit')}"
    )
    lines.append(
        f"{_INDENT}Quote provenance   fuzzy_threshold {rules.get('fuzzy_threshold')}"
    )
    lines.append(
        f"{_INDENT}Coding rules       codes/response "
        f"{rules.get('min_codes_per_response')}-{rules.get('max_codes_per_response')}; "
        f"codes/segment max {rules.get('max_codes_per_segment')}; "
        f"quote max {rules.get('max_quote_sentences')} sentence(s) / "
        f"{rules.get('max_quote_words')} words; hierarchy depth "
        f"{rules.get('hierarchy_depth')}"
    )

    models = config.get("models") or {}
    if models:
        lines.append("")
        lines.append(f"{_INDENT}Model bindings")
        for role in ("coder_a", "coder_b", "judge", "refactorer"):
            spec = models.get(role)
            if not isinstance(spec, dict):
                continue
            lines.append(
                f"{_INDENT * 2}{role.ljust(11)}{spec.get('provider')}/{spec.get('model')}"
                f"  temperature {spec.get('temperature')}"
            )

    analysis = config.get("analysis") or {}
    if analysis:
        lines.append("")
        lines.append(
            f"{_INDENT}Analysis tail      min_code_frequency "
            f"{analysis.get('min_code_frequency')}; fraction "
            f"{analysis.get('min_code_frequency_fraction')}; linkage "
            f"{analysis.get('linkage_method')}/{analysis.get('linkage_metric')}; "
            f"n_clusters {analysis.get('n_clusters')}"
        )
    return lines


def _coding(stats: RunStats) -> list[str]:
    proposed = sum(stats.candidates_proposed.values())
    survived = sum(stats.candidates_survived.values())
    lines = _heading("CODING — what the two coders proposed and what survived")
    lines.append("")
    lines.append(_field("responses coded", stats.n_responses))
    lines.append(_field("duplicate responses", stats.n_duplicate_responses))
    lines.append(_field("segments prepared", stats.n_segments))
    due = stats.checkpoint_due or {}
    if due.get("fires"):
        lines.append(_field("slow loop", f"DUE — {due.get('trigger', '?')}: {due.get('reason', '')}"))
        lines.append(_field("", "run `gaf checkpoint --run <dir> --interactive` to review the proposal"))
    else:
        lines.append(_field("slow loop", f"not due ({due.get('trigger', 'none')})"))
    lines.append("")
    lines.append(_field("candidates proposed", f"{proposed}  ({_counts(stats.candidates_proposed)})"))
    lines.append(_field("candidates survived", f"{survived}  ({_counts(stats.candidates_survived)})"))
    lines.append(_field("candidates dropped", _counts(stats.candidates_dropped)))
    lines.append(_field("candidates accepted", stats.candidates_accepted))
    lines.append(_field("acceptance by origin", _counts(stats.acceptance_by_origin)))
    lines.append("")
    lines.append(_field("agreement rate", f"{stats.agreement_rate:.4f}"))
    lines.append(_field("integration routes", _counts(stats.routes)))
    lines.append(_field("integration actions", _counts(stats.actions)))
    lines.append(_field("escalations", stats.escalations))
    lines.append(_field("judge calls", _counts(stats.judge_calls)))
    lines.append("")
    lines.extend(
        _paragraph(
            "The fast loop never restructures the codebook: MERGE attaches evidence to an "
            "existing code and CREATE admits a new one. Splitting, re-parenting and "
            "renaming happen only behind the human gate in the slow loop (ADR-0004)."
        )
    )
    return lines


def _model_calls(stats: RunStats) -> list[str]:
    llm = stats.llm
    lines = _heading("MODEL CALLS")
    lines.append("")
    lines.append(_field("calls", llm.get("calls", 0)))
    by_task = llm.get("by_task") or {}
    lines.append(_field("by task", _counts(dict(by_task))))
    lines.append(_field("cache hits", llm.get("cache_hits", 0)))
    lines.append(_field("fail-safe replies", llm.get("fail_safes", 0)))
    lines.append(
        _field(
            "tokens",
            f"{llm.get('input_tokens', 0)} in / {llm.get('output_tokens', 0)} out",
        )
    )
    lines.append(_field("cost (provider)", _money(float(llm.get("cost_usd", 0.0) or 0.0))))
    lines.append(_field("latency (provider)", f"{llm.get('latency_ms_total', 0.0)} ms"))
    lines.append("")
    lines.extend(
        _paragraph(
            "Cost and latency are reported by the provider and are the only figures in "
            "this report that two identical runs may differ on. They are zero offline."
        )
    )
    fit_calls = int((by_task or {}).get("judge_fit", 0))
    total_calls = int(llm.get("calls", 0) or 0)
    if stats.offline and total_calls and fit_calls:
        share = fit_calls / total_calls
        lines.append("")
        lines.extend(
            _paragraph(
                f"{fit_calls} of {total_calls} calls ({share:.0%}) are M3 fit rulings. "
                "ADR-0022 measured the same effect at 84% on the real sample: it is the "
                "stand-in embedder escalating, not the coding being ambiguous."
            )
        )
    return lines


def _codebook_section(artefact: RunArtefact) -> list[str]:
    stats = artefact.stats
    codebook = artefact.codebook
    lines = _heading("CODEBOOK")
    lines.append("")
    lines.append(_field("codes", stats.codes_final))
    lines.append(_field("codes created here", stats.codes_created))
    lines.append(_field("families", stats.families_final))
    lines.append(_field("assignments written", stats.assignments))
    lines.append("")

    per_code: dict[str, int] = {}
    for assignment in artefact.assignments:
        per_code[assignment.code] = per_code.get(assignment.code, 0) + 1

    rows: list[list[str]] = []
    for family, codes in codebook.families().items():
        quotes = sum(len(code.evidence) for code in codes)
        responses = sorted({e.response_id for code in codes for e in code.evidence if e.verified})
        rows.append([family, str(len(codes)), str(quotes), str(len(responses))])
    if rows:
        lines.extend(
            _table(
                ["family", "codes", "quotes", "responses"],
                rows,
                align_right={1, 2, 3},
            )
        )
    else:
        lines.append(f"{_INDENT}The codebook is empty — no candidate was admitted.")

    if codebook.codes:
        lines.append("")
        lines.append(f"{_INDENT}Codes, with the number of responses each is applied to:")
        for code in codebook.sorted_codes():
            count = per_code.get(code.name, len(code.response_ids()))
            lines.append(f"{_INDENT * 2}{code.name}  ({count})")
    return lines


def _saturation(artefact: RunArtefact) -> list[str]:
    lines = _heading("THEORETICAL SATURATION")
    lines.append("")
    curve = artefact.saturation()
    if not curve.points:
        lines.append(f"{_INDENT}No assignments — the curve has no batches.")
        return lines
    lines.append(
        f"{_INDENT}Batch size {curve.batch_size}; {curve.total_codes} distinct code(s) "
        "over the run."
    )
    lines.append("")
    rows = [
        [
            str(point.batch),
            str(point.responses_in_batch),
            str(point.cumulative_responses),
            str(point.new_codes),
            str(point.cumulative_codes),
        ]
        for point in curve.points
    ]
    lines.extend(
        _table(
            ["batch", "responses", "cumulative", "new codes", "codes so far"],
            rows,
            align_right={0, 1, 2, 3, 4},
        )
    )
    lines.append("")
    if curve.saturated_at_batch is None:
        lines.extend(
            _paragraph(
                "No batch was empty of new codes: the curve has not flattened, so "
                "theoretical saturation is not yet evidenced."
            )
        )
    else:
        lines.extend(
            _paragraph(
                f"First batch contributing no new code: batch {curve.saturated_at_batch}. "
                "Saturation is a claim about further sampling, so it is evidence and "
                "not a stopping rule on its own."
            )
        )
    return lines


def _decision_matrix(artefact: RunArtefact) -> list[str]:
    """The handover trace as a table, and the spikes the growth curve carries.

    This is the *run's* decisions, one row per batch boundary. The static matrix — every
    decision the system can take, under this run's thresholds — is a separate file,
    written by `write_decision_matrix`, because it says nothing about this run and a
    reader looking for it should not have to scroll past it every time they do not.
    """
    stats = artefact.stats
    lines = _heading("DECISION MATRIX — what each loop decided, and where")
    lines.append("")
    lines.extend(
        _paragraph(
            "The handover — 'is the slow loop due' — is evaluated at every batch "
            "boundary and never acted on by the fast loop, which does not block and "
            "does not restructure. One row per batch; the verdict is the trigger that "
            "won under the precedence health > spike > floor > cadence."
        )
    )
    lines.append("")

    trace = artefact.decision_trace()
    if not trace:
        lines.append(f"{_INDENT}No batch boundary was evaluated — the run coded no responses.")
        return lines

    rows = [
        [
            str(row.get("batch", "")),
            str(row.get("responses_coded", "")),
            str(row.get("new_codes", "")),
            str(row.get("near_duplicate_pairs", "")),
            "yes" if row.get("spike") else "-",
            str(row.get("verdict", "")),
            _clip(str(row.get("reason", "")), _REASON_WIDTH),
        ]
        for row in trace
    ]
    lines.extend(
        _table(
            [
                "batch",
                "responses",
                "new codes",
                "near-dup",
                "spike",
                "verdict",
                "reason",
            ],
            rows,
            align_right={0, 1, 2, 3},
        )
    )
    lines.append("")

    # The reasons are clipped in the table so the report keeps its width. The ones that
    # actually came due are printed in full here, because "why did the gate come due at
    # batch 4" is the question this section exists to answer; run.json carries every
    # reason verbatim for the rest.
    due = [row for row in trace if row.get("verdict") == "checkpoint_due"]
    if due:
        lines.append(f"{_INDENT}Why each batch came due, in full:")
        for row in due:
            lines.append(f"{_INDENT * 2}batch {row.get('batch')}:")
            lines.extend(_paragraph(str(row.get("reason", "")), indent=_INDENT * 3))
            held = [str(name) for name in row.get("held") or []]
            if held:
                lines.append(f"{_INDENT * 3}held: {', '.join(held)}")
        lines.append("")

    if stats.halted_at_batch is not None:
        lines.append(
            _field(
                "halted",
                f"after batch {stats.halted_at_batch}; {stats.responses_uncoded} "
                "response(s) left uncoded",
            )
        )
        lines.append(_field("", "the run still closed normally: checks, final snapshot, run_completed"))
        lines.append("")

    spikes = artefact.spikes()
    lines.append(f"{_INDENT}Code-growth spikes:")
    if not spikes:
        lines.append(f"{_INDENT * 2}None. No batch admitted codes far out of step with the ones before it.")
    else:
        for spike in spikes:
            ratio = spike.get("ratio")
            shape = f"{ratio}x" if ratio is not None else "no baseline"
            lines.append(
                f"{_INDENT * 2}batch {spike.get('batch')}: {spike.get('new_codes')} new "
                f"code(s), {shape}, rule `{spike.get('rule')}`"
            )
            lines.extend(_paragraph(str(spike.get("reason", "")), indent=_INDENT * 3))
    lines.append("")
    lines.extend(
        _paragraph(
            "The spike rule sits beside the absolute ceiling, not in place of it: an "
            "absolute ceiling cannot tell a first batch, where every code is new, from "
            "a late batch where the same count means the codebook has stopped "
            "converging. Its thresholds are uncalibrated (ADR-0033)."
        )
    )
    lines.append("")
    lines.extend(
        _paragraph(
            f"The full static matrix — every decision either loop can take, with this "
            f"run's thresholds — is written to {DECISION_MATRIX_NAME} beside this report."
        )
    )
    return lines


def write_decision_matrix(run_dir: Path, artefact: RunArtefact) -> Path:
    """Write the static decision matrix beside a run report; return the path.

    Exposed here rather than inlined into `gaf report` so that the renderer and the
    filename live with the rest of the report layer and the CLI only has to call it.
    Deterministic and self-contained: the same run directory and the same artefact
    write the same bytes, with no wall clock and no run id in the file.
    """
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / DECISION_MATRIX_NAME
    path.write_text(render_matrix_markdown(artefact.run_config()), encoding="utf-8")
    return path


# --------------------------------------------------------------------------- #
# The report
# --------------------------------------------------------------------------- #


def render_run_report(artefact: RunArtefact) -> str:
    """The whole run report as plain text. Pure, deterministic, no wall-clock."""
    stats = artefact.stats
    lines: list[str] = []
    lines.extend(_header(stats))
    lines.extend(_caveats(stats, artefact.provenance))
    lines.extend(_provenance(artefact))
    lines.extend(_configuration(artefact))
    lines.extend(_coding(stats))
    lines.extend(_model_calls(stats))
    lines.extend(_codebook_section(artefact))
    lines.extend(_saturation(artefact))
    lines.extend(_decision_matrix(artefact))
    lines.append("")
    lines.append(
        render_checks_section(
            artefact.report, offline=stats.offline, error_means=RUN_ERROR_MEANS
        )
    )
    lines.append("")
    lines.append("=" * _WIDTH)
    verdict = (
        "no ERROR finding"
        if artefact.report.passed()
        else f"{artefact.report.totals()['ERROR']} ERROR finding(s); the run completed"
    )
    lines.append(f"END OF REPORT — {verdict}.")
    lines.append("=" * _WIDTH)
    return "\n".join(lines) + "\n"
