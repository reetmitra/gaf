"""The local provider and the local embedding space (ADR-0049). No server, no network.

Every test here replaces the two HTTP helpers in `gaf.local_endpoint` with an in-process
fake, so the suite exercises the real request building, parsing, fail-safe and
dimension checks without a model server — and without a socket, which is the rule for
this suite. The corpus is the synthetic one; no respondent text is anywhere near it.
"""

from __future__ import annotations

import io
import json
import sqlite3
import urllib.error
from pathlib import Path
from typing import Any

import numpy as np
import pytest

import gaf.llm.local_client as local_client_module
import gaf.local_endpoint as endpoint
from gaf.cli import EXIT_INPUT, EXIT_OK, EXIT_USAGE, CliError, main
from gaf.cli._common import (
    check_local_models,
    coders_are_distinct,
    load_profile,
    model_family,
)
from gaf.config import EmbeddingSpaceConfig, ModelRegistry, ModelSpec, RunConfig
from gaf.embed.service import LOCAL_BATCH_SIZE, EmbeddingService, lexical_vector
from gaf.ingest.corpus import write_corpus_json
from gaf.llm.base import LLMError, LLMRequest, TaskType, fail_safe_for
from gaf.llm.local_client import LocalClient, strip_thinking
from tests.fixtures.corpus import synthetic_corpus

LOCAL_MODELS = ("qwen3.5:9b", "gemma4:12b", "gpt-oss:20b", "qwen3-embedding:0.6b")


def _spec(model: str = "qwen3.5:9b", role: str = "coder_a") -> ModelSpec:
    return ModelSpec(provider="local", model=model, role=role)  # type: ignore[arg-type]


def _request(task: TaskType = TaskType.JUDGE_FIT) -> LLMRequest:
    return LLMRequest(task=task, system="s", user="u", prompt_version="v0", subject="1")


def _chat_reply(content: str, prompt_tokens: int = 7, completion_tokens: int = 3) -> dict[str, Any]:
    return {
        "choices": [{"message": {"role": "assistant", "content": content}}],
        "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens},
    }


@pytest.fixture
def no_local_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(endpoint.BASE_URL_ENV, raising=False)
    monkeypatch.delenv(endpoint.ALLOW_REMOTE_ENV, raising=False)


# --------------------------------------------------------------------------- #
# The endpoint: which server, and the refusal that keeps "local" local
# --------------------------------------------------------------------------- #


def test_the_default_endpoint_is_ollama_on_this_machine(no_local_env: None) -> None:
    assert endpoint.local_base_url() == "http://localhost:11434/v1"


@pytest.mark.parametrize(
    "url", ["http://127.0.0.1:1234/v1/", "http://[::1]:8080/v1", "https://localhost/v1"]
)
def test_any_loopback_server_is_accepted_and_the_trailing_slash_dropped(url: str) -> None:
    assert endpoint.local_base_url({endpoint.BASE_URL_ENV: url}) == url.rstrip("/")


def test_a_remote_host_is_refused_because_local_is_a_privacy_claim() -> None:
    env = {endpoint.BASE_URL_ENV: "https://api.example.com/v1"}
    with pytest.raises(endpoint.LocalEndpointError, match=endpoint.ALLOW_REMOTE_ENV):
        endpoint.local_base_url(env)
    env[endpoint.ALLOW_REMOTE_ENV] = "1"
    assert endpoint.local_base_url(env) == "https://api.example.com/v1"


def test_a_url_that_is_not_http_is_refused() -> None:
    with pytest.raises(endpoint.LocalEndpointError, match="not an http"):
        endpoint.local_base_url({endpoint.BASE_URL_ENV: "localhost:11434"})


class _FakeReply(io.BytesIO):
    def __enter__(self) -> _FakeReply:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def test_post_json_round_trips_and_names_the_server_when_it_is_down(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent: list[Any] = []

    def ok(request: Any, timeout: float) -> _FakeReply:
        sent.append(json.loads(request.data))
        return _FakeReply(b'{"ok": true}')

    monkeypatch.setattr(endpoint.urllib.request, "urlopen", ok)
    assert endpoint.post_json("http://localhost:1/v1/x", {"a": 1}) == {"ok": True}
    assert sent == [{"a": 1}]

    def down(request: Any, timeout: float) -> _FakeReply:
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(endpoint.urllib.request, "urlopen", down)
    with pytest.raises(endpoint.LocalEndpointError, match="ollama serve"):
        endpoint.get_json("http://localhost:1/v1/models")


def test_the_bearer_token_is_the_configured_key_or_a_placeholder(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[str | None] = []

    def capture(request: Any, timeout: float) -> _FakeReply:
        seen.append(request.get_header("Authorization"))
        return _FakeReply(b"{}")

    monkeypatch.setattr(endpoint.urllib.request, "urlopen", capture)
    monkeypatch.delenv(endpoint.API_KEY_ENV, raising=False)
    endpoint.get_json("http://localhost:1/v1/models")
    monkeypatch.setenv(endpoint.API_KEY_ENV, "sk-test")
    endpoint.post_json("http://localhost:1/v1/x", {})
    assert seen == ["Bearer local", "Bearer sk-test"]


def test_an_http_error_and_a_non_json_body_are_reported_not_swallowed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def refused(request: Any, timeout: float) -> _FakeReply:
        raise urllib.error.HTTPError(
            request.full_url, 404, "nf", {}, io.BytesIO(b'{"error":"model not found"}')  # type: ignore[arg-type]
        )

    monkeypatch.setattr(endpoint.urllib.request, "urlopen", refused)
    with pytest.raises(endpoint.LocalEndpointError, match=r"404.*model not found"):
        endpoint.post_json("http://localhost:1/v1/x", {})

    monkeypatch.setattr(
        endpoint.urllib.request, "urlopen", lambda request, timeout: _FakeReply(b"<html>")
    )
    with pytest.raises(endpoint.LocalEndpointError, match="non-JSON"):
        endpoint.get_json("http://localhost:1/v1/models")


def test_require_model_accepts_a_bare_name_as_latest_and_names_the_pull_command(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    listing = {"data": [{"id": "embeddinggemma:latest"}, {"id": "qwen3.5:9b"}]}
    monkeypatch.setattr(endpoint, "get_json", lambda url, timeout=5.0: listing)
    endpoint.require_model("http://localhost:1/v1", "embeddinggemma")
    endpoint.require_model("http://localhost:1/v1", "qwen3.5:9b")
    with pytest.raises(endpoint.LocalEndpointError, match="ollama pull gemma4:12b"):
        endpoint.require_model("http://localhost:1/v1", "gemma4:12b")
    monkeypatch.setattr(endpoint, "get_json", lambda url, timeout=5.0: {"models": []})
    with pytest.raises(endpoint.LocalEndpointError, match="model list"):
        endpoint.served_models("http://localhost:1/v1")


# --------------------------------------------------------------------------- #
# The chat client
# --------------------------------------------------------------------------- #


def test_a_thinking_block_is_removed_even_when_it_holds_braces_or_never_closes() -> None:
    assert strip_thinking('<think>try {"verdict": "X"}</think>\n{"verdict": "APPLIES"}') == (
        '{"verdict": "APPLIES"}'
    )
    assert strip_thinking('{"a": 1}<think>ran out of tokens {') == '{"a": 1}'
    assert strip_thinking('{"a": 1}') == '{"a": 1}'


def test_the_local_client_sends_a_json_request_and_parses_through_the_shared_safety_net(
    monkeypatch: pytest.MonkeyPatch, no_local_env: None
) -> None:
    calls: list[tuple[str, dict[str, Any]]] = []

    def fake_post(url: str, payload: dict[str, Any], *, timeout: float = 0) -> dict[str, Any]:
        calls.append((url, payload))
        return _chat_reply('<think>{"hmm": 1}</think>```json\n{"verdict": " applies "}\n```')

    monkeypatch.setattr(local_client_module, "post_json", fake_post)
    client = LocalClient(_spec(role="judge"), seed=7)
    result = client.complete_json(_request())
    assert result.data["verdict"] == "APPLIES"
    assert result.fail_safe is False
    assert result.provider == "local" and result.model == "qwen3.5:9b"
    assert (result.input_tokens, result.output_tokens, result.cost_usd) == (7, 3, 0.0)
    url, payload = calls[0]
    assert url == "http://localhost:11434/v1/chat/completions"
    assert payload["model"] == "qwen3.5:9b"
    assert payload["response_format"] == {"type": "json_object"}
    assert payload["seed"] == 7 and payload["stream"] is False
    assert [m["role"] for m in payload["messages"]] == ["system", "user"]


def test_a_local_model_that_cannot_follow_the_schema_fails_safe_and_never_raises(
    monkeypatch: pytest.MonkeyPatch, no_local_env: None
) -> None:
    monkeypatch.setattr(
        local_client_module, "post_json", lambda url, payload, **_: _chat_reply("Sure! Here you go.")
    )
    client = LocalClient(_spec())
    for task in TaskType:
        result = client.complete_json(_request(task))
        assert result.fail_safe is True
        assert result.data == fail_safe_for(task)


def test_a_dead_server_or_an_empty_reply_is_a_transport_failure_after_retries(
    monkeypatch: pytest.MonkeyPatch, no_local_env: None
) -> None:
    attempts: list[int] = []

    def dead(url: str, payload: dict[str, Any], **_: Any) -> dict[str, Any]:
        attempts.append(1)
        raise endpoint.LocalEndpointError("no local model server")

    monkeypatch.setattr(local_client_module, "post_json", dead)
    client = LocalClient(_spec(), max_attempts=2, base_delay_s=0.0)
    with pytest.raises(LLMError, match="no local model server"):
        client.complete_json(_request())
    assert len(attempts) == 2

    monkeypatch.setattr(local_client_module, "post_json", lambda url, payload, **_: {"choices": []})
    with pytest.raises(LLMError, match="no choices"):
        LocalClient(_spec(), max_attempts=1).complete_json(_request())


# --------------------------------------------------------------------------- #
# The local embedding space
# --------------------------------------------------------------------------- #


def _fake_embeddings(dim: int, calls: list[int] | None = None) -> Any:
    def fake_post(url: str, payload: dict[str, Any], **_: Any) -> dict[str, Any]:
        texts = payload["input"]
        if calls is not None:
            calls.append(len(texts))
        # Unnormalised on purpose, and returned out of order: the service must fix both.
        data = [
            {"index": i, "embedding": list(lexical_vector(t, dim) * 3.0 + 0.01)}
            for i, t in enumerate(texts)
        ]
        return {"data": list(reversed(data))}

    return fake_post


def test_the_local_space_needs_a_model_and_names_itself_by_model_and_dim(
    no_local_env: None,
) -> None:
    with pytest.raises(ValueError, match="needs a model"):
        EmbeddingService(EmbeddingSpaceConfig(mode="local", dim=768))
    service = EmbeddingService(EmbeddingSpaceConfig(mode="local", model="embeddinggemma", dim=768))
    assert service.space_id == "local-embeddinggemma-768"
    assert service.model == "embeddinggemma"


def test_local_vectors_are_normalised_ordered_and_sent_in_batches(
    monkeypatch: pytest.MonkeyPatch, no_local_env: None
) -> None:
    calls: list[int] = []
    monkeypatch.setattr(endpoint, "post_json", _fake_embeddings(64, calls))
    service = EmbeddingService(EmbeddingSpaceConfig(mode="local", model="m", dim=64))
    texts = [f"text number {i}" for i in range(LOCAL_BATCH_SIZE * 2 + 3)]
    vectors = service.embed(texts)
    assert vectors.shape == (len(texts), 64)
    assert np.allclose(np.linalg.norm(vectors, axis=1), 1.0)
    assert calls == [LOCAL_BATCH_SIZE, LOCAL_BATCH_SIZE, 3]
    expected = lexical_vector(texts[5], 64) * 3.0 + 0.01
    assert np.allclose(vectors[5], expected / np.linalg.norm(expected))
    service.embed(texts[:10])
    assert calls == [LOCAL_BATCH_SIZE, LOCAL_BATCH_SIZE, 3], "memoised strings are free"


def test_a_local_space_refuses_a_wrong_dimension_or_a_short_reply(
    monkeypatch: pytest.MonkeyPatch, no_local_env: None
) -> None:
    monkeypatch.setattr(endpoint, "post_json", _fake_embeddings(32))
    with pytest.raises(ValueError, match="expects dim 64"):
        EmbeddingService(EmbeddingSpaceConfig(mode="local", model="m", dim=64)).embed(["a"])
    monkeypatch.setattr(endpoint, "post_json", lambda url, payload, **_: {"data": []})
    with pytest.raises(endpoint.LocalEndpointError, match="0 embeddings for 1"):
        EmbeddingService(EmbeddingSpaceConfig(mode="local", model="m", dim=64)).embed(["a"])


# --------------------------------------------------------------------------- #
# Coder diversity, profiles and the pre-flight check
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("model", "family"),
    [
        ("qwen3.5:9b", "qwen"),
        ("qwen3-embedding:0.6b", "qwen"),
        ("gemma4:12b", "gemma"),
        ("gpt-oss:20b", "gpt"),
        ("hf.co/someone/Llama-3.1-8B-GGUF", "llama"),
        ("7b-model", "7b-model"),
    ],
)
def test_model_family_is_the_makers_name(model: str, family: str) -> None:
    assert model_family(model) == family


def _registry(a: ModelSpec, b: ModelSpec) -> ModelRegistry:
    return ModelRegistry(
        coder_a=a, coder_b=b, judge=_spec("gpt-oss:20b", "judge"),
        refactorer=_spec("gpt-oss:20b", "refactorer"),
    )


def test_two_local_coders_must_come_from_different_families() -> None:
    assert coders_are_distinct(_registry(_spec("qwen3.5:9b"), _spec("gemma4:12b", "coder_b")))
    assert not coders_are_distinct(_registry(_spec("qwen3.5:9b"), _spec("qwen3:8b", "coder_b")))
    hosted = ModelSpec(provider="openai", model="gpt-4o-mini", role="coder_b")
    assert coders_are_distinct(_registry(_spec("qwen3.5:9b"), hosted))


def _write_profile(path: Path, **overrides: Any) -> Path:
    profile: dict[str, Any] = {
        "models": {
            "coder_a": {"provider": "local", "model": "qwen3.5:9b"},
            "coder_b": {"provider": "local", "model": "gemma4:12b"},
            "judge": {"provider": "local", "model": "gpt-oss:20b"},
            "refactorer": {"provider": "local", "model": "gpt-oss:20b", "max_output_tokens": 8192},
        },
        "embedding": {"mode": "local", "model": "qwen3-embedding:0.6b", "dim": 16},
    }
    profile.update(overrides)
    path.write_text(json.dumps(profile))
    return path


def test_a_profile_fills_each_role_and_carries_the_embedding_space(tmp_path: Path) -> None:
    models, embedding = load_profile(_write_profile(tmp_path / "p.json"))
    assert models.coder_b.role == "coder_b" and models.coder_b.model == "gemma4:12b"
    assert models.refactorer.max_output_tokens == 8192
    assert models.judge.cost_usd(10**6, 10**6) == 0.0
    assert embedding == EmbeddingSpaceConfig(
        space_id="local-qwen3-embedding:0.6b-16", mode="local", model="qwen3-embedding:0.6b", dim=16
    )
    models, embedding = load_profile(_write_profile(tmp_path / "q.json", embedding=None))
    assert embedding is None


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"models": {"coder_a": {"provider": "local", "model": "x"}}}, "exactly the roles"),
        (
            {"models": {r: {"provider": "local"} for r in ("coder_a", "coder_b", "judge", "refactorer")}},
            "needs a provider and a model",
        ),
        (
            {"models": {r: {"provider": "local", "model": "x", "colour": 1}
                        for r in ("coder_a", "coder_b", "judge", "refactorer")}},
            "unknown field",
        ),
        (
            {"models": {r: {"provider": "kimi", "model": "x"}
                        for r in ("coder_a", "coder_b", "judge", "refactorer")}},
            "names provider 'kimi'",
        ),
        ({"embedding": ["local"]}, "must be an object"),
        ({"embedding": {"mode": "local", "size": 3}}, "unknown field"),
        ({"embedding": {"mode": "local", "dim": 8}}, "needs a model"),
    ],
)
def test_a_malformed_profile_is_refused_with_the_reason(
    tmp_path: Path, override: dict[str, Any], message: str
) -> None:
    with pytest.raises(CliError, match=message):
        load_profile(_write_profile(tmp_path / "bad.json", **override))


def test_an_unreadable_profile_is_refused(tmp_path: Path) -> None:
    (tmp_path / "broken.json").write_text("{not json")
    with pytest.raises(CliError, match="cannot read profile"):
        load_profile(tmp_path / "broken.json")


def test_the_preflight_check_is_a_no_op_when_nothing_is_local() -> None:
    check_local_models(RunConfig())


def test_the_preflight_check_names_every_missing_model(
    monkeypatch: pytest.MonkeyPatch, no_local_env: None, tmp_path: Path
) -> None:
    models, embedding = load_profile(_write_profile(tmp_path / "p.json"))
    assert embedding is not None
    config = RunConfig(offline=False, models=models, embedding=embedding)
    monkeypatch.setattr(
        endpoint, "get_json", lambda url, timeout=5.0: {"data": [{"id": "qwen3.5:9b"}]}
    )
    with pytest.raises(CliError, match="ollama pull gemma4:12b"):
        check_local_models(config)


# --------------------------------------------------------------------------- #
# The CLI, end to end, against a fake local server
# --------------------------------------------------------------------------- #


@pytest.fixture
def corpus_json(tmp_path: Path) -> Path:
    path = tmp_path / "corpus.json"
    write_corpus_json(synthetic_corpus(), path)
    return path


def test_a_profile_without_live_is_a_usage_error(
    tmp_path: Path, corpus_json: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    profile = _write_profile(tmp_path / "p.json")
    code = main(["run", "--corpus", str(corpus_json), "--profile", str(profile),
                 "--out", str(tmp_path / "out")])
    assert code == EXIT_USAGE
    assert "add --live" in capsys.readouterr().err


def test_a_local_run_with_no_server_fails_before_it_writes_anything(
    tmp_path: Path, corpus_json: Path, capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch, no_local_env: None,
) -> None:
    def down(url: str, timeout: float = 5.0) -> Any:
        raise endpoint.LocalEndpointError("no local model server; start one with `ollama serve`")

    monkeypatch.setattr(endpoint, "get_json", down)
    profile = _write_profile(tmp_path / "p.json")
    code = main(["run", "--corpus", str(corpus_json), "--live", "--profile", str(profile),
                 "--out", str(tmp_path / "out"), "--no-cache"])
    assert code == EXIT_INPUT
    assert "ollama serve" in capsys.readouterr().err
    assert not (tmp_path / "out" / "codebook.json").exists()


def test_a_local_run_completes_through_the_real_transport_and_records_what_it_did(
    tmp_path: Path, corpus_json: Path, monkeypatch: pytest.MonkeyPatch, no_local_env: None,
) -> None:
    """A model that answers every call with prose: every call fails safe, nothing is
    invented, the run still completes, and `llm_calls` says so — provider, model, zero
    cost. This is the smallest honest end-to-end check of the local path."""
    listing = {"data": [{"id": m} for m in LOCAL_MODELS]}
    monkeypatch.setattr(endpoint, "get_json", lambda url, timeout=5.0: listing)
    monkeypatch.setattr(endpoint, "post_json", _fake_embeddings(16))
    monkeypatch.setattr(
        local_client_module, "post_json",
        lambda url, payload, **_: _chat_reply("I would rather describe it in words."),
    )
    profile = _write_profile(tmp_path / "p.json")
    out = tmp_path / "out"
    code = main(["run", "--corpus", str(corpus_json), "--live", "--profile", str(profile),
                 "--out", str(out), "--run-id", "localsmoke", "--no-cache"])
    assert code == EXIT_OK
    config = json.loads((out / "run.json").read_text())["config"]
    assert config["models"]["coder_b"]["provider"] == "local"
    assert config["embedding"]["space_id"] == "local-qwen3-embedding:0.6b-16"
    assert json.loads((out / "stats.json").read_text())["space_id"] == "local-qwen3-embedding:0.6b-16"
    with sqlite3.connect(out / "gaf.sqlite") as db:
        rows = db.execute(
            "SELECT provider, COUNT(*), SUM(fail_safe), SUM(cost_usd) FROM llm_calls "
            "WHERE run_id = 'localsmoke' GROUP BY provider"
        ).fetchall()
    assert len(rows) == 1
    provider, n_calls, n_fail_safe, cost = rows[0]
    assert provider == "local" and n_calls > 0
    assert n_fail_safe == n_calls and cost == 0.0


def test_every_shipped_profile_loads_and_keeps_its_coders_distinct() -> None:
    profiles = sorted((Path(__file__).parent.parent / "profiles").glob("*.json"))
    assert profiles, "profiles/ ships at least one example"
    for path in profiles:
        models, _ = load_profile(path)
        assert coders_are_distinct(models), path.name
