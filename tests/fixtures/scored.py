"""A synthetic pooled scored table with a planted vocabulary, for the §13 lexical check.

The lexical validation asks whether treating a per-response score as continuous
changes the extracted vocabulary compared with a binarised framing. To test that
machinery you need data whose answer you already know, so this fixture plants two word
sets and injects them at rates that vary monotonically with the score:

* ``HIGH_SIGNAL`` words appear with probability ``0.10 + 0.16 * score`` (0.10 at
  score 0, 0.90 at score 5);
* ``LOW_SIGNAL`` words appear with probability ``0.90 - 0.16 * score``;
* ``FILLER`` words are independent of the score and must **not** be selected.

The score distribution is chosen so both binarised cuts are fittable and so the ge3
cut has a meaningful number of ``score == 2`` rows — those count as **negatives**, and
silently dropping them is one of the two documented ways to get this test wrong.

Generation uses `random.Random(seed)`, never the global RNG, so the table is identical
across runs, processes and platforms.

Validation principle: **reliability**.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

__all__ = [
    "FILLER",
    "GROUPS",
    "HIGH_SIGNAL",
    "LOW_SIGNAL",
    "SCORE_DISTRIBUTION",
    "ScoredRow",
    "score_counts",
    "synthetic_scored_table",
]

#: Planted words that drive a high score. Every target must recover these.
HIGH_SIGNAL: tuple[str, ...] = (
    "automation",
    "unemployment",
    "surveillance",
    "displacement",
    "algorithmic",
    "governance",
    "inequality",
    "accountability",
)

#: Planted words that drive a low score.
LOW_SIGNAL: tuple[str, ...] = (
    "unsure",
    "maybe",
    "unclear",
    "vague",
    "ordinary",
    "somewhat",
    "unremarkable",
    "unchanged",
)

#: Score-independent vocabulary. Selecting one of these is a false positive.
FILLER: tuple[str, ...] = (
    "society", "future", "people", "country", "system", "work", "life", "change",
    "technology", "machine", "computer", "data", "family", "school", "city",
    "village", "market", "service", "company", "worker", "student", "doctor",
    "farmer", "office", "transport", "energy", "water", "health", "education",
    "policy", "decision", "process", "result", "example", "reason", "problem",
    "solution", "question", "answer", "opinion", "view", "picture", "scenario",
    "development", "progress", "growth", "risk", "benefit", "cost", "value",
)

#: score -> number of responses. ge1: 180 positive / 60 negative.
#: ge3: 95 positive / 145 negative, of which 45 are score == 2.
SCORE_DISTRIBUTION: dict[int, int] = {0: 60, 1: 40, 2: 45, 3: 40, 4: 35, 5: 20}

#: Deliberately imbalanced, so the pooled report has an imbalance to surface.
GROUPS: tuple[tuple[str, int], ...] = (("india", 150), ("singapore", 90))


@dataclass(frozen=True, slots=True)
class ScoredRow:
    response_id: int
    text: str
    score: int
    group: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "response_id": self.response_id,
            "text": self.text,
            "score": self.score,
            "group": self.group,
        }


def _sentence(words: list[str], rng: random.Random) -> str:
    rng.shuffle(words)
    return " ".join(words).capitalize() + "."


def synthetic_scored_table(seed: int = 1729) -> list[ScoredRow]:
    """The pooled table: 240 rows, planted signal, deterministic for a given seed."""
    rng = random.Random(seed)

    groups: list[str] = []
    for name, count in GROUPS:
        groups.extend([name] * count)
    total = sum(SCORE_DISTRIBUTION.values())
    if len(groups) != total:
        raise AssertionError(f"group sizes ({len(groups)}) must sum to {total}")
    rng.shuffle(groups)

    scores: list[int] = []
    for score, count in sorted(SCORE_DISTRIBUTION.items()):
        scores.extend([score] * count)
    rng.shuffle(scores)

    rows: list[ScoredRow] = []
    for index, (score, group) in enumerate(zip(scores, groups, strict=True)):
        p_high = 0.10 + 0.16 * score
        p_low = 0.90 - 0.16 * score
        words: list[str] = [w for w in HIGH_SIGNAL if rng.random() < p_high]
        words += [w for w in LOW_SIGNAL if rng.random() < p_low]
        words += rng.sample(FILLER, k=rng.randint(18, 26))
        # Three short sentences, so the review sheet has real excerpts to quote.
        rng.shuffle(words)
        third = max(1, len(words) // 3)
        text = " ".join(
            _sentence(words[i : i + third], rng) for i in range(0, len(words), third)
        )
        rows.append(
            # Non-contiguous ids, matching the shape of the real corpus.
            ScoredRow(response_id=1000 + index * 3, text=text, score=score, group=group)
        )
    return rows


def score_counts(rows: list[ScoredRow]) -> dict[str, Any]:
    """Score distribution and both binarised class balances — printed before any fit."""
    by_score: dict[int, int] = {}
    for row in rows:
        by_score[row.score] = by_score.get(row.score, 0) + 1
    ge1_pos = sum(1 for r in rows if r.score >= 1)
    ge3_pos = sum(1 for r in rows if r.score >= 3)
    return {
        "n": len(rows),
        "by_score": {k: by_score[k] for k in sorted(by_score)},
        "ge1": {"positive": ge1_pos, "negative": len(rows) - ge1_pos},
        "ge3": {"positive": ge3_pos, "negative": len(rows) - ge3_pos},
        "score_2_rows": by_score.get(2, 0),
        "by_group": {
            g: sum(1 for r in rows if r.group == g) for g, _ in sorted(GROUPS)
        },
    }
