"""Where a model served on this machine lives, and the two HTTP calls made to it.

The ``"local"`` provider and the ``"local"`` embedding mode talk to an OpenAI-compatible
server on this machine — Ollama by default, but LM Studio, llama.cpp's ``llama-server``
and ``mlx_lm.server`` speak the same two endpoints (``/chat/completions`` and
``/embeddings``). Both go through this module, so there is one place that decides which
server is meant and one place that refuses a server that is not local (ADR-0049).

**"Local" is a privacy claim, so it is enforced, not assumed.** A run whose models are
local sends no respondent's words off the machine. That stops being true the moment the
base URL points somewhere else — a hosted Kimi or Qwen endpoint speaks the same protocol
— so a non-loopback host is refused unless ``GAF_LOCAL_ALLOW_REMOTE=1`` says, on purpose,
that this run may leave the machine. Sending the corpus to a new provider is the PI's
decision (the same one the live run waits on), never a side effect of an edited URL.

Standard library only: no SDK, no key and no extra to install, so ``--live`` with a
local profile works from a clean ``uv sync``. The HTTP reading itself (`read_json`) is
shared with `gaf.compat_endpoint`, the hosted provider that speaks the same protocol
(ADR-0052); the loopback refusal is not, because a hosted endpoint is by definition not
this machine and must never be reachable under the name "local".

Validation principle: **transparency** — the endpoint a call went to is decided in one
function and its refusal names the variable that would change it.
"""

from __future__ import annotations

import ipaddress
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from typing import Any

__all__ = [
    "ALLOW_REMOTE_ENV",
    "API_KEY_ENV",
    "BASE_URL_ENV",
    "DEFAULT_BASE_URL",
    "EndpointError",
    "LocalEndpointError",
    "get_json",
    "json_post_request",
    "local_base_url",
    "post_json",
    "read_json",
    "require_model",
    "served_models",
]

BASE_URL_ENV = "GAF_LOCAL_BASE_URL"
ALLOW_REMOTE_ENV = "GAF_LOCAL_ALLOW_REMOTE"
#: Sent as a bearer token. A local server ignores it; a remote OpenAI-compatible endpoint
#: reached under `ALLOW_REMOTE_ENV` (Moonshot's Kimi API, say) needs it.
API_KEY_ENV = "GAF_LOCAL_API_KEY"

#: Ollama's OpenAI-compatible root. LM Studio's default is ``http://localhost:1234/v1``.
DEFAULT_BASE_URL = "http://localhost:11434/v1"

#: A local model on a laptop can take minutes over a long refactor prompt; the timeout
#: exists to catch a dead server, not a slow one.
_REQUEST_TIMEOUT_S = 900.0
_PROBE_TIMEOUT_S = 5.0

_LOOPBACK_NAMES = frozenset({"localhost", "localhost.localdomain"})


class EndpointError(RuntimeError):
    """An OpenAI-compatible server is refused, unreachable, or answered unusably."""


class LocalEndpointError(EndpointError):
    """The local server is refused, unreachable, or answered with something unusable."""


def _is_loopback(host: str) -> bool:
    if host.lower() in _LOOPBACK_NAMES:
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def local_base_url(env: dict[str, str] | None = None) -> str:
    """The base URL of the local server, checked to be on this machine.

    Read from ``GAF_LOCAL_BASE_URL`` (default `DEFAULT_BASE_URL`). A host that is not a
    loopback address raises `LocalEndpointError` unless ``GAF_LOCAL_ALLOW_REMOTE=1``.
    """
    source = os.environ if env is None else env
    raw = (source.get(BASE_URL_ENV) or DEFAULT_BASE_URL).strip().rstrip("/")
    parsed = urllib.parse.urlparse(raw)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise LocalEndpointError(
            f"{BASE_URL_ENV}={raw!r} is not an http(s) URL; "
            f"the default is {DEFAULT_BASE_URL!r} (Ollama)"
        )
    if not _is_loopback(parsed.hostname) and source.get(ALLOW_REMOTE_ENV) != "1":
        raise LocalEndpointError(
            f"{BASE_URL_ENV} points at {parsed.hostname!r}, which is not this machine. "
            "A 'local' model must keep respondent text on the machine; to send it to "
            f"that host on purpose, set {ALLOW_REMOTE_ENV}=1 (and record why)."
        )
    return raw


def _auth_header() -> dict[str, str]:
    return {"Authorization": f"Bearer {os.environ.get(API_KEY_ENV) or 'local'}"}


def _local_unreachable(url: str, exc: Exception) -> str:
    return (
        f"no local model server at {url} ({exc}). Start one with "
        f"`ollama serve`, or point {BASE_URL_ENV} at the server you run."
    )


def read_json(
    request: urllib.request.Request,
    timeout: float,
    *,
    error: type[EndpointError] = LocalEndpointError,
    unreachable: Callable[[str, Exception], str] = _local_unreachable,
) -> Any:
    """Send `request` and decode its JSON reply, raising `error` with a usable message.

    An HTTP error status carries the first 300 characters of the server's body, which is
    where an OpenAI-compatible server says what it objected to; an unreachable server is
    described by `unreachable`, so the message names the fix for that kind of server.
    """
    try:
        with urllib.request.urlopen(request, timeout=timeout) as reply:
            body = reply.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:300]
        raise error(f"{request.full_url} answered {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
        raise error(unreachable(request.full_url, exc)) from exc
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise error(f"{request.full_url} returned non-JSON: {body[:200]!r}") from exc


def json_post_request(
    url: str, payload: dict[str, Any], headers: dict[str, str]
) -> urllib.request.Request:
    """A JSON POST to `url` with `headers` (the bearer token, for one)."""
    return urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )


def post_json(url: str, payload: dict[str, Any], *, timeout: float = _REQUEST_TIMEOUT_S) -> Any:
    """POST `payload` as JSON to `url` and return the decoded reply."""
    return read_json(json_post_request(url, payload, _auth_header()), timeout)


def get_json(url: str, *, timeout: float = _PROBE_TIMEOUT_S) -> Any:
    """GET `url` and return the decoded reply. Used to probe the server before a run."""
    return read_json(urllib.request.Request(url, headers=_auth_header(), method="GET"), timeout)


def served_models(base_url: str) -> set[str]:
    """Model ids the server at `base_url` says it can serve (``GET /models``)."""
    reply = get_json(f"{base_url}/models")
    data = reply.get("data") if isinstance(reply, dict) else None
    if not isinstance(data, list):
        raise LocalEndpointError(f"{base_url}/models did not return a model list")
    return {str(item.get("id")) for item in data if isinstance(item, dict) and item.get("id")}


def require_model(base_url: str, model: str) -> None:
    """Fail before a run starts if the server cannot serve `model`.

    Ollama lists ``name:tag``; a bare name means ``name:latest``, so both are accepted.
    """
    available = served_models(base_url)
    candidates = {model, f"{model}:latest"} if ":" not in model else {model}
    if not candidates & available:
        listing = ", ".join(sorted(available)) or "none"
        raise LocalEndpointError(
            f"the local server at {base_url} does not have model {model!r} "
            f"(it has: {listing}). With Ollama: `ollama pull {model}`."
        )
