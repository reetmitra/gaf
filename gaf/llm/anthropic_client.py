"""The Anthropic client. Live path only — never imported, constructed or run offline.

Implements `gaf.llm.base.LLMClient` over the Messages API. This is the provider the
default registry binds to the **Judge** and the **Refactorer**: the third provider that
neither coder uses, so that a disputed coding is settled by a model with no stake in
either reading, and the frontier refactor proposal is not the coders marking their own
work.

The Messages API has no response-format flag, so JSON is asked for in the prompt and
recovered by `parse_json_object`, which strips a markdown fence and, failing that,
takes the outermost ``{...}`` span — rescuing the "Here is the JSON you asked for:"
preamble that a chat-tuned model produces regardless of instruction. A malformed reply
degrades to `fail_safe_for(request.task)` with `LLMResult.fail_safe = True` and never
raises; a **transport** failure raises `LLMError`, because a silent outage is worse
than a halted run.

The `anthropic` package is an optional extra (`uv sync --extra anthropic`) and is not
installed by default. It is imported lazily via `importlib` — see
`gaf.llm.openai_client` for why `importlib` rather than a `# type: ignore` — and a
missing SDK is reported at construction time with the command that fixes it.

Validation principle: **epistemic diversity** — the judge is a third provider by
construction, so an escalation is arbitration rather than a second opinion from an
interested party.
"""

from __future__ import annotations

import importlib
import time
from collections.abc import Callable
from typing import Any

from gaf.checks.contracts import FIT_VERDICTS
from gaf.config import ModelSpec
from gaf.llm.base import (
    LLMRequest,
    LLMResult,
    MalformedReplyError,
    TaskType,
    fail_safe_for,
    parse_json_object,
    retry_with_jitter,
    strip_fences,
    validate_enum,
)

__all__ = ["INSTALL_HINT", "AnthropicClient", "MissingProviderSDKError", "Transport"]

INSTALL_HINT = "uv sync --extra anthropic"

#: ``(reply_text, input_tokens, output_tokens)``. See `gaf.llm.openai_client.Transport`.
Transport = Callable[[LLMRequest], tuple[str, int, int]]

_ENUM_FIELDS: dict[TaskType, tuple[str, tuple[str, ...], str]] = {
    TaskType.JUDGE_FIT: ("verdict", FIT_VERDICTS, "APPLIES"),
    TaskType.JUDGE_DISPUTE: ("verdict", ("KEEP", "DROP"), "KEEP"),
    TaskType.JUDGE_ROUTE: ("route", ("MERGE", "CREATE"), "CREATE"),
}

_LIST_FIELDS: dict[TaskType, str] = {
    TaskType.CODE: "candidates",
    TaskType.REFACTOR: "operations",
}


class MissingProviderSDKError(RuntimeError):
    """The optional `anthropic` extra is not installed."""


def _coerce_payload(task: TaskType, data: dict[str, Any]) -> dict[str, Any]:
    """Whitelist the enum field and require the list field for `task`."""
    out = dict(data)
    enum_field = _ENUM_FIELDS.get(task)
    if enum_field is not None:
        field, allowed, default = enum_field
        out[field] = validate_enum(out.get(field), allowed, default)
    list_field = _LIST_FIELDS.get(task)
    if list_field is not None and not isinstance(out.get(list_field), list):
        raise MalformedReplyError(f"expected a JSON list under {list_field!r}")
    return out


class AnthropicClient:
    """One Anthropic model, bound to one `ModelSpec`."""

    def __init__(
        self,
        spec: ModelSpec,
        *,
        api_key: str | None = None,
        transport: Transport | None = None,
        max_attempts: int = 3,
        base_delay_s: float = 0.5,
        seed: int = 0,
    ) -> None:
        self.spec = spec
        self._max_attempts = max_attempts
        self._base_delay_s = base_delay_s
        self._seed = seed
        self._transport: Transport = transport or self._build_transport(api_key)

    def _build_transport(self, api_key: str | None) -> Transport:
        try:
            module = importlib.import_module("anthropic")
        except ImportError as exc:
            raise MissingProviderSDKError(
                "the 'anthropic' package is required for provider 'anthropic' and is "
                f"not installed; run `{INSTALL_HINT}`"
            ) from exc
        client = module.Anthropic(api_key=api_key) if api_key else module.Anthropic()

        def send(request: LLMRequest) -> tuple[str, int, int]:
            message = client.messages.create(
                model=self.spec.model,
                system=request.system,
                messages=[{"role": "user", "content": request.user}],
                temperature=(
                    self.spec.temperature if request.temperature is None else request.temperature
                ),
                max_tokens=request.max_output_tokens or self.spec.max_output_tokens,
            )
            text = "".join(
                block.text
                for block in message.content
                if getattr(block, "type", "") == "text"
            )
            usage = getattr(message, "usage", None)
            return (
                text,
                int(getattr(usage, "input_tokens", 0) or 0),
                int(getattr(usage, "output_tokens", 0) or 0),
            )

        return send

    def complete_json(self, request: LLMRequest) -> LLMResult:
        started = time.perf_counter()
        (text, input_tokens, output_tokens), attempts = retry_with_jitter(
            lambda: self._transport(request),
            attempts=self._max_attempts,
            base_delay_s=self._base_delay_s,
            seed=self._seed,
        )
        try:
            data = _coerce_payload(request.task, parse_json_object(strip_fences(text)))
            fail_safe = False
        except MalformedReplyError:
            data = fail_safe_for(request.task)
            fail_safe = True
        return LLMResult(
            data=data,
            task=request.task,
            provider=self.spec.provider,
            model=self.spec.model,
            prompt_version=request.prompt_version,
            raw_text=text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=self.spec.cost_usd(input_tokens, output_tokens),
            latency_ms=(time.perf_counter() - started) * 1000.0,
            cache_hit=False,
            fail_safe=fail_safe,
            attempts=attempts,
        )
