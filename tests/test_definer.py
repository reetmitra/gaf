"""T5 gate for the Definer — the fourth LLM role, and the only one outside both loops.

Eleven claims, each of them something the researcher or a later reader depends on:

1. **The role can only write prose.** Renaming, merging, splitting, creating and
   choosing an example are absent from the output object, so the role cannot express
   them; a reply that tries is discarded unread.
2. **The prompt carries exactly what the brief specifies** — the code's name, its
   parent, its sibling names and *all* of its segments — and nothing else.
3. **A parent is described from its children**, their descriptions and their counts,
   never from raw segments.
4. **Every guard fires as a finding through `gaf.checks.contracts`**, and never repairs
   anything: an empty description, a fourth sentence, a verbatim copy of a segment and
   a run of eight or more shared words each produce a row.
5. **A refused description is not written anywhere**, including into its own finding:
   the guard that catches a quote must not become the thing that publishes it.
6. **The mock persona is extractive, deterministic and structurally safe** — the same
   context yields byte-identical output across processes, and the output cannot trip
   the shared-run guard by construction.
7. **Every artefact carrying a mock description says so** (`description_source`).
8. **The agent is built exactly like the other three**: a versioned template, a request
   that carries the version id, the disk-cache-compatible client protocol, the call log.
9. **The Definer's template is deliberately not in `all_templates()`**, because that set
   is the prompt surface of a *run* and the Definer never sees a response being coded.
10. **The sentence counter agrees with the structural layer's**, so "three sentences"
    means the same thing in both places.
11. **A malformed reply is a fail-safe**, leaving the code undescribed rather than
    inventing a definition.

Every segment, code name and description in this file is invented. No real survey
response, or any fragment of one, appears here or reaches any file these tests write.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import gaf.agents.definer as definer_module
from gaf.agents.definer import (
    DEFINER_CHECK_IDS,
    DEFINER_LATEST,
    MAX_SENTENCES,
    MAX_SHARED_WORD_RUN,
    ChildSummary,
    DefineContext,
    DefinerAgent,
    check_description,
    count_sentences,
    definer_renderer,
    definition_subject,
    get_definer_template,
    longest_shared_word_run,
    parse_description,
    word_tokens,
)
from gaf.agents.prompts.loader import UnknownTemplateError, all_templates
from gaf.checks.contracts import SCOPES, Severity
from gaf.config import MOCK_REGISTRY, RunConfig
from gaf.llm.base import CallLog, LLMRequest, LLMResult, TaskType
from gaf.llm.mock import MockDefinerClient

#: ADR-0005. This study is inductive grounded theory; the word must not reach a model.
FORBIDDEN_VOCABULARY = ("frame", "framing")

#: Invented segments. They are prose about an invented subject and share no run of
#: words with any real response.
LEAF_SEGMENTS: tuple[str, ...] = (
    "the ferry timetable is rebuilt every morning by a scheduler nobody meets",
    "a scheduler rearranges the ferry timetable before the harbour wakes up",
    "timetables at the harbour are now drawn by a scheduler rather than a clerk",
)

SIBLING_SEGMENTS: tuple[str, ...] = (
    "the lighthouse keeper files a report that nobody reads",
    "reports from the lighthouse pile up unread in a cabinet",
)


def leaf_context(
    name: str = "harbour-timetables",
    segments: tuple[str, ...] = LEAF_SEGMENTS,
    siblings: tuple[str, ...] = ("harbour-reports", "harbour-staffing"),
) -> DefineContext:
    return DefineContext(
        name=name,
        parent="harbour",
        siblings=siblings,
        segments=segments,
        count=len(segments),
    )


def parent_context() -> DefineContext:
    return DefineContext(
        name="harbour",
        parent="",
        siblings=("inland",),
        segments=LEAF_SEGMENTS + SIBLING_SEGMENTS,
        children=(
            ChildSummary("harbour-timetables", "Scheduling work moving off a clerk.", 3),
            ChildSummary("harbour-reports", "Written records that go unread.", 2),
        ),
        count=5,
    )


def agent(**kwargs: object) -> DefinerAgent:
    return DefinerAgent(MockDefinerClient(), **kwargs)  # type: ignore[arg-type]


# --------------------------------------------------------------------------- #
# 1. The role can only write prose
# --------------------------------------------------------------------------- #


def test_the_output_object_has_no_way_to_restructure_anything():
    """Not a policy: the schema the parser reads holds one key, so nothing else exists."""
    forbidden = {
        "name": "renamed",
        "operations": [{"type": "merge", "targets": ["a"]}],
        "into": ["a", "b"],
        "parent_id": "code-1",
        "examples": ["a quote the role must not choose"],
    }
    assert parse_description({**forbidden, "description": "A settled meaning."}) == (
        "A settled meaning."
    )
    assert parse_description(forbidden) == ""


def test_a_reply_that_only_tries_to_restructure_leaves_the_code_undescribed():
    class Restructurer:
        spec = MOCK_REGISTRY.refactorer

        def complete_json(self, request: LLMRequest) -> LLMResult:
            return LLMResult(
                data={"operations": [{"type": "split", "targets": ["x"]}]},
                task=request.task,
                provider="mock",
                model="mock",
                prompt_version=request.prompt_version,
            )

    definition = DefinerAgent(Restructurer()).define(leaf_context())  # type: ignore[arg-type]
    assert definition.description == ""
    assert not definition.accepted
    assert [f.check_id for f in definition.findings] == ["D1"]


# --------------------------------------------------------------------------- #
# 2. The prompt carries the four things, and every segment
# --------------------------------------------------------------------------- #


def test_the_prompt_carries_the_name_the_parent_the_siblings_and_every_segment():
    request = agent().build_request(leaf_context())
    assert request.task is TaskType.REFACTOR
    assert request.prompt_version == DEFINER_LATEST
    assert request.subject == definition_subject("harbour-timetables")
    user = request.user
    assert "harbour-timetables" in user
    assert "harbour-reports" in user and "harbour-staffing" in user
    for segment in LEAF_SEGMENTS:
        assert segment in user, "the role is shown every segment assigned to the code"


def test_a_leaf_with_no_siblings_says_so_rather_than_printing_an_empty_list():
    request = agent().build_request(leaf_context(siblings=()))
    assert "no siblings" in request.user


def test_the_request_is_a_pure_function_of_its_context():
    first = agent().build_request(leaf_context())
    second = agent().build_request(leaf_context())
    assert (first.system, first.user) == (second.system, second.user)


# --------------------------------------------------------------------------- #
# 3. A parent is described from its children
# --------------------------------------------------------------------------- #


def test_a_parent_prompt_carries_its_children_and_no_raw_segment():
    request = agent().build_request(parent_context())
    user = request.user
    assert "harbour-timetables" in user
    assert "Scheduling work moving off a clerk." in user
    assert "n=3" in user
    for segment in LEAF_SEGMENTS + SIBLING_SEGMENTS:
        assert segment not in user, "a parent is described from its children, not the text"


def test_a_parent_is_still_guarded_against_the_segments_beneath_it():
    """It never sees them, but a description that reproduces one is still a quote."""
    leaked = LEAF_SEGMENTS[0]
    report = check_description(leaked, parent_context().segments, code="harbour")
    assert "D4" in {finding.check_id for finding in report.findings}


# --------------------------------------------------------------------------- #
# 4. The guards — findings, never repairs
# --------------------------------------------------------------------------- #


def test_every_guard_id_is_declared_and_every_finding_uses_a_valid_scope():
    cases = [
        ("", LEAF_SEGMENTS),
        ("One. Two. Three. Four.", LEAF_SEGMENTS),
        (LEAF_SEGMENTS[0], LEAF_SEGMENTS),
    ]
    seen: set[str] = set()
    for description, segments in cases:
        for finding in check_description(description, segments, code="c-x").findings:
            assert finding.check_id in DEFINER_CHECK_IDS
            assert finding.scope in SCOPES
            assert finding.subject == "c-x"
            seen.add(finding.check_id)
    assert {"D1", "D2", "D3", "D4"} <= seen


def test_an_empty_description_is_an_error_and_nothing_else_fires():
    report = check_description("   ", LEAF_SEGMENTS, code="c-x")
    assert [(f.check_id, f.severity) for f in report.findings] == [("D1", Severity.ERROR)]


def test_three_sentences_pass_and_four_do_not():
    three = "One thing. Another thing. A third thing."
    four = "One thing. Another thing. A third thing. A fourth thing."
    assert count_sentences(three) == MAX_SENTENCES
    assert not check_description(three, LEAF_SEGMENTS, code="c-x").findings
    report = check_description(four, LEAF_SEGMENTS, code="c-x")
    assert [(f.check_id, f.severity) for f in report.findings] == [("D2", Severity.ERROR)]
    assert report.findings[0].data["sentences"] == 4
    assert report.findings[0].data["max_sentences"] == MAX_SENTENCES


def test_a_verbatim_copy_of_a_short_segment_is_refused():
    """R1 I3, ADR-0039: a whole segment reproduced is a quote, whatever its length."""
    short = "clerks vanish quietly"
    report = check_description(short, (short,), code="c-x")
    assert [(f.check_id, f.severity) for f in report.findings] == [("D3", Severity.ERROR)]
    assert not report.passed(), "a quote is not a description at any length"
    assert report.findings[0].data["words"] == 3


@pytest.mark.parametrize(
    "description",
    ["clerks vanish quietly.", "Clerks vanish quietly", "  CLERKS, vanish -- quietly!  "],
)
def test_punctuation_and_case_do_not_hide_a_verbatim_copy(description: str):
    """R1 I3. `normalise_for_match` folds case and whitespace and keeps punctuation.

    A seven-word copy with a full stop added therefore tripped neither D3, which
    compared the normalised strings, nor D4, which needs eight consecutive words.
    """
    segment = "clerks vanish quietly"
    report = check_description(description, (segment,), code="c-x")
    assert [(f.check_id, f.severity) for f in report.findings] == [("D3", Severity.ERROR)]


def test_a_description_that_merely_shares_words_with_a_segment_is_not_a_copy():
    report = check_description(
        "Posts disappearing from an office.", ("clerks vanish quietly",), code="c-x"
    )
    assert report.findings == []
    assert report.passed()


def test_a_verbatim_copy_of_a_long_segment_trips_both_rules():
    long_segment = LEAF_SEGMENTS[0]
    assert len(word_tokens(long_segment)) >= MAX_SHARED_WORD_RUN
    report = check_description(long_segment, (long_segment,), code="c-x")
    ids = {(f.check_id, f.severity) for f in report.findings}
    assert ("D3", Severity.ERROR) in ids
    assert ("D4", Severity.ERROR) in ids
    assert not report.passed()


def test_a_run_of_eight_shared_words_is_refused_and_seven_is_not():
    words = word_tokens(LEAF_SEGMENTS[0])
    eight = " ".join(words[:MAX_SHARED_WORD_RUN])
    seven = " ".join(words[: MAX_SHARED_WORD_RUN - 1])
    assert longest_shared_word_run(eight, LEAF_SEGMENTS) == MAX_SHARED_WORD_RUN
    assert longest_shared_word_run(seven, LEAF_SEGMENTS) == MAX_SHARED_WORD_RUN - 1
    assert check_description(eight, LEAF_SEGMENTS, code="c-x").errors()
    assert not check_description(seven, LEAF_SEGMENTS, code="c-x").errors()


def test_the_run_rule_ignores_punctuation_and_case():
    words = word_tokens(LEAF_SEGMENTS[0])
    dressed = ", ".join(w.upper() for w in words[:MAX_SHARED_WORD_RUN])
    assert longest_shared_word_run(dressed, LEAF_SEGMENTS) == MAX_SHARED_WORD_RUN


def test_a_code_with_no_segments_cannot_trip_the_two_leak_guards():
    report = check_description("A definition with nothing behind it.", (), code="c-x")
    assert not report.findings


def test_a_guard_never_rewrites_the_description():
    over_long = "One. Two. Three. Four."
    # `_definition_for` is the seam the guards sit on: the same call `define` makes
    # once a reply has been parsed, minus the client.
    definition = agent()._definition_for(leaf_context(), over_long)
    assert definition.description == over_long, "reported, never repaired"
    assert not definition.accepted


# --------------------------------------------------------------------------- #
# 5. A refused description is not published, not even by its own finding
# --------------------------------------------------------------------------- #


def test_no_finding_and_no_serialised_definition_carries_the_text():
    leaked = LEAF_SEGMENTS[0]
    definition = agent()._definition_for(leaf_context(), leaked)
    payload = json.dumps(definition.to_json(), ensure_ascii=False)
    assert leaked not in payload
    assert "description" not in definition.to_json()
    for finding in definition.findings:
        assert leaked not in json.dumps(finding.to_json(), ensure_ascii=False)


# --------------------------------------------------------------------------- #
# 6. The mock persona
# --------------------------------------------------------------------------- #


def test_the_mock_is_extractive_and_names_the_code():
    definition = agent().define(leaf_context())
    assert definition.accepted
    assert definition.source == "definer-mock"
    assert "harbour-timetables" in definition.description
    # Extractive: the most frequent content words of its own segments reach the text.
    assert "scheduler" in definition.description


def test_the_mock_is_byte_identical_across_calls_and_agents():
    first = agent().define(leaf_context())
    second = DefinerAgent(MockDefinerClient()).define(leaf_context())
    assert first.description == second.description
    assert first.result.raw_text == second.result.raw_text
    assert first.result.latency_ms == 0.0


def test_the_mock_cannot_trip_the_shared_run_guard_by_construction():
    """It lists at most seven content words, so the longest possible run is seven."""
    for context in (leaf_context(), parent_context()):
        definition = agent().define(context)
        assert definition.accepted, [f.message for f in definition.findings]
        assert longest_shared_word_run(definition.description, context.segments) < (
            MAX_SHARED_WORD_RUN
        )


def test_the_mock_writes_at_most_three_sentences_even_on_a_bare_code():
    empty = DefineContext(name="lonely", parent="", siblings=(), segments=(), count=0)
    definition = agent().define(empty)
    assert definition.description
    assert count_sentences(definition.description) <= MAX_SENTENCES
    assert definition.accepted


def test_the_mock_describes_a_parent_from_its_children():
    definition = agent().define(parent_context())
    assert definition.accepted
    assert "harbour" in definition.description
    assert "2" in definition.description, "the child count is part of what it reports"


def test_the_mock_refuses_a_task_it_does_not_answer():
    request = LLMRequest(
        task=TaskType.CODE, system="s", user="u", prompt_version="coder-v1", subject="9"
    )
    result = MockDefinerClient().complete_json(request)
    assert result.fail_safe
    assert "description" not in result.data


def test_the_mock_returns_a_fail_safe_for_a_prompt_that_is_not_a_definer_prompt():
    request = LLMRequest(
        task=TaskType.REFACTOR,
        system="s",
        user="an edit script request with no segments block",
        prompt_version="refactorer-v1",
        subject="checkpoint:snap-1",
    )
    result = MockDefinerClient().complete_json(request)
    assert result.fail_safe
    assert result.data.get("description", "") == ""


# --------------------------------------------------------------------------- #
# 7. Labelling
# --------------------------------------------------------------------------- #


def test_the_source_follows_the_client_and_is_recorded_on_the_definition():
    definition = agent().define(leaf_context())
    assert definition.to_json()["source"] == "definer-mock"
    assert definition.to_json()["code"] == "harbour-timetables"
    assert definition.to_json()["prompt_version"] == DEFINER_LATEST


# --------------------------------------------------------------------------- #
# 8. Built like the other three
# --------------------------------------------------------------------------- #


def test_the_agent_records_every_call_on_the_shared_log():
    log = CallLog()
    definer = DefinerAgent(MockDefinerClient(), config=RunConfig(), call_log=log)
    definer.define(leaf_context())
    definer.define(parent_context())
    assert log.calls == 2
    assert log.fail_safes == 0


def test_an_unknown_prompt_version_is_refused_rather_than_silently_downgraded():
    with pytest.raises(UnknownTemplateError):
        DefinerAgent(MockDefinerClient(), prompt_version="definer-v99")
    with pytest.raises(UnknownTemplateError):
        definer_renderer("definer-v99")
    with pytest.raises(UnknownTemplateError):
        get_definer_template("definer-v99")


def test_the_template_declares_its_static_text_and_names_its_role():
    template = get_definer_template()
    assert template.role == "definer"
    assert template.version == DEFINER_LATEST == "definer-v1"
    assert template.version.startswith(template.role)
    assert template.texts
    assert template.to_json()["sections"] == sorted(template.texts)


def test_the_template_uses_no_framing_vocabulary():
    haystack = get_definer_template().all_text().casefold()
    for word in FORBIDDEN_VOCABULARY:
        assert word not in haystack


# --------------------------------------------------------------------------- #
# 9. Outside the run's prompt surface, on purpose
# --------------------------------------------------------------------------- #


def test_the_definer_is_in_the_loader_but_not_in_a_runs_prompt_surface():
    """Registered with the other three (R1 N7a), and excluded from a run's manifest.

    The loader's own first claim is that it is the one place that knows which prompt
    versions exist, so leaving the Definer out of it was simply false. The claim the
    golden manifest makes is a different one — "this wording produced this coding" —
    and the Definer produced none of it, so `tests/test_golden.py` filters on
    `loader.LOOP_ROLES` rather than taking every template in the build (ADR-0034).
    """
    from gaf.agents.prompts.loader import LOOP_ROLES, get_template

    versions = [template.version for template in all_templates()]
    assert versions == ["coder-v1", "definer-v1", "judge-v1", "refactorer-v1"]
    assert DEFINER_LATEST in versions
    assert get_template("definer") is get_definer_template()

    assert "definer" not in LOOP_ROLES
    in_a_run = [t.version for t in all_templates() if t.role in LOOP_ROLES]
    assert in_a_run == ["coder-v1", "judge-v1", "refactorer-v1"]

    from tests.test_golden import _run_prompt_hashes

    assert sorted(_run_prompt_hashes()) == [
        "coder/coder-v1",
        "judge/judge-v1",
        "refactorer/refactorer-v1",
    ]


# --------------------------------------------------------------------------- #
# 10. One meaning of "three sentences"
# --------------------------------------------------------------------------- #


def test_the_sentence_counter_agrees_with_the_structural_layer():
    from gaf.checks.structural import _sentence_count

    for text in (
        "One.",
        "One. Two.",
        "One! Two? Three.",
        "no terminator at all",
        "Ellipsis... counts as one run.",
        "  spaced out .  ",
    ):
        assert count_sentences(text) == _sentence_count(text), text


# --------------------------------------------------------------------------- #
# 11. Fail-safe
# --------------------------------------------------------------------------- #


def test_a_malformed_reply_leaves_the_code_undescribed_rather_than_inventing_one():
    class Malformed:
        spec = MOCK_REGISTRY.refactorer

        def complete_json(self, request: LLMRequest) -> LLMResult:
            return LLMResult(
                data={"description": 17},
                task=request.task,
                provider="mock",
                model="mock",
                prompt_version=request.prompt_version,
                fail_safe=True,
            )

    definition = DefinerAgent(Malformed()).define(leaf_context())  # type: ignore[arg-type]
    assert definition.description == ""
    assert definition.fail_safe
    assert not definition.accepted


# --------------------------------------------------------------------------- #
# Housekeeping
# --------------------------------------------------------------------------- #


def test_the_module_source_uses_no_framing_vocabulary():
    for module in (definer_module, __import__("gaf.agents.prompts.definer_v1", fromlist=["x"])):
        source = Path(module.__file__).read_text(encoding="utf-8").casefold()  # type: ignore[arg-type]
        for word in FORBIDDEN_VOCABULARY:
            assert word not in source, f"{module.__name__} uses {word!r}"


# --------------------------------------------------------------------------- #
# Branches the paths above do not reach
# --------------------------------------------------------------------------- #


def test_the_run_guard_answers_zero_when_there_is_nothing_to_compare():
    assert longest_shared_word_run("", LEAF_SEGMENTS) == 0
    assert longest_shared_word_run("   ", LEAF_SEGMENTS) == 0
    assert longest_shared_word_run("a definition", ("", "   ")) == 0


def test_a_context_serialises_as_names_and_counts_and_never_as_text():
    payload = parent_context().to_json()
    assert payload["is_parent"] is True
    assert payload["segment_count"] == 5
    assert payload["children"] == ["harbour-timetables", "harbour-reports"]
    assert leaf_context().to_json()["is_parent"] is False
    blob = json.dumps(payload, ensure_ascii=False)
    for segment in LEAF_SEGMENTS + SIBLING_SEGMENTS:
        assert segment not in blob


def test_a_child_summary_serialises():
    child = ChildSummary("harbour-reports", "Written records that go unread.", 2)
    assert child.to_json() == {
        "name": "harbour-reports",
        "description": "Written records that go unread.",
        "count": 2,
    }
    assert child.as_line() == ("harbour-reports", "Written records that go unread.", 2)


def test_a_moved_sentence_bound_is_rendered_into_the_prompt_the_guard_enforces():
    """The wording and the guard must not be able to say different numbers."""
    relaxed = DefinerAgent(MockDefinerClient(), max_sentences=5)
    assert "one to five sentences" in relaxed.build_request(leaf_context()).user
    odd = DefinerAgent(MockDefinerClient(), max_sentences=7)
    assert "one to 7 sentences" in odd.build_request(leaf_context()).user
    four = "One. Two. Three. Four."
    assert not relaxed._definition_for(leaf_context(), four).findings


def test_the_templates_self_check_refuses_a_second_output_key(monkeypatch: pytest.MonkeyPatch):
    from gaf.agents.prompts import definer_v1

    monkeypatch.setattr(
        definer_v1, "OUTPUT", '{"description": "...", "name": "renamed"}', raising=True
    )
    with pytest.raises(RuntimeError, match="exactly one output key"):
        definer_v1._self_check()


def test_the_templates_self_check_refuses_an_unpaired_block(monkeypatch: pytest.MonkeyPatch):
    from gaf.agents.prompts import definer_v1

    monkeypatch.setattr(definer_v1, "CHILDREN_CLOSE", "</kids>", raising=True)
    with pytest.raises(RuntimeError, match="not a pair"):
        definer_v1._self_check()
