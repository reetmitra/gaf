"""Offline fixtures: an invented corpus, planted check violations, toy codebooks,
a stub embedder, in-test spreadsheet builders, and a scored table with a known signal.

Nothing here derives from a human survey response. The whole test suite runs from a
clean clone with no data files, no API keys and no network.
"""

from tests.fixtures.assignments import human_assignments, machine_assignments
from tests.fixtures.candidates import CASES, Case, cand, case, clean_candidates, word_windows
from tests.fixtures.codebooks import broken_codebook, near_duplicate_codebook, toy_codebook
from tests.fixtures.corpus import (
    FABRICATED_QUOTE,
    MOCKFIT_UNNECESSARY,
    S2B_THREE_SENTENCES,
    S4_SHARED_SENTENCE,
    SOURCE,
    corpus_by_id,
    response_ids,
    synthetic_corpus,
)
from tests.fixtures.embedding import StubEmbedder
from tests.fixtures.scored import ScoredRow, score_counts, synthetic_scored_table
from tests.fixtures.xlsx import write_coded_xlsx, write_narrative_state_xlsx

__all__ = [
    "CASES",
    "FABRICATED_QUOTE",
    "MOCKFIT_UNNECESSARY",
    "S2B_THREE_SENTENCES",
    "S4_SHARED_SENTENCE",
    "SOURCE",
    "Case",
    "ScoredRow",
    "StubEmbedder",
    "broken_codebook",
    "cand",
    "case",
    "clean_candidates",
    "corpus_by_id",
    "human_assignments",
    "machine_assignments",
    "near_duplicate_codebook",
    "response_ids",
    "score_counts",
    "synthetic_corpus",
    "synthetic_scored_table",
    "toy_codebook",
    "word_windows",
    "write_coded_xlsx",
    "write_narrative_state_xlsx",
]
