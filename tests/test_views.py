"""T6 gate for `views.html`, the shared SVG primitives and the Mermaid codebook tree.

The claims under test, in the order they matter:

1. **No respondent text reaches the page.** Not a quote, not a segment, not a
   description. Asserted the way `tests/test_golden.py` asserts it of the repository:
   no run of twenty characters of any synthetic response appears anywhere in the HTML.
   This is the whole reason `views.html` exists beside `codebook.html` rather than
   instead of it, so it is the first test in the file.
2. **Self-contained**, on the same terms `codebook.html` is tested on: no script, no
   `http`, no external asset, no web font, no `url(` and no `@import`.
3. **Deterministic** — the same data renders byte-identical HTML.
4. **Eleven views, always**, each with an anchor, a number and a "how to read this";
   a view whose artefact is missing names the command that writes it instead of
   raising.
5. **Every figure is well-formed XML**, and a figure inlined from another module
   carries its stylesheet scoped to itself rather than leaking it over the page.
6. **A family keeps its colour** from one figure to the next, and colour is never the
   only carrier: every band is labelled or carries a `<title>`.
7. **Null is not zero.** The reorganisation trail records codebook health after a
   checkpoint as null by design; the page says "not recorded".

Everything here is offline and synthetic: the invented corpus of
`tests.fixtures.corpus`, the toy codebooks, and names this file makes up.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from xml.etree import ElementTree

import pytest

from gaf.analysis import hca
from gaf.checks.growth import Spike, code_growth, detect_spikes
from gaf.config import CheckpointPolicy
from gaf.models import Assignment, Code, Codebook
from gaf.pipeline import slow_loop
from gaf.report import svg as g
from gaf.report import timeline as timeline_module
from gaf.report.run_report import RUN_JSON_NAME, RunArtefact
from gaf.report.trail import ReorganisationTrail, TrailEntry
from gaf.report.views import (
    VIEWS,
    ViewsData,
    _inline_figure,
    _pairs,
    _scope_css,
    _spike_markers,
    codebook_mermaid,
    default_analysis_dir,
    growth_markdown,
    render_views_html,
    views_from_coding,
    views_from_run,
)
from tests.fixtures.assignments import human_assignments
from tests.fixtures.codebooks import toy_codebook
from tests.fixtures.corpus import synthetic_corpus

#: The same shingle `make provenance` and `scripts/export_results.py` now use
#: (ADR-0047). It was chosen here when the repository-wide guard was still 30, because
#: this page is the artefact most likely to leave the machine; the guard has since
#: come down to meet it.
SHINGLE = 20


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #


@pytest.fixture
def coding() -> ViewsData:
    """A hand coding with no run behind it — the bare path."""
    return views_from_coding(
        human_assignments(),
        codebook=toy_codebook(),
        responses=synthetic_corpus(),
    )


@pytest.fixture(scope="module")
def run_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """One real offline run of the synthetic corpus, through the CLI."""
    from gaf.cli import main
    from gaf.ingest.corpus import write_corpus_json

    base = tmp_path_factory.mktemp("views-run")
    corpus = base / "corpus.json"
    write_corpus_json(synthetic_corpus(), corpus)
    out = base / "run"
    assert (
        main(
            [
                "run",
                "--corpus",
                str(corpus),
                "--run-id",
                "views",
                "--out",
                str(out),
                "--cache-dir",
                str(base / "cache"),
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "analyse",
                "--assignments",
                str(out / "assignments.json"),
                "--data",
                str(corpus),
                "--out",
                str(out / "analysis"),
            ]
        )
        == 0
    )
    return out


@pytest.fixture(scope="module")
def run_data(run_dir: Path) -> ViewsData:
    document = json.loads((run_dir / RUN_JSON_NAME).read_text(encoding="utf-8"))
    return views_from_run(RunArtefact.from_json(document), run_dir)


@pytest.fixture(scope="module")
def run_page(run_data: ViewsData) -> str:
    return render_views_html(run_data)


def _figures(page: str) -> list[str]:
    return re.findall(r"<svg\b.*?</svg>", page, re.DOTALL)


# --------------------------------------------------------------------------- #
# 1. No respondent text. The reason this page exists.
# --------------------------------------------------------------------------- #


def _leaks(page: str) -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    for response in synthetic_corpus():
        text = response.content
        for start in range(0, max(0, len(text) - SHINGLE) + 1):
            shingle = text[start : start + SHINGLE]
            if shingle in page:
                found.append((response.id, shingle))
                break
    return found


def test_no_respondent_text_reaches_the_page_from_a_run(run_page: str):
    assert _leaks(run_page) == []


def test_no_respondent_text_reaches_the_page_from_a_coding(coding: ViewsData):
    """The coding path sees `Assignment.segment`, which *is* respondent text."""
    assert any(
        row.segment in response.content
        for row in human_assignments()
        for response in synthetic_corpus()
    ), "the fixture must really carry respondent text, or this test proves nothing"
    assert _leaks(render_views_html(coding)) == []


def test_no_evidence_quote_reaches_the_page(run_data: ViewsData, run_page: str):
    quotes = [
        evidence.quote
        for code in (run_data.codebook.codes.values() if run_data.codebook else [])
        for evidence in code.evidence
    ]
    assert quotes, "the run must have produced evidence, or this test proves nothing"
    for quote in quotes:
        assert quote not in run_page


def test_no_code_description_reaches_the_page(run_data: ViewsData, run_page: str):
    """A description is written by an agent that has just read a response."""
    descriptions = [
        code.description
        for code in (run_data.codebook.codes.values() if run_data.codebook else [])
        if code.description.strip()
    ]
    assert descriptions, "the run must have produced descriptions"
    for description in descriptions:
        assert description not in run_page


def test_the_mermaid_tree_carries_no_respondent_text(run_data: ViewsData):
    assert _leaks(run_data.mermaid()) == []


# --------------------------------------------------------------------------- #
# 2. Self-contained, on the same terms codebook.html is tested on
# --------------------------------------------------------------------------- #


def test_the_page_is_self_contained(run_page: str):
    assert "http://" not in run_page
    assert "https://" not in run_page
    assert "http" not in run_page, "not even a namespace URL from an inlined figure"
    assert "<script" not in run_page.lower()
    assert "@import" not in run_page
    assert "url(" not in run_page
    assert "<style>" in run_page


def test_the_page_has_no_external_reference_but_the_mermaid_file(run_page: str):
    hrefs = set(re.findall(r'href="([^"]+)"', run_page))
    external = {href for href in hrefs if not href.startswith("#")}
    assert external == {"tree.mmd"}, external
    assert 'src="' not in run_page


def test_both_colour_schemes_define_every_token(run_page: str):
    style = run_page.split("<style>", 1)[1].split("</style>", 1)[0]
    assert style.count("@media (prefers-color-scheme: dark)") == 2, (
        "both the page palette and the chart palette redefine themselves in dark"
    )
    for slot in range(g.N_FAMILY_SLOTS):
        assert style.count(f"--f{slot}:") == 2, f"--f{slot} is not defined for both schemes"
    for token in ("--ink", "--paper", "--muted", "--rule", "--v-grid", "--v-seq"):
        assert style.count(f"{token}:") >= 2, token


# --------------------------------------------------------------------------- #
# 3. Deterministic
# --------------------------------------------------------------------------- #


def test_the_page_is_deterministic(run_data: ViewsData):
    assert render_views_html(run_data) == render_views_html(run_data)


def test_two_collections_of_the_same_run_render_the_same_bytes(run_dir: Path):
    document = json.loads((run_dir / RUN_JSON_NAME).read_text(encoding="utf-8"))
    first = views_from_run(RunArtefact.from_json(document), run_dir)
    second = views_from_run(RunArtefact.from_json(document), run_dir)
    assert render_views_html(first) == render_views_html(second)


def test_the_mermaid_tree_is_deterministic(run_data: ViewsData):
    assert run_data.mermaid() == run_data.mermaid()


# --------------------------------------------------------------------------- #
# 4. Eleven views, always
# --------------------------------------------------------------------------- #


def test_every_view_has_an_anchor_a_number_and_a_how_to_read(run_page: str):
    assert len(VIEWS) == 11
    for index, (anchor, title) in enumerate(VIEWS, start=1):
        assert f'<section class="view" id="{anchor}">' in run_page
        assert f"VIEW {index} OF 11" in run_page
        assert f"<h2>{title}</h2>" in run_page
    assert run_page.count('class="how"') == 11
    assert run_page.count("<strong>How to read this.</strong>") == 11


def test_the_navigation_links_to_every_view(run_page: str):
    for anchor, title in VIEWS:
        assert f'<li><a href="#{anchor}">{title}</a></li>' in run_page
    assert '<main id="top">' in run_page
    assert run_page.count('href="#top"') == 11


def test_the_run_page_states_its_counts_and_its_run_id(run_data: ViewsData, run_page: str):
    assert "run views" in run_page
    assert "responses coded" in run_page
    assert "embedding space" in run_page
    assert "batch size" in run_page
    assert run_data.run_id == "views"


def test_the_caveats_are_carried_above_the_figures(run_page: str):
    assert "Caveats — read these before the figures" in run_page
    assert "ADR-0019" in run_page


def test_a_missing_artefact_names_the_command_that_writes_it(coding: ViewsData):
    """The bare coding has no analysis directory and no audit log."""
    page = render_views_html(coding)
    assert "gaf analyse --assignments" in page
    assert "gaf report --run" in page or "gaf run --corpus" in page
    for anchor, _ in VIEWS:
        assert f'id="{anchor}"' in page, "a missing artefact removes no view"
    available = coding.available()
    assert available["codebook-tree"] and available["heatmap"] and available["growth"]
    assert not available["patterns"] and not available["trail"]


def test_an_empty_coding_still_renders_eleven_views():
    data = views_from_coding([])
    page = render_views_html(data)
    assert page.rstrip().endswith("</html>")
    for anchor, _ in VIEWS:
        assert f'id="{anchor}"' in page
    assert data.mermaid() == ""
    assert not any(data.available().values())


def test_a_run_whose_store_is_missing_still_renders(run_dir: Path, tmp_path: Path):
    """A run directory copied without gaf.sqlite loses the timeline, not the page."""
    copy = tmp_path / "no-store"
    copy.mkdir()
    (copy / RUN_JSON_NAME).write_text(
        (run_dir / RUN_JSON_NAME).read_text(encoding="utf-8"), encoding="utf-8"
    )
    document = json.loads((copy / RUN_JSON_NAME).read_text(encoding="utf-8"))
    data = views_from_run(RunArtefact.from_json(document), copy)
    assert data.timeline is None and data.trail is None
    page = render_views_html(data)
    assert "gaf report --run" in page
    assert page.rstrip().endswith("</html>")


def test_an_unreadable_store_is_treated_as_absent(run_dir: Path, tmp_path: Path):
    copy = tmp_path / "bad-store"
    copy.mkdir()
    (copy / RUN_JSON_NAME).write_text(
        (run_dir / RUN_JSON_NAME).read_text(encoding="utf-8"), encoding="utf-8"
    )
    (copy / "gaf.sqlite").write_text("this is not a database", encoding="utf-8")
    document = json.loads((copy / RUN_JSON_NAME).read_text(encoding="utf-8"))
    data = views_from_run(RunArtefact.from_json(document), copy)
    assert data.timeline is None and data.trail is None


def test_an_unreadable_analysis_artefact_is_treated_as_absent(run_dir: Path, tmp_path: Path):
    analysis = tmp_path / "half-written"
    analysis.mkdir()
    (analysis / "patterns.json").write_text("{not json", encoding="utf-8")
    (analysis / "affinity.json").write_text("[]", encoding="utf-8")  # a list, not an object
    document = json.loads((run_dir / RUN_JSON_NAME).read_text(encoding="utf-8"))
    data = views_from_run(RunArtefact.from_json(document), run_dir, analysis_dir=analysis)
    assert data.patterns is None and data.affinity is None
    assert "gaf analyse --assignments" in render_views_html(data)


def test_the_analysis_directory_defaults_to_the_one_beside_the_run(run_dir: Path, tmp_path: Path):
    assert default_analysis_dir(run_dir) == run_dir / "analysis"
    assert default_analysis_dir(tmp_path) is None


def test_the_run_page_draws_the_analyses_the_analysis_directory_holds(run_data: ViewsData):
    available = run_data.available()
    assert available["patterns"] and available["affinity"] and available["clusters"]
    assert not available["crosswalk"], "no crosswalk target was named"


def test_the_manifest_says_what_the_page_will_show(run_data: ViewsData):
    manifest = run_data.to_json()
    assert manifest["run_id"] == "views"
    assert set(manifest["views"]) == {anchor for anchor, _ in VIEWS}
    assert manifest["n_codes"] > 0 and manifest["n_families"] > 0
    assert manifest["n_responses_with_a_code"] == run_data.n_responses


# --------------------------------------------------------------------------- #
# 5. Figures: well formed, and scoped
# --------------------------------------------------------------------------- #


def test_every_figure_is_well_formed_xml(run_page: str):
    figures = _figures(run_page)
    assert len(figures) >= 8
    for figure in figures:
        ElementTree.fromstring(figure)


def test_every_figure_carries_a_title_for_a_screen_reader(run_page: str):
    for figure in _figures(run_page):
        root = ElementTree.fromstring(figure)
        assert root.get("role") == "img"
        assert root.get("aria-label")
        assert root.find("title") is not None or root.find("{*}title") is not None


def test_an_inlined_figure_has_its_stylesheet_scoped_to_itself(run_page: str):
    """`hca` and `timeline` style bare `text`; inline SVG leaks that over the page."""
    style = run_page.split("<style>", 1)[1].split("</style>", 1)[0]
    for figure_id in ("#fig-dendrogram", "#fig-saturation", "#fig-timeline"):
        assert f"{figure_id} text" in style, figure_id
    assert not re.search(r"(^|\n)\s*text\s*\{", style), "a bare text rule reached the page"
    assert '<div class="scroll figure" id="fig-dendrogram">' in run_page


def test_scope_css_prefixes_every_selector():
    scoped = _scope_css("text{fill:#000}.a,.b{stroke:red}", "#fig")
    assert scoped == "#fig text {fill:#000}\n#fig .a, #fig .b {stroke:red}"


def test_scope_css_leaves_an_at_rule_alone_rather_than_mangling_it():
    """The documented fallback: an at-rule nests, and this pass cannot split it."""
    css = "@media print{text{fill:#000}}"
    assert _scope_css(css, "#fig") == css


def test_no_renderer_in_this_project_writes_an_at_rule():
    """Which is why the fallback above is unreachable today, and stays a fallback."""
    assert "@" not in hca._SVG_CSS
    assert "@" not in timeline_module._MARKER_CSS


def test_inline_figure_strips_the_prolog_the_namespace_and_the_style():
    source = (
        '<?xml version="1.0"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://x" width="10" '
        'height="10"><style>text{fill:#000}</style><rect/></svg>'
    )
    css, markup = _inline_figure(source, figure_id="fig-x")
    assert markup.startswith("<svg ")
    assert "xmlns" not in markup
    assert "http" not in markup
    assert "<style>" not in markup
    assert css == "#fig-x text {fill:#000}"


def test_a_figure_with_no_stylesheet_inlines_to_no_css():
    css, markup = _inline_figure('<svg width="4" height="4"><rect/></svg>', figure_id="fig-y")
    assert css == ""
    assert markup == '<svg width="4" height="4"><rect/></svg>'


# --------------------------------------------------------------------------- #
# 6. The palette: one slot per family, and never the only carrier
# --------------------------------------------------------------------------- #


def test_family_palette_is_sorted_and_wraps():
    palette = g.family_palette(["zulu", "alpha", "mike", "alpha"])
    assert palette == {"alpha": 0, "mike": 1, "zulu": 2}
    many = g.family_palette(f"f{i:02d}" for i in range(g.N_FAMILY_SLOTS + 3))
    assert many[f"f{g.N_FAMILY_SLOTS:02d}"] == 0, "the palette wraps rather than running out"
    assert sorted(set(many.values())) == list(range(g.N_FAMILY_SLOTS))


def test_a_family_keeps_its_colour_slot_across_every_figure(run_data: ViewsData, run_page: str):
    palette = run_data.palette
    assert palette, "the run must have families"
    family = sorted(palette)[0]
    slot = palette[family]
    # The class appears in the tree, the frequency bars and the heatmap bands alike,
    # and the family's own name is written out beside at least one of them.
    assert run_page.count(f'class="v-f{slot}"') >= 3
    assert family in run_page


def test_colour_is_never_the_only_carrier_in_the_handover_grid(run_page: str):
    for glyph, word in (("●", "fired"), ("·", "quiet")):
        assert f"{glyph} {word}" in run_page


def test_a_truncated_label_keeps_its_full_text_in_a_title(run_data: ViewsData):
    page = render_views_html(run_data)
    assert "<title>" in page
    assert page.count("<title>") > len(_figures(page)), "labels carry tooltips too"


def test_truncate_never_returns_an_empty_label():
    assert g.truncate("abcdef", 4) == "abc…"
    assert g.truncate("abc", 9) == "abc"
    assert g.truncate("abcdef", 1) == "…"
    assert g.truncate("abcdef", 0) == ""


def test_a_degenerate_scale_maps_to_the_middle_rather_than_dividing_by_zero():
    flat = g.scale((3.0, 3.0), (0.0, 100.0))
    assert flat(3.0) == 50.0
    assert flat(9.0) == 50.0
    assert flat.span(1.0) == 0.0
    usual = g.scale((0.0, 10.0), (0.0, 50.0))
    assert usual(5.0) == 25.0
    assert usual.span(2.0) == 10.0


def test_the_sequential_ramp_separates_none_from_one_and_stays_under_its_label():
    assert g.ramp(0.0, 10.0) == "0", "an empty cell shows the page through it"
    assert g.ramp(5.0, 0.0) == "0"
    assert float(g.ramp(1.0, 10.0)) > 0.1, "one is never drawn as none"
    assert g.ramp(10.0, 10.0) == "0.70", "the ramp stops short, so the count stays legible"
    assert g.ramp(20.0, 10.0) == "0.70", "a value above the maximum clamps"
    assert float(g.ramp(1.0, 10.0)) < float(g.ramp(9.0, 10.0)), "the ramp is monotone"


def test_band_never_collapses_to_nothing():
    slot, inner = g.band(4, (0.0, 100.0), pad=2.0)
    assert slot == 25.0 and inner == 23.0
    _, tiny = g.band(10_000, (0.0, 100.0), pad=2.0)
    assert tiny >= 0.4
    assert g.band(0, (0.0, 10.0))[0] == 10.0


def test_svg_primitives_escape_and_round():
    assert g.num(-0.0001) == "0.00"
    assert 'class="v-f1"' in g.rect(0, 0, 1, 1, cls="v-f1")
    tooltip = g.rect(0, 0, 1, 1, tooltip='a & "b"')
    assert "<title>a &amp; &quot;b&quot;</title>" in tooltip
    label = g.text(0, 0, "abc", tooltip="abcdef")
    assert "<title>abcdef</title>" in label
    assert "<title>" not in g.text(0, 0, "abc", tooltip="abc")
    assert 'text-anchor="end"' in g.text(0, 0, "x", anchor="end")
    assert "rotate(" in g.text(0, 0, "x", rotate=-60.0)
    assert g.escape(None) == ""
    assert "<line" in g.line(0, 0, 1, 1)


def test_hostile_code_names_are_escaped():
    hostile = 'future-<script>alert("x")</script>'
    data = views_from_coding(
        [Assignment(203, "invented segment", hostile)],
        codebook=Codebook(codes={"c-h": Code(id="c-h", name=hostile, description="")}),
    )
    page = render_views_html(data)
    assert "<script>alert" not in page
    assert "&lt;script&gt;alert" in page
    assert "invented segment" not in page
    assert "#quot;" in data.mermaid(), "a quotation mark would break the Mermaid label"


# --------------------------------------------------------------------------- #
# 7. Null is not zero
# --------------------------------------------------------------------------- #


def test_health_after_a_checkpoint_is_not_recorded_rather_than_zero():
    assert _pairs(None) == "not recorded"
    assert _pairs(0) == "0"
    assert _pairs(3) == "3"


def test_the_trail_view_prints_not_recorded_for_the_health_it_never_measured():
    changelog = slow_loop.Changelog(
        run_id="views",
        checkpoint_id="ckpt-invented",
        trigger="health",
        at_response_count=14,
        base_snapshot_id="snap-a",
        result_snapshot_id="snap-b",
        entries=[],
        dropped=[],
        codes_before=6,
        codes_after=7,
        evidence_before=9,
        evidence_after=9,
    )
    entry = TrailEntry(
        status="applied",
        trigger="health",
        reason="an invented reason for a fixture checkpoint",
        health_before={"near_duplicate_pairs": 2, "n_codes": 6},
        families_before=3,
        families_after=4,
        refactorer_reasoning="invented reasoning that must not reach the page",
        edited=[],
        changelog=changelog,
    )
    data = views_from_coding(human_assignments(), codebook=toy_codebook())
    from dataclasses import replace

    data = replace(data, trail=ReorganisationTrail(run_id="views", entries=[entry]))
    page = render_views_html(data)
    assert "not recorded" in page
    assert "invented reasoning that must not reach the page" not in page
    section = page.split('id="trail"', 1)[1].split("</section>", 1)[0]
    assert ">0<" not in section.replace("near-duplicate pairs", ""), "null never renders as zero"
    assert "ckpt-invented" in section


# --------------------------------------------------------------------------- #
# The Mermaid tree
# --------------------------------------------------------------------------- #


def test_the_mermaid_tree_has_the_flowchart_shape():
    tree = codebook_mermaid(toy_codebook(), {"positive_impacts-healthcare": 4})
    lines = tree.splitlines()
    assert lines[0] == "flowchart LR"
    assert lines[1].strip() == 'ROOT(["Codebook"]):::root'
    assert any(line.strip().startswith('P1["') and "<br/>n=" in line for line in lines)
    assert any(line.strip() == "ROOT --> P1" for line in lines)
    assert any('["healthcare<br/>n=4"]:::leaf' in line for line in lines)
    assert sum(1 for line in lines if line.strip().startswith("classDef ")) == 3


def test_the_mermaid_tree_counts_a_leaf_nothing_carries_as_zero():
    tree = codebook_mermaid(toy_codebook(), {})
    assert "n=0" in tree
    assert "n=" in tree


# --------------------------------------------------------------------------- #
# The growth table, and the spike markers
# --------------------------------------------------------------------------- #


def test_growth_markdown_states_the_batch_numbering_and_every_spike():
    curve = code_growth(human_assignments(), batch_size=2)
    spikes = detect_spikes(curve, CheckpointPolicy(spike_min_new_codes=1, spike_factor=1.0))
    markdown = growth_markdown(curve, spikes)
    assert "## Code growth" in markdown
    assert "1-based" in markdown
    assert "| batch |" in markdown
    for point in curve.points:
        assert f"| {point.batch} | {point.responses_in_batch} |" in markdown
    assert ("### Spikes" in markdown) and (
        ("No batch met the spike rule." in markdown) or ("**batch " in markdown)
    )


def test_growth_markdown_says_so_when_nothing_spiked():
    curve = code_growth(human_assignments(), batch_size=2)
    assert "No batch met the spike rule." in growth_markdown(curve, [])


def test_spike_markers_key_by_the_real_batch_number_not_a_list_position():
    """T4's `markers` keys off `BatchSummary.batch`; T2's `Spike.batch` is the same."""
    spike = Spike(
        batch=7,
        new_codes=9,
        baseline=2.0,
        ratio=4.5,
        rule="ratio",
        window=3,
        reason="an invented reason",
    )
    assert _spike_markers([spike]) == ((7, "spike: 9 new"),)


def test_the_growth_curve_and_the_timeline_share_one_batch_numbering(run_data: ViewsData):
    assert run_data.growth is not None and run_data.timeline is not None
    growth_batches = [point.batch for point in run_data.growth.points]
    timeline_batches = [batch.batch for batch in run_data.timeline.batches]
    assert growth_batches[0] == 1 and timeline_batches[0] == 1
    assert growth_batches == timeline_batches


def test_the_marked_batches_appear_in_the_timeline_figure(run_data: ViewsData):
    """The demo corpus is two batches long, so no batch ever has a baseline.

    The spike rule needs `spike_window` (3) coded batches behind it, so it raises
    nothing here and marks nothing on the figure. It used to fall back to the absolute
    ceiling on batch 1 and mark that, which was `handover.new_codes` reported twice
    under another rule's name (R1 Minor). The marking itself is exercised against a
    hand-built curve below.
    """
    assert run_data.spikes == ()
    assert run_data.timeline_figure is not None
    assert "spike:" not in run_data.timeline_figure


def test_a_spiking_curve_marks_its_batch_on_the_timeline_figure() -> None:
    """The marking path, driven by a curve long enough for the ratio rule to speak."""
    from gaf.checks.growth import code_growth, detect_spikes
    from gaf.config import CheckpointPolicy
    from gaf.models import Assignment
    from gaf.report.timeline import timeline_from_assignments, timeline_svg
    from gaf.report.views import _spike_markers

    rows: list[Assignment] = []
    response_id = 0
    for batch_index, count in enumerate([1, 1, 1, 12]):
        response_id += 1
        rows.extend(
            Assignment(response_id, "s", f"b{batch_index}-code{code}") for code in range(count)
        )
    order = list(range(1, response_id + 1))
    curve = code_growth(rows, batch_size=1, order=order, response_ids=order)
    spikes = detect_spikes(curve, CheckpointPolicy())
    assert [s.batch for s in spikes] == [4], "batch 4 is the first with a baseline"

    timeline = timeline_from_assignments(rows, batch_size=1, response_order=order)
    figure = timeline_svg(timeline, markers=list(_spike_markers(tuple(spikes))))
    assert "spike: 12 new" in figure


# --------------------------------------------------------------------------- #
# The heatmap, the tree and the frequency bars over an unfiltered codebook
# --------------------------------------------------------------------------- #


def test_the_tree_counts_a_code_the_low_frequency_filter_dropped(run_data: ViewsData):
    """The filter belongs to the clustering, not to "what did this coding produce?"."""
    assert run_data.matrix is not None
    dropped = set(run_data.frequencies) - set(run_data.matrix.code_names)
    assert dropped, "the demo corpus has rare codes, or this test proves nothing"
    page = render_views_html(run_data)
    for name in dropped:
        assert name.split("-", 1)[-1] in page


def test_the_heatmap_states_the_filter_and_the_response_order(run_page: str):
    assert "Filter applied to this matrix" in run_page
    assert "cluster order" in run_page or "ascending response number" in run_page


def test_the_heatmap_falls_back_to_response_order_without_a_clustering(coding: ViewsData):
    page = render_views_html(coding)
    assert "ascending response number" in page


def test_the_page_grows_gently_with_the_dataset(run_data: ViewsData):
    """A sanity bound: the page is a page, not a data dump of the matrix."""
    page = render_views_html(run_data)
    assert len(page) < 400_000


# --------------------------------------------------------------------------- #
# Every branch of every view, driven from hand-made artefacts
#
# The shapes below are the ones T3 published, filled with invented code and family
# names. They exist to reach the branches a two-batch demo run never takes: an empty
# table, a capped list, a crosswalk, a figure the analysis directory is missing.
# --------------------------------------------------------------------------- #


def _with(data: ViewsData, **changes: object) -> ViewsData:
    from dataclasses import replace

    return replace(data, **changes)  # type: ignore[arg-type]


def test_a_malformed_score_is_printed_rather_than_raising(coding: ViewsData):
    """An artefact written by an older build is data, not a crash."""
    patterns = {
        "family_cooccurrence": {"names": [], "counts": []},
        "combinations": {"pairs": [{"codes": ["a-x", "b-y"], "support": 2, "lift": "not a number"}]},
        "groups": [],
        "singleton_response_ids": [201],
    }
    page = render_views_html(_with(coding, patterns=patterns))
    assert "The analysis recorded no family co-occurrence." in page
    assert "not a number" in page
    assert "No two responses share an identical family signature" in page


def test_a_long_pair_list_and_a_long_group_list_are_capped(coding: ViewsData):
    pairs = [
        {"codes": [f"fam_a-leaf_{i}", f"fam_b-leaf_{i}"], "support": 60 - i, "share": 0.1, "lift": 1.0}
        for i in range(60)
    ]
    groups = [
        {"family_signature": ["fam_a", "fam_b"], "response_ids": [900 + i, 950 + i]}
        for i in range(60)
    ]
    patterns = {
        "family_cooccurrence": {"names": ["fam_a", "fam_b"], "counts": [[3, 1], [1, 2]]},
        "combinations": {"pairs": pairs},
        "groups": groups,
        "singleton_response_ids": [],
    }
    page = render_views_html(_with(coding, patterns=patterns))
    assert "strongest of 60 pairs" in page
    assert "largest of 60 groups" in page
    assert "0 response(s) carry a family signature no other response shares: none." in page


def test_the_affinity_view_draws_cards_a_caveat_and_the_cross_family_table(coding: ViewsData):
    affinity = {
        "alpha": 0.7,
        "threshold": 0.5,
        "offline_caveat": "An invented caveat about the fallback embedder.",
        "groups": [
            {
                "members": ["fam_a-shared", "fam_b-shared"],
                "families": ["fam_a", "fam_b"],
                "cross_family": True,
                "total_responses": 4,
                "per_code_frequency": {"fam_a-shared": 3, "fam_b-shared": 1},
                "label_suggestion": "shared_fam",
                "label_is_mechanical": True,
            }
        ],
        "singleton_leaves": ["fam_c-alone"],
        "cross_family_subcodes": [
            {"sub_label": "shared", "families": ["fam_a", "fam_b"], "codes": ["fam_a-shared"]}
        ],
        "excluded": [{"name": "fam_d-never", "reason": "not present in the occurrence matrix"}],
    }
    page = render_views_html(_with(coding, affinity=affinity, has_descriptions=False))
    assert "An invented caveat about the fallback embedder." in page
    assert "spans families" in page and "mechanical label" in page
    assert "shared_fam" in page
    assert "Supply --codebook to gaf analyse" in page
    assert "Leaves the clustering could not place" in page
    assert "1 leaf code(s) clustered with nothing else" in page


def test_the_affinity_view_says_when_nothing_clustered_and_caps_a_long_list(coding: ViewsData):
    empty = {"alpha": 0.7, "threshold": 0.5, "groups": [], "cross_family_subcodes": []}
    page = render_views_html(_with(coding, affinity=empty, has_descriptions=True))
    assert "No two leaf codes clustered together at this threshold." in page
    assert "Supply --codebook to gaf analyse" not in page

    many = dict(empty)
    many["groups"] = [
        {
            "members": [f"fam_a-leaf_{i}"],
            "families": ["fam_a"],
            "cross_family": False,
            "total_responses": 1,
            "per_code_frequency": {f"fam_a-leaf_{i}": 1},
            "label_suggestion": "",
        }
        for i in range(60)
    ]
    page = render_views_html(_with(coding, affinity=many, has_descriptions=True))
    assert "Showing the first 40 of 60 groups." in page
    assert "(unnamed)" in page


def test_the_crosswalk_view_draws_the_matrix_the_bands_and_both_lists(coding: ViewsData):
    crosswalk = {
        "space_id": "lexical-v1-512",
        "names_only": True,
        "tau_high": 0.8,
        "tau_low": 0.45,
        "fair_mode_note": "An invented note about which comparison is the fair one.",
        "mappings": [
            {"source": "fam_a-one", "nearest": {"target": "tgt_a-one", "score": 0.9, "band": "same"}},
            {"source": "fam_a-two", "nearest": {"target": "tgt_b-two", "score": 0.6, "band": "grey"}},
            {"source": "fam_b-three", "nearest": {"target": None, "score": None, "band": None}},
        ],
        "source_family_rollup": [
            {"family": "fam_a", "n_leaves": 2, "distribution": {"tgt_a": 1, "tgt_b": 1}, "n_unmapped": 0},
            {"family": "fam_b", "n_leaves": 1, "distribution": {}, "n_unmapped": 1},
        ],
        "unmapped_target_leaves": ["tgt_c-missed"],
        "unmapped_source_leaves": ["fam_b-three"],
    }
    page = render_views_html(_with(coding, crosswalk=crosswalk))
    assert "An invented note about which comparison is the fair one." in page
    assert "names only: yes" in page
    assert "Blind spots" in page and "tgt_c-missed" in page
    assert "Inventions" in page and "fam_b-three" in page
    section = page.split('id="crosswalk"', 1)[1].split("</section>", 1)[0]
    assert "same" in section and "grey" in section and "unmapped" in section


def test_the_crosswalk_view_survives_a_rollup_with_no_targets(coding: ViewsData):
    crosswalk = {
        "space_id": "lexical-v1-512",
        "names_only": False,
        "tau_high": 0.8,
        "tau_low": 0.45,
        "fair_mode_note": "",
        "mappings": [],
        "source_family_rollup": [],
        "unmapped_target_leaves": [],
        "unmapped_source_leaves": [],
    }
    page = render_views_html(_with(coding, crosswalk=crosswalk))
    section = page.split('id="crosswalk"', 1)[1].split("</section>", 1)[0]
    assert section.count("<p class=\"empty\">None.</p>") == 2
    assert "names only: no" in section


def test_the_cluster_view_carries_the_warnings_and_names_the_missing_figures(coding: ViewsData):
    clusters = {
        "n_responses": 9,
        "n_codes": 4,
        "n_clusters": 1,
        "n_clusters_source": "schedule",
        "cut_distance": 3.5,
        "warnings": ["An invented warning carried over from clusters.json."],
        "response_ids": [201, 202],
        "labels": [1, 1],
    }
    saturation = {"batch_size": 10, "total_codes": 4, "saturated_at_batch": None}
    page = render_views_html(_with(coding, clusters=clusters, saturation=saturation))
    assert "An invented warning carried over from clusters.json." in page
    assert "`dendrogram.svg` was not found." in page
    assert "`saturation.svg` was not found." in page
    assert "no batch yet" in page
    assert "cluster order" in page, "a clustering orders the heatmap"


def test_the_handover_grid_marks_fired_held_and_quiet(coding: ViewsData):
    trace = [
        {
            "batch": 1,
            "verdict": "checkpoint_due",
            "trigger": "health",
            "reason": "an invented reason",
            "fired": ["handover.new_codes"],
            "held": ["handover.spacing_hold"],
        }
    ]
    page = render_views_html(_with(coding, decision_trace=tuple(trace)))
    section = page.split('id="handover"', 1)[1].split("</section>", 1)[0]
    assert "● fired" in section
    assert "◐ held" in section
    assert "· quiet" in section
    assert "an invented reason" in section
    assert "The static decision matrix is rendered from a run configuration" in section


def test_the_decision_matrix_is_rendered_loop_by_loop(run_page: str):
    section = run_page.split('id="handover"', 1)[1].split("</section>", 1)[0]
    assert "<h4>fast loop</h4>" in section
    assert "<h4>handover loop</h4>" in section
    assert "<h4>slow loop</h4>" in section
    assert "fast.duplicate_response" in section
    assert "Trigger precedence: health &gt; spike &gt; floor &gt; cadence." in section


def test_an_unreadable_figure_file_is_treated_as_absent(tmp_path: Path):
    from gaf.report.views import _read_text

    missing = tmp_path / "not-here.svg"
    assert _read_text(missing) is None
    directory = tmp_path / "a-directory"
    directory.mkdir()
    assert _read_text(directory) is None


def test_a_coding_with_no_rows_has_no_matrix_and_no_growth():
    data = views_from_coding([])
    assert data.matrix is None and data.growth is None and data.frequencies == {}
    assert data.timeline is None and data.timeline_figure is None


def test_a_coding_whose_matrix_cannot_be_built_degrades_to_no_matrix():
    """A coding that names a response outside the corpus loses the matrix, not the page.

    `build_matrix` refuses that combination by name — the codings and the corpus
    genuinely disagree — and a page is not the place to raise on it: the tree, the
    frequency bars and the growth curve all still describe the coding truthfully.
    """
    rows = [Assignment(9999, "invented segment", "fam_a-leaf")]
    data = views_from_coding(rows, responses=synthetic_corpus())
    assert data.matrix is None and data.frequencies == {}
    page = render_views_html(data)
    assert 'id="heatmap"' in page
    assert page.rstrip().endswith("</html>")
