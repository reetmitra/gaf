"""The pre-registered split: ids only, deterministic, stratified, and selected by id.

Four claims:

1. **The pilot ids are always in the calibration fold**, and a pilot id that is not coded
   is an error rather than a quietly smaller fold.
2. **The folds partition the coded set** -- disjoint, together exactly the golden ids --
   with the calibration fold about half of it.
3. **The fill is stratified and deterministic.** Each band of codes-per-response
   contributes in proportion to its size, the same inputs always write the same bytes,
   and a different seed draws a different fold.
4. **Selection is by id.** A coded response far from the front of the corpus is found,
   one the corpus lacks is an error, and the file the script writes holds ids, the seed
   and the method and nothing else.

Every id, code and response below is invented.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from gaf.ingest.corpus import read_corpus_json, write_corpus_json
from gaf.ingest.split import (
    PILOT_IDS,
    SPLIT_SEED,
    codes_per_response,
    filter_corpus,
    make_split,
    read_golden_codes,
)
from gaf.models import Response

REPO_ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location("gaf_make_split", REPO_ROOT / "scripts" / "make_split.py")
assert _SPEC is not None and _SPEC.loader is not None
make_split_script = importlib.util.module_from_spec(_SPEC)
sys.modules["gaf_make_split"] = make_split_script
_SPEC.loader.exec_module(make_split_script)


def coded(n: int = 39, *, skip: tuple[int, ...] = ()) -> dict[int, int]:
    """n invented coded responses: the pilot ids, then ids that jump about, with spread counts."""
    ids = [*PILOT_IDS, *range(43, 43 + 3 * (n - len(PILOT_IDS)), 3)]
    return {rid: 1 + (i * 7) % 13 for i, rid in enumerate(ids) if rid not in skip}


def test_the_pilot_ids_are_always_in_the_calibration_fold() -> None:
    split = make_split(coded())
    assert set(PILOT_IDS) <= set(split.calibration)


def test_a_pilot_id_that_is_not_coded_is_refused_by_name() -> None:
    with pytest.raises(ValueError, match=r"pilot ids not in the golden set: \[24\]"):
        make_split(coded(skip=(24,)))


def test_the_folds_partition_the_coded_set_and_calibration_is_about_half() -> None:
    codes = coded()
    split = make_split(codes)
    assert not set(split.calibration) & set(split.held_out)
    assert set(split.calibration) | set(split.held_out) == set(codes)
    assert (len(split.calibration), len(split.held_out)) == (20, 19)
    assert list(split.calibration) == sorted(split.calibration)
    assert list(split.held_out) == sorted(split.held_out)


def test_the_same_inputs_give_the_same_split_and_another_seed_gives_another() -> None:
    again = make_split(coded()).to_json()
    assert make_split(coded()).to_json() == again
    other = make_split(coded(), seed=SPLIT_SEED + 1)
    assert other.calibration != make_split(coded()).calibration
    assert set(PILOT_IDS) <= set(other.calibration)
    assert other.seed == SPLIT_SEED + 1 and again["seed"] == SPLIT_SEED


def test_the_fill_takes_the_same_share_of_every_band() -> None:
    codes = coded(60)
    split = make_split(codes)
    ordered = sorted(codes.values())
    last = len(ordered) - 1
    cuts = (ordered[last // 3], ordered[(2 * last) // 3])

    def band(rid: int) -> int:
        return 0 if codes[rid] <= cuts[0] else 1 if codes[rid] <= cuts[1] else 2

    for b in range(3):
        members = [rid for rid in codes if band(rid) == b]
        taken = sum(1 for rid in members if rid in set(split.calibration))
        ideal = len(members) * len(split.calibration) / len(codes)
        assert abs(taken - ideal) <= 1.5, f"band {b}: {taken} of {len(members)}, ideal {ideal:.1f}"


def test_the_method_is_written_into_the_split_and_names_no_response() -> None:
    payload = make_split(coded()).to_json()
    assert list(payload) == ["calibration", "held_out", "seed", "method"]
    method = payload["method"]
    assert "random.Random(20261004)" in method and "by id" in method and "tercile" in method
    assert "10 pilot ids" in method and "39 coded responses" in method


def test_more_pilots_than_half_leaves_the_fold_at_the_pilots() -> None:
    codes = {rid: 1 + rid % 5 for rid in (*PILOT_IDS, 50, 51)}
    split = make_split(codes)
    assert set(split.calibration) == set(PILOT_IDS)
    assert set(split.held_out) == {50, 51}


def test_two_coded_responses_are_enough_for_a_split() -> None:
    split = make_split({11: 3, 14: 4}, pilot_ids=(11,))
    assert (split.calibration, split.held_out) == ((11,), (14,))
    with pytest.raises(ValueError, match="at least two"):
        make_split({11: 3}, pilot_ids=())


def test_a_band_that_cannot_take_its_share_hands_the_rest_to_the_others() -> None:
    # nearly every response sits in the top band, so the bottom bands cannot fill alone
    codes = dict.fromkeys(range(100, 130), 9) | {11: 1, 14: 2}
    split = make_split(codes, pilot_ids=(11, 14))
    assert len(split.calibration) == 16 and {11, 14} <= set(split.calibration)


def test_codes_per_response_counts_distinct_codes() -> None:
    rows = [
        {"response_id": 5, "code": "a-b", "segment": "x"},
        {"response_id": 5, "code": "a-b", "segment": "y"},
        {"response_id": 5, "code": "a-c", "segment": "z"},
        {"response_id": 9, "code": "a-b", "segment": "w"},
    ]
    assert codes_per_response(rows) == {5: 2, 9: 1}


def test_a_golden_file_that_is_not_a_golden_set_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "golden.json"
    path.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="non-empty list"):
        read_golden_codes(path)
    path.write_text('{"a": 1}', encoding="utf-8")
    with pytest.raises(ValueError, match="non-empty list"):
        read_golden_codes(path)


def _corpus(ids: list[int]) -> list[Response]:
    return [Response(id=i, question="q", content=f"body {i}", source="s") for i in ids]


def test_responses_are_selected_by_id_not_by_position() -> None:
    corpus = _corpus([3, 40, 41, 76, 200])
    assert [r.id for r in filter_corpus(corpus, [200, 3])] == [3, 200], "corpus order, by id"
    assert [r.id for r in filter_corpus(corpus, [76])] == [76]
    with pytest.raises(ValueError, match=r"ids not in the corpus: \[77, 78\]"):
        filter_corpus(corpus, [3, 77, 78])


def test_the_script_writes_ids_only_and_three_loadable_corpus_files(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    codes = coded()
    golden = [
        {"response_id": rid, "code": f"code-{k}", "segment": "S"}
        for rid, n in codes.items()
        for k in range(n)
    ]
    golden_path = tmp_path / "golden.json"
    golden_path.write_text(json.dumps(golden), encoding="utf-8")
    ids = sorted(codes)
    corpus_path = write_corpus_json(_corpus([*range(1, 400)]), tmp_path / "corpus.json")
    out = tmp_path / "v2" / "split.json"

    status = make_split_script.main(
        [
            "--golden", str(golden_path),
            "--corpus", str(corpus_path),
            "--out", str(out),
            "--corpus-dir", str(tmp_path / "runs"),
        ]
    )
    assert status == 0
    shown = capsys.readouterr().out
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert sorted([*payload["calibration"], *payload["held_out"]]) == ids
    assert set(PILOT_IDS) <= set(payload["calibration"])
    assert set(payload) == {"calibration", "held_out", "seed", "method"}
    import hashlib

    assert hashlib.sha256(out.read_bytes()).hexdigest() in shown

    expected = {
        "split-calibration-corpus.json": payload["calibration"],
        "split-heldout-corpus.json": payload["held_out"],
        "coded39-corpus.json": ids,
    }
    for name, wanted in expected.items():
        loaded = read_corpus_json(tmp_path / "runs" / name)
        assert sorted(r.id for r in loaded) == sorted(wanted)
        assert all(r.question for r in loaded)

    first = out.read_bytes()
    make_split_script.main(
        [
            "--golden", str(golden_path),
            "--corpus", str(corpus_path),
            "--out", str(out),
            "--corpus-dir", str(tmp_path / "runs"),
        ]
    )
    assert out.read_bytes() == first, "the same inputs write the same bytes"
