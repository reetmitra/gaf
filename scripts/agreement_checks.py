"""Three cheap checks on a run's agreement with the PI, from files the run already wrote.

usage: uv run python scripts/agreement_checks.py RUN_DIR [RUN_DIR ...] [--human runs/human200-v2]

For each run and each matching variant (`agreement`, `agreement_nameonly`) it reads the
agreement report `agreement.py` wrote, the run's assignments and the PI's coding, and
prints and saves (`RUN_DIR/agreement_checks.json`) numbers only, never a segment:

* **code level, with an interval**: kappa and F1 over response-by-code cells on the held-out
  fold, with a percentile bootstrap over the responses (the fold is 19 responses, so a
  point value says little).
* **family level**: every machine code is rolled up to the PI family of its *nearest* PI
  code (whether or not the match was accepted), and the PI's codes to their families, so
  cells are response-by-family (15 families). The generous reading of "do they find the
  same themes".
* **a chance reference**: the same statistic when the machine's per-response code sets are
  dealt to the responses at random (a permutation test), so a figure can be read against
  what no relationship at all would give.

No model is called. The statistics are plain counts over sets, so they are exact and
reproducible given the seed.
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
from pathlib import Path

N_RESAMPLES = 5000
SEED = 20261105


def cell_stats(tp: int, fp: int, fn: int, n_cells: int) -> dict[str, float]:
    """Cohen's kappa and F1 of a 2x2 table over `n_cells` cells."""
    tn = n_cells - tp - fp - fn
    po = (tp + tn) / n_cells
    pe = ((tp + fp) * (tp + fn) + (fn + tn) * (fp + tn)) / n_cells**2
    kappa = 0.0 if pe == 1 else (po - pe) / (1 - pe)
    f1 = 0.0 if tp == 0 else 2 * tp / (2 * tp + fp + fn)
    return {"kappa": kappa, "f1": f1, "tp": tp, "fp": fp, "fn": fn}


def per_response(human: dict[str, set[str]], machine: dict[str, set[str]]) -> dict[str, tuple[int, int, int]]:
    return {
        r: (len(human[r] & machine[r]), len(machine[r] - human[r]), len(human[r] - machine[r])) for r in human
    }


def table(rows: list[tuple[int, int, int]], n_codes: int) -> dict[str, float]:
    tp, fp, fn = (sum(x[i] for x in rows) for i in range(3))
    return cell_stats(tp, fp, fn, len(rows) * n_codes)


def percentile(xs: list[float], q: float) -> float:
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * len(xs)))]


def interval_and_chance(
    human: dict[str, set[str]], machine: dict[str, set[str]], n_codes: int, rng: random.Random
) -> dict[str, object]:
    """Point value, bootstrap interval over responses, and permutation chance level."""
    ids = sorted(human)
    rows = per_response(human, machine)
    point = table([rows[r] for r in ids], n_codes)
    # A trivial predictor that never reads a response: give every response the k codes the
    # PI used most across the fold (k = the machine's mean codes per response), which is
    # optimistic for the trivial side because it is told the PI's own totals.
    top = round(statistics.fmean(len(machine[r]) for r in ids))
    freq = sorted({c for r in ids for c in human[r]}, key=lambda c: (-sum(c in human[r] for r in ids), c))
    trivial_rows = per_response(human, {r: set(freq[:top]) for r in ids})
    boot, gap = [], []
    for _ in range(N_RESAMPLES):
        pick = [rng.choice(ids) for _ in ids]
        mine, triv = table([rows[r] for r in pick], n_codes), table([trivial_rows[r] for r in pick], n_codes)
        boot.append(mine)
        gap.append({m: mine[m] - triv[m] for m in ("kappa", "f1")})
    chance = []
    for _ in range(N_RESAMPLES):
        dealt = ids[:]
        rng.shuffle(dealt)
        chance.append(table(list(per_response(human, {r: machine[d] for r, d in zip(ids, dealt, strict=True)}).values()), n_codes))
    trivial = table([trivial_rows[r] for r in ids], n_codes)
    out: dict[str, object] = {"point": point, "n_responses": len(ids), "n_codes": n_codes, "trivial_top_k": trivial, "k": top}
    for k in ("kappa", "f1"):
        out[f"{k}_ci95"] = [percentile([b[k] for b in boot], 0.025), percentile([b[k] for b in boot], 0.975)]
        out[f"{k}_minus_trivial_ci95"] = [percentile([g[k] for g in gap], 0.025), percentile([g[k] for g in gap], 0.975)]
        out[f"{k}_chance_mean"] = statistics.fmean(c[k] for c in chance)
        out[f"{k}_chance_p95"] = percentile([c[k] for c in chance], 0.95)
        out[f"{k}_p_at_least"] = sum(c[k] >= point[k] for c in chance) / N_RESAMPLES
    return out


def load_sets(run: Path, human_dir: Path, fold: set[str], variant: str) -> dict[str, object]:
    report = json.loads((run / variant / "agreement.json").read_text(encoding="utf-8"))
    pairs = report["matching"]["pairs"]
    accepted = {p["machine_code"]: p["human_code"] for p in pairs if p["accepted"]}
    nearest = {p["machine_code"]: p["human_code"] for p in pairs}
    codebook = json.loads((human_dir / "codebook.json").read_text(encoding="utf-8"))["codes"]
    by_id = {c["id"]: c for c in codebook}
    family = {c["name"]: by_id[c["parent_id"]]["name"] if c["parent_id"] else c["name"] for c in codebook}
    families = sorted({c["name"] for c in codebook if c["parent_id"] is None})

    def sets(rows: list[dict[str, object]], rename) -> dict[str, set[str]]:  # type: ignore[no-untyped-def]
        out: dict[str, set[str]] = {r: set() for r in fold}
        for row in rows:
            r = str(row["response_id"])
            if r in out:
                out[r].add(rename(str(row["code"])))
        return out

    h_rows = json.loads((human_dir / "golden.json").read_text(encoding="utf-8"))
    m_rows = json.loads((run / "assignments.json").read_text(encoding="utf-8"))
    human_codes = sets(h_rows, lambda c: c)
    machine_codes = sets(m_rows, lambda c: accepted.get(c, c))
    return {
        "code": (human_codes, machine_codes, report["code_level"]["n_codes"]),
        "family": (
            sets(h_rows, lambda c: family[c]),
            sets(m_rows, lambda c: family[nearest[c]] if c in nearest else c),
            len(families),
        ),
        "reported": report["code_level"],
    }


def figure(results: dict[str, dict[str, dict[str, object]]]) -> str:
    """One SVG: kappa with its 95% bootstrap interval for every run, code level beside family level.

    A filled dot is the machine; an open circle is the permutation chance mean; a diamond is the
    trivial predictor that gives every response the PI's most common codes.
    """
    rows = list(results)
    w, left, pw, top, rh = 880, 190, 300, 70, 30
    h = top + rh * len(rows) + 50
    lo, hi = -0.2, 0.8

    def x(v: float, panel: int) -> float:
        return left + panel * (pw + 40) + (min(max(v, lo), hi) - lo) / (hi - lo) * pw

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-label="Agreement with the PI: kappa with intervals, code level and family level">',
        "<style>:root{--bg:#fcfcfb;--ink:#0b0b0b;--mute:#898781;--grid:#e1e0d9;--s1:#2a78d6;--s2:#eb6834}"
        "@media (prefers-color-scheme:dark){:root{--bg:#1a1a19;--ink:#f0efec;--grid:#2c2c2a;--s1:#3987e5;--s2:#d95926}}"
        ".bg{fill:var(--bg)}text{fill:var(--ink);font:12px system-ui,-apple-system,Helvetica,Arial,sans-serif}"
        ".m{fill:var(--mute)}.g{stroke:var(--grid)}.ci{stroke:var(--s1);stroke-width:2}.dot{fill:var(--s1)}"
        ".ch{fill:none;stroke:var(--mute);stroke-width:1.5}.tr{fill:var(--s2)}</style>",
        f'<rect class="bg" width="{w}" height="{h}"/>',
        '<text x="16" y="24" font-weight="600" font-size="15">Agreement with the PI, held-out fold (kappa, 95% interval)</text>',
        '<text class="m" x="16" y="44">dot = machine  |  open circle = chance with responses shuffled  |  diamond = a predictor that gives every response the PI\'s most common codes</text>',
    ]
    for panel, (key, title) in enumerate((("agreement.code", "Leaf codes (116)"), ("agreement.family", "Families (15)"))):
        out.append(f'<text x="{x(lo, panel)}" y="{top - 8}" font-weight="600">{title}</text>')
        for tick in (0.0, 0.2, 0.4, 0.6):
            out.append(f'<line class="g" x1="{x(tick, panel)}" x2="{x(tick, panel)}" y1="{top}" y2="{top + rh * len(rows)}"/>')
            out.append(f'<text class="m" x="{x(tick, panel) - 8}" y="{top + rh * len(rows) + 16}">{tick:g}</text>')
        for i, run in enumerate(rows):
            res = results[run][key]
            y = top + rh * i + rh / 2
            p, ci = res["point"], res["kappa_ci95"]  # type: ignore[index]
            if panel == 0:
                out.append(f'<text x="{left - 10}" y="{y + 4}" text-anchor="end">{run}</text>')
            out.append(f'<line class="ci" x1="{x(ci[0], panel)}" x2="{x(ci[1], panel)}" y1="{y}" y2="{y}"/>')
            out.append(f'<circle class="dot" cx="{x(p["kappa"], panel)}" cy="{y}" r="4.5"/>')
            out.append(f'<circle class="ch" cx="{x(res["kappa_chance_mean"], panel)}" cy="{y}" r="4.5"/>')  # type: ignore[arg-type]
            tx, ty = x(res["trivial_top_k"]["kappa"], panel), y  # type: ignore[index]
            out.append(f'<path class="tr" d="M{tx} {ty - 5}L{tx + 5} {ty}L{tx} {ty + 5}L{tx - 5} {ty}Z"/>')
    out.append("</svg>")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", nargs="+", type=Path)
    ap.add_argument("--human", type=Path, default=Path("runs/human200-v2"))
    ap.add_argument("--svg", type=Path, help="also draw the kappa figure for the with-descriptions variant")
    args = ap.parse_args()
    split = json.loads((args.human / "split.json").read_text(encoding="utf-8"))
    fold = {str(i) for i in split["held_out"]}
    drawn: dict[str, dict[str, dict[str, object]]] = {}
    for run in args.runs:
        result: dict[str, object] = {}
        for variant in ("agreement", "agreement_nameonly"):
            if not (run / variant / "agreement.json").exists():
                continue
            loaded = load_sets(run, args.human, fold, variant)
            rep = loaded["reported"]
            for level in ("code", "family"):
                h, m, n = loaded[level]  # type: ignore[misc]
                res = interval_and_chance(h, m, n, random.Random(SEED))
                if level == "code":  # the reproduction must match the pipeline's own report
                    got = res["point"]
                    assert (got["tp"], got["fp"], got["fn"]) == (rep["tp"], rep["fp"], rep["fn"]), (run, variant, got, rep)  # type: ignore[index]
                result[f"{variant}.{level}"] = res
        (run / "agreement_checks.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
        if "agreement.code" in result:
            drawn[run.name.removeprefix("local-")] = result  # type: ignore[assignment]
        print(f"== {run.name}")
        for key, res in result.items():
            p = res["point"]  # type: ignore[index]
            print(
                f"  {key:28s} kappa {p['kappa']:+.3f} [{res['kappa_ci95'][0]:+.3f},{res['kappa_ci95'][1]:+.3f}]"  # type: ignore[index]
                f" chance {res['kappa_chance_mean']:+.3f} (p>= {res['kappa_p_at_least']:.3f})"  # type: ignore[index]
                f" trivial F1 {res['trivial_top_k']['f1']:.3f}/k {res['trivial_top_k']['kappa']:+.3f}"  # type: ignore[index]
                f" gap F1 [{res['f1_minus_trivial_ci95'][0]:+.3f},{res['f1_minus_trivial_ci95'][1]:+.3f}]"  # type: ignore[index]
                f" | F1 {p['f1']:.3f} [{res['f1_ci95'][0]:.3f},{res['f1_ci95'][1]:.3f}] tp {p['tp']} fp {p['fp']} fn {p['fn']}"  # type: ignore[index]
            )
    if args.svg and drawn:
        args.svg.write_text(figure(drawn), encoding="utf-8")
        print(f"wrote {args.svg}")


if __name__ == "__main__":
    main()
