"""T6 gate for the CLI wiring: `gaf analyse`'s new artefacts, `gaf report`, `gaf views`.

Six claims:

1. **`gaf analyse` writes the three further readings** — patterns, affinity and code
   growth — as JSON and as Markdown, beside what it already wrote, and a fourth, the
   crosswalk, when `--crosswalk-target` names a codebook to map onto.
2. **Without `--codebook`, affinity runs on code names alone and says so** — in the
   Markdown it writes and on stdout, rather than quietly comparing empty descriptions.
3. **What `gaf analyse` and `gaf report` already wrote is byte-identical**: the
   occurrence matrix, the clusters, the saturation curve and `report.txt` do not move
   because three new files landed beside them.
4. **`gaf report` writes the timeline, the trail, the decision matrix and the views
   page**, and `codebook.html` carries the one link across to `views.html`.
5. **`gaf views` builds the page alone** — from a run, from a run plus an analysis
   directory written elsewhere, and from a bare human coding with no audit log behind
   it. A missing artefact is a section naming the command that writes it, never a
   non-zero exit.
6. **No respondent text reaches `views.html` through any of those paths.**

`gaf views` is registered by `gaf/cli/parser.py`, which this task does not own, so the
tests here build a parser from `add_views_parser` — which is exactly the contract the
orchestrator's one-line registration will use.

Every test is offline, on the invented corpus of `tests.fixtures.corpus`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pytest

from gaf.cli import EXIT_OK, EXIT_USAGE, CliError, main
from gaf.cli.views import add_views_parser
from gaf.ingest.corpus import write_corpus_json
from gaf.models import Assignment
from gaf.report.run_report import DECISION_MATRIX_NAME
from gaf.report.views import TREE_MMD_NAME, VIEWS, VIEWS_HTML_NAME
from tests.fixtures.assignments import human_assignments
from tests.fixtures.codebooks import toy_codebook
from tests.fixtures.corpus import synthetic_corpus

SHINGLE = 20

#: What `gaf analyse` gains, and must not lose.
NEW_ANALYSIS_ARTEFACTS = (
    "patterns.json",
    "patterns.md",
    "affinity.json",
    "affinity.md",
    "growth.json",
    "growth.md",
)
OLD_ANALYSIS_ARTEFACTS = (
    "occurrence_matrix.csv",
    "occurrence_matrix.json",
    "clusters.json",
    "clusters.md",
    "dendrogram.svg",
    "saturation.json",
    "saturation.md",
    "saturation.svg",
)

#: What `gaf report` gains.
NEW_REPORT_ARTEFACTS = (
    "timeline.json",
    "timeline.md",
    "timeline.svg",
    "reorganisation_trail.json",
    "reorganisation_trail.md",
    DECISION_MATRIX_NAME,
    VIEWS_HTML_NAME,
    TREE_MMD_NAME,
)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def run_views(*argv: str) -> int:
    """`gaf views ...` through a parser built from the entry point this task exposes."""
    parser = argparse.ArgumentParser(prog="gaf")
    sub = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")
    add_views_parser(sub)
    args = parser.parse_args(list(argv))
    try:
        return int(args.handler(args))
    except CliError as exc:
        print(f"gaf: {exc}", file=sys.stderr)
        return exc.code


def leaks(text: str) -> list[int]:
    """Response ids whose text shows through, by a twenty-character shingle."""
    found: list[int] = []
    for response in synthetic_corpus():
        body = response.content
        for start in range(0, max(0, len(body) - SHINGLE) + 1):
            if body[start : start + SHINGLE] in text:
                found.append(response.id)
                break
    return found


@pytest.fixture(scope="module")
def corpus_json(tmp_path_factory: pytest.TempPathFactory) -> Path:
    path = tmp_path_factory.mktemp("cliviews-corpus") / "corpus.json"
    write_corpus_json(synthetic_corpus(), path)
    return path


@pytest.fixture(scope="module")
def run(tmp_path_factory: pytest.TempPathFactory, corpus_json: Path) -> Path:
    """`gaf run` then `gaf analyse` into `<run>/analysis`, then `gaf report`."""
    base = tmp_path_factory.mktemp("cliviews")
    out = base / "run"
    assert (
        main(
            [
                "run",
                "--corpus",
                str(corpus_json),
                "--run-id",
                "cliviews",
                "--out",
                str(out),
                "--cache-dir",
                str(base / "cache"),
            ]
        )
        == EXIT_OK
    )
    assert (
        main(
            [
                "analyse",
                "--assignments",
                str(out / "assignments.json"),
                "--data",
                str(corpus_json),
                "--out",
                str(out / "analysis"),
            ]
        )
        == EXIT_OK
    )
    assert main(["report", "--run", str(out)]) == EXIT_OK
    return out


@pytest.fixture
def coding_paths(tmp_path: Path) -> tuple[Path, Path]:
    """A hand coding on disk: assignment rows, and the codebook they belong to."""
    assignments = tmp_path / "golden.json"
    assignments.write_text(
        json.dumps([row.to_json() for row in human_assignments()], indent=2), encoding="utf-8"
    )
    codebook = tmp_path / "codebook.json"
    codebook.write_text(toy_codebook().to_json_str(), encoding="utf-8")
    return assignments, codebook


# --------------------------------------------------------------------------- #
# 1-3. `gaf analyse`
# --------------------------------------------------------------------------- #


def test_analyse_writes_the_three_further_readings(run: Path):
    analysis = run / "analysis"
    for name in (*OLD_ANALYSIS_ARTEFACTS, *NEW_ANALYSIS_ARTEFACTS):
        assert (analysis / name).exists(), name
    patterns = json.loads((analysis / "patterns.json").read_text(encoding="utf-8"))
    assert {"responses", "groups", "combinations", "family_cooccurrence"} <= set(patterns)
    affinity = json.loads((analysis / "affinity.json").read_text(encoding="utf-8"))
    assert {"groups", "similarity", "cross_family_subcodes"} <= set(affinity)
    growth = json.loads((analysis / "growth.json").read_text(encoding="utf-8"))
    assert growth["points"] and growth["points"][0]["batch"] == 1, "batches are 1-based"


def test_analyse_says_when_affinity_ran_on_names_alone(
    run: Path, corpus_json: Path, tmp_path: Path, capsys
):
    out = tmp_path / "names-only"
    assert (
        main(
            [
                "analyse",
                "--assignments",
                str(run / "assignments.json"),
                "--data",
                str(corpus_json),
                "--out",
                str(out),
            ]
        )
        == EXIT_OK
    )
    assert "names-only" in (out / "affinity.md").read_text(encoding="utf-8")
    assert "no codebook with descriptions was supplied" in capsys.readouterr().out


def test_analyse_uses_the_descriptions_a_codebook_supplies(
    run: Path, corpus_json: Path, tmp_path: Path
):
    out = tmp_path / "described"
    assert (
        main(
            [
                "analyse",
                "--assignments",
                str(run / "assignments.json"),
                "--data",
                str(corpus_json),
                "--out",
                str(out),
                "--codebook",
                str(run / "codebook.json"),
            ]
        )
        == EXIT_OK
    )
    assert "names-only" not in (out / "affinity.md").read_text(encoding="utf-8")


def test_analyse_writes_a_crosswalk_only_when_a_target_is_named(
    run: Path, corpus_json: Path, tmp_path: Path, coding_paths: tuple[Path, Path]
):
    _, target = coding_paths
    without = tmp_path / "no-crosswalk"
    assert (
        main(
            [
                "analyse",
                "--assignments",
                str(run / "codebook.json"),
                "--data",
                str(corpus_json),
                "--out",
                str(without),
            ]
        )
        == EXIT_OK
    )
    assert not (without / "crosswalk.json").exists()

    with_target = tmp_path / "crosswalk"
    assert (
        main(
            [
                "analyse",
                "--assignments",
                str(run / "codebook.json"),
                "--data",
                str(corpus_json),
                "--out",
                str(with_target),
                "--crosswalk-target",
                str(target),
            ]
        )
        == EXIT_OK
    )
    crosswalk = json.loads((with_target / "crosswalk.json").read_text(encoding="utf-8"))
    assert crosswalk["mappings"]
    assert {"source_family_rollup", "unmapped_target_leaves", "fair_mode_note"} <= set(crosswalk)
    assert crosswalk["names_only"] is False
    assert "Crosswalk" in (with_target / "crosswalk.md").read_text(encoding="utf-8")


def test_the_crosswalk_can_be_asked_for_the_fair_names_only_comparison(
    run: Path, tmp_path: Path, coding_paths: tuple[Path, Path]
):
    _, target = coding_paths
    out = tmp_path / "fair"
    assert (
        main(
            [
                "analyse",
                "--assignments",
                str(run / "codebook.json"),
                "--out",
                str(out),
                "--crosswalk-target",
                str(target),
                "--crosswalk-names-only",
            ]
        )
        == EXIT_OK
    )
    assert json.loads((out / "crosswalk.json").read_text(encoding="utf-8"))["names_only"] is True


def test_analyse_is_byte_identical_across_two_runs(run: Path, corpus_json: Path, tmp_path: Path):
    outputs = []
    for label in ("first", "second"):
        out = tmp_path / label
        assert (
            main(
                [
                    "analyse",
                    "--assignments",
                    str(run / "assignments.json"),
                    "--data",
                    str(corpus_json),
                    "--out",
                    str(out),
                ]
            )
            == EXIT_OK
        )
        outputs.append(out)
    first, second = outputs
    for name in (*OLD_ANALYSIS_ARTEFACTS, *NEW_ANALYSIS_ARTEFACTS):
        assert (first / name).read_bytes() == (second / name).read_bytes(), name


def test_the_new_readings_survive_a_matrix_too_degenerate_to_cluster(tmp_path: Path):
    """None of the three needs a partition, so none of them is lost when one fails."""
    rows = [Assignment(203, "invented segment", "solo_family-solo_code")]
    path = tmp_path / "tiny.json"
    path.write_text(json.dumps([row.to_json() for row in rows]), encoding="utf-8")
    out = tmp_path / "tiny-analysis"
    assert main(["analyse", "--assignments", str(path), "--out", str(out)]) == EXIT_OK
    assert not (out / "clusters.json").exists(), "the matrix must really be degenerate"
    for name in NEW_ANALYSIS_ARTEFACTS:
        assert (out / name).exists(), name


def test_analyse_accepts_a_codebook_artefact_with_no_corpus(run: Path, tmp_path: Path):
    out = tmp_path / "codebook-only"
    assert main(["analyse", "--assignments", str(run / "codebook.json"), "--out", str(out)]) == EXIT_OK
    for name in NEW_ANALYSIS_ARTEFACTS:
        assert (out / name).exists(), name


# --------------------------------------------------------------------------- #
# 4. `gaf report`
# --------------------------------------------------------------------------- #


def test_report_writes_the_timeline_the_trail_the_matrix_and_the_views_page(run: Path):
    for name in NEW_REPORT_ARTEFACTS:
        assert (run / name).exists(), name
    timeline = json.loads((run / "timeline.json").read_text(encoding="utf-8"))
    assert timeline["batches"] and timeline["batches"][0]["batch"] == 1
    trail = json.loads((run / "reorganisation_trail.json").read_text(encoding="utf-8"))
    assert trail["run_id"] == "cliviews"
    assert "<svg" in (run / "timeline.svg").read_text(encoding="utf-8")
    assert "flowchart LR" in (run / TREE_MMD_NAME).read_text(encoding="utf-8")


def test_report_still_renders_the_two_artefacts_it_always_did(run: Path, tmp_path: Path):
    out = tmp_path / "rendered"
    assert main(["report", "--run", str(run), "--out", str(out)]) == EXIT_OK
    assert (out / "report.txt").read_bytes() == (run / "report.txt").read_bytes()
    assert (out / "codebook.html").read_bytes() == (run / "codebook.html").read_bytes()
    assert (out / VIEWS_HTML_NAME).exists()


def test_the_codebook_explorer_links_across_to_the_views_page(run: Path):
    page = (run / "codebook.html").read_text(encoding="utf-8")
    assert f'<a href="{VIEWS_HTML_NAME}">{VIEWS_HTML_NAME}</a>' in page
    assert "carries no respondent text" in page
    assert "http://" not in page and "https://" not in page


def test_the_views_page_report_writes_is_deterministic(run: Path, tmp_path: Path):
    first = tmp_path / "a"
    second = tmp_path / "b"
    for out in (first, second):
        assert main(["report", "--run", str(run), "--out", str(out)]) == EXIT_OK
    assert (first / VIEWS_HTML_NAME).read_bytes() == (second / VIEWS_HTML_NAME).read_bytes()
    assert (first / TREE_MMD_NAME).read_bytes() == (second / TREE_MMD_NAME).read_bytes()


# --------------------------------------------------------------------------- #
# 5. `gaf views`
# --------------------------------------------------------------------------- #


def test_views_builds_the_page_for_a_run(run: Path, tmp_path: Path, capsys):
    out = tmp_path / "standalone.html"
    assert run_views("views", "--run", str(run), "--out", str(out)) == EXIT_OK
    page = out.read_text(encoding="utf-8")
    for anchor, _ in VIEWS:
        assert f'id="{anchor}"' in page
    assert (out.parent / TREE_MMD_NAME).exists()
    stdout = capsys.readouterr().out
    assert "gaf views" in stdout
    assert "Codebook tree" in stdout and "drawn" in stdout


def test_views_defaults_to_the_run_directory(run: Path):
    (run / VIEWS_HTML_NAME).unlink()
    assert run_views("views", "--run", str(run)) == EXIT_OK
    assert (run / VIEWS_HTML_NAME).exists()


def test_views_accepts_a_directory_as_out(run: Path, tmp_path: Path):
    target = tmp_path / "pages"
    target.mkdir()
    assert run_views("views", "--run", str(run), "--out", str(target)) == EXIT_OK
    assert (target / VIEWS_HTML_NAME).exists()
    assert (target / TREE_MMD_NAME).exists()


def test_views_reads_an_analysis_directory_written_elsewhere(
    run: Path, corpus_json: Path, tmp_path: Path
):
    elsewhere = tmp_path / "elsewhere"
    assert (
        main(
            [
                "analyse",
                "--assignments",
                str(run / "assignments.json"),
                "--data",
                str(corpus_json),
                "--out",
                str(elsewhere),
                "--min-frequency",
                "1",
            ]
        )
        == EXIT_OK
    )
    out = tmp_path / "with-analysis.html"
    assert (
        run_views("views", "--run", str(run), "--analysis", str(elsewhere), "--out", str(out))
        == EXIT_OK
    )
    page = out.read_text(encoding="utf-8")
    assert str(elsewhere) in page
    assert "Top code pairs" in page


def test_views_builds_a_page_for_a_coding_with_no_run_behind_it(
    coding_paths: tuple[Path, Path], corpus_json: Path, tmp_path: Path, capsys
):
    assignments, codebook = coding_paths
    out = tmp_path / "coding.html"
    assert (
        run_views(
            "views",
            "--assignments",
            str(assignments),
            "--codebook",
            str(codebook),
            "--data",
            str(corpus_json),
            "--out",
            str(out),
        )
        == EXIT_OK
    )
    page = out.read_text(encoding="utf-8")
    assert "human coding golden.json" in page
    assert "audit log" in page and "this is a coding, not a run" in page
    # The two views that need an audit log say which command writes one; the rest draw.
    assert "gaf run --corpus" in page
    assert "gaf report --run" in page
    assert leaks(page) == []
    stdout = capsys.readouterr().out
    assert "Reorganisation trail" in stdout and "not available" in stdout


def test_views_without_a_codebook_still_draws_the_tree(
    coding_paths: tuple[Path, Path], tmp_path: Path
):
    assignments, _ = coding_paths
    out = tmp_path / "bare.html"
    assert run_views("views", "--assignments", str(assignments), "--out", str(out)) == EXIT_OK
    page = out.read_text(encoding="utf-8")
    assert 'id="codebook-tree"' in page
    assert "positive_impacts" in page


def test_views_needs_exactly_one_of_run_and_assignments(run: Path, tmp_path: Path, capsys):
    assert run_views("views") == EXIT_USAGE
    assert "exactly one" in capsys.readouterr().err
    assert (
        run_views("views", "--run", str(run), "--assignments", str(run / "assignments.json"))
        == EXIT_USAGE
    )
    assert "exactly one" in capsys.readouterr().err


def test_views_refuses_a_directory_that_is_not_a_run(tmp_path: Path, capsys):
    assert run_views("views", "--run", str(tmp_path)) != EXIT_OK
    assert "does not exist" in capsys.readouterr().err


def test_views_survives_a_run_with_no_analysis_directory(
    tmp_path_factory: pytest.TempPathFactory, corpus_json: Path, tmp_path: Path
):
    base = tmp_path_factory.mktemp("unanalysed")
    out = base / "run"
    assert (
        main(
            [
                "run",
                "--corpus",
                str(corpus_json),
                "--run-id",
                "unanalysed",
                "--out",
                str(out),
                "--cache-dir",
                str(base / "cache"),
            ]
        )
        == EXIT_OK
    )
    page_path = tmp_path / "unanalysed.html"
    assert run_views("views", "--run", str(out), "--out", str(page_path)) == EXIT_OK
    page = page_path.read_text(encoding="utf-8")
    assert "gaf analyse --assignments" in page
    for anchor, _ in VIEWS:
        assert f'id="{anchor}"' in page


# --------------------------------------------------------------------------- #
# 6. No respondent text, through every path
# --------------------------------------------------------------------------- #


def test_no_respondent_text_reaches_views_html_from_a_run(run: Path):
    assert leaks((run / VIEWS_HTML_NAME).read_text(encoding="utf-8")) == []
    assert leaks((run / TREE_MMD_NAME).read_text(encoding="utf-8")) == []


def test_the_codebook_explorer_does_carry_respondent_text(run: Path):
    """The control on the test above: the two pages differ, and differ on purpose."""
    assert leaks((run / "codebook.html").read_text(encoding="utf-8")) != []


def test_the_views_page_is_self_contained_through_the_cli(run: Path):
    page = (run / VIEWS_HTML_NAME).read_text(encoding="utf-8")
    assert "http" not in page
    assert "<script" not in page.lower()
    assert "url(" not in page and "@import" not in page


def test_report_says_so_when_a_run_directory_has_no_store(
    run: Path, tmp_path: Path, capsys
):
    """A run directory copied without gaf.sqlite loses two artefacts, not the command."""
    copy = tmp_path / "no-store"
    copy.mkdir()
    (copy / "run.json").write_text((run / "run.json").read_text(encoding="utf-8"), encoding="utf-8")
    assert main(["report", "--run", str(copy)]) == EXIT_OK
    assert not (copy / "timeline.json").exists()
    assert not (copy / "reorganisation_trail.json").exists()
    assert (copy / VIEWS_HTML_NAME).exists()
    assert "has no readable" in capsys.readouterr().out
