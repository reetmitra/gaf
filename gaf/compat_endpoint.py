"""Where a hosted OpenAI-compatible model lives, and the one HTTP call made to it.

The ``"openai_compatible"`` provider (ADR-0052) is a model served by a third party over
the same Chat Completions protocol a local server speaks — Alibaba Cloud Model Studio's
compatible mode for Qwen, or OpenRouter. It is a separate provider from ``"local"``
rather than ``"local"`` with ``GAF_LOCAL_ALLOW_REMOTE=1``, because "local" is a privacy
claim (ADR-0049): a run that sends respondent text to a hosted endpoint must say so in
its config echo, under its own name, with its own variables.

So everything here is explicit and nothing has a default that could send text anywhere
by accident:

* ``GAF_COMPAT_BASE_URL`` — required, and ``https`` is required: respondent text never
  crosses the network in the clear. The two hosts the RUNBOOK documents are
  `DASHSCOPE_INTL_BASE_URL` (preferred: Singapore, to be verified by the user) and
  `OPENROUTER_BASE_URL` (fallback).
* ``GAF_COMPAT_API_KEY`` — required; sent as a bearer token.
* ``GAF_COMPAT_THINKING_OFF`` — on unless set to ``0``. Asks the host to switch a hybrid
  reasoning model's thinking off with ``"enable_thinking": false``, the field
  DashScope's compatible mode reads (and JSON-object mode needs thinking off there). A
  host that does not know the field ignores it; ``0`` drops it for a host that rejects
  unknown fields instead.

Standard library only, through `gaf.local_endpoint.read_json`: no SDK and no extra.

Validation principle: **transparency** — where respondent text goes is decided by two
variables a reader can see, and refused when either is missing.
"""

from __future__ import annotations

import os
import urllib.parse
from typing import Any

from gaf.local_endpoint import EndpointError, json_post_request, read_json

__all__ = [
    "API_KEY_ENV",
    "BASE_URL_ENV",
    "DASHSCOPE_INTL_BASE_URL",
    "OPENROUTER_BASE_URL",
    "THINKING_OFF_ENV",
    "CompatEndpointError",
    "compat_api_key",
    "compat_base_url",
    "post_json",
    "thinking_off",
]

BASE_URL_ENV = "GAF_COMPAT_BASE_URL"
API_KEY_ENV = "GAF_COMPAT_API_KEY"
THINKING_OFF_ENV = "GAF_COMPAT_THINKING_OFF"

#: Alibaba Cloud Model Studio, international (Singapore) region, OpenAI-compatible mode.
DASHSCOPE_INTL_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
#: OpenRouter's OpenAI-compatible root. Model ids there carry a maker prefix (``qwen/...``).
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

#: A hosted frontier model can think for minutes over a long prompt; the timeout exists
#: to catch a dead connection, not a slow answer.
_REQUEST_TIMEOUT_S = 600.0


class CompatEndpointError(EndpointError):
    """The hosted endpoint is not configured, unreachable, or answered unusably."""


def compat_base_url(env: dict[str, str] | None = None) -> str:
    """The hosted endpoint's base URL, from ``GAF_COMPAT_BASE_URL``. Required, https only."""
    source = os.environ if env is None else env
    raw = (source.get(BASE_URL_ENV) or "").strip().rstrip("/")
    if not raw:
        raise CompatEndpointError(
            f"{BASE_URL_ENV} is not set. Provider 'openai_compatible' sends respondent text "
            f"to the host it names, so there is no default; e.g. {DASHSCOPE_INTL_BASE_URL} "
            "(see docs/RUNBOOK.md)."
        )
    parsed = urllib.parse.urlparse(raw)
    if parsed.scheme != "https" or not parsed.hostname:
        raise CompatEndpointError(
            f"{BASE_URL_ENV}={raw!r} is not an https URL; respondent text is only sent to a "
            "hosted endpoint over TLS."
        )
    return raw


def compat_api_key(env: dict[str, str] | None = None) -> str:
    """The bearer token from ``GAF_COMPAT_API_KEY``. Required."""
    source = os.environ if env is None else env
    key = (source.get(API_KEY_ENV) or "").strip()
    if not key:
        raise CompatEndpointError(
            f"{API_KEY_ENV} is not set; the hosted endpoint needs its API key "
            "(add it to .env, see .env.example)."
        )
    return key


def thinking_off(env: dict[str, str] | None = None) -> bool:
    """Whether to send ``"enable_thinking": false``. On unless ``GAF_COMPAT_THINKING_OFF=0``."""
    source = os.environ if env is None else env
    return (source.get(THINKING_OFF_ENV) or "1").strip() != "0"


def _unreachable(url: str, exc: Exception) -> str:
    return (
        f"the hosted endpoint at {url} could not be reached ({exc}). Check {BASE_URL_ENV} "
        "and the network."
    )


def post_json(
    url: str, payload: dict[str, Any], *, api_key: str, timeout: float = _REQUEST_TIMEOUT_S
) -> Any:
    """POST `payload` as JSON to `url` with `api_key` as the bearer token."""
    request = json_post_request(url, payload, {"Authorization": f"Bearer {api_key}"})
    return read_json(request, timeout, error=CompatEndpointError, unreachable=_unreachable)
