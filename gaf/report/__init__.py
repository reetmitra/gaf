"""Run report and the two HTML pages, all generated from the store.

Reading, not editing: the human gate is a CLI workflow. `codebook.html` exists so that
a methods reviewer can audit a codebook — code, description, family, evidence, the
findings attached to it — without opening a database. `views.html` is its shareable
counterpart: eleven views of the same dataset drawn from code names, family names,
response numbers, counts and scores, with **no respondent text anywhere in it**.

`gaf.report.svg` holds the chart primitives the views page's hand-written figures
share, so that a family keeps its colour from one figure to the next.

Validation principle: **transparency**.
"""

from __future__ import annotations

from gaf.report.html import render_codebook_html
from gaf.report.run_report import (
    CHECK_NOTES,
    RUN_JSON_NAME,
    RunArtefact,
    render_checks_section,
    render_run_report,
)
from gaf.report.timeline import (
    BatchSummary,
    BirthEvent,
    CheckpointMarker,
    CodeBiography,
    EvidencePoint,
    HandoverEvaluation,
    RenamedCode,
    SnapshotDiff,
    Timeline,
    TimelineStep,
    build_timeline,
    timeline_from_assignments,
    timeline_svg,
)
from gaf.report.trail import (
    EditedOperation,
    LineageRow,
    ReorganisationTrail,
    TrailEntry,
    build_trail,
)
from gaf.report.views import (
    TREE_MMD_NAME,
    VIEWS,
    VIEWS_HTML_NAME,
    ViewsData,
    codebook_mermaid,
    default_analysis_dir,
    growth_markdown,
    render_views_html,
    views_from_coding,
    views_from_run,
)

__all__ = [
    "CHECK_NOTES",
    "RUN_JSON_NAME",
    "TREE_MMD_NAME",
    "VIEWS",
    "VIEWS_HTML_NAME",
    "BatchSummary",
    "BirthEvent",
    "CheckpointMarker",
    "CodeBiography",
    "EditedOperation",
    "EvidencePoint",
    "HandoverEvaluation",
    "LineageRow",
    "RenamedCode",
    "ReorganisationTrail",
    "RunArtefact",
    "SnapshotDiff",
    "Timeline",
    "TimelineStep",
    "TrailEntry",
    "ViewsData",
    "build_timeline",
    "build_trail",
    "codebook_mermaid",
    "default_analysis_dir",
    "growth_markdown",
    "render_checks_section",
    "render_codebook_html",
    "render_run_report",
    "render_views_html",
    "timeline_from_assignments",
    "timeline_svg",
    "views_from_coding",
    "views_from_run",
]
