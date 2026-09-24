"""`views.html` — eleven views of one coded dataset, in a single self-contained page.

PI note 10 asked for "multiple views on the dataset using more visualisations". Wave A
built those views as data — the growth curve, the patterns, the affinity groups, the
timeline, the reorganisation trail, the crosswalk. This module is where they become
something a person can look at: one HTML file per run, opened from a memory stick on a
machine with no network, carrying every figure inline.

**No respondent text, anywhere, ever.** This is the hard constraint the module is built
around, not a caveat appended to it. The page draws code names, family names, response
*numbers*, counts and scores, and nothing else. It never reads
`Assignment.segment`, never reads `Evidence.quote`, never reads `Response.content`, and
never prints a code description or a model's prose rationale — a description is written
by an agent that has just read a response, and the safe rule is the simple one. The
codebook explorer (`gaf.report.html`) is where quotes belong, because that page exists
to be audited against the corpus and is not a shareable artefact. This one is.

**Self-contained, like `codebook.html`.** Inline CSS, inline SVG, in-page anchors,
`<details>` for depth. No script, no network request, no external asset, no web font.
Figures written elsewhere in the project — the dendrogram, the saturation curve, the
timeline — are inlined with their stylesheets *scoped to the figure*, because an
inline `<svg>` in an HTML document leaks its own `<style>` rules into the whole page
and those renderers legitimately style bare `text` elements.

**Deterministic.** The same run directory produces byte-identical HTML: no timestamp,
no generated id, no dictionary iterated in insertion order, two decimal places on every
coordinate.

**A missing artefact is a sentence, not an error.** Each view that depends on something
`gaf analyse` or `gaf report` writes says, when that file is absent, exactly which
command creates it. A page built from half a run is still a page.

Vocabulary is grounded theory's throughout (ADR-0005): codes, families, clusters,
themes, constant comparison, saturation.

Validation principle: **transparency** — and, in the same breath, **interpretive
depth**: eleven views of one coding exist so that the reader can disagree with it.
"""

from __future__ import annotations

import html
import json
import re
import sqlite3
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from gaf.analysis.matrix import OccurrenceMatrix, build_matrix
from gaf.checks.growth import GrowthCurve, Spike, code_growth, detect_spikes
from gaf.config import AnalysisConfig, CheckpointPolicy, RunConfig
from gaf.models import Assignment, Codebook, Response, family_of, sub_of
from gaf.pipeline.decision_matrix import HANDOVER_RULES, matrix_to_json
from gaf.report import svg as g
from gaf.report.run_report import RunArtefact
from gaf.report.timeline import Timeline, build_timeline, timeline_from_assignments, timeline_svg
from gaf.report.trail import ReorganisationTrail, build_trail
from gaf.store.blackboard import Blackboard

__all__ = [
    "ANALYSIS_FILES",
    "TREE_MMD_NAME",
    "VIEWS",
    "VIEWS_HTML_NAME",
    "ViewsData",
    "codebook_mermaid",
    "default_analysis_dir",
    "growth_markdown",
    "render_views_html",
    "views_from_coding",
    "views_from_run",
]

#: The page this module writes.
VIEWS_HTML_NAME = "views.html"

#: The Mermaid codebook tree, written beside the page by the same command.
TREE_MMD_NAME = "tree.mmd"

#: The eleven views, in the order the brief fixes them, as ``(anchor, title)``.
VIEWS: tuple[tuple[str, str], ...] = (
    ("codebook-tree", "Codebook tree"),
    ("frequencies", "Code frequencies"),
    ("heatmap", "Response by code"),
    ("cooccurrence", "Co-occurrence"),
    ("patterns", "Pattern map"),
    ("affinity", "Affinity map"),
    ("growth", "Code growth and timeline"),
    ("handover", "Loop handover"),
    ("trail", "Reorganisation trail"),
    ("crosswalk", "Crosswalk"),
    ("clusters", "Clusters and saturation"),
)

#: The files `gaf analyse` writes that this page reads back, and what each one feeds.
ANALYSIS_FILES: tuple[str, ...] = (
    "patterns.json",
    "affinity.json",
    "crosswalk.json",
    "clusters.json",
    "saturation.json",
    "dendrogram.svg",
    "saturation.svg",
)

#: The conventional analysis directory inside a run directory.
_ANALYSIS_DIRNAME = "analysis"

_ANALYSE_CMD = "gaf analyse --assignments <assignments.json> --data <corpus.json> --out <dir>"
_REPORT_CMD = "gaf report --run <run dir>"
_RUN_CMD = "gaf run --corpus <corpus.json> --out <run dir>"

#: Mechanical caps, so a page over a large codebook stays a page.
_MAX_PATTERN_GROUPS = 40
_MAX_PAIRS = 30
_MAX_AFFINITY_GROUPS = 40
_MAX_CROSSWALK_ROWS = 40

_SLUG_RE = re.compile(r"[^a-z0-9]+")
_STYLE_RE = re.compile(r"<style>(.*?)</style>", re.DOTALL)
_XMLNS_RE = re.compile(r'\sxmlns(:[A-Za-z_][\w.-]*)?="[^"]*"')
_PROLOG_RE = re.compile(r"^\s*<\?xml[^>]*\?>\s*")


# --------------------------------------------------------------------------- #
# Escaping and identifiers
# --------------------------------------------------------------------------- #


def _e(value: Any) -> str:
    """Escape anything for HTML text or an attribute value. No exceptions."""
    return html.escape("" if value is None else str(value), quote=True)


def _slug(value: str) -> str:
    slug = _SLUG_RE.sub("-", value.casefold()).strip("-")
    return slug or "unnamed"


def _n(value: Any) -> str:
    """An integer for a table cell, or an em dash when the artefact recorded none."""
    return "—" if value is None else str(value)


def _float(value: Any) -> float:
    """A number for sorting by. A value that is not one sorts as zero, not as a crash.

    An artefact written by an older build, or truncated mid-write, is data this page
    reports; it is never a reason for the page to refuse to render.
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _round(value: Any, places: int = 3) -> str:
    """A score for a table cell, at fixed precision, or an em dash when absent."""
    if value is None:
        return "—"
    try:
        return f"{float(value):.{places}f}"
    except (TypeError, ValueError):  # a malformed artefact is data, not a crash
        return _e(value)


# --------------------------------------------------------------------------- #
# The page's whole input
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class ViewsData:
    """Everything `render_views_html` can draw, each piece independently optional.

    Built by :func:`views_from_run` or :func:`views_from_coding`. Every analysis is
    held in the JSON shape its own module publishes — the shapes T3 and T4 documented
    — rather than as live objects, so that the run path (read back from disk) and the
    bare-coding path (computed in process) reach exactly one renderer.

    The two exceptions are the occurrence matrix and the growth curve, which this
    module always builds itself. The heatmap must line up with the clustering, and the
    timeline's spike markers must key to the same batch numbering the timeline uses;
    reading either from a file written under a different batch size or a different
    filter would silently draw a picture of a different coding.
    """

    source_label: str
    run_id: str | None = None
    meta: tuple[tuple[str, str], ...] = ()
    caveats: tuple[str, ...] = ()
    codebook: Codebook | None = None
    assignments: tuple[Assignment, ...] = ()
    frequencies: dict[str, int] = field(default_factory=dict)
    matrix: OccurrenceMatrix | None = None
    filter_summary: str = ""
    batch_size: int = 10
    growth: GrowthCurve | None = None
    spikes: tuple[Spike, ...] = ()
    timeline: Timeline | None = None
    timeline_figure: str | None = None
    trail: ReorganisationTrail | None = None
    decision_trace: tuple[dict[str, Any], ...] = ()
    decision_matrix: dict[str, Any] | None = None
    clusters: dict[str, Any] | None = None
    saturation: dict[str, Any] | None = None
    dendrogram_figure: str | None = None
    saturation_figure: str | None = None
    patterns: dict[str, Any] | None = None
    affinity: dict[str, Any] | None = None
    crosswalk: dict[str, Any] | None = None
    has_descriptions: bool = False
    analysis_label: str = ""

    # -- derived ---------------------------------------------------------- #

    @property
    def families(self) -> tuple[str, ...]:
        """Every family the codebook or the coding names, sorted."""
        names = {family_of(name) for name in self.frequencies}
        if self.codebook is not None:
            names.update(self.codebook.families())
        return tuple(sorted(names))

    @property
    def palette(self) -> dict[str, int]:
        """Family -> colour slot, fixed for the whole page."""
        return g.family_palette(self.families)

    @property
    def n_responses(self) -> int:
        """Responses carrying at least one code.

        Not the corpus size and not the run's `n_responses`: a response the coders
        processed and produced nothing for still consumed a place in a batch, and the
        header's "responses coded" reports that number. This one is what the figures
        have rows for.
        """
        return len({row.response_id for row in self.assignments})

    def mermaid(self) -> str:
        """The codebook tree as Mermaid, or an empty string when there is no codebook."""
        if self.codebook is None or not self.codebook.codes:
            return ""
        return codebook_mermaid(self.codebook, self.frequencies)

    def available(self) -> dict[str, bool]:
        """Which of the eleven views this data can actually draw."""
        has_codes = bool(self.frequencies) or bool(self.codebook and self.codebook.codes)
        return {
            "codebook-tree": has_codes,
            "frequencies": has_codes,
            "heatmap": self.matrix is not None and not self.matrix.is_empty,
            "cooccurrence": self.patterns is not None,
            "patterns": self.patterns is not None,
            "affinity": self.affinity is not None,
            "growth": self.growth is not None,
            "handover": bool(self.decision_trace) or self.decision_matrix is not None,
            "trail": self.trail is not None,
            "crosswalk": self.crosswalk is not None,
            "clusters": self.clusters is not None or self.saturation is not None,
        }

    def to_json(self) -> dict[str, Any]:
        """A manifest: what this page is drawn from and which views it can draw.

        Not the data itself — that is already on disk in the artefacts this was built
        from. This is what a command prints to say what the reader will and will not
        find on the page.
        """
        return {
            "source": self.source_label,
            "run_id": self.run_id,
            "n_responses_with_a_code": self.n_responses,
            "n_codes": len(self.frequencies),
            "n_families": len(self.families),
            "n_assignments": len(self.assignments),
            "batch_size": self.batch_size,
            "views": {anchor: self.available()[anchor] for anchor, _ in VIEWS},
        }


# --------------------------------------------------------------------------- #
# Collecting — from a run, and from a bare human coding
# --------------------------------------------------------------------------- #


def _read_json(path: Path) -> dict[str, Any] | None:
    """One artefact, or None when it is absent or unreadable.

    Unreadable is treated as absent on purpose: the view then prints the command that
    writes the file, which is exactly the advice a reader with a truncated artefact
    needs. A page is not the place to raise on a half-written analysis directory.
    """
    if not path.exists():
        return None
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return loaded if isinstance(loaded, dict) else None


def _read_text(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _analysis_artefacts(analysis_dir: Path | None) -> dict[str, Any]:
    """Whatever `gaf analyse` left behind, keyed by the field that consumes it."""
    if analysis_dir is None or not analysis_dir.is_dir():
        return {}
    return {
        "patterns": _read_json(analysis_dir / "patterns.json"),
        "affinity": _read_json(analysis_dir / "affinity.json"),
        "crosswalk": _read_json(analysis_dir / "crosswalk.json"),
        "clusters": _read_json(analysis_dir / "clusters.json"),
        "saturation": _read_json(analysis_dir / "saturation.json"),
        "dendrogram_svg": _read_text(analysis_dir / "dendrogram.svg"),
        "saturation_svg": _read_text(analysis_dir / "saturation.svg"),
    }


def default_analysis_dir(run_dir: Path) -> Path | None:
    """`<run>/analysis` when it exists — the layout `make analyse` already uses."""
    candidate = run_dir / _ANALYSIS_DIRNAME
    return candidate if candidate.is_dir() else None


def _matrices(
    assignments: Sequence[Assignment],
    responses: Sequence[Response] | None,
    analysis: AnalysisConfig,
) -> tuple[OccurrenceMatrix | None, dict[str, int], str]:
    """The filtered matrix for the heatmap, and unfiltered frequencies for the bars.

    The heatmap has to agree with the clustering, which runs on the filtered matrix.
    The tree and the frequency bars must not: the low-frequency filter removes exactly
    the codes a reader is looking for when asking "what did this coding produce?", so
    those two views count on the unfiltered matrix and the page states the filter.
    """
    if not assignments:
        return None, {}, ""
    unfiltered_config = AnalysisConfig(
        **{**analysis.to_json(), "min_code_frequency": 1, "min_code_frequency_fraction": None}
    )
    try:
        unfiltered = build_matrix(assignments, config=unfiltered_config, responses=responses)
        filtered = build_matrix(assignments, config=analysis, responses=responses)
    except ValueError:  # nothing coded yet: a legitimate state, not a failure
        return None, {}, ""
    return filtered, dict(unfiltered.frequencies()), filtered.filter.summary()


def _growth_and_spikes(
    assignments: Sequence[Assignment],
    *,
    batch_size: int,
    policy: CheckpointPolicy,
    order: Sequence[int] | None = None,
) -> tuple[GrowthCurve | None, tuple[Spike, ...]]:
    if not assignments:
        return None, ()
    curve = code_growth(
        assignments,
        batch_size=batch_size,
        order=list(order) if order else None,
        response_ids=list(order) if order else None,
    )
    return curve, tuple(detect_spikes(curve, policy))


def _spike_markers(spikes: Sequence[Spike]) -> tuple[tuple[int, str], ...]:
    """`timeline_svg`'s `markers`, keyed by real (1-based) batch number.

    T4's `markers` parameter keys off `BatchSummary.batch`, not a position in the
    batches list, and T2's `Spike.batch` is the same 1-based number the growth curve,
    the saturation table and the `checkpoint_evaluated` event all use. They join
    directly; nothing here converts an index.
    """
    return tuple((spike.batch, f"spike: {spike.new_codes} new") for spike in spikes)


def _store_views(
    run_dir: Path, run_id: str
) -> tuple[Timeline | None, ReorganisationTrail | None]:
    """The timeline and the reorganisation trail, read out of the run's own store.

    Both need the audit log, which only a run has. A missing, foreign or unreadable
    `gaf.sqlite` yields ``(None, None)`` and the two views say which command writes
    them — a page must not fail because a run directory was copied without its store.
    """
    database = run_dir / "gaf.sqlite"
    if not database.exists():
        return None, None
    try:
        with Blackboard(database) as board:
            return build_timeline(board, run_id), build_trail(board, run_id)
    except (sqlite3.Error, KeyError, TypeError, ValueError):
        return None, None


def views_from_run(
    artefact: RunArtefact,
    run_dir: Path,
    *,
    analysis_dir: Path | None = None,
) -> ViewsData:
    """Everything the page can draw for one finished run.

    `analysis_dir` defaults to `<run_dir>/analysis`, the layout `make analyse` already
    writes; pass it explicitly to read an analysis written elsewhere.
    """
    stats = artefact.stats
    resolved = analysis_dir if analysis_dir is not None else default_analysis_dir(run_dir)
    found = _analysis_artefacts(resolved)

    analysis = artefact.analysis_config()
    matrix, frequencies, filter_summary = _matrices(
        artefact.assignments, artefact.coded_responses(), analysis
    )
    batch_size = int(artefact.config.get("batch_size") or RunConfig().batch_size)
    order = [int(o["response_id"]) for o in artefact.outcomes if "response_id" in o]
    curve, spikes = _growth_and_spikes(
        artefact.assignments,
        batch_size=batch_size,
        policy=artefact.checkpoint_policy(),
        order=order or None,
    )
    timeline, trail = _store_views(run_dir, stats.run_id)

    meta: list[tuple[str, str]] = [
        ("responses coded", str(stats.n_responses)),
        ("codes", str(len(artefact.codebook))),
        ("families", str(len(artefact.codebook.families()))),
        ("assignment rows", str(len(artefact.assignments))),
        ("embedding space", stats.space_id),
        ("snapshot", stats.snapshot_ids[-1] if stats.snapshot_ids else "none"),
        ("mode", "offline" if stats.offline else "live"),
        ("seed", str(artefact.config.get("seed", RunConfig().seed))),
        ("batch size", str(batch_size)),
    ]
    return _assemble(
        source_label=f"run {stats.run_id}",
        run_id=stats.run_id,
        meta=tuple(meta),
        caveats=tuple(stats.caveats),
        codebook=artefact.codebook,
        assignments=tuple(artefact.assignments),
        frequencies=frequencies,
        matrix=matrix,
        filter_summary=filter_summary,
        batch_size=batch_size,
        growth=curve,
        spikes=spikes,
        timeline=timeline,
        trail=trail,
        decision_trace=tuple(artefact.decision_trace()),
        decision_matrix=matrix_to_json(artefact.run_config()),
        analysis_label=str(resolved) if resolved is not None else "",
        found=found,
    )


def views_from_coding(
    assignments: Sequence[Assignment],
    *,
    codebook: Codebook | None = None,
    responses: Sequence[Response] | None = None,
    analysis: AnalysisConfig | None = None,
    policy: CheckpointPolicy | None = None,
    batch_size: int = 10,
    source_label: str = "human coding",
    analysis_dir: Path | None = None,
) -> ViewsData:
    """Everything the page can draw for a coding with no run behind it.

    A hand coding carries no audit log, so the two views that read one — the decision
    trace and the reorganisation trail — say so rather than being drawn from a guess.
    Everything else is available: the timeline comes from `timeline_from_assignments`,
    and the analyses come from an `--analysis` directory when one is supplied.
    """
    analysis = analysis or AnalysisConfig()
    policy = policy or CheckpointPolicy()
    found = _analysis_artefacts(analysis_dir)
    matrix, frequencies, filter_summary = _matrices(assignments, responses, analysis)
    curve, spikes = _growth_and_spikes(assignments, batch_size=batch_size, policy=policy)
    timeline = timeline_from_assignments(list(assignments), batch_size=batch_size) if assignments else None

    n_families = len({family_of(name) for name in frequencies})
    if codebook is not None:
        n_families = len(codebook.families())
    meta: list[tuple[str, str]] = [
        ("responses coded", str(len({row.response_id for row in assignments}))),
        ("codes", str(len(codebook) if codebook is not None else len(frequencies))),
        ("families", str(n_families)),
        ("assignment rows", str(len(assignments))),
        ("batch size", str(batch_size)),
        ("audit log", "none — this is a coding, not a run"),
    ]
    return _assemble(
        source_label=source_label,
        run_id=None,
        meta=tuple(meta),
        caveats=(),
        codebook=codebook,
        assignments=tuple(assignments),
        frequencies=frequencies,
        matrix=matrix,
        filter_summary=filter_summary,
        batch_size=batch_size,
        growth=curve,
        spikes=spikes,
        timeline=timeline,
        trail=None,
        decision_trace=(),
        decision_matrix=None,
        analysis_label=str(analysis_dir) if analysis_dir is not None else "",
        found=found,
    )


def _assemble(*, found: Mapping[str, Any], **kwargs: Any) -> ViewsData:
    """One constructor for both collectors, so the two paths cannot drift."""
    codebook: Codebook | None = kwargs.get("codebook")
    data = ViewsData(
        **kwargs,
        has_descriptions=bool(
            codebook is not None
            and any(code.description.strip() for code in codebook.codes.values())
        ),
        patterns=found.get("patterns"),
        affinity=found.get("affinity"),
        crosswalk=found.get("crosswalk"),
        clusters=found.get("clusters"),
        saturation=found.get("saturation"),
    )
    # The timeline figure is drawn here rather than in the renderer because it needs
    # the spike markers, and the markers must key to the very batch numbering the
    # timeline object carries — which only the assembled data knows.
    timeline_figure: str | None = None
    if data.timeline is not None:
        timeline_figure = timeline_svg(
            data.timeline,
            title=f"Timeline of code generation and change — {data.source_label}",
            markers=list(_spike_markers(data.spikes)),
        )
    return replace(
        data,
        dendrogram_figure=found.get("dendrogram_svg"),
        saturation_figure=found.get("saturation_svg"),
        timeline_figure=timeline_figure,
    )


# --------------------------------------------------------------------------- #
# The Mermaid tree, and the growth table as Markdown
# --------------------------------------------------------------------------- #


def _mermaid_label(value: str) -> str:
    """A Mermaid node label: quotation marks are the one character that breaks it."""
    return value.replace('"', "#quot;")


def codebook_mermaid(codebook: Codebook, frequencies: Mapping[str, int]) -> str:
    """The codebook as a Mermaid ``flowchart LR``: names and counts, never a quote.

    The same shape `gaf.ingest.tagged.OrganisedCodebook.to_mermaid` renders for a hand
    coding, built here from a `Codebook` so that a run's own codebook reaches the same
    picture. Node ids are positional in sorted order, so the file is deterministic.
    """
    families = codebook.families()
    lines = ["flowchart LR", '  ROOT(["Codebook"]):::root']
    for f_index, (family, codes) in enumerate(sorted(families.items()), start=1):
        parent_id = f"P{f_index}"
        total = sum(int(frequencies.get(code.name, 0)) for code in codes)
        lines.append(f'  {parent_id}["{_mermaid_label(family)}<br/>n={total}"]:::parent')
        lines.append(f"  ROOT --> {parent_id}")
        leaves = [code for code in codes if sub_of(code.name)]
        for l_index, code in enumerate(sorted(leaves, key=lambda c: c.name), start=1):
            leaf_id = f"{parent_id}L{l_index}"
            count = int(frequencies.get(code.name, 0))
            label = _mermaid_label(sub_of(code.name))
            lines.append(f'  {leaf_id}["{label}<br/>n={count}"]:::leaf')
            lines.append(f"  {parent_id} --> {leaf_id}")
    lines.append("  classDef root fill:#1b1b1b,color:#ffffff,stroke:#1b1b1b")
    lines.append("  classDef parent fill:#29506d,color:#ffffff,stroke:#29506d")
    lines.append("  classDef leaf fill:#f2efe9,color:#1b1b1b,stroke:#d8d5cf")
    return "\n".join(lines) + "\n"


def growth_markdown(curve: GrowthCurve, spikes: Sequence[Spike]) -> str:
    """The code-growth curve and its spikes as Markdown. Counts only, no text."""
    saturated = (
        f"batch {curve.saturated_at_batch}"
        if curve.saturated_at_batch is not None
        else "not reached"
    )
    lines = [
        "## Code growth",
        "",
        f"Source `{curve.source}`; batch size {curve.batch_size}; "
        f"{curve.total_codes} distinct code(s) in total. "
        f"First batch that admitted nothing new: {saturated}.",
        "",
        "Batch numbers are 1-based, as everywhere else in this build.",
        "",
        "| batch | responses | cumulative responses | new codes | cumulative codes "
        "| new codes per response | spike |",
        "|---:|---:|---:|---:|---:|---:|:--|",
    ]
    spiked = {spike.batch: spike for spike in spikes}
    for point in curve.points:
        spike = spiked.get(point.batch)
        mark = f"yes ({spike.rule})" if spike is not None else "-"
        lines.append(
            f"| {point.batch} | {point.responses_in_batch} | {point.cumulative_responses} "
            f"| {point.new_codes} | {point.cumulative_codes} "
            f"| {point.new_codes_per_response:.3f} | {mark} |"
        )
    lines.extend(["", "### Spikes", ""])
    if not spikes:
        lines.append("_No batch met the spike rule._")
    else:
        for spike in spikes:
            ratio = "no baseline" if spike.ratio is None else f"{spike.ratio:.2f}x the baseline"
            lines.append(
                f"- **batch {spike.batch}** — {spike.new_codes} new code(s), {ratio}, "
                f"rule `{spike.rule}`, window {spike.window}. {spike.reason}"
            )
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
# Inlining a figure this module did not write
# --------------------------------------------------------------------------- #


def _scope_css(css: str, prefix: str) -> str:
    """Prefix every selector in a flat stylesheet, so it cannot reach the whole page.

    The renderers in `gaf.analysis.hca` and `gaf.report.timeline` write a flat list of
    ``selector{declarations}`` rules, including bare element selectors like ``text``.
    Inlined into HTML, those apply document-wide. Prefixing each selector with the
    figure's own id confines them.

    A stylesheet carrying an at-rule (``@media``, ``@font-face``) cannot be scoped by
    this simple pass, and is returned unchanged rather than mangled — a nested block
    would be cut in the wrong place. No renderer in this project writes one, and a
    test asserts that; this branch exists so that the day one does, the figure still
    renders and the leak is a styling bug rather than a corrupted page.
    """
    if "@" in css:
        return css.strip()
    rules: list[str] = []
    for chunk in css.split("}"):
        selectors, brace, declarations = chunk.partition("{")
        if not brace:
            continue
        scoped = ", ".join(
            f"{prefix} {selector.strip()}" for selector in selectors.split(",") if selector.strip()
        )
        if scoped:
            rules.append(f"{scoped} {{{declarations.strip()}}}")
    return "\n".join(rules)


def _inline_figure(svg_text: str, *, figure_id: str) -> tuple[str, str]:
    """``(scoped css, svg markup)`` for a standalone SVG file, ready to inline.

    Three things are removed: the XML prolog (meaningless inside HTML), every
    ``xmlns`` declaration (implied for inline SVG, and the only reason a namespace
    URL would appear in a page that makes no network request), and the ``<style>``
    element, whose rules are returned separately for the page's own stylesheet.
    """
    body = _PROLOG_RE.sub("", svg_text).strip()
    blocks = _STYLE_RE.findall(body)
    body = _XMLNS_RE.sub("", _STYLE_RE.sub("", body))
    css = "\n".join(_scope_css(block, f"#{figure_id}") for block in blocks if block.strip())
    return css, body


# --------------------------------------------------------------------------- #
# Page furniture
# --------------------------------------------------------------------------- #


def _missing(what: str, command: str) -> str:
    return (
        f'<p class="missing"><strong>Not on this page.</strong> {_e(what)} '
        f'Run <code>{_e(command)}</code> and build the page again.</p>'
    )


def _how(sentence: str) -> str:
    return f'<p class="how"><strong>How to read this.</strong> {_e(sentence)}</p>'


def _note(sentence: str) -> str:
    return f'<p class="note">{_e(sentence)}</p>'


def _swatch(slot: int, family: str) -> str:
    return (
        f'<span class="v-swatch v-f{slot}" aria-hidden="true"></span> '
        f'<span class="fam">{_e(family)}</span>'
    )


def _table(headers: Sequence[tuple[str, bool]], rows: Sequence[Sequence[str]]) -> list[str]:
    """One HTML table. `headers` is ``(label, numeric)``; cells are pre-escaped."""
    head = "".join(
        f'<th class="num">{_e(label)}</th>' if numeric else f"<th>{_e(label)}</th>"
        for label, numeric in headers
    )
    out = [f'<div class="wrap"><table><thead><tr>{head}</tr></thead><tbody>']
    for row in rows:
        cells = "".join(
            f'<td class="num">{cell}</td>' if numeric else f"<td>{cell}</td>"
            for cell, (_, numeric) in zip(row, headers, strict=False)
        )
        out.append(f"<tr>{cells}</tr>")
    if not rows:
        out.append(f'<tr><td colspan="{len(headers)}" class="empty">Nothing to show.</td></tr>')
    out.append("</tbody></table></div>")
    return out


# --------------------------------------------------------------------------- #
# View 1 — the codebook tree as an icicle
# --------------------------------------------------------------------------- #


def _leaf_rows(data: ViewsData) -> list[tuple[str, str, int]]:
    """``(family, leaf name, frequency)`` for every leaf, family then frequency."""
    names: set[str] = set(data.frequencies)
    if data.codebook is not None:
        names.update(code.name for code in data.codebook.leaves())
    rows = [(family_of(name), name, int(data.frequencies.get(name, 0))) for name in sorted(names)]
    rows.sort(key=lambda r: (r[0], -r[2], r[1]))
    return rows


def _view_codebook_tree(data: ViewsData) -> list[str]:
    rows = _leaf_rows(data)
    if not rows:
        return [_missing("No codebook or coding was supplied.", _RUN_CMD)]
    palette = data.palette
    total = sum(freq for _, _, freq in rows) or 1
    unit = min(18.0, max(2.0, 620.0 / total))
    min_h = 4.0

    width, left_w, gap = 900.0, 210.0, 6.0
    heights = [max(min_h, freq * unit) for _, _, freq in rows]
    height = sum(heights) + 34.0
    body: list[str] = [
        g.text(0, 12, "family", cls="v-tick"),
        g.text(left_w + gap, 12, "leaf code — band height is the number of responses", cls="v-tick"),
    ]

    y = 22.0
    family_start: dict[str, tuple[float, float, int, int]] = {}
    for (family, name, freq), band_h in zip(rows, heights, strict=True):
        slot = palette.get(family, 0)
        start, extent, count, freq_sum = family_start.get(family, (y, 0.0, 0, 0))
        family_start[family] = (start, extent + band_h, count + 1, freq_sum + freq)
        label = sub_of(name) or name
        body.append(
            g.rect(
                left_w + gap,
                y,
                width - left_w - gap,
                max(1.0, band_h - 1.0),
                cls=f"v-f{slot}",
                opacity="0.55",
                tooltip=f"{name} — {freq} response(s)",
            )
        )
        if band_h >= 9.0:
            body.append(
                g.text(
                    left_w + gap + 5,
                    y + band_h / 2.0 + 3.0,
                    f"{g.truncate(label, 58)}  ({freq})",
                    cls="v-lbl",
                    tooltip=f"{name} — {freq} response(s)",
                )
            )
        y += band_h

    for family, (start, extent, count, freq_sum) in sorted(family_start.items()):
        slot = palette.get(family, 0)
        body.append(
            g.rect(
                0,
                start,
                left_w,
                max(1.0, extent - 1.0),
                cls=f"v-f{slot}",
                tooltip=f"{family} — {count} leaf code(s), {freq_sum} response(s)",
            )
        )
        if extent >= 11.0:
            body.append(
                g.text(
                    6,
                    start + extent / 2.0 + 3.0,
                    f"{g.truncate(family, 24)} ({count})",
                    cls="v-lbl",
                    tooltip=f"{family} — {count} leaf code(s), {freq_sum} response(s)",
                )
            )

    out = [
        '<div class="scroll">',
        g.figure(width, height, body, label="Codebook tree, families and their leaf codes"),
        "</div>",
    ]
    out.append(
        '<details><summary>Every family and leaf, as text</summary>'
        '<ul class="tree">'
    )
    current = ""
    for family, name, freq in rows:
        if family != current:
            if current:
                out.append("</ul></li>")
            slot = palette.get(family, 0)
            out.append(f'<li>{_swatch(slot, family)}<ul>')
            current = family
        out.append(f'<li><span class="mono">{_e(sub_of(name) or name)}</span> — {freq}</li>')
    if current:
        out.append("</ul></li>")
    out.append("</ul></details>")

    mermaid = data.mermaid()
    if mermaid:
        out.append(
            f'<p>The same tree as Mermaid: <a href="{_e(TREE_MMD_NAME)}"><code>'
            f"{_e(TREE_MMD_NAME)}</code></a>, written beside this page.</p>"
        )
        out.append(
            "<details><summary>The Mermaid source, inline</summary>"
            f"<pre class=\"mono\">{_e(mermaid)}</pre></details>"
        )
    return out


# --------------------------------------------------------------------------- #
# View 2 — code frequencies
# --------------------------------------------------------------------------- #


def _view_frequencies(data: ViewsData) -> list[str]:
    rows = _leaf_rows(data)
    if not rows:
        return [_missing("No codebook or coding was supplied.", _RUN_CMD)]
    palette = data.palette
    top = max((freq for _, _, freq in rows), default=1) or 1

    width, label_w, right_w = 900.0, 300.0, 56.0
    row_h, header_h = 14.0, 19.0
    families = sorted({family for family, _, _ in rows})
    height = 26.0 + len(families) * header_h + len(rows) * row_h
    bars = g.scale((0.0, float(top)), (0.0, width - label_w - right_w))

    body: list[str] = [g.text(0, 12, "responses carrying each code", cls="v-tick")]
    y = 26.0
    for family in families:
        slot = palette.get(family, 0)
        members = [row for row in rows if row[0] == family]
        body.append(
            g.text(
                0,
                y + 9,
                f"{g.truncate(family, 40)} — {len(members)} code(s)",
                cls="v-ttl",
                tooltip=family,
            )
        )
        y += header_h
        for _, name, freq in members:
            label = sub_of(name) or name
            body.append(
                g.text(
                    label_w - 6,
                    y + row_h - 4,
                    g.truncate(label, 42),
                    cls="v-lbl",
                    anchor="end",
                    tooltip=f"{name} — {freq} response(s)",
                )
            )
            body.append(
                g.rect(
                    label_w,
                    y + 2,
                    max(1.0, bars(float(freq))),
                    row_h - 4,
                    cls=f"v-f{slot}",
                    tooltip=f"{name} — {freq} response(s)",
                )
            )
            body.append(
                g.text(label_w + max(1.0, bars(float(freq))) + 5, y + row_h - 4, str(freq), cls="v-tick")
            )
            y += row_h

    return [
        '<div class="scroll">',
        g.figure(width, height, body, label="Code frequencies, grouped by family"),
        "</div>",
    ]


# --------------------------------------------------------------------------- #
# View 3 — the response-by-code heatmap
# --------------------------------------------------------------------------- #


def _cluster_of(data: ViewsData) -> dict[int, int]:
    clusters = data.clusters
    if not clusters:
        return {}
    ids = clusters.get("response_ids") or []
    labels = clusters.get("labels") or []
    return {int(r): int(c) for r, c in zip(ids, labels, strict=False)}


def _view_heatmap(data: ViewsData) -> list[str]:
    matrix = data.matrix
    if matrix is None or matrix.is_empty:
        return [_missing("Nothing has been coded, so there is no occurrence matrix.", _RUN_CMD)]
    palette = data.palette
    frequencies = matrix.frequencies()
    codes = sorted(matrix.code_names, key=lambda n: (family_of(n), -frequencies.get(n, 0), n))
    code_index = {name: i for i, name in enumerate(matrix.code_names)}

    cluster_of = _cluster_of(data)
    responses = sorted(matrix.response_ids, key=lambda r: (cluster_of.get(r, 0), r))
    row_index = {rid: i for i, rid in enumerate(matrix.response_ids)}
    counts = matrix.codes_per_response()
    top_count = max(counts.values(), default=1) or 1

    # Cells shrink to fit: at 120 codes and 200 responses this lands near 6 x 3 px,
    # which is still a readable band; at a dozen of each it stops growing at 22 px
    # rather than spreading a tiny matrix across the whole page.
    cell_w = max(3.0, min(22.0, 720.0 / max(1, len(codes))))
    cell_h = max(2.0, min(22.0, 620.0 / max(1, len(responses))))
    left, top_m, margin_w = 62.0, 96.0, 74.0
    plot_w, plot_h = cell_w * len(codes), cell_h * len(responses)
    width = max(460.0, left + plot_w + margin_w + 10.0)
    height = top_m + plot_h + 26.0

    body: list[str] = []
    # Family bands across the top, labelled directly.
    start = 0
    while start < len(codes):
        family = family_of(codes[start])
        stop = start
        while stop < len(codes) and family_of(codes[stop]) == family:
            stop += 1
        x0 = left + start * cell_w
        band_w = (stop - start) * cell_w
        slot = palette.get(family, 0)
        body.append(
            g.rect(
                x0,
                top_m - 10.0,
                max(1.0, band_w - 1.0),
                7.0,
                cls=f"v-f{slot}",
                tooltip=f"{family} — {stop - start} code(s)",
            )
        )
        body.append(
            g.text(
                x0 + 2,
                top_m - 16.0,
                g.truncate(family, max(3, int(band_w / 5.6))),
                cls="v-tick",
                tooltip=family,
            )
        )
        start = stop

    for position, rid in enumerate(responses):
        y = top_m + position * cell_h
        row = matrix.values[row_index[rid]]
        cluster = cluster_of.get(rid)
        marker = f"cluster {cluster}" if cluster is not None else "no clustering"
        body.append(
            g.rect(
                left,
                y,
                plot_w,
                max(0.6, cell_h - 0.4),
                cls="v-off",
                tooltip=f"response {rid} — {counts.get(rid, 0)} code(s), {marker}",
            )
        )
        for column, name in enumerate(codes):
            if not row[code_index[name]]:
                continue
            slot = palette.get(family_of(name), 0)
            body.append(
                g.rect(
                    left + column * cell_w,
                    y,
                    max(0.8, cell_w - 0.4),
                    max(0.6, cell_h - 0.4),
                    cls=f"v-f{slot}",
                    tooltip=f"response {rid} — {name}",
                )
            )
        count = counts.get(rid, 0)
        body.append(
            g.rect(
                left + plot_w + 8.0,
                y,
                max(0.8, (margin_w - 16.0) * count / top_count),
                max(0.6, cell_h - 0.4),
                cls="v-seq",
                opacity="0.8",
                tooltip=f"response {rid} — {count} code(s)",
            )
        )
        if cell_h >= 8.0 or position % 10 == 0:
            body.append(g.text(left - 6, y + cell_h - 1.0, str(rid), cls="v-tick", anchor="end"))
    body.append(
        g.text(left + plot_w + 8.0, top_m - 16.0, "codes per response", cls="v-tick")
    )
    body.append(
        g.text(
            left,
            top_m + plot_h + 16.0,
            f"{len(codes)} code(s) left to right, by family then frequency; "
            f"{len(responses)} response(s) top to bottom",
            cls="v-tick",
        )
    )

    out = [
        '<div class="scroll">',
        g.figure(width, height, body, label="Response by code occurrence"),
        "</div>",
    ]
    if cluster_of:
        out.append(
            _note(
                "Responses are grouped by the cluster Ward's HCA assigned them, then by "
                "response number inside each cluster. This is the cluster order, not the "
                "dendrogram's own leaf order: clusters.json records the partition, not the "
                "drawing order, and view 11 shows the dendrogram itself."
            )
        )
    else:
        out.append(
            _note(
                "No clustering was found, so responses are in ascending response number. "
                f"Run `{_ANALYSE_CMD}` to order them by cluster."
            )
        )
    if data.filter_summary:
        out.append(_note(f"Filter applied to this matrix: {data.filter_summary}"))
    return out


# --------------------------------------------------------------------------- #
# View 4 — co-occurrence
# --------------------------------------------------------------------------- #


def _matrix_figure(
    names: Sequence[str],
    values: Sequence[Sequence[float]],
    *,
    label: str,
    palette: Mapping[str, int],
    row_names: Sequence[str] | None = None,
) -> str:
    """A labelled square matrix with the count printed in every cell."""
    rows = list(row_names) if row_names is not None else list(names)
    cell = max(26.0, min(46.0, 620.0 / max(1, len(names))))
    left, top = 190.0, 130.0
    width = left + cell * len(names) + 12.0
    height = top + cell * len(rows) + 16.0
    top_value = max((max(row, default=0.0) for row in values), default=0.0)

    body: list[str] = []
    for column, name in enumerate(names):
        x = left + column * cell + cell / 2.0
        body.append(
            g.text(
                x,
                top - 8.0,
                g.truncate(name, 20),
                cls="v-tick",
                anchor="start",
                tooltip=name,
                rotate=-60.0,
            )
        )
    for r, row_name in enumerate(rows):
        y = top + r * cell
        slot = palette.get(row_name, 0)
        body.append(
            g.text(left - 10.0, y + cell / 2.0 + 3.0, g.truncate(row_name, 28), cls=f"v-f{slot}", anchor="end", tooltip=row_name)
        )
        for c, col_name in enumerate(names):
            value = float(values[r][c]) if r < len(values) and c < len(values[r]) else 0.0
            x = left + c * cell
            body.append(
                g.rect(
                    x,
                    y,
                    cell - 1.0,
                    cell - 1.0,
                    cls="v-seq",
                    opacity=g.ramp(value, top_value),
                    tooltip=f"{row_name} x {col_name}: {value:.0f}",
                )
            )
            if value:
                body.append(
                    g.text(x + cell / 2.0, y + cell / 2.0 + 3.0, f"{value:.0f}", cls="v-tick", anchor="middle")
                )
    return g.figure(width, height, body, label=label)


def _view_cooccurrence(data: ViewsData) -> list[str]:
    patterns = data.patterns
    if patterns is None:
        return [_missing("`patterns.json` was not found.", _ANALYSE_CMD)]
    table = patterns.get("family_cooccurrence") or {}
    names = [str(n) for n in table.get("names") or []]
    counts = table.get("counts") or []
    out: list[str] = []
    if names:
        out.extend(
            [
                '<div class="scroll">',
                _matrix_figure(
                    names,
                    counts,
                    label="Family by family co-occurrence",
                    palette=data.palette,
                ),
                "</div>",
            ]
        )
    else:
        out.append('<p class="empty">The analysis recorded no family co-occurrence.</p>')

    combinations = patterns.get("combinations") or {}
    pairs = list(combinations.get("pairs") or [])
    pairs.sort(
        key=lambda p: (
            -_float(p.get("support", 0)),
            -_float(p.get("lift", 0)),
            tuple(str(c) for c in p.get("codes", ())),
        )
    )
    rows = [
        [
            " + ".join(_e(c) for c in pair.get("codes", ())),
            _n(pair.get("support")),
            _round(pair.get("share")),
            _round(pair.get("lift"), 2),
        ]
        for pair in pairs[:_MAX_PAIRS]
    ]
    out.append("<h3>Top code pairs</h3>")
    out.extend(
        _table(
            (("code pair", False), ("support", True), ("share", True), ("lift", True)),
            rows,
        )
    )
    if len(pairs) > _MAX_PAIRS:
        out.append(_note(f"Showing the {_MAX_PAIRS} strongest of {len(pairs)} pairs."))
    out.append(
        _note(
            "Support is the number of responses carrying both codes; share is that over all "
            "responses; lift is the joint share over what chance alone would give — 1.00 is "
            "chance, above 1.00 is travelling together."
        )
    )
    return out


# --------------------------------------------------------------------------- #
# View 5 — the pattern map
# --------------------------------------------------------------------------- #


def _view_patterns(data: ViewsData) -> list[str]:
    patterns = data.patterns
    if patterns is None:
        return [_missing("`patterns.json` was not found.", _ANALYSE_CMD)]
    groups = list(patterns.get("groups") or [])
    if not groups:
        return [
            '<p class="empty">No two responses share an identical family signature, so '
            "there is no pattern group to draw.</p>"
        ]
    shown = groups[:_MAX_PATTERN_GROUPS]
    families = data.families or tuple(
        sorted({f for group in shown for f in group.get("family_signature") or []})
    )
    palette = data.palette
    cell, row_h = 16.0, 18.0
    left, top = 74.0, 150.0
    width = left + cell * len(families) + 90.0
    height = top + row_h * len(shown) + 18.0

    body: list[str] = []
    for column, family in enumerate(families):
        slot = palette.get(family, 0)
        body.append(
            g.text(
                left + column * cell + cell - 4.0,
                top - 8.0,
                g.truncate(family, 24),
                cls=f"v-f{slot}",
                tooltip=family,
                rotate=-60.0,
            )
        )
    for index, group in enumerate(shown):
        y = top + index * row_h
        signature = {str(f) for f in group.get("family_signature") or []}
        size = len(group.get("response_ids") or [])
        body.append(g.text(left - 8.0, y + row_h - 5.0, f"n={size}", cls="v-tick", anchor="end"))
        for column, family in enumerate(families):
            present = family in signature
            body.append(
                g.rect(
                    left + column * cell,
                    y + 2.0,
                    cell - 2.0,
                    row_h - 6.0,
                    cls=f"v-f{palette.get(family, 0)}" if present else "v-off",
                    tooltip=f"group {index + 1}: {family} {'present' if present else 'absent'}",
                )
            )
        body.append(
            g.text(
                left + cell * len(families) + 8.0,
                y + row_h - 5.0,
                g.truncate(", ".join(str(r) for r in group.get("response_ids") or []), 14),
                cls="v-tick",
                tooltip=", ".join(str(r) for r in group.get("response_ids") or []),
            )
        )

    out = [
        '<div class="scroll">',
        g.figure(width, height, body, label="Pattern groups by family signature"),
        "</div>",
    ]
    rows = [
        [
            str(index + 1),
            str(len(group.get("response_ids") or [])),
            ", ".join(_e(f) for f in group.get("family_signature") or []) or "<em>no codes</em>",
            _e(", ".join(str(r) for r in group.get("response_ids") or [])),
        ]
        for index, group in enumerate(shown)
    ]
    out.extend(
        _table(
            (("group", True), ("size", True), ("family signature", False), ("responses", False)),
            rows,
        )
    )
    if len(groups) > _MAX_PATTERN_GROUPS:
        out.append(_note(f"Showing the {_MAX_PATTERN_GROUPS} largest of {len(groups)} groups."))
    singletons = patterns.get("singleton_response_ids") or []
    out.append(
        _note(
            f"{len(singletons)} response(s) carry a family signature no other response "
            "shares: " + (", ".join(str(r) for r in singletons) or "none") + "."
        )
    )
    return out


# --------------------------------------------------------------------------- #
# View 6 — the affinity map
# --------------------------------------------------------------------------- #


def _view_affinity(data: ViewsData) -> list[str]:
    affinity = data.affinity
    if affinity is None:
        return [_missing("`affinity.json` was not found.", _ANALYSE_CMD)]
    palette = data.palette
    groups = list(affinity.get("groups") or [])
    out: list[str] = []
    caveat = str(affinity.get("offline_caveat") or "")
    if caveat:
        out.append(f'<div class="caveat"><p>{_e(caveat)}</p></div>')
    out.append(
        _note(
            f"alpha {affinity.get('alpha')} on the description cosine, "
            f"{_round(1 - float(affinity.get('alpha', 0) or 0), 2)} on co-occurrence; "
            f"cut at similarity {affinity.get('threshold')}. Both are uncalibrated "
            "inspection defaults (ADR-0036)."
        )
    )
    if not data.has_descriptions:
        out.append(
            _note(
                "This codebook carries no descriptions, so the cosine half of the blend "
                "compares code names alone. Supply --codebook to gaf analyse to give it "
                "descriptions."
            )
        )
    if not groups:
        out.append('<p class="empty">No two leaf codes clustered together at this threshold.</p>')
    out.append('<div class="cards">')
    for group in groups[:_MAX_AFFINITY_GROUPS]:
        members = [str(m) for m in group.get("members") or []]
        per_code = group.get("per_code_frequency") or {}
        badges = ['<span class="badge">mechanical label</span>']
        if group.get("cross_family"):
            badges.append('<span class="badge badge-cross">spans families</span>')
        chips = " ".join(
            f'<span class="chip">{_swatch(palette.get(family_of(m), 0), family_of(m))}'
            f'<span class="sep">·</span>'
            f'<span class="mono">{_e(sub_of(m) or m)}</span>'
            f'<span class="sub"> {int(per_code.get(m, 0))}</span></span>'
            for m in members
        )
        out.append(
            '<article class="card">'
            f'<h3>{_e(group.get("label_suggestion") or "(unnamed)")}</h3>'
            f'<p class="meta">{" ".join(badges)} · {len(members)} code(s) · '
            f'{_n(group.get("total_responses"))} response(s)</p>'
            f'<p class="chips">{chips}</p>'
            "</article>"
        )
    out.append("</div>")
    if len(groups) > _MAX_AFFINITY_GROUPS:
        out.append(_note(f"Showing the first {_MAX_AFFINITY_GROUPS} of {len(groups)} groups."))
    out.append(
        _note(
            "Every label above is mechanical — the most frequent name tokens among the "
            "group's members. Naming a theme is a human act; this is a starting point for "
            "one, not a finding."
        )
    )

    out.append("<h3>Sub-labels that occur under more than one family</h3>")
    rows = [
        [
            f'<span class="mono">{_e(entry.get("sub_label"))}</span>',
            ", ".join(
                _swatch(palette.get(str(f), 0), str(f)) for f in entry.get("families") or []
            ),
            ", ".join(f'<span class="mono">{_e(c)}</span>' for c in entry.get("codes") or []),
        ]
        for entry in affinity.get("cross_family_subcodes") or []
    ]
    out.extend(_table((("sub-label", False), ("families", False), ("codes", False)), rows))
    singletons = affinity.get("singleton_leaves") or []
    out.append(
        _note(f"{len(singletons)} leaf code(s) clustered with nothing else at this threshold.")
    )
    excluded = affinity.get("excluded") or []
    if excluded:
        out.append("<h3>Leaves the clustering could not place</h3>")
        out.extend(
            _table(
                (("code", False), ("why", False)),
                [
                    [f'<span class="mono">{_e(row.get("name"))}</span>', _e(row.get("reason"))]
                    for row in excluded
                ],
            )
        )
    return out


# --------------------------------------------------------------------------- #
# View 7 — code growth and the timeline
# --------------------------------------------------------------------------- #


def _view_growth(data: ViewsData, figures: list[str]) -> list[str]:
    curve = data.growth
    if curve is None:
        return [_missing("Nothing has been coded, so there is no growth curve.", _RUN_CMD)]
    out: list[str] = []
    if data.timeline_figure is not None:
        css, markup = _inline_figure(data.timeline_figure, figure_id="fig-timeline")
        figures.append(css)
        out.extend(['<div class="scroll figure" id="fig-timeline">', markup, "</div>"])
    else:
        out.append(_missing("No timeline could be built.", _REPORT_CMD))

    spiked = {spike.batch: spike for spike in data.spikes}
    rows = []
    for point in curve.points:
        spike = spiked.get(point.batch)
        rows.append(
            [
                str(point.batch),
                str(point.responses_in_batch),
                str(point.cumulative_responses),
                str(point.new_codes),
                str(point.cumulative_codes),
                f"{point.new_codes_per_response:.3f}",
                f'<strong>{_e(spike.rule)}</strong>' if spike is not None else "·",
            ]
        )
    out.extend(
        _table(
            (
                ("batch", True),
                ("responses", True),
                ("cumulative", True),
                ("new codes", True),
                ("codes so far", True),
                ("new per response", True),
                ("spike", False),
            ),
            rows,
        )
    )
    saturated = (
        f"batch {curve.saturated_at_batch}"
        if curve.saturated_at_batch is not None
        else "no batch yet"
    )
    out.append(
        _note(
            f"Batch numbers are 1-based. Batch size {curve.batch_size}; "
            f"{curve.total_codes} distinct code(s); first batch admitting nothing new: "
            f"{saturated}."
        )
    )
    if data.spikes:
        out.append("<h3>Spikes</h3><ul class=\"findings\">")
        for spike in data.spikes:
            ratio = "no baseline" if spike.ratio is None else f"{spike.ratio:.2f}x baseline"
            out.append(
                f"<li><strong>batch {spike.batch}</strong> — {spike.new_codes} new code(s), "
                f"{_e(ratio)}, rule <span class=\"mono\">{_e(spike.rule)}</span>. "
                f"{_e(spike.reason)}</li>"
            )
        out.append("</ul>")
        out.append(
            _note(
                "The spike thresholds are uncalibrated defaults (ADR-0033): a spike is a "
                "prompt to look, not a finding."
            )
        )
    else:
        out.append(_note("No batch met the spike rule."))
    return out


# --------------------------------------------------------------------------- #
# View 8 — the loop handover
# --------------------------------------------------------------------------- #


def _view_handover(data: ViewsData) -> list[str]:
    out: list[str] = []
    rule_ids = [rule.id for rule in HANDOVER_RULES]
    if not data.decision_trace:
        out.append(
            _missing(
                "This coding has no per-batch handover trace: only a run records one.",
                _RUN_CMD,
            )
        )
    else:
        header: list[tuple[str, bool]] = [("batch", True), ("verdict", False)]
        header += [(rid.removeprefix("handover."), False) for rid in rule_ids]
        header += [("trigger", False), ("reason", False)]
        rows = []
        for row in data.decision_trace:
            fired = {str(r) for r in row.get("fired") or ()}
            held = {str(r) for r in row.get("held") or ()}
            cells = [
                _n(row.get("batch")),
                f'<span class="verdict v-{_slug(str(row.get("verdict")))}">'
                f'{_e(row.get("verdict"))}</span>',
            ]
            for rid in rule_ids:
                if rid in fired:
                    cells.append('<span class="fired" title="fired">● fired</span>')
                elif rid in held:
                    cells.append('<span class="held" title="held">◐ held</span>')
                else:
                    cells.append('<span class="quiet" title="quiet">· quiet</span>')
            cells.append(_e(row.get("trigger")))
            cells.append(_e(row.get("reason")))
            rows.append(cells)
        out.extend(_table(header, rows))
        out.append(
            _note(
                "One row per batch boundary, 1-based. A cell says whether that rule fired, "
                "was held by the spacing rule, or was quiet; the glyph carries the same "
                "meaning as the colour."
            )
        )

    if data.decision_matrix is None:
        out.append(
            _missing(
                "The static decision matrix is rendered from a run configuration, and this "
                "coding has none.",
                _RUN_CMD,
            )
        )
        return out
    matrix = data.decision_matrix
    out.append("<h3>The decision matrix</h3>")
    out.append(
        _note(
            f"{_n(matrix.get('n_rules'))} rules across "
            + ", ".join(str(loop) for loop in matrix.get("loops") or [])
            + ". Trigger precedence: "
            + " > ".join(str(t) for t in matrix.get("trigger_precedence") or [])
            + "."
        )
    )
    for loop in matrix.get("loops") or []:
        rules = [r for r in matrix.get("rules") or [] if r.get("loop") == loop]
        out.append(f"<h4>{_e(loop)} loop</h4>")
        out.extend(
            _table(
                (
                    ("rule", False),
                    ("decision", False),
                    ("decided by", False),
                    ("condition", False),
                    ("outcome", False),
                ),
                [
                    [
                        f'<span class="mono">{_e(rule.get("id"))}</span>',
                        _e(rule.get("decision")),
                        _e(rule.get("decided_by")),
                        _e(rule.get("condition")),
                        _e(rule.get("outcome")),
                    ]
                    for rule in rules
                ],
            )
        )
    return out


# --------------------------------------------------------------------------- #
# View 9 — the reorganisation trail
# --------------------------------------------------------------------------- #


def _pairs(value: Any) -> str:
    """A near-duplicate-pair count, with `null` read as what it means: unrecorded.

    The trail reports codebook health *after* a checkpoint as null by design — nothing
    recomputes it, and doing so needs an embedding space `build_trail` is not given.
    Rendering that as `0` would claim a clean codebook the run never measured.
    """
    return "not recorded" if value is None else str(value)


def _view_trail(data: ViewsData) -> list[str]:
    if data.trail is None:
        return [
            _missing(
                "The reorganisation trail is read from a run's own store (`gaf.sqlite`).",
                _REPORT_CMD,
            )
        ]
    trail = data.trail.to_json()
    entries = list(trail.get("entries") or [])
    out: list[str] = []
    if not entries:
        out.append(
            '<p class="empty">No checkpoint ran in this run: the codebook was never '
            "reorganised.</p>"
        )
    for entry in entries:
        net = entry.get("net_change") or {}
        out.append("<details><summary>")
        out.append(
            f'<span class="mono">{_e(entry.get("checkpoint_id"))}</span> — '
            f'{_e(entry.get("status"))}, trigger {_e(entry.get("trigger"))}, at '
            f'{_n(entry.get("at_response_count"))} response(s)'
        )
        out.append("</summary>")
        out.extend(
            _table(
                (("measure", False), ("before", True), ("after", True), ("net", True)),
                [
                    [
                        "families",
                        _n(entry.get("families_before")),
                        _n(entry.get("families_after")),
                        _n(net.get("families")),
                    ],
                    [
                        "near-duplicate pairs",
                        _pairs(entry.get("near_duplicate_pairs_before")),
                        _pairs(entry.get("near_duplicate_pairs_after")),
                        _pairs(net.get("near_duplicate_pairs")),
                    ],
                    ["codes", "", "", _n(net.get("codes"))],
                ],
            )
        )
        out.append(f'<p class="note">{_e(entry.get("reason"))}</p>')
        edited = entry.get("edited") or []
        out.append(
            _note(
                f"{len(edited)} operation(s) the human replaced rather than accepting or "
                "rejecting outright."
            )
        )
        out.append("</details>")
    out.append(
        _note(
            "Codebook health after a checkpoint is not recomputed anywhere in this build, "
            "so it is reported as not recorded rather than as zero."
        )
    )

    out.append("<h3>Lineage — every name that no longer exists</h3>")
    rows = [
        [
            f'<span class="mono">{_e(row.get("from_name"))}</span>',
            _e(row.get("reason")),
            ", ".join(f'<span class="mono">{_e(n)}</span>' for n in row.get("to_names") or [])
            or "<em>nothing</em>",
            f'<span class="mono">{_e(row.get("checkpoint_id"))}</span>',
        ]
        for row in trail.get("lineage") or []
    ]
    out.extend(
        _table(
            (("was", False), ("why", False), ("became", False), ("at checkpoint", False)), rows
        )
    )
    return out


# --------------------------------------------------------------------------- #
# View 10 — the crosswalk
# --------------------------------------------------------------------------- #


def _view_crosswalk(data: ViewsData) -> list[str]:
    crosswalk = data.crosswalk
    if crosswalk is None:
        return [
            _missing(
                "`crosswalk.json` was not found.",
                "gaf analyse --assignments <assignments.json> --out <dir> "
                "--crosswalk-target <codebook.json>",
            )
        ]
    out: list[str] = [
        _note(
            f"Embedding space {crosswalk.get('space_id')}; tau_high "
            f"{crosswalk.get('tau_high')}, tau_low {crosswalk.get('tau_low')}; "
            f"names only: {'yes' if crosswalk.get('names_only') else 'no'}."
        )
    ]
    note = str(crosswalk.get("fair_mode_note") or "")
    if note:
        out.append(f'<div class="caveat"><p>{_e(note)}</p></div>')

    rollup = list(crosswalk.get("source_family_rollup") or [])[:_MAX_CROSSWALK_ROWS]
    targets = sorted({t for row in rollup for t in (row.get("distribution") or {})})
    if rollup and targets:
        values = [
            [float((row.get("distribution") or {}).get(t, 0)) for t in targets] for row in rollup
        ]
        out.extend(
            [
                '<div class="scroll">',
                _matrix_figure(
                    targets,
                    values,
                    label="Source families mapped onto target families",
                    palette=data.palette,
                    row_names=[str(row.get("family")) for row in rollup],
                ),
                "</div>",
            ]
        )
    bands = {"same": 0, "grey": 0, "unmapped": 0}
    for mapping in crosswalk.get("mappings") or []:
        band = str(((mapping.get("nearest") or {}).get("band")) or "unmapped")
        bands[band] = bands.get(band, 0) + 1
    out.append("<h3>Bands</h3>")
    out.extend(
        _table(
            (("band", False), ("leaves", True), ("what it means", False)),
            [
                ["same", str(bands.get("same", 0)), "at or above tau_high — the same code"],
                ["grey", str(bands.get("grey", 0)), "between the two thresholds — a judgment call"],
                ["unmapped", str(bands.get("unmapped", 0)), "below tau_low — nothing on the other side"],
            ],
        )
    )
    out.append("<h3>Blind spots — target leaves nothing reaches</h3>")
    out.append(_code_list(crosswalk.get("unmapped_target_leaves") or []))
    out.append("<h3>Inventions — source leaves nothing matches</h3>")
    out.append(_code_list(crosswalk.get("unmapped_source_leaves") or []))
    return out


def _code_list(names: Sequence[Any]) -> str:
    if not names:
        return '<p class="empty">None.</p>'
    items = " ".join(f'<span class="chip mono">{_e(n)}</span>' for n in names)
    return f'<p class="chips">{items}</p>'


# --------------------------------------------------------------------------- #
# View 11 — clusters and saturation
# --------------------------------------------------------------------------- #


def _view_clusters(data: ViewsData, figures: list[str]) -> list[str]:
    if data.clusters is None and data.saturation is None:
        return [_missing("No clustering or saturation curve was found.", _ANALYSE_CMD)]
    out: list[str] = []
    clusters = data.clusters or {}
    if clusters:
        out.append("<h3>Ward's hierarchical cluster analysis</h3>")
        out.append(
            _note(
                f"{_n(clusters.get('n_responses'))} response(s) x "
                f"{_n(clusters.get('n_codes'))} code(s) into "
                f"{_n(clusters.get('n_clusters'))} cluster(s) "
                f"({_e(clusters.get('n_clusters_source'))}), cut at distance "
                f"{_round(clusters.get('cut_distance'))}."
            )
        )
        warnings = [str(w) for w in clusters.get("warnings") or []]
        if warnings:
            out.append('<div class="caveat"><h3>Warnings carried from clusters.json</h3>')
            out.extend(f"<p>{_e(warning)}</p>" for warning in warnings)
            out.append("</div>")
    if data.dendrogram_figure is not None:
        css, markup = _inline_figure(data.dendrogram_figure, figure_id="fig-dendrogram")
        figures.append(css)
        out.extend(['<div class="scroll figure" id="fig-dendrogram">', markup, "</div>"])
    else:
        out.append(_missing("`dendrogram.svg` was not found.", _ANALYSE_CMD))

    out.append("<h3>Theoretical saturation</h3>")
    saturation = data.saturation or {}
    if saturation:
        reached = saturation.get("saturated_at_batch")
        out.append(
            _note(
                f"Batch size {_n(saturation.get('batch_size'))}; "
                f"{_n(saturation.get('total_codes'))} distinct code(s); first batch "
                "admitting nothing new: "
                + (f"batch {reached}" if reached is not None else "no batch yet")
                + "."
            )
        )
    if data.saturation_figure is not None:
        css, markup = _inline_figure(data.saturation_figure, figure_id="fig-saturation")
        figures.append(css)
        out.extend(['<div class="scroll figure" id="fig-saturation">', markup, "</div>"])
    else:
        out.append(_missing("`saturation.svg` was not found.", _ANALYSE_CMD))
    return out


# --------------------------------------------------------------------------- #
# The page
# --------------------------------------------------------------------------- #

_HOW_TO_READ: dict[str, str] = {
    "codebook-tree": (
        "Each band is one code; its height is how many responses carry it, and its colour "
        "is its family."
    ),
    "frequencies": (
        "One bar per code, grouped under its family and ordered by how many responses "
        "carry it; the number at the end of each bar is that count."
    ),
    "heatmap": (
        "One row per response and one column per code: a filled cell means that response "
        "carries that code, and the bar in the right margin is how many codes it carries "
        "in total."
    ),
    "cooccurrence": (
        "The matrix counts responses in which two families both appear; the table below "
        "ranks individual code pairs by how often they travel together."
    ),
    "patterns": (
        "Each row is a group of responses whose codes touch exactly the same families; a "
        "filled cell means that family is in the group's signature."
    ),
    "affinity": (
        "Each card is a group of leaf codes that sit close together by description and by "
        "co-occurrence, regardless of which family they were filed under."
    ),
    "growth": (
        "The line is how many distinct codes existed after each batch and the bars are how "
        "many were new; a marked batch is one the spike rule flagged."
    ),
    "handover": (
        "One row per batch boundary, showing which handover rule fired, which was held "
        "back by the spacing rule, and which stayed quiet."
    ),
    "trail": (
        "One entry per checkpoint the slow loop opened, what the human decided, and what "
        "every retired code name became."
    ),
    "crosswalk": (
        "The matrix counts how many of each source family's leaf codes land on each target "
        "family; scattered rows are where the two codebooks cut the world differently."
    ),
    "clusters": (
        "The dendrogram is the full agglomeration the cluster partition was cut out of; "
        "the saturation curve is the grounded-theory claim that further sampling stops "
        "producing new codes."
    ),
}

_STYLE = """
:root {
  --ink: #1b1b1b;
  --muted: #5b5b5b;
  --rule: #d8d5cf;
  --paper: #fbfaf7;
  --panel: #ffffff;
  --accent: #29506d;
  --flag: #8c1d18;
  --hold: #8a5a00;
  --caveat-bg: #fdf6e3;
  --caveat-rule: #b8860b;
}
@media (prefers-color-scheme: dark) {
  :root {
    --ink: #e8e6e1;
    --muted: #a09b93;
    --rule: #3a3936;
    --paper: #17181a;
    --panel: #1e1f22;
    --accent: #8fb6d8;
    --flag: #e58a86;
    --hold: #e0a458;
    --caveat-bg: #2a2418;
    --caveat-rule: #b8860b;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0;
  padding: 0 0 4rem;
  background: var(--paper);
  color: var(--ink);
  font: 16px/1.55 "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
}
main { max-width: 68rem; margin: 0 auto; padding: 0 1.5rem; }
header.page { border-bottom: 2px solid var(--ink); margin-bottom: 1rem; padding: 2rem 0 1rem; }
h1 { font-size: 1.7rem; margin: 0 0 .35rem; letter-spacing: -.01em; }
h2 { font-size: 1.3rem; margin: 0 0 .5rem; }
h3 { font-size: 1.02rem; margin: 1.3rem 0 .3rem; }
h4 { font-size: .95rem; margin: 1rem 0 .2rem; color: var(--muted); }
p { margin: .5rem 0; }
a { color: var(--accent); }
.sub, .meta { color: var(--muted); font-size: .85rem; }
.mono, code, pre { font-family: "SF Mono", ui-monospace, "DejaVu Sans Mono", Menlo, Consolas, monospace; font-size: .85em; }
pre { white-space: pre-wrap; word-break: break-word; }
nav.toc { border-bottom: 1px solid var(--rule); padding-bottom: .7rem; margin-bottom: 1.4rem; }
nav.toc ol { margin: 0; padding-left: 1.3rem; columns: 2; font-size: .9rem; }
section.view {
  border-top: 1px solid var(--rule);
  padding-top: 1.4rem;
  margin-top: 2rem;
}
section.view > .idx { color: var(--muted); font-size: .8rem; letter-spacing: .08em; }
.how { border-left: 3px solid var(--accent); padding-left: .7rem; font-size: .92rem; }
.note { color: var(--muted); font-size: .86rem; }
.missing { background: var(--panel); border: 1px dashed var(--rule); padding: .7rem .9rem; font-size: .9rem; }
.caveat { background: var(--caveat-bg); border: 1px solid var(--rule); border-left: 5px solid var(--caveat-rule); padding: .7rem .9rem; margin: .9rem 0; }
.caveat h2, .caveat h3 { border: 0; margin: 0 0 .3rem; font-size: 1rem; }
table { border-collapse: collapse; width: 100%; margin: .7rem 0; font-size: .88rem; }
th, td { border-bottom: 1px solid var(--rule); padding: .32rem .45rem; text-align: left; vertical-align: top; }
th { border-bottom: 2px solid var(--ink); font-weight: 600; }
td.num, th.num { text-align: right; }
.wrap, .scroll { overflow-x: auto; }
.scroll { max-height: 42rem; overflow-y: auto; border: 1px solid var(--rule); background: var(--panel); padding: .6rem; }
.figure { background: #ffffff; }
details { margin: .6rem 0; }
summary { cursor: pointer; font-size: .92rem; }
ul.tree { list-style: none; padding-left: .8rem; font-size: .88rem; }
ul.tree ul { list-style: none; padding-left: 1.1rem; }
ul.findings { list-style: none; margin: .4rem 0; padding: 0; font-size: .88rem; }
ul.findings li { border-top: 1px dotted var(--rule); padding: .3rem 0; }
.cards { display: flex; flex-wrap: wrap; gap: .7rem; margin: .8rem 0; }
.card { background: var(--panel); border: 1px solid var(--rule); border-radius: 3px; padding: .6rem .8rem; flex: 1 1 19rem; }
.card h3 { margin: 0 0 .2rem; font-size: 1rem; }
.chips { margin: .3rem 0; line-height: 2; }
.chip { border: 1px solid var(--rule); border-radius: 3px; padding: .1rem .35rem; margin-right: .25rem; font-size: .82rem; white-space: nowrap; }
.chip .fam { color: var(--muted); }
.chip .sep { color: var(--muted); padding: 0 .2em; }
.badge { border: 1px solid var(--rule); border-radius: 2px; padding: 0 .3rem; font-size: .72rem; letter-spacing: .04em; text-transform: uppercase; }
.badge-cross { border-color: var(--accent); color: var(--accent); }
.fired { color: var(--flag); font-weight: 600; }
.held { color: var(--hold); }
.quiet { color: var(--muted); }
.verdict { font-weight: 600; }
.empty { color: var(--muted); font-style: italic; }
footer { border-top: 1px solid var(--rule); margin-top: 2.5rem; padding-top: .8rem; color: var(--muted); font-size: .85rem; }
@media print { body { background: #fff; } section.view { break-inside: avoid; } .scroll { max-height: none; } }
""".strip()


def render_views_html(data: ViewsData, *, title: str | None = None) -> str:
    """The whole page as one HTML document. Pure and deterministic.

    No respondent text reaches this function: `data` carries code names, family names,
    response numbers, counts and scores, and the renderers below draw only those.
    """
    heading = title or f"Views of the dataset — {data.source_label}"
    figures: list[str] = []

    bodies: dict[str, list[str]] = {
        "codebook-tree": _view_codebook_tree(data),
        "frequencies": _view_frequencies(data),
        "heatmap": _view_heatmap(data),
        "cooccurrence": _view_cooccurrence(data),
        "patterns": _view_patterns(data),
        "affinity": _view_affinity(data),
        "growth": _view_growth(data, figures),
        "handover": _view_handover(data),
        "trail": _view_trail(data),
        "crosswalk": _view_crosswalk(data),
        "clusters": _view_clusters(data, figures),
    }

    style = "\n".join([_STYLE, g.CHART_CSS, *figures])
    parts: list[str] = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{_e(heading)}</title>",
        f"<style>{style}</style>",
        "</head>",
        "<body>",
        # `id="top"` is the anchor every "back to the top" link uses, so the page needs
        # no script for navigation.
        '<main id="top">',
        '<header class="page">',
        f"<h1>{_e(heading)}</h1>",
        '<p class="sub">'
        + " · ".join(f"{_e(label)} {_e(value)}" for label, value in data.meta)
        + "</p>",
        '<p class="sub">Eleven views of one coding. This page shows code names, family '
        "names, response numbers, counts and scores — never a respondent's words. It is "
        "self-contained: no script, no network request, no external asset.</p>",
        "</header>",
    ]
    if data.analysis_label:
        parts.append(
            f'<p class="sub">Analysis artefacts read from '
            f'<span class="mono">{_e(data.analysis_label)}</span>.</p>'
        )
    if data.caveats:
        parts.append('<div class="caveat">')
        parts.append("<h2>Caveats — read these before the figures</h2>")
        parts.extend(f"<p>{_e(caveat)}</p>" for caveat in data.caveats)
        parts.append("</div>")

    parts.append('<nav class="toc"><ol>')
    parts.extend(
        f'<li><a href="#{_e(anchor)}">{_e(view_title)}</a></li>' for anchor, view_title in VIEWS
    )
    parts.append("</ol></nav>")

    for index, (anchor, view_title) in enumerate(VIEWS, start=1):
        parts.append(f'<section class="view" id="{_e(anchor)}">')
        parts.append(f'<p class="idx">VIEW {index} OF {len(VIEWS)}</p>')
        parts.append(f"<h2>{_e(view_title)}</h2>")
        parts.append(_how(_HOW_TO_READ[anchor]))
        parts.extend(bodies[anchor])
        parts.append('<p class="sub"><a href="#top">back to the top</a></p>')
        parts.append("</section>")

    parts.append("<footer>")
    parts.append(
        f'<p>Generated by gaf from {_e(data.source_label)}. '
        "No respondent text appears anywhere on this page. This file is self-contained: "
        "no script, no network request, no external asset.</p>"
    )
    parts.append("</footer>")
    parts.extend(["</main>", "</body>", "</html>"])
    return "\n".join(parts) + "\n"
