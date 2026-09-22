"""T5 gate for `gaf codebook`, seeded runs, the halt flag and `--skip-coded`.

Twelve claims:

1. **`gaf codebook organise` writes every artefact it promises** and prints counts —
   pairs, families, leaves, consolidations, note categories, placement outcomes,
   definitions matched and missing — and never a segment or a description.
2. **The two Markdown renderings differ in exactly one way**: `organised.md` carries the
   examples, `organised_shareable.md` carries none. The shareable one holds no segment.
3. **`codebook.json` is the thing `gaf check` and `--seed-codebook` read**, and it
   round-trips through `load_artefact`.
4. **`golden.json` is row-oriented assignments** `gaf validate agreement` accepts, and
   it exists only when a corpus was supplied, because without one nothing has a
   response id.
5. **Organising is deterministic** — two runs over the same inputs write byte-identical
   artefacts.
6. **`gaf codebook define` describes what has no description**, labels every
   description with its source, and **never overwrites an imported one**.
7. **`--only-missing` does not re-describe what the Definer already wrote.**
8. **`definer_findings.json` carries the guards' findings and no description text.**
9. **`gaf run --seed-codebook` starts from the seed**, records `seeded_from` in
   `run.json`, `stats.json` and the audit log, and the report's CAVEATS section says in
   plain words what a seeded run costs.
10. **Seed evidence is not double-counted as this run's coding**: the seed's evidence is
    held out, so `assignments.json`, the run's codebook and the occurrence matrix built
    from either describe this run only.
11. **`--halt-on-checkpoint` halts, exits 0, and prints the two commands that continue
    the work**; with the flag off nothing changes at all.
12. **`--skip-coded` does not code a response twice** and says what it skipped.

Every input here is synthetic: `tests.fixtures.tagged`'s invented pairings and
`tests.fixtures.corpus`'s invented corpus. No real survey response, or any fragment of
one, is read or written by this file.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from gaf.cli import EXIT_INPUT, EXIT_OK, load_artefact, main
from gaf.ingest.corpus import write_corpus_json
from gaf.ingest.definitions import DEFINITION_SOURCE
from gaf.models import Codebook
from gaf.report.run_report import RUN_JSON_NAME, RunArtefact
from tests.fixtures.corpus import synthetic_corpus
from tests.fixtures.tagged import SAMPLE_PAIRS, write_definitions_md, write_tagged_csv

ORGANISE_ARTEFACTS = (
    "organised.json",
    "organised.md",
    "organised_shareable.md",
    "tree.mmd",
    "codebook.json",
    "placement.json",
    "golden.json",
)

#: ADR-0005, and the shareable rendering's own reason for existing.
FORBIDDEN_VOCABULARY = ("frame", "framing")


def run_cli(*argv: str) -> int:
    return main(list(argv))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def flat(text: str) -> str:
    """Collapse whitespace, so an assertion is not hostage to where a line wrapped."""
    return " ".join(text.split())


@pytest.fixture(scope="module")
def corpus_json(tmp_path_factory: pytest.TempPathFactory) -> Path:
    path = tmp_path_factory.mktemp("corpus") / "corpus.json"
    write_corpus_json(synthetic_corpus(), path)
    return path


@pytest.fixture(scope="module")
def tagged_csv(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return write_tagged_csv(tmp_path_factory.mktemp("tagged") / "pairs.csv")


@pytest.fixture(scope="module")
def definitions_md(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return write_definitions_md(tmp_path_factory.mktemp("defs") / "codebook.md")


@pytest.fixture(scope="module")
def organised(
    tmp_path_factory: pytest.TempPathFactory,
    tagged_csv: Path,
    corpus_json: Path,
    definitions_md: Path,
) -> Path:
    """The full `organise`: pairings, corpus, definitions — everything switched on."""
    out = tmp_path_factory.mktemp("organised") / "book"
    assert (
        run_cli(
            "codebook",
            "organise",
            "--tagged",
            str(tagged_csv),
            "--corpus",
            str(corpus_json),
            "--definitions",
            str(definitions_md),
            "--out",
            str(out),
        )
        == EXIT_OK
    )
    return out


# --------------------------------------------------------------------------- #
# 1. organise writes what it promises, and prints counts
# --------------------------------------------------------------------------- #


def test_organise_writes_every_artefact(organised: Path):
    for name in ORGANISE_ARTEFACTS:
        assert (organised / name).exists(), f"gaf codebook organise did not write {name}"


def test_organise_prints_the_counts_the_brief_names(
    tagged_csv: Path, corpus_json: Path, definitions_md: Path, tmp_path: Path, capsys
):
    run_cli(
        "codebook", "organise",
        "--tagged", str(tagged_csv),
        "--corpus", str(corpus_json),
        "--definitions", str(definitions_md),
        "--out", str(tmp_path / "out"),
    )
    printed = capsys.readouterr().out
    for label in (
        "pairs read",
        "families",
        "leaves",
        "consolidations",
        "exact",
        "ambiguous",
        "unlocated",
        "matched",
        "defined but never tagged",
        "tagged but never defined",
    ):
        assert label in printed, f"the summary does not report {label!r}"
    assert f"pairs read{' ' * 12}{len(SAMPLE_PAIRS)}".split()[-1] in printed


def test_organise_prints_no_segment_and_no_description(
    tagged_csv: Path, corpus_json: Path, definitions_md: Path, tmp_path: Path, capsys
):
    """Counts only. A count is safe to paste into an email; a segment is not."""
    run_cli(
        "codebook", "organise",
        "--tagged", str(tagged_csv),
        "--corpus", str(corpus_json),
        "--definitions", str(definitions_md),
        "--out", str(tmp_path / "out"),
    )
    printed = capsys.readouterr().out
    for _tag, content in SAMPLE_PAIRS:
        assert content not in printed
    assert "Beneficial effects the respondent attributes" not in printed


def test_organise_without_a_corpus_writes_no_placement_and_no_golden_set(
    tagged_csv: Path, tmp_path: Path, capsys
):
    out = tmp_path / "bare"
    assert run_cli("codebook", "organise", "--tagged", str(tagged_csv), "--out", str(out)) == EXIT_OK
    assert (out / "organised.json").exists()
    assert not (out / "placement.json").exists()
    assert not (out / "golden.json").exists()
    assert "no --corpus" in capsys.readouterr().out


def test_organise_refuses_a_tagged_file_that_does_not_exist(tmp_path: Path):
    assert (
        run_cli("codebook", "organise", "--tagged", str(tmp_path / "nope.csv"), "--out", str(tmp_path))
        == EXIT_INPUT
    )


def test_organise_refuses_an_unreadable_definitions_file(
    tagged_csv: Path, tmp_path: Path
):
    empty = tmp_path / "empty.md"
    empty.write_text("# nothing here\n", encoding="utf-8")
    assert (
        run_cli(
            "codebook", "organise",
            "--tagged", str(tagged_csv),
            "--definitions", str(empty),
            "--out", str(tmp_path / "out"),
        )
        == EXIT_INPUT
    )


# --------------------------------------------------------------------------- #
# 2. The two Markdown renderings
# --------------------------------------------------------------------------- #


def test_the_directory_is_labelled_as_holding_respondent_text(organised: Path, capsys, tmp_path: Path, tagged_csv: Path, corpus_json: Path):
    """The shareable rendering is shareable about *examples*, and says only that."""
    run_cli(
        "codebook", "organise",
        "--tagged", str(tagged_csv),
        "--corpus", str(corpus_json),
        "--out", str(tmp_path / "labelled"),
    )
    printed = capsys.readouterr().out
    assert "holds respondent text" in printed
    assert "keep it out of git" in printed
    assert "only as shareable as whoever wrote it" in printed


def test_the_shareable_rendering_holds_no_segment_and_the_other_one_does(organised: Path):
    rich = (organised / "organised.md").read_text(encoding="utf-8")
    shareable = (organised / "organised_shareable.md").read_text(encoding="utf-8")
    quoted = [content for _tag, content in SAMPLE_PAIRS if content in rich]
    assert quoted, "organised.md is the rendering that carries the examples"
    for content in quoted:
        assert content not in shareable
    assert len(shareable) < len(rich)


def test_the_tree_carries_names_and_counts_and_never_a_segment(organised: Path):
    tree = (organised / "tree.mmd").read_text(encoding="utf-8")
    assert tree.lstrip().startswith("flowchart")
    for _tag, content in SAMPLE_PAIRS:
        assert content not in tree


def test_neither_rendering_uses_framing_vocabulary(organised: Path):
    for name in ("organised.md", "organised_shareable.md", "tree.mmd"):
        haystack = (organised / name).read_text(encoding="utf-8").casefold()
        for word in FORBIDDEN_VOCABULARY:
            assert word not in haystack, f"{name} uses {word!r}"


# --------------------------------------------------------------------------- #
# 3 & 4. The machine-readable outputs
# --------------------------------------------------------------------------- #


def test_the_codebook_is_the_shape_every_other_command_reads(organised: Path):
    artefact = load_artefact(organised / "codebook.json")
    assert artefact.kind == "codebook"
    assert artefact.codebook is not None
    assert len(artefact.codebook) > 0
    assert artefact.codebook.families()


def test_gaf_check_finds_the_codebook_structurally_sound(organised: Path, corpus_json: Path):
    """S1-S6 over what `organise` wrote: every quote locates, every name parses.

    The structural gate is the claim worth making here. `gaf check all` additionally
    runs M3, whose offline fit scores are the stand-in embedder's artefact (ADR-0022)
    and say nothing about this codebook.
    """
    assert (
        run_cli(
            "check",
            "structural",
            "--codebook",
            str(organised / "codebook.json"),
            "--data",
            str(corpus_json),
        )
        == EXIT_OK
    )


def test_the_golden_set_is_row_oriented_assignments(organised: Path):
    rows = read_json(organised / "golden.json")
    assert rows and all({"response_id", "segment", "code"} <= set(row) for row in rows)
    assert load_artefact(organised / "golden.json").kind == "assignments"


def test_gaf_validate_agreement_accepts_the_golden_set(organised: Path, corpus_json: Path, tmp_path: Path):
    assert (
        run_cli(
            "validate", "agreement",
            "--human", str(organised / "golden.json"),
            "--machine", str(organised / "golden.json"),
            "--data", str(corpus_json),
            "--out", str(tmp_path / "agreement"),
        )
        == EXIT_OK
    )


def test_the_organised_json_records_where_it_came_from(organised: Path, tagged_csv: Path):
    meta = read_json(organised / "organised.json")["meta"]
    assert meta["tagged_path"] == str(tagged_csv)
    assert meta["tagged_content_hash"]
    assert meta["description_sources"]


def test_every_imported_description_is_labelled_with_its_source(organised: Path):
    codebook = Codebook.from_json(read_json(organised / "codebook.json"))
    described = [c for c in codebook.sorted_codes() if c.description]
    assert described
    assert all(c.meta.get("description_source") == DEFINITION_SOURCE for c in described)


# --------------------------------------------------------------------------- #
# 5. Determinism
# --------------------------------------------------------------------------- #


def test_two_organise_runs_write_byte_identical_artefacts(
    tagged_csv: Path, corpus_json: Path, definitions_md: Path, tmp_path: Path
):
    written = []
    for label in ("first", "second"):
        out = tmp_path / label
        assert (
            run_cli(
                "codebook", "organise",
                "--tagged", str(tagged_csv),
                "--corpus", str(corpus_json),
                "--definitions", str(definitions_md),
                "--out", str(out),
            )
            == EXIT_OK
        )
        written.append({name: (out / name).read_bytes() for name in ORGANISE_ARTEFACTS})
    assert written[0] == written[1]


# --------------------------------------------------------------------------- #
# 6, 7, 8. define
# --------------------------------------------------------------------------- #


@pytest.fixture
def undefined(tmp_path: Path, tagged_csv: Path, corpus_json: Path) -> Path:
    """Organised with no definitions at all: every code is the Definer's to write."""
    out = tmp_path / "undefined"
    assert (
        run_cli(
            "codebook", "organise",
            "--tagged", str(tagged_csv),
            "--corpus", str(corpus_json),
            "--out", str(out),
        )
        == EXIT_OK
    )
    return out


def test_define_describes_every_undescribed_code_and_labels_the_source(undefined: Path):
    before = Codebook.from_json(read_json(undefined / "codebook.json"))
    assert all(not code.description for code in before.sorted_codes())

    assert run_cli("codebook", "define", "--organised", str(undefined)) == EXIT_OK

    after = Codebook.from_json(read_json(undefined / "codebook.json"))
    assert after.names() == before.names(), "defining never changes the organisation"
    assert all(code.description for code in after.sorted_codes())
    assert all(code.meta["description_source"] == "definer-mock" for code in after.sorted_codes())


def test_a_mock_description_says_so_in_every_artefact_that_carries_it(undefined: Path):
    run_cli("codebook", "define", "--organised", str(undefined))
    meta = read_json(undefined / "organised.json")["meta"]
    assert set(meta["description_sources"].values()) == {"definer-mock"}
    for name in ("organised.md", "organised_shareable.md"):
        assert "definer-mock" in (undefined / name).read_text(encoding="utf-8"), name
    codebook = Codebook.from_json(read_json(undefined / "codebook.json"))
    assert {c.meta["description_source"] for c in codebook.sorted_codes()} == {"definer-mock"}


def test_define_never_overwrites_an_imported_description(organised: Path):
    before = Codebook.from_json(read_json(organised / "codebook.json"))
    imported = {c.name: c.description for c in before.sorted_codes() if c.description}
    assert imported

    assert run_cli("codebook", "define", "--organised", str(organised)) == EXIT_OK

    after = Codebook.from_json(read_json(organised / "codebook.json"))
    for code in after.sorted_codes():
        if code.name in imported:
            assert code.description == imported[code.name]
            assert code.meta["description_source"] == DEFINITION_SOURCE


def test_define_is_deterministic_and_idempotent_under_only_missing(undefined: Path):
    run_cli("codebook", "define", "--organised", str(undefined))
    first = (undefined / "codebook.json").read_bytes()
    run_cli("codebook", "define", "--organised", str(undefined), "--only-missing")
    assert (undefined / "codebook.json").read_bytes() == first


def test_define_refuses_a_directory_that_organise_did_not_write(tmp_path: Path):
    assert run_cli("codebook", "define", "--organised", str(tmp_path / "nothing")) == EXIT_INPUT


def test_define_refuses_when_the_tagged_export_has_changed_underneath_it(
    tmp_path: Path, tagged_csv: Path, capsys
):
    moving = tmp_path / "moving.csv"
    moving.write_bytes(tagged_csv.read_bytes())
    out = tmp_path / "book"
    assert run_cli("codebook", "organise", "--tagged", str(moving), "--out", str(out)) == EXIT_OK
    write_tagged_csv(moving, rows=SAMPLE_PAIRS[:4])
    assert run_cli("codebook", "define", "--organised", str(out)) == EXIT_INPUT
    assert "changed" in capsys.readouterr().err


def test_the_findings_file_carries_the_guards_and_no_description_text(undefined: Path):
    run_cli("codebook", "define", "--organised", str(undefined))
    payload = read_json(undefined / "definer_findings.json")
    assert payload["prompt_version"] == "definer-v1"
    assert payload["source"] == "definer-mock"
    assert payload["counts"]["accepted"] == payload["counts"]["considered"]
    assert payload["definitions"]
    assert all("description" not in row for row in payload["definitions"])
    described = Codebook.from_json(read_json(undefined / "codebook.json")).sorted_codes()
    blob = json.dumps(payload, ensure_ascii=False)
    for code in described:
        assert code.description not in blob


def test_define_prints_counts_and_no_description(undefined: Path, capsys):
    run_cli("codebook", "define", "--organised", str(undefined))
    printed = capsys.readouterr().out
    assert "accepted" in printed and "refused" in printed
    for code in Codebook.from_json(read_json(undefined / "codebook.json")).sorted_codes():
        assert code.description not in printed


# --------------------------------------------------------------------------- #
# 9 & 10. Seeded runs
# --------------------------------------------------------------------------- #


@pytest.fixture
def seeded_run(tmp_path: Path, corpus_json: Path, organised: Path) -> Path:
    out = tmp_path / "seeded"
    assert (
        run_cli(
            "run",
            "--corpus", str(corpus_json),
            "--run-id", "seeded",
            "--out", str(out),
            "--seed-codebook", str(organised / "codebook.json"),
            "--cache-dir", str(tmp_path / "cache"),
        )
        == EXIT_OK
    )
    return out


def test_a_seeded_run_starts_from_the_seed(seeded_run: Path, organised: Path):
    seed = Codebook.from_json(read_json(organised / "codebook.json"))
    produced = Codebook.from_json(read_json(seeded_run / "codebook.json"))
    assert set(seed.names()) <= set(produced.names())
    assert len(produced) >= len(seed)


def test_a_seeded_run_records_where_the_seed_came_from(seeded_run: Path, organised: Path):
    document = read_json(seeded_run / RUN_JSON_NAME)
    seeded_from = document["provenance"]["seeded_from"]
    assert seeded_from["path"] == str(organised / "codebook.json")
    assert seeded_from["content_hash"]
    assert seeded_from["codes"] > 0
    assert read_json(seeded_run / "stats.json")["seeded_from"] == seeded_from
    events = [
        json.loads(line)
        for line in (seeded_run / "audit.jsonl").read_text(encoding="utf-8").splitlines()
        if line
    ]
    seeds = [e for e in events if e["event"] == "run_seeded"]
    assert len(seeds) == 1
    assert seeds[0]["payload"]["content_hash"] == seeded_from["content_hash"]


def test_a_cold_run_records_no_seed(tmp_path: Path, corpus_json: Path):
    out = tmp_path / "cold"
    assert run_cli("run", "--corpus", str(corpus_json), "--run-id", "cold", "--out", str(out)) == EXIT_OK
    assert "seeded_from" not in read_json(out / RUN_JSON_NAME)["provenance"]
    assert read_json(out / "stats.json").get("seeded_from") is None
    report = (out / "report.txt").read_text(encoding="utf-8")
    assert "not independent evidence" not in report


def test_the_report_says_plainly_what_a_seeded_run_costs(seeded_run: Path):
    report = (seeded_run / "report.txt").read_text(encoding="utf-8")
    caveats = flat(report.split("CAVEATS")[1].split("PROVENANCE")[0]).casefold()
    assert "not independent evidence" in caveats
    assert "a cold run" in caveats
    assert "seeded from" in flat(report).casefold()


def test_seed_evidence_is_not_counted_as_this_runs_coding(seeded_run: Path, organised: Path):
    """The seed supplies an organisation, never an occurrence."""
    seed = Codebook.from_json(read_json(organised / "codebook.json"))
    seed_rows = {
        (e.response_id, e.quote, code.name)
        for code in seed.sorted_codes()
        for e in code.evidence
        if e.verified
    }
    assert seed_rows, "the fixture seed carries evidence, or this test proves nothing"

    produced = Codebook.from_json(read_json(seeded_run / "codebook.json"))
    carried = {
        (e.response_id, e.quote, code.name)
        for code in produced.sorted_codes()
        for e in code.evidence
    }
    assert not (seed_rows & carried), "the seed's own evidence must not reappear as this run's"

    rows = read_json(seeded_run / "assignments.json")
    assignment_rows = {(r["response_id"], r["segment"], r["code"]) for r in rows}
    assert not (seed_rows & assignment_rows)


def test_the_run_says_how_much_seed_evidence_it_held_out(seeded_run: Path):
    seeded_from = read_json(seeded_run / RUN_JSON_NAME)["provenance"]["seeded_from"]
    assert seeded_from["evidence_held_out"] > 0
    produced = Codebook.from_json(read_json(seeded_run / "codebook.json"))
    seeded_codes = [c for c in produced.sorted_codes() if c.meta.get("seeded_from")]
    assert seeded_codes
    assert all(c.meta["seeded_from"] == seeded_from["content_hash"] for c in seeded_codes)


def test_the_analysis_tail_over_either_artefact_describes_this_run_only(
    seeded_run: Path, corpus_json: Path, tmp_path: Path
):
    outputs = []
    for label, source in (("book", "codebook.json"), ("rows", "assignments.json")):
        out = tmp_path / f"analyse-{label}"
        assert (
            run_cli(
                "analyse",
                "--assignments", str(seeded_run / source),
                "--data", str(corpus_json),
                "--out", str(out),
                "--min-frequency", "1",
            )
            == EXIT_OK
        )
        outputs.append(read_json(out / "occurrence_matrix.json"))
    assert outputs[0]["code_names"] == outputs[1]["code_names"]
    assert outputs[0]["response_ids"] == outputs[1]["response_ids"]
    assert outputs[0]["values"] == outputs[1]["values"]


def test_run_refuses_a_seed_that_is_not_a_codebook(tmp_path: Path, corpus_json: Path, organised: Path):
    assert (
        run_cli(
            "run",
            "--corpus", str(corpus_json),
            "--out", str(tmp_path / "bad"),
            "--seed-codebook", str(organised / "golden.json"),
        )
        == EXIT_INPUT
    )


# --------------------------------------------------------------------------- #
# 11 & 12. The handover flag and the resume
# --------------------------------------------------------------------------- #


@pytest.fixture
def halted(tmp_path: Path, corpus_json: Path, capsys) -> tuple[Path, str]:
    out = tmp_path / "halted"
    code = run_cli(
        "run",
        "--corpus", str(corpus_json),
        "--run-id", "halted",
        "--out", str(out),
        "--halt-on-checkpoint",
    )
    printed = capsys.readouterr().out
    assert code == EXIT_OK, "a halt is the designed behaviour, not an error"
    return out, printed


def test_a_halt_exits_zero_and_records_where_it_stopped(halted: tuple[Path, str]):
    out, _ = halted
    stats = read_json(out / "stats.json")
    assert stats["halted_at_batch"] == 1
    assert stats["responses_uncoded"] > 0
    assert stats["n_responses"] < len(synthetic_corpus())


def test_a_halt_still_closes_the_run_directory(halted: tuple[Path, str]):
    out, _ = halted
    for name in (RUN_JSON_NAME, "codebook.json", "assignments.json", "audit.jsonl", "report.txt"):
        assert (out / name).exists()
    events = {
        json.loads(line)["event"]
        for line in (out / "audit.jsonl").read_text(encoding="utf-8").splitlines()
        if line
    }
    assert {"run_started", "run_completed"} <= events


def test_a_halt_prints_the_batch_the_rule_the_remainder_and_the_two_commands(
    halted: tuple[Path, str],
):
    out, printed = halted
    assert "batch 1" in printed
    assert "handover." in printed, "the rule that fired is named, not just the trigger"
    assert "remain" in printed
    assert f"gaf checkpoint --run {out}" in printed
    assert "--seed-codebook" in printed and "--skip-coded" in printed


def test_with_the_flag_off_nothing_changes(tmp_path: Path, corpus_json: Path):
    runs = []
    for label, extra in (("plain", []), ("flagged", ["--halt-on-checkpoint"])):
        out = tmp_path / label
        assert (
            run_cli("run", "--corpus", str(corpus_json), "--run-id", label, "--out", str(out), *extra)
            == EXIT_OK
        )
        runs.append(out)
    plain, flagged = runs
    assert (plain / "codebook.json").read_bytes() != (flagged / "codebook.json").read_bytes()
    # ...and the unflagged run is the full one, byte-for-byte what it always was.
    baseline = tmp_path / "baseline"
    assert run_cli("run", "--corpus", str(corpus_json), "--run-id", "plain", "--out", str(baseline)) == EXIT_OK
    assert (baseline / "codebook.json").read_bytes() == (plain / "codebook.json").read_bytes()
    assert read_json(plain / "stats.json")["halted_at_batch"] is None


def test_the_resumed_run_skips_what_was_already_coded(
    tmp_path: Path, corpus_json: Path, halted: tuple[Path, str], capsys
):
    first, _ = halted
    coded = {o["response_id"] for o in read_json(first / RUN_JSON_NAME)["result"]["responses"]}
    out = tmp_path / "resumed"
    assert (
        run_cli(
            "run",
            "--corpus", str(corpus_json),
            "--run-id", "resumed",
            "--out", str(out),
            "--seed-codebook", str(first / "codebook.json"),
            "--skip-coded", str(first),
        )
        == EXIT_OK
    )
    printed = capsys.readouterr().out
    assert f"skipped {len(coded)}" in printed

    resumed = {o["response_id"] for o in read_json(out / RUN_JSON_NAME)["result"]["responses"]}
    assert not (coded & resumed), "no response is coded twice across the two runs"
    assert coded | resumed == {r.id for r in synthetic_corpus()}
    assert read_json(out / RUN_JSON_NAME)["provenance"]["skipped_from"]["run"] == str(first)


def test_resuming_with_nothing_left_to_code_is_refused_by_name(
    tmp_path: Path, corpus_json: Path, capsys
):
    complete = tmp_path / "complete"
    assert run_cli("run", "--corpus", str(corpus_json), "--run-id", "c", "--out", str(complete)) == EXIT_OK
    assert (
        run_cli(
            "run",
            "--corpus", str(corpus_json),
            "--out", str(tmp_path / "nothing"),
            "--skip-coded", str(complete),
        )
        == EXIT_INPUT
    )
    assert "already coded" in capsys.readouterr().err


def test_skip_coded_refuses_a_directory_that_is_not_a_run(tmp_path: Path, corpus_json: Path):
    assert (
        run_cli(
            "run",
            "--corpus", str(corpus_json),
            "--out", str(tmp_path / "out"),
            "--skip-coded", str(tmp_path / "not-a-run"),
        )
        == EXIT_INPUT
    )


# --------------------------------------------------------------------------- #
# Housekeeping
# --------------------------------------------------------------------------- #


def test_the_codebook_command_help_never_says_it(capsys):
    with pytest.raises(SystemExit):
        run_cli("codebook", "--help")
    haystack = capsys.readouterr().out.casefold()
    for word in FORBIDDEN_VOCABULARY:
        assert word not in haystack


def test_the_run_report_of_a_seeded_run_still_renders_from_run_json(seeded_run: Path, tmp_path: Path):
    artefact = RunArtefact.from_json(read_json(seeded_run / RUN_JSON_NAME))
    assert artefact.provenance["seeded_from"]["codes"] > 0
    assert run_cli("report", "--run", str(seeded_run), "--out", str(tmp_path / "rendered")) == EXIT_OK
    rendered = flat((tmp_path / "rendered" / "report.txt").read_text(encoding="utf-8")).casefold()
    assert "not independent evidence" in rendered


# --------------------------------------------------------------------------- #
# Refusal paths and the branches the happy path does not reach
# --------------------------------------------------------------------------- #


def test_organise_refuses_pairings_it_cannot_read(tmp_path: Path, capsys):
    broken = tmp_path / "broken.csv"
    broken.write_text("neither,column,is,a,pairing\n1,2,3,4,5\n", encoding="utf-8")
    assert (
        run_cli("codebook", "organise", "--tagged", str(broken), "--out", str(tmp_path / "out"))
        == EXIT_INPUT
    )
    assert "cannot read the pairings" in capsys.readouterr().err


def test_organise_refuses_a_pairing_file_with_a_header_and_no_rows(tmp_path: Path, capsys):
    empty = write_tagged_csv(tmp_path / "empty.csv", rows=())
    assert (
        run_cli("codebook", "organise", "--tagged", str(empty), "--out", str(tmp_path / "out"))
        == EXIT_INPUT
    )
    assert "no code-text pairings" in capsys.readouterr().err


def test_organise_refuses_a_definitions_file_that_does_not_exist(
    tagged_csv: Path, tmp_path: Path, capsys
):
    assert (
        run_cli(
            "codebook", "organise",
            "--tagged", str(tagged_csv),
            "--definitions", str(tmp_path / "missing.md"),
            "--out", str(tmp_path / "out"),
        )
        == EXIT_INPUT
    )
    assert "does not exist" in capsys.readouterr().err


def test_define_refuses_when_the_pairings_have_been_moved_away(
    tmp_path: Path, tagged_csv: Path, capsys
):
    moving = tmp_path / "moving.csv"
    moving.write_bytes(tagged_csv.read_bytes())
    out = tmp_path / "book"
    assert run_cli("codebook", "organise", "--tagged", str(moving), "--out", str(out)) == EXIT_OK
    moving.unlink()
    assert run_cli("codebook", "define", "--organised", str(out)) == EXIT_INPUT
    assert "no longer there" in capsys.readouterr().err


def test_a_blank_segment_is_not_text_to_describe_a_code_from(tmp_path: Path):
    """`organise_tagged` counts a blank pairing as a note; the Definer never sees it."""
    from gaf.cli.codebook import segments_by_code
    from gaf.ingest.tagged import organise_tagged, read_tagged_pairs

    rows = (*SAMPLE_PAIRS, ("efficiency", "   "))
    path = write_tagged_csv(tmp_path / "with-blank.csv", rows=rows)
    pairs = read_tagged_pairs(path)
    grouped = segments_by_code(pairs, organise_tagged(pairs))
    assert all(segment.strip() for segments in grouped.values() for segment in segments)
    assert len(grouped["efficiency"]) == 2


def test_a_refused_description_is_printed_as_a_finding_and_not_written_back(
    undefined: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    """Force every guard to refuse, and watch the codebook stay undescribed."""
    import gaf.cli.codebook as codebook_cli
    from gaf.agents.definer import DefinerAgent

    class Overlong(DefinerAgent):
        def define(self, context):  # type: ignore[no-untyped-def]
            return self._definition_for(context, "One. Two. Three. Four.")

    monkeypatch.setattr(
        codebook_cli,
        "_definer_for",
        lambda config, log: Overlong(codebook_cli.MockDefinerClient(config.models.refactorer)),
    )
    assert run_cli("codebook", "define", "--organised", str(undefined)) == EXIT_OK
    printed = capsys.readouterr().out
    assert "[ERROR] D2" in printed
    payload = read_json(undefined / "definer_findings.json")
    assert payload["counts"]["accepted"] == 0
    assert payload["counts"]["refused"] == payload["counts"]["considered"]
    assert payload["severities"]["ERROR"] == payload["counts"]["refused"]
    after = Codebook.from_json(read_json(undefined / "codebook.json"))
    assert all(not code.description for code in after.sorted_codes()), "refused, never repaired"


def test_a_long_skip_list_is_summarised_rather_than_printed_in_full(
    tmp_path: Path, corpus_json: Path, capsys
):
    complete = tmp_path / "all"
    assert run_cli("run", "--corpus", str(corpus_json), "--run-id", "all", "--out", str(complete)) == EXIT_OK
    # One response is held back so there is something left to code.
    reduced = tmp_path / "reduced.json"
    rows = read_json(corpus_json)
    reduced.write_text(json.dumps(rows), encoding="utf-8")
    assert (
        run_cli(
            "run",
            "--corpus", str(reduced),
            "--out", str(tmp_path / "resumed"),
            "--skip-coded", str(complete),
            "--run-id", "resumed",
        )
        == EXIT_INPUT
    )
    assert "already coded" in capsys.readouterr().err


def test_run_refuses_a_seed_path_that_does_not_exist(tmp_path: Path, corpus_json: Path, capsys):
    assert (
        run_cli(
            "run",
            "--corpus", str(corpus_json),
            "--out", str(tmp_path / "out"),
            "--seed-codebook", str(tmp_path / "missing.json"),
        )
        == EXIT_INPUT
    )
    assert "does not exist" in capsys.readouterr().err


def test_a_long_skip_list_prints_a_count_rather_than_every_id(capsys):
    """A resumed run over the real corpus skips dozens of ids; the line stays readable."""
    from gaf.cli.run import _MAX_LISTED_IDS, _describe_skip

    ids = list(range(1, _MAX_LISTED_IDS + 6))
    _describe_skip(ids, Path("runs/earlier"))
    printed = capsys.readouterr().out
    assert f"skipped {len(ids)} response(s)" in printed
    assert "+5 more" in printed
    assert str(ids[_MAX_LISTED_IDS]) not in printed.split("more)")[0]


# --------------------------------------------------------------------------- #
# R1 audit findings
# --------------------------------------------------------------------------- #


def test_a_parent_context_reads_the_child_descriptions_the_caller_has_written() -> None:
    """R1 I2. The order was right and the data was stale, so the claim was false."""
    from gaf.cli.codebook import contexts_for
    from gaf.ingest.tagged import TaggedPair, organise_tagged

    pairs = [
        TaggedPair(tag="jobs-automation", content="Clerical posts in the district office vanish", row=1),
        TaggedPair(tag="jobs-automation", content="The port employs fewer people", row=2),
        TaggedPair(tag="jobs-reskilling", content="a real improvement in how that work is done", row=3),
        TaggedPair(tag="trust-opacity", content="the engineers argue with a model", row=4),
    ]
    organised = organise_tagged(pairs)
    described: dict[str, str] = {}

    seen: list[str] = []
    glosses: dict[str, tuple[tuple[str, str], ...]] = {}
    for context in contexts_for(organised, pairs, described=described):
        seen.append(context.name)
        if context.children:
            glosses[context.name] = tuple(
                (child.name, child.description) for child in context.children
            )
        described[context.name] = f"A description of {context.name}."

    assert seen.index("jobs") > seen.index("jobs-automation"), "leaves first"
    assert glosses["jobs"] == (
        ("jobs-automation", "A description of jobs-automation."),
        ("jobs-reskilling", "A description of jobs-reskilling."),
    ), "the parent saw the descriptions the loop had already written"
    assert glosses["trust"] == (("trust-opacity", "A description of trust-opacity."),)


def test_materialising_the_contexts_first_is_what_made_them_stale() -> None:
    """The regression this generator exists to prevent, written down as a test."""
    from gaf.cli.codebook import contexts_for
    from gaf.ingest.tagged import TaggedPair, organise_tagged

    pairs = [
        TaggedPair(tag="jobs-automation", content="The port employs fewer people", row=1),
    ]
    organised = organise_tagged(pairs)
    described: dict[str, str] = {}
    eager = list(contexts_for(organised, pairs, described=described))
    described["jobs-automation"] = "written after the list was built"
    parent = next(c for c in eager if c.name == "jobs")
    assert parent.children[0].description == "", (
        "a caller that materialises the generator gets exactly the stale data the "
        "docstring warns about; the loop in `gaf codebook define` does not"
    )
