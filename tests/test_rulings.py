"""The PI's rulings on his own export (ADR-0050), and what each one does.

Five claims, each tested on invented data:

1. **A rulings file is validated, not trusted.** Unknown keys, wrong types, a merge onto
   itself and a chain of merges are refused; a missing manual-placement file is a no-op
   and a malformed one is not.
2. **A label merge is a recorded, provisional consolidation.** It runs after the trivial
   rules, can rename a label whose correct spelling was never written, carries its
   ``provisional`` flag, and carries a definition keyed by the old spelling to the new
   one without ever replacing a definition the target already had.
3. **A top-level ruling suppresses the bare-code note and is recorded instead.**
4. **Multi-placement is opt-in and exact.** A highlight with two or more candidates in
   the coded set goes into every one of them (outcome ``multi_placed``); with none in the
   set, or with the rule off, it stays ambiguous. Evidence, ``placed_segments`` and the
   golden rows follow.
5. **A manual placement is applied after both passes** and only ever with a reason when
   it is not.

Every label, segment and response below is invented. The segments are substrings of
the invented bodies in this file, and no real survey response, or fragment of one, is
read or written by it.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from gaf.analysis.matrix import assignments_from_codebook
from gaf.cli import EXIT_INPUT, EXIT_OK, main
from gaf.ingest.corpus import write_corpus_json
from gaf.ingest.definitions import attach_definitions
from gaf.ingest.rulings import (
    HeldMerge,
    LabelMerge,
    Rulings,
    RulingsError,
    load_manual_placements,
    load_rulings,
    parse_manual_placements,
    parse_rulings,
)
from gaf.ingest.tagged import TaggedPair, organise_tagged, read_tagged_pairs, to_codebook
from gaf.ingest.xlsx import HighlightsReport, place_highlights
from gaf.models import Response
from tests.fixtures.corpus import synthetic_corpus
from tests.fixtures.tagged import write_tagged_csv

REPO_ROOT = Path(__file__).resolve().parents[1]

BODIES = (
    "The depot rota was rebuilt by hand every Monday before the system arrived.",  # 900
    "Harbour cranes now schedule themselves around the tide tables each morning.",  # 901
    "The depot rota is something the night shift still argues about in winter.",  # 902
    "Ferries to the island run on a timetable nobody has revised since long ago.",  # 903
    "Nobody on the late shift trusts the depot rota after the long autumn.",  # 904
    "Ferries are cancelled whenever the tide tables disagree with the harbour office.",  # 905
)


def corpus(*bodies: str) -> list[Response]:
    return [
        Response(id=900 + i, question="q", content=body, source="synthetic-rulings")
        for i, body in enumerate(bodies or BODIES)
    ]


def pair(tag: str, content: str, row: int = 1, hid: str = "") -> TaggedPair:
    return TaggedPair(tag=tag, content=content, row=row, highlight_id=hid)


#: Anchors that place exactly on one response each, so the coded set is {900, 902}.
ANCHORS = (
    pair("a-anchor", "rebuilt by hand every Monday", 1),
    pair("a-anchor", "night shift still argues", 2),
)


# --------------------------------------------------------------------------- #
# 1. The file is validated
# --------------------------------------------------------------------------- #


def test_an_empty_object_is_a_rulings_file_that_rules_nothing() -> None:
    rulings = parse_rulings({})
    assert rulings == Rulings()
    assert not rulings.multi_place_ambiguous and not rulings.label_merges


def test_a_full_rulings_file_round_trips() -> None:
    payload = {
        "description": "d",
        "top_level": ["efficiency"],
        "label_merges": [{"from": "a-b", "to": "a-c", "provisional": False, "reason": "typo"}],
        "label_merges_held": [{"labels": ["x", "y"], "level": "token", "reason": "r"}],
        "multi_place_ambiguous": True,
        "manual_placements": {"7": 903},
        "manual_placements_file": "runs/m.json",
    }
    rulings = parse_rulings(payload)
    assert rulings.label_merges == (LabelMerge("a-b", "a-c", False, "typo"),)
    assert rulings.label_merges_held == (HeldMerge(("x", "y"), "token", "r"),)
    assert rulings.to_json() == payload
    assert rulings.merge_map()["a-b"].target == "a-c"


@pytest.mark.parametrize(
    "payload, fragment",
    [
        ([], "one JSON object"),
        ({"top_levle": []}, "unknown key"),
        ({"top_level": "efficiency"}, "list of non-empty"),
        ({"top_level": ["a", "a"]}, "twice"),
        ({"label_merges": {}}, "must be a list"),
        ({"label_merges": ["x"]}, "must be an object"),
        ({"label_merges": [{"from": "a", "to": "a"}]}, "onto itself"),
        ({"label_merges": [{"from": "", "to": "a"}]}, "non-empty"),
        ({"label_merges": [{"from": "a", "to": "b", "provisional": "yes"}]}, "true or false"),
        ({"label_merges": [{"from": "a", "to": "b", "why": "x"}]}, "unknown key"),
        (
            {"label_merges": [{"from": "a", "to": "b"}, {"from": "a", "to": "c"}]},
            "same label",
        ),
        (
            {"label_merges": [{"from": "a", "to": "b"}, {"from": "b", "to": "c"}]},
            "both rewritten",
        ),
        ({"label_merges_held": {}}, "must be a list"),
        ({"label_merges_held": ["x"]}, "must be an object"),
        ({"label_merges_held": [{"labels": ["only-one"]}]}, "'labels'"),
        ({"label_merges_held": [{"labels": ["a", "b"], "extra": 1}]}, "unknown key"),
        ({"multi_place_ambiguous": "on"}, "true or false"),
        ({"manual_placements_file": 3}, "path string"),
        ({"manual_placements": []}, "must be an object"),
        ({"manual_placements": {"1": "903"}}, "whole response id"),
        ({"manual_placements": {"1": True}}, "whole response id"),
    ],
)
def test_a_malformed_rulings_file_is_refused_by_name(payload: Any, fragment: str) -> None:
    with pytest.raises(RulingsError, match=fragment):
        parse_rulings(payload)


def test_load_rulings_records_the_path_and_a_hash_and_names_the_file_on_error(
    tmp_path: Path,
) -> None:
    good = tmp_path / "r.json"
    good.write_text('{"multi_place_ambiguous": true}', encoding="utf-8")
    rulings = load_rulings(good)
    assert rulings.multi_place_ambiguous and rulings.path == str(good)
    assert len(rulings.content_hash) == 16
    good.write_text('{"multi_place_ambiguous": false}', encoding="utf-8")
    assert load_rulings(good).content_hash != rulings.content_hash

    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(RulingsError, match=r"bad\.json"):
        load_rulings(bad)
    bad.write_text('{"nope": 1}', encoding="utf-8")
    with pytest.raises(RulingsError, match=r"bad\.json"):
        load_rulings(bad)
    with pytest.raises(RulingsError, match=r"missing\.json"):
        load_rulings(tmp_path / "missing.json")
    bad.write_bytes(b"\xff\xfe")
    with pytest.raises(RulingsError, match="not valid JSON"):
        load_rulings(bad)


def test_the_tracked_rulings_file_is_valid_and_says_what_it_does() -> None:
    rulings = load_rulings(REPO_ROOT / "rulings" / "india-process.json")
    assert rulings.description and "\n" not in rulings.description
    assert rulings.top_level == ("efficiency",)
    assert rulings.multi_place_ambiguous is True
    assert all(merge.provisional for merge in rulings.label_merges)
    assert rulings.manual_placements == {}, "the real mapping is local, never tracked"
    assert rulings.manual_placements_file.startswith("runs/")
    # every held pair is a pair of labels, and none of them is also merged
    merged = {m.source for m in rulings.label_merges} | {m.target for m in rulings.label_merges}
    assert not merged & {label for held in rulings.label_merges_held for label in held.labels}


def test_a_manual_placement_file_that_is_not_there_is_a_no_op(tmp_path: Path) -> None:
    assert load_manual_placements(tmp_path / "nothing.json") == ({}, False)
    assert parse_manual_placements(None) == {}


def test_a_manual_placement_file_that_is_there_must_be_readable(tmp_path: Path) -> None:
    path = tmp_path / "m.json"
    path.write_text('{"12": 903, "13": 900}', encoding="utf-8")
    assert load_manual_placements(path) == ({"12": 903, "13": 900}, True)
    path.write_text("[1, 2]", encoding="utf-8")
    with pytest.raises(RulingsError, match="object"):
        load_manual_placements(path)
    path.write_text("{oops", encoding="utf-8")
    with pytest.raises(RulingsError, match="cannot read"):
        load_manual_placements(path)


# --------------------------------------------------------------------------- #
# 2. Label merges
# --------------------------------------------------------------------------- #


def _typo_pairs() -> list[TaggedPair]:
    return [
        pair("safety-home", "one", 2),
        pair("safety-home", "two", 3),
        pair("safety-travel", "three", 4),
        pair("challenges-saftey", "four", 5),
        pair("challenges-saftey", "five", 6),
    ]


def _merge(**extra: Any) -> Rulings:
    return Rulings(
        label_merges=(
            LabelMerge("challenges-saftey", "challenges-safety", extra.get("provisional", True)),
        ),
        **{k: v for k, v in extra.items() if k != "provisional"},
    )


def test_a_label_merge_renames_a_label_whose_correct_spelling_was_never_written() -> None:
    organised = organise_tagged(_typo_pairs(), rulings=_merge())
    assert "challenges-safety" in organised.names() or any(
        c.name == "challenges-safety" for c in organised.leaves()
    )
    assert not any(c.name == "challenges-saftey" for c in organised.leaves())
    (merge,) = [c for c in organised.consolidations if c.ruling]
    assert (merge.from_label, merge.to, merge.rule) == (
        "challenges-saftey",
        "challenges-safety",
        "label_merge",
    )
    assert merge.provisional and merge.rows == (5, 6) and not merge.target_also_written
    assert merge.to_json()["ruling"] is True and merge.to_json()["provisional"] is True
    assert organised.canonical("challenges-saftey") == "challenges-safety"


def test_a_merge_is_provisional_only_when_the_ruling_says_so() -> None:
    organised = organise_tagged(_typo_pairs(), rulings=_merge(provisional=False))
    (merge,) = [c for c in organised.consolidations if c.ruling]
    assert merge.provisional is False and merge.to_json()["provisional"] is False


def test_a_merge_onto_a_label_that_exists_adds_its_segments_to_it() -> None:
    pairs = [*_typo_pairs(), pair("challenges-safety", "six", 7)]
    organised = organise_tagged(pairs, rulings=_merge())
    target = organised.leaf("challenges-safety")
    assert target is not None and target.count == 3
    (merge,) = [c for c in organised.consolidations if c.ruling]
    assert merge.target_also_written is True


def test_a_merge_runs_after_the_trivial_rules_and_keeps_both_in_the_rule() -> None:
    pairs = [pair("Challenges-Saftey", "one", 2), pair("challenges-saftey", "two", 3)]
    organised = organise_tagged(pairs, rulings=_merge())
    rules = {c.from_label: c.rule for c in organised.consolidations}
    assert rules["Challenges-Saftey"] == "case+label_merge"
    assert rules["challenges-saftey"] == "label_merge"
    assert organised.leaf("challenges-safety") is not None


def test_a_merge_removes_the_near_miss_it_resolves_and_keeps_the_others() -> None:
    pairs = [*_typo_pairs(), pair("alpha-research", "x", 7), pair("alpha-search", "y", 8)]
    before = organise_tagged(pairs).notes_by_category()["label_near_miss"]
    after = organise_tagged(pairs, rulings=_merge()).notes_by_category()["label_near_miss"]
    assert any("saftey" in note.subject for note in before)
    assert not any("saftey" in note.subject for note in after)
    assert any("research" in note.subject for note in after)


def test_a_merge_naming_a_label_the_export_does_not_hold_is_recorded_not_applied() -> None:
    rulings = Rulings(label_merges=(LabelMerge("never-written", "never-wrote"),))
    organised = organise_tagged(_typo_pairs(), rulings=rulings)
    (entry,) = organised.meta["rulings"]["label_merges"]
    assert entry["applied"] is False and entry["rows"] == [] and entry["segments"] == 0
    assert not [c for c in organised.consolidations if c.ruling]


def test_the_trail_names_each_ruling_and_holds_no_segment() -> None:
    rulings = Rulings(
        description="trail test",
        top_level=("efficiency", "absent-label"),
        label_merges=(LabelMerge("challenges-saftey", "challenges-safety"),),
        label_merges_held=(
            HeldMerge(("safety-home", "safety-travel"), "label", "different codes"),
            HeldMerge(("deskilling", "upskilling"), "token", "opposites"),
        ),
        multi_place_ambiguous=True,
        path="rulings/test.json",
        content_hash="abc",
    )
    organised = organise_tagged([*_typo_pairs(), pair("efficiency", "e", 7)], rulings=rulings)
    trail = organised.meta["rulings"]
    assert trail["path"] == "rulings/test.json" and trail["content_hash"] == "abc"
    assert trail["description"] == "trail test" and trail["multi_place_ambiguous"] is True
    assert trail["top_level"] == [
        {"label": "efficiency", "present": True, "count": 1, "subcodes": 0},
        {"label": "absent-label", "present": False, "count": 0, "subcodes": 0},
    ]
    held = trail["label_merges_held"]
    assert held[0]["both_present"] is True and "both_present" not in held[1]
    blob = json.dumps(trail)
    for text in ("one", "two", "three", "four", "five"):
        assert f'"{text}"' not in blob, "a segment must never travel in the trail"
    assert json.loads(json.dumps(organised.to_json(include_examples=True)))["meta"]["rulings"]


def test_the_markdown_lists_the_rulings_and_marks_the_merge_provisional() -> None:
    rulings = Rulings(
        description="md test",
        top_level=("efficiency",),
        label_merges=(LabelMerge("challenges-saftey", "challenges-safety"),),
        label_merges_held=(HeldMerge(("safety-home", "safety-travel")),),
    )
    organised = organise_tagged([*_typo_pairs(), pair("efficiency", "e", 7)], rulings=rulings)
    text = organised.to_markdown()
    assert "**rulings applied**" in text and "md test" in text
    assert "label merge (provisional): `challenges-saftey` -> `challenges-safety`" in text
    assert "top level: `efficiency` -- top-level code, 1 segment(s), 0 subcode(s)" in text
    assert "held, not merged: `safety-home` ~ `safety-travel` (label)" in text
    assert "label_merge, PI ruling, provisional; rows 5, 6" in text


def test_without_rulings_nothing_is_added_anywhere() -> None:
    organised = organise_tagged(_typo_pairs())
    assert "rulings" not in organised.meta
    assert not any(c.ruling for c in organised.consolidations)
    assert all("ruling" not in c.to_json() for c in organised.consolidations)
    assert "rulings applied" not in organised.to_markdown()


def test_a_definition_keyed_by_the_old_spelling_goes_to_the_new_one() -> None:
    organised = organise_tagged(_typo_pairs(), rulings=_merge())
    described, match = attach_definitions(
        organised,
        {
            "challenges-saftey": "the old spelling's definition",
            "safety-home": "a",
            "safety-travel": "b",
            "challenges": "c",
            "safety": "d",
        },
    )
    leaf = described.leaf("challenges-safety")
    assert leaf is not None and leaf.description == "the old spelling's definition"
    assert match.defined_not_tagged == () and match.tagged_not_defined == ()
    assert [(m.name, m.from_labels) for m in match.matched_after_consolidation] == [
        ("challenges-safety", ("challenges-saftey",))
    ]


def test_a_merge_never_replaces_a_definition_the_target_already_has() -> None:
    organised = organise_tagged(_typo_pairs(), rulings=_merge())
    described, match = attach_definitions(
        organised,
        {"challenges-saftey": "old", "challenges-safety": "new", "safety-home": "a"},
    )
    leaf = described.leaf("challenges-safety")
    assert leaf is not None and leaf.description == "new"
    assert match.defined_not_tagged == ("challenges-saftey",)


def test_a_definition_keyed_by_a_trivially_consolidated_spelling_is_matched_too() -> None:
    organised = organise_tagged([pair("Alpha-one", "x", 2), pair("alpha-one", "y", 3)])
    assert organised.canonical("Alpha-one") == "alpha-one"
    described, match = attach_definitions(organised, {"Alpha-one": "text", "alpha": "family"})
    leaf = described.leaf("alpha-one")
    assert leaf is not None and leaf.description == "text"
    assert match.defined_not_tagged == () and match.tagged_not_defined == ()


# --------------------------------------------------------------------------- #
# 3. Top-level rulings
# --------------------------------------------------------------------------- #


def _top_level_pairs() -> list[TaggedPair]:
    return [
        pair("efficiency", "e1", 2),
        pair("efficiency", "e2", 3),
        pair("positive-health", "h", 4),
        pair("positive-jobs", "j", 5),
    ]


def test_a_bare_top_level_code_is_noted_unless_the_pi_ruled_it_top_level() -> None:
    plain = organise_tagged(_top_level_pairs()).notes_by_category()
    assert [n.subject for n in plain["bare_top_level_code"]] == ["efficiency"]
    ruled = organise_tagged(_top_level_pairs(), rulings=Rulings(top_level=("efficiency",)))
    assert "bare_top_level_code" not in ruled.notes_by_category()
    family = ruled.parent("efficiency")
    assert family is not None and family.is_leaf and family.count == 2


def test_the_ruling_reaches_the_codebook_as_a_flag_on_that_code_only() -> None:
    ruled = organise_tagged(_top_level_pairs(), rulings=Rulings(top_level=("efficiency",)))
    book = to_codebook(ruled)
    flagged = [code.name for code in book.codes.values() if code.meta.get("ruled_top_level")]
    assert flagged == ["efficiency"]
    plain = to_codebook(organise_tagged(_top_level_pairs()))
    assert not any("ruled_top_level" in code.meta for code in plain.codes.values())


def test_a_ruling_for_a_label_the_export_lacks_flags_nothing() -> None:
    ruled = organise_tagged(_top_level_pairs(), rulings=Rulings(top_level=("not-there",)))
    assert "bare_top_level_code" in ruled.notes_by_category()
    assert not any(c.meta.get("ruled_top_level") for c in to_codebook(ruled).codes.values())


# --------------------------------------------------------------------------- #
# 4. Multi-placement
# --------------------------------------------------------------------------- #


def _depot_pairs(*extra: TaggedPair) -> list[TaggedPair]:
    return [*ANCHORS, pair("b-tie", "depot rota", 3, "h-tie"), *extra]


def test_the_rule_is_off_by_default_and_the_output_is_the_old_output() -> None:
    _, report = place_highlights(_depot_pairs(), corpus())
    assert report.ambiguous == 1 and report.multi_placed == 0 and report.mapped == 2
    payload = report.to_json()
    assert "multi_placed" not in payload and "manual" not in payload
    assert "multi_place_enabled" not in payload
    assert "multi-placed" not in report.summary()
    explicit = place_highlights(_depot_pairs(), corpus(), multi_place=False)[1]
    assert explicit.to_json() == payload


def test_a_highlight_with_two_candidates_in_the_coded_set_goes_into_both() -> None:
    assignments, report = place_highlights(_depot_pairs(), corpus(), multi_place=True)
    assert (report.exact, report.resolved, report.multi_placed, report.ambiguous) == (2, 0, 1, 0)
    assert report.multi_placements == 2
    rows = [m for m in report.mappings if m.outcome == "multi_placed"]
    assert sorted(m.response_id for m in rows if m.response_id is not None) == [900, 902]
    assert all(m.span is not None and m.score == 1.0 for m in rows)
    assert all(m.candidates == (900, 902, 904) for m in rows), "the 904 outside stays visible"
    assert report.total == 3 and report.mapped == 3
    assert report.per_response == {900: 2, 902: 2}
    tie = [a for a in assignments if a.code == "b-tie"]
    assert sorted(a.response_id for a in tie) == [900, 902]
    assert "1 multi-placed (2 placements)" in report.summary()
    payload = report.to_json()
    assert payload["multi_place_enabled"] is True
    assert (payload["multi_placed"], payload["multi_placements"]) == (1, 2)


def test_a_third_candidate_inside_the_coded_set_is_placed_too() -> None:
    pairs = [*ANCHORS, pair("c-anchor", "trusts the depot rota after", 3), *_depot_pairs()[2:]]
    _, report = place_highlights(pairs, corpus(), multi_place=True)
    assert report.multi_placed == 1 and report.multi_placements == 3
    ids = sorted(m.response_id or 0 for m in report.mappings if m.outcome == "multi_placed")
    assert ids == [900, 902, 904]


def test_a_highlight_with_no_candidate_in_the_coded_set_stays_ambiguous() -> None:
    pairs = [*ANCHORS, pair("b-tie", "Ferries", 3)]
    _, report = place_highlights(pairs, corpus(), multi_place=True)
    assert report.ambiguous == 1 and report.multi_placed == 0
    assert report.mapped == 2
    assert report.to_json()["multi_placed"] == 0, "enabled but nothing qualified is still stated"


def test_a_highlight_with_exactly_one_candidate_in_the_coded_set_is_still_resolved() -> None:
    pairs = [*ANCHORS, pair("c-anchor", "cranes now schedule", 3), pair("b-tie", "tide tables", 4)]
    _, report = place_highlights(pairs, corpus(), multi_place=True)
    assert report.resolved == 1 and report.multi_placed == 0
    tie = next(m for m in report.mappings if m.tag == "b-tie")
    assert tie.outcome == "resolved" and tie.response_id == 901


def test_the_multi_placed_outcome_does_not_depend_on_the_order_of_the_rows() -> None:
    forward = place_highlights(_depot_pairs(), corpus(), multi_place=True)[1]
    reverse = place_highlights(list(reversed(_depot_pairs())), corpus(), multi_place=True)[1]
    assert (forward.multi_placed, forward.multi_placements) == (
        reverse.multi_placed,
        reverse.multi_placements,
    )
    assert sorted((m.tag, m.response_id) for m in forward.mappings) == sorted(
        (m.tag, m.response_id) for m in reverse.mappings
    )


def test_a_multi_placed_highlight_is_one_segment_and_several_pieces_of_evidence() -> None:
    pairs = _depot_pairs()
    organised = organise_tagged(pairs)
    _, report = place_highlights(pairs, corpus(), multi_place=True)
    book = to_codebook(organised, placements=report)
    tie = next(code for code in book.codes.values() if code.name == "b-tie")
    assert sorted(e.response_id for e in tie.evidence) == [900, 902]
    assert all(e.verified for e in tie.evidence)
    assert tie.meta["segment_count"] == 1
    assert tie.meta["placed_segments"] == 1 and tie.meta["unplaced_segments"] == 0
    golden = [(a.response_id, a.code) for a in assignments_from_codebook(book)]
    assert (900, "b-tie") in golden and (902, "b-tie") in golden


def test_the_report_round_trips_through_the_placement_json_shape() -> None:
    from gaf.cli.codebook import placements_from_json

    _, report = place_highlights(
        _depot_pairs(),
        corpus(),
        multi_place=True,
        manual_placements={"h-tie": 903, "h-none": 900},
    )
    again = placements_from_json(json.loads(json.dumps(report.to_json())))
    assert again.to_json() == report.to_json()
    assert isinstance(again, HighlightsReport)


# --------------------------------------------------------------------------- #
# 5. Manual placements
# --------------------------------------------------------------------------- #


def test_no_manual_placements_is_a_no_op() -> None:
    plain = place_highlights(_depot_pairs(), corpus())[1]
    for empty in (None, {}):
        assert place_highlights(_depot_pairs(), corpus(), manual_placements=empty)[1].to_json() == (
            plain.to_json()
        )


def test_a_manual_placement_settles_an_ambiguous_highlight_after_both_passes() -> None:
    assignments, report = place_highlights(
        _depot_pairs(), corpus(), manual_placements={"h-tie": 904}
    )
    tie = next(m for m in report.mappings if m.tag == "b-tie")
    assert tie.outcome == "manual" and tie.response_id == 904 and tie.span is not None
    assert report.manual == 1 and report.ambiguous == 0 and report.mapped == 3
    assert report.manual_applied == (("h-tie", 904, "ambiguous"),)
    assert report.manual_unapplied == () and report.manual_requested == 1
    assert (904, "b-tie") in [(a.response_id, a.code) for a in assignments]
    assert "1 placed by hand" in report.summary()
    payload = report.to_json()
    assert (payload["manual"], payload["manual_requested"]) == (1, 1)
    assert payload["manual_applied"] == [["h-tie", 904, "ambiguous"]]
    # the coded set is a fact about pass one and is not moved by the PI's answer
    assert report.coded_response_count == 2


def test_a_manual_placement_replaces_a_multi_placement_with_one_row() -> None:
    _, report = place_highlights(
        _depot_pairs(), corpus(), multi_place=True, manual_placements={"h-tie": 902}
    )
    rows = [m for m in report.mappings if m.tag == "b-tie"]
    assert [(m.outcome, m.response_id) for m in rows] == [("manual", 902)]
    assert report.multi_placed == 0 and report.manual == 1
    assert report.manual_applied == (("h-tie", 902, "multi_placed"),)


def test_a_manual_placement_can_place_an_unlocated_highlight_by_the_nearest_span() -> None:
    pairs = [*ANCHORS, pair("z-lost", "the night shift argues at winter", 3, "h-lost")]
    _, plain = place_highlights(pairs, corpus())
    assert plain.unlocated == 1
    _, report = place_highlights(pairs, corpus(), manual_placements={"h-lost": 902})
    lost = next(m for m in report.mappings if m.tag == "z-lost")
    assert lost.outcome == "manual" and lost.response_id == 902 and lost.span is not None
    assert 0.0 < lost.score < 1.0, "the score it earned is kept, not rounded up to the PI's word"
    assert report.unlocated == 0 and report.manual_applied == (("h-lost", 902, "unlocated"),)


def test_a_manual_placement_may_correct_a_text_placement() -> None:
    _, report = place_highlights(
        _depot_pairs(), corpus(), manual_placements={"0": 904}
    )
    first = report.mappings[0]
    assert first.outcome == "manual" and first.response_id == 904
    assert report.manual_applied[0][2] == "exact"


def test_a_manual_placement_that_cannot_be_applied_says_why() -> None:
    _, report = place_highlights(
        _depot_pairs(),
        corpus(),
        manual_placements={"h-tie": 123456, "no-such-highlight": 900},
    )
    assert report.manual == 0 and report.manual_requested == 2
    reasons = dict(report.manual_unapplied)
    assert "not in the corpus" in reasons["h-tie"]
    assert "no highlight" in reasons["no-such-highlight"]
    assert report.ambiguous == 1, "nothing was placed"


def test_a_manual_placement_for_text_with_no_words_in_the_target_is_refused() -> None:
    blank = [*corpus(), Response(id=990, question="q", content="   ", source="s")]
    _, report = place_highlights(
        _depot_pairs(), blank, manual_placements={"h-tie": 990}
    )
    assert report.manual == 0
    assert "cannot be given a span" in dict(report.manual_unapplied)["h-tie"]


# --------------------------------------------------------------------------- #
# The command
# --------------------------------------------------------------------------- #


def run_cli(*argv: str) -> int:
    return main(list(argv))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def inputs(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    """A synthetic corpus, and pairings with one tie that two coded responses share."""
    root = tmp_path_factory.mktemp("rulings-cli")
    bodies = synthetic_corpus()
    needle = "district"
    holders = sorted(r.id for r in bodies if needle in r.content)[:2]
    by_id = {r.id: r for r in bodies}
    rows = [
        ("zz-anchor", by_id[holders[0]].content[:60]),
        ("zz-anchor", by_id[holders[1]].content[:60]),
        ("tie-code", needle),
        ("efficiency", "moves twice the tonnage"),
        ("safety-falls", "something watching for a fall"),
        ("saftey-falls", "nag them about the tablets they skip"),
        ("lost-code", "a sentence that occurs in no response"),
    ]
    return {
        "corpus": write_corpus_json(bodies, root / "corpus.json"),
        "tagged": write_tagged_csv(root / "pairs.csv", rows=rows),
        "first": holders[0],
        "second": holders[1],
    }


def write_rulings(path: Path, **payload: Any) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def organise(inputs: dict[str, Any], out: Path, *extra: str) -> int:
    return run_cli(
        "codebook",
        "organise",
        "--tagged",
        str(inputs["tagged"]),
        "--corpus",
        str(inputs["corpus"]),
        "--out",
        str(out),
        *extra,
    )


def test_organise_without_rulings_writes_no_rulings_file(
    inputs: dict[str, Any], tmp_path: Path
) -> None:
    out = tmp_path / "plain"
    assert organise(inputs, out) == EXIT_OK
    assert not (out / "rulings_applied.json").exists()
    assert "rulings" not in read_json(out / "organised.json")["meta"]
    placement = read_json(out / "placement.json")
    assert placement["ambiguous"] == 1 and "multi_placed" not in placement


def test_organise_with_rulings_applies_and_records_every_ruling(
    inputs: dict[str, Any], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rulings = write_rulings(
        tmp_path / "rulings.json",
        description="cli test",
        top_level=["efficiency"],
        label_merges=[{"from": "saftey-falls", "to": "safety-falls", "provisional": True}],
        label_merges_held=[{"labels": ["safety-falls", "efficiency"], "level": "label"}],
        multi_place_ambiguous=True,
        manual_placements_file=str(tmp_path / "absent.json"),
    )
    out = tmp_path / "ruled"
    assert organise(inputs, out, "--rulings", str(rulings)) == EXIT_OK
    shown = capsys.readouterr().out
    assert "label merges applied" in shown and "multi_placed" in shown
    assert "saftey-falls -> safety-falls" in shown and "provisional" in shown
    assert "not present, nothing applied" in shown

    placement = read_json(out / "placement.json")
    assert (placement["multi_placed"], placement["multi_placements"]) == (1, 2)
    assert placement["ambiguous"] == 0 and placement["multi_place_enabled"] is True

    golden = read_json(out / "golden.json")
    assert sum(1 for row in golden if row["code"] == "tie-code") == 2

    trail = read_json(out / "rulings_applied.json")
    assert trail == read_json(out / "organised.json")["meta"]["rulings"]
    assert trail["label_merges"][0]["applied"] is True
    assert trail["label_merges"][0]["provisional"] is True
    assert trail["top_level"][0]["present"] is True
    assert trail["placement"]["multi_place_ambiguous"] == {
        "enabled": True,
        "highlights": 1,
        "placements": 2,
    }
    assert trail["placement"]["manual_placements"]["file_found"] is False
    assert trail["placement"]["manual_placements"]["applied"] == 0
    assert trail["content_hash"] and trail["path"] == str(rulings)

    shareable = (out / "organised_shareable.md").read_text(encoding="utf-8")
    assert "**rulings applied**" in shareable
    assert "multi-placement of ambiguous highlights: on -- 1 highlight(s)" in shareable
    book = read_json(out / "codebook.json")
    flagged = [c["name"] for c in book["codes"] if c.get("meta", {}).get("ruled_top_level")]
    assert flagged == ["efficiency"]


def test_organise_reads_a_manual_placement_file_given_on_the_command_line(
    inputs: dict[str, Any], tmp_path: Path
) -> None:
    plain = tmp_path / "plain"
    assert organise(inputs, plain) == EXIT_OK
    lost = next(
        m["highlight_id"] for m in read_json(plain / "placement.json")["mappings"]
        if m["tag"] == "lost-code"
    )
    tie = next(
        m["highlight_id"] for m in read_json(plain / "placement.json")["mappings"]
        if m["tag"] == "tie-code"
    )
    manual = tmp_path / "manual.json"
    manual.write_text(
        json.dumps({lost: inputs["first"], tie: inputs["second"]}),
        encoding="utf-8",
    )
    out = tmp_path / "manual-out"
    assert organise(inputs, out, "--manual-placements", str(manual)) == EXIT_OK
    placement = read_json(out / "placement.json")
    assert (placement["manual"], placement["manual_requested"]) == (2, 2)
    assert placement["unlocated"] == 0 and placement["ambiguous"] == 0
    outcomes = {m["tag"]: m["outcome"] for m in placement["mappings"]}
    assert outcomes["lost-code"] == "manual" and outcomes["tie-code"] == "manual"
    assert not (out / "rulings_applied.json").exists(), "no rulings file, no rulings trail"


def test_a_placement_that_cannot_be_applied_is_printed_with_its_reason(
    inputs: dict[str, Any], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    manual = tmp_path / "manual.json"
    manual.write_text(json.dumps({"no-such-highlight": inputs["first"]}), encoding="utf-8")
    out = tmp_path / "unapplied"
    assert organise(inputs, out, "--manual-placements", str(manual)) == EXIT_OK
    shown = capsys.readouterr().out
    assert "manual placement not applied: highlight no-such-highlight" in shown
    assert "no highlight in the export has this id" in shown
    placement = read_json(out / "placement.json")
    assert placement["manual"] == 0 and placement["manual_requested"] == 1


def test_an_unusable_rulings_file_is_a_usage_error_not_a_traceback(
    inputs: dict[str, Any], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bad = write_rulings(tmp_path / "bad.json", surprise=True)
    assert organise(inputs, tmp_path / "x", "--rulings", str(bad)) == EXIT_INPUT
    assert "unknown key" in capsys.readouterr().err
    assert organise(inputs, tmp_path / "y", "--rulings", str(tmp_path / "gone.json")) == EXIT_INPUT


def test_a_manual_placement_file_that_is_malformed_stops_the_command(
    inputs: dict[str, Any], tmp_path: Path
) -> None:
    broken = tmp_path / "broken.json"
    broken.write_text("[1]", encoding="utf-8")
    assert organise(inputs, tmp_path / "z", "--manual-placements", str(broken)) == EXIT_INPUT


def test_define_re_applies_the_rulings_and_refuses_when_they_changed(
    inputs: dict[str, Any], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rulings = write_rulings(
        tmp_path / "rulings.json",
        label_merges=[{"from": "saftey-falls", "to": "safety-falls"}],
        multi_place_ambiguous=True,
    )
    out = tmp_path / "book"
    assert organise(inputs, out, "--rulings", str(rulings)) == EXIT_OK
    before = read_json(out / "placement.json")
    assert run_cli("codebook", "define", "--organised", str(out)) == EXIT_OK
    names = {c["name"] for c in read_json(out / "codebook.json")["codes"]}
    assert "safety-falls" in names and "saftey-falls" not in names
    after = read_json(out / "placement.json")
    assert after == before, "define must not alter the placement it re-reads"
    assert read_json(out / "rulings_applied.json")["label_merges"][0]["applied"] is True

    rulings.write_text('{"multi_place_ambiguous": false}', encoding="utf-8")
    assert run_cli("codebook", "define", "--organised", str(out)) == EXIT_INPUT
    assert "changed since" in capsys.readouterr().err
    rulings.unlink()
    assert run_cli("codebook", "define", "--organised", str(out)) == EXIT_INPUT
    assert "no longer there" in capsys.readouterr().err


def test_the_tracked_rulings_file_runs_through_organise_on_invented_data(
    inputs: dict[str, Any], tmp_path: Path
) -> None:
    out = tmp_path / "tracked"
    assert organise(inputs, out, "--rulings", str(REPO_ROOT / "rulings" / "india-process.json")) == (
        EXIT_OK
    )
    trail = read_json(out / "rulings_applied.json")
    assert trail["top_level"][0] == {
        "label": "efficiency",
        "present": True,
        "count": 1,
        "subcodes": 0,
    }
    assert trail["label_merges"][0]["applied"] is False, "the invented export has no such label"


def test_the_pairings_reader_is_unchanged_by_a_workbook_with_extra_columns(
    tmp_path: Path,
) -> None:
    """The canonical export grew count and model columns and fifteen empty-pair rows."""
    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.append(["tag", "content", "count", "Claude1", "Claude2"])
    sheet.append(["alpha-one", "first segment", None, None, None])
    sheet.append([None, None, 3, 1, 2])
    sheet.append(["alpha-two", "second segment", None, None, None])
    path = tmp_path / "export.xlsx"
    workbook.save(path)
    pairs = read_tagged_pairs(path)
    assert [(p.tag, p.row) for p in pairs] == [("alpha-one", 2), ("alpha-two", 4)]
