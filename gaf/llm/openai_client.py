"""The OpenAI client. Live path only — never imported, constructed or run offline.

Implements `gaf.llm.base.LLMClient` over the Chat Completions API in JSON-object mode,
and still parses defensively: a structured-output flag is a request, not a guarantee,
and `parse_json_object` has to survive a fenced reply, a leading apology and a trailing
explanation. A malformed reply degrades to `fail_safe_for(request.task)` with
`LLMResult.fail_safe = True` and never raises — the fail-safe defaults are the
non-destructive option for every task, so a bad reply costs a coding, not the data.

A **transport** failure is different and is allowed to raise `LLMError`: an outage that
silently produced empty codings for five hundred responses would be a far worse
outcome than a halted run. `LLMError` exists in `gaf.llm.base` for exactly that.

The `openai` package is an optional extra (`uv sync --extra openai`) and is not
installed by default. It is imported **lazily**, so importing this module costs nothing
and the offline path never touches it, and a missing SDK is reported at construction
time with the command that fixes it — not as an `ImportError` halfway through a paid
batch. The import goes through `importlib` rather than a top-level ``import openai``
guarded by ``# type: ignore[import-not-found]``: the project sets
``warn_unused_ignores = true``, so such an ignore would be required while the extra is
absent and would itself become a type error the moment anyone installed it. `importlib`
types the module as `Any` either way, so both configurations check cleanly with no
comment to maintain in two directions.

Validation principle: **transparency** — every call returns its provider, model, prompt
version, token counts, cost, latency and attempt count, so a run report can account for
it line by line.
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

__all__ = ["INSTALL_HINT", "MissingProviderSDKError", "OpenAIClient", "Transport"]

INSTALL_HINT = "uv sync --extra openai"

#: A transport turns one request into ``(reply_text, input_tokens, output_tokens)``.
#: The seam exists so the parse-and-fail-safe path can be exercised without an SDK,
#: a key or a network; the live transport is built lazily from the optional extra.
Transport = Callable[[LLMRequest], tuple[str, int, int]]

#: Enum-valued reply fields, by task. Mirrors the shape of `FAIL_SAFE_DEFAULTS`, which
#: `gaf.llm.base` does not export as whitelists.
_ENUM_FIELDS: dict[TaskType, tuple[str, tuple[str, ...], str]] = {
    TaskType.JUDGE_FIT: ("verdict", FIT_VERDICTS, "APPLIES"),
    TaskType.JUDGE_DISPUTE: ("verdict", ("KEEP", "DROP"), "KEEP"),
    TaskType.JUDGE_ROUTE: ("route", ("MERGE", "CREATE"), "CREATE"),
}

#: Reply fields that must be a list, or the reply is not usable.
_LIST_FIELDS: dict[TaskType, str] = {
    TaskType.CODE: "candidates",
    TaskType.REFACTOR: "operations",
}


class MissingProviderSDKError(RuntimeError):
    """The optional `openai` extra is not installed."""


def _coerce_payload(task: TaskType, data: dict[str, Any]) -> dict[str, Any]:
    """Whitelist the enum field and require the list field for `task`.

    A verdict outside the whitelist is not a verdict, so it becomes the non-destructive
    default. A missing or non-list `candidates`/`operations` is a malformed reply, which
    routes to the fail-safe rather than to a `TypeError` three stages later.
    """
    out = dict(data)
    enum_field = _ENUM_FIELDS.get(task)
    if enum_field is not None:
        field, allowed, default = enum_field
        out[field] = validate_enum(out.get(field), allowed, default)
    list_field = _LIST_FIELDS.get(task)
    if list_field is not None and not isinstance(out.get(list_field), list):
        raise MalformedReplyError(f"expected a JSON list under {list_field!r}")
    return out


class OpenAIClient:
    """One OpenAI model, bound to one `ModelSpec`."""

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
            module = importlib.import_module("openai")
        except ImportError as exc:
            raise MissingProviderSDKError(
                "the 'openai' package is required for provider 'openai' and is not "
                f"installed; run `{INSTALL_HINT}`"
            ) from exc
        client = module.OpenAI(api_key=api_key) if api_key else module.OpenAI()

        def send(request: LLMRequest) -> tuple[str, int, int]:
            response = client.chat.completions.create(
                model=self.spec.model,
                messages=[
                    {"role": "system", "content": request.system},
                    {"role": "user", "content": request.user},
                ],
                # Ask for JSON; still parse as though it had not been honoured.
                response_format={"type": "json_object"},
                temperature=(
                    self.spec.temperature if request.temperature is None else request.temperature
                ),
                max_tokens=request.max_output_tokens or self.spec.max_output_tokens,
            )
            text = response.choices[0].message.content or ""
            usage = getattr(response, "usage", None)
            return (
                text,
                int(getattr(usage, "prompt_tokens", 0) or 0),
                int(getattr(usage, "completion_tokens", 0) or 0),
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
