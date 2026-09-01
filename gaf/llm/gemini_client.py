"""The Google Gemini client. Live path only — never imported, constructed or run offline.

Implements `gaf.llm.base.LLMClient` over `google-genai`, asking for
``response_mime_type="application/json"`` and still parsing defensively: a structured
output flag is a request, not a guarantee. A malformed reply degrades to
`fail_safe_for(request.task)` with `LLMResult.fail_safe = True` and never raises. A
**transport** failure does raise `LLMError`, because an outage that quietly produced
empty codings for a whole batch would be worse than a halted run.

Gemini exists in this project for a specific reason: `ModelRegistry` requires the two
coders to come from *different providers*, and that difference is simultaneously the
epistemic-diversity mechanism and the cost-control mechanism, since only disagreement
escalates to the frontier judge. A single-provider pipeline would lose both.

The `google-genai` package is an optional extra (`uv sync --extra gemini`) and is not
installed by default. It is imported lazily via `importlib` — see
`gaf.llm.openai_client` for why `importlib` rather than a `# type: ignore` — and a
missing SDK is reported at construction time with the command that fixes it.

Validation principle: **epistemic diversity** — a second provider reading the same
context is the only reason cross-coder agreement is evidence of anything.
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

__all__ = ["INSTALL_HINT", "GeminiClient", "MissingProviderSDKError", "Transport"]

INSTALL_HINT = "uv sync --extra gemini"

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
    """The optional `gemini` extra is not installed."""


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


class GeminiClient:
    """One Gemini model, bound to one `ModelSpec`."""

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
            module = importlib.import_module("google.genai")
        except ImportError as exc:
            raise MissingProviderSDKError(
                "the 'google-genai' package is required for provider 'gemini' and is "
                f"not installed; run `{INSTALL_HINT}`"
            ) from exc
        client = module.Client(api_key=api_key) if api_key else module.Client()

        def send(request: LLMRequest) -> tuple[str, int, int]:
            response = client.models.generate_content(
                model=self.spec.model,
                contents=request.user,
                config={
                    "system_instruction": request.system,
                    "response_mime_type": "application/json",
                    "temperature": (
                        self.spec.temperature
                        if request.temperature is None
                        else request.temperature
                    ),
                    "max_output_tokens": (
                        request.max_output_tokens or self.spec.max_output_tokens
                    ),
                },
            )
            usage = getattr(response, "usage_metadata", None)
            return (
                response.text or "",
                int(getattr(usage, "prompt_token_count", 0) or 0),
                int(getattr(usage, "candidates_token_count", 0) or 0),
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
