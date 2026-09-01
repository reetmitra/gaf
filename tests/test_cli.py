"""Wave 3 gate for the CLI, the run report and the HTML codebook explorer (C2).

Twelve claims, each of them something a reader or a reviewer depends on:

1. **`make demo`'s underlying commands run end to end offline** and write every
   artefact a later command reads: the codebook, the assignments, the findings, the
   audit log, the blackboard, the run report and the explorer.
2. **Determinism.** Two independent runs of the same corpus produce byte-identical
   codebook JSON and an identical snapshot-id sequence — acceptance criterion 3,
   asserted through the CLI rather than through the loop's own API.
3. **`gaf check` exits 1 if and only if an ERROR was found**, in both directions and
   in both artefact shapes: the pipeline's codebook JSON and the row-oriented
   assignments a coding spreadsheet produces.
4. **A WARN-only artefact exits 0.** This is the half people get wrong: a WARN is a
   judgment about meaning, it is kept and flagged, and it never fails a command.
5. **`gaf validate lexical` refuses an unfittable cut with a message that explains
   itself**, and never fails on low Jaccard overlap — low overlap is a finding.
6. **`gaf validate agreement` reports both levels and both unmatched lists**, which
   are the interpretive output the headline rate hides.
7. **The run report carries a CHECKS section and the caveats**, so 166 offline M3
   warnings can never be read as substance (ADR-0019, ADR-0022).
7b. **A run exits 0 even when its checks found ERRORs.** The two command families have
   different exit-code semantics on purpose: `gaf check` answers "is this artefact
   valid?" and a CI pipeline should fail on that; `gaf run` answers "what did the
   coders propose and what did the checks find?", and findings are its deliverable.
   The synthetic corpus carries planted violations precisely so the drop paths run
   offline, so conflating the two would mean the pipeline could never be demonstrated
   on any corpus containing a single unverifiable quote — which is every real corpus.
8. **The explorer is deterministic, self-contained and escapes hostile text.**
9. **No output uses framing-analysis vocabulary** (ADR-0005), across every help
   string, the run report, the explorer and the commands' own stdout.
10. **The live component builder fails clearly without an SDK or a key**, and is never
    allowed to construct a real client here: no network, no key, no provider SDK.
11. **A checkpoint with no human present is a no-op**, never an auto-accept (ADR-0004).
12. **Bad input is refused by name**, with the exit code that says which kind of
    failure it was.

Every test is offline: mock clients, the lexical embedding fallback, the invented
corpus of `tests.fixtures.corpus`, and no real survey response anywhere.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from gaf.cli import (
    EXIT_FINDINGS,
    EXIT_INPUT,
    EXIT_OK,
    EXIT_USAGE,
    CliError,
    build_parser,
    live_components,
    load_artefact,
    main,
)
from gaf.config import DEFAULT_LIVE_REGISTRY, ModelRegistry, ModelSpec, RunConfig
from gaf.ingest.corpus import write_corpus_json
from gaf.models import Assignment, Code, Codebook, Evidence
from gaf.report.html import render_codebook_html
from gaf.report.run_report import RUN_JSON_NAME, RunArtefact, render_run_report
from tests.fixtures.assignments import human_assignments, machine_assignments
from tests.fixtures.codebooks import broken_codebook, toy_codebook
from tests.fixtures.corpus import (
    FABRICATED_QUOTE,
    MOCKFIT_UNNECESSARY,
    RAW_RESPONSES,
    synthetic_corpus,
)
from tests.fixtures.scored import synthetic_scored_table
from tests.fixtures.xlsx import write_narrative_state_xlsx

#: ADR-0005. This study is inductive grounded theory; the word must not reach a reader.
FORBIDDEN_VOCABULARY = ("frame", "framing", "frame element")

#: The response carrying the sentinel the mock judge rules UNNECESSARY on.
SENTINEL_RESPONSE = 231

#: Every artefact `gaf run` promises to leave behind.
RUN_ARTEFACTS = (
    RUN_JSON_NAME,
    "codebook.json",
    "assignments.json",
    "findings.json",
    "stats.json",
    "audit.jsonl",
    "report.txt",
    "gaf.sqlite",
)


# --------------------------------------------------------------------------- #
# Helpers and fixtures
# --------------------------------------------------------------------------- #


def write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def write_assignments(path: Path, rows: list[Assignment]) -> Path:
    return write_json(path, [row.to_json() for row in rows])


def write_codebook(path: Path, codebook: Codebook) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(codebook.to_json_str(), encoding="utf-8")
    return path


def flat(text: str) -> str:
    """Collapse whitespace, so an assertion is not hostage to where a line wrapped."""
    return " ".join(text.split())


def run_cli(*argv: str) -> int:
    """`gaf ...` in-process, returning the exit code the console script would."""
    return main(list(argv))


@pytest.fixture(scope="module")
def corpus_json(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """The synthetic corpus on disk — the only corpus these tests are allowed."""
    path = tmp_path_factory.mktemp("corpus") / "corpus.json"
    write_corpus_json(synthetic_corpus(), path)
    return path


@pytest.fixture(scope="module")
def demo(tmp_path_factory: pytest.TempPathFactory, corpus_json: Path) -> Path:
    """What `make demo` does: `gaf run` then `gaf report`, offline, on the synthetic corpus."""
    out = tmp_path_factory.mktemp("demo") / "run"
    assert run_cli(
        "run",
        "--corpus",
        str(corpus_json),
        "--run-id",
        "demo",
        "--offline",
        "--out",
        str(out),
        "--cache-dir",
        str(out.parent / "cache"),
    ) == EXIT_OK
    assert run_cli("report", "--run", str(out)) == EXIT_OK
    return out


@pytest.fixture(scope="module")
def demo_artefact(demo: Path) -> RunArtefact:
    return RunArtefact.from_json(json.loads((demo / RUN_JSON_NAME).read_text(encoding="utf-8")))


@pytest.fixture
def clean_codebook_path(tmp_path: Path) -> Path:
    return write_codebook(tmp_path / "toy.json", toy_codebook())


@pytest.fixture
def broken_codebook_path(tmp_path: Path) -> Path:
    return write_codebook(tmp_path / "broken.json", broken_codebook())


@pytest.fixture
def clean_assignments_path(tmp_path: Path) -> Path:
    """The human golden set: WARNs (no descriptions, few codes) but no ERROR."""
    return write_assignments(tmp_path / "human.json", human_assignments())


@pytest.fixture
def fabricated_assignments_path(tmp_path: Path) -> Path:
    """The same spreadsheet with one quote that occurs in no response: an S2 ERROR."""
    rows = [*human_assignments(), Assignment(203, FABRICATED_QUOTE, "future-invented")]
    return write_assignments(tmp_path / "fabricated.json", rows)


# --------------------------------------------------------------------------- #
# 1. The demo runs end to end and writes what it promises
# --------------------------------------------------------------------------- #


def test_demo_writes_every_artefact(demo: Path):
    for name in RUN_ARTEFACTS:
        assert (demo / name).exists(), f"gaf run did not write {name}"
    assert (demo / "codebook.html").exists()


def test_demo_codebook_and_assignments_are_populated(demo: Path, demo_artefact: RunArtefact):
    codebook = json.loads((demo / "codebook.json").read_text(encoding="utf-8"))
    assert len(codebook["codes"]) == len(demo_artefact.codebook)
    assert len(demo_artefact.codebook) > 0
    assert demo_artefact.stats.families_final > 1
    assignments = json.loads((demo / "assignments.json").read_text(encoding="utf-8"))
    assert assignments and set(assignments[0]) == {"response_id", "segment", "code"}


def test_demo_audit_log_is_a_line_per_event(demo: Path):
    lines = [
        line for line in (demo / "audit.jsonl").read_text(encoding="utf-8").splitlines() if line
    ]
    events = [json.loads(line) for line in lines]
    names = {event["event"] for event in events}
    assert {"run_started", "run_completed", "snapshot_frozen"} <= names
    assert all(event["run_id"] == "demo" for event in events)


def test_demo_findings_round_trip_through_the_contract(demo: Path, demo_artefact: RunArtefact):
    findings = json.loads((demo / "findings.json").read_text(encoding="utf-8"))
    assert len(findings) == len(demo_artefact.report)
    assert all({"check_id", "severity", "scope", "subject", "message"} <= set(f) for f in findings)


# --------------------------------------------------------------------------- #
# 2. Determinism — acceptance criterion 3, through the CLI
# --------------------------------------------------------------------------- #


def test_two_runs_produce_byte_identical_codebook_and_snapshots(tmp_path: Path, corpus_json: Path):
    outputs = []
    for label in ("first", "second"):
        out = tmp_path / label
        assert run_cli(
            "run",
            "--corpus",
            str(corpus_json),
            "--run-id",
            "determinism",
            "--out",
            str(out),
            "--cache-dir",
            str(tmp_path / "cache" / label),
        ) == EXIT_OK
        outputs.append(out)

    first, second = outputs
    assert (first / "codebook.json").read_bytes() == (second / "codebook.json").read_bytes()
    assert (first / "assignments.json").read_bytes() == (second / "assignments.json").read_bytes()
    assert (first / "findings.json").read_bytes() == (second / "findings.json").read_bytes()

    def snapshots(run_dir: Path) -> list[str]:
        document = json.loads((run_dir / RUN_JSON_NAME).read_text(encoding="utf-8"))
        return list(document["result"]["snapshot_ids"])

    assert snapshots(first) == snapshots(second)
    assert len(snapshots(first)) >= 2


def test_the_run_report_itself_is_deterministic(tmp_path: Path, corpus_json: Path):
    """No wall-clock anywhere in the report: two runs render the same bytes.

    `--no-cache` on both, because a warm response cache legitimately changes one line
    of the accounting (`cache hits`) — that is the cache being reported honestly, not
    the report being non-deterministic.
    """
    out = tmp_path / "det"
    texts = []
    for _ in range(2):
        assert run_cli(
            "run", "--corpus", str(corpus_json), "--run-id", "det", "--out", str(out),
            "--no-cache",
        ) == EXIT_OK
        texts.append((out / "report.txt").read_text(encoding="utf-8"))
    assert texts[0] == texts[1]


# --------------------------------------------------------------------------- #
# 3. `gaf check` exits 1 iff an ERROR was found — both shapes, both directions
# --------------------------------------------------------------------------- #


def test_structural_passes_a_clean_codebook(clean_codebook_path: Path, corpus_json: Path, capsys):
    assert run_cli(
        "check", "structural", "--codebook", str(clean_codebook_path), "--data", str(corpus_json)
    ) == EXIT_OK
    assert "RESULT: PASS" in capsys.readouterr().out


def test_structural_fails_a_codebook_with_a_planted_error(broken_codebook_path: Path, capsys):
    assert run_cli("check", "structural", "--codebook", str(broken_codebook_path)) == EXIT_FINDINGS
    out = flat(capsys.readouterr().out)
    assert "ERROR finding(s)" in out
    assert "The artefact is structurally invalid where they point" in out
    assert "S6" in out
    assert "share the name" in out


def test_structural_passes_a_clean_assignments_file(
    clean_assignments_path: Path, corpus_json: Path, capsys
):
    assert run_cli(
        "check", "structural", "--assignments", str(clean_assignments_path), "--data", str(corpus_json)
    ) == EXIT_OK
    assert "RESULT: PASS" in capsys.readouterr().out


def test_structural_fails_assignments_with_a_fabricated_quote(
    fabricated_assignments_path: Path, corpus_json: Path, capsys
):
    assert run_cli(
        "check",
        "structural",
        "--assignments",
        str(fabricated_assignments_path),
        "--data",
        str(corpus_json),
    ) == EXIT_FINDINGS
    out = capsys.readouterr().out
    assert "ERROR finding(s)" in out
    assert "S2" in out


def test_semantic_passes_a_clean_codebook(clean_codebook_path: Path, corpus_json: Path, capsys):
    assert run_cli(
        "check", "semantic", "--codebook", str(clean_codebook_path), "--data", str(corpus_json)
    ) == EXIT_OK
    out = capsys.readouterr().out
    assert "RESULT: PASS" in out
    assert "M3 code-to-evidence fit" in out


def test_semantic_fails_when_every_quote_of_a_code_is_ruled_unnecessary(
    tmp_path: Path, corpus_json: Path, capsys
):
    code = Code(
        id="c-sentinel",
        name="applications-assistant",
        description="A personal assistant that knows a health history.",
        evidence=[
            Evidence(
                response_id=SENTINEL_RESPONSE,
                quote=MOCKFIT_UNNECESSARY,
                verified=True,
                score=1.0,
            )
        ],
    )
    path = write_codebook(tmp_path / "unnecessary.json", Codebook(codes={code.id: code}))
    assert run_cli(
        "check", "semantic", "--codebook", str(path), "--data", str(corpus_json)
    ) == EXIT_FINDINGS
    out = capsys.readouterr().out
    assert "ERROR finding(s)" in out
    assert "UNNECESSARY" in out


def test_semantic_fails_on_the_assignments_shape_too(tmp_path: Path, corpus_json: Path):
    path = write_assignments(
        tmp_path / "sentinel.json",
        [Assignment(SENTINEL_RESPONSE, MOCKFIT_UNNECESSARY, "applications-assistant")],
    )
    assert run_cli(
        "check", "semantic", "--assignments", str(path), "--data", str(corpus_json)
    ) == EXIT_FINDINGS


def test_check_all_runs_both_layers(demo: Path, corpus_json: Path, capsys):
    assert run_cli(
        "check", "all", "--codebook", str(demo / "codebook.json"), "--data", str(corpus_json)
    ) == EXIT_OK
    out = capsys.readouterr().out
    assert "structural checks run" in out
    assert "M4 near-duplicate leaves" in out


def test_check_writes_findings_when_asked(broken_codebook_path: Path, tmp_path: Path):
    target = tmp_path / "findings.json"
    run_cli(
        "check", "structural", "--codebook", str(broken_codebook_path), "--out", str(target)
    )
    findings = json.loads(target.read_text(encoding="utf-8"))
    assert any(f["severity"] == "ERROR" for f in findings)


def test_check_names_the_checks_it_could_not_run_without_a_corpus(
    clean_assignments_path: Path, capsys
):
    """A check that cannot see its subject must not pretend to have passed."""
    assert run_cli("check", "structural", "--assignments", str(clean_assignments_path)) == EXIT_OK
    out = capsys.readouterr().out
    assert "structural skipped" in out
    for check in ("S2", "S4", "S5"):
        assert check in out


# --------------------------------------------------------------------------- #
# 4. A WARN-only artefact exits 0
# --------------------------------------------------------------------------- #


def test_warn_only_artefact_exits_zero(tmp_path: Path, capsys):
    """S6 WARNs on an empty description and a three-deep chain; no ERROR anywhere."""
    codes = [
        Code(id="c-root", name="future", description="How the future is characterised."),
        Code(
            id="c-mid",
            name="future-uncertainty",
            description="",  # WARN: a code without a description is not yet a code
            parent_id="c-root",
        ),
        Code(
            id="c-deep",
            name="future-uncertainty-timing",
            description="Uncertainty about when.",  # WARN: deeper than two levels
            parent_id="c-mid",
        ),
    ]
    path = write_codebook(tmp_path / "warnings.json", Codebook(codes={c.id: c for c in codes}))
    assert run_cli("check", "structural", "--codebook", str(path)) == EXIT_OK
    out = capsys.readouterr().out
    assert "RESULT: PASS" in out
    assert "WARN findings by check" in out


def test_the_human_golden_set_warns_but_never_fails(clean_assignments_path: Path, corpus_json: Path, capsys):
    assert run_cli(
        "check", "structural", "--assignments", str(clean_assignments_path), "--data", str(corpus_json)
    ) == EXIT_OK
    out = capsys.readouterr().out
    assert "WARN" in out
    assert "RESULT: PASS" in out


# --------------------------------------------------------------------------- #
# 5. Lexical validation: a refused fit explains itself; low overlap never fails
# --------------------------------------------------------------------------- #


def test_lexical_refuses_an_unfittable_cut_with_a_message_that_explains_itself(
    demo: Path, corpus_json: Path, capsys
):
    """The real seed sample's own case: 14 responses cannot support a binarised cut."""
    assert run_cli(
        "validate",
        "lexical",
        "--table",
        str(corpus_json),
        "--score-from",
        "codes",
        "--codebook",
        str(demo / "codebook.json"),
    ) == EXIT_FINDINGS
    out = flat(capsys.readouterr().out)
    assert "REFUSED" in out
    assert "refusing to fit the ge1 cut" in out
    assert "min_class_count" in out
    assert "This is a verdict about the data, not a crash" in out


def fittable_rows() -> list[dict[str, Any]]:
    """A balanced subsample: both binarised cuts clear `min_class_count` comfortably."""
    table = synthetic_scored_table()
    picked: list[dict[str, Any]] = []
    for score, wanted in ((0, 15), (1, 15), (3, 15)):
        picked.extend(
            row.to_dict() for row in [r for r in table if r.score == score][:wanted]
        )
    return picked


def test_lexical_succeeds_on_a_fittable_table_and_does_not_fail_on_low_overlap(
    tmp_path: Path, capsys
):
    path = write_json(tmp_path / "table.json", fittable_rows())
    assert run_cli("validate", "lexical", "--table", str(path), "--bootstrap", "1") == EXIT_OK
    out = flat(capsys.readouterr().out)
    assert "Jaccard overlap of top-20 vocabularies" in out
    assert "Low overlap between the vocabularies is a finding to report" in out


def test_lexical_writes_its_artefacts(tmp_path: Path):
    path = write_json(tmp_path / "table.json", fittable_rows())
    out = tmp_path / "lex"
    assert run_cli(
        "validate", "lexical", "--table", str(path), "--bootstrap", "1", "--out", str(out)
    ) == EXIT_OK
    for name in ("lexical.json", "lexical.md", "lexical_methods.txt"):
        assert (out / name).exists()


def test_lexical_refuses_a_malformed_table(tmp_path: Path, capsys):
    path = write_json(tmp_path / "bad.json", [{"response_id": 1, "text": "x", "score": -3}])
    assert run_cli("validate", "lexical", "--table", str(path)) == EXIT_INPUT
    assert "gaf:" in capsys.readouterr().err


def test_score_from_a_family_needs_a_codebook(tmp_path: Path, capsys):
    path = write_json(tmp_path / "table.json", fittable_rows())
    assert run_cli(
        "validate", "lexical", "--table", str(path), "--score-from", "code-family:future"
    ) == EXIT_USAGE
    assert "--codebook" in capsys.readouterr().err


# --------------------------------------------------------------------------- #
# 6. Agreement: both levels, and both unmatched lists
# --------------------------------------------------------------------------- #


def test_agreement_reports_both_levels_and_both_unmatched_lists(
    tmp_path: Path, corpus_json: Path, clean_codebook_path: Path, capsys
):
    human = write_assignments(tmp_path / "human.json", human_assignments())
    machine = write_assignments(tmp_path / "machine.json", machine_assignments())
    assert run_cli(
        "validate",
        "agreement",
        "--human",
        str(human),
        "--machine",
        str(machine),
        "--data",
        str(corpus_json),
        "--codebook",
        str(clean_codebook_path),
    ) == EXIT_OK
    out = capsys.readouterr().out
    assert "### Code level" in out
    assert "### Segment level" in out
    assert "Cohen's kappa" in out
    assert "Over-coding" in out
    assert "Blind spots" in out
    # The two fixture lists are non-empty by construction, and both must show up.
    assert "future-inevitability" in out
    assert "negative_impacts-lack_of_inclusion" in out
    assert "right code, wrong place" in out


def test_agreement_says_when_the_segment_level_had_to_degrade(tmp_path: Path, capsys):
    human = write_assignments(tmp_path / "human.json", human_assignments())
    machine = write_assignments(tmp_path / "machine.json", machine_assignments())
    assert run_cli(
        "validate", "agreement", "--human", str(human), "--machine", str(machine)
    ) == EXIT_OK
    assert "string containment" in capsys.readouterr().out


def test_agreement_writes_its_artefacts(tmp_path: Path, corpus_json: Path):
    human = write_assignments(tmp_path / "human.json", human_assignments())
    machine = write_assignments(tmp_path / "machine.json", machine_assignments())
    out = tmp_path / "agreement"
    assert run_cli(
        "validate", "agreement", "--human", str(human), "--machine", str(machine),
        "--data", str(corpus_json), "--out", str(out),
    ) == EXIT_OK
    assert (out / "agreement.json").exists()
    assert (out / "agreement.md").exists()


# --------------------------------------------------------------------------- #
# 7. The run report: a CHECKS section, and the caveats where a reader meets them
# --------------------------------------------------------------------------- #


def test_run_report_has_a_checks_section_with_counts_by_check_and_severity(demo: Path):
    text = (demo / "report.txt").read_text(encoding="utf-8")
    assert "CHECKS" in text
    assert "check  ERROR  WARN  INFO  total" in text
    assert "TOTAL" in text
    assert "RESULT:" in text


def test_run_report_prints_the_caveats_above_every_number(demo: Path):
    text = (demo / "report.txt").read_text(encoding="utf-8")
    assert "CAVEATS" in text
    assert "ADR-0019" in text
    assert "artefacts of the stand-in embedder" in flat(text)
    # Above, not buried: the caveats precede the coding statistics.
    assert text.index("CAVEATS") < text.index("CODING")
    assert text.index("CAVEATS") < text.index("CHECKS")


def test_run_report_annotates_the_offline_artefact_rows(demo: Path):
    text = (demo / "report.txt").read_text(encoding="utf-8")
    checks = text[text.index("CHECKS") :]
    for line in checks.splitlines():
        if line.strip().startswith(("M2 ", "M3 ")):
            assert "offline artefact" in line


def test_run_report_echoes_the_thresholds_and_the_provenance(demo: Path, demo_artefact: RunArtefact):
    text = (demo / "report.txt").read_text(encoding="utf-8")
    assert "CONFIGURATION" in text
    assert "tau_high 0.8" in text
    assert "tau_fit 0.3" in text
    assert "PROVENANCE" in text
    assert "corpus hash" in text
    assert demo_artefact.snapshot_ids[-1] in text


def test_run_report_carries_cost_latency_and_the_codebook_shape(demo: Path):
    text = (demo / "report.txt").read_text(encoding="utf-8")
    for label in (
        "MODEL CALLS",
        "cost (provider)",
        "latency (provider)",
        "candidates proposed",
        "agreement rate",
        "integration routes",
        "judge calls",
        "THEORETICAL SATURATION",
    ):
        assert label in text, label


def test_run_report_renders_the_same_from_the_result_and_from_run_json(
    demo: Path, demo_artefact: RunArtefact
):
    assert render_run_report(demo_artefact) == (demo / "report.txt").read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# 7b. A run reports findings; only a check turns one into a non-zero exit
# --------------------------------------------------------------------------- #


def test_the_demo_exits_zero_while_its_report_shows_errors(demo: Path, demo_artefact: RunArtefact):
    """`make demo` must stay green on a corpus with planted violations.

    The three ERRORs are deliberate fixture material, and a demo that produced none
    would be a worse demo, not a better one. Pinned here so nobody later "fixes" the
    demo by making it exit 1, or by sanitising the corpus.

    Where the three come from, after the ADR-0024 corpus rewrite:

    * **two M3 drops** of the `MOCKFIT_UNNECESSARY` sentinel. This one is structural:
      the sentinel is planted in exactly one response (231), the fast loop runs two
      coder personas over every response, and the mock judge rules UNNECESSARY on any
      quote containing it — so both personas' candidate loses its only evidence and is
      dropped. One sentinel x two coders = 2.
    * **one S2 drop** of the mock's own fabricated quote. Persona B appends a
      `future-superintelligence` candidate citing `gaf.llm.mock.FABRICATED_QUOTE` on a
      content-hash cadence of one response in `_B_FABRICATION_MODULUS` (6), so the
      count is a property of the corpus text rather than of the check layer: over these
      fourteen responses it fires once, where the pre-rewrite corpus happened to fire
      three times. The same count is pinned independently, and regenerated from the
      same offline run, in `tests/fixtures/golden/findings.json`.
    """
    severities = demo_artefact.report.totals()
    assert severities["ERROR"] == 3
    assert not demo_artefact.report.passed()

    by_marker: dict[tuple[str, str], int] = {}
    for finding in demo_artefact.report.errors():
        by_marker[(finding.check_id, str(finding.data.get("marker", "")))] = (
            by_marker.get((finding.check_id, str(finding.data.get("marker", ""))), 0) + 1
        )
    assert by_marker == {
        ("S2", "no_verified_evidence"): 1,
        ("M3", "candidate_dropped_no_evidence"): 2,
    }

    # The `demo` fixture already asserted EXIT_OK for both `gaf run` and `gaf report`.
    text = flat((demo / "report.txt").read_text(encoding="utf-8"))
    assert "3 ERROR finding(s)" in text
    assert "That is the layer working, not the run failing." in text
    assert "the run completed" in text


def test_a_rerun_of_the_demo_still_exits_zero(tmp_path: Path, corpus_json: Path):
    """The exit code answers "did the run complete", not "were there findings"."""
    out = tmp_path / "again"
    assert run_cli("run", "--corpus", str(corpus_json), "--out", str(out), "--no-cache") == EXIT_OK
    findings = json.loads((out / "findings.json").read_text(encoding="utf-8"))
    assert any(f["severity"] == "ERROR" for f in findings)


def test_analyse_exits_zero_on_an_artefact_whose_checks_would_fail(
    broken_codebook_path: Path, tmp_path: Path
):
    """`gaf analyse` is a run-family command: it exits non-zero only on a real failure."""
    assert run_cli(
        "analyse", "--assignments", str(broken_codebook_path), "--out", str(tmp_path / "an")
    ) in {EXIT_OK, EXIT_INPUT}
    assert run_cli("check", "structural", "--codebook", str(broken_codebook_path)) == EXIT_FINDINGS


def test_the_check_and_run_families_say_different_things_about_an_error(
    demo: Path, corpus_json: Path, capsys
):
    run_text = flat((demo / "report.txt").read_text(encoding="utf-8"))
    assert "only `gaf check` turns an ERROR into a non-zero exit" in run_text
    assert "`gaf run` exits 0 whenever the run completes" in run_text

    run_cli(
        "check", "structural", "--codebook", str(demo / "codebook.json"), "--data", str(corpus_json)
    )
    check_text = flat(capsys.readouterr().out)
    assert "the layer working, not the run failing" not in check_text


# --------------------------------------------------------------------------- #
# 8. The explorer: deterministic, self-contained, and escaped without exception
# --------------------------------------------------------------------------- #


def test_explorer_is_deterministic(demo_artefact: RunArtefact):
    assert render_codebook_html(demo_artefact) == render_codebook_html(demo_artefact)


def test_explorer_is_self_contained(demo: Path):
    page = (demo / "codebook.html").read_text(encoding="utf-8")
    assert "http://" not in page
    assert "https://" not in page
    assert "<script" not in page.lower()
    assert "<style>" in page


def test_explorer_is_navigable(demo: Path, demo_artefact: RunArtefact):
    import html as html_module

    page = (demo / "codebook.html").read_text(encoding="utf-8")
    assert 'id="summary"' in page
    assert 'id="checks"' in page
    for family in demo_artefact.codebook.families():
        assert f'id="family-{family.replace("_", "-")}"' in page
    for code in demo_artefact.codebook.sorted_codes():
        anchor = code.name.casefold().replace("_", "-")
        assert f'id="code-{anchor}"' in page
        assert f'href="#code-{anchor}"' in page
        assert html_module.escape(code.description, quote=True) in page


def test_explorer_shows_evidence_with_response_ids_and_spans(demo: Path, demo_artefact: RunArtefact):
    page = (demo / "codebook.html").read_text(encoding="utf-8")
    code = next(c for c in demo_artefact.codebook.sorted_codes() if c.evidence)
    evidence = code.evidence[0]
    assert f"response {evidence.response_id}" in page
    assert "characters" in page
    assert "locator score" in page


def test_explorer_carries_the_checks_summary_and_the_caveats(demo: Path):
    page = (demo / "codebook.html").read_text(encoding="utf-8")
    assert "Caveats" in page
    assert "ADR-0019" in page
    assert "what it checks" in page
    assert "TOTAL" in page


def test_explorer_escapes_hostile_text(tmp_path: Path, demo_artefact: RunArtefact):
    """Survey text is arbitrary respondent input. Nothing reaches the page unescaped."""
    hostile_name = 'future-<script>alert("x")</script>'
    hostile_quote = "AI & \"progress\" <b>will</b> change us — o'clock"
    code = Code(
        id="c-hostile",
        name=hostile_name,
        description="A description with <angle> brackets & an ampersand.",
        evidence=[Evidence(response_id=203, quote=hostile_quote, verified=True, score=1.0)],
    )
    artefact = RunArtefact(
        stats=demo_artefact.stats,
        codebook=Codebook(codes={code.id: code}),
        assignments=[Assignment(203, hostile_quote, hostile_name)],
        report=demo_artefact.report,
        snapshot_ids=demo_artefact.snapshot_ids,
    )
    page = render_codebook_html(artefact)
    assert "<script>alert" not in page
    assert "&lt;script&gt;alert" in page
    assert "AI &amp; &quot;progress&quot; &lt;b&gt;will&lt;/b&gt;" in page
    assert hostile_quote not in page


def test_explorer_handles_an_empty_codebook(demo_artefact: RunArtefact):
    artefact = RunArtefact(
        stats=demo_artefact.stats,
        codebook=Codebook(),
        assignments=[],
        report=demo_artefact.report,
        snapshot_ids=demo_artefact.snapshot_ids,
    )
    page = render_codebook_html(artefact)
    assert "The codebook is empty" in page
    assert page.rstrip().endswith("</html>")


# --------------------------------------------------------------------------- #
# 9. Vocabulary (ADR-0005)
# --------------------------------------------------------------------------- #


def all_help_text() -> str:
    """Every help string in the parser tree, including every subcommand's."""
    parser = build_parser()
    collected = [parser.format_help()]
    stack = [parser]
    while stack:
        node = stack.pop()
        for action in node._actions:
            choices = getattr(action, "choices", None)
            if isinstance(choices, dict):
                for child in choices.values():
                    collected.append(child.format_help())
                    stack.append(child)
    return "\n".join(collected)


def test_no_help_text_uses_framing_vocabulary():
    haystack = all_help_text().casefold()
    for word in FORBIDDEN_VOCABULARY:
        assert word not in haystack, f"CLI help text uses {word!r}"


def test_neither_report_module_uses_framing_vocabulary():
    import gaf.report.html
    import gaf.report.run_report

    for module in (gaf.report.run_report, gaf.report.html):
        source = Path(module.__file__).read_text(encoding="utf-8").casefold()
        for word in FORBIDDEN_VOCABULARY:
            assert word not in source, f"{Path(module.__file__).name} uses {word!r}"


def test_the_cli_module_does_not_use_framing_vocabulary():
    import gaf.cli

    source = Path(gaf.cli.__file__).read_text(encoding="utf-8").casefold()
    for word in FORBIDDEN_VOCABULARY:
        assert word not in source, f"gaf/cli.py uses {word!r}"


def test_the_run_report_and_the_explorer_never_say_it(demo: Path):
    for name in ("report.txt", "codebook.html"):
        haystack = (demo / name).read_text(encoding="utf-8").casefold()
        for word in FORBIDDEN_VOCABULARY:
            assert word not in haystack, f"{name} uses {word!r}"


def test_the_commands_stdout_never_says_it(
    demo: Path, corpus_json: Path, clean_codebook_path: Path, tmp_path: Path, capsys
):
    human = write_assignments(tmp_path / "human.json", human_assignments())
    machine = write_assignments(tmp_path / "machine.json", machine_assignments())
    run_cli("check", "all", "--codebook", str(clean_codebook_path), "--data", str(corpus_json))
    run_cli("analyse", "--assignments", str(demo / "assignments.json"), "--data", str(corpus_json), "--out", str(tmp_path / "an"))
    run_cli("validate", "agreement", "--human", str(human), "--machine", str(machine), "--data", str(corpus_json))
    run_cli("report", "--run", str(demo))
    captured = capsys.readouterr()
    haystack = (captured.out + captured.err).casefold()
    for word in FORBIDDEN_VOCABULARY:
        assert word not in haystack, f"command output uses {word!r}"


# --------------------------------------------------------------------------- #
# 10. The live component builder — clear failure, and never a real client
# --------------------------------------------------------------------------- #


def test_live_components_refuses_an_offline_config():
    with pytest.raises(CliError) as excinfo:
        live_components(RunConfig(offline=True))
    assert "offline" in str(excinfo.value)
    assert "offline_components" in str(excinfo.value)


def test_live_components_refuses_a_mock_bound_registry():
    """The default registry is the mock one, so a careless --live must fail loudly."""
    with pytest.raises(CliError) as excinfo:
        live_components(RunConfig(offline=False))
    message = str(excinfo.value)
    assert "mock provider" in message
    assert "DEFAULT_LIVE_REGISTRY" in message
    assert "coder_a" in message


def test_live_components_requires_two_different_coder_providers():
    same = ModelRegistry(
        coder_a=ModelSpec(provider="openai", model="a", role="coder_a"),
        coder_b=ModelSpec(provider="openai", model="b", role="coder_b"),
        judge=ModelSpec(provider="anthropic", model="c", role="judge"),
        refactorer=ModelSpec(provider="anthropic", model="d", role="refactorer"),
    )
    with pytest.raises(CliError) as excinfo:
        live_components(RunConfig(offline=False, models=same))
    assert "different providers" in str(excinfo.value)


def test_live_components_names_the_extra_or_the_key_it_needs(monkeypatch):
    """No SDK and no key: the error must say which, and must never reach the network."""
    for variable in ("OPENAI_API_KEY", "GOOGLE_API_KEY", "ANTHROPIC_API_KEY"):
        monkeypatch.delenv(variable, raising=False)
    with pytest.raises(CliError) as excinfo:
        live_components(RunConfig(offline=False, models=DEFAULT_LIVE_REGISTRY))
    message = str(excinfo.value)
    assert "coder_a" in message
    assert ("uv sync --extra openai" in message) or ("OPENAI_API_KEY" in message)


def test_a_live_run_fails_before_it_spends_anything(tmp_path: Path, corpus_json: Path, capsys, monkeypatch):
    for variable in ("OPENAI_API_KEY", "GOOGLE_API_KEY", "ANTHROPIC_API_KEY"):
        monkeypatch.delenv(variable, raising=False)
    assert run_cli(
        "run", "--corpus", str(corpus_json), "--live", "--out", str(tmp_path / "live")
    ) == EXIT_INPUT
    assert "gaf:" in capsys.readouterr().err
    assert not (tmp_path / "live" / "codebook.json").exists()


# --------------------------------------------------------------------------- #
# 11. The checkpoint: a no-op without a human, never an auto-accept
# --------------------------------------------------------------------------- #


def test_a_checkpoint_without_a_human_changes_nothing(demo: Path, capsys):
    pytest.importorskip(
        "gaf.pipeline.slow_loop", reason="the slow loop is agent C1's module"
    )
    before = (demo / "codebook.json").read_bytes()
    assert run_cli("checkpoint", "--run", str(demo)) == EXIT_OK
    out = flat(capsys.readouterr().out)
    assert "RejectAllGate" in out
    assert "never an auto-accept" in out
    assert (demo / "codebook.json").read_bytes() == before


def test_a_checkpoint_needs_a_run_directory(tmp_path: Path, capsys):
    assert run_cli("checkpoint", "--run", str(tmp_path)) == EXIT_INPUT
    assert "run.json" in capsys.readouterr().err


# --------------------------------------------------------------------------- #
# 12. Ingest, analyse, report, and refusing bad input by name
# --------------------------------------------------------------------------- #


def test_ingest_reads_a_workbook_into_the_canonical_corpus(tmp_path: Path, capsys):
    workbook = write_narrative_state_xlsx(tmp_path / "raw.xlsx", RAW_RESPONSES)
    target = tmp_path / "corpus.json"
    assert run_cli(
        "ingest", "--xlsx", str(workbook), "--question-variant", "v3", "--out", str(target)
    ) == EXIT_OK
    out = capsys.readouterr().out
    assert "content hash" in out
    assert "question v3" in out
    document = json.loads(target.read_text(encoding="utf-8"))
    rows = document["responses"] if isinstance(document, dict) else document
    assert len(rows) == len(RAW_RESPONSES)


def test_analyse_writes_the_matrix_the_clusters_and_the_curve(
    demo: Path, corpus_json: Path, tmp_path: Path, capsys
):
    out = tmp_path / "analysis"
    assert run_cli(
        "analyse",
        "--assignments",
        str(demo / "assignments.json"),
        "--data",
        str(corpus_json),
        "--out",
        str(out),
    ) == EXIT_OK
    for name in (
        "occurrence_matrix.csv",
        "occurrence_matrix.json",
        "clusters.json",
        "clusters.md",
        "dendrogram.svg",
        "saturation.json",
        "saturation.md",
        "saturation.svg",
    ):
        assert (out / name).exists(), name
    text = capsys.readouterr().out
    assert "Low-frequency filter" in text
    assert "Ward's hierarchical cluster analysis" in text
    assert "Saturation" in text


def test_analyse_accepts_a_codebook_as_well_as_assignments(demo: Path, tmp_path: Path):
    assert run_cli(
        "analyse", "--assignments", str(demo / "codebook.json"), "--out", str(tmp_path / "a2")
    ) == EXIT_OK


def test_report_rebuilds_both_artefacts_from_run_json(demo: Path, tmp_path: Path):
    out = tmp_path / "rendered"
    assert run_cli("report", "--run", str(demo), "--out", str(out)) == EXIT_OK
    assert (out / "report.txt").read_text(encoding="utf-8") == (
        demo / "report.txt"
    ).read_text(encoding="utf-8")
    assert (out / "codebook.html").read_bytes() == (demo / "codebook.html").read_bytes()


def test_load_artefact_reads_both_shapes(tmp_path: Path):
    codebook_path = write_codebook(tmp_path / "cb.json", toy_codebook())
    assignments_path = write_assignments(tmp_path / "as.json", human_assignments())
    assert load_artefact(codebook_path).kind == "codebook"
    assert load_artefact(assignments_path).kind == "assignments"
    # A codebook still yields assignments, so every command accepts either file.
    assert load_artefact(codebook_path).assignments


def test_an_unrecognised_artefact_is_refused_by_name(tmp_path: Path, capsys):
    path = write_json(tmp_path / "junk.json", {"nonsense": [1, 2, 3]})
    assert run_cli("check", "structural", "--codebook", str(path)) == EXIT_INPUT
    assert "unrecognised artefact shape" in capsys.readouterr().err


def test_a_missing_file_is_refused(tmp_path: Path, capsys):
    assert run_cli("check", "structural", "--codebook", str(tmp_path / "nope.json")) == EXIT_INPUT
    assert "does not exist" in capsys.readouterr().err


def test_check_needs_exactly_one_artefact(clean_codebook_path: Path, capsys):
    assert run_cli("check", "structural") == EXIT_USAGE
    assert run_cli(
        "check", "structural", "--codebook", str(clean_codebook_path), "--assignments", str(clean_codebook_path)
    ) == EXIT_USAGE
    assert "exactly one" in capsys.readouterr().err


def test_a_codebook_referencing_a_response_outside_the_corpus_is_an_error(
    tmp_path: Path, corpus_json: Path, capsys
):
    """S6's corpus-reference check binds only when a corpus is supplied to bind against."""
    code = Code(
        id="c-ghost",
        name="future-unknown",
        description="Uncertainty about what comes next.",
        evidence=[Evidence(response_id=9999, quote="a quote from nowhere", verified=True)],
    )
    path = write_codebook(tmp_path / "ghost.json", Codebook(codes={code.id: code}))

    # Without a corpus there is nothing to check the reference against, so it passes.
    assert run_cli("check", "structural", "--codebook", str(path)) == EXIT_OK
    capsys.readouterr()

    assert run_cli(
        "check", "structural", "--codebook", str(path), "--data", str(corpus_json)
    ) == EXIT_FINDINGS
    out = capsys.readouterr().out
    assert "9999" in out
    # Reported by S6, not raised by the CLI: a finding never becomes a crash.
    assert "responses not in the corpus" in out
    assert "S6" in out
