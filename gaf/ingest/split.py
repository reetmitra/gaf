"""A pre-registered split of the PI's coded responses into a calibration fold and a held-out fold.

The PI hand-coded a subset of the corpus (39 of 200 responses on the India Process
export). Thresholds are calibrated against his coding, and agreement is quoted from
responses the calibration never saw, so the two folds are fixed **before any paid run**
and written to a file that carries ids and nothing else. That file is the
pre-registration: its hash is recorded, and nothing downstream may re-draw it.

The method is deterministic and written down in the file it produces:

* the **pilot ids** (the ten responses every earlier pilot run used) are always in the
  calibration fold, so the clean before-and-after of calibration is measured on
  responses that were already coded;
* the calibration fold is about half of the coded responses, so the rest of it is
  filled from the others;
* the fill is **stratified by the number of distinct codes on a response** -- the one
  property of a response that drives how hard it is to match -- in three bands cut at
  the terciles of the coded set, with each band's share of the fill set so that the
  calibration fold, pilots included, takes the same fraction of every band (largest
  remainder, ties to the lower band);
* inside a band the picks are drawn with ``random.Random(seed)`` over the ids sorted
  ascending, so the same golden set and seed always give the same split.

Responses are chosen **by id from the coded set**, never by slicing the corpus: the
last coded response sits at corpus position 76, and a slice would have dropped it.

Nothing here reads or writes a respondent's words. `filter_corpus` is the one function
that handles response bodies, and it only copies whole records through by id.

Validation principle: **reliability** -- an evaluation is only as honest as the split it
was drawn on, and a split is only honest if it was fixed before the result.
"""

from __future__ import annotations

import json
import math
import random
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gaf.models import Response

__all__ = [
    "PILOT_IDS",
    "SPLIT_SEED",
    "Split",
    "codes_per_response",
    "filter_corpus",
    "make_split",
    "read_golden_codes",
]

#: The ten responses the pilot runs (`runs/pilot10-*`) used. Always in the calibration fold.
PILOT_IDS: tuple[int, ...] = (11, 14, 15, 19, 22, 23, 24, 33, 40, 42)

#: Fixed in advance (the date the split was drawn, 4 October 2026) and recorded in the
#: file, so a reader can re-draw it and get the same ids.
SPLIT_SEED = 20261004



@dataclass(frozen=True, slots=True)
class Split:
    """Two disjoint folds of response ids that together are the whole coded set."""

    calibration: tuple[int, ...]
    held_out: tuple[int, ...]
    seed: int
    method: str

    def to_json(self) -> dict[str, Any]:
        """Ids, the seed and the method: the whole of the pre-registration."""
        return {
            "calibration": list(self.calibration),
            "held_out": list(self.held_out),
            "seed": self.seed,
            "method": self.method,
        }


def codes_per_response(rows: Iterable[Mapping[str, Any]]) -> dict[int, int]:
    """Distinct codes on each response in a golden set (rows with ``response_id``, ``code``)."""
    seen: dict[int, set[str]] = defaultdict(set)
    for row in rows:
        seen[int(row["response_id"])].add(str(row["code"]))
    return {rid: len(codes) for rid, codes in seen.items()}


def read_golden_codes(path: Path | str) -> dict[int, int]:
    """`codes_per_response` for the ``golden.json`` that `gaf codebook organise` wrote."""
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{path}: a golden set is a non-empty list of assignment rows")
    return codes_per_response(rows)


def _cuts(counts: Sequence[int]) -> tuple[int, int]:
    """The two band edges: the values at the first and second tercile of the sorted counts."""
    ordered = sorted(counts)
    last = len(ordered) - 1
    return ordered[last // 3], ordered[(2 * last) // 3]


def _band(value: int, cuts: tuple[int, int]) -> int:
    return 0 if value <= cuts[0] else 1 if value <= cuts[1] else 2


def _allocate(wanted: Sequence[float], capacity: Sequence[int], total: int) -> list[int]:
    """Spread `total` picks over the bands in proportion to `wanted`, by largest remainder.

    A band never receives more than its capacity; whatever it cannot take goes to the
    others in the same order. Ties on the remainder go to the lower band, so the result
    is a function of the numbers and nothing else.
    """
    total = min(total, sum(capacity))
    weights = [max(w, 0.0) for w in wanted]
    if sum(weights) == 0:
        weights = [float(c) for c in capacity]
    scale = total / sum(weights)
    exact = [w * scale for w in weights]
    given = [min(math.floor(x), cap) for x, cap in zip(exact, capacity, strict=True)]
    order = sorted(range(len(exact)), key=lambda i: (-(exact[i] - math.floor(exact[i])), i))
    while sum(given) < total:
        progressed = False
        for i in order:
            if sum(given) >= total:
                break
            if given[i] < capacity[i]:
                given[i] += 1
                progressed = True
        if not progressed:  # pragma: no cover - total was clamped to the capacity above
            break
    return given


def make_split(
    codes: Mapping[int, int],
    *,
    pilot_ids: Sequence[int] = PILOT_IDS,
    seed: int = SPLIT_SEED,
) -> Split:
    """Split the coded responses (id -> distinct codes) into calibration and held-out folds.

    Raises `ValueError` if a pilot id is not among the coded responses: a split that
    quietly dropped a pilot would no longer measure what it was drawn to measure.
    """
    ids = sorted(codes)
    if len(ids) < 2:
        raise ValueError("a split needs at least two coded responses")
    pilots = sorted(set(pilot_ids))
    missing = [rid for rid in pilots if rid not in codes]
    if missing:
        raise ValueError(f"pilot ids not in the golden set: {missing}")

    target = math.ceil(len(ids) / 2)
    cuts = _cuts([codes[rid] for rid in ids])
    bands: list[list[int]] = [[], [], []]
    for rid in ids:
        bands[_band(codes[rid], cuts)].append(rid)
    pilot_set = set(pilots)
    in_band = [len(band) for band in bands]
    pilots_in = [sum(1 for rid in band if rid in pilot_set) for band in bands]
    free = [[rid for rid in band if rid not in pilot_set] for band in bands]

    # What each band should contribute to the fill so that, pilots included, the
    # calibration fold holds `target / n` of every band.
    share = target / len(ids)
    wanted = [n * share - p for n, p in zip(in_band, pilots_in, strict=True)]
    fill = _allocate(wanted, [len(f) for f in free], max(target - len(pilots), 0))

    rng = random.Random(seed)
    chosen = set(pilots)
    for band_free, count in zip(free, fill, strict=True):
        chosen.update(rng.sample(band_free, count))
    calibration = tuple(sorted(chosen))
    held_out = tuple(rid for rid in ids if rid not in chosen)
    assert set(calibration) | set(held_out) == set(ids) and not set(calibration) & set(held_out)

    method = (
        f"{len(ids)} coded responses in golden.json; the {len(pilots)} pilot ids are fixed in the "
        f"calibration fold; the remaining {target - len(pilots)} calibration ids are drawn by "
        "stratifying the others on distinct codes per response, in three bands "
        f"(<= {cuts[0]}, {cuts[0] + 1} to {cuts[1]}, >= {cuts[1] + 1}; terciles of the coded set), "
        f"allocated so every band has the same calibration share (band sizes "
        f"{in_band[0]}/{in_band[1]}/{in_band[2]}, fill {fill[0]}/{fill[1]}/{fill[2]}); "
        f"picks drawn with random.Random({seed}).sample over ids sorted ascending; "
        "responses selected by id, never by slicing the corpus"
    )
    return Split(calibration=calibration, held_out=held_out, seed=seed, method=method)


def filter_corpus(responses: Sequence[Response], ids: Iterable[int]) -> list[Response]:
    """The records with these ids, in the corpus's own order. A missing id is an error.

    Selection is by id and nothing else. A coded response that is not in the corpus means
    the golden set and the corpus disagree, and a subset that silently lacked it would
    make a fold smaller than the file that registered it.
    """
    wanted = set(ids)
    found = [r for r in responses if r.id in wanted]
    absent = sorted(wanted - {r.id for r in found})
    if absent:
        raise ValueError(f"ids not in the corpus: {absent}")
    return found
