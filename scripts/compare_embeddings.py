"""Compare embedding spaces on the investigator's own coding. Prints numbers, never text.

Usage (from the repository root, with a local model server running for local spaces):

    uv run python scripts/compare_embeddings.py \
        --golden runs/human200/golden.json \
        --codebook runs/human200/codebook.json \
        --space lexical \
        --space local:qwen3-embedding:0.6b \
        --out runs/embedding-comparison

Each unit is one highlight the investigator coded; its correct codes are the codes he
applied to that exact highlight. Every highlight is scored against every code in his
codebook, rendered by `gaf.embed.protocol.code_text` — the same rendering M1 (retrieval)
and M3 (code↔evidence fit) use — once with his definitions and once with names only.

Three numbers per space, each tied to a stage of the pipeline:

* **top-1** — his code is the nearest code. The best case for the dedup gate and the
  crosswalk, which both act on the nearest neighbour.
* **recall@k** (k = `RunConfig.retrieval_top_k`, 8) — his code is among the k codes the
  Coder is shown in full. A miss here means the Coder never sees the right code's
  definition while coding that text.
* **fit AUC** — the chance that a highlight scores higher against a code he applied than
  against one he did not. This is what M3 needs: the better the separation, the fewer
  code↔evidence pairs fall in the grey band and go to the judge, which is 64-80% of the
  live bill (ADR-0022). 0.5 is chance.

Plus **wrong-pass at 90%**: with a cut that lets 90% of his own pairs through without a
judge call, the share of wrong code↔highlight pairs that would also pass. Lower is better.

Nothing here reads or writes a threshold; it compares geometries. Output goes to
``--out`` (under ``runs/``, which is never tracked) as JSON and a Markdown table of
aggregates. No respondent text is printed or written.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

from gaf.config import EmbeddingSpaceConfig, RunConfig
from gaf.embed.protocol import code_text
from gaf.embed.service import EmbeddingService
from gaf.local_endpoint import local_base_url, post_json

#: Distinct strings one full offline run over the 200-response corpus embeds (measured
#: on 25 Sep 2026 by counting what reached `EmbeddingService._fill`). Used only to turn a
#: measured throughput into "seconds per full run".
STRINGS_PER_FULL_RUN = 1688


def _auc(pos: np.ndarray, neg: np.ndarray) -> float:
    """Mann-Whitney AUC: P(score of a positive > score of a negative), ties count half."""
    scores = np.concatenate([pos, neg])
    order = scores.argsort(kind="mergesort")
    ranks = np.empty(len(scores), dtype=np.float64)
    ranks[order] = np.arange(1, len(scores) + 1)
    # average ranks over ties
    sorted_scores = scores[order]
    start = 0
    for end in range(1, len(scores) + 1):
        if end == len(scores) or sorted_scores[end] != sorted_scores[start]:
            ranks[order[start:end]] = (start + 1 + end) / 2.0
            start = end
    rank_sum = ranks[: len(pos)].sum()
    return float((rank_sum - len(pos) * (len(pos) + 1) / 2.0) / (len(pos) * len(neg)))


def _space(spec: str) -> EmbeddingSpaceConfig:
    if spec == "lexical":
        return EmbeddingSpaceConfig()
    mode, _, model = spec.partition(":")
    if mode != "local" or not model:
        raise SystemExit(f"--space must be 'lexical' or 'local:<model>', got {spec!r}")
    probe = post_json(f"{local_base_url()}/embeddings", {"model": model, "input": ["probe"]})
    dim = len(probe["data"][0]["embedding"])
    return EmbeddingSpaceConfig(mode="local", model=model, dim=dim)


def _score(
    service: EmbeddingService,
    segments: list[str],
    gold: list[set[int]],
    code_texts: list[str],
    k: int,
) -> dict[str, float]:
    seg = service.embed(segments)
    codes = service.embed(code_texts)
    sim = seg @ codes.T  # vectors are L2-normalised: cosine is a dot product
    ranked = np.argsort(-sim, axis=1, kind="stable")
    top1 = np.mean([ranked[i, 0] in gold[i] for i in range(len(gold))])
    recall = np.mean([bool(set(ranked[i, :k]) & gold[i]) for i in range(len(gold))])
    mask = np.zeros_like(sim, dtype=bool)
    for i, g in enumerate(gold):
        mask[i, list(g)] = True
    pos, neg = sim[mask], sim[~mask]
    cut = float(np.quantile(pos, 0.10))
    return {
        "top1": round(float(top1), 4),
        f"recall_at_{k}": round(float(recall), 4),
        "fit_auc": round(_auc(pos, neg), 4),
        "wrong_pass_at_90": round(float(np.mean(neg >= cut)), 4),
        "pos_mean_cosine": round(float(pos.mean()), 4),
        "neg_mean_cosine": round(float(neg.mean()), 4),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--golden", required=True, type=Path)
    parser.add_argument("--codebook", required=True, type=Path)
    parser.add_argument("--space", action="append", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)

    golden = json.loads(args.golden.read_text())
    codebook = json.loads(args.codebook.read_text())["codes"]
    names = [c["name"] for c in codebook]
    index = {n: i for i, n in enumerate(names)}

    by_highlight: dict[tuple[int, str], set[int]] = defaultdict(set)
    for row in golden:
        by_highlight[(row["response_id"], row["segment"])].add(index[row["code"]])
    keys = sorted(by_highlight)
    segments = [segment for _, segment in keys]
    gold = [by_highlight[key] for key in keys]
    with_defs = [code_text(c["name"], c.get("description") or "") for c in codebook]
    names_only = [code_text(c["name"]) for c in codebook]
    k = RunConfig().retrieval_top_k

    results = []
    for spec in args.space:
        config = _space(spec)
        service = EmbeddingService(config)
        started = time.perf_counter()
        defs = _score(service, segments, gold, with_defs, k)
        elapsed = time.perf_counter() - started
        n_embedded = service.memo_size
        bare = _score(service, segments, gold, names_only, k)
        row = {
            "space_id": service.space_id,
            "dim": config.dim,
            "with_definitions": defs,
            "names_only": bare,
            "seconds_first_pass": round(elapsed, 2),
            "strings_first_pass": n_embedded,
            "est_seconds_per_full_run": round(elapsed / max(n_embedded, 1) * STRINGS_PER_FULL_RUN, 1),
        }
        results.append(row)
        print(json.dumps(row), flush=True)

    summary = {
        "n_highlights": len(keys),
        "n_highlight_code_pairs": sum(len(g) for g in gold),
        "n_codes": len(codebook),
        "retrieval_top_k": k,
        "spaces": results,
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "comparison.json").write_text(json.dumps(summary, indent=2) + "\n")
    lines = [
        f"{len(keys)} highlights, {summary['n_highlight_code_pairs']} highlight-code pairs, "
        f"{len(codebook)} codes. Aggregates only.",
        "",
        f"| space | top-1 | recall@{k} | fit AUC | wrong-pass@90% | top-1 (names) | "
        f"recall@{k} (names) | fit AUC (names) | s / full run |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in results:
        d, n = r["with_definitions"], r["names_only"]
        lines.append(
            f"| `{r['space_id']}` | {d['top1']:.2f} | {d[f'recall_at_{k}']:.2f} | "
            f"{d['fit_auc']:.3f} | {d['wrong_pass_at_90']:.2f} | {n['top1']:.2f} | "
            f"{n[f'recall_at_{k}']:.2f} | {n['fit_auc']:.3f} | {r['est_seconds_per_full_run']} |"
        )
    (args.out / "comparison.md").write_text("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
