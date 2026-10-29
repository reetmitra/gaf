"""Write the pre-registered calibration / held-out split, and the corpus subsets it names.

Usage (from the repository root):

    uv run python scripts/make_split.py \
        --golden runs/human200-v2/golden.json \
        --corpus runs/process200/corpus.json \
        --out runs/human200-v2/split.json \
        --corpus-dir runs

Writes ``split.json`` (ids, the seed and the method; no text) and, in ``--corpus-dir``,
three corpus files in the shape of ``runs/pilot10-corpus.json``, each filtered **by id**
from the corpus: ``split-calibration-corpus.json``, ``split-heldout-corpus.json`` and
``coded<N>-corpus.json`` (every coded response). The corpus files hold respondents'
words and belong under the gitignored ``runs/``. Prints counts, ids and the sha256 of
``split.json``, never a response.

The method lives in ``gaf.ingest.split`` and is deterministic: the same golden set and
seed always write the same bytes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from gaf.ingest.corpus import read_corpus_json, write_corpus_json
from gaf.ingest.split import SPLIT_SEED, filter_corpus, make_split, read_golden_codes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--golden", required=True, type=Path, help="golden.json of the organised coding")
    parser.add_argument("--corpus", required=True, type=Path, help="the corpus JSON `gaf ingest` wrote")
    parser.add_argument("--out", required=True, type=Path, help="where to write split.json")
    parser.add_argument("--corpus-dir", required=True, type=Path, help="where to write the corpus subsets")
    parser.add_argument("--seed", type=int, default=SPLIT_SEED, help="default: %(default)s")
    args = parser.parse_args(argv)

    codes = read_golden_codes(args.golden)
    split = make_split(codes, seed=args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(split.to_json(), indent=2) + "\n"
    args.out.write_text(payload, encoding="utf-8")

    corpus = read_corpus_json(args.corpus)
    n_coded = len(codes)
    subsets = {
        "split-calibration-corpus.json": split.calibration,
        "split-heldout-corpus.json": split.held_out,
        f"coded{n_coded}-corpus.json": tuple(sorted(codes)),
    }
    for name, ids in subsets.items():
        path = write_corpus_json(filter_corpus(corpus, ids), args.corpus_dir / name)
        loaded = read_corpus_json(path)
        if sorted(r.id for r in loaded) != sorted(ids):
            raise SystemExit(f"{path}: read back different ids than were written")
        print(f"  wrote {path}  ({len(loaded)} responses)")

    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    print(f"  wrote {args.out}")
    print(f"  calibration {len(split.calibration)}: {list(split.calibration)}")
    print(f"  held out    {len(split.held_out)}: {list(split.held_out)}")
    print(f"  split.json sha256 {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
