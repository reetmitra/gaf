"""Canonical text normalisation — the single function every character span is defined against.

FROZEN CONTRACT (Wave 0). Do not change without re-broadcasting.

`Segment.start`/`Segment.end`, `Evidence.span`, and every span produced by the S2
quote locator are offsets into ``normalise(response.content)`` — never into the raw
source text. Exactly one normalisation function exists so that a span recorded by the
coder, re-checked by S2, clustered by S4, and displayed in the HTML explorer all refer
to the same characters.

Validation principle: **reliability** — a span is only replayable if the string it
indexes into is reproducible from the raw source by a documented, idempotent function.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = ["NORMALISATION_VERSION", "normalise", "normalise_for_match"]

# Bumped only if the normalisation changes. Recorded alongside spans in the store so
# that spans from an earlier version are never silently compared against a later one.
NORMALISATION_VERSION = "norm-1"

# 1:1 character replacements applied after NFKC. Length-preserving by construction,
# which keeps the mapping easy to reason about; the only length changes come from
# NFKC itself (e.g. "…" -> "...") and from whitespace collapsing.
_PUNCT_MAP = str.maketrans(
    {
        "‘": "'",  # left single quote
        "’": "'",  # right single quote / apostrophe
        "‚": "'",  # single low-9 quote
        "‛": "'",  # single high-reversed-9 quote
        "“": '"',  # left double quote
        "”": '"',  # right double quote
        "„": '"',  # double low-9 quote
        "′": "'",  # prime
        "″": '"',  # double prime
        "‐": "-",  # hyphen
        "‑": "-",  # non-breaking hyphen
        "‒": "-",  # figure dash
        "–": "-",  # en dash
        "—": "-",  # em dash
        "―": "-",  # horizontal bar
        " ": " ",  # no-break space
        "​": " ",  # zero-width space
        "﻿": " ",  # BOM / zero-width no-break space
    }
)

_WHITESPACE_RE = re.compile(r"\s+")


def normalise(text: str) -> str:
    """Return the canonical form of ``text``.

    Steps, in order:

    1. Unicode NFKC normalisation (folds ligatures, full-width forms, "..." for "…").
    2. Length-preserving punctuation folding (curly quotes, dashes, exotic spaces).
    3. Collapse every run of whitespace to a single ASCII space.
    4. Strip leading and trailing whitespace.

    Case is deliberately **preserved**: normalised text is quoted verbatim in the
    codebook, the audit log and the run report, and must stay human-readable.
    Case-insensitive comparison is the caller's business (see `normalise_for_match`).

    The function is idempotent: ``normalise(normalise(t)) == normalise(t)``.
    """
    folded = unicodedata.normalize("NFKC", text)
    folded = folded.translate(_PUNCT_MAP)
    folded = _WHITESPACE_RE.sub(" ", folded)
    return folded.strip()


def normalise_for_match(text: str) -> str:
    """Case-folded canonical form, for *comparison only*.

    Never use the result to compute a span: it is not offset-compatible with
    `normalise` under every input (case folding can change length, e.g. "ß" -> "ss").
    """
    return normalise(text).casefold()
