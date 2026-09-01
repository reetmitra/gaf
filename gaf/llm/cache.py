"""Content-addressed disk memoisation for model calls.

A wrapper that implements `gaf.llm.base.LLMClient` and delegates to an inner client,
keyed on `LLMRequest.cache_key_parts()`. Those parts deliberately exclude run ids and
timestamps, so the key is a fact about the *question* rather than about the occasion:
re-running a batch against the same snapshot asks the same questions and pays nothing.

Two deliberate additions to the key, both load-bearing:

* **the inner client's provider and model.** `cache_key_parts` describes the request,
  not the respondent. Coder A and coder B are given the same context on purpose — that
  is the epistemic-diversity mechanism — so a key without the provider would serve
  A's answer to B and silently collapse two coders into one.
* **a schema version**, so a change to what is stored invalidates old entries instead of
  being read back as the wrong shape.

Two things are deliberately *not* cached: a `fail_safe` result, because freezing a
transient parse failure would make it permanent; and a cache hit itself, which is
already on disk.

A corrupt or truncated entry is ignored and refetched. A cache is an optimisation, and
an optimisation that can halt a run is not one.

Validation principle: **reliability** — a cached call is a replayable fact, and the
stored entry carries the exact key parts that produced it, so a reviewer can see what
question an answer was an answer to.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from gaf.config import ModelSpec
from gaf.llm.base import LLMClient, LLMRequest, LLMResult, TaskType

__all__ = ["CACHE_SCHEMA_VERSION", "CachingLLMClient", "cache_key"]

#: Bumped when the on-disk entry shape changes. Part of the key, so a bump orphans old
#: entries rather than misreading them.
CACHE_SCHEMA_VERSION = "1"


def cache_key(request: LLMRequest, spec: ModelSpec) -> str:
    """The content address of one question asked of one model.

    Hex blake2b over the frozen `cache_key_parts()` plus the provider, the model and the
    schema version. Parts are joined with a unit separator that cannot occur in a prompt
    field, so no two distinct part lists can produce the same joined string.
    """
    parts = (
        CACHE_SCHEMA_VERSION,
        spec.provider,
        spec.model,
        *request.cache_key_parts(),
    )
    hasher = hashlib.blake2b(digest_size=16)
    hasher.update("\x1f".join(parts).encode("utf-8"))
    return hasher.hexdigest()


class CachingLLMClient:
    """Wraps an `LLMClient` with a content-addressed JSON cache on disk.

    `cache_dir=None` disables caching entirely and the wrapper becomes a pass-through,
    which is what `RunConfig.cache_dir = None` means.
    """

    def __init__(self, inner: LLMClient, cache_dir: Path | None) -> None:
        self.inner = inner
        self.spec: ModelSpec = inner.spec
        self.cache_dir = Path(cache_dir) if cache_dir is not None else None
        self.hits = 0
        self.misses = 0

    @property
    def enabled(self) -> bool:
        return self.cache_dir is not None

    def path_for(self, request: LLMRequest) -> Path | None:
        """Where this request's entry lives, or None when caching is off."""
        if self.cache_dir is None:
            return None
        return self.cache_dir / f"{cache_key(request, self.spec)}.json"

    def complete_json(self, request: LLMRequest) -> LLMResult:
        path = self.path_for(request)
        if path is not None:
            cached = self._read(path, request)
            if cached is not None:
                self.hits += 1
                return cached
        self.misses += 1
        result = self.inner.complete_json(request)
        if path is not None and not result.fail_safe and not result.cache_hit:
            self._write(path, request, result)
        return result

    # -- disk ------------------------------------------------------------- #

    def _read(self, path: Path, request: LLMRequest) -> LLMResult | None:
        """Load an entry, or None if it is absent, unreadable or not what it claims."""
        try:
            stored = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        if not isinstance(stored, dict):
            return None
        try:
            meta = stored["result"]
            data = stored["data"]
            if not isinstance(data, dict):
                return None
            task = TaskType(meta["task"])
        except (KeyError, TypeError, ValueError):
            return None
        if task is not request.task:
            # A digest collision, or a hand-edited file. Refetch rather than answer
            # the wrong question.
            return None
        return LLMResult(
            data=data,
            task=task,
            provider=str(meta.get("provider", self.spec.provider)),
            model=str(meta.get("model", self.spec.model)),
            prompt_version=str(meta.get("prompt_version", request.prompt_version)),
            raw_text=str(stored.get("raw_text", "")),
            input_tokens=int(meta.get("input_tokens", 0)),
            output_tokens=int(meta.get("output_tokens", 0)),
            # A hit costs nothing and takes no measurable time: neither the money nor
            # the wall clock of the original call is claimed twice.
            cost_usd=0.0,
            latency_ms=0.0,
            cache_hit=True,
            fail_safe=False,
            attempts=int(meta.get("attempts", 1)),
        )

    def _write(self, path: Path, request: LLMRequest, result: LLMResult) -> None:
        """Store an entry. A cache that cannot be written is not an error."""
        payload: dict[str, Any] = {
            "schema": CACHE_SCHEMA_VERSION,
            "subject": request.subject,
            "key_parts": list(request.cache_key_parts()),
            "result": result.to_json(),
            "data": result.data,
            "raw_text": result.raw_text,
        }
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            # Write beside the target and rename, so an interrupted run leaves either
            # the old entry or the new one, never half of one.
            temporary = path.with_suffix(".json.tmp")
            temporary.write_text(
                json.dumps(payload, sort_keys=True, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            temporary.replace(path)
        except (OSError, TypeError, ValueError):
            return

    def stats(self) -> dict[str, Any]:
        """Hit/miss counts for the run report."""
        return {
            "enabled": self.enabled,
            "cache_dir": str(self.cache_dir) if self.cache_dir else None,
            "hits": self.hits,
            "misses": self.misses,
        }
