"""The four input shapes that arrived after the first two, and what each reader refuses.

`tests/test_ingest.py` covers the headed workbook, the numbered single-column workbook
and the first highlights export. This file covers what came next:

* **1a** a numbered corpus as CSV (``All,,Trimmed``), routed by suffix and sniff;
* **1b** code-text pairings and the organiser that turns them into a codebook;
* **1c** the principal investigator's own code descriptions, read from Markdown;
* **1d** placing highlights on a corpus large enough that one segment occurs twice.

Every file here is built in `tmp_path` from `tests.fixtures.tagged`, whose tags,
segments and descriptions are invented; the segments are substrings of the invented
`tests.fixtures.corpus`. The real files' *shape* is reproduced faithfully -- the
byte-order mark, the unnamed empty middle column, the non-contiguous numbers, the
repeated number, the hyphen-for-underscore family, the misspelt subcode -- without
reproducing any of their content.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from gaf.checks.contracts import Severity
from gaf.checks.structural import check_codebook
from gaf.config import CodingRules
from gaf.ingest.corpus import (
    META_DUPLICATE_OF_NUMBER,
    META_ENCODING_REPAIRED,
    META_SOURCE_NUMBER,
    load_corpus,
    load_corpus_with_report,
)
from gaf.ingest.csv_corpus import (
    read_csv_rows,
    read_numbered_csv,
    sniff_numbered_csv,
)
from gaf.ingest.definitions import (
    DEFINITION_SOURCE,
    DefinitionsReport,
    attach_definitions,
    read_definitions_md,
)
from gaf.ingest.tagged import (
    TAGGED_SOURCE,
    OrganisedCodebook,
    TaggedPair,
    organise_tagged,
    read_tagged_pairs,
    to_codebook,
)
from gaf.ingest.xlsx import (
    DUPLICATE_ID_STRIDE,
    HighlightsReport,
    SpreadsheetFormatError,
    place_highlights,
    read_highlights_xlsx,
)
from gaf.models import Codebook, Response
from gaf.textnorm import normalise
from tests.fixtures.corpus import corpus_by_id, synthetic_corpus
from tests.fixtures.tagged import (
    DEFINITIONS_MD,
    HIGHLIGHTS_HEADER,
    SAMPLE_NUMBERED,
    SAMPLE_PAIRS,
    write_definitions_md,
    write_numbered_csv,
    write_rows_csv,
    write_tagged_csv,
    write_tagged_xlsx,
)

# UTF-8 curly quotes decoded once as MacRoman -- the damage the real files carry.
MOJIBAKE_OPEN = "\u201a\u00c4\u00fa"
MOJIBAKE_CLOSE = "\u201a\u00c4\u00f9"


# --------------------------------------------------------------------------- #
# 1a -- the numbered CSV corpus
# --------------------------------------------------------------------------- #


def test_the_numbered_csv_is_detected_and_a_headed_csv_is_not(tmp_path: Path) -> None:
    numbered = write_numbered_csv(tmp_path / "corpus.csv")
    headed = write_rows_csv(tmp_path / "headed.csv", [("Number", "Response"), (9, "text here")])
    assert sniff_numbered_csv(numbered) is True
    assert sniff_numbered_csv(headed) is False


def test_the_number_comes_from_the_all_prefix_and_the_text_from_trimmed(tmp_path: Path) -> None:
    path = write_numbered_csv(tmp_path / "corpus.csv")
    rows, disagreements = read_numbered_csv(path)
    assert [r.response_id for r in rows] == [11, 14, 19]
    assert [r.source_number for r in rows] == [11, 14, 19]
    assert [r.content for r in rows] == [text for _, text in SAMPLE_NUMBERED]
    assert disagreements == ()


def test_trimmed_wins_when_it_disagrees_with_all_and_the_row_is_reported(tmp_path: Path) -> None:
    """`Trimmed` is the PI's own cleaning pass; it wins, but silence would hide it."""
    path = write_numbered_csv(
        tmp_path / "corpus.csv",
        trimmed=[SAMPLE_NUMBERED[0][1], "A different sentence entirely.", SAMPLE_NUMBERED[2][1]],
    )
    rows, disagreements = read_numbered_csv(path)
    assert disagreements == (14,)
    assert rows[1].content == "A different sentence entirely."

    _, report = load_corpus_with_report(path)
    assert report.trimmed_disagreements == (14,)
    assert "14" in report.summary() and "Trimmed" in report.summary()


def test_whitespace_only_difference_between_the_columns_is_not_a_disagreement(
    tmp_path: Path,
) -> None:
    path = write_numbered_csv(
        tmp_path / "corpus.csv",
        trimmed=[f"  {SAMPLE_NUMBERED[0][1]}  ", SAMPLE_NUMBERED[1][1], SAMPLE_NUMBERED[2][1]],
    )
    rows, disagreements = read_numbered_csv(path)
    assert disagreements == ()
    assert rows[0].content == SAMPLE_NUMBERED[0][1], "Trimmed still wins, stripped"


@pytest.mark.parametrize("header", [None, ("All",)])
def test_a_csv_with_only_the_numbered_column_also_works(
    tmp_path: Path, header: tuple[str, ...] | None
) -> None:
    path = write_numbered_csv(tmp_path / "one.csv", header=header)
    rows, disagreements = read_numbered_csv(path)
    assert [r.response_id for r in rows] == [11, 14, 19]
    assert [r.content for r in rows] == [text for _, text in SAMPLE_NUMBERED]
    assert disagreements == ()


def test_a_repeated_number_in_a_csv_follows_adr_0029(tmp_path: Path) -> None:
    """The first keeps its number; the k-th extra is offset and the fact is reported."""
    path = write_numbered_csv(
        tmp_path / "dup.csv",
        [(44, "The first response numbered forty-four."), (44, "A different one, also forty-four."), (45, "The next.")],
    )
    responses, report = load_corpus_with_report(path)
    assert sorted(r.id for r in responses) == [44, 45, 44 + DUPLICATE_ID_STRIDE]
    extra = next(r for r in responses if r.id == 44 + DUPLICATE_ID_STRIDE)
    assert extra.meta[META_SOURCE_NUMBER] == 44
    assert extra.meta[META_DUPLICATE_OF_NUMBER] == 44
    assert report.duplicate_numbers == ((44, 44 + DUPLICATE_ID_STRIDE),)


def test_mojibake_in_a_csv_is_repaired_and_flagged(tmp_path: Path) -> None:
    damaged = f"He said {MOJIBAKE_OPEN}not now{MOJIBAKE_CLOSE} and walked away from it."
    path = write_numbered_csv(tmp_path / "moji.csv", [(11, damaged)])
    responses, report = load_corpus_with_report(path)
    assert responses[0].content == "He said \u201cnot now\u201d and walked away from it."
    assert responses[0].meta[META_ENCODING_REPAIRED] is True
    assert report.repaired_response_ids == (11,)


def test_a_csv_in_neither_shape_raises_naming_what_was_found(tmp_path: Path) -> None:
    path = write_rows_csv(tmp_path / "other.csv", [("alpha", "beta"), ("one", "two")])
    with pytest.raises(SpreadsheetFormatError) as excinfo:
        read_numbered_csv(path)
    message = str(excinfo.value)
    assert "other.csv" in message and "alpha" in message and "beta" in message


def test_an_empty_csv_raises(tmp_path: Path) -> None:
    path = write_rows_csv(tmp_path / "empty.csv", [])
    with pytest.raises(SpreadsheetFormatError, match="empty"):
        read_numbered_csv(path)


def test_a_missing_csv_raises_a_named_error(tmp_path: Path) -> None:
    with pytest.raises(SpreadsheetFormatError, match="no such"):
        read_numbered_csv(tmp_path / "absent.csv")


def test_a_numbered_row_with_no_text_raises(tmp_path: Path) -> None:
    path = write_rows_csv(tmp_path / "bare.csv", [("All", "", "Trimmed"), ("11.  ", "", "")])
    with pytest.raises(SpreadsheetFormatError, match="no text"):
        read_numbered_csv(path)


def test_a_row_whose_all_cell_carries_no_number_raises(tmp_path: Path) -> None:
    path = write_rows_csv(
        tmp_path / "mixed.csv",
        [("All", "", "Trimmed"), ("11. one sentence", "", "one sentence"), ("no number", "", "x")],
    )
    with pytest.raises(SpreadsheetFormatError, match="NN"):
        read_numbered_csv(path)


def test_an_unnamed_csv_column_carrying_data_raises_rather_than_guessing(tmp_path: Path) -> None:
    path = write_rows_csv(
        tmp_path / "third.csv",
        [("All", "", "Trimmed"), ("11. a sentence here", "stray", "a sentence here")],
    )
    with pytest.raises(SpreadsheetFormatError, match="no header"):
        read_numbered_csv(path)


def test_blank_rows_are_dropped_and_the_byte_order_mark_is_not_part_of_the_header(
    tmp_path: Path,
) -> None:
    path = write_rows_csv(
        tmp_path / "blanks.csv",
        [("All", "", "Trimmed"), ("11. one sentence", "", "one sentence"), ("", "", ""), ("14. two", "", "two")],
    )
    rows, _ = read_numbered_csv(path)
    assert [r.response_id for r in rows] == [11, 14]
    assert read_csv_rows(path)[0][0] == "All", "the BOM is stripped by the reader, not left on the header"


def test_a_headerless_csv_with_a_second_populated_column_is_refused(tmp_path: Path) -> None:
    """Autodetection must not turn the reader into a guesser -- as for the workbook."""
    path = write_rows_csv(tmp_path / "two.csv", [("11. a sentence here", "extra")])
    with pytest.raises(SpreadsheetFormatError, match="one column"):
        read_numbered_csv(path)
    assert sniff_numbered_csv(path) is False


def test_the_sniff_refuses_a_headed_csv_whose_all_column_is_not_numbered(
    tmp_path: Path,
) -> None:
    path = write_rows_csv(
        tmp_path / "unnumbered.csv",
        [("All", "", "Trimmed"), ("", "", ""), ("no number at all", "", "no number at all")],
    )
    assert sniff_numbered_csv(path) is False


def test_the_sniff_refuses_a_csv_with_a_header_and_no_rows(tmp_path: Path) -> None:
    path = write_rows_csv(tmp_path / "headeronly.csv", [("All", "", "Trimmed")])
    assert sniff_numbered_csv(path) is False


def test_load_corpus_routes_a_csv_by_suffix_and_attaches_the_question(tmp_path: Path) -> None:
    path = write_numbered_csv(tmp_path / "IndiaProcess(1-3).csv")
    responses = load_corpus(path)
    assert [r.id for r in responses] == [11, 14, 19]
    assert all(r.question for r in responses)
    assert all(r.source == "1_3" for r in responses)


def test_an_unsupported_suffix_still_raises(tmp_path: Path) -> None:
    path = tmp_path / "corpus.tsv"
    path.write_text("nothing", encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported corpus format"):
        load_corpus(path)


# --------------------------------------------------------------------------- #
# 1a -- `gaf ingest` takes the CSV from the same command, under either spelling
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("flag", ["--input", "--xlsx"])
def test_gaf_ingest_accepts_a_csv_under_either_spelling_of_the_flag(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], flag: str
) -> None:
    from gaf.cli import EXIT_OK, main

    source = write_numbered_csv(tmp_path / "IndiaProcess(1-3).csv")
    target = tmp_path / f"corpus{flag.strip('-')}.json"
    assert main(["ingest", flag, str(source), "--out", str(target)]) == EXIT_OK
    written = json.loads(target.read_text(encoding="utf-8"))
    assert [r["id"] for r in written["responses"]] == [11, 14, 19]
    assert "3 responses" in capsys.readouterr().out


def test_gaf_ingest_reports_a_trimmed_disagreement(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from gaf.cli import EXIT_OK, main

    source = write_numbered_csv(
        tmp_path / "IndiaProcess(1-3).csv",
        trimmed=[SAMPLE_NUMBERED[0][1], "A different sentence entirely.", SAMPLE_NUMBERED[2][1]],
    )
    assert main(["ingest", "--input", str(source), "--out", str(tmp_path / "c.json")]) == EXIT_OK
    out = capsys.readouterr().out
    assert "Trimmed" in out and "14" in out


def test_gaf_ingest_refuses_a_csv_in_neither_shape(tmp_path: Path) -> None:
    from gaf.cli import EXIT_INPUT, main

    source = write_rows_csv(tmp_path / "other.csv", [("alpha", "beta"), ("one", "two")])
    assert main(["ingest", "--input", str(source), "--out", str(tmp_path / "c.json")]) == EXIT_INPUT


# --------------------------------------------------------------------------- #
# 1b -- code-text pairings and the organiser
# --------------------------------------------------------------------------- #


def test_tagged_pairs_read_from_csv_and_xlsx_are_identical(tmp_path: Path) -> None:
    from_csv = read_tagged_pairs(write_tagged_csv(tmp_path / "p.csv"))
    from_xlsx = read_tagged_pairs(write_tagged_xlsx(tmp_path / "p.xlsx"))
    assert [(p.tag, p.content, p.row) for p in from_csv] == [
        (p.tag, p.content, p.row) for p in from_xlsx
    ]
    assert [p.tag for p in from_csv] == [tag for tag, _ in SAMPLE_PAIRS], "file order is kept"
    # Row 1 is the header, so the first pairing is on row 2 -- the number a spreadsheet
    # shows in its own margin, which is the number a researcher can act on.
    assert [p.row for p in from_csv] == list(range(2, len(SAMPLE_PAIRS) + 2))
    assert all(p.highlight_id == "" for p in from_csv)


def test_tagged_pairs_accept_the_four_column_highlights_export(tmp_path: Path) -> None:
    rows = [(f"h{i}", "Doc (1-100)", tag, content) for i, (tag, content) in enumerate(SAMPLE_PAIRS)]
    path = write_tagged_csv(tmp_path / "hl.csv", rows, header=HIGHLIGHTS_HEADER)
    pairs = read_tagged_pairs(path)
    assert [p.tag for p in pairs] == [tag for tag, _ in SAMPLE_PAIRS]
    assert pairs[0].highlight_id == "h0"
    assert pairs[0].document == "Doc (1-100)"
    assert json.dumps(pairs[0].to_json())


def test_a_pairing_export_missing_its_tag_column_raises_naming_the_file(tmp_path: Path) -> None:
    path = write_tagged_csv(tmp_path / "bad.csv", [("x", "y")], header=("id", "content"))
    with pytest.raises(SpreadsheetFormatError, match=r"bad\.csv"):
        read_tagged_pairs(path)


def test_a_segment_with_no_tag_raises_rather_than_being_placed_under_a_guess(
    tmp_path: Path,
) -> None:
    path = write_tagged_csv(tmp_path / "gap.csv", [("", "moves twice the tonnage")])
    with pytest.raises(SpreadsheetFormatError, match="names no code"):
        read_tagged_pairs(path)


def test_a_tag_with_no_segment_is_kept_for_the_organiser_to_note(tmp_path: Path) -> None:
    """A code the PI applied to nothing is a fact about his coding, not a bad row."""
    path = write_tagged_csv(
        tmp_path / "blank.csv", [("efficiency", "moves twice the tonnage"), ("efficiency", "")]
    )
    pairs = read_tagged_pairs(path)
    assert [p.content for p in pairs] == ["moves twice the tonnage", ""]
    assert any(n.category == "empty_content" for n in organise_tagged(pairs).notes)


def test_a_row_blank_in_both_pairing_columns_is_skipped_and_leaves_a_gap(
    tmp_path: Path,
) -> None:
    """The PI's later workbook carries rows with values only in columns this never reads."""
    path = write_tagged_csv(
        tmp_path / "wide.csv",
        [
            ("efficiency", "moves twice the tonnage", "7"),
            ("", "", "3"),
            ("efficiency", "The port employs fewer people", "1"),
        ],
        header=("tag", "content", "count"),
    )
    pairs = read_tagged_pairs(path)
    assert [p.row for p in pairs] == [2, 4], "the skipped row leaves a visible gap"


def _organised(pairs: tuple[tuple[str, str], ...] = SAMPLE_PAIRS) -> OrganisedCodebook:
    return organise_tagged(
        [TaggedPair(tag=tag, content=content, row=i + 1) for i, (tag, content) in enumerate(pairs)]
    )


def test_the_hierarchy_splits_on_the_first_hyphen_only_and_stays_two_deep() -> None:
    organised = _organised()
    applications = organised.parent("applications")
    assert applications is not None
    assert [leaf.sub for leaf in applications.children] == ["decision-making"]
    assert all(not leaf.children for parent in organised.parents for leaf in parent.children)


def test_a_bare_top_level_code_is_its_own_leaf() -> None:
    efficiency = _organised().parent("efficiency")
    assert efficiency is not None
    assert efficiency.children == () and efficiency.is_leaf
    assert efficiency.count == 2 and len(efficiency.examples) == 2


def test_case_and_whitespace_variants_consolidate_and_every_one_is_recorded() -> None:
    organised = _organised(
        (
            ("efficiency", "moves twice the tonnage"),
            ("Efficiency", "the whole line runs without a shift supervisor"),
            (" efficiency ", "Quality of life improves on average"),
            ("effic iency", "The port employs fewer people"),
        )
    )
    assert [p.name for p in organised.parents] == ["efficiency"]
    assert organised.parents[0].count == 4
    assert {c.from_label: c.rule for c in organised.consolidations} == {
        "Efficiency": "case",
        " efficiency ": "whitespace",
        "effic iency": "whitespace",
    }
    assert all(c.to == "efficiency" for c in organised.consolidations)
    assert all(c.rows for c in organised.consolidations)
    assert all(c.target_also_written for c in organised.consolidations), (
        "`efficiency` was written out as a label of its own"
    )


def test_a_hyphenated_family_token_consolidates_onto_its_underscore_family() -> None:
    organised = _organised()
    assert organised.parent("key") is None, "key-sectors-water is not its own family"
    key_sectors = organised.parent("key_sectors")
    assert key_sectors is not None
    assert sorted(leaf.sub for leaf in key_sectors.children) == ["transport", "water"]
    consolidation = next(c for c in organised.consolidations if c.rule == "family_separator")
    assert (consolidation.from_label, consolidation.to) == (
        "key-sectors-water",
        "key_sectors-water",
    )


def test_a_multi_hyphen_subcode_is_kept_whole_when_no_family_matches() -> None:
    """`applications-decision-making` must not become family `applications_decision`."""
    organised = _organised()
    assert organised.parent("applications_decision") is None
    assert not any(c.from_label == "applications-decision-making" for c in organised.consolidations)


def test_singular_plural_and_spelling_near_misses_are_flagged_never_merged() -> None:
    organised = _organised()
    assert organised.parent("saftey") is not None and organised.parent("safety") is not None
    near = [n for n in organised.notes if n.category == "label_near_miss"]
    assert any("saftey" in n.subject or "saftey" in str(n.data) for n in near)
    assert not any("saftey" in c.from_label for c in organised.consolidations)


def test_ordering_is_frequency_descending_then_name() -> None:
    organised = _organised()
    keys = [(-p.count, p.name) for p in organised.parents]
    assert keys == sorted(keys)
    for parent in organised.parents:
        child_keys = [(-leaf.count, leaf.name) for leaf in parent.children]
        assert child_keys == sorted(child_keys)


def test_each_leaf_gets_two_distinct_examples_by_the_documented_rule() -> None:
    leaf = _organised().leaf("positive_impacts-health")
    assert leaf is not None
    assert len(leaf.examples) == 2
    assert len(set(leaf.examples)) == 2
    assert leaf.example_note == ""
    # The documented rule: longest first, ties broken by the normalised text.
    assert len(leaf.examples[0]) >= len(leaf.examples[1])


def test_a_leaf_with_one_segment_says_so() -> None:
    leaf = _organised().leaf("negative_impacts-dependency")
    assert leaf is not None
    assert len(leaf.examples) == 1
    assert "one" in leaf.example_note.lower()


def test_duplicate_segments_under_one_leaf_do_not_count_as_two_examples() -> None:
    organised = _organised(
        (("efficiency", "moves twice the tonnage"), ("efficiency", "moves twice the tonnage"))
    )
    leaf = organised.leaf("efficiency")
    assert leaf is not None
    assert len(leaf.examples) == 1 and leaf.example_note


def test_a_subcode_label_under_two_parents_is_a_note() -> None:
    notes = {n.subject: n for n in _organised().notes if n.category == "shared_subcode"}
    # `decision-making` sits under two parents; so does `falls`, under the misspelt
    # family and the correct one -- which is exactly the pair a researcher must see.
    assert set(notes) == {"decision-making", "falls"}
    assert sorted(notes["decision-making"].data["parents"]) == ["applications", "improvement"]
    assert sorted(notes["falls"].data["parents"]) == ["safety", "saftey"]


def test_single_segment_leaves_are_noted() -> None:
    notes = [n for n in _organised().notes if n.category == "single_segment_leaf"]
    assert "negative_impacts-dependency" in {n.subject for n in notes}


def test_multi_hyphen_subcodes_are_noted() -> None:
    notes = [n for n in _organised().notes if n.category == "multi_hyphen_subcode"]
    assert "applications-decision-making" in {n.subject for n in notes}


def test_a_bare_top_level_code_beside_sub_coded_families_is_noted() -> None:
    notes = [n for n in _organised().notes if n.category == "bare_top_level_code"]
    assert [n.subject for n in notes] == ["efficiency"]


def test_one_segment_under_several_codes_is_noted() -> None:
    shared = "moves twice the tonnage"
    organised = _organised((("efficiency", shared), ("positive_impacts-general", shared)))
    notes = [n for n in organised.notes if n.category == "segment_under_several_codes"]
    assert len(notes) == 1
    assert sorted(notes[0].data["codes"]) == ["efficiency", "positive_impacts-general"]
    assert not any(n.category == "segment_over_code_limit" for n in organised.notes)


def test_three_codes_on_one_segment_trips_the_s4_limit_note() -> None:
    shared = "moves twice the tonnage"
    organised = _organised(
        (
            ("efficiency", shared),
            ("positive_impacts-general", shared),
            ("improvement-speed", shared),
        )
    )
    over = [n for n in organised.notes if n.category == "segment_over_code_limit"]
    assert len(over) == 1 and over[0].data["code_count"] == 3
    assert over[0].data["limit"] == CodingRules().max_codes_per_segment


def test_the_s4_limit_note_follows_the_rules_argument() -> None:
    shared = "moves twice the tonnage"
    pairs = [
        TaggedPair(tag="efficiency", content=shared, row=1),
        TaggedPair(tag="positive_impacts-general", content=shared, row=2),
    ]
    organised = organise_tagged(pairs, rules=CodingRules(max_codes_per_segment=1))
    assert any(n.category == "segment_over_code_limit" for n in organised.notes)


def test_empty_content_is_noted_rather_than_dropped_silently() -> None:
    pairs = [
        TaggedPair(tag="efficiency", content="moves twice the tonnage", row=1),
        TaggedPair(tag="efficiency", content="   ", row=2),
    ]
    organised = organise_tagged(pairs)
    notes = [n for n in organised.notes if n.category == "empty_content"]
    assert len(notes) == 1 and notes[0].data["row"] == 2
    leaf = organised.leaf("efficiency")
    assert leaf is not None and leaf.count == 1, "an empty segment is not a segment"


def test_organise_tagged_refuses_an_empty_tag(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="empty tag"):
        organise_tagged([TaggedPair(tag="  ", content="moves twice the tonnage", row=1)])


def test_the_renderers_do_not_depend_on_the_order_the_rows_arrived_in() -> None:
    """Two calls in one process share an iteration order and so prove nothing.

    Rewriting the *arrival* order with the row numbers held fixed is the failure this
    module's `sorted` calls exist to prevent: a set or dict iteration leaking into the
    output would move a code, an example or a note.
    """
    rows = [
        TaggedPair(tag=tag, content=content, row=index + 1)
        for index, (tag, content) in enumerate(SAMPLE_PAIRS)
    ]
    shuffled = [rows[i] for i in (9, 2, 13, 5, 0, 11, 7, 3, 12, 1, 8, 4, 10, 6)]
    assert sorted(r.row for r in shuffled) == sorted(r.row for r in rows)

    forward, backward = organise_tagged(rows), organise_tagged(shuffled)
    assert forward.to_json(include_examples=True) == backward.to_json(include_examples=True)
    assert forward.to_markdown(include_examples=True) == backward.to_markdown(
        include_examples=True
    )
    assert forward.to_mermaid() == backward.to_mermaid()


def test_the_organised_json_round_trips_through_json() -> None:
    """A tuple or a set in `to_json` would survive `dumps` and fail to come back."""
    payload = _organised().to_json(include_examples=True)
    assert json.loads(json.dumps(payload, sort_keys=True)) == payload


def test_the_renderers_withhold_examples_unless_asked() -> None:
    organised = _organised()
    example = organised.leaf("negative_impacts-dependency")
    assert example is not None
    quote = example.examples[0]

    assert quote not in organised.to_markdown()
    assert quote not in json.dumps(organised.to_json())
    assert quote in organised.to_markdown(include_examples=True)
    assert quote in json.dumps(organised.to_json(include_examples=True))
    assert quote not in organised.to_mermaid()


def test_the_lookups_answer_none_for_a_name_the_codebook_does_not_have() -> None:
    organised = _organised()
    assert organised.leaf("no_such-code") is None
    assert organised.parent("no_such") is None
    assert organised.canonical("no_such-code") == "no_such-code"
    leaf = organised.leaf("key_sectors-water")
    assert leaf is not None and leaf.parent == "key_sectors" and leaf.level == 2
    assert organised.parents[0].level == 1
    assert "key_sectors-water" in organised.names()


def test_canonical_reaches_a_consolidated_label_through_a_tidied_spelling() -> None:
    """A caller holding a stripped spelling still lands on the same code."""
    organised = _organised(
        (
            (" efficiency ", "moves twice the tonnage"),
            ("efficiency", "The port employs fewer people"),
        )
    )
    assert organised.canonical(" efficiency ") == "efficiency"
    assert organised.canonical("efficiency") == "efficiency"
    assert organised.canonical("efficiency ") == "efficiency", "trivial-key fallback"


def test_a_near_miss_pair_is_reported_once_however_many_ways_it_is_found() -> None:
    organised = _organised(
        (
            ("safety-falls", "something watching for a fall"),
            ("saftey-falls", "nag them about the tablets they skip"),
            ("saftey-falls", "calling a doctor unprompted"),
        )
    )
    subjects = [n.subject for n in organised.notes if n.category == "label_near_miss"]
    assert len(subjects) == len(set(subjects)), "each pair is named once"
    assert "safety ~ saftey" in subjects


def test_two_bare_top_level_codes_are_a_near_miss_reported_once() -> None:
    """A bare top-level code is both a label and a token, so the pair is found twice."""
    organised = _organised(
        (
            ("efficiency", "moves twice the tonnage"),
            ("efficienyc", "The port employs fewer people"),
        )
    )
    near = [n for n in organised.notes if n.category == "label_near_miss"]
    assert [n.subject for n in near] == ["efficiency ~ efficienyc"]
    assert near[0].data["level"] == "label", "the first finding wins; the token repeat is dropped"


def test_a_label_below_the_length_guard_is_not_a_near_miss() -> None:
    """Two edits is most of a short word; flagging those would drown the notes."""
    organised = _organised(
        (("a-b", "moves twice the tonnage"), ("a-c", "The port employs fewer people"))
    )
    assert [n for n in organised.notes if n.category == "label_near_miss"] == []


def test_the_markdown_says_so_when_there_is_nothing_to_flag() -> None:
    bland = organise_tagged(
        [
            TaggedPair(tag="a_family-one", content="moves twice the tonnage", row=1),
            TaggedPair(tag="a_family-one", content="The port employs fewer people", row=2),
        ]
    )
    assert bland.notes == ()
    assert "Nothing to flag." in bland.to_markdown()


def test_the_markdown_has_the_pi_five_section_layout() -> None:
    markdown = _organised().to_markdown()
    for heading in (
        "## 1. Tree Diagram",
        "## 2. Code and Subcode Listing",
        "## 3. Descriptions",
        "## 4. Examples",
        "## 5. Notes for the Researcher",
    ):
        assert heading in markdown
    assert "(no description yet)" in markdown
    assert "n=" in markdown


def test_the_markdown_shows_a_description_once_one_is_attached(tmp_path: Path) -> None:
    definitions = read_definitions_md(write_definitions_md(tmp_path / "cb.md"))
    organised, _ = attach_definitions(_organised(), definitions)
    markdown = organised.to_markdown()
    assert "Doing the same work with less time" in markdown
    assert "(no description yet)" in markdown, "codes the PI never defined still say so"


def test_the_mermaid_matches_the_pi_flowchart_shape() -> None:
    mermaid = _organised().to_mermaid()
    lines = mermaid.splitlines()
    assert lines[0] == "flowchart LR"
    assert lines[1].strip() == 'ROOT(["Codebook"]):::root'
    assert any(line.strip().startswith('P1["') and "<br/>n=" in line for line in lines)
    assert any(line.strip() == "ROOT --> P1" for line in lines)
    assert any(line.strip().startswith('S1["') for line in lines)
    assert sum(1 for line in lines if line.strip().startswith("classDef ")) == 3


def test_the_mermaid_gives_a_bare_top_level_leaf_no_children() -> None:
    mermaid = _organised().to_mermaid()
    node = next(line for line in mermaid.splitlines() if '["efficiency<br/>' in line)
    node_id = node.strip().split("[", 1)[0]
    assert not any(line.strip().startswith(f"{node_id} -->") for line in mermaid.splitlines())


# --------------------------------------------------------------------------- #
# 1b -- to_codebook
# --------------------------------------------------------------------------- #


def test_to_codebook_makes_parents_families_and_leaves_their_children() -> None:
    codebook = to_codebook(_organised())
    assert isinstance(codebook, Codebook)
    health = codebook.by_name("positive_impacts-health")
    parent = codebook.by_name("positive_impacts")
    assert health is not None and parent is not None
    assert health.parent_id == parent.id
    assert parent.parent_id is None
    assert health.meta["source"] == TAGGED_SOURCE == "human-tagged"
    assert parent.meta["source"] == TAGGED_SOURCE


def test_to_codebook_carries_no_evidence_without_placements() -> None:
    codebook = to_codebook(_organised())
    assert all(not code.evidence for code in codebook.codes.values())


def test_to_codebook_takes_descriptions_as_a_mapping() -> None:
    codebook = to_codebook(
        _organised(),
        descriptions={"efficiency": "Less time, effort or cost."},
        description_source="pi-codebook-md",
    )
    code = codebook.by_name("efficiency")
    assert code is not None and code.description == "Less time, effort or cost."


def _placed(tmp_path: Path) -> tuple[OrganisedCodebook, HighlightsReport]:
    corpus = synthetic_corpus()
    pairs = read_tagged_pairs(write_tagged_csv(tmp_path / "pairs.csv"))
    _, report = place_highlights(pairs, corpus)
    return organise_tagged(pairs), report


def test_to_codebook_attaches_placed_segments_as_verified_evidence(tmp_path: Path) -> None:
    organised, placements = _placed(tmp_path)
    codebook = to_codebook(organised, placements=placements)
    health = codebook.by_name("positive_impacts-health")
    assert health is not None
    assert health.evidence, "a placed segment is evidence"
    for evidence in health.evidence:
        assert evidence.verified is True
        assert evidence.span is not None
        start, end = evidence.span
        body = normalise(corpus_by_id()[evidence.response_id].content)
        assert body[start:end] == normalise(evidence.quote)


def test_to_codebook_counts_the_segments_it_could_not_place(tmp_path: Path) -> None:
    organised, placements = _placed(tmp_path)
    codebook = to_codebook(organised, placements=placements)
    efficiency = codebook.by_name("efficiency")
    assert efficiency is not None
    assert efficiency.meta["placed_segments"] + efficiency.meta["unplaced_segments"] == 2
    placed = sum(c.meta.get("placed_segments", 0) for c in codebook.codes.values())
    unplaced = sum(c.meta.get("unplaced_segments", 0) for c in codebook.codes.values())
    assert placed + unplaced == organised.segment_count
    assert placed == placements.mapped


def test_to_codebook_does_not_count_an_unplaced_segment_as_evidence() -> None:
    corpus = synthetic_corpus()
    pairs = [
        TaggedPair(tag="efficiency", content="moves twice the tonnage", row=1),
        TaggedPair(tag="efficiency", content="a sentence that occurs in no response", row=2),
    ]
    _, placements = place_highlights(pairs, corpus)
    code = to_codebook(organise_tagged(pairs), placements=placements).by_name("efficiency")
    assert code is not None
    assert len(code.evidence) == 1
    assert code.meta["placed_segments"] == 1 and code.meta["unplaced_segments"] == 1


def test_to_codebook_records_one_piece_of_evidence_for_a_repeated_segment() -> None:
    corpus = synthetic_corpus()
    segment = "moves twice the tonnage"
    pairs = [
        TaggedPair(tag="efficiency", content=segment, row=1),
        TaggedPair(tag="efficiency", content=segment, row=2),
    ]
    _, placements = place_highlights(pairs, corpus)
    code = to_codebook(organise_tagged(pairs), placements=placements).by_name("efficiency")
    assert code is not None
    assert len(code.evidence) == 1, "the same quote on the same response is one piece of evidence"
    assert code.meta["placed_segments"] == 2, "both rows were still placed, and are counted"


def test_the_codebook_passes_check_codebook_without_an_s6_error(tmp_path: Path) -> None:
    organised, placements = _placed(tmp_path)
    definitions = read_definitions_md(write_definitions_md(tmp_path / "cb.md"))
    organised, _ = attach_definitions(organised, definitions)
    codebook = to_codebook(organised, placements=placements)
    report = check_codebook(codebook, [r.id for r in synthetic_corpus()])
    assert [f for f in report.findings if f.severity is Severity.ERROR] == []


# --------------------------------------------------------------------------- #
# 1c -- the definitions reader
# --------------------------------------------------------------------------- #


def test_definitions_are_keyed_by_the_pipeline_name_form(tmp_path: Path) -> None:
    report = read_definitions_md(write_definitions_md(tmp_path / "cb.md"))
    assert isinstance(report, DefinitionsReport)
    assert "positive_impacts-health" in report.definitions
    assert "positive_impacts" in report.definitions
    assert report.definitions["positive_impacts-health"].startswith("Better diagnosis")
    assert report.counts["positive_impacts-health"] == 2
    assert len(report) == 11, "five top-level codes and six subcodes"
    assert report.subcode_count == 6
    assert "11 descriptions from" in report.summary()
    assert "5 top-level codes (2 of them leaves), 6 subcodes" in report.summary()
    assert "0 lines not parsed" in report.summary()
    assert json.loads(json.dumps(report.to_json())) == report.to_json()


def test_a_top_level_leaf_has_only_the_parent_line(tmp_path: Path) -> None:
    report = read_definitions_md(write_definitions_md(tmp_path / "cb.md"))
    assert "efficiency" in report.definitions
    assert not [name for name in report.definitions if name.startswith("efficiency-")]
    assert "efficiency" in report.top_level_leaves


def test_a_markdown_without_a_descriptions_section_raises(tmp_path: Path) -> None:
    path = tmp_path / "no3.md"
    path.write_text("# Codebook\n\n## 1. Tree Diagram\n\n## 2. Listing\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r"3\. Descriptions"):
        read_definitions_md(path)


def test_an_unparsed_line_is_counted_by_number_never_quoted(tmp_path: Path) -> None:
    loose = "A line this reader has no rule for."
    text = DEFINITIONS_MD.replace(
        "### never_tagged  *(n=0)*", f"### never_tagged  *(n=0)*\n\n{loose}"
    )
    report = read_definitions_md(write_definitions_md(tmp_path / "loose.md", text))
    assert report.unparsed_line_numbers
    assert loose not in json.dumps(report.to_json())
    assert "no rule for" not in json.dumps(report.to_json())


def test_attach_definitions_sets_the_description_and_its_source(tmp_path: Path) -> None:
    definitions = read_definitions_md(write_definitions_md(tmp_path / "cb.md"))
    organised, match = attach_definitions(_organised(), definitions)
    leaf = organised.leaf("positive_impacts-health")
    assert leaf is not None
    assert leaf.description.startswith("Better diagnosis")
    assert organised.meta["description_source"] == DEFINITION_SOURCE == "pi-codebook-md"
    assert match.matched > 0


def test_attach_definitions_works_on_a_codebook_too(tmp_path: Path) -> None:
    definitions = read_definitions_md(write_definitions_md(tmp_path / "cb.md"))
    codebook, match = attach_definitions(to_codebook(_organised()), definitions)
    code = codebook.by_name("efficiency")
    assert code is not None
    assert code.description.startswith("Doing the same work")
    assert code.meta["description_source"] == DEFINITION_SOURCE
    assert match.matched > 0
    assert json.dumps(match.to_json())


def test_attach_definitions_reports_both_directions_of_absence(tmp_path: Path) -> None:
    definitions = read_definitions_md(write_definitions_md(tmp_path / "cb.md"))
    _, match = attach_definitions(_organised(), definitions)
    assert "never_tagged" in match.defined_not_tagged
    assert "safety-falls" in match.tagged_not_defined
    assert "never_tagged" not in match.tagged_not_defined
    assert "the codebook" in match.summary() or "defined" in match.summary()


def test_attach_definitions_reports_names_that_matched_only_after_consolidation(
    tmp_path: Path,
) -> None:
    definitions = read_definitions_md(write_definitions_md(tmp_path / "cb.md"))
    _, match = attach_definitions(_organised(), definitions)
    assert [(m.name, m.from_labels) for m in match.matched_after_consolidation] == [
        ("key_sectors-water", ("key-sectors-water",)),
    ]


def test_attach_definitions_does_no_fuzzy_matching(tmp_path: Path) -> None:
    """`saftey-falls` is one transposition from a defined name and must stay undefined."""
    text = DEFINITIONS_MD.replace(
        "### never_tagged  *(n=0)*\n\n**never_tagged**",
        "### safety  *(n=1)*\n\n**safety**",
    ).replace(
        "A code the descriptions define and the pairings never use.",
        "Freedom from harm.\n\n- **safety > falls** *(n=1)* \u2014 Someone falling over.",
    )
    definitions = read_definitions_md(write_definitions_md(tmp_path / "near.md", text))
    organised, match = attach_definitions(_organised(), definitions)
    assert "saftey-falls" in match.tagged_not_defined
    leaf = organised.leaf("saftey-falls")
    assert leaf is not None and leaf.description == ""
    assert organised.leaf("safety-falls") is not None


def test_attach_definitions_accepts_a_plain_mapping(tmp_path: Path) -> None:
    organised, match = attach_definitions(_organised(), {"efficiency": "Less effort."})
    leaf = organised.leaf("efficiency")
    assert leaf is not None and leaf.description == "Less effort."
    assert match.matched == 1


# --------------------------------------------------------------------------- #
# 1d -- placing highlights on a large corpus
# --------------------------------------------------------------------------- #

def _two_response_segment() -> tuple[str, tuple[int, int]]:
    """A segment present verbatim in exactly two responses, with those two ids."""
    corpus = synthetic_corpus()
    needle = "district"
    holders = tuple(sorted(r.id for r in corpus if needle in r.content))
    assert len(holders) >= 2, "the fixture needs a segment in at least two responses"
    return needle, (holders[0], holders[1])


def test_an_ambiguous_highlight_with_one_candidate_in_the_coded_set_is_resolved() -> None:
    """The one new rule: the coded set breaks a tie that nothing else can break."""
    needle, (first, second) = _two_response_segment()
    corpus = [r for r in synthetic_corpus() if r.id in {first, second}]
    anchor = next(r for r in corpus if r.id == first)
    pairs = [
        TaggedPair(tag="a-anchor", content=anchor.content[:60], row=1),
        TaggedPair(tag="b-tie", content=needle, row=2),
    ]
    assignments, report = place_highlights(pairs, corpus)
    assert report.exact == 1 and report.resolved == 1 and report.ambiguous == 0
    assert report.mapped == 2, "resolved is counted apart from exact and fuzzy, and is mapped"
    tie = next(m for m in report.mappings if m.tag == "b-tie")
    assert tie.outcome == "resolved" and tie.response_id == first
    assert sorted(a.response_id for a in assignments) == sorted([first, first])
    assert "resolved" in report.summary()


def test_an_ambiguous_highlight_with_two_candidates_in_the_coded_set_stays_ambiguous() -> None:
    needle, (first, second) = _two_response_segment()
    corpus = [r for r in synthetic_corpus() if r.id in {first, second}]
    by_id = {r.id: r for r in corpus}
    pairs = [
        TaggedPair(tag="a-anchor", content=by_id[first].content[:60], row=1),
        TaggedPair(tag="a-anchor", content=by_id[second].content[:60], row=2),
        TaggedPair(tag="b-tie", content=needle, row=3),
    ]
    _, report = place_highlights(pairs, corpus)
    assert report.exact == 2 and report.resolved == 0 and report.ambiguous == 1


def test_an_ambiguous_highlight_with_no_candidate_in_the_coded_set_stays_ambiguous() -> None:
    needle, (first, second) = _two_response_segment()
    corpus = [r for r in synthetic_corpus() if r.id in {first, second}]
    pairs = [TaggedPair(tag="b-tie", content=needle, row=1)]
    _, report = place_highlights(pairs, corpus)
    assert report.resolved == 0 and report.ambiguous == 1 and report.mapped == 0


def test_an_unlocated_highlight_is_never_resolved() -> None:
    corpus = synthetic_corpus()
    pairs = [TaggedPair(tag="x-y", content="a sentence that occurs in no response", row=1)]
    _, report = place_highlights(pairs, corpus)
    assert report.unlocated == 1 and report.resolved == 0
    assert report.mappings[0].response_id is None and report.mappings[0].span is None


def _pair_corpus(*bodies: str) -> list[Response]:
    """A tiny corpus of invented responses, for the fuzzy branches of the locator."""
    return [
        Response(id=900 + i, question="q", content=body, source="synthetic-placement")
        for i, body in enumerate(bodies)
    ]


def test_a_retyped_segment_is_placed_fuzzily_and_still_carries_a_span() -> None:
    corpus = _pair_corpus(
        "The depot rota was rebuilt by hand every Monday before the system arrived.",
        "Ferries to the island run on a timetable nobody has revised since 1998.",
    )
    retyped = "The depot rota was rebuilt by hand every Monday before the sytem arrived"
    _, report = place_highlights([TaggedPair(tag="a-b", content=retyped, row=1)], corpus)
    assert report.fuzzy == 1 and report.exact == 0
    mapping = report.mappings[0]
    assert mapping.outcome == "fuzzy" and mapping.response_id == 900
    assert mapping.span is not None and 0.85 <= mapping.score < 1.0


def test_a_segment_close_to_two_responses_is_ambiguous_not_fuzzy() -> None:
    corpus = _pair_corpus(
        "The depot rota was rebuilt by hand every Monday before the system arrived.",
        "The depot rota was rebuilt by hand every Tuesday before the system arrived.",
    )
    retyped = "The depot rota was rebuilt by hand every Monbay before the system arrived"
    _, report = place_highlights([TaggedPair(tag="a-b", content=retyped, row=1)], corpus)
    assert report.ambiguous == 1 and report.fuzzy == 0 and report.resolved == 0
    assert len(report.mappings[0].candidates) == 2


def test_a_fuzzy_ambiguous_highlight_can_be_resolved_and_keeps_a_fuzzy_span() -> None:
    corpus = _pair_corpus(
        "The depot rota was rebuilt by hand every Monday before the system arrived.",
        "The depot rota was rebuilt by hand every Tuesday before the system arrived.",
    )
    retyped = "The depot rota was rebuilt by hand every Monbay before the system arrived"
    pairs = [
        TaggedPair(tag="a-anchor", content="every Monday before the system", row=1),
        TaggedPair(tag="b-tie", content=retyped, row=2),
    ]
    _, report = place_highlights(pairs, corpus)
    assert report.exact == 1 and report.resolved == 1 and report.ambiguous == 0
    tie = next(m for m in report.mappings if m.tag == "b-tie")
    assert tie.response_id == 900
    assert tie.span is not None, "the span comes from the locator, not from a substring search"


def test_an_empty_segment_is_never_placed() -> None:
    corpus = synthetic_corpus()
    _, report = place_highlights([TaggedPair(tag="a-b", content="   ", row=1)], corpus)
    assert report.unlocated == 1 and report.mapped == 0


def test_a_placed_mapping_carries_the_span_it_was_located_at() -> None:
    corpus = synthetic_corpus()
    segment = "Rural clinics get diagnostic support"
    _, report = place_highlights([TaggedPair(tag="a-b", content=segment, row=1)], corpus)
    mapping = report.mappings[0]
    assert mapping.outcome == "exact" and mapping.span is not None
    start, end = mapping.span
    body = normalise(corpus_by_id()[mapping.response_id or 0].content)
    assert body[start:end] == normalise(segment)


def test_place_highlights_is_source_agnostic(tmp_path: Path) -> None:
    corpus = synthetic_corpus()
    from_csv = place_highlights(read_tagged_pairs(write_tagged_csv(tmp_path / "p.csv")), corpus)[1]
    from_xlsx = place_highlights(read_tagged_pairs(write_tagged_xlsx(tmp_path / "p.xlsx")), corpus)[1]
    assert from_csv.to_json() == from_xlsx.to_json()


def test_the_highlights_workbook_reader_still_works_and_reports_resolved(tmp_path: Path) -> None:
    """The four-column path, with a tie the coded set actually resolves.

    `SAMPLE_PAIRS` alone places fourteen exact highlights and nothing else, so a
    numbered assertion is the only way this test can notice that `resolved` stopped
    working: ``mapped == exact + fuzzy + resolved`` is the definition of the property
    and holds whatever the reader does (R1, weak-test scan).
    """
    corpus = synthetic_corpus()
    tie, (first, _second) = _two_response_segment()
    pairs = [*SAMPLE_PAIRS, ("zz-tie", tie)]
    rows = [(str(i), "Doc (1-100)", tag, content) for i, (tag, content) in enumerate(pairs)]
    path = write_tagged_xlsx(tmp_path / "hl.xlsx", rows, header=HIGHLIGHTS_HEADER)
    assignments, report = read_highlights_xlsx(path, corpus)

    assert (report.total, report.exact, report.fuzzy) == (15, 14, 0)
    assert (report.resolved, report.ambiguous, report.unlocated) == (1, 0, 0)
    assert report.mapped == 15 and len(assignments) == 15
    resolved = next(m for m in report.mappings if m.outcome == "resolved")
    assert resolved.tag == "zz-tie" and resolved.response_id == first
    assert report.path.endswith("hl.xlsx")
    assert json.loads(json.dumps(report.to_json())) == report.to_json()


def test_the_placement_report_serialises_every_outcome() -> None:
    """All five outcomes at once, asserted by name rather than by subset.

    A subset test passes when only one outcome occurs, which is what `SAMPLE_PAIRS`
    produces (R1, weak-test scan). The five here are staged deliberately: three
    responses anchored exactly, a word in three responses of which all three are now
    in the coded set (ambiguous), a word in two of which exactly one is (resolved), a
    transposed slice of a fourth response (fuzzy), and an invented sentence
    (unlocated).
    """
    corpus = synthetic_corpus()
    body = {r.id: r.content for r in corpus}
    transposed = body[212][:35] + body[212][36] + body[212][35] + body[212][37:70]
    pairs = [
        TaggedPair(tag="a-anchor", content=body[203][:60], row=1),
        TaggedPair(tag="b-anchor", content=body[207][:60], row=2),
        TaggedPair(tag="c-anchor", content=body[218][:60], row=3),
        TaggedPair(tag="d-ambiguous", content="district", row=4),
        TaggedPair(tag="e-resolved", content="forget", row=5),
        TaggedPair(tag="f-fuzzy", content=transposed, row=6),
        TaggedPair(tag="g-unlocated", content="a sentence that occurs in no response", row=7),
    ]
    _, report = place_highlights(pairs, corpus, path="somewhere.csv")
    payload = report.to_json()
    assert payload["path"] == "somewhere.csv"
    assert [m["outcome"] for m in payload["mappings"]] == [
        "exact",
        "exact",
        "exact",
        "ambiguous",
        "resolved",
        "fuzzy",
        "unlocated",
    ]
    assert (payload["exact"], payload["fuzzy"], payload["resolved"]) == (3, 1, 1)
    assert (payload["ambiguous"], payload["unlocated"], payload["mapped"]) == (1, 1, 5)
    assert payload["coded_response_count"] == 4, "203, 207, 218 exactly and 212 fuzzily"


# --------------------------------------------------------------------------- #
# The provenance scan now reads CSVs as well as workbooks
# --------------------------------------------------------------------------- #


def test_the_provenance_scan_finds_csv_sources_beside_workbooks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tests.test_golden import _real_responses, _real_sources

    write_numbered_csv(tmp_path / "IndiaProcess(1-3).csv")
    write_tagged_csv(tmp_path / "pairs.csv")
    write_tagged_xlsx(tmp_path / "pairs.xlsx")
    monkeypatch.setenv("GAF_REAL_CORPUS", str(tmp_path))

    found = {p.name for p in _real_sources()}
    assert found == {"IndiaProcess(1-3).csv", "pairs.csv", "pairs.xlsx"}

    texts = _real_responses()
    assert any(SAMPLE_NUMBERED[0][1].casefold() in t for t in texts), "CSV prose is scanned"
    assert any(SAMPLE_PAIRS[7][1].casefold() in t for t in texts), "a content column is scanned"
    tags = {tag.casefold() for tag, _ in SAMPLE_PAIRS}
    assert not (tags & set(texts)), "a tag column is skipped, in a CSV as in a workbook"


def test_the_provenance_scan_skips_when_no_source_is_present(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tests.test_golden import _real_responses

    monkeypatch.setenv("GAF_REAL_CORPUS", str(tmp_path / "nothing-here"))
    with pytest.raises(pytest.skip.Exception, match="provenance scan skipped"):
        _real_responses()


# --------------------------------------------------------------------------- #
# R1 audit findings -- ingest
# --------------------------------------------------------------------------- #


def test_a_blank_trimmed_cell_is_reported_as_a_disagreement_not_absorbed(
    tmp_path: Path,
) -> None:
    """R1 I11. An empty `Trimmed` beside a populated `All` is the maximal disagreement."""
    path = write_numbered_csv(
        tmp_path / "blank-trimmed.csv",
        trimmed=[SAMPLE_NUMBERED[0][1], "", SAMPLE_NUMBERED[2][1]],
    )
    rows, disagreements = read_numbered_csv(path)
    assert disagreements == (14,), "a blank Trimmed must not fall back to All in silence"
    assert rows[1].content == SAMPLE_NUMBERED[1][1], "All is the fallback, and it is reported"

    _, report = load_corpus_with_report(path)
    assert report.trimmed_disagreements == (14,)


def test_a_family_with_its_own_segments_and_subcodes_keeps_every_segment() -> None:
    """R1 C3. `alpha` tagged directly, beside `alpha-child`: all three segments count."""
    organised = _organised(
        (
            ("alpha", "Rural clinics get diagnostic support"),
            ("alpha", "The port employs fewer people"),
            ("alpha-child", "moves twice the tonnage"),
        )
    )
    alpha = organised.parent("alpha")
    assert alpha is not None
    assert alpha.count == 3 and alpha.own_count == 2
    assert not alpha.is_leaf and alpha.carries_own_segments
    assert len(alpha.examples) == 2, "the family's own segments are its own examples"
    assert organised.segment_count == 3


def test_a_mixed_family_is_noted_rather_than_absorbed() -> None:
    """R1 C3. The shape is unusual enough that a researcher should be told."""
    organised = _organised(
        (
            ("alpha", "Rural clinics get diagnostic support"),
            ("alpha-child", "moves twice the tonnage"),
        )
    )
    notes = organised.notes_by_category()
    assert [n.subject for n in notes["family_with_own_segments"]] == ["alpha"]
    assert notes["family_with_own_segments"][0].data == {"code": "alpha", "own_count": 1}


def test_a_mixed_family_keeps_the_placement_accounting_invariant() -> None:
    """R1 C3. `placed + unplaced == segment_count` and `placed == mapped`, mixed too."""
    corpus = synthetic_corpus()
    pairs = [
        TaggedPair(tag="alpha", content="Rural clinics get diagnostic support", row=1),
        TaggedPair(tag="alpha", content="The port employs fewer people", row=2),
        TaggedPair(tag="alpha-child", content="moves twice the tonnage", row=3),
    ]
    _, placements = place_highlights(pairs, corpus)
    organised = organise_tagged(pairs)
    codebook = to_codebook(organised, placements=placements)

    alpha = codebook.by_name("alpha")
    assert alpha is not None
    assert alpha.meta["segment_count"] == 2, "its own segments, never its children's"
    assert len(alpha.evidence) == 2

    placed = sum(c.meta.get("placed_segments", 0) for c in codebook.codes.values())
    unplaced = sum(c.meta.get("unplaced_segments", 0) for c in codebook.codes.values())
    assert placed + unplaced == organised.segment_count == 3
    assert placed == placements.mapped


def test_a_mixed_family_renders_its_own_examples() -> None:
    """R1 C3. Section 4 of the rendering is every code that carries segments."""
    organised = _organised(
        (
            ("alpha", "Rural clinics get diagnostic support"),
            ("alpha-child", "moves twice the tonnage"),
        )
    )
    markdown = organised.to_markdown(include_examples=True)
    assert "Rural clinics get diagnostic support" in markdown
    payload = organised.to_json(include_examples=True)
    assert payload["codes"][0]["examples"] == ["Rural clinics get diagnostic support"]


def test_a_bare_family_token_with_the_wrong_separator_consolidates() -> None:
    """R1 I10. `key-sectors` beside `key_sectors-*` is the same family, misspelt."""
    organised = _organised(
        (
            ("key_sectors-water", "Municipal water boards will lean on forecasting engines"),
            ("key_sectors-transport", "Freight is where I notice it first"),
            ("key-sectors", "moves twice the tonnage"),
        )
    )
    assert [p.name for p in organised.parents] == ["key_sectors"]
    rewritten = {c.from_label: (c.to, c.rule) for c in organised.consolidations}
    assert rewritten["key-sectors"] == ("key_sectors", "family_separator")


def test_a_hyphenless_label_never_collects_a_family_separator_rule() -> None:
    """R1 I10. Deleting the guard must not label an untouched rewrite a separator fix."""
    organised = _organised(
        (
            ("efficiency", "moves twice the tonnage"),
            ("Efficiency", "The port employs fewer people"),
            ("efficiency-yard", "drivers dispatched to the yard the moment a lorry is free"),
        )
    )
    rules = {c.from_label: c.rule for c in organised.consolidations}
    assert rules == {"Efficiency": "case"}


def test_to_codebook_records_where_a_supplied_description_came_from() -> None:
    """R1 I12. A description must never travel further than its provenance."""
    codebook = to_codebook(
        _organised(),
        descriptions={"efficiency": "Less time, effort or cost."},
        description_source="pi-codebook-md",
    )
    code = codebook.by_name("efficiency")
    assert code is not None
    assert code.meta["description_source"] == "pi-codebook-md"

    undescribed = codebook.by_name("positive_impacts-health")
    assert undescribed is not None
    assert "description_source" not in undescribed.meta


def test_to_codebook_refuses_descriptions_with_no_source() -> None:
    """R1 I12. Silence about provenance is the failure D2 exists to prevent."""
    with pytest.raises(ValueError, match="description_source"):
        to_codebook(_organised(), descriptions={"efficiency": "Less time, effort or cost."})


def test_matched_after_consolidation_excludes_a_name_that_was_also_written_plainly(
    tmp_path: Path,
) -> None:
    """R1 I9(a). A code tagged verbatim did not match "only after" anything."""
    organised = _organised(
        (
            ("alpha-one", "Rural clinics get diagnostic support"),
            ("alpha-one", "The port employs fewer people"),
            ("Alpha-One", "moves twice the tonnage"),
        )
    )
    _, match = attach_definitions(organised, {"alpha-one": "A description."})
    assert match.matched == 1
    assert match.matched_after_consolidation == ()


def test_matched_after_consolidation_keeps_every_variant_of_a_many_to_one_fold() -> None:
    """R1 I9(b). Three spellings folding onto one name are three rewrites, not one."""
    organised = _organised(
        (
            ("key_sectors-transport", "Freight is where I notice it first"),
            ("key-sectors-water", "Municipal water boards will lean on forecasting engines"),
            ("Key-Sectors-Water", "moves twice the tonnage"),
            (" key-sectors-water ", "The port employs fewer people"),
        )
    )
    _, match = attach_definitions(organised, {"key_sectors-water": "A description."})
    assert [(m.name, m.from_labels) for m in match.matched_after_consolidation] == [
        (
            "key_sectors-water",
            (" key-sectors-water ", "Key-Sectors-Water", "key-sectors-water"),
        ),
    ]
    assert "3 spelling(s)" in match.summary()
    payload = match.to_json()
    assert payload["matched_after_consolidation"] == [
        {
            "name": "key_sectors-water",
            "from_labels": [" key-sectors-water ", "Key-Sectors-Water", "key-sectors-water"],
        }
    ]


def test_the_definitions_summary_counts_subcodes_from_what_it_parsed(
    tmp_path: Path,
) -> None:
    """R1 Minor. A heading with no parent line must not push the count negative."""
    text = DEFINITIONS_MD.replace(
        "### never_tagged  *(n=0)*\n\n"
        "**never_tagged** — A code the descriptions define and the pairings never use.",
        "### headingless  *(n=0)*\n\n### headingless  *(n=0)*",
    )
    report = read_definitions_md(write_definitions_md(tmp_path / "odd.md", text))
    assert "headingless" not in report.definitions
    assert report.parents.count("headingless") == 1, "a repeated heading is one code"
    assert "6 subcodes" in report.summary()
    assert "5 top-level codes" in report.summary()


def test_a_resolved_highlight_scores_at_the_response_it_was_placed_on() -> None:
    """R1 brief Important. `Evidence(verified=True, score=0.0)` on a verbatim match."""
    needle, (first, second) = _two_response_segment()
    corpus = [r for r in synthetic_corpus() if r.id in {first, second}]
    anchor = next(r for r in corpus if r.id == first)
    pairs = [
        TaggedPair(tag="a-anchor", content=anchor.content[:60], row=1),
        TaggedPair(tag="b-tie", content=needle, row=2),
    ]
    _, report = place_highlights(pairs, corpus)
    resolved = [m for m in report.mappings if m.outcome == "resolved"]
    assert len(resolved) == 1
    assert resolved[0].score == 1.0, "an exact substring of the chosen response scores 1.0"

    codebook = to_codebook(
        organise_tagged(pairs), placements=report
    )
    tie = codebook.by_name("b-tie")
    assert tie is not None and len(tie.evidence) == 1
    assert tie.evidence[0].verified is True and tie.evidence[0].score == 1.0
