"""A model served on this machine. Live path only — never constructed offline.

`LocalClient` is `OpenAIClient` with a different transport: the same Chat Completions
request in JSON-object mode, the same defensive parse, the same fail-safe on a malformed
reply and the same `LLMError` on a transport failure — sent to the server that
`gaf.local_endpoint.local_base_url` names (Ollama by default) with the standard library
instead of an SDK. So a local run exercises exactly the parse-and-fail-safe path a paid
run does, which is the point of running one before a paid run is approved (ADR-0049).

Two things differ from a hosted model and are handled here:

* **Reasoning models think out loud.** Qwen 3.x, gpt-oss, DeepSeek-R1 and Gemma 4 can
  emit a ``<think>…</think>`` block before the answer, or return it in a separate
  ``reasoning`` field. A thinking block routinely contains braces, which would make
  `parse_json_object`'s outermost-``{…}`` rescue pick up the wrong span, so the block is
  removed before parsing. The request also asks the server not to think
  (``reasoning_effort: "none"``); servers that do not know the field ignore it.
* **Nothing is billed.** A `ModelSpec` bound to ``"local"`` carries no price, so
  `cost_usd` is 0.0 by construction, and the run report says so rather than inventing a
  rate. Token counts are still recorded: they are what a hosted run of the same prompts
  would be billed on.

The request-and-parse body is `chat_completions_transport`, which the hosted
``"openai_compatible"`` provider (`gaf.llm.compat_client`, ADR-0052) shares: one
transport, two destinations, and only the destination decides whether text leaves the
machine.

Validation principle: **reliability** — a local reply goes through the same whitelist
and fail-safe as any other; a model that cannot follow the output schema shows up as
``fail_safe`` rows in ``llm_calls``, which is itself a finding about that model.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from typing import Any

from gaf.config import ModelSpec
from gaf.llm.base import LLMError, LLMRequest
from gaf.llm.openai_client import OpenAIClient, Transport
from gaf.local_endpoint import EndpointError, local_base_url, post_json

__all__ = ["INSTALL_HINT", "LocalClient", "chat_completions_transport", "strip_thinking"]

INSTALL_HINT = "ollama serve  (then: ollama pull <model>)"

_THINK_RE = re.compile(r"<think(?:ing)?>.*?</think(?:ing)?>", re.DOTALL | re.IGNORECASE)
#: An opening tag the model never closed (it ran out of tokens while thinking).
_OPEN_THINK_RE = re.compile(r"<think(?:ing)?>.*\Z", re.DOTALL | re.IGNORECASE)


def strip_thinking(text: str) -> str:
    """Remove ``<think>`` blocks, and an unclosed one running to the end of the reply."""
    return _OPEN_THINK_RE.sub("", _THINK_RE.sub("", text)).strip()


def chat_completions_transport(
    spec: ModelSpec,
    *,
    url: str,
    seed: int,
    post: Callable[[str, dict[str, Any]], Any],
    extra: Mapping[str, Any] | None = None,
) -> Transport:
    """A `Transport` that POSTs one Chat Completions request in JSON-object mode to `url`.

    `post` sends the body and returns the decoded reply (it raises `EndpointError` when
    it cannot); `extra` adds server-specific fields to the body. The reply's ``<think>``
    block is removed before anything parses it. A refusing or unreachable server is a
    transport failure (`LLMError`: retried, then raised); a reply with no choices is too.
    """
    fixed = dict(extra or {})

    def send(request: LLMRequest) -> tuple[str, int, int]:
        payload: dict[str, Any] = {
            "model": spec.model,
            "messages": [
                {"role": "system", "content": request.system},
                {"role": "user", "content": request.user},
            ],
            "response_format": {"type": "json_object"},
            "temperature": (
                spec.temperature if request.temperature is None else request.temperature
            ),
            "max_tokens": request.max_output_tokens or spec.max_output_tokens,
            "seed": seed,
            "stream": False,
            **fixed,
        }
        try:
            reply = post(url, payload)
        except EndpointError as exc:
            # A dead or refusing server is a transport failure: retried, then raised.
            raise LLMError(str(exc)) from exc
        try:
            message = reply["choices"][0]["message"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError(f"{url} returned no choices: {str(reply)[:200]!r}") from exc
        text = strip_thinking(str(message.get("content") or ""))
        usage = reply.get("usage") or {}
        return (
            text,
            int(usage.get("prompt_tokens") or 0),
            int(usage.get("completion_tokens") or 0),
        )

    return send


class LocalClient(OpenAIClient):
    """One locally served model, bound to one `ModelSpec` whose provider is ``"local"``."""

    def _build_transport(self, api_key: str | None) -> Transport:
        return chat_completions_transport(
            self.spec,
            url=f"{local_base_url()}/chat/completions",
            seed=self._seed,
            post=post_json,
            extra={"reasoning_effort": "none"},
        )
