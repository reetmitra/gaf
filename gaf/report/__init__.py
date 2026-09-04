"""Run report and the HTML codebook explorer, both generated from the store.

Reading, not editing: the human gate is a CLI workflow. The explorer exists so that a
methods reviewer can audit a codebook — code, description, family, evidence, the
findings attached to it — without opening a database.

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

__all__ = [
    "CHECK_NOTES",
    "RUN_JSON_NAME",
    "RunArtefact",
    "render_checks_section",
    "render_codebook_html",
    "render_run_report",
]
