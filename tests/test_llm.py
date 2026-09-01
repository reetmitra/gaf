"""Wave 1 gate for the model clients (A2): the mocks, the cache, the live seam.

The offline path is the default path, so the mocks carry the weight here. Four claims:

1. every mock is a **pure function of its request** — the same request twice, and two
   fresh instances, give identical results, because a run that is not reproducible is
   not evidence;
2. `MockCoderClient` works on **arbitrary text**, not only on the fixture corpus: over
   the whole synthetic corpus its quotes are verbatim substrings of the normalised
   response (the property S2 depends on), its counts sit inside the PI's 2..12, and no
   quote exceeds `CodingRules.max_quote_words`;
3. the two personas **agree on most codes and differ on some** — agreement with no
   divergence would leave the disagreement router and M1 untestable;
4. nothing, however malformed, raises: a bad reply becomes the non-destructive
   fail-safe default with `fail_safe=True`.

No key, no network, no provider SDK: the live clients are exercised only through their
injected transport seam, and their construction path is asserted to fail loudly.
"""

from __future__ import annotations

import importlib.util
import json

import pytest

from gaf.checks.contracts import FIT_VERDICTS
from gaf.config import MOCK_REGISTRY, CodingRules, ModelSpec
from gaf.llm.anthropic_client import AnthropicClient
from gaf.llm.anthropic_client import MissingProviderSDKError as AnthropicSDKError
from gaf.llm.base import LLMError, LLMRequest, TaskType, fail_safe_for
from gaf.llm.cache import CachingLLMClient, cache_key
from gaf.llm.gemini_client import GeminiClient
from gaf.llm.gemini_client import MissingProviderSDKError as GeminiSDKError
from gaf.llm.mock import (
    DISPUTE_VERDICTS,
    FABRICATED_QUOTE,
    MOCKDISPUTE_DROP,
    MOCKFIT_UNNECESSARY,
    MOCKROUTE_MERGE,
    ROUTE_VERDICTS,
    MockCoderClient,
    MockJudgeClient,
    MockRefactorerClient,
    extract_code_ids,
    extract_response_id,
    extract_response_text,
    mock_candidates_for,
    split_segments,
)
from gaf.llm.openai_client import MissingProviderSDKError as OpenAISDKError
from gaf.llm.openai_client import OpenAIClient
from gaf.models import Candidate, Operation
from gaf.textnorm import normalise
from tests.fixtures.codebooks import toy_codebook
from tests.fixtures.corpus import synthetic_corpus

RULES = CodingRules()

#: A response with no sentence terminator at all — three of the twenty real seed
#: responses look like this (ADR-0015), and a sentence-only splitter would quote it
#: whole, tripping S2b, starving S5 and risking a spurious S4 error.
UNPUNCTUATED = (
    "By 2050 these systems will sit in every office in my district and they will help "
    "doctors and farmers and teachers but many people will lose their jobs because "
    "machines can do repetitive work faster so the government must plan for this while "
    "the technology keeps improving every year which nobody can stop"
)

#: Twenty-eight words, under the survey's stated minimum. Five of the twenty real
#: responses are short like this.
VERY_SHORT = (
    "AI will help in healthcare and education but I am worried about jobs, that is my "
    "main fear for the coming years in my own country and city"
)


def coding_request(text: str, response_id: int) -> LLMRequest:
    return LLMRequest(
        task=TaskType.CODE,
        system="You are an initial coder.",
        user=f"<response>{text}</response>",
        prompt_version="coder-v0",
        subject=str(response_id),
    )


# --------------------------------------------------------------------------- #
# Determinism
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("client_factory", "request_factory"),
    [
        (
            lambda: MockCoderClient(MOCK_REGISTRY.coder_a),
            lambda: coding_request(synthetic_corpus()[0].content, 3),
        ),
        (
            lambda: MockCoderClient(MOCK_REGISTRY.coder_b),
            lambda: coding_request(synthetic_corpus()[4].content, 21),
        ),
        (
            MockJudgeClient,
            lambda: LLMRequest(
                task=TaskType.JUDGE_FIT,
                system="judge",
                user="does this code fit this quote",
                prompt_version="judge-v0",
                subject="c-1",
            ),
        ),
        (
            MockJudgeClient,
            lambda: LLMRequest(
                task=TaskType.JUDGE_DISPUTE,
                system="judge",
                user="coder A says keep, coder B says drop",
                prompt_version="judge-v0",
                subject="39",
            ),
        ),
        (
            MockRefactorerClient,
            lambda: LLMRequest(
                task=TaskType.REFACTOR,
                system="refactorer",
                user=toy_codebook().to_json_str(),
                prompt_version="refactor-v0",
                subject="snap-seed",
            ),
        ),
    ],
)
def test_every_mock_is_a_pure_function_of_its_request(client_factory, request_factory) -> None:  # type: ignore[no-untyped-def]
    request = request_factory()
    first = client_factory().complete_json(request)
    again = client_factory().complete_json(request)
    same_instance = client_factory()
    assert first == again, "two fresh instances must agree"
    assert same_instance.complete_json(request) == same_instance.complete_json(request)
    # No wall clock leaks into an offline result, or `make demo` could not be byte-identical.
    assert first.latency_ms == 0.0
    assert first.attempts == 1
    assert first.cache_hit is False


def test_a_mock_result_is_fully_populated() -> None:
    client = MockCoderClient(MOCK_REGISTRY.coder_a)
    result = client.complete_json(coding_request(synthetic_corpus()[0].content, 3))
    assert result.provider == "mock"
    assert result.model == "mock-coder-a"
    assert result.prompt_version == "coder-v0"
    assert result.input_tokens > 0 and result.output_tokens > 0
    assert result.cost_usd == 0.0  # the mock spec carries no prices
    assert json.loads(result.raw_text) == result.data


# --------------------------------------------------------------------------- #
# The coder works on arbitrary text
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("persona", ["A", "B"])
def test_every_quote_is_a_verbatim_substring_of_the_normalised_response(persona: str) -> None:
    """The property S2 provenance depends on, asserted over the whole corpus."""
    for response in synthetic_corpus():
        norm = normalise(response.content)
        for candidate in mock_candidates_for(response.content, response.id, persona):
            for evidence in candidate["evidence"]:
                quote = evidence["quote"]
                if quote == FABRICATED_QUOTE:
                    continue  # planted on purpose; see the S2 drop test below
                assert quote in norm, f"response {response.id}: {quote!r} not in the source"
                assert evidence["response_id"] == response.id


@pytest.mark.parametrize("persona", ["A", "B"])
def test_candidate_counts_sit_inside_the_pis_range(persona: str) -> None:
    for response in synthetic_corpus():
        count = len(mock_candidates_for(response.content, response.id, persona))
        assert RULES.min_codes_per_response <= count <= RULES.max_codes_per_response, (
            f"response {response.id} produced {count} candidates"
        )
        assert count <= 6, "a typical response should stay well inside the range"


@pytest.mark.parametrize("persona", ["A", "B"])
def test_no_quote_exceeds_the_word_bound(persona: str) -> None:
    """ADR-0015: S2b also bounds a quote by word count, and the coder must respect it."""
    for response in synthetic_corpus():
        for candidate in mock_candidates_for(response.content, response.id, persona):
            for evidence in candidate["evidence"]:
                words = len(evidence["quote"].split())
                assert words <= RULES.max_quote_words, f"{words}-word quote on {response.id}"


def test_candidates_parse_through_the_frozen_model() -> None:
    for response in synthetic_corpus():
        for raw in mock_candidates_for(response.content, response.id, "A"):
            candidate = Candidate.from_json(raw)
            assert candidate.name and candidate.description
            assert candidate.evidence
            assert candidate.family == raw["parent_hint"]
            # S1: a description that copies its own quote explains nothing.
            assert all(candidate.description != e.quote for e in candidate.evidence)


def test_descriptions_are_stable_per_code_name() -> None:
    """Two coders proposing the same name must propose the same description.

    Otherwise cross-coder matching would measure phrasing rather than agreement.
    """
    seen: dict[str, str] = {}
    for response in synthetic_corpus():
        for persona in ("A", "B"):
            for raw in mock_candidates_for(response.content, response.id, persona):
                assert seen.setdefault(raw["name"], raw["description"]) == raw["description"]


# --------------------------------------------------------------------------- #
# Segmentation on text the real corpus actually contains
# --------------------------------------------------------------------------- #


def test_an_unpunctuated_response_is_split_at_clause_boundaries() -> None:
    """Three of the twenty real responses contain no '.', '?' or '!' at all."""
    assert not any(mark in UNPUNCTUATED for mark in ".?!")
    segments = split_segments(UNPUNCTUATED)
    assert len(segments) >= 3, "a terminator-only split would return the whole response"
    norm = normalise(UNPUNCTUATED)
    for segment in segments:
        assert segment in norm
        assert len(segment.split()) <= RULES.max_quote_words


def test_an_unpunctuated_response_still_yields_several_distinct_codes() -> None:
    candidates = mock_candidates_for(UNPUNCTUATED, 18, "A")
    assert 2 <= len(candidates) <= RULES.max_codes_per_response
    quotes = [e["quote"] for c in candidates for e in c["evidence"]]
    assert len(set(quotes)) == len(quotes), "distinct codes must not share one huge span"


def test_a_very_short_response_degrades_gracefully() -> None:
    candidates = mock_candidates_for(VERY_SHORT, 9, "A")
    assert len(candidates) >= 1
    norm = normalise(VERY_SHORT)
    assert all(e["quote"] in norm for c in candidates for e in c["evidence"])


def test_a_single_phrase_is_not_padded_out_to_a_quota() -> None:
    """One phrase supports one code. Manufacturing a second would invent evidence."""
    candidates = mock_candidates_for("AI will change everything", 1, "A")
    assert len(candidates) == 1


def test_segments_carry_at_most_one_sentence() -> None:
    for response in synthetic_corpus():
        for segment in split_segments(response.content):
            assert sum(segment.count(mark) for mark in ".?!") <= RULES.max_quote_sentences


def test_empty_text_yields_nothing_rather_than_raising() -> None:
    assert split_segments("   ") == []
    assert mock_candidates_for("", 1, "A") == []


def test_an_unknown_persona_is_refused() -> None:
    with pytest.raises(ValueError, match="persona"):
        mock_candidates_for("AI will change everything", 1, "C")


# --------------------------------------------------------------------------- #
# Personas: mostly agreeing, partly diverging
# --------------------------------------------------------------------------- #


def test_the_personas_agree_on_most_codes() -> None:
    shared = union = 0
    for response in synthetic_corpus():
        names_a = {c["name"] for c in mock_candidates_for(response.content, response.id, "A")}
        names_b = {c["name"] for c in mock_candidates_for(response.content, response.id, "B")}
        shared += len(names_a & names_b)
        union += len(names_a | names_b)
    agreement = shared / union
    assert agreement >= 0.6, f"the personas agree on only {agreement:.0%} of codes"


def test_the_personas_diverge_somewhere() -> None:
    """Agreement with no divergence would make M1 and the router untestable."""
    diverging = [
        response.id
        for response in synthetic_corpus()
        if {c["name"] for c in mock_candidates_for(response.content, response.id, "A")}
        != {c["name"] for c in mock_candidates_for(response.content, response.id, "B")}
    ]
    assert diverging, "the two personas never disagree, so the router has nothing to route"
    assert len(diverging) < len(synthetic_corpus()), "and they must not disagree everywhere"


def test_persona_b_plants_a_fabricated_quote_so_the_s2_drop_path_is_exercised() -> None:
    fabricated = [
        response.id
        for response in synthetic_corpus()
        for candidate in mock_candidates_for(response.content, response.id, "B")
        for evidence in candidate["evidence"]
        if evidence["quote"] == FABRICATED_QUOTE
    ]
    assert fabricated, "persona B never cites an invented quote"
    assert len(fabricated) <= len(synthetic_corpus()) // 3, "it must stay rare"
    # It really is unlocatable — that is what makes it a provenance failure.
    for response in synthetic_corpus():
        assert FABRICATED_QUOTE not in normalise(response.content)


def test_persona_a_never_fabricates() -> None:
    assert not [
        1
        for response in synthetic_corpus()
        for candidate in mock_candidates_for(response.content, response.id, "A")
        for evidence in candidate["evidence"]
        if evidence["quote"] == FABRICATED_QUOTE
    ]


def test_the_persona_follows_the_role_when_not_given_explicitly() -> None:
    assert MockCoderClient(MOCK_REGISTRY.coder_a).persona == "A"
    assert MockCoderClient(MOCK_REGISTRY.coder_b).persona == "B"
    assert MockCoderClient(MOCK_REGISTRY.coder_a, persona="B").persona == "B"
    with pytest.raises(ValueError, match="persona"):
        MockCoderClient(MOCK_REGISTRY.coder_a, persona="Z")


# --------------------------------------------------------------------------- #
# Prompt-shape helpers
# --------------------------------------------------------------------------- #


def test_the_response_block_is_used_when_present_and_the_whole_prompt_otherwise() -> None:
    assert extract_response_text("noise <response>the body</response> more") == "the body"
    assert extract_response_text("just the body") == "just the body"


def test_the_response_id_is_recovered_from_the_subject() -> None:
    assert extract_response_id("39") == 39
    assert extract_response_id("response:39") == 39
    assert extract_response_id("no digits here") == 0


def test_code_ids_are_recovered_from_a_codebook_prompt() -> None:
    ids = extract_code_ids(toy_codebook().to_json_str())
    assert "c-negative_impacts-job_destruction" in ids
    assert len(ids) == len(toy_codebook())
    assert len(set(ids)) == len(ids)
    # A response_id field must not be mistaken for a code id.
    assert not any(identifier.isdigit() for identifier in ids)
    assert extract_code_ids("consider merging c-future into c-future-inevitability") == [
        "c-future",
        "c-future-inevitability",
    ]


# --------------------------------------------------------------------------- #
# The judge
# --------------------------------------------------------------------------- #


def fit_request(quote: str) -> LLMRequest:
    return LLMRequest(
        task=TaskType.JUDGE_FIT,
        system="judge",
        user=f"code: positive_impacts-healthcare\nquote: {quote}",
        prompt_version="judge-v0",
        subject="c-1",
    )


def test_the_judge_honours_the_unnecessary_sentinel() -> None:
    judge = MockJudgeClient()
    flagged = judge.complete_json(fit_request(f"prefix {MOCKFIT_UNNECESSARY} suffix"))
    ordinary = judge.complete_json(fit_request("It will remind them to take medicine"))
    assert flagged.data["verdict"] == "UNNECESSARY"
    assert ordinary.data["verdict"] == "APPLIES"
    assert flagged.fail_safe is False


def test_every_fit_verdict_is_whitelisted() -> None:
    judge = MockJudgeClient()
    for response in synthetic_corpus():
        for segment in split_segments(response.content):
            verdict = judge.complete_json(fit_request(segment)).data["verdict"]
            assert verdict in FIT_VERDICTS


def test_the_dispute_judge_is_biased_to_keep() -> None:
    judge = MockJudgeClient()
    verdicts = [
        judge.complete_json(
            LLMRequest(
                task=TaskType.JUDGE_DISPUTE,
                system="judge",
                user=f"coder A proposed {response.id}, coder B did not",
                prompt_version="judge-v0",
                subject=str(response.id),
            )
        ).data["verdict"]
        for response in synthetic_corpus()
    ]
    assert set(verdicts) <= set(DISPUTE_VERDICTS)
    assert verdicts.count("KEEP") > verdicts.count("DROP")


def test_the_dispute_sentinel_forces_a_drop() -> None:
    result = MockJudgeClient().complete_json(
        LLMRequest(
            task=TaskType.JUDGE_DISPUTE,
            system="judge",
            user=f"the disputed candidate is {MOCKDISPUTE_DROP}",
            prompt_version="judge-v0",
            subject="7",
        )
    )
    assert result.data["verdict"] == "DROP"
    assert result.data["reasoning"]


def test_routing_verdicts_are_whitelisted_and_the_sentinel_forces_a_merge() -> None:
    judge = MockJudgeClient()
    routes = {
        judge.complete_json(
            LLMRequest(
                task=TaskType.JUDGE_ROUTE,
                system="judge",
                user=f"candidate {n} against the codebook",
                prompt_version="judge-v0",
                subject=str(n),
            )
        ).data["route"]
        for n in range(30)
    }
    assert routes <= set(ROUTE_VERDICTS)
    assert routes == set(ROUTE_VERDICTS), "both routes must be reachable"
    forced = judge.complete_json(
        LLMRequest(
            task=TaskType.JUDGE_ROUTE,
            system="judge",
            user=f"candidate {MOCKROUTE_MERGE}",
            prompt_version="judge-v0",
            subject="x",
        )
    )
    assert forced.data["route"] == "MERGE"


def test_a_role_asked_the_wrong_task_fails_safe_rather_than_raising() -> None:
    request = LLMRequest(
        task=TaskType.REFACTOR,
        system="judge",
        user="restructure the codebook",
        prompt_version="judge-v0",
        subject="snap",
    )
    result = MockJudgeClient().complete_json(request)
    assert result.fail_safe is True
    assert result.data == fail_safe_for(TaskType.REFACTOR)
    assert MockCoderClient().complete_json(request).fail_safe is True


# --------------------------------------------------------------------------- #
# The refactorer
# --------------------------------------------------------------------------- #


def refactor_request(user: str) -> LLMRequest:
    return LLMRequest(
        task=TaskType.REFACTOR,
        system="refactorer",
        user=user,
        prompt_version="refactor-v0",
        subject="snap-seed",
    )


def test_the_edit_script_parses_and_carries_a_split_and_a_reparent() -> None:
    result = MockRefactorerClient().complete_json(refactor_request(toy_codebook().to_json_str()))
    operations = [Operation.from_json(o) for o in result.data["operations"]]
    types = {o.type for o in operations}
    assert "split" in types, "split exists because the predecessor could not restructure"
    assert "reparent" in types
    assert all(o.rationale for o in operations), "the human gate reads the rationale"


def test_every_operation_targets_a_code_that_is_actually_in_the_codebook() -> None:
    codebook = toy_codebook()
    result = MockRefactorerClient().complete_json(refactor_request(codebook.to_json_str()))
    for raw in result.data["operations"]:
        operation = Operation.from_json(raw)
        assert all(target in codebook for target in operation.targets)
        if operation.type == "reparent":
            parent = operation.payload["new_parent_id"]
            assert parent is None or parent in codebook
            assert parent not in operation.targets
        if operation.type == "split":
            assert len(operation.payload["into"]) >= 2
            assert all(part["name"] and part["description"] for part in operation.payload["into"])


def test_a_request_naming_no_codes_yields_a_valid_no_op_script() -> None:
    """Inventing a target would produce an edit script the slow loop must reject."""
    result = MockRefactorerClient().complete_json(refactor_request("there is no codebook here"))
    operations = [Operation.from_json(o) for o in result.data["operations"]]
    assert [o.type for o in operations] == ["noop"]
    assert operations[0].targets == []


# --------------------------------------------------------------------------- #
# The cache
# --------------------------------------------------------------------------- #


def test_miss_then_hit(tmp_path) -> None:  # type: ignore[no-untyped-def]
    inner = MockCoderClient(MOCK_REGISTRY.coder_a)
    client = CachingLLMClient(inner, tmp_path / "cache")
    request = coding_request(synthetic_corpus()[0].content, 3)

    first = client.complete_json(request)
    assert first.cache_hit is False
    assert (client.hits, client.misses) == (0, 1)

    second = client.complete_json(request)
    assert second.cache_hit is True
    assert second.cost_usd == 0.0
    assert second.data == first.data
    assert second.task is first.task
    assert second.provider == first.provider
    assert (client.hits, client.misses) == (1, 1)
    assert client.stats()["hits"] == 1


def test_a_second_client_reads_the_first_ones_entries(tmp_path) -> None:  # type: ignore[no-untyped-def]
    request = coding_request(synthetic_corpus()[1].content, 7)
    CachingLLMClient(MockCoderClient(MOCK_REGISTRY.coder_a), tmp_path).complete_json(request)
    fresh = CachingLLMClient(MockCoderClient(MOCK_REGISTRY.coder_a), tmp_path)
    assert fresh.complete_json(request).cache_hit is True


def test_the_key_binds_the_provider_so_two_coders_never_share_an_answer() -> None:
    """Coder A and coder B are given the same context on purpose. That is the mechanism."""
    request = coding_request(synthetic_corpus()[0].content, 3)
    key_a = cache_key(request, MOCK_REGISTRY.coder_a)
    key_b = cache_key(request, MOCK_REGISTRY.coder_b)
    assert key_a != key_b
    assert cache_key(request, MOCK_REGISTRY.coder_a) == key_a


def test_the_key_ignores_the_subject_because_it_is_content_addressed() -> None:
    """`cache_key_parts` excludes run ids and subjects on purpose."""
    text = synthetic_corpus()[0].content
    assert cache_key(coding_request(text, 3), MOCK_REGISTRY.coder_a) == cache_key(
        coding_request(text, 999), MOCK_REGISTRY.coder_a
    )


def test_a_corrupt_entry_is_survived_not_raised_on(tmp_path) -> None:  # type: ignore[no-untyped-def]
    client = CachingLLMClient(MockCoderClient(MOCK_REGISTRY.coder_a), tmp_path)
    request = coding_request(synthetic_corpus()[2].content, 12)
    expected = client.complete_json(request)

    path = client.path_for(request)
    assert path is not None and path.exists()
    path.write_text("{ this is not json", encoding="utf-8")

    recovered = client.complete_json(request)
    assert recovered.cache_hit is False, "a corrupt entry is refetched, not read"
    assert recovered.data == expected.data
    assert client.complete_json(request).cache_hit is True, "and is repaired on the way past"


def test_an_entry_for_a_different_task_is_ignored(tmp_path) -> None:  # type: ignore[no-untyped-def]
    client = CachingLLMClient(MockCoderClient(MOCK_REGISTRY.coder_a), tmp_path)
    request = coding_request(synthetic_corpus()[3].content, 17)
    client.complete_json(request)
    path = client.path_for(request)
    assert path is not None
    stored = json.loads(path.read_text(encoding="utf-8"))
    stored["result"]["task"] = "judge_fit"
    path.write_text(json.dumps(stored), encoding="utf-8")
    assert client.complete_json(request).cache_hit is False


def test_a_disabled_cache_is_a_pass_through() -> None:
    client = CachingLLMClient(MockCoderClient(MOCK_REGISTRY.coder_a), None)
    request = coding_request(synthetic_corpus()[0].content, 3)
    assert client.enabled is False
    assert client.path_for(request) is None
    assert client.complete_json(request).cache_hit is False
    assert client.complete_json(request).cache_hit is False
    assert client.spec is MOCK_REGISTRY.coder_a


def test_a_fail_safe_result_is_never_cached(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Freezing a transient parse failure would make it permanent."""
    client = CachingLLMClient(MockJudgeClient(), tmp_path)
    request = refactor_request("the judge cannot answer this")
    assert client.complete_json(request).fail_safe is True
    path = client.path_for(request)
    assert path is not None and not path.exists()
    assert client.complete_json(request).cache_hit is False


# --------------------------------------------------------------------------- #
# The live clients — construction, and the parse path through the transport seam
# --------------------------------------------------------------------------- #

LIVE = [
    ("openai", OpenAIClient, OpenAISDKError, "uv sync --extra openai"),
    ("google.genai", GeminiClient, GeminiSDKError, "uv sync --extra gemini"),
    ("anthropic", AnthropicClient, AnthropicSDKError, "uv sync --extra anthropic"),
]


def _spec(provider: str) -> ModelSpec:
    return ModelSpec(
        provider="openai" if provider == "openai" else ("gemini" if "genai" in provider else "anthropic"),
        model=f"{provider}-test-model",
        role="coder_a",
        input_usd_per_mtok=1.0,
        output_usd_per_mtok=2.0,
    )


@pytest.mark.parametrize(("module", "client_cls", "error_cls", "hint"), LIVE)
def test_a_live_client_imports_cleanly_and_names_its_extra_when_constructed(
    module: str, client_cls, error_cls, hint: str  # type: ignore[no-untyped-def]
) -> None:
    """Importing the module must cost nothing; constructing without the SDK must be loud."""
    if importlib.util.find_spec(module.split(".")[0]) is not None:  # pragma: no cover
        pytest.skip(f"{module} is installed in this environment")
    with pytest.raises(error_cls, match=hint):
        client_cls(_spec(module))


@pytest.mark.parametrize(("module", "client_cls", "_error_cls", "_hint"), LIVE)
def test_a_malformed_reply_becomes_the_fail_safe_and_never_raises(
    module: str, client_cls, _error_cls, _hint: str  # type: ignore[no-untyped-def]
) -> None:
    for task in TaskType:
        client = client_cls(
            _spec(module),
            transport=lambda _request: ("I'm sorry, I cannot help with that.", 11, 3),
        )
        result = client.complete_json(
            LLMRequest(task=task, system="s", user="u", prompt_version="v0", subject="1")
        )
        assert result.fail_safe is True
        assert result.data == fail_safe_for(task)
        assert result.input_tokens == 11 and result.output_tokens == 3
        assert result.cost_usd == pytest.approx((11 * 1.0 + 3 * 2.0) / 1_000_000)
        assert result.attempts == 1


@pytest.mark.parametrize(("module", "client_cls", "_error_cls", "_hint"), LIVE)
def test_a_fenced_reply_is_parsed_and_the_verdict_whitelisted(
    module: str, client_cls, _error_cls, _hint: str  # type: ignore[no-untyped-def]
) -> None:
    client = client_cls(
        _spec(module),
        transport=lambda _request: ('```json\n{"verdict": " applies "}\n```', 5, 2),
    )
    result = client.complete_json(
        LLMRequest(task=TaskType.JUDGE_FIT, system="s", user="u", prompt_version="v0", subject="1")
    )
    assert result.fail_safe is False
    assert result.data["verdict"] == "APPLIES"


@pytest.mark.parametrize(("module", "client_cls", "_error_cls", "_hint"), LIVE)
def test_a_verdict_outside_the_whitelist_becomes_the_non_destructive_default(
    module: str, client_cls, _error_cls, _hint: str  # type: ignore[no-untyped-def]
) -> None:
    client = client_cls(
        _spec(module),
        transport=lambda _request: ('{"verdict": "OBLITERATE", "reasoning": "x"}', 5, 2),
    )
    result = client.complete_json(
        LLMRequest(task=TaskType.JUDGE_FIT, system="s", user="u", prompt_version="v0", subject="1")
    )
    assert result.data["verdict"] == "APPLIES"
    assert result.data["reasoning"] == "x"
    assert result.fail_safe is False, "the reply parsed; only the verdict was coerced"


@pytest.mark.parametrize(("module", "client_cls", "_error_cls", "_hint"), LIVE)
def test_a_coding_reply_without_a_candidate_list_fails_safe(
    module: str, client_cls, _error_cls, _hint: str  # type: ignore[no-untyped-def]
) -> None:
    client = client_cls(
        _spec(module),
        transport=lambda _request: ('{"candidates": "positive_impacts-healthcare"}', 5, 2),
    )
    result = client.complete_json(
        LLMRequest(task=TaskType.CODE, system="s", user="u", prompt_version="v0", subject="3")
    )
    assert result.fail_safe is True
    assert result.data["candidates"] == []


@pytest.mark.parametrize(("module", "client_cls", "_error_cls", "_hint"), LIVE)
def test_a_transient_transport_failure_is_retried_and_counted(
    module: str, client_cls, _error_cls, _hint: str  # type: ignore[no-untyped-def]
) -> None:
    attempts = {"n": 0}

    def flaky(_request: LLMRequest) -> tuple[str, int, int]:
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise TimeoutError("transient")
        return '{"verdict": "KEEP", "reasoning": "ok"}', 4, 1

    client = client_cls(_spec(module), transport=flaky, base_delay_s=0.0)
    result = client.complete_json(
        LLMRequest(
            task=TaskType.JUDGE_DISPUTE, system="s", user="u", prompt_version="v0", subject="1"
        )
    )
    assert result.attempts == 3
    assert result.fail_safe is False
    assert result.data["verdict"] == "KEEP"


@pytest.mark.parametrize(("module", "client_cls", "_error_cls", "_hint"), LIVE)
def test_an_outage_raises_rather_than_silently_producing_empty_codings(
    module: str, client_cls, _error_cls, _hint: str  # type: ignore[no-untyped-def]
) -> None:
    """A malformed *reply* fails safe. A dead *transport* must halt the run."""

    def dead(_request: LLMRequest) -> tuple[str, int, int]:
        raise ConnectionError("no route to host")

    client = client_cls(_spec(module), transport=dead, base_delay_s=0.0, max_attempts=2)
    with pytest.raises(LLMError, match="failed after 2 attempts"):
        client.complete_json(
            LLMRequest(task=TaskType.CODE, system="s", user="u", prompt_version="v0", subject="3")
        )
