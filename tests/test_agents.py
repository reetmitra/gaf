"""Wave 2 gate for the three LLM roles (B1): Coder, Judge, Refactorer, and their prompts.

Six claims, each of which a later wave depends on:

1. **`JudgeAgent` satisfies the `Judge` protocol** that `gaf.checks.semantic` declares,
   so M1, M2 and M3 can take it by injection without knowing what it is.
2. **Mock-persona parity.** One template drives the offline and the live path: driven by
   `MockCoderClient`, the coder returns candidates that parse through
   `Candidate.from_json` and whose quotes are verbatim substrings of the *normalised*
   response text. That substring property is what S2 verifies and what every span in the
   store indexes into.
3. **The two coders receive identical context.** Their disagreement is the epistemic
   diversity mechanism and the router's escalation signal at once, so any asymmetry in
   the prompt would make cross-coder agreement a measurement of the wording. The two
   requests are asserted byte-identical.
4. **Prompts are built from `CodingRules`.** Changing the config changes the prompt.
5. **No template anywhere uses framing-analysis vocabulary** (ADR-0005). This study is
   inductive grounded theory, and that word must not reach a model or an output.
6. **Nothing raises.** A garbage reply becomes the non-destructive default -- keep the
   quote, keep both candidates, create rather than merge, propose nothing -- with
   `fail_safe` visible on the result.

No key, no network, no provider SDK, no real data: every client here is a deterministic
mock or a two-line stub.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

import gaf.agents
from gaf.agents.coder import CoderAgent, CoderContext, parse_candidates, subject_for
from gaf.agents.judge import JudgeAgent, JudgeRuling
from gaf.agents.prompts import coder_v1, judge_v1, refactorer_v1
from gaf.agents.prompts.loader import (
    LATEST,
    UnknownTemplateError,
    all_templates,
    coder_renderer,
    get_template,
    judge_renderers,
    refactorer_renderer,
    versions_for,
)
from gaf.agents.refactorer import (
    EditScript,
    RefactorContext,
    RefactorerAgent,
    codebook_digest,
    parse_operations,
    usage_from_codebook,
    usage_summary,
)
from gaf.checks.contracts import FIT_VERDICTS
from gaf.checks.semantic import Judge
from gaf.config import MOCK_REGISTRY, CodingRules, ModelSpec, RunConfig
from gaf.llm.base import (
    DISPUTE_VERDICTS,
    ROUTE_VERDICTS,
    CallLog,
    LLMRequest,
    LLMResult,
    TaskType,
    fail_safe_for,
)
from gaf.llm.mock import (
    MOCKDISPUTE_DROP,
    MOCKFIT_UNNECESSARY,
    MOCKROUTE_MERGE,
    MockCoderClient,
    MockJudgeClient,
    MockRefactorerClient,
    extract_code_ids,
    extract_response_id,
    extract_response_text,
)
from gaf.models import Assignment, Candidate, Operation, Response
from gaf.store.snapshot import freeze
from gaf.textnorm import normalise
from tests.fixtures.codebooks import toy_codebook
from tests.fixtures.corpus import SOURCE, synthetic_corpus

RULES = CodingRules()

#: A real seed-sample property: five of twenty responses are under the 100-word minimum
#: the survey asked for, the shortest is 28 words, and three contain no sentence
#: terminator at all (ADR-0015). A prompt that demands a minimum number of codes cannot
#: survive this input, so it is coded here rather than assumed away.
SHORT_UNPUNCTUATED = (
    "ai will be everywhere in daily life it will help doctors and teachers and it will "
    "take away some jobs from people who have no training and that worries me a lot"
)

#: One hand-coded example, phrased so that no word of it occurs in the fixture corpus:
#: the held-out assertion has to fail if the block is rendered, and pass otherwise.
HELD_OUT_CORRECTIONS = (
    Assignment(
        response_id=57,
        segment="the queue at the clinic will be shorter",
        code="positive_impacts-waiting_times",
    ),
)

#: The vocabulary ADR-0005 forbids anywhere in this project's prompts or output.
FORBIDDEN_VOCABULARY = ("frame", "framing", "frame element")


# --------------------------------------------------------------------------- #
# Stub clients
# --------------------------------------------------------------------------- #


class ScriptedClient:
    """Returns one fixed reply, whatever it is asked. The garbage-in half of fail-safe."""

    def __init__(self, data: dict[str, Any], spec: ModelSpec | None = None) -> None:
        self.spec = spec or MOCK_REGISTRY.judge
        self.data = data
        self.requests: list[LLMRequest] = []

    def complete_json(self, request: LLMRequest) -> LLMResult:
        self.requests.append(request)
        return LLMResult(
            data=dict(self.data),
            task=request.task,
            provider=self.spec.provider,
            model=self.spec.model,
            prompt_version=request.prompt_version,
        )


class FailSafeClient:
    """Behaves as a real client does on an unparseable reply: the task's safe default."""

    def __init__(self, spec: ModelSpec | None = None) -> None:
        self.spec = spec or MOCK_REGISTRY.judge

    def complete_json(self, request: LLMRequest) -> LLMResult:
        return LLMResult(
            data=fail_safe_for(request.task),
            task=request.task,
            provider=self.spec.provider,
            model=self.spec.model,
            prompt_version=request.prompt_version,
            fail_safe=True,
        )


class RecordingClient:
    """Wraps a mock and keeps every request, so the prompt version can be inspected."""

    def __init__(self, inner: Any) -> None:
        self.inner = inner
        self.spec = inner.spec
        self.requests: list[LLMRequest] = []

    def complete_json(self, request: LLMRequest) -> LLMResult:
        self.requests.append(request)
        return self.inner.complete_json(request)


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #


@pytest.fixture
def snapshot():
    return freeze(toy_codebook(), reason="seed")


@pytest.fixture
def corpus():
    return synthetic_corpus()


@pytest.fixture
def context(corpus, snapshot):
    return CoderContext.from_snapshot(
        corpus[0], snapshot, [code.id for code in snapshot.codes()[:4]]
    )


def coder(role: str = "coder_a", **kwargs: Any) -> CoderAgent:
    return CoderAgent(MockCoderClient(MOCK_REGISTRY.for_role(role)), **kwargs)


# --------------------------------------------------------------------------- #
# 1. The judge satisfies the protocol the semantic checks declare
# --------------------------------------------------------------------------- #


def test_judge_agent_satisfies_the_judge_protocol():
    """M1, M2 and M3 inject a `Judge`; this is the sole concrete one."""
    agent = JudgeAgent(MockJudgeClient())
    assert isinstance(agent, Judge)


def test_judge_agent_is_accepted_where_the_checks_expect_a_judge():
    """Not merely `isinstance`: the three methods answer with the declared shapes."""
    agent = JudgeAgent(MockJudgeClient())
    fit = agent.rule_on_fit(
        candidate_name="future-inevitability",
        candidate_description="AI's arrival is treated as unavoidable.",
        quote="Quality of life improves on average",
        response_text="Quality of life improves on average. It is the twenty years of transition",
    )
    assert set(fit) == {"verdict", "reasoning"}
    assert fit["verdict"] in FIT_VERDICTS

    dispute = agent.rule_on_dispute(
        candidate_a=Candidate(name="a-one", description="x").to_json(),
        candidate_b=Candidate(name="a-two", description="y").to_json(),
        response_text="some response",
    )
    assert set(dispute) == {"verdict", "reasoning"}
    assert dispute["verdict"] in DISPUTE_VERDICTS

    route = agent.rule_on_route(
        candidate_name="a-one",
        candidate_description="x",
        neighbour_name="a-two",
        neighbour_description="y",
        score=0.55,
    )
    assert set(route) == {"route", "reasoning"}
    assert route["route"] in ROUTE_VERDICTS


# --------------------------------------------------------------------------- #
# 2. Mock-persona parity: one template, two paths, verbatim quotes
# --------------------------------------------------------------------------- #


def test_coder_candidates_parse_and_quote_the_normalised_response(corpus, snapshot):
    """The property S2 depends on, asserted over the whole corpus and both personas."""
    seen = 0
    for response in corpus:
        ctx = CoderContext.from_snapshot(
            response, snapshot, [code.id for code in snapshot.codes()[:4]]
        )
        norm = normalise(response.content)
        for role in ("coder_a", "coder_b"):
            proposal = coder(role).code(ctx)
            assert proposal.candidates, f"no candidates for response {response.id} ({role})"
            for candidate in proposal.candidates:
                round_tripped = Candidate.from_json(candidate.to_json())
                assert round_tripped.name == candidate.name
                assert candidate.evidence, f"{candidate.name} cites no evidence"
                for item in candidate.evidence:
                    assert item.response_id == response.id
                    seen += 1
                    if item.quote != "" and item.quote in norm:
                        continue
                    # The one documented exception: persona B plants a fabricated quote
                    # on roughly one response in six, so that the S2 provenance-drop path
                    # is exercised on any corpus. It must come from persona B only.
                    assert role == "coder_b", (
                        f"coder_a quoted text absent from response {response.id}: "
                        f"{item.quote!r}"
                    )
    assert seen > 50


def test_coder_survives_a_short_unpunctuated_response(snapshot):
    """A 28-word answer with no full stop yields the codes it carries, and no quota."""
    response = Response(
        id=99, question="q", content=SHORT_UNPUNCTUATED, source=SOURCE, meta={}
    )
    ctx = CoderContext.from_snapshot(response, snapshot)
    proposal = coder().code(ctx)
    norm = normalise(response.content)
    assert proposal.candidates
    for candidate in proposal.candidates:
        for item in candidate.evidence:
            assert item.quote in norm
    # S5's "usually 2 to 12" is advisory, and the prompt has to say so: a hard minimum
    # would make a short response unencodable rather than under-coded.
    assert "advisory, not a quota" in proposal.request.user


def test_the_prompt_honours_the_mock_extraction_convention(corpus, snapshot):
    """One template drives both paths, so the offline reader must find what it expects.

    `MockCoderClient` takes the response text from between the `<response>` tags and the
    response id from the first integer in `LLMRequest.subject`. If the template stopped
    emitting either, the mock would silently code the whole prompt, and every quote it
    produced would still be a substring of *something* -- which is the failure mode this
    assertion exists to make loud.
    """
    for response in corpus:
        request = coder().build_request(CoderContext.from_snapshot(response, snapshot))
        assert extract_response_text(request.user).strip() == normalise(response.content)
        assert extract_response_id(request.subject) == response.id


def test_the_refactor_prompt_honours_the_mock_id_convention(snapshot):
    """The mock targets the code ids it can see, so the digest has to expose them."""
    request = RefactorerAgent(MockRefactorerClient()).build_request(
        RefactorContext.from_codebook(snapshot.codebook, snapshot.snapshot_id)
    )
    assert extract_code_ids(request.user) == [code.id for code in snapshot.codes()]


def test_coder_candidates_carry_the_role_that_produced_them(context):
    assert coder("coder_a").code(context).candidates[0].coder == "coder_a"
    assert coder("coder_b").code(context).candidates[0].coder == "coder_b"


# --------------------------------------------------------------------------- #
# 3. Identical context for the two coders
# --------------------------------------------------------------------------- #


def test_both_coders_receive_identical_context(context):
    """Any asymmetry here would make cross-coder disagreement measure the prompt."""
    request_a = coder("coder_a").build_request(context)
    request_b = coder("coder_b").build_request(context)
    assert request_a == request_b
    assert request_a.system == request_b.system
    assert request_a.user == request_b.user
    assert request_a.subject == request_b.subject == subject_for(context.response.id)
    # The only difference between the two coders is the model binding.
    assert MOCK_REGISTRY.coder_a.model != MOCK_REGISTRY.coder_b.model


def test_the_two_coders_still_disagree_about_meaning(corpus, snapshot):
    """Identical context must not mean identical output, or M1 has nothing to measure."""
    disagreements = 0
    for response in corpus:
        ctx = CoderContext.from_snapshot(response, snapshot)
        names_a = {c.name for c in coder("coder_a").code(ctx).candidates}
        names_b = {c.name for c in coder("coder_b").code(ctx).candidates}
        disagreements += names_a != names_b
    assert disagreements > 0


# --------------------------------------------------------------------------- #
# 4. The prompt carries the context, and is built from CodingRules
# --------------------------------------------------------------------------- #


def test_coder_prompt_carries_question_response_and_skeleton(context):
    prompt = coder().build_request(context).user
    assert normalise(context.response.question) in prompt
    assert f"<response>\n{normalise(context.response.content)}\n</response>" in prompt
    assert f"Response id: {context.response.id}" in prompt
    assert context.snapshot_id in prompt

    skeleton = context.skeleton
    assert skeleton, "the fixture codebook has families"
    for family, subs in skeleton.items():
        assert f"  {family}" in prompt
        for sub in subs:
            assert f"    - {sub}" in prompt
    for code in context.retrieved:
        assert f"  - {code.name}: {code.description}" in prompt


def test_changing_coding_rules_changes_the_rendered_prompt(context):
    """A threshold cannot drift away from the sentence that states it."""
    default = coder().build_request(context).user
    changed = coder(
        config=RunConfig(rules=CodingRules(max_codes_per_response=5))
    ).build_request(context).user
    assert default != changed
    assert "between 2 and 12 codes" in default
    assert "between 2 and 5 codes" in changed

    for field, needle in (
        ("max_codes_per_segment", "maximum of 3 codes"),
        ("max_quote_words", "at most 7 words"),
        ("min_codes_per_response", "between 4 and 12 codes"),
        ("hierarchy_depth", "The codebook has 9 levels"),
    ):
        value = {"max_codes_per_segment": 3, "max_quote_words": 7,
                 "min_codes_per_response": 4, "hierarchy_depth": 9}[field]
        rules = CodingRules(**{field: value})
        rendered = coder(config=RunConfig(rules=rules)).build_request(context).user
        assert needle in rendered, f"{field} does not reach the prompt"


def test_optional_rules_switch_sections_off(context):
    """`prefer_subcode_first` and `require_description` are booleans in the config."""
    on = coder().build_request(context).user
    assert "before you add a new top-level family" in on
    off = coder(
        config=RunConfig(rules=CodingRules(prefer_subcode_first=False))
    ).build_request(context).user
    assert "before you add a new top-level family" not in off


def test_empty_codebook_renders_a_first_pass_prompt(corpus):
    from gaf.models import Codebook

    empty = freeze(Codebook(), reason="seed")
    ctx = CoderContext.from_snapshot(corpus[0], empty)
    prompt = coder().build_request(ctx).user
    assert "The codebook is empty" in prompt


def test_context_from_snapshot_skips_ids_the_snapshot_does_not_hold(corpus, snapshot):
    ctx = CoderContext.from_snapshot(
        corpus[0], snapshot, ["c-does-not-exist", snapshot.codes()[0].id]
    )
    assert [code.id for code in ctx.retrieved] == [snapshot.codes()[0].id]


# --------------------------------------------------------------------------- #
# Human corrections: held out by default (brief 16.6)
# --------------------------------------------------------------------------- #


def test_human_corrections_are_held_out_by_default(context):
    """Recycling the golden set into the prompt is what stops it being independent."""
    agent = coder(corrections=HELD_OUT_CORRECTIONS)
    assert agent.corrections == ()
    prompt = agent.build_request(context).user
    assert HELD_OUT_CORRECTIONS[0].segment not in prompt
    assert HELD_OUT_CORRECTIONS[0].code not in prompt


def test_human_corrections_are_injected_when_the_run_asks_for_them(context):
    agent = coder(
        config=RunConfig(recycle_human_corrections=True), corrections=HELD_OUT_CORRECTIONS
    )
    prompt = agent.build_request(context).user
    assert HELD_OUT_CORRECTIONS[0].segment in prompt
    assert HELD_OUT_CORRECTIONS[0].code in prompt
    assert "response 57" in prompt


# --------------------------------------------------------------------------- #
# 5. Vocabulary (ADR-0005)
# --------------------------------------------------------------------------- #


def test_no_template_uses_framing_vocabulary():
    """This study is inductive grounded theory. The word must not reach a model."""
    for template in all_templates():
        haystack = template.all_text().casefold()
        for word in FORBIDDEN_VOCABULARY:
            assert word not in haystack, f"{template.version} uses {word!r}"


def test_no_agent_source_file_uses_framing_vocabulary():
    """Stronger than scanning the declared sections: nothing in the package says it."""
    package = Path(gaf.agents.__file__).parent
    sources = sorted(package.rglob("*.py"))
    assert len(sources) >= 7
    for path in sources:
        haystack = path.read_text(encoding="utf-8").casefold()
        for word in FORBIDDEN_VOCABULARY:
            assert word not in haystack, f"{path.name} uses {word!r}"


def test_prompts_speak_grounded_theory(context):
    coding_prompt = coder().build_request(context)
    assert "grounded-theory" in coding_prompt.system
    assert "constant comparison" in coding_prompt.system
    assert "initial coding" in coding_prompt.system


# --------------------------------------------------------------------------- #
# 6. The judge: sentinels, whitelists, and failing safe
# --------------------------------------------------------------------------- #


def test_judge_honours_the_mock_sentinels():
    agent = JudgeAgent(MockJudgeClient())
    unnecessary = agent.fit_ruling(
        candidate_name="a-b",
        candidate_description="d",
        quote=f"a quote carrying {MOCKFIT_UNNECESSARY} in it",
        response_text="the response",
    )
    assert unnecessary.value == "UNNECESSARY"

    dropped = agent.dispute_ruling(
        candidate_a={"name": "a-b", "description": MOCKDISPUTE_DROP},
        candidate_b={"name": "a-c", "description": "d"},
        response_text="the response",
    )
    assert dropped.value == "DROP"

    merged = agent.route_ruling(
        candidate_name="a-b",
        candidate_description=MOCKROUTE_MERGE,
        neighbour_name="a-c",
        neighbour_description="d",
        score=0.6,
    )
    assert merged.value == "MERGE"


def test_judge_returns_only_whitelisted_verdicts(corpus):
    """Every ruling over the corpus lands inside the whitelist that validates it."""
    agent = JudgeAgent(MockJudgeClient())
    for response in corpus:
        fit = agent.fit_ruling(
            candidate_name=f"family-code_{response.id}",
            candidate_description="a description",
            quote=response.content[:60],
            response_text=response.content,
            response_id=response.id,
        )
        assert fit.value in FIT_VERDICTS
        route = agent.route_ruling(
            candidate_name=f"family-code_{response.id}",
            candidate_description="a description",
            neighbour_name="family-other",
            neighbour_description="another description",
            score=0.5,
        )
        assert route.value in ROUTE_VERDICTS
        dispute = agent.dispute_ruling(
            candidate_a={"name": "family-a", "description": "d"},
            candidate_b={"name": "family-b", "description": "e"},
            response_text=response.content,
        )
        assert dispute.value in DISPUTE_VERDICTS


@pytest.mark.parametrize(
    "reply",
    [
        {},
        {"verdict": "MAYBE", "route": "MAYBE"},
        {"verdict": 17, "route": None, "reasoning": 5},
        {"verdict": ["APPLIES"], "route": ["MERGE"]},
        {"unrelated": "nonsense"},
    ],
)
def test_judge_fails_safe_to_the_non_destructive_default(reply):
    """Keep the quote, keep both candidates, create rather than merge. Never raise."""
    agent = JudgeAgent(ScriptedClient(reply))
    assert agent.rule_on_fit(
        candidate_name="a-b", candidate_description="d", quote="q", response_text="t"
    ) == {"verdict": "APPLIES", "reasoning": ""}
    assert agent.rule_on_dispute(
        candidate_a={"name": "a-b"}, candidate_b={"name": "a-c"}, response_text="t"
    ) == {"verdict": "KEEP", "reasoning": ""}
    assert agent.rule_on_route(
        candidate_name="a-b",
        candidate_description="d",
        neighbour_name="a-c",
        neighbour_description="e",
        score=0.5,
    ) == {"route": "CREATE", "reasoning": ""}


def test_judge_reports_a_client_side_fail_safe():
    """A client that already fell back is visible as such on the ruling."""
    ruling = JudgeAgent(FailSafeClient()).fit_ruling(
        candidate_name="a-b", candidate_description="d", quote="q", response_text="t"
    )
    assert ruling.fail_safe is True
    assert ruling.value == "APPLIES"


def test_judge_tolerates_lowercase_and_padded_verdicts():
    agent = JudgeAgent(ScriptedClient({"verdict": " imprecise ", "reasoning": "r"}))
    assert agent.rule_on_fit(
        candidate_name="a-b", candidate_description="d", quote="q", response_text="t"
    ) == {"verdict": "IMPRECISE", "reasoning": "r"}


def test_fit_prompt_does_not_invite_a_replacement_code():
    """On IMPRECISE or INCOMPLETE the verdict is the deliverable; refinement is human."""
    text = judge_v1.FIT_TEXT.casefold()
    assert "do not propose a different code" in text
    for invitation in (
        "what code would be better",
        "suggest a better",
        "propose a replacement",
        "a better name for",
        "rewrite the code",
        '"replacement"',
        '"suggested_code"',
        '"better_code"',
    ):
        assert invitation not in text, f"the fit prompt invites {invitation!r}"

    rendered = judge_v1.render_fit(
        candidate_name="a-b", candidate_description="d", quote="q", response_text="t"
    )
    assert set(json.loads('{"verdict": "", "reasoning": ""}')) == {"verdict", "reasoning"}
    assert "reasoning" in rendered.user
    assert "replacement" not in rendered.user.casefold()


def test_fit_prompt_offers_exactly_the_whitelisted_verdicts():
    """The menu is rendered from `FIT_VERDICTS`, so prompt and validation cannot drift."""
    rendered = judge_v1.render_fit(
        candidate_name="a-b", candidate_description="d", quote="q", response_text="t"
    )
    for verdict in FIT_VERDICTS:
        assert verdict in rendered.user
    assert set(judge_v1.FIT_VERDICT_GLOSS) == set(FIT_VERDICTS)
    assert set(judge_v1.DISPUTE_VERDICT_GLOSS) == set(DISPUTE_VERDICTS)
    assert set(judge_v1.ROUTE_VERDICT_GLOSS) == set(ROUTE_VERDICTS)


def test_route_prompt_states_the_band_from_the_config():
    rules = CodingRules(tau_low=0.30, tau_high=0.90)
    rendered = judge_v1.render_route(
        candidate_name="a-b",
        candidate_description="d",
        neighbour_name="a-c",
        neighbour_description="e",
        score=0.5,
        rules=rules,
    )
    assert "0.30" in rendered.user
    assert "0.90" in rendered.user
    assert "0.500" in rendered.user


def test_dispute_prompt_carries_both_candidates_and_the_response():
    candidate_a = Candidate(
        name="negative_impacts-job_loss",
        description="Work disappears.",
        evidence=[],
    ).to_json()
    candidate_b = Candidate(name="future-uncertainty", description="Unknowable.").to_json()
    rendered = judge_v1.render_dispute(
        candidate_a=candidate_a,
        candidate_b=candidate_b,
        response_text="Clerical posts in the district office vanish quietly.",
        rules=RULES,
    )
    assert "negative_impacts-job_loss" in rendered.user
    assert "future-uncertainty" in rendered.user
    assert "Clerical posts in the district office vanish quietly." in rendered.user
    assert f"maximum of {RULES.max_codes_per_segment} codes" in rendered.user


# --------------------------------------------------------------------------- #
# The refactorer
# --------------------------------------------------------------------------- #


def test_refactorer_edit_script_parses_and_can_split_and_reparent(snapshot):
    agent = RefactorerAgent(MockRefactorerClient())
    script = agent.propose(RefactorContext.from_codebook(snapshot.codebook, snapshot.snapshot_id))
    assert isinstance(script, EditScript)
    assert script.operations
    for operation in script.operations:
        assert isinstance(operation, Operation)
        assert Operation.from_json(operation.to_json()) == operation
        assert operation.rationale
    assert "split" in script.types()
    assert "reparent" in script.types()
    assert script.is_noop() is False
    assert script.subject == f"checkpoint:{snapshot.snapshot_id}"


def test_refactorer_prompt_invites_restructuring_and_names_the_codes(snapshot):
    agent = RefactorerAgent(MockRefactorerClient())
    context = RefactorContext.from_codebook(
        snapshot.codebook, snapshot.snapshot_id, health={"n_codes": len(snapshot)}
    )
    prompt = agent.build_request(context).user
    assert snapshot.snapshot_id in prompt
    for code in snapshot.codes():
        assert f'"id": "{code.id}"' in prompt
        assert code.name in prompt
    for operation_type in ("create", "merge", "split", "reparent", "rename", "noop"):
        assert operation_type in prompt
    assert "SPLIT an overloaded code" in prompt
    assert "REPARENT a misplaced code" in prompt
    assert "must name the evidence" in prompt
    assert '"n_codes"' in prompt


def test_refactorer_proposes_and_never_applies(snapshot):
    """There is no apply path on the proposer, and there must not be one (ADR-0004)."""
    agent = RefactorerAgent(MockRefactorerClient())
    before = snapshot.codebook.to_json_str()
    agent.propose(RefactorContext.from_codebook(snapshot.codebook, snapshot.snapshot_id))
    assert snapshot.codebook.to_json_str() == before
    assert not hasattr(agent, "apply")


def test_refactorer_edit_script_survives_one_bad_operation():
    """One hallucinated type must not discard the good operations beside it."""
    reply = {
        "operations": [
            {"type": "split", "targets": ["c-a"], "payload": {}, "rationale": "r"},
            {"type": "teleport", "targets": ["c-b"], "rationale": "r"},
            "not an object",
            {"type": "reparent", "targets": ["c-c"], "rationale": "r"},
        ],
        "reasoning": "partial",
    }
    assert [op.type for op in parse_operations(reply)] == ["split", "reparent"]


@pytest.mark.parametrize(
    "reply", [{}, {"operations": None}, {"operations": "nope"}, {"operations": 3}]
)
def test_refactorer_fails_safe_to_an_empty_script(reply, snapshot):
    agent = RefactorerAgent(ScriptedClient(reply, spec=MOCK_REGISTRY.refactorer))
    script = agent.propose(
        RefactorContext.from_codebook(snapshot.codebook, snapshot.snapshot_id)
    )
    assert script.operations == []
    assert len(script) == 0


def test_usage_statistics_are_derived_from_the_codebook(snapshot):
    usage = usage_from_codebook(snapshot.codebook)
    assert usage["c-positive_impacts-healthcare"] == 2
    assert usage["c-future"] == 0
    summary = usage_summary(snapshot.codebook, usage)
    assert "codes with no verified evidence" in summary
    assert "positive_impacts-healthcare: 2" in summary
    digest = codebook_digest(snapshot.codebook, usage)
    parsed = json.loads(digest)
    assert [row["id"] for row in parsed["codes"]] == [
        code.id for code in snapshot.codes()
    ]
    assert parsed["codes"][0]["responses"] >= 0


# --------------------------------------------------------------------------- #
# Coder parsing: never raise, never invent
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "reply",
    [
        {},
        {"candidates": None},
        {"candidates": "not a list"},
        {"candidates": [1, 2, 3]},
        {"candidates": [{"description": "no name at all"}]},
        {"candidates": [{"name": "   "}]},
        fail_safe_for(TaskType.CODE),
    ],
)
def test_coder_invents_nothing_from_an_unreadable_reply(reply, context):
    agent = CoderAgent(ScriptedClient(reply, spec=MOCK_REGISTRY.coder_a))
    proposal = agent.code(context)
    assert proposal.candidates == []


def test_coder_keeps_the_readable_candidates_and_drops_the_rest():
    reply = {
        "candidates": [
            {
                "name": "future-uncertainty",
                "description": "What AI does next is unknown.",
                "evidence": [
                    {"response_id": 212, "quote": "hard to guess"},
                    {"response_id": "212", "quote": "worries me"},
                    {"quote": "no response id at all"},
                    {"response_id": 212, "quote": "   "},
                    "not an object",
                ],
                "parent_hint": "future",
            },
            {"name": "", "description": "nameless"},
            {"name": "adoption-everyday_life", "evidence": "not a list"},
        ]
    }
    candidates = parse_candidates(reply, response_id=212, coder="coder_a")
    assert [c.name for c in candidates] == ["future-uncertainty", "adoption-everyday_life"]
    first = candidates[0]
    assert [e.quote for e in first.evidence] == [
        "hard to guess",
        "worries me",
        "no response id at all",
    ]
    # int, string-coerced, and the missing-id fallback all resolve to the coded response
    assert {e.response_id for e in first.evidence} == {212}
    assert first.parent_hint == "future"
    assert first.raw["name"] == "future-uncertainty"
    assert candidates[1].evidence == []


def test_coder_never_raises_on_a_client_side_fail_safe(context):
    proposal = CoderAgent(FailSafeClient(spec=MOCK_REGISTRY.coder_a)).code(context)
    assert proposal.candidates == []
    assert proposal.fail_safe is True


# --------------------------------------------------------------------------- #
# Prompt versions are recorded on every request
# --------------------------------------------------------------------------- #


def test_prompt_version_is_recorded_on_every_request(context, snapshot):
    coder_client = RecordingClient(MockCoderClient(MOCK_REGISTRY.coder_a))
    judge_client = RecordingClient(MockJudgeClient())
    refactor_client = RecordingClient(MockRefactorerClient())

    coding = CoderAgent(coder_client).code(context)
    judge = JudgeAgent(judge_client)
    judge.rule_on_fit(
        candidate_name="a-b", candidate_description="d", quote="q", response_text="t"
    )
    judge.rule_on_dispute(
        candidate_a={"name": "a-b"}, candidate_b={"name": "a-c"}, response_text="t"
    )
    judge.rule_on_route(
        candidate_name="a-b",
        candidate_description="d",
        neighbour_name="a-c",
        neighbour_description="e",
        score=0.5,
    )
    script = RefactorerAgent(refactor_client).propose(
        RefactorContext.from_codebook(snapshot.codebook, snapshot.snapshot_id)
    )

    assert [r.prompt_version for r in coder_client.requests] == [coder_v1.VERSION]
    assert [r.prompt_version for r in judge_client.requests] == [judge_v1.VERSION] * 3
    assert [r.prompt_version for r in refactor_client.requests] == [refactorer_v1.VERSION]
    assert coding.result.prompt_version == coder_v1.VERSION
    assert script.result.prompt_version == refactorer_v1.VERSION
    assert [r.task for r in judge_client.requests] == [
        TaskType.JUDGE_FIT,
        TaskType.JUDGE_DISPUTE,
        TaskType.JUDGE_ROUTE,
    ]
    assert all(r.subject for r in judge_client.requests)


def test_every_call_can_be_accounted_for(context, snapshot):
    """One `CallLog` across the three roles is what the run report and `llm_calls` read."""
    log = CallLog()
    CoderAgent(MockCoderClient(MOCK_REGISTRY.coder_a), call_log=log).code(context)
    JudgeAgent(MockJudgeClient(), call_log=log).fit_ruling(
        candidate_name="a-b", candidate_description="d", quote="q", response_text="t"
    )
    RefactorerAgent(MockRefactorerClient(), call_log=log).propose(
        RefactorContext.from_codebook(snapshot.codebook, snapshot.snapshot_id)
    )
    assert log.calls == 3
    assert log.by_task() == {"code": 1, "judge_fit": 1, "refactor": 1}
    assert log.fail_safes == 0


# --------------------------------------------------------------------------- #
# Determinism
# --------------------------------------------------------------------------- #


def test_the_same_inputs_render_the_same_prompt_twice(context, snapshot):
    assert coder().build_request(context) == coder().build_request(context)

    judge_prompts = [
        judge_v1.render_fit(
            candidate_name="a-b", candidate_description="d", quote="q", response_text="t"
        )
        for _ in range(2)
    ]
    assert judge_prompts[0] == judge_prompts[1]

    agent = RefactorerAgent(MockRefactorerClient())
    ctx = RefactorContext.from_codebook(snapshot.codebook, snapshot.snapshot_id)
    assert agent.build_request(ctx) == agent.build_request(ctx)


def test_the_same_inputs_produce_the_same_parsed_result_twice(context, snapshot):
    first = coder().code(context)
    second = coder().code(context)
    assert [c.to_json() for c in first.candidates] == [c.to_json() for c in second.candidates]

    judge = JudgeAgent(MockJudgeClient())
    rulings = [
        judge.fit_ruling(
            candidate_name="a-b", candidate_description="d", quote="q", response_text="t"
        ).to_reply()
        for _ in range(2)
    ]
    assert rulings[0] == rulings[1]

    agent = RefactorerAgent(MockRefactorerClient())
    ctx = RefactorContext.from_codebook(snapshot.codebook, snapshot.snapshot_id)
    assert agent.propose(ctx).to_json()["operations"] == agent.propose(ctx).to_json()["operations"]


# --------------------------------------------------------------------------- #
# The loader
# --------------------------------------------------------------------------- #


def test_loader_resolves_every_role_to_its_latest_version():
    """All four, including the Definer, which runs outside both loops (R1 N7a)."""
    from gaf.agents.prompts import definer_v1

    assert sorted(LATEST) == ["coder", "definer", "judge", "refactorer"]
    for role, version in LATEST.items():
        template = get_template(role)
        assert template.role == role
        assert template.version == version
        assert get_template(role, version) is template
        assert version in versions_for(role)
    assert [t.version for t in all_templates()] == [
        coder_v1.VERSION,
        definer_v1.VERSION,
        judge_v1.VERSION,
        refactorer_v1.VERSION,
    ]


def test_loader_refuses_an_unknown_role_or_version():
    """A run that names a version this build lacks must fail, not fall back silently."""
    with pytest.raises(UnknownTemplateError):
        get_template("summariser")
    with pytest.raises(UnknownTemplateError):
        get_template("coder", "coder-v99")
    with pytest.raises(UnknownTemplateError):
        coder_renderer("coder-v99")
    with pytest.raises(UnknownTemplateError):
        judge_renderers("judge-v99")
    with pytest.raises(UnknownTemplateError):
        refactorer_renderer("refactorer-v99")
    with pytest.raises(UnknownTemplateError):
        CoderAgent(MockCoderClient(), prompt_version="coder-v99")


def test_version_ids_name_their_role():
    for template in all_templates():
        assert template.version.startswith(template.role)
        assert template.texts, f"{template.version} declares no static text"


def test_a_ruling_serialises_for_the_audit_log():
    ruling = JudgeAgent(MockJudgeClient()).route_ruling(
        candidate_name="a-b",
        candidate_description="d",
        neighbour_name="a-c",
        neighbour_description="e",
        score=0.6,
    )
    assert isinstance(ruling, JudgeRuling)
    payload = ruling.to_json()
    assert payload["key"] == "route"
    assert payload["prompt_version"] == judge_v1.VERSION
    assert payload["subject"] == "route:a-b<->a-c"
    assert json.dumps(payload, sort_keys=True)
