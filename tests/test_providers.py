"""The live provider clients on the 5-series (ADR-0051) and the hosted OpenAI-compatible
provider (ADR-0052). No key, no network, no paid call.

The Anthropic tests put a fake ``anthropic`` module in front of `importlib`, so the real
request building and reply reading run without the SDK (which CI does not install).
One further test drives the real 1.x SDK against an in-process HTTP transport, and skips
where the SDK is absent. The hosted-endpoint tests replace ``urlopen`` or the module's
``post_json``; nothing opens a socket. Every prompt and reply is made up.
"""

from __future__ import annotations

import io
import json
import sys
import types
import urllib.error
from pathlib import Path
from typing import Any

import pytest

import gaf.cli._common as common
import gaf.compat_endpoint as compat
import gaf.llm.compat_client as compat_client_module
import gaf.llm.local_client as local_client_module
import gaf.local_endpoint as local_endpoint
from gaf.cli import CliError
from gaf.cli._common import (
    _live_client,
    _run_config_from_json,
    coder_family,
    coders_are_distinct,
    live_components,
    load_profile,
)
from gaf.config import EFFORT_LEVELS, ModelRegistry, ModelSpec, RunConfig
from gaf.llm.anthropic_client import (
    AnthropicClient,
    IncompleteReplyError,
    accepts_sampling_params,
    read_message,
)
from gaf.llm.base import LLMError, LLMRequest, TaskType, fail_safe_for
from gaf.llm.compat_client import OpenAICompatibleClient
from gaf.llm.local_client import LocalClient
from gaf.llm.mock import MockCoderClient, MockJudgeClient

OPUS = "claude-opus-5-5"


def _opus(role: str = "judge", **overrides: Any) -> ModelSpec:
    fields: dict[str, Any] = {
        "provider": "anthropic",
        "model": OPUS,
        "role": role,
        "max_output_tokens": 4096,
        "input_usd_per_mtok": 4.0,
        "output_usd_per_mtok": 20.0,
        **overrides,
    }
    return ModelSpec(**fields)


def _request(task: TaskType = TaskType.JUDGE_FIT, **overrides: Any) -> LLMRequest:
    fields: dict[str, Any] = {
        "task": task, "system": "sys", "user": "usr", "prompt_version": "v0", "subject": "7",
        **overrides,
    }
    return LLMRequest(**fields)


# --------------------------------------------------------------------------- #
# The rule: which models take sampling parameters
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "model",
    [
        "claude-opus-5-5", "claude-opus-5", "claude-opus-4-8", "claude-opus-4-7",
        "claude-sonnet-5-5", "claude-sonnet-5", "claude-fable-5-1", "claude-fable-5",
        "claude-mythos-5-1", "claude-opus-6", "claude-something-new", "gpt-4o-mini",
    ],
)
def test_the_5_series_and_any_unrecognised_id_get_no_sampling_parameters(model: str) -> None:
    assert accepts_sampling_params(model) is False


@pytest.mark.parametrize(
    "model",
    [
        "claude-opus-4-6", "claude-sonnet-4-6", "claude-opus-4-5", "claude-haiku-4-5",
        "claude-haiku-4-5-20251001", "claude-sonnet-4-5-20250929", "claude-opus-4-1-20250805",
        "claude-opus-4-20250514", "claude-opus-4-0", "claude-3-5-haiku-20241022",
    ],
)
def test_the_older_lines_keep_their_temperature(model: str) -> None:
    assert accepts_sampling_params(model) is True


# --------------------------------------------------------------------------- #
# The request shape
# --------------------------------------------------------------------------- #


def test_an_opus_5_5_request_carries_no_temperature_and_the_effort_only_when_set() -> None:
    def never(_request: LLMRequest) -> tuple[str, int, int]:
        raise AssertionError("not called")

    with_effort = AnthropicClient(_opus(effort="low"), transport=never)
    params = with_effort.request_params(_request(temperature=0.7))
    assert params == {
        "model": OPUS,
        "max_tokens": 4096,
        "system": "sys",
        "messages": [{"role": "user", "content": "usr"}],
        "output_config": {"effort": "low"},
    }
    assert "thinking" not in params, "thinking is always on; it is never configured"
    without = AnthropicClient(_opus(), transport=never).request_params(_request())
    assert "output_config" not in without and "extra_body" not in without


def test_an_older_model_still_gets_its_temperature_through_the_body() -> None:
    spec = _opus(model="claude-sonnet-4-6", temperature=0.0)
    client = AnthropicClient(spec, transport=lambda _r: ("{}", 0, 0))
    assert client.request_params(_request())["extra_body"] == {"temperature": 0.0}
    assert client.request_params(_request(temperature=0.4))["extra_body"] == {"temperature": 0.4}
    assert client.request_params(_request(max_output_tokens=99))["max_tokens"] == 99


# --------------------------------------------------------------------------- #
# The reply: text blocks only, and the two early stops
# --------------------------------------------------------------------------- #


def _block(kind: str, text: str = "") -> types.SimpleNamespace:
    if kind == "thinking":
        return types.SimpleNamespace(type="thinking", thinking="", signature="sig")
    return types.SimpleNamespace(type=kind, text=text)


def _message(
    *blocks: types.SimpleNamespace,
    stop_reason: str = "end_turn",
    category: str | None = None,
    input_tokens: int = 120,
    output_tokens: int = 900,
) -> types.SimpleNamespace:
    details = (
        types.SimpleNamespace(type="refusal", category=category, explanation="x")
        if stop_reason == "refusal"
        else None
    )
    return types.SimpleNamespace(
        content=list(blocks),
        stop_reason=stop_reason,
        stop_details=details,
        usage=types.SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens),
    )


def test_only_text_blocks_are_read_and_thinking_counts_as_output() -> None:
    message = _message(
        _block("thinking"), _block("text", '{"verdict": '), _block("text", '"APPLIES"}')
    )
    assert read_message(message) == ('{"verdict": "APPLIES"}', 120, 900)


@pytest.mark.parametrize(
    ("stop_reason", "category", "described"),
    [("refusal", "bio", "refusal (bio)"), ("refusal", None, "refusal"),
     ("max_tokens", None, "max_tokens")],
)
def test_an_early_stop_is_raised_with_the_tokens_it_was_billed_for(
    stop_reason: str, category: str | None, described: str
) -> None:
    message = _message(_block("thinking"), _block("text", '{"verd'),
                       stop_reason=stop_reason, category=category)
    with pytest.raises(IncompleteReplyError) as excinfo:
        read_message(message)
    stop = excinfo.value
    assert (stop.stop_reason, stop.category, stop.describe()) == (stop_reason, category, described)
    assert (stop.text, stop.input_tokens, stop.output_tokens) == ('{"verd', 120, 900)


@pytest.mark.parametrize("task", list(TaskType))
@pytest.mark.parametrize("stop_reason", ["refusal", "max_tokens"])
def test_an_early_stop_becomes_the_fail_safe_is_recorded_and_is_not_retried(
    task: TaskType, stop_reason: str
) -> None:
    calls: list[int] = []

    def stops(_request: LLMRequest) -> tuple[str, int, int]:
        calls.append(1)
        # A reply that would parse, to prove an early stop is never read as an answer.
        raise IncompleteReplyError(
            stop_reason, text='{"verdict": "DROP", "route": "MERGE", "candidates": [], '
            '"operations": []}', input_tokens=50, output_tokens=4096, category="cyber"
            if stop_reason == "refusal" else None,
        )

    client = AnthropicClient(_opus(), transport=stops, base_delay_s=0.0)
    result = client.complete_json(_request(task))
    assert calls == [1], "an early stop is returned, not retried"
    assert result.fail_safe is True and result.attempts == 1
    expected = fail_safe_for(task)
    for key, value in expected.items():
        if key != "reasoning":
            assert result.data[key] == value
    assert result.data["_stop_reason"] == stop_reason
    if "reasoning" in expected:
        assert stop_reason in result.data["reasoning"]
    assert (result.input_tokens, result.output_tokens) == (50, 4096)
    assert result.cost_usd == pytest.approx((50 * 4.0 + 4096 * 20.0) / 1_000_000)


# --------------------------------------------------------------------------- #
# The live transport, against a fake SDK module
# --------------------------------------------------------------------------- #


class _FakeStream:
    def __init__(self, message: Any) -> None:
        self._message = message

    def __enter__(self) -> _FakeStream:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def get_final_message(self) -> Any:
        return self._message


def _fake_sdk(
    monkeypatch: pytest.MonkeyPatch, replies: list[Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Install a fake ``anthropic`` module. Returns (requests sent, client kwargs)."""
    sent: list[dict[str, Any]] = []
    built: list[dict[str, Any]] = []

    class _Messages:
        def stream(self, **params: Any) -> _FakeStream:
            sent.append(params)
            return _FakeStream(replies.pop(0))

        def create(self, **params: Any) -> Any:  # pragma: no cover - must not be used
            raise AssertionError("non-streaming create() must not be used")

    class _Anthropic:
        def __init__(self, **kwargs: Any) -> None:
            built.append(kwargs)
            self.messages = _Messages()

    module = types.ModuleType("anthropic")
    module.Anthropic = _Anthropic  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "anthropic", module)
    return sent, built


def test_the_live_transport_streams_and_reads_the_final_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent, built = _fake_sdk(
        monkeypatch,
        [_message(_block("thinking"), _block("text", '```json\n{"verdict": "drop"}\n```'),
                  input_tokens=300, output_tokens=650)],
    )
    client = AnthropicClient(_opus(effort="low"), api_key="sk-test")
    result = client.complete_json(_request(TaskType.JUDGE_DISPUTE))
    assert built == [{"api_key": "sk-test"}]
    assert sent == [client.request_params(_request(TaskType.JUDGE_DISPUTE))]
    assert "temperature" not in sent[0] and "extra_body" not in sent[0]
    assert result.data["verdict"] == "DROP" and result.fail_safe is False
    assert (result.input_tokens, result.output_tokens) == (300, 650)
    assert result.cost_usd == pytest.approx((300 * 4.0 + 650 * 20.0) / 1_000_000)
    assert result.provider == "anthropic" and result.model == OPUS


def test_a_live_refusal_fails_safe_with_its_category_in_the_reasoning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, built = _fake_sdk(monkeypatch, [_message(_block("thinking"), stop_reason="refusal",
                                                category="bio", input_tokens=80,
                                                output_tokens=0)])
    result = AnthropicClient(_opus()).complete_json(_request(TaskType.JUDGE_FIT))
    assert built == [{}], "no key passed: the SDK resolves its own credentials"
    assert result.fail_safe is True
    assert result.data["verdict"] == "APPLIES", "the non-destructive default"
    assert result.data["_stop_category"] == "bio"
    assert result.data["reasoning"] == "fail-safe: the model stopped with refusal (bio)"


# --------------------------------------------------------------------------- #
# The real 1.x SDK, end to end over an in-process transport
# --------------------------------------------------------------------------- #


def _sse(events: list[tuple[str, dict[str, Any]]]) -> bytes:
    return "".join(
        f"event: {name}\ndata: {json.dumps(data)}\n\n" for name, data in events
    ).encode("utf-8")


def _stream_body(text: str, stop_reason: str = "end_turn") -> bytes:
    message = {
        "id": "msg_test", "type": "message", "role": "assistant", "model": OPUS,
        "content": [], "stop_reason": None, "stop_sequence": None,
        "usage": {"input_tokens": 210, "output_tokens": 1},
    }
    return _sse([
        ("message_start", {"type": "message_start", "message": message}),
        ("content_block_start", {"type": "content_block_start", "index": 0,
                                 "content_block": {"type": "thinking", "thinking": "",
                                                   "signature": ""}}),
        ("content_block_delta", {"type": "content_block_delta", "index": 0,
                                 "delta": {"type": "signature_delta", "signature": "abc"}}),
        ("content_block_stop", {"type": "content_block_stop", "index": 0}),
        ("content_block_start", {"type": "content_block_start", "index": 1,
                                 "content_block": {"type": "text", "text": ""}}),
        ("content_block_delta", {"type": "content_block_delta", "index": 1,
                                 "delta": {"type": "text_delta", "text": text}}),
        ("content_block_stop", {"type": "content_block_stop", "index": 1}),
        ("message_delta", {"type": "message_delta",
                           "delta": {"stop_reason": stop_reason, "stop_sequence": None},
                           "usage": {"output_tokens": 777}}),
        ("message_stop", {"type": "message_stop"}),
    ])


def test_the_real_sdk_sends_effort_and_no_temperature_and_reads_past_the_thinking(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    anthropic = pytest.importorskip("anthropic")
    httpx2 = pytest.importorskip("httpx2")
    bodies: list[dict[str, Any]] = []
    replies = [_stream_body('{"route": "merge", "reasoning": "same idea"}'),
               _stream_body('{"route": "MERGE"', stop_reason="max_tokens")]

    def handler(request: Any) -> Any:
        bodies.append(json.loads(request.content))
        return httpx2.Response(
            200, content=replies.pop(0), headers={"content-type": "text/event-stream"}
        )

    real = anthropic.Anthropic

    def offline(**kwargs: Any) -> Any:
        return real(
            base_url="http://anthropic.test",
            http_client=anthropic.DefaultHttpxClient(transport=httpx2.MockTransport(handler)),
            max_retries=0,
            **kwargs,
        )

    monkeypatch.setattr(anthropic, "Anthropic", offline)
    client = AnthropicClient(_opus(role="coder_a", effort="medium"), api_key="sk-offline")
    first = client.complete_json(_request(TaskType.JUDGE_ROUTE))
    second = client.complete_json(_request(TaskType.JUDGE_ROUTE))

    body = bodies[0]
    assert body["model"] == OPUS and body["stream"] is True
    assert body["output_config"] == {"effort": "medium"}
    assert not {"temperature", "top_p", "top_k", "thinking"} & set(body)
    assert first.data == {"route": "MERGE", "reasoning": "same idea"}
    assert (first.input_tokens, first.output_tokens, first.fail_safe) == (210, 777, False)
    assert second.fail_safe is True and second.data["route"] == "CREATE"
    assert second.data["_stop_reason"] == "max_tokens"
    assert second.output_tokens == 777, "a truncated reply is still billed and recorded"


# --------------------------------------------------------------------------- #
# Shared fixtures for the hosted-endpoint tests below
# --------------------------------------------------------------------------- #


class _FakeReply(io.BytesIO):
    def __enter__(self) -> _FakeReply:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def _chat_reply(content: str, prompt_tokens: int = 11, completion_tokens: int = 5) -> dict[str, Any]:
    return {
        "choices": [{"message": {"role": "assistant", "content": content}}],
        "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens},
    }



@pytest.fixture
def compat_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(compat.BASE_URL_ENV, compat.DASHSCOPE_INTL_BASE_URL + "/")
    monkeypatch.setenv(compat.API_KEY_ENV, "sk-made-up")
    monkeypatch.delenv(compat.THINKING_OFF_ENV, raising=False)


def _qwen(model: str = "qwen3.8-max", role: str = "coder_b") -> ModelSpec:
    return ModelSpec(
        provider="openai_compatible", model=model, role=role,  # type: ignore[arg-type]
        input_usd_per_mtok=2.0, output_usd_per_mtok=6.0,
    )


# --------------------------------------------------------------------------- #
# The hosted endpoint: explicit, https, keyed
# --------------------------------------------------------------------------- #


def test_the_hosted_endpoint_has_no_default_and_requires_https_and_a_key() -> None:
    with pytest.raises(compat.CompatEndpointError, match="no default"):
        compat.compat_base_url({})
    for url in ("http://dashscope-intl.aliyuncs.com/compatible-mode/v1", "dashscope.example"):
        with pytest.raises(compat.CompatEndpointError, match="not an https URL"):
            compat.compat_base_url({compat.BASE_URL_ENV: url})
    assert compat.compat_base_url({compat.BASE_URL_ENV: compat.OPENROUTER_BASE_URL + "/"}) == (
        "https://openrouter.ai/api/v1"
    )
    with pytest.raises(compat.CompatEndpointError, match=compat.API_KEY_ENV):
        compat.compat_api_key({compat.API_KEY_ENV: "  "})
    assert compat.compat_api_key({compat.API_KEY_ENV: " k "}) == "k"


def test_thinking_off_is_the_default_and_zero_turns_the_field_off() -> None:
    assert compat.thinking_off({}) is True
    assert compat.thinking_off({compat.THINKING_OFF_ENV: "1"}) is True
    assert compat.thinking_off({compat.THINKING_OFF_ENV: "0"}) is False


def test_the_hosted_post_sends_the_key_and_names_the_host_when_it_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[tuple[str | None, Any]] = []

    def ok(request: Any, timeout: float) -> _FakeReply:
        seen.append((request.get_header("Authorization"), json.loads(request.data)))
        return _FakeReply(b'{"ok": 1}')

    monkeypatch.setattr(compat.urllib.request, "urlopen", ok)
    assert compat.post_json("https://h.test/v1/chat/completions", {"a": 1}, api_key="k") == {"ok": 1}
    assert seen == [("Bearer k", {"a": 1})]

    def down(request: Any, timeout: float) -> _FakeReply:
        raise urllib.error.URLError("name not known")

    monkeypatch.setattr(compat.urllib.request, "urlopen", down)
    with pytest.raises(compat.CompatEndpointError, match=compat.BASE_URL_ENV) as excinfo:
        compat.post_json("https://h.test/v1/chat/completions", {}, api_key="k")
    assert "ollama" not in str(excinfo.value), "a hosted failure is not described as local"

    def refused(request: Any, timeout: float) -> _FakeReply:
        raise urllib.error.HTTPError(
            request.full_url, 401, "no", {}, io.BytesIO(b'{"error":"invalid api key"}')  # type: ignore[arg-type]
        )

    monkeypatch.setattr(compat.urllib.request, "urlopen", refused)
    with pytest.raises(compat.CompatEndpointError, match=r"401.*invalid api key"):
        compat.post_json("https://h.test/v1/chat/completions", {}, api_key="k")


# --------------------------------------------------------------------------- #
# The hosted client: the shared transport, sent elsewhere
# --------------------------------------------------------------------------- #


def test_the_hosted_client_sends_json_mode_with_thinking_off_to_the_configured_host(
    monkeypatch: pytest.MonkeyPatch, compat_env: None
) -> None:
    calls: list[tuple[str, dict[str, Any], str]] = []

    def fake_post(url: str, payload: dict[str, Any], *, api_key: str, **_: Any) -> Any:
        calls.append((url, payload, api_key))
        return _chat_reply('<think>{"draft": 1}</think>{"candidates": []}', 1200, 300)

    monkeypatch.setattr(compat_client_module, "post_json", fake_post)
    client = OpenAICompatibleClient(_qwen(), seed=11)
    result = client.complete_json(_request(TaskType.CODE))
    assert result.fail_safe is False and result.data == {"candidates": []}
    assert result.provider == "openai_compatible" and result.model == "qwen3.8-max"
    assert result.cost_usd == pytest.approx((1200 * 2.0 + 300 * 6.0) / 1_000_000)
    url, payload, key = calls[0]
    assert url == compat.DASHSCOPE_INTL_BASE_URL + "/chat/completions"
    assert key == "sk-made-up"
    assert payload["response_format"] == {"type": "json_object"}
    assert payload["enable_thinking"] is False
    assert "reasoning_effort" not in payload, "Ollama's field is not sent to a hosted router"
    assert payload["model"] == "qwen3.8-max" and payload["seed"] == 11
    assert payload["stream"] is False


def test_the_thinking_field_can_be_dropped_for_a_strict_host_and_a_key_passed_in(
    monkeypatch: pytest.MonkeyPatch, compat_env: None
) -> None:
    monkeypatch.setenv(compat.THINKING_OFF_ENV, "0")
    sent: list[tuple[dict[str, Any], str]] = []
    monkeypatch.setattr(
        compat_client_module, "post_json",
        lambda url, payload, *, api_key, **_: sent.append((payload, api_key))
        or _chat_reply('{"verdict": "KEEP"}'),
    )
    OpenAICompatibleClient(_qwen(), api_key="explicit").complete_json(
        _request(TaskType.JUDGE_DISPUTE)
    )
    payload, key = sent[0]
    assert "enable_thinking" not in payload and key == "explicit"


def test_a_hosted_client_without_its_variables_is_refused_at_construction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(compat.BASE_URL_ENV, raising=False)
    monkeypatch.setenv(compat.API_KEY_ENV, "k")
    with pytest.raises(compat.CompatEndpointError, match=compat.BASE_URL_ENV):
        OpenAICompatibleClient(_qwen())
    monkeypatch.setenv(compat.BASE_URL_ENV, compat.OPENROUTER_BASE_URL)
    monkeypatch.delenv(compat.API_KEY_ENV)
    with pytest.raises(compat.CompatEndpointError, match=compat.API_KEY_ENV):
        OpenAICompatibleClient(_qwen())


def test_a_hosted_failure_is_a_transport_error_and_prose_is_a_fail_safe(
    monkeypatch: pytest.MonkeyPatch, compat_env: None
) -> None:
    def dead(url: str, payload: dict[str, Any], **_: Any) -> Any:
        raise compat.CompatEndpointError("the hosted endpoint could not be reached")

    monkeypatch.setattr(compat_client_module, "post_json", dead)
    with pytest.raises(LLMError, match="could not be reached"):
        OpenAICompatibleClient(_qwen(), max_attempts=2, base_delay_s=0.0).complete_json(
            _request()
        )
    monkeypatch.setattr(
        compat_client_module, "post_json", lambda url, payload, **_: _chat_reply("In words.")
    )
    result = OpenAICompatibleClient(_qwen()).complete_json(_request(TaskType.JUDGE_ROUTE))
    assert result.fail_safe is True and result.data == fail_safe_for(TaskType.JUDGE_ROUTE)


def test_the_local_providers_loopback_guard_is_unchanged_by_the_hosted_provider(
    monkeypatch: pytest.MonkeyPatch, compat_env: None
) -> None:
    """Configuring the hosted endpoint must not make a remote host acceptable as "local"."""
    monkeypatch.delenv(local_endpoint.ALLOW_REMOTE_ENV, raising=False)
    monkeypatch.setenv(local_endpoint.BASE_URL_ENV, compat.DASHSCOPE_INTL_BASE_URL)
    with pytest.raises(local_endpoint.LocalEndpointError, match=local_endpoint.ALLOW_REMOTE_ENV):
        local_endpoint.local_base_url()
    with pytest.raises(local_endpoint.LocalEndpointError, match=local_endpoint.ALLOW_REMOTE_ENV):
        LocalClient(ModelSpec(provider="local", model="qwen3.5:9b", role="coder_b"))
    monkeypatch.delenv(local_endpoint.BASE_URL_ENV)
    assert local_endpoint.local_base_url() == local_endpoint.DEFAULT_BASE_URL
    # And the local client still sends Ollama's field and no hosted one.
    sent: list[dict[str, Any]] = []
    monkeypatch.setattr(
        local_client_module, "post_json",
        lambda url, payload, **_: sent.append(payload) or _chat_reply("{}"),
    )
    LocalClient(ModelSpec(provider="local", model="qwen3.5:9b", role="coder_b")).complete_json(
        _request()
    )
    assert sent[0]["reasoning_effort"] == "none" and "enable_thinking" not in sent[0]


# --------------------------------------------------------------------------- #
# Coder diversity across server providers
# --------------------------------------------------------------------------- #


def _two(a: ModelSpec, b: ModelSpec) -> ModelRegistry:
    return ModelRegistry(coder_a=a, coder_b=b, judge=_opus(), refactorer=_opus("refactorer"))


def test_opus_beside_a_hosted_qwen_is_diverse_and_two_qwens_are_not() -> None:
    opus = _opus("coder_a")
    assert coders_are_distinct(_two(opus, _qwen()))
    assert not coders_are_distinct(_two(_qwen(role="coder_a"), _qwen("qwen3.5-plus")))
    assert coders_are_distinct(_two(_qwen(role="coder_a"), _qwen("glm-5")))
    local_qwen = ModelSpec(provider="local", model="qwen3.5:9b", role="coder_a")
    assert not coders_are_distinct(_two(local_qwen, _qwen())), "one family, two servers"
    routed_claude = _qwen("anthropic/claude-opus-5-5")
    assert coder_family(routed_claude) == "claude"
    assert not coders_are_distinct(_two(opus, routed_claude)), "Claude through a router is Claude"


def test_live_components_names_the_shared_family_of_two_hosted_coders() -> None:
    same = _two(_qwen(role="coder_a"), _qwen("qwen3.5-plus"))
    with pytest.raises(CliError) as excinfo:
        live_components(RunConfig(offline=False, models=same))
    message = str(excinfo.value)
    assert "different providers" in message and "'qwen'" in message and "ADR-0052" in message


def test_a_missing_hosted_variable_is_a_cli_error_with_no_install_step(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(compat.BASE_URL_ENV, raising=False)
    with pytest.raises(CliError) as excinfo:
        _live_client(_qwen(), RunConfig(offline=False))
    message = str(excinfo.value)
    assert "GAF_COMPAT_BASE_URL and GAF_COMPAT_API_KEY" in message
    assert "install the provider extra" not in message


# --------------------------------------------------------------------------- #
# Profiles: effort, and every shipped profile through the live validation
# --------------------------------------------------------------------------- #

PROFILES = sorted((Path(__file__).parent.parent / "profiles").glob("*.json"))


def _profile(path: Path, models: dict[str, Any]) -> Path:
    path.write_text(json.dumps({"models": models}))
    return path


def _opus_roles(**judge: Any) -> dict[str, Any]:
    opus = {"provider": "anthropic", "model": OPUS}
    return {
        "coder_a": {**opus, "effort": "medium"},
        "coder_b": {"provider": "openai_compatible", "model": "qwen3.8-max"},
        "judge": {**opus, **judge},
        "refactorer": {**opus, "effort": "high", "max_output_tokens": 16000},
    }


def test_a_profile_carries_effort_and_the_echo_shows_it_only_where_set(tmp_path: Path) -> None:
    models, _ = load_profile(_profile(tmp_path / "p.json", _opus_roles(effort="low")))
    assert (models.coder_a.effort, models.judge.effort, models.refactorer.effort) == (
        "medium", "low", "high",
    )
    echo = RunConfig(offline=False, models=models).to_json()
    assert echo["models"]["judge"]["effort"] == "low"
    assert "effort" not in echo["models"]["coder_b"]
    assert _run_config_from_json(echo).to_json() == echo, "the echo round-trips exactly"
    assert all("effort" not in spec for spec in RunConfig().to_json()["models"].values())


def test_an_unknown_effort_is_refused(tmp_path: Path) -> None:
    with pytest.raises(CliError, match="one of low, medium, high, xhigh, max"):
        load_profile(_profile(tmp_path / "p.json", _opus_roles(effort="extreme")))


def test_effort_on_a_provider_without_it_is_refused(tmp_path: Path) -> None:
    roles = _opus_roles()
    roles["coder_b"] = {**roles["coder_b"], "effort": "low"}
    with pytest.raises(CliError, match="only the anthropic provider has"):
        load_profile(_profile(tmp_path / "p.json", roles))


def test_the_shipped_profiles_are_the_three_the_runbook_names() -> None:
    assert {p.name for p in PROFILES} >= {
        "local-ollama.json", "opus-qwen.json", "opus-local-qwen.json",
    }


@pytest.mark.parametrize("path", PROFILES, ids=lambda p: p.name)
def test_every_shipped_profile_passes_the_live_validation(
    path: Path, monkeypatch: pytest.MonkeyPatch, compat_env: None
) -> None:
    """Loads through `load_profile` and through `live_components` — the mock-role check,
    the coder-diversity rule and the local pre-flight — with the provider clients and the
    local server faked, so nothing is sent anywhere."""
    models, embedding = load_profile(path)
    assert embedding is not None and embedding.mode == "local" and embedding.dim == 768
    for spec in models.all_specs():
        assert spec.provider != "mock"
        if spec.provider == "anthropic":
            assert spec.effort in EFFORT_LEVELS, (path.name, spec.role)
            assert spec.priced_on and spec.output_usd_per_mtok > 0, (path.name, spec.role)
    if any(s.provider == "anthropic" for s in models.all_specs()):
        floors = {"coder_a": 8192, "judge": 4096, "refactorer": 16000}
        for role, floor in floors.items():
            spec = models.for_role(role)
            if spec.provider == "anthropic":
                assert spec.max_output_tokens >= floor, (path.name, role)
    served = {"data": [{"id": f"{m}:latest" if ":" not in m else m}
                       for m in ("embeddinggemma", *(s.model for s in models.all_specs()))]}
    monkeypatch.setattr(local_endpoint, "get_json", lambda url, timeout=5.0: served)
    built: list[str] = []

    def fake_client(spec: ModelSpec, config: RunConfig) -> Any:
        built.append(spec.role)
        return MockCoderClient(spec) if spec.role.startswith("coder") else MockJudgeClient(spec)

    monkeypatch.setattr(common, "_live_client", fake_client)
    components = live_components(
        RunConfig(offline=False, models=models, embedding=embedding, cache_dir=None)
    )
    assert built == ["coder_a", "coder_b", "judge"]
    assert components.embedder.space_id == "local-embeddinggemma-768"


def test_the_opus_profiles_say_where_respondent_text_goes() -> None:
    for name in ("opus-qwen.json", "opus-local-qwen.json"):
        raw = json.loads((Path(__file__).parent.parent / "profiles" / name).read_text())
        assert "WHERE RESPONDENT TEXT GOES" in raw["description"]
        assert "Anthropic" in raw["description"]
    hosted = json.loads((Path(__file__).parent.parent / "profiles" / "opus-qwen.json").read_text())
    assert "GAF_COMPAT_BASE_URL" in hosted["description"]
    assert "CONFIRM ON THE DAY" in hosted["description"]
