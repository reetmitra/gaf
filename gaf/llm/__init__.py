"""Model clients: one protocol, three live providers, deterministic mocks, a disk cache.

No agent framework, no cross-call memory, no fine-tuning. Every call is stateless and
re-grounded from canonical sources; handoffs between stages carry ids, not prose. The
offline path (mock clients) is the default and the only path tests and CI use.

Validation principle: **reliability** — a stateless, content-addressed, cached call is
a replayable fact; a conversation with a model is not.
"""

from __future__ import annotations

from gaf.llm.anthropic_client import AnthropicClient
from gaf.llm.base import (
    DISPUTE_VERDICTS,
    FAIL_SAFE_DEFAULTS,
    ROUTE_VERDICTS,
    CallLog,
    LLMClient,
    LLMError,
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
from gaf.llm.cache import CachingLLMClient, cache_key
from gaf.llm.gemini_client import GeminiClient

# Each of `anthropic_client`, `gemini_client` and `openai_client` defines its own
# `MissingProviderSDKError` — three distinct exception classes, one per provider, so
# that catching one never masks a different provider's failure. A single unqualified
# name at this package's level could only ever refer to one of the three, which would
# be misleading; catch each provider's own via its submodule
# (`gaf.llm.anthropic_client.MissingProviderSDKError`, and so on), as
# `gaf.cli._common` already does.
from gaf.llm.mock import (
    FABRICATED_QUOTE,
    MOCKDISPUTE_DROP,
    MOCKFIT_UNNECESSARY,
    MOCKROUTE_MERGE,
    MockCoderClient,
    MockJudgeClient,
    MockRefactorerClient,
    extract_code_ids,
    extract_response_id,
    extract_response_text,
    mock_candidates_for,
    split_segments,
)
from gaf.llm.openai_client import OpenAIClient

__all__ = [
    "DISPUTE_VERDICTS",
    "FABRICATED_QUOTE",
    "FAIL_SAFE_DEFAULTS",
    "MOCKDISPUTE_DROP",
    "MOCKFIT_UNNECESSARY",
    "MOCKROUTE_MERGE",
    "ROUTE_VERDICTS",
    "AnthropicClient",
    "CachingLLMClient",
    "CallLog",
    "GeminiClient",
    "LLMClient",
    "LLMError",
    "LLMRequest",
    "LLMResult",
    "MalformedReplyError",
    "MockCoderClient",
    "MockJudgeClient",
    "MockRefactorerClient",
    "OpenAIClient",
    "TaskType",
    "cache_key",
    "extract_code_ids",
    "extract_response_id",
    "extract_response_text",
    "fail_safe_for",
    "mock_candidates_for",
    "parse_json_object",
    "retry_with_jitter",
    "split_segments",
    "strip_fences",
    "validate_enum",
]
