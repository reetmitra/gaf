"""The Anthropic client. Live path only — never imported, constructed or run offline.

Implements `gaf.llm.base.LLMClient` over the Messages API. In the default registry this
is the provider bound to the **Judge** and the **Refactorer**; a profile may also bind
it to a coder (``profiles/opus-qwen.json`` puts Opus 5.5 on coder A, the judge and the
refactorer, with a different maker on coder B).

The Messages API has no response-format flag in the shape this package uses, so JSON is
asked for in the prompt and recovered by `parse_json_object`, which strips a markdown
fence and, failing that, takes the outermost ``{...}`` span — rescuing the "Here is the
JSON you asked for:" preamble that a chat-tuned model produces regardless of
instruction. A malformed reply degrades to `fail_safe_for(request.task)` with
`LLMResult.fail_safe = True` and never raises; a **transport** failure raises
`LLMError`, because a silent outage is worse than a halted run.

**The 5-series request shape (ADR-0051).** On Opus 5.5 — and Opus 5, Opus 4.7/4.8,
Sonnet 5/5.5 and Fable 5/5.1 — thinking is always on, a sampling parameter such as
``temperature`` is an HTTP 400, and the depth of thinking is set by
``output_config.effort``. So:

* sampling parameters are sent only to the older lines that accept them
  (`accepts_sampling_params`, an explicit rule on the model id), and through
  ``extra_body`` because the 1.x SDK no longer has a ``temperature`` argument;
* ``ModelSpec.effort`` is sent as ``output_config.effort`` when it is set, and nothing
  is sent when it is not;
* only ``text`` blocks are read — a reply now opens with ``thinking`` blocks;
* a ``refusal`` or ``max_tokens`` stop is not an answer to a JSON task: it becomes the
  task's fail-safe default, recorded on the result (``fail_safe`` in ``llm_calls``,
  ``_stop_reason`` in the data, and the judge's or refactorer's ``reasoning``), and is
  never retried inside the call — a refusal is a property of the input and a retry
  bills the same thinking again. Fail-safe results are never cached, so a re-run asks
  again. The server-side ``fallbacks`` beta is deliberately not used: a silent switch
  to another model mid-run would change who coded what;
* every request streams and reads the final message, so a long refactor at high effort
  cannot hit the SDK's ten-minute non-streaming guard. Usage is as before: output
  tokens include the thinking, which is billed as output.

The `anthropic` package is an optional extra (`uv sync --extra anthropic`, 1.x) and is
not installed by default. It is imported lazily via `importlib` — see
`gaf.llm.openai_client` for why `importlib` rather than a `# type: ignore` — and a
missing SDK is reported at construction time with the command that fixes it.

Validation principle: **reliability** — a refusal or a truncated reply cannot become a
coding, a verdict or an edit; it becomes the non-destructive default, visibly.
"""

from __future__ import annotations

import importlib
import re
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

__all__ = [
    "INCOMPLETE_STOPS",
    "INSTALL_HINT",
    "AnthropicClient",
    "IncompleteReplyError",
    "MissingProviderSDKError",
    "Transport",
    "accepts_sampling_params",
    "read_message",
]

INSTALL_HINT = "uv sync --extra anthropic"

#: ``(reply_text, input_tokens, output_tokens)``. See `gaf.llm.openai_client.Transport`.
#: A transport that stops early raises `IncompleteReplyError` instead of returning.
Transport = Callable[[LLMRequest], tuple[str, int, int]]

#: Stop reasons after which the text is not the answer the task asked for.
INCOMPLETE_STOPS = frozenset({"refusal", "max_tokens"})

#: The Anthropic lines that still take ``temperature``: the Claude 2 and 3 families and
#: Claude 4.0 to 4.6 (Opus, Sonnet, Haiku; bare or with a date suffix). Opus 4.7 and
#: later, Sonnet 5 and later, Fable and Mythos reject sampling parameters with a 400, and
#: so — deliberately — does any id this rule does not recognise: a new line is far more
#: likely to have dropped them than to have brought them back, and an omitted
#: temperature fails nothing.
_SAMPLING_MODEL_RE = re.compile(
    r"^claude-(?:[23]-|instant|(?:opus|sonnet|haiku)-4(?:-[0-6])?(?:-\d{8})?$)"
)

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


class IncompleteReplyError(RuntimeError):
    """The model stopped before answering: a ``refusal`` or a ``max_tokens`` stop.

    Carries the tokens the call was billed for, so a reply that is not used is still
    accounted for. Caught inside `AnthropicClient.complete_json`, never by the retry.
    """

    def __init__(
        self,
        stop_reason: str,
        *,
        text: str = "",
        input_tokens: int = 0,
        output_tokens: int = 0,
        category: str | None = None,
    ) -> None:
        self.stop_reason = stop_reason
        self.text = text
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.category = category
        super().__init__(self.describe())

    def describe(self) -> str:
        """``"refusal (bio)"``, ``"refusal"`` or ``"max_tokens"``."""
        return f"{self.stop_reason} ({self.category})" if self.category else self.stop_reason


def accepts_sampling_params(model: str) -> bool:
    """Whether the Messages API takes ``temperature`` for `model` (ADR-0051).

    True for the Claude 2 and 3 families and Claude 4.0 to 4.6; False for Opus 4.7 and
    later, Sonnet 5 and later, Fable, Mythos and any id the rule does not recognise.
    """
    return bool(_SAMPLING_MODEL_RE.match(model))


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


def _stopped_early(task: TaskType, stop: IncompleteReplyError) -> dict[str, Any]:
    """The fail-safe default for `task`, marked with why the model stopped."""
    data = fail_safe_for(task)
    data["_stop_reason"] = stop.stop_reason
    if stop.category:
        data["_stop_category"] = stop.category
    if "reasoning" in data:
        # The judge's and the refactorer's reasoning reaches the store; say why.
        data["reasoning"] = f"fail-safe: the model stopped with {stop.describe()}"
    return data


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

    def request_params(self, request: LLMRequest) -> dict[str, Any]:
        """The keyword arguments of ``client.messages.stream`` for `request`.

        Public so the request shape can be checked without an SDK or a network.
        """
        spec = self.spec
        params: dict[str, Any] = {
            "model": spec.model,
            "max_tokens": request.max_output_tokens or spec.max_output_tokens,
            "system": request.system,
            "messages": [{"role": "user", "content": request.user}],
        }
        if spec.effort is not None:
            params["output_config"] = {"effort": spec.effort}
        if accepts_sampling_params(spec.model):
            # The 1.x SDK has no `temperature` argument; the older lines still take the
            # field, so it travels in the body as it always did.
            temperature = spec.temperature if request.temperature is None else request.temperature
            params["extra_body"] = {"temperature": temperature}
        return params

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
            with client.messages.stream(**self.request_params(request)) as stream:
                message = stream.get_final_message()
            return read_message(message)

        return send

    def complete_json(self, request: LLMRequest) -> LLMResult:
        started = time.perf_counter()

        def attempt() -> tuple[str, int, int, IncompleteReplyError | None]:
            try:
                text, input_tokens, output_tokens = self._transport(request)
            except IncompleteReplyError as stop:
                # Not a transport failure: returned, so the retry does not bill it again.
                return stop.text, stop.input_tokens, stop.output_tokens, stop
            return text, input_tokens, output_tokens, None

        (text, input_tokens, output_tokens, stop), attempts = retry_with_jitter(
            attempt,
            attempts=self._max_attempts,
            base_delay_s=self._base_delay_s,
            seed=self._seed,
        )
        if stop is not None:
            data = _stopped_early(request.task, stop)
            fail_safe = True
        else:
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


def read_message(message: Any) -> tuple[str, int, int]:
    """``(text, input_tokens, output_tokens)`` from a Messages API reply.

    Joins the ``text`` blocks only: thinking blocks come first on the 5-series and are
    not the answer. Raises `IncompleteReplyError` on a ``refusal`` or ``max_tokens``
    stop, carrying the billed tokens. Output tokens include thinking.
    """
    text = "".join(
        str(getattr(block, "text", "") or "")
        for block in getattr(message, "content", None) or []
        if getattr(block, "type", "") == "text"
    )
    usage = getattr(message, "usage", None)
    input_tokens = int(getattr(usage, "input_tokens", 0) or 0)
    output_tokens = int(getattr(usage, "output_tokens", 0) or 0)
    stop_reason = getattr(message, "stop_reason", None)
    if stop_reason in INCOMPLETE_STOPS:
        details = getattr(message, "stop_details", None)
        category = getattr(details, "category", None) if details is not None else None
        raise IncompleteReplyError(
            str(stop_reason),
            text=text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            category=str(category) if category else None,
        )
    return text, input_tokens, output_tokens
