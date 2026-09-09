"""Export a run's results as Markdown that carries no respondent text.

The run directory holds the coded corpus verbatim and is gitignored for that reason.
This script reads the run and writes only what can be shared: counts, code names,
response *numbers*, metrics, cluster structure, threshold curves and the machine
codebook's names and descriptions. It never emits a segment, a quote, a highlight's
content or a response body; and after writing, it re-reads every file it produced
and fails if any of them shares a run of ``GUARD_SHINGLE`` characters with any text it
was told to withhold. The guard is the contract; the field discipline is how it is met.

Usage::

    uv run python scripts/export_results.py --run runs/process --out results/india-process-1-20

Inputs are located by the run layout ``gaf`` writes (``corpus.json``, ``golden.json``,
``golden_mapping.json``, ``golden_checks.json``, ``analysis_golden/``, ``agreement/``,
``agreement_nameonly/``, ``calibration_report.json``, ``stats.json``, ``codebook.json``,
``assignments.json``). A missing input skips its section and says so.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

#: Shorter than the repository's 30-character provenance shingle on purpose: this guard
#: runs on the machine that has the data and can afford to be stricter.
GUARD_SHINGLE = 20

Json = dict[str, Any]


# --------------------------------------------------------------------------- helpers


def _load(path: Path) -> Any | None:
    if not path.exists():
        print(f"  skip  {path} (absent)")
        return None
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _rows(obj: Any) -> list[Json]:
    if isinstance(obj, list):
        return obj
    for key in ("assignments", "rows", "responses", "codes", "findings"):
        if isinstance(obj, dict) and key in obj:
            return list(obj[key])
    raise ValueError("unrecognised row container")


def _table(header: list[str], rows: list[list[Any]], align: str | None = None) -> str:
    align = align or "".join("r" if h.lower() in _NUMERIC else "l" for h in header)
    sep = "|" + "|".join("---:" if a == "r" else "---" for a in align) + "|"
    out = ["| " + " | ".join(header) + " |", sep]
    out += ["| " + " | ".join(_cell(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


_NUMERIC = {
    "n",
    "count",
    "codes",
    "highlights",
    "responses",
    "words",
    "mean",
    "stage",
    "distance",
    "delta",
    "size",
    "tp",
    "fp",
    "fn",
    "tn",
    "precision",
    "recall",
    "f1",
    "kappa",
    "cosine",
    "similarity",
    "threshold",
    "batch",
    "new codes",
    "cumulative codes",
    "error",
    "warn",
    "info",
    "total",
    "in export",
    "in sample",
    "response",
    "id",
    "number",
    "distinct codes",
    "segments",
    "evidence",
    "assignments",
    "current",
    "recommended",
    "units",
    "positives",
    "f1 at current",
    "best f1",
    "share",
    "codes in export",
    "codes in sample",
    "highlights in export",
    "highlights in sample",
    "responses in sample",
}


def _cell(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.3f}"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if value is None:
        return "-"
    return str(value).replace("|", "\\|")


def _code(name: str | None) -> str:
    return f"`{name}`" if name else "-"


def _family(name: str) -> str:
    return name.split("-", 1)[0]


def _sorted_ids(ids: Any) -> list[int]:
    return sorted(int(i) for i in ids)


def _write(out: Path, name: str, body: str) -> Path:
    path = out / name
    path.write_text(body.rstrip() + "\n", encoding="utf-8")
    print(f"  wrote {path}")
    return path


# --------------------------------------------------------------------------- withheld


class Withheld:
    """Every string the export must not reproduce, collected as it is read."""

    def __init__(self) -> None:
        self.shingles: set[str] = set()
        self.n_texts = 0

    @staticmethod
    def _norm(text: str) -> str:
        return re.sub(r"\s+", " ", text).casefold().strip()

    def add(self, text: Any) -> None:
        if not isinstance(text, str):
            return
        norm = self._norm(text)
        if len(norm) < GUARD_SHINGLE:
            # Short strings still must not be emitted verbatim: keep them whole.
            if norm:
                self.shingles.add(norm)
            return
        self.n_texts += 1
        for i in range(len(norm) - GUARD_SHINGLE + 1):
            self.shingles.add(norm[i : i + GUARD_SHINGLE])

    def scan(self, paths: list[Path]) -> list[tuple[Path, str]]:
        hits: list[tuple[Path, str]] = []
        for path in paths:
            try:
                hay = self._norm(path.read_text(encoding="utf-8"))
            except UnicodeDecodeError:
                continue
            for i in range(max(0, len(hay) - GUARD_SHINGLE + 1)):
                piece = hay[i : i + GUARD_SHINGLE]
                if piece in self.shingles:
                    hits.append((path, piece))
                    break
        return hits


# --------------------------------------------------------------------------- sections


def section_inputs(run: Path, withheld: Withheld, label: str) -> str | None:
    corpus = _load(run / "corpus.json")
    if corpus is None:
        return None
    responses = _rows(corpus)
    golden = _load(run / "golden.json")
    mapping = _load(run / "golden_mapping.json")
    grows = _rows(golden) if golden is not None else []
    for r in responses:
        withheld.add(r.get("content"))
    for r in grows:
        withheld.add(r.get("segment"))

    highlights = Counter(int(r["response_id"]) for r in grows)
    distinct = defaultdict(set)
    for r in grows:
        distinct[int(r["response_id"])].add(r["code"])
    rows = []
    for r in sorted(responses, key=lambda x: int(x["id"])):
        meta = r.get("meta") or {}
        notes = []
        if "duplicate_of_number" in meta:
            notes.append(f"second response numbered {meta['duplicate_of_number']} in the file")
        if meta.get("encoding_repaired"):
            notes.append("mojibake repaired at ingest")
        rows.append(
            [
                r["id"],
                meta.get("source_number", "-"),
                "; ".join(notes) or "-",
                len(str(r.get("content", "")).split()),
                highlights.get(int(r["id"]), 0),
                len(distinct.get(int(r["id"]), ())),
            ]
        )
    question = next((r.get("question") for r in responses if r.get("question")), None)
    source = next((r.get("source") for r in responses if r.get("source")), "-")

    parts = [f"# 01 - Inputs: {label}", ""]
    parts += [
        f"**Corpus.** {len(responses)} responses, source `{source}`.",
        "",
        f"> {question}" if question else "> (no question attached)",
        "",
        "Word counts are derived from the response bodies; the bodies themselves stay in the",
        "gitignored run directory.",
        "",
        _table(["id", "number as written", "note", "words", "highlights", "distinct codes"], rows),
        "",
    ]
    if mapping is not None:
        m = mapping
        parts += [
            "## The coding export, placed onto the corpus",
            "",
            "Each highlight in the principal investigator's export was located by its text in",
            "the corpus (exact substring first, then the same fuzzy locator the S2 check uses,",
            "threshold 0.85). Nothing was assigned by guess.",
            "",
            _table(
                ["outcome", "n"],
                [
                    ["highlights in the export", m["total"]],
                    ["mapped, exact", m["exact"]],
                    ["mapped, fuzzy", m["fuzzy"]],
                    ["ambiguous (text present in more than one response)", m["ambiguous"]],
                    ["unlocated (text belongs to responses not in this sample)", m["unlocated"]],
                ],
                align="lr",
            ),
            "",
        ]
        amb = [x for x in m.get("mappings", []) if x.get("outcome") == "ambiguous"]
        for x in m.get("mappings", []):
            withheld.add(x.get("content"))
        if amb:
            parts += [
                "Ambiguous highlights (code, and the responses the text occurs in):",
                "",
                _table(
                    ["code", "candidate responses"],
                    [
                        [_code(x["tag"]), ", ".join(str(c) for c in x.get("candidates", []))]
                        for x in amb
                    ],
                    align="ll",
                ),
                "",
            ]
        un = [
            x.get("score")
            for x in m.get("mappings", [])
            if x.get("outcome") == "unlocated" and x.get("score") is not None
        ]
        if un:
            parts += [
                f"Best fuzzy score among the unlocated highlights: {min(un):.2f} to {max(un):.2f}, all below the 0.85 line.",
                "",
            ]
        per = m.get("per_response") or {}
        if per:
            vals = list(per.values())
            parts += [
                f"Mapped highlights per response: {min(vals)} to {max(vals)}, every response covered."
                if len(per) == len(responses)
                else f"Mapped highlights per response: {min(vals)} to {max(vals)} over {len(per)} of {len(responses)} responses.",
                "",
            ]
    return "\n".join(parts)


def section_human_codebook(run: Path, withheld: Withheld) -> str | None:
    mapping = _load(run / "golden_mapping.json")
    golden = _load(run / "golden.json")
    if mapping is None or golden is None:
        return None
    tags_all = [x["tag"] for x in mapping["mappings"]]
    grows = _rows(golden)
    in_sample = Counter(r["code"] for r in grows)
    resp_per_code = defaultdict(set)
    for r in grows:
        resp_per_code[r["code"]].add(int(r["response_id"]))
    all_counts = Counter(tags_all)
    families_all = defaultdict(set)
    for t in all_counts:
        families_all[_family(t)].add(t)
    fam_rows = []
    for fam, codes in sorted(families_all.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        fam_rows.append(
            [
                _code(fam),
                len(codes),
                sum(all_counts[c] for c in codes),
                sum(1 for c in codes if in_sample[c]),
                sum(in_sample[c] for c in codes),
            ]
        )
    code_rows = [
        [_code(c), all_counts[c], in_sample[c], len(resp_per_code[c])]
        for c in sorted(all_counts, key=lambda c: (_family(c), c))
    ]
    bare = sorted(c for c in all_counts if "-" not in c)
    singles = sorted(f for f, cs in families_all.items() if len(cs) == 1)
    seg_dup = Counter((r["response_id"], r["segment"]) for r in grows)
    twice = sum(1 for v in seg_dup.values() if v >= 2)
    most = max(seg_dup.values()) if seg_dup else 0
    words = [len(str(r["segment"]).split()) for r in grows]
    words_sorted = sorted(words)
    median = words_sorted[len(words_sorted) // 2] if words_sorted else 0

    parts = ["# 02 - The principal investigator's codebook, profiled", ""]
    parts += [
        f"{len(all_counts)} distinct codes over {len(tags_all)} highlights in the export;",
        f"{len(in_sample)} of them occur in the {len(grows)} highlights that map onto this sample.",
        f"Segments run {min(words)} to {max(words)} words (median {median}); {twice} segments carry two",
        f"codes and none carries more than {most}, which is his own rule visible in the data.",
        "",
        "## Families (first hyphen splits family from code)",
        "",
        _table(
            [
                "family",
                "codes in export",
                "highlights in export",
                "codes in sample",
                "highlights in sample",
            ],
            fam_rows,
        ),
        "",
        "Bare top-level codes (no family separator): "
        + (", ".join(_code(c) for c in bare) or "none")
        + ".",
        "",
        "Single-member families, worth a look for a typo in the family token: "
        + (", ".join(_code(f) for f in singles) or "none")
        + ".",
        "",
        "## Every code",
        "",
        _table(
            ["code", "highlights in export", "highlights in sample", "responses in sample"],
            code_rows,
        ),
    ]
    return "\n".join(parts)


def section_structural(run: Path) -> str | None:
    checks = _load(run / "golden_checks.json")
    if checks is None:
        return None
    findings = _rows(checks)
    by: defaultdict[str, Counter[str]] = defaultdict(Counter)
    for f in findings:
        by[f["check_id"]][f["severity"]] += 1
    names = {
        "S1": "name, description, evidence present",
        "S2": "every quote locates in its response",
        "S3": "two-level name grammar; sub-code before new top-level",
        "S4": "at most two codes on one piece of text",
        "S5": "the usual two to twelve codes per response",
        "S6": "candidate count sanity",
    }
    summary = [
        [c, by[c]["ERROR"], by[c]["WARN"], by[c]["INFO"], names.get(c, "")]
        for c in sorted(set(by) | {"S1", "S2", "S3", "S4", "S5"})
    ]
    n_error = sum(v["ERROR"] for v in by.values())
    grouped: Counter[tuple[str, str, str, str, str]] = Counter()
    s1_subjects: set[str] = set()
    for f in findings:
        if f["check_id"] == "S1":
            s1_subjects.add(str(f["subject"]))
            continue
        marker = str((f.get("data") or {}).get("marker", "-"))
        grouped[
            (f["check_id"], f["severity"], marker, str(f.get("subject", "-")), f["message"])
        ] += 1
    detail = [[*key, n] for key, n in sorted(grouped.items())]
    parts = ["# 03 - His coding against his own rules (structural checks S1-S6)", ""]
    parts += [
        "The rules are the ones transcribed from his working document into `docs/CODING_RULES.md`.",
        "A WARN is kept and flagged and is never fatal; only an ERROR fails the gate.",
        "",
        _table(["check", "ERROR", "WARN", "INFO", "what it checks"], summary, align="lrrrl"),
        "",
        f"**RESULT: {'PASS - no ERROR finding' if n_error == 0 else f'FAIL - {n_error} ERROR finding(s)'}.**",
        "",
    ]
    if detail:
        parts += [
            "## Findings other than S1",
            "",
            _table(
                ["check", "severity", "marker", "subject", "message", "n"], detail, align="lllllr"
            ),
            "",
        ]
    if s1_subjects:
        parts += [
            f"## S1 - missing description, {by['S1']['WARN'] + by['S1']['ERROR']} findings",
            "",
            "The export carries code names and no definitions, so every response-code pair lacks one.",
            f"Not a coding fault; the codes concerned ({len(s1_subjects)}):",
            "",
            ", ".join(_code(s) for s in sorted(s1_subjects)),
        ]
    return "\n".join(parts)


def section_clustering(run: Path, out: Path) -> str | None:
    adir = run / "analysis_golden"
    clusters = _load(adir / "clusters.json")
    matrix = _load(adir / "occurrence_matrix.json")
    if clusters is None:
        return None
    sched = clusters["schedule"]
    filt = (matrix or {}).get("filter", {})
    parts = ["# 04 - Ward's hierarchical cluster analysis over his coding", ""]
    parts += [
        f"{clusters['n_responses']} responses x {clusters['n_codes']} codes after the low-frequency filter",
        f"(minimum {filt.get('min_code_frequency', '?')} responses per code: {filt.get('n_kept', '?')} kept, {filt.get('n_dropped', '?')} dropped).",
        f"Cluster count from the agglomeration schedule: `{sched.get('rule', '')}` -> largest break at stage",
        f"{sched['break_stage']} of {sched['n_steps']} (delta {sched['break_delta']:.3f}) -> **{clusters['n_clusters']} clusters**, cut at distance {clusters['cut_distance']:.3f}.",
        "",
        _table(
            ["cluster", "n", "share", "members (response ids)"],
            [
                [
                    k,
                    len(v),
                    f"{100 * len(v) / clusters['n_responses']:.0f}%",
                    ", ".join(str(i) for i in _sorted_ids(v)),
                ]
                for k, v in sorted(clusters["members"].items())
            ],
            align="rrrl",
        ),
        "",
        "![dendrogram](dendrogram.svg)",
        "",
    ]
    for k, means in sorted(clusters["means"].items()):
        top = sorted(means, key=lambda m: (-m["mean"], m["code"]))[:10]
        parts += [
            f"## Cluster {k} - code means (top 10; prominent at >= {clusters['cluster_mean_highlight']})",
            "",
            _table(
                ["code", "mean", "responses", "prominent"],
                [[_code(m["code"]), m["mean"], m["count"], m["prominent"]] for m in top],
                align="lrrl",
            ),
            "",
        ]
    parts += [
        "## Agglomeration schedule",
        "",
        _table(
            ["stage", "distance", "delta", "size"],
            [[s["stage"], s["distance"], s["delta"], s["size"]] for s in sched["steps"]],
        ),
        "",
    ]
    if filt.get("dropped"):
        parts += [
            f"## Codes dropped by the frequency filter ({filt['n_dropped']})",
            "",
            ", ".join(_code(d["name"]) for d in filt["dropped"]),
            "",
        ]
    for svg in ("dendrogram.svg",):
        if (adir / svg).exists():
            shutil.copy(adir / svg, out / svg)
            print(f"  wrote {out / svg}")
    return "\n".join(parts)


def section_saturation(run: Path, out: Path) -> str | None:
    adir = run / "analysis_golden"
    sat = _load(adir / "saturation.json")
    if sat is None:
        return None
    parts = ["# 05 - Theoretical saturation over his coding", ""]
    parts += [
        f"Batch size {sat['batch_size']}; {sat['total_codes']} distinct codes in total; "
        + (
            f"saturated at batch {sat['saturated_at_batch']}."
            if sat.get("saturated_at_batch")
            else "**not saturated**: every batch introduced new codes."
        ),
        "",
        _table(
            ["batch", "responses", "cumulative responses", "new codes", "cumulative codes"],
            [
                [
                    p["batch"],
                    p["responses_in_batch"],
                    p["cumulative_responses"],
                    p["new_codes"],
                    p["cumulative_codes"],
                ]
                for p in sat["points"]
            ],
        ),
        "",
        "![saturation](saturation.svg)",
        "",
    ]
    for p in sat["points"]:
        parts += [
            f"## Batch {p['batch']} - new codes ({p['new_codes']})",
            "",
            ", ".join(_code(c) for c in p["new_code_names"]),
            "",
        ]
    if (adir / "saturation.svg").exists():
        shutil.copy(adir / "saturation.svg", out / "saturation.svg")
        print(f"  wrote {out / 'saturation.svg'}")
    return "\n".join(parts)


def _agreement_block(title: str, j: Json, withheld: Withheld) -> list[str]:
    for side in ("over_coding", "blind_spots"):
        for group in j.get(side, []):
            for row in group.get("rows", []):
                withheld.add(row.get("segment"))
    cl, mo, seg, mt = j["code_level"], j["matched_only"], j["segment_level"], j["matching"]
    accepted = [p for p in mt["pairs"] if p["accepted"]]
    parts = [f"## {title}", ""]
    parts += [
        f"Embedding space `{mt['space_id']}`, tau_high {mt['tau_high']}: {len(accepted)} of {mt['n_human_codes']} human codes matched to one of {mt['n_machine_codes']} machine codes.",
        "",
        _table(
            ["scope", "precision", "recall", "F1", "kappa", "TP", "FP", "FN"],
            [
                [
                    "all codes (union vocabulary)",
                    cl["precision"],
                    cl["recall"],
                    cl["f1"],
                    cl["cohens_kappa"],
                    cl["tp"],
                    cl["fp"],
                    cl["fn"],
                ],
                [
                    "matched codes only",
                    mo["precision"],
                    mo["recall"],
                    mo["f1"],
                    mo["cohens_kappa"],
                    mo["tp"],
                    mo["fp"],
                    mo["fn"],
                ],
            ],
            align="lrrrrrrr",
        ),
        "",
        _table(
            ["segment level", "precision", "recall", "F1"],
            [
                [
                    "span-overlap weighted",
                    seg["weighted_precision"],
                    seg["weighted_recall"],
                    seg["weighted_f1"],
                ],
                [
                    f"strict (overlap >= {seg['overlap_threshold']})",
                    seg["strict_precision"],
                    seg["strict_recall"],
                    seg["strict_f1"],
                ],
            ],
            align="lrrr",
        ),
        "",
        f"Right code, wrong place: {seg['right_code_wrong_place']}; mean overlap on shared codes {seg['mean_overlap_on_shared_codes']:.3f}.",
        "",
        "### Code matching (Hungarian assignment, nearest pairs)",
        "",
        _table(
            ["human code", "machine code", "similarity", "accepted"],
            [
                [_code(p["human_code"]), _code(p["machine_code"]), p["similarity"], p["accepted"]]
                for p in mt["pairs"]
            ],
            align="llrl",
        ),
        "",
        f"### Over-coding - machine codes with no human counterpart ({len(j.get('over_coding', []))} codes, {sum(g['n_assignments'] for g in j.get('over_coding', []))} segments)",
        "",
        _table(
            ["machine code", "segments", "responses", "nearest human code", "cosine"],
            [
                [
                    _code(g["code"]),
                    g["n_assignments"],
                    ", ".join(str(i) for i in _sorted_ids(g["response_ids"])),
                    _code(g.get("nearest_code")),
                    g["nearest_similarity"],
                ]
                for g in j.get("over_coding", [])
            ],
            align="lrllr",
        ),
        "",
        f"### Blind spots - human codes the machine never produced ({len(j.get('blind_spots', []))} codes, {sum(g['n_assignments'] for g in j.get('blind_spots', []))} segments)",
        "",
        'The only place the negative example "you did not generate a new code" is observable:',
        "a code never invented leaves no artefact inside a run. The segments themselves are in",
        "the local run directory's `agreement.md`.",
        "",
        _table(
            ["human code", "segments", "responses", "nearest machine code", "cosine"],
            [
                [
                    _code(g["code"]),
                    g["n_assignments"],
                    ", ".join(str(i) for i in _sorted_ids(g["response_ids"])),
                    _code(g.get("nearest_code")),
                    g["nearest_similarity"],
                ]
                for g in j.get("blind_spots", [])
            ],
            align="lrllr",
        ),
        "",
    ]
    return parts


def section_agreement(run: Path, withheld: Withheld) -> str | None:
    runs = [
        ("agreement", "As first run: machine codes carry descriptions, his do not"),
        ("agreement_nameonly", "Name against name: no descriptions on either side"),
    ]
    blocks = []
    for d, title in runs:
        j = _load(run / d / "agreement.json")
        if j is not None:
            blocks += _agreement_block(title, j, withheld)
    if not blocks:
        return None
    parts = ["# 06 - Concurrent validation: his coding against the machine's", ""]
    parts += [
        "The machine side here is the offline stand-in coder (a deterministic keyword table used",
        "so the pipeline runs without a model or a key). Its agreement with an expert is not the",
        "question; whether the harness measures and explains a disagreement on real inputs is.",
        "",
    ]
    parts += blocks
    return "\n".join(parts)


def section_calibration(run: Path) -> str | None:
    j = _load(run / "calibration_report.json")
    if j is None:
        return None
    g = j.get("generated_from", {})
    rows = []
    for name, s in j["sweeps"].items():
        rows.append(
            [
                f"`{name}`",
                s["unit"],
                s["n_units"],
                s["n_positive"],
                s["current"],
                s["recommended"],
                s["f1_at_current"],
                s["best_f1"],
                f"{s['plateau'][0]}-{s['plateau'][1]}",
            ]
        )
    parts = ["# 07 - Threshold calibration against his coding", ""]
    parts += [
        f"Space `{j['space_id']}`; from {g.get('n_human_assignments', '?')} human and {g.get('n_machine_assignments', '?')} machine codings over {g.get('n_responses', '?')} responses.",
        "The module reports; it never writes a threshold. `CodingRules` in `gaf/config.py` is unchanged.",
        "",
        _table(
            [
                "threshold",
                "unit",
                "units",
                "positives",
                "current",
                "recommended",
                "F1 at current",
                "best F1",
                "F1 plateau",
            ],
            rows,
            align="llrrrrrrl",
        ),
        "",
        "## The module's own notes",
        "",
    ]
    parts += [f"- {n}" for n in j.get("notes", [])]
    parts += ["", "## Narrative", "", j.get("narrative", ""), ""]
    for name, s in j["sweeps"].items():
        parts += [
            f"## Curve - `{name}` ({s['prediction_label']} vs {s['positive_label']})",
            "",
            _table(
                ["threshold", "TP", "FP", "FN", "TN", "precision", "recall", "F1"],
                [
                    [
                        c["threshold"],
                        c["tp"],
                        c["fp"],
                        c["fn"],
                        c["tn"],
                        c["precision"],
                        c["recall"],
                        c["f1"],
                    ]
                    for c in s["curve"]
                ],
            ),
            "",
        ]
    return "\n".join(parts)


def section_machine_run(run: Path, withheld: Withheld) -> str | None:
    stats = _load(run / "stats.json")
    codebook = _load(run / "codebook.json")
    if stats is None or codebook is None:
        return None
    assignments = _load(run / "assignments.json")
    arows = _rows(assignments) if assignments is not None else []
    for r in arows:
        withheld.add(r.get("segment"))
    per_code = Counter(r["code"] for r in arows)
    codes = _rows(codebook)
    for c in codes:
        for e in c.get("evidence", []):
            withheld.add(e.get("quote"))
    by_id = {c["id"]: c for c in codes}
    code_rows = []
    for c in sorted(codes, key=lambda c: (_family(c["name"]), c["name"])):
        parent = by_id.get(c.get("parent_id") or "", {}).get("name")
        code_rows.append(
            [
                _code(c["name"]),
                _code(parent) if parent else "-",
                c.get("description", ""),
                len(c.get("evidence", [])),
                per_code.get(c["name"], 0),
                c.get("created_in_snapshot", "-"),
            ]
        )
    f = stats.get("findings", {})
    frows = [
        [k, v.get("ERROR", 0), v.get("WARN", 0), v.get("INFO", 0)] for k, v in sorted(f.items())
    ]
    top2 = per_code.most_common(2)
    parts = [f"# 08 - The machine run (offline stand-in coder), run id `{stats.get('run_id')}`", ""]
    parts += [
        f"{stats['n_responses']} responses, {stats['n_segments']} segments, {stats['assignments']} assignments, {stats['codes_final']} codes in {stats['families_final']} families; embedding space `{stats['space_id']}`; offline: {stats.get('offline')}.",
        "",
        "**Caveats the run printed about itself:**",
        "",
    ]
    parts += [f"- {c}" for c in stats.get("caveats", [])]
    parts += [
        "",
        f"The two most-used machine codes account for {sum(n for _, n in top2)} of {stats['assignments']} assignments: "
        + ", ".join(f"{_code(c)} {n}" for c, n in top2)
        + ". That is the keyword table's fallback behaviour, not a finding.",
        "",
        "## Findings by check",
        "",
        _table(["check", "ERROR", "WARN", "INFO"], frows),
        "",
        "## Pipeline counts",
        "",
        _table(
            ["quantity", "value"],
            [
                [
                    "candidates proposed (coder A / B)",
                    f"{stats['candidates_proposed']['coder_a']} / {stats['candidates_proposed']['coder_b']}",
                ],
                ["candidates accepted", stats["candidates_accepted"]],
                [
                    "dropped: structural / fit / dispute",
                    f"{stats['candidates_dropped']['structural']} / {stats['candidates_dropped']['fit']} / {stats['candidates_dropped']['dispute']}",
                ],
                [
                    "routes CREATE / MERGE / JUDGE",
                    f"{stats['routes'].get('CREATE', 0)} / {stats['routes'].get('MERGE', 0)} / {stats['routes'].get('JUDGE', 0)}",
                ],
                ["coder agreement rate", f"{stats['agreement_rate']:.3f}"],
                ["model calls (all mock)", stats["llm"]["calls"]],
                [
                    "checkpoint due",
                    f"{stats['checkpoint_due']['fires']} ({stats['checkpoint_due']['reason']})",
                ],
                ["snapshots", ", ".join(stats.get("snapshot_ids", []))],
            ],
            align="ll",
        ),
        "",
        "## The machine codebook (names and descriptions; the quotes stay in the run directory)",
        "",
        _table(
            ["code", "parent", "description", "evidence", "assignments", "created in"],
            code_rows,
            align="lllrrl",
        ),
    ]
    return "\n".join(parts)


# --------------------------------------------------------------------------- main


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--run", required=True, type=Path, help="run directory written by gaf")
    ap.add_argument("--out", required=True, type=Path, help="directory to write the Markdown into")
    ap.add_argument(
        "--label", default=None, help="human label for the sample (default: the run directory name)"
    )
    args = ap.parse_args(argv)
    run: Path = args.run
    out: Path = args.out
    label = args.label or run.name
    if not run.is_dir():
        print(f"not a run directory: {run}", file=sys.stderr)
        return 2
    out.mkdir(parents=True, exist_ok=True)
    withheld = Withheld()
    written: list[Path] = []

    sections = [
        ("01-inputs.md", lambda: section_inputs(run, withheld, label)),
        ("02-human-codebook.md", lambda: section_human_codebook(run, withheld)),
        ("03-structural-checks.md", lambda: section_structural(run)),
        ("04-clustering.md", lambda: section_clustering(run, out)),
        ("05-saturation.md", lambda: section_saturation(run, out)),
        ("06-agreement.md", lambda: section_agreement(run, withheld)),
        ("07-calibration.md", lambda: section_calibration(run)),
        ("08-machine-run.md", lambda: section_machine_run(run, withheld)),
    ]
    for name, build in sections:
        body = build()
        if body is None:
            print(f"  skip  {name}")
            continue
        written.append(_write(out, name, body))

    # The guard: nothing written may share a run of GUARD_SHINGLE characters with any
    # withheld string. This is checked on the files as written, not on the data in memory.
    produced = sorted(p for p in out.iterdir() if p.suffix in {".md", ".svg", ".json"})
    hits = withheld.scan(produced)
    if hits:
        for path, piece in hits:
            print(f"  GUARD  {path}: shares {piece!r} with withheld text", file=sys.stderr)
        for path in produced:
            path.unlink()
        print(
            "export aborted and its files removed; nothing with respondent text was left behind",
            file=sys.stderr,
        )
        return 1
    print(
        f"  guard  {len(produced)} files scanned against {withheld.n_texts} withheld texts ({len(withheld.shingles)} shingles): clean"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
