"""A hosted model behind an OpenAI-compatible endpoint. Live path only.

`OpenAICompatibleClient` is the ``"openai_compatible"`` provider (ADR-0052): the same
Chat Completions request, JSON-object mode, ``<think>`` stripping, defensive parse and
fail-safe as `gaf.llm.local_client.LocalClient` — the transport is literally shared
(`chat_completions_transport`) — sent instead to the hosted endpoint that
`gaf.compat_endpoint` names, with that endpoint's key. It exists for the hosted Qwen
coder the PI chose, reached through Alibaba Cloud Model Studio (or OpenRouter), and it is
a provider of its own so that a run sending respondent text to a third party is never
labelled ``"local"``.

Two differences from the local client, both in the body:

* ``"enable_thinking": false`` (unless ``GAF_COMPAT_THINKING_OFF=0``): DashScope's
  switch for a hybrid Qwen model's reasoning, which its JSON-object mode requires off.
  Any ``<think>`` block that arrives anyway is still removed before parsing.
* no ``reasoning_effort: "none"``: that is Ollama's field, and a hosted router may map
  it onto something else.

The model id is the host's: ``qwen3.8-max`` on DashScope, ``qwen/...`` on OpenRouter.
It is recorded in every ``llm_calls`` row and in the run's config echo.

Validation principle: **transparency** — the provider name in the audit log says that
this text left the machine, and for which host the run was configured.
"""

from __future__ import annotations

from typing import Any

from gaf.compat_endpoint import (
    compat_api_key,
    compat_base_url,
    post_json,
    thinking_off,
)
from gaf.llm.local_client import chat_completions_transport
from gaf.llm.openai_client import OpenAIClient, Transport

__all__ = ["INSTALL_HINT", "OpenAICompatibleClient"]

#: Nothing to install: the transport is the standard library.
INSTALL_HINT = ""


class OpenAICompatibleClient(OpenAIClient):
    """One hosted model, bound to a `ModelSpec` whose provider is ``"openai_compatible"``.

    Construction reads and checks ``GAF_COMPAT_BASE_URL`` and ``GAF_COMPAT_API_KEY``
    (an explicit `api_key` wins over the variable), so a missing variable stops the run
    before anything is sent.
    """

    def _build_transport(self, api_key: str | None) -> Transport:
        base = compat_base_url()
        key = api_key or compat_api_key()
        extra: dict[str, Any] = {"enable_thinking": False} if thinking_off() else {}

        def post(url: str, payload: dict[str, Any]) -> Any:
            return post_json(url, payload, api_key=key)

        return chat_completions_transport(
            self.spec,
            url=f"{base}/chat/completions",
            seed=self._seed,
            post=post,
            extra=extra,
        )
