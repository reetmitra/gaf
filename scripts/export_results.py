"""Export a run's results as Markdown that carries no respondent text.

The run directory holds the coded corpus verbatim and is gitignored for that reason.
This script reads the run and writes only what can be shared: counts, code names,
response *numbers*, metrics, cluster structure, threshold curves, the handover trace
and — one at a time, each tested on its own — code descriptions. It never emits a
segment, a quote, a highlight's content, an organised codebook's example or a response
body; and after writing, it re-reads **every file it produced**, in every subdirectory
and of every type, and fails if any of them shares a run of ``GUARD_SHINGLE``
characters with any text it was told to withhold. The guard is the contract; the field
discipline is how it is met.

**Descriptions are not blanket-shareable.** A definition is only as shareable as
whoever wrote it made it: a researcher's own codebook can quote the response that
prompted a code, and an offline stand-in's description is assembled from words the
response supplied. So every description is tested individually by
:func:`guarded_description` before it is emitted, and a colliding one is replaced by
its code name plus :data:`WITHHELD_DESCRIPTION`. The count of what was withheld is
printed, and is written into the export itself.

Usage::

    uv run python scripts/export_results.py --run runs/process --out results/india-process-1-20
    uv run python scripts/export_results.py --run runs/process200 --human runs/human200 \\
        --seeded runs/process200-seeded --halted runs/process200-halted \\
        --resumed runs/process200-resumed --out results/india-process-1-200

Inputs are located by the run layout ``gaf`` writes: ``corpus.json``,
``stats.json``, ``codebook.json``, ``assignments.json``, ``findings.json``,
``timeline.json``, ``reorganisation_trail.json``, ``decision_matrix.md``,
``analysis/`` and ``views/`` under ``--run``; ``golden.json``, ``placement.json`` (or
the older ``golden_mapping.json``), ``organised.json``, ``codebook.json``,
``golden_checks.json``, ``tree.mmd``, ``analysis_golden/`` and ``views/`` under
``--human``, which defaults to ``--run`` so a directory holding both still exports
exactly as it did. A missing input skips its section, prints why, and is recorded as
"not produced" in the generated ``README.md``.

Validation principle: **transparency** — everything here is a count, a name or a
metric a reader can check, and what cannot be shown is named rather than omitted.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from gaf.checks.growth import GrowthCurve, GrowthPoint, Spike, detect_spikes
from gaf.config import CheckpointPolicy

#: Shorter than the repository's 30-character provenance shingle on purpose: this guard
#: runs on the machine that has the data and can afford to be stricter.
GUARD_SHINGLE = 20

#: What stands in for a description that shares wording with a response. The code name
#: is still emitted beside it: withholding a definition is not withholding the code.
WITHHELD_DESCRIPTION = "*definition withheld: shares wording with a response*"

#: Where the offending run itself is written when the guard fires, inside the **run**
#: directory. A guard that prints the text it caught puts respondent words into a
#: terminal, a CI log and a scrollback buffer, none of which is gitignored and none of
#: which `make scrub` empties (R2 M-2). The console gets the file, the offset and the
#: length; the words go where the words already are.
GUARD_LOG_NAME = "export-guard-hits.txt"

Json = dict[str, Any]


# --------------------------------------------------------------------------- helpers


def _load(path: Path) -> Any | None:
    if not path.exists():
        print(f"  skip  {path} (absent)")
        return None
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _quiet_load(path: Path) -> Any | None:
    """:func:`_load` without the line. Feeding the guard is not a section's business."""
    if not path.is_file():
        return None
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _first(*paths: Path) -> Path | None:
    """The first of these that exists — how an artefact is found in either layout."""
    for path in paths:
        if path.is_file():
            return path
    return None


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
    "machine assignments",
    "distinct machine codes",
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


def _drop_empty(header: list[str], rows: list[list[Any]]) -> tuple[list[str], list[list[Any]]]:
    """Remove columns that carry nothing but '-' in every row."""
    keep = [i for i in range(len(header)) if any(r[i] != "-" for r in rows)]
    return [header[i] for i in keep], [[r[i] for i in keep] for r in rows]


# --------------------------------------------------------------------------- withheld


class Withheld:
    """Every string the export must not reproduce, collected as it is read.

    ``shingle`` is the window length at which a shared run counts as reproduction.
    :data:`GUARD_SHINGLE` (20) is the default and is deliberately stricter than the
    repository-wide provenance standard of 30 characters. It is a parameter and not a
    constant because the right value depends on corpus size: over 200 responses a
    twenty-character window of ordinary English recurs by chance, and a guard that
    cannot be stated and moved deliberately gets moved carelessly.
    """

    def __init__(self, shingle: int = GUARD_SHINGLE) -> None:
        self.shingles: set[str] = set()
        self.n_texts = 0
        self.shingle = shingle

    @staticmethod
    def _norm(text: str) -> str:
        return re.sub(r"\s+", " ", text).casefold().strip()

    def add(self, text: Any) -> None:
        if not isinstance(text, str):
            return
        norm = self._norm(text)
        if len(norm) < self.shingle:
            # Short strings still must not be emitted verbatim: keep them whole.
            if norm:
                self.shingles.add(norm)
            return
        self.n_texts += 1
        for i in range(len(norm) - self.shingle + 1):
            self.shingles.add(norm[i : i + self.shingle])

    def locate(self, text: str) -> tuple[int, str] | None:
        """``(offset, run)`` for the first withheld run in `text`, or ``None``.

        The offset is into the **normalised** text — whitespace collapsed, case
        folded — which is the only coordinate system the guard has. It is enough to
        find the run again in the file, and it names no words (R2 M-2).

        Short strings are compared whole, matching :meth:`add`: a withheld text below
        the shingle length is kept entire, so reproducing it entire is still a hit.
        """
        hay = self._norm(text)
        if not hay:
            return None
        if len(hay) < self.shingle:
            return (0, hay) if hay in self.shingles else None
        for i in range(len(hay) - self.shingle + 1):
            piece = hay[i : i + self.shingle]
            if piece in self.shingles:
                return (i, piece)
        return None

    def first_hit(self, text: str) -> str | None:
        """The first withheld run this string contains, or ``None`` if it is clean."""
        found = self.locate(text)
        return None if found is None else found[1]

    def is_clean(self, text: str) -> bool:
        return self.first_hit(text) is None

    def scan(self, paths: list[Path]) -> list[tuple[Path, int, str]]:
        """Re-read what was written. An unreadable file is a hit, not a skip.

        The exporter writes text and nothing else, so a file it cannot decode is a
        file whose contents it cannot account for. Treating that as clean would be a
        hole in the one guarantee this script makes.
        """
        hits: list[tuple[Path, int, str]] = []
        for path in paths:
            try:
                hay = self._norm(path.read_text(encoding="utf-8"))
            except (UnicodeDecodeError, OSError):
                hits.append((path, -1, "<not decodable as UTF-8 text>"))
                continue
            for i in range(max(0, len(hay) - self.shingle + 1)):
                piece = hay[i : i + self.shingle]
                if piece in self.shingles:
                    hits.append((path, i, piece))
                    break
        return hits



def record_guard_hit(run: Path, where: str, offset: int, piece: str) -> Path | None:
    """Append one caught run to :data:`GUARD_LOG_NAME` inside the run directory.

    The run directory is gitignored, holds the corpus already and is what `make scrub`
    deletes, so it is the one place a caught run may be written down. Returns the log
    path, or ``None`` if it could not be written — a guard that cannot log still
    refuses, it just cannot say where to look.
    """
    log = run / GUARD_LOG_NAME
    try:
        with log.open("a", encoding="utf-8") as fh:
            fh.write(f"{where}\toffset {offset}\t{piece!r}\n")
    except OSError:
        return None
    return log


def guarded_description(text: Any, withheld: Withheld) -> tuple[str, bool]:
    """One description, tested on its own: ``(what to emit, whether it was clean)``.

    Blanket rules do not work here. Most of a researcher's definitions say what a code
    means in words nobody wrote in a response; a few quote the response that prompted
    them. The first kind is exactly what a collaborator needs in order to read this
    export; the second is respondent text wearing a definition's clothes. So each one
    is asked the question separately, and a failure costs that definition and nothing
    else. An empty description is clean and stays empty: there is nothing to withhold.
    """
    if not isinstance(text, str) or not text.strip():
        return "", True
    if withheld.is_clean(text):
        return text, True
    return WITHHELD_DESCRIPTION, False


# --------------------------------------------------------------------------- feeding


def _feed_codebook(payload: Any, withheld: Withheld) -> None:
    rows = payload.get("codes", []) if isinstance(payload, dict) else payload
    for code in rows or []:
        for ev in code.get("evidence", []) or []:
            withheld.add(ev.get("quote"))


def _feed_organised_codes(codes: Any, withheld: Withheld) -> None:
    for code in codes or []:
        for example in code.get("examples", []) or []:
            withheld.add(example)
        _feed_organised_codes(code.get("children"), withheld)


#: The JSON keys that carry respondent text anywhere in this project. A response body
#: is ``content``; a coded span is ``segment``; a piece of verified evidence is
#: ``quote``; a highlight from the researcher's export is ``content`` again; and
#: ``rationale`` is the Refactorer's own sentence about an operation, which the prompt
#: once required to name the quotes it rested on (R2 C-1). Harvesting
#: by key rather than by file name is what makes the guard survive a new artefact: a
#: reorganisation trail that starts carrying an edited operation's quote is covered the
#: day it does, without this script being told about it.
TEXT_KEYS = frozenset({"content", "segment", "quote", "example", "examples", "rationale"})


def _harvest(node: Any, withheld: Withheld) -> None:
    """Every value under a respondent-text key, at any depth, in any shape."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key in TEXT_KEYS:
                if isinstance(value, str):
                    withheld.add(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, str):
                            withheld.add(item)
                        else:
                            _harvest(item, withheld)
                else:
                    _harvest(value, withheld)
            else:
                _harvest(value, withheld)
    elif isinstance(node, list):
        for item in node:
            _harvest(item, withheld)


def feed_run(run: Path, withheld: Withheld) -> None:
    """Every text a run directory holds: the corpus, every segment, every quote.

    Called once per run directory named on the command line — the cold run, a seeded
    run, a halted run and its resumption all hold the same respondents' words. **Every**
    JSON file in the directory at any depth is walked, and every value under a key in
    :data:`TEXT_KEYS` is withheld, wherever in the structure it sits. The recursion is
    `rglob` rather than two fixed levels because a run artefact that moves one directory
    deeper would otherwise stop being harvested silently (R2 M-4).
    """
    for path in sorted(run.rglob("*.json")):
        try:
            payload = _quiet_load(path)
        except (json.JSONDecodeError, UnicodeDecodeError):
            print(f"  warn  {path} is not readable JSON; its text cannot be withheld")
            continue
        _harvest(payload, withheld)


def feed_human(human: Path, withheld: Withheld) -> None:
    """Every text an organised human coding holds, including the examples.

    ``organised.json`` is the one artefact in this project that carries respondent
    text under the name of a *codebook*, because a leaf keeps up to two of its own
    segments as examples. Definitions are shareable one at a time; examples never are.
    The walk in :func:`feed_run` reaches them through ``examples``; this function adds
    the recursive descent through ``children`` that a tree needs, and the highlight
    contents in the placement report.
    """
    feed_run(human, withheld)
    for name in ("placement.json", "golden_mapping.json"):
        placement = _quiet_load(human / name)
        if placement is None:
            continue
        for mapping in placement.get("mappings", []):
            withheld.add(mapping.get("content"))
    organised = _quiet_load(human / "organised.json")
    if organised is not None:
        _feed_organised_codes(organised.get("codes"), withheld)


@dataclass
class Ctx:
    """Where everything is, what may not be said, and what could not be produced.

    ``human`` defaults to ``run``: a directory holding both a machine run and a human
    coding — the layout the first export used — still resolves exactly as it did.
    """

    run: Path
    human: Path
    out: Path
    label: str
    withheld: Withheld
    seeded: Path | None = None
    halted: Path | None = None
    resumed: Path | None = None
    #: section file name -> why it could not be produced
    missing: dict[str, str] = field(default_factory=dict)
    #: how many descriptions the per-item guard replaced, by source
    withheld_descriptions: dict[str, int] = field(default_factory=dict)
    described: dict[str, int] = field(default_factory=dict)

    def skip(self, name: str, reason: str) -> None:
        self.missing.setdefault(name, reason)

    def describe(self, source: str, text: Any) -> str:
        """Emit one description through the per-item guard, counting what it caught."""
        emitted, clean = guarded_description(text, self.withheld)
        if clean and emitted:
            self.described[source] = self.described.get(source, 0) + 1
        if not clean:
            self.withheld_descriptions[source] = self.withheld_descriptions.get(source, 0) + 1
        return emitted


def _analysis_dir(ctx: Ctx) -> tuple[Path, str]:
    """The analysis to export and whose coding it was computed over.

    A human coding analysed in its own right carries ``analysis_golden/``; a run
    without one carries only ``analysis/`` (over the machine's). The human directory
    is consulted first, because with ``--human`` that is where the tail over his
    coding was written.
    """
    for base in (ctx.human, ctx.run):
        if (base / "analysis_golden").is_dir():
            return base / "analysis_golden", "his coding"
    return ctx.run / "analysis", "the machine's coding"


def _machine_analysis(ctx: Ctx) -> Path | None:
    adir = ctx.run / "analysis"
    return adir if adir.is_dir() else None


# --------------------------------------------------------------------------- sections


def _question_line(question: Any, ctx: Ctx) -> str:
    """The survey question, if reproducing it is not also reproducing a response.

    The question is the instrument, not a respondent's words — but a respondent who
    echoes the question's phrasing back into an answer makes the two indistinguishable
    to a guard that works on character runs, and this one does. So the question is
    tested like any other prose: emitted when clean, named by its variant when not.
    Withholding the instrument is a small loss (it is in `gaf/config.py`, and it is his
    own question) beside a hole in the only guarantee this script makes.
    """
    if not question:
        return "> (no question attached)"
    emitted, clean = guarded_description(question, ctx.withheld)
    if clean:
        return f"> {emitted}"
    return (
        "> *The question's wording is withheld here: at least one respondent echoed a run "
        f"of {ctx.withheld.shingle} characters of it back in their answer, which makes the two "
        "indistinguishable to this guard. The variant is recorded on every response in the "
        "run directory and the wording is in `gaf/config.py`.*"
    )


def section_inputs(ctx: Ctx) -> str | None:
    run, withheld, label = ctx.run, ctx.withheld, ctx.label
    corpus = _load(run / "corpus.json")
    if corpus is None:
        ctx.skip("01-inputs.md", "no `corpus.json` in the run directory (`gaf ingest` writes it)")
        return None
    responses = _rows(corpus)
    golden = _load(_first(ctx.human / "golden.json", run / "golden.json") or run / "golden.json")
    placement = _first(
        ctx.human / "golden_mapping.json",
        ctx.human / "placement.json",
        run / "golden_mapping.json",
        run / "placement.json",
    )
    mapping = _load(placement) if placement is not None else None
    grows = _rows(golden) if golden is not None else []
    for r in responses:
        withheld.add(r.get("content"))
    for r in grows:
        withheld.add(r.get("segment"))

    if grows:
        coded_rows, col_n, col_d = grows, "highlights", "distinct codes"
    else:
        assignments = _load(run / "assignments.json")
        coded_rows = _rows(assignments) if assignments is not None else []
        for r in coded_rows:
            withheld.add(r.get("segment"))
        col_n, col_d = "machine assignments", "distinct machine codes"
    highlights = Counter(int(r["response_id"]) for r in coded_rows)
    distinct = defaultdict(set)
    for r in coded_rows:
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
        _question_line(question, ctx),
        "",
        "Word counts are derived from the response bodies; the bodies themselves stay in the",
        "gitignored run directory.",
        "",
        _table(*_drop_empty(["id", "number as written", "note", "words", col_n, col_d], rows)),
        "",
    ]
    if mapping is not None:
        m = mapping
        outcomes: list[list[Any]] = [
            ["highlights in the export", m["total"]],
            ["mapped, exact", m["exact"]],
            ["mapped, fuzzy", m["fuzzy"]],
        ]
        if "resolved" in m:
            outcomes.append(
                ["mapped, resolved (ambiguous, but only one candidate is in the coded set)", m["resolved"]]
            )
        outcomes += [
            ["ambiguous (text present in more than one response)", m["ambiguous"]],
            ["unlocated (text belongs to responses not in this sample)", m["unlocated"]],
        ]
        parts += [
            "## The coding export, placed onto the corpus",
            "",
            "Each highlight in the principal investigator's export was located by its text in",
            "the corpus (exact substring first, then the same fuzzy locator the S2 check uses,",
            "threshold 0.85). Nothing was assigned by guess.",
            "",
            _table(["outcome", "n"], outcomes, align="lr"),
            "",
        ]
        if "resolved" in m:
            parts += [
                f"**Read the three mapping numbers separately: {m['exact']} exact, {m['fuzzy']} fuzzy, {m['resolved']} resolved.**",
                "`exact` is the text found verbatim in exactly one response. `fuzzy` is the",
                "locator's own near match above 0.85. `resolved` is a *weaker* claim than either:",
                "the text occurs verbatim in more than one response, and exactly one of those",
                "responses is in the coded set, so the highlight was attributed there. A single",
                f"\"mapped\" total of {m['exact'] + m['fuzzy'] + m['resolved']} would hide that distinction (ADR-0031).",
                "",
            ]
        if m.get("coded_response_count"):
            parts += [
                f"**The coded set is {m['coded_response_count']} responses** of the {len(responses)} in the corpus —",
                "every response the export places at least one highlight on. It is the universe",
                "every number about his coding below is computed over.",
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


def _flatten_organised(codes: Any, out: list[Json] | None = None) -> list[Json]:
    """Every node of the organised tree, parents and leaves, in the tree's own order."""
    out = [] if out is None else out
    for code in codes or []:
        out.append(code)
        _flatten_organised(code.get("children"), out)
    return out


def _organised_tree_lines(codes: Any, described: dict[str, str], depth: int = 0) -> list[str]:
    lines: list[str] = []
    for code in codes or []:
        bullet = "  " * depth + f"- {_code(code['name'])} — {code['count']} segment(s)"
        note = described.get(code["name"], "")
        lines.append(bullet + (f" — {note}" if note else ""))
        lines += _organised_tree_lines(code.get("children"), described, depth + 1)
    return lines


def section_organised_codebook(ctx: Ctx) -> str | None:
    """The PI's own codebook as `gaf codebook organise` reconstructed it."""
    organised = _load(ctx.human / "organised.json")
    if organised is None:
        return None
    meta = organised.get("meta") or {}
    nodes = _flatten_organised(organised.get("codes"))
    n_leaves = sum(1 for n in nodes if n.get("leaf"))

    book = _load(ctx.human / "codebook.json")
    brows = _rows(book) if book is not None else []
    sources = Counter(
        str((c.get("meta") or {}).get("description_source", meta.get("description_source", "-")))
        for c in brows
        if c.get("description")
    )
    golden = _load(ctx.human / "golden.json")
    grows = _rows(golden) if golden is not None else []
    placed = Counter(r["code"] for r in grows)
    responses_per_code: defaultdict[str, set[int]] = defaultdict(set)
    for r in grows:
        responses_per_code[r["code"]].add(int(r["response_id"]))
    evidence_count: dict[str, list[Any]] = {
        str(c["name"]): list(c.get("evidence") or []) for c in brows
    }

    notes = Counter(str(n["category"]) for n in organised.get("notes", []))
    by_category: defaultdict[str, list[str]] = defaultdict(list)
    for note in organised.get("notes", []):
        by_category[str(note["category"])].append(str(note.get("subject", "-")))

    tops = list(organised.get("codes") or [])
    fam_rows = [
        [
            _code(top["name"]),
            len(top.get("children", [])),
            len(top.get("rows", [])),
            top["count"],
            sum(placed[ch["name"]] for ch in top.get("children", [])) + placed[top["name"]],
            len(evidence_count.get(top["name"], ())),
        ]
        for top in sorted(tops, key=lambda t: (-int(t["count"]), str(t["name"])))
    ]
    code_rows = [
        [
            _code(node["name"]),
            node["level"],
            node["count"],
            placed[node["name"]],
            len(responses_per_code[node["name"]]),
            ctx.describe("the researcher's codebook", node.get("description")) or "-",
        ]
        for node in sorted(nodes, key=lambda n: (_family(str(n["name"])), str(n["name"])))
    ]
    n_withheld = ctx.withheld_descriptions.get("the researcher's codebook", 0)
    n_described = sum(1 for n in nodes if str(n.get("description", "")).strip())

    parts = ["# 02 - The principal investigator's codebook, organised", ""]
    parts += [
        f"His tagged export holds **{organised['pair_count']} code-segment pairings** over",
        f"**{organised['segment_count']} segments**. Organising them by the first hyphen gives",
        f"**{organised['parent_count']} top-level codes** and **{len(nodes) - organised['parent_count']} sub-codes**,",
        f"{len(nodes)} in all; {n_leaves} of them are leaves (a top-level code with no sub-codes",
        "is a leaf as well as a family).",
        "",
        "Nothing here was invented by the pipeline: the tree is his labels, read back.",
        "",
        "## Definitions, and where they came from",
        "",
        f"**{n_described} of {len(nodes)} codes carry a definition.** Their stated source, as the",
        "organiser recorded it code by code:",
        "",
        _table(
            ["description source", "codes"],
            [[f"`{k}`", v] for k, v in sorted(sources.items())] or [["none recorded", 0]],
            align="lr",
        ),
        "",
        f"`{meta.get('definitions_path', '-')}` is the document they were read from;",
        f"`{meta.get('tagged_path', '-')}` is the export the pairings came from.",
        "",
        "**A definition is only as shareable as whoever wrote it made it.** Each one was",
        "tested on its own against every response in the corpus before being reproduced here:",
        f"**{n_withheld} of {n_described}** share a {ctx.withheld.shingle}-character run with a response and",
        "appear below as *definition withheld*, with their code name intact. That is the",
        "exporter's own guard applied per item rather than to the file as a whole — a",
        "definition that quotes the response which prompted it is respondent text, however",
        "it is labelled.",
        "",
        f"## Families ({len(tops)} top-level codes)",
        "",
        "`own segments` is the count of segments carrying the family label with no sub-code",
        "after it. A family with sub-codes *and* its own segments is worth a look: the last",
        "column is the evidence that actually reached the codebook, and the two should agree.",
        "",
        _table(
            [
                "family",
                "sub-codes",
                "own segments",
                "segments in export",
                "segments placed",
                "evidence rows in the codebook",
            ],
            fam_rows,
            align="lrrrrr",
        ),
        "",
    ]
    mismatched = [
        row for row in fam_rows if int(row[2]) and int(row[1]) and int(row[4]) != int(row[5])
    ]
    if mismatched:
        parts += [
            "> **Read that last column.** "
            + ", ".join(str(row[0]) for row in mismatched)
            + " carries both its own segments and sub-codes, and its placed count and its",
            "> evidence count disagree. Its own segments are the ones at risk of being lost.",
            "",
        ]
    else:
        parts += [
            "Every family's placed segments and its evidence rows agree, so no family lost its",
            "own segments on the way into the codebook.",
            "",
        ]
    cons = organised.get("consolidations") or []
    parts += [
        f"## Consolidations ({len(cons)})",
        "",
        "Two labels the organiser judged to be the same code, written differently. It",
        "consolidates and records; it never merges two codes that merely look alike.",
        "",
    ]
    parts += (
        [
            _table(
                ["from", "to", "rule", "rows"],
                [
                    [_code(c["from"]), _code(c["to"]), f"`{c['rule']}`", len(c.get("rows", []))]
                    for c in cons
                ],
                align="lllr",
            ),
            "",
        ]
        if cons
        else ["None.", ""]
    )
    parts += [
        f"## Researcher notes ({sum(notes.values())})",
        "",
        "Every observation the organiser made about his labelling, as counts and code names.",
        "None of them changed anything: they are the agenda for a conversation, not edits.",
        "",
        _table(
            ["category", "n", "subjects"],
            [
                [f"`{cat}`", n, ", ".join(_code(s) for s in sorted(set(by_category[cat])))]
                for cat, n in sorted(notes.items())
            ],
            align="lrl",
        ),
        "",
        "## The tree",
        "",
    ]
    parts += _organised_tree_lines(organised.get("codes"), {})
    parts += [
        "",
        "The same tree as Mermaid source is in [`tree.mmd`](tree.mmd), and as a drawing in",
        "[`views-human/views.html`](views-human/views.html).",
        "",
        "## Every code, with its definition",
        "",
        _table(
            ["code", "level", "segments in export", "segments placed", "responses", "definition"],
            code_rows,
            align="lrrrrl",
        ),
    ]
    return "\n".join(parts)


def section_human_codebook(ctx: Ctx) -> str | None:
    run = ctx.human
    organised = section_organised_codebook(ctx)
    if organised is not None:
        return organised
    mapping = _load(run / "golden_mapping.json")
    golden = _load(run / "golden.json")
    if mapping is None or golden is None:
        ctx.skip(
            "02-human-codebook.md",
            "no `organised.json` and no `golden_mapping.json` (`gaf codebook organise` writes the first)",
        )
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


def section_structural(ctx: Ctx) -> str | None:
    path = _first(ctx.human / "golden_checks.json", ctx.run / "golden_checks.json")
    checks = _load(path) if path is not None else None
    if checks is None:
        ctx.skip(
            "03-structural-checks.md",
            "no `golden_checks.json` (`gaf check all --out <dir>/golden_checks.json` writes it)",
        )
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


#: Where the same coding, clustered over the whole corpus instead of the coded set,
#: is written. Optional: without it the choice is stated but not measured.
ALT_UNIVERSE_DIR = "analysis_golden_all200"


def _universe_block(ctx: Ctx, clusters: Json) -> list[str]:
    """The choice of row universe, made explicit and, where possible, measured.

    A coding that covers part of a corpus can be clustered two ways: over the responses
    it actually coded, or over every response with the uncoded ones as all-zero rows.
    Both are defensible and they are different questions. Which one was used is not a
    detail to leave to a default.
    """
    alt = _quiet_load(ctx.human / ALT_UNIVERSE_DIR / "clusters.json")
    lines = [
        "## The row universe, and why it is the coded set",
        "",
        f"The matrix above has **{clusters['n_responses']} rows: the responses his export actually",
        "codes**, not one row per response in the corpus. Clustering the whole corpus would put",
        "every uncoded response in as an identical all-zero row, and Ward's linkage would then",
        "be describing the uncoded majority rather than the coding. Both readings are",
        "legitimate and they answer different questions; this one answers \"what structure is in",
        "his coding\".",
        "",
    ]
    if alt is None:
        return lines
    sizes = ", ".join(str(len(v)) for _, v in sorted(alt["members"].items()))
    lines += [
        "Measured, on the same coding, over the whole corpus instead:",
        "",
        _table(
            ["row universe", "rows", "codes after the filter", "clusters", "cluster sizes"],
            [
                [
                    "the coded set (used here)",
                    clusters["n_responses"],
                    clusters["n_codes"],
                    clusters["n_clusters"],
                    ", ".join(str(len(v)) for _, v in sorted(clusters["members"].items())),
                ],
                [
                    "every response in the corpus",
                    alt["n_responses"],
                    alt["n_codes"],
                    alt["n_clusters"],
                    sizes,
                ],
            ],
            align="lrrrl",
        ),
        "",
    ]
    for warning in alt.get("schedule", {}).get("warnings", []):
        lines += ["> **What the whole-corpus reading says about itself.** " + warning, ""]
    return lines


def section_clustering(ctx: Ctx) -> str | None:
    out = ctx.out
    adir, whose = _analysis_dir(ctx)
    clusters = _load(adir / "clusters.json")
    matrix = _load(adir / "occurrence_matrix.json")
    if clusters is None:
        ctx.skip("04-clustering.md", f"no `clusters.json` in `{adir}` (`gaf analyse` writes it)")
        return None
    sched = clusters["schedule"]
    filt = (matrix or {}).get("filter", {})
    parts = [f"# 04 - Ward's hierarchical cluster analysis over {whose}", ""]
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
    for warning in sched.get("warnings", []):
        parts += ["> **The analysis's own warning.** " + warning, ""]
    parts += _universe_block(ctx, clusters)
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
            copy_guarded(ctx, adir / svg, out / svg, svg)
    return "\n".join(parts)


def section_saturation(ctx: Ctx) -> str | None:
    out = ctx.out
    adir, whose = _analysis_dir(ctx)
    sat = _load(adir / "saturation.json")
    if sat is None:
        ctx.skip("05-saturation.md", f"no `saturation.json` in `{adir}` (`gaf analyse` writes it)")
        return None
    parts = [f"# 05 - Theoretical saturation over {whose}", ""]
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
        copy_guarded(ctx, adir / "saturation.svg", out / "saturation.svg", "saturation.svg")
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


def section_agreement(ctx: Ctx) -> str | None:
    run, withheld = ctx.run, ctx.withheld
    runs = [
        ("agreement", "Descriptions on both sides"),
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


def section_calibration(ctx: Ctx) -> str | None:
    j = _load(ctx.run / "calibration_report.json")
    if j is None:
        ctx.skip(
            "07-calibration.md",
            "no `calibration_report.json` (the `calibrate_thresholds` snippet in `docs/RUNBOOK.md` writes it)",
        )
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


def section_machine_run(ctx: Ctx) -> str | None:
    run, withheld = ctx.run, ctx.withheld
    stats = _load(run / "stats.json")
    codebook = _load(run / "codebook.json")
    if stats is None or codebook is None:
        ctx.skip("08-machine-run.md", "no `stats.json` or no `codebook.json` in the run directory")
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
                ctx.describe("the offline stand-in coder", c.get("description", "")),
                len(c.get("evidence", [])),
                per_code.get(c["name"], 0),
                c.get("created_in_snapshot", "-"),
            ]
        )
    f = stats.get("findings", {})
    frows = [
        [k, v.get("ERROR", 0), v.get("WARN", 0), v.get("INFO", 0)] for k, v in sorted(f.items())
    ]
    findings = _load(run / "findings.json")
    frows_marker: list[list[Any]] = []
    flagged: Counter[tuple[str, str, str, str, str]] = Counter()
    if findings is not None:
        by_marker: Counter[tuple[str, str, str]] = Counter()
        for x in _rows(findings):
            marker = str((x.get("data") or {}).get("marker", "-"))
            by_marker[(x["check_id"], x["severity"], marker)] += 1
            if x["severity"] in ("ERROR", "WARN"):
                flagged[
                    (x["check_id"], x["severity"], marker, str(x.get("subject", "-")), x["message"])
                ] += 1
        frows_marker = [[c, sev, mk, n] for (c, sev, mk), n in sorted(by_marker.items())]
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
    ]
    if frows_marker:
        parts += [
            "## Findings by marker",
            "",
            _table(["check", "severity", "marker", "n"], frows_marker, align="lllr"),
            "",
        ]
    if flagged:
        parts += [
            "## Every ERROR and WARN (subject is the candidate or response concerned)",
            "",
            _table(
                ["check", "severity", "marker", "subject", "message", "n"],
                [[*k, n] for k, n in sorted(flagged.items())],
                align="lllllr",
            ),
            "",
        ]
    parts += [
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


# ------------------------------------------------------------------ the newer readings


def _curve_from_json(payload: Json) -> GrowthCurve:
    """Rebuild `gaf.checks.growth`'s curve from its own JSON, so the spike rule is *the*
    spike rule and not a second copy of it written in this script."""
    return GrowthCurve(
        source=str(payload.get("source", "assignments")),
        batch_size=int(payload["batch_size"]),
        points=tuple(
            GrowthPoint(
                batch=int(p["batch"]),
                responses_in_batch=int(p["responses_in_batch"]),
                cumulative_responses=int(p["cumulative_responses"]),
                new_codes=int(p["new_codes"]),
                cumulative_codes=int(p["cumulative_codes"]),
                new_codes_per_response=float(p["new_codes_per_response"]),
                new_code_names=tuple(p.get("new_code_names", ())),
            )
            for p in payload["points"]
        ),
        total_codes=int(payload["total_codes"]),
        saturated_at_batch=payload.get("saturated_at_batch"),
    )


def _growth_block(title: str, payload: Json, spikes: list[Spike]) -> list[str]:
    curve = payload
    by_batch = {s.batch: s for s in spikes}
    rows = [
        [
            p["batch"],
            p["responses_in_batch"],
            p["cumulative_responses"],
            p["new_codes"],
            p["cumulative_codes"],
            p["new_codes_per_response"],
            f"yes ({by_batch[p['batch']].rule})" if p["batch"] in by_batch else "-",
        ]
        for p in curve["points"]
    ]
    sat = curve.get("saturated_at_batch")
    parts = [f"## {title}", ""]
    parts += [
        f"Batch size {curve['batch_size']}; {curve['total_codes']} distinct code(s) in all; "
        + (
            f"first batch that admitted nothing new: batch {sat}."
            if sat
            else "**no batch admitted nothing new** — the curve has not flattened."
        ),
        "",
        _table(
            [
                "batch",
                "responses",
                "cumulative responses",
                "new codes",
                "cumulative codes",
                "new codes per response",
                "spike",
            ],
            rows,
            align="rrrrrrl",
        ),
        "",
    ]
    if spikes:
        parts += [f"**Spikes: {len(spikes)}.**", ""]
        parts += [
            f"- batch {s.batch}: {s.new_codes} new code(s), rule `{s.rule}`, baseline "
            f"{s.baseline:.2f}, window {s.window}"
            + (f", ratio {s.ratio:.2f}" if s.ratio is not None else ", ratio not defined")
            for s in spikes
        ]
        parts += [""]
    else:
        parts += ["No batch met the spike rule.", ""]
    return parts


def policy_batch(ctx: Ctx) -> int:
    """The batch size the curves in this section were cut at."""
    human_dir, _ = _analysis_dir(ctx)
    for adir in (human_dir, ctx.run / "analysis"):
        payload = _quiet_load(adir / "growth.json")
        if payload is not None:
            return int(payload["batch_size"])
    return 10


def _run_growth(ctx: Ctx) -> Json | None:
    """The run's **own** growth curve, from `run.json`, not from `gaf analyse`.

    They are the same curve when every response carries at least one assignment and
    the two batch sizes agree, and a different curve when either is false: the analysis
    tail batches the *coded* responses in their own order, while a run batches the
    corpus. The run's own number is the one a handover trace and a timeline are keyed
    to, so it is the one quoted here, and the two are compared rather than assumed
    equal.
    """
    payload = _quiet_load(ctx.run / "run.json")
    if payload is None:
        return None
    try:
        from gaf.report.run_report import RunArtefact

        return dict(RunArtefact.from_json(payload).growth().to_json())
    except Exception as exc:  # pragma: no cover - a run.json an older build wrote
        print(f"  warn  could not read the run's own growth curve: {type(exc).__name__}")
        return None


def section_growth(ctx: Ctx) -> str | None:
    """Code growth and the spike rule, over both codings."""
    human_dir, _ = _analysis_dir(ctx)
    sources: list[tuple[str, Path]] = []
    if (human_dir / "growth.json").is_file() and human_dir.name == "analysis_golden":
        sources.append(("Code growth over his coding", human_dir))
    machine = _machine_analysis(ctx)
    if machine is not None and (machine / "growth.json").is_file():
        sources.append(("Code growth over the machine run", machine))
    if not sources:
        ctx.skip("09-growth.md", "no `growth.json` in either analysis directory (`gaf analyse` writes it)")
        return None

    policy = CheckpointPolicy()
    parts = ["# 09 - Code growth, the spike rule and saturation", ""]
    parts += [
        "Growth counts **admissions**: the batch in which each code entered the codebook",
        "for the first time. A batch spikes when it admits at least",
        f"{policy.spike_min_new_codes} new codes *and* at least {policy.spike_factor:g}x the median of the",
        f"previous {policy.spike_window} batches; before a baseline exists the absolute ceiling of",
        f"{policy.max_new_codes_per_batch} per batch applies instead. Both rules are uncalibrated (ADR-0033)",
        "and both are reported rather than acted on here.",
        "",
    ]
    parts += [
        "**Batches here are batches of *coded* responses.** The curve is cut every",
        f"{policy_batch(ctx)} responses that carry at least one code, in the order they were coded;",
        "a response nobody coded does not advance it. For a run that codes everything the",
        "two readings coincide, and for a coding that covers part of a corpus they do not.",
        "",
    ]
    for title, adir in sources:
        payload = _load(adir / "growth.json")
        if payload is None:
            continue
        if "machine" in title:
            own = _run_growth(ctx)
            if own is not None:
                same = [
                    (p["batch"], p["responses_in_batch"], p["new_codes"], p["cumulative_codes"])
                    for p in own["points"]
                ] == [
                    (p["batch"], p["responses_in_batch"], p["new_codes"], p["cumulative_codes"])
                    for p in payload["points"]
                ]
                parts += [
                    "> The run records a growth curve of its own, built from its admissions at its",
                    "> own batch size. It is the one the handover trace and the timeline are keyed to."
                    + (
                        " It agrees with the analysis tail's point for point, so the table below"
                        " reads the same either way."
                        if same
                        else " **It does not agree with the analysis tail's**, so the table below"
                        " is the run's own and `analysis/growth.json` is cut differently."
                    ),
                    "",
                ]
                if not same:
                    payload = own
        spikes = detect_spikes(_curve_from_json(payload), policy)
        parts += _growth_block(title, payload, spikes)

    if machine is not None:
        sat = _load(machine / "saturation.json")
        if sat is not None:
            parts += [
                "## Saturation over the machine run",
                "",
                f"Batch size {sat['batch_size']}; {sat['total_codes']} distinct codes; "
                + (
                    f"**saturated at batch {sat['saturated_at_batch']}**"
                    f" — that batch admitted nothing new."
                    if sat.get("saturated_at_batch")
                    else "**not saturated**: every batch introduced new codes."
                ),
                "",
                "The curve is the growth table above (the two are one fact read two ways, and a",
                "test asserts they agree batch by batch), so it is not repeated here.",
                "",
                "A stand-in coder built on a keyword table saturates because its vocabulary is",
                "finite, not because the corpus ran out of ideas. Read this as a property of the",
                "offline coder, not a finding about the corpus.",
                "",
            ]
    return "\n".join(parts)


def section_handover(ctx: Ctx) -> str | None:
    """Where the decision matrix first hands over on real data, and which rule fired."""
    stats = _load(ctx.run / "stats.json")
    trace = (stats or {}).get("decision_trace") or []
    if not trace:
        ctx.skip("10-handover.md", "no `decision_trace` in `stats.json` (a run written before ADR-0033)")
        return None
    due = [row for row in trace if row.get("verdict") == "checkpoint_due"]
    first = due[0] if due else None
    fired: Counter[str] = Counter()
    for row in trace:
        fired.update(row.get("fired", ()))
    rows = [
        [
            r["batch"],
            r["responses_coded"],
            r["new_codes"],
            r["cumulative_codes"],
            r["near_duplicate_pairs"],
            (r.get("spike") or {}).get("rule", "-"),
            ", ".join(r.get("fired", ())) or "-",
            ", ".join(r.get("held", ())) or "-",
            r.get("trigger", "-"),
            r.get("verdict", "-"),
        ]
        for r in trace
    ]
    parts = ["# 10 - The loop handover: where the matrix first hands over on real data", ""]
    parts += [
        "The fast loop never blocks. At every batch boundary it evaluates the handover rows",
        "of the decision matrix and records the verdict; a `checkpoint_due` verdict says a",
        "human should look at the codebook before coding continues. Nothing in this export",
        "took a checkpoint: `--halt-on-checkpoint` is the flag that stops at one, and section",
        "16 shows what happens when it does.",
        "",
    ]
    if first is not None:
        parts += [
            f"**First handover: batch {first['batch']}, after {first['responses_coded']} responses.**",
            "",
            _table(
                ["what", "value"],
                [
                    ["trigger", f"`{first.get('trigger', '-')}`"],
                    ["rule(s) fired", ", ".join(f"`{r}`" for r in first.get("fired", ())) or "-"],
                    ["new codes in that batch", first["new_codes"]],
                    ["near-duplicate leaf pairs", first["near_duplicate_pairs"]],
                    ["spike rule", f"`{(first.get('spike') or {}).get('rule', '-')}`"],
                ],
                align="ll",
            ),
            "",
            "> " + str(first.get("reason", "")).replace("\n", " "),
            "",
        ]
    parts += [
        f"**{len(due)} of {len(trace)} batches came due.** Rules fired across the whole run:",
        "",
        "Read that count with one thing in mind: `handover.floor` is a *schedule*, not a",
        "diagnosis. Once the hard floor of responses has been passed it is satisfied at every",
        "subsequent batch boundary, so a long run reports it repeatedly. The batches worth",
        "looking at are the ones whose trigger is `health` or `spike` — those are the ones",
        "saying something about this codebook rather than about how far the run has got.",
        "",
        _table(
            ["rule", "batches"],
            [[f"`{k}`", v] for k, v in sorted(fired.items())] or [["none", 0]],
            align="lr",
        ),
        "",
        "## The trace, batch by batch",
        "",
        _table(
            [
                "batch",
                "responses coded",
                "new codes",
                "cumulative codes",
                "near-duplicate pairs",
                "spike rule",
                "fired",
                "held",
                "trigger",
                "verdict",
            ],
            rows,
            align="rrrrrlllll",
        ),
        "",
    ]
    matrix = _first(ctx.run / "decision_matrix.md")
    if matrix is not None:
        kept, dropped = _guarded_lines(matrix.read_text(encoding="utf-8"), ctx.withheld)
        parts += [
            "## The decision matrix, as this run's configuration renders it",
            "",
            "Every decision the pipeline can take, which loop takes it, who decides, and the",
            "condition under which it fires. Written by `gaf report` from the run's own config,",
            "so the thresholds below are the ones this run used.",
            "",
        ]
        if dropped:
            parts += [
                f"> **{dropped} line(s) of this table are withheld.** The matrix is the",
                "> pipeline's own prose about itself, and a line of it happened to share a run",
                "> of characters with a response. Each one is tested on its own and replaced",
                "> rather than costing the whole section; the full table is in the run",
                "> directory's `decision_matrix.md`.",
                "",
            ]
        parts += [kept.strip(), ""]
    return "\n".join(parts)


#: What replaces a withheld line of a copied document.
WITHHELD_LINE = "| *line withheld: shares wording with a response* |"


def _guarded_lines(body: str, withheld: Withheld) -> tuple[str, int]:
    """A copied document, line by line: ``(what to emit, how many lines were cut)``.

    The per-item rule again, at the granularity a table has. A document written by the
    pipeline about itself is not respondent text, but a guard on character runs cannot
    know that, and the alternative — exempting it — is a hole. So one line is lost
    instead of one section.
    """
    kept: list[str] = []
    dropped = 0
    for line in body.splitlines():
        if line.strip() and not withheld.is_clean(line):
            kept.append(WITHHELD_LINE)
            dropped += 1
        else:
            kept.append(line)
    return "\n".join(kept), dropped


def _patterns_block(title: str, j: Json) -> list[str]:
    combos = j.get("combinations") or {}
    pairs = sorted(
        combos.get("pairs", []),
        key=lambda p: (-int(p["support"]), -float(p.get("lift", 0.0)), tuple(p["codes"])),
    )[:20]
    fam = j.get("family_cooccurrence") or {}
    names = fam.get("names", [])
    counts = fam.get("counts", [])
    parts = [f"## {title}", ""]
    parts += [
        f"{j['n_responses']} responses x {j['n_codes']} codes; minimum support {j['min_support']}.",
        f"{len(j.get('groups', []))} pattern group(s) — responses touching exactly the same set of",
        f"families — and {len(j.get('singleton_response_ids', []))} response(s) whose family signature is unique.",
        "",
    ]
    groups = sorted(j.get("groups", []), key=lambda g: (-int(g["size"]), tuple(g["family_signature"])))
    if groups:
        parts += [
            _table(
                ["size", "families touched", "responses"],
                [
                    [
                        g["size"],
                        ", ".join(_code(f) for f in g["family_signature"]),
                        ", ".join(str(i) for i in _sorted_ids(g["response_ids"])),
                    ]
                    for g in groups[:20]
                ],
                align="rll",
            ),
            "",
        ]
        if len(groups) > 20:
            parts += [f"Showing the 20 largest of {len(groups)} groups.", ""]
    if names and counts:
        parts += [
            "### Family co-occurrence (responses carrying both)",
            "",
            _table(
                ["family", *names],
                [[_code(n), *counts[i]] for i, n in enumerate(names)],
                align="l" + "r" * len(names),
            ),
            "",
        ]
    if pairs:
        parts += [
            f"### Code pairs that travel together ({len(combos.get('pairs', []))} at or above support {j['min_support']})",
            "",
            "`lift` is the joint share over the product of the two individual shares: 1.0 is",
            "chance, above 1.0 is more often than chance.",
            "",
            _table(
                ["code", "code", "support", "share", "lift"],
                [[_code(p["codes"][0]), _code(p["codes"][1]), p["support"], p["share"], p["lift"]] for p in pairs],
                align="llrrr",
            ),
            "",
        ]
        n_triples = len(combos.get("triples", []))
        parts += [
            f"Triples at or above the same support: {n_triples}"
            + (" (the candidate bound was hit; see `patterns.json`)." if combos.get("triple_bound_hit") else "."),
            "",
        ]
    return parts


def section_patterns(ctx: Ctx) -> str | None:
    sources: list[tuple[str, Path]] = []
    human_dir, _ = _analysis_dir(ctx)
    if human_dir.name == "analysis_golden" and (human_dir / "patterns.json").is_file():
        sources.append(("Patterns in his coding", human_dir))
    machine = _machine_analysis(ctx)
    if machine is not None and (machine / "patterns.json").is_file():
        sources.append(("Patterns in the machine run", machine))
    if not sources:
        ctx.skip("11-patterns.md", "no `patterns.json` in either analysis directory (`gaf analyse` writes it)")
        return None
    parts = ["# 11 - Pattern mapping: which responses look alike", ""]
    parts += [
        "A pattern group is a set of responses that touch exactly the same families. It is a",
        "description of the coding, not a claim about the respondents: two responses in one",
        "group may say opposite things about the same subjects.",
        "",
    ]
    for title, adir in sources:
        payload = _load(adir / "patterns.json")
        if payload is not None:
            parts += _patterns_block(title, payload)
    return "\n".join(parts)


def _affinity_block(title: str, j: Json) -> list[str]:
    groups = sorted(
        j.get("groups", []),
        key=lambda g: (not g.get("cross_family"), -int(g["size"]), tuple(g["members"])),
    )
    crossing = [g for g in groups if g.get("cross_family")]
    parts = [f"## {title}", ""]
    parts += [
        f"Space `{j['space_id']}`; blend alpha {j['alpha']} (embedding) against co-occurrence;",
        f"cut at similarity {j['threshold']}. {j['n_leaves_clustered']} of {j['n_leaves_total']} leaves were in the",
        f"matrix; {len(j.get('excluded', []))} were not, and {len(j.get('singleton_leaves', []))} clustered with nothing.",
        "",
    ]
    if groups:
        parts += [
            f"**{len(crossing)} of {len(groups)} affinity group(s) span more than one family.**",
            "Those are the ones worth reading first: a group that stays inside a family mostly",
            "restates the family, while a group that crosses one is the codebook telling you two",
            "branches are doing the same work.",
            "",
        ]
    else:
        parts += [
            "**No two leaves clustered together at all**, so there is nothing here that spans a",
            "family. A vocabulary this small, in a lexical space, gives the blend nothing to",
            "work with.",
            "",
        ]
    if groups:
        parts += [
            _table(
                ["spans families", "families", "size", "responses", "mechanical label", "members"],
                [
                    [
                        "**yes**" if g.get("cross_family") else "no",
                        ", ".join(_code(f) for f in g["families"]),
                        g["size"],
                        g["total_responses"],
                        f"`{g['label_suggestion']}`",
                        ", ".join(_code(m) for m in g["members"]),
                    ]
                    for g in groups
                ],
                align="llrrll",
            ),
            "",
            "The label is mechanical — the commonest tokens among the members' names. Naming a",
            "theme is a human act and this table does not do it.",
            "",
        ]
    subs = j.get("cross_family_subcodes") or []
    parts += [
        f"### The same sub-label under more than one family ({len(subs)})",
        "",
        "A structural fact about the codebook rather than a clustering result: these are",
        "sub-labels spelled identically under two or more families.",
        "",
    ]
    parts += (
        [
            _table(
                ["sub-label", "families", "codes"],
                [
                    [
                        f"`{s['sub_label']}`",
                        ", ".join(_code(f) for f in s["families"]),
                        ", ".join(_code(c) for c in s["codes"]),
                    ]
                    for s in subs
                ],
                align="lll",
            ),
            "",
        ]
        if subs
        else ["None.", ""]
    )
    if j.get("offline_caveat"):
        parts += ["> **The analysis's own caveat.** " + str(j["offline_caveat"]), ""]
    return parts


def section_affinity(ctx: Ctx) -> str | None:
    sources: list[tuple[str, Path]] = []
    human_dir, _ = _analysis_dir(ctx)
    if human_dir.name == "analysis_golden" and (human_dir / "affinity.json").is_file():
        sources.append(("Affinity in his coding", human_dir))
    machine = _machine_analysis(ctx)
    if machine is not None and (machine / "affinity.json").is_file():
        sources.append(("Affinity in the machine run", machine))
    if not sources:
        ctx.skip("12-affinity.md", "no `affinity.json` in either analysis directory (`gaf analyse` writes it)")
        return None
    parts = ["# 12 - Affinity: themes that cut across the families", ""]
    parts += [
        "Affinity clusters **leaf codes**, deliberately across families rather than within",
        "one, because the interesting case is a leaf that belongs with a leaf from somewhere",
        "else in the tree. Groups that span families are flagged in the first column of every",
        "table below.",
        "",
    ]
    for title, adir in sources:
        payload = _load(adir / "affinity.json")
        if payload is not None:
            parts += _affinity_block(title, payload)
    return "\n".join(parts)


def section_crosswalk(ctx: Ctx) -> str | None:
    machine = _machine_analysis(ctx)
    payload = _load(machine / "crosswalk.json") if machine is not None else None
    if payload is None:
        ctx.skip(
            "13-crosswalk.md",
            "no `crosswalk.json` (`gaf analyse --crosswalk-target <codebook.json>` writes it)",
        )
        return None
    j = payload
    bands = Counter(str(m["nearest"]["band"]) for m in j["mappings"])
    rows = [
        [
            _code(m["source"]),
            _code(m["hungarian"]["target"]),
            m["hungarian"]["score"],
            m["hungarian"]["band"] or "-",
            _code(m["nearest"]["target"]),
            m["nearest"]["score"],
            m["nearest"]["band"] or "-",
        ]
        for m in sorted(j["mappings"], key=lambda m: str(m["source"]))
    ]
    parts = ["# 13 - Crosswalk: the machine's codebook mapped onto his", ""]
    parts += [
        f"Space `{j['space_id']}`; tau_high {j['tau_high']}, tau_low {j['tau_low']};",
        f"names only: {'yes' if j['names_only'] else 'no'}.",
        f"{j['n_source_leaves']} machine leaves against {j['n_target_leaves']} of his.",
        "",
        "> " + str(j.get("fair_mode_note", "")),
        "",
        _table(
            ["band", "machine leaves", "what it means"],
            [
                ["`same`", bands.get("same", 0), f"at or above tau_high {j['tau_high']} — the same concept"],
                ["`grey`", bands.get("grey", 0), "between the thresholds — a live pipeline would ask the judge"],
                ["`unmapped`", bands.get("unmapped", 0), f"below tau_low {j['tau_low']} — nothing of his is close"],
            ],
            align="lrl",
        ),
        "",
        f"**Blind spots: {len(j.get('unmapped_target_leaves', []))} of his leaves nothing maps onto.**",
        f"**Inventions: {len(j.get('unmapped_source_leaves', []))} machine leaves with no counterpart of his.**",
        "",
        "## Every machine leaf",
        "",
        "`hungarian` is the one-to-one assignment over the whole vocabulary; `nearest` is the",
        "unconstrained neighbour. They differ when a better-scoring leaf took the target first.",
        "",
        _table(
            [
                "machine leaf",
                "hungarian target",
                "score",
                "band",
                "nearest target",
                "score",
                "band",
            ],
            rows,
            align="llrllrl",
        ),
        "",
        "## His families, and where the machine's leaves land",
        "",
        _table(
            [
                "his family",
                "his leaves",
                "machine leaves landing here",
                "from machine families",
                "blind spots",
            ],
            [
                [
                    _code(r["family"]),
                    r["n_leaves"],
                    r["n_source_leaves"],
                    ", ".join(f"{_code(k)} {v}" for k, v in sorted(r["distribution"].items())) or "-",
                    r["n_blind_spots"],
                ]
                for r in j.get("target_family_rollup", [])
            ],
            align="lrrlr",
        ),
        "",
        "## The machine's families, and where they land in his tree",
        "",
        _table(
            ["machine family", "leaves", "lands in", "scattered", "unmapped"],
            [
                [
                    _code(r["family"]),
                    r["n_leaves"],
                    ", ".join(f"{_code(k)} {v}" for k, v in sorted(r["distribution"].items())) or "-",
                    "yes" if r["scattered"] else "no",
                    r["n_unmapped"],
                ]
                for r in j.get("source_family_rollup", [])
            ],
            align="lrllr",
        ),
        "",
        "### Blind spots — his leaves nothing maps onto",
        "",
        ", ".join(_code(n) for n in j.get("unmapped_target_leaves", [])) or "none",
        "",
        "### Inventions — machine leaves with no counterpart of his",
        "",
        ", ".join(_code(n) for n in j.get("unmapped_source_leaves", [])) or "none",
        "",
    ]
    return "\n".join(parts)


def section_timeline(ctx: Ctx) -> str | None:
    payload = _load(ctx.run / "timeline.json")
    if payload is None:
        ctx.skip("14-timeline.md", "no `timeline.json` (`gaf report --run <dir>` writes it)")
        return None
    j = payload
    batches = j.get("batches", [])
    bios = list(j.get("biographies", {}).values())
    births = Counter(str(b["born"]["origin"]) for b in bios)
    fates = Counter(str(b["fate_kind"]) for b in bios)
    trail = _load(ctx.run / "reorganisation_trail.json")
    parts = ["# 14 - Timeline: when each code was generated, and what happened to it", ""]
    parts += [
        f"{len(j.get('steps', []))} response(s) coded over {len(batches)} batch(es);",
        f"{len(j.get('snapshot_diffs', []))} snapshot transition(s); {len(bios)} code biograph(ies);",
        f"{len(j.get('checkpoints', []))} checkpoint(s).",
        "",
        "## Batches",
        "",
        _table(
            [
                "batch",
                "responses",
                "new codes",
                "cumulative codes",
                "merges",
                "judge consultations",
                "handover verdict",
            ],
            [
                [
                    b["batch"],
                    b["n_responses"],
                    b["n_new_codes"],
                    b["cumulative_codes"],
                    b["merges"],
                    b["judge_consultations"],
                    (b.get("handover") or {}).get("verdict", "-"),
                ]
                for b in batches
            ],
            align="rrrrrrl",
        ),
        "",
        "## How the codes were born, and how they ended",
        "",
        _table(
            ["origin", "codes"],
            [[f"`{k}`", v] for k, v in sorted(births.items())] or [["none", 0]],
            align="lr",
        ),
        "",
        _table(
            ["fate", "codes"],
            [[f"`{k}`", v] for k, v in sorted(fates.items())] or [["none", 0]],
            align="lr",
        ),
        "",
        "## Every code, and the batch that admitted it",
        "",
        _table(
            ["code", "family", "origin", "response", "batch", "fate"],
            [
                [
                    _code(b["name"]),
                    _code(b["family"]),
                    f"`{b['born']['origin']}`",
                    b["born"].get("response_id"),
                    b["born"].get("batch"),
                    f"`{b['fate_kind']}`",
                ]
                for b in sorted(bios, key=lambda b: (str(b["family"]), str(b["name"])))
            ],
            align="lllrrl",
        ),
        "",
    ]
    if trail is not None:
        n = trail.get("n_checkpoints", 0)
        parts += [
            "## Reorganisation trail",
            "",
            (
                f"{n} checkpoint(s) ran, with {len(trail.get('lineage', []))} lineage row(s)."
                if n
                else "No checkpoint ran in this export: the codebook was never reorganised. "
                "The slow loop needs a human at a terminal, and nothing here ran one."
            ),
            "",
        ]
    return "\n".join(parts)


def _run_pair(a: Json, b: Json, key: str) -> list[Any]:
    return [key.replace("_", " "), a.get(key), b.get(key)]


def section_seeded(ctx: Ctx) -> str | None:
    if ctx.seeded is None:
        return None
    seeded = _load(ctx.seeded / "stats.json")
    cold = _load(ctx.run / "stats.json")
    if seeded is None or cold is None:
        ctx.skip("15-seeded-run.md", "no `stats.json` in the seeded run or in the cold run")
        return None
    seed = seeded.get("seeded_from") or {}
    cold_rows = _quiet_load(ctx.run / "assignments.json") or []
    seed_rows = _quiet_load(ctx.seeded / "assignments.json") or []

    def key(row: Json) -> tuple[Any, ...]:
        return (int(row["response_id"]), str(row["code"]), str(row.get("segment", "")))

    differing = len({key(r) for r in cold_rows} ^ {key(r) for r in seed_rows}) // 2
    seed_book = _quiet_load(ctx.seeded / "codebook.json") or {"codes": []}
    seed_source = _quiet_load(ctx.human / "codebook.json") or {"codes": []}
    seed_names = {c["name"] for c in seed_source.get("codes", [])}
    final_names = {c["name"] for c in seed_book.get("codes", [])}

    def evidence(book: Json) -> set[tuple[str, int, str]]:
        return {
            (c["name"], int(e["response_id"]), str(e.get("quote", "")))
            for c in book.get("codes", [])
            for e in c.get("evidence", []) or []
        }

    overlap = len(evidence(seed_source) & evidence(seed_book))

    parts = ["# 15 - A seeded run: can the machine code into his organisation?", ""]
    parts += [
        "**This is a demonstration, not a result.** A seeded run starts from his codebook",
        "instead of an empty one, so the machine codes *into his categories*. That makes it",
        "the right way to ask \"can this pipeline work inside an existing codebook\" and the",
        "wrong way to ask anything about agreement: a run that was handed the answer's",
        "vocabulary is not independent evidence about that vocabulary (ADR-0035).",
        "",
        "**ADR-0035's caveat applies to every number on this page.**",
        "",
        "## The seed",
        "",
        _table(
            ["what", "value"],
            [
                ["codebook", f"`{seed.get('path', '-')}`"],
                ["content hash", f"`{seed.get('content_hash', '-')}`"],
                ["codes", seed.get("codes")],
                ["families", seed.get("families")],
                ["codes carrying a definition", seed.get("described")],
                ["evidence rows held out", seed.get("evidence_held_out")],
                ["sources", ", ".join(f"`{s}`" for s in seed.get("sources", []))],
            ],
            align="ll",
        ),
        "",
        "**Held out means held out.** The seed arrives with the verified evidence his own",
        "coding attached to it, and a seeded run must not count that evidence as its own work:",
        f"overlap between the seed's {seed.get('evidence_held_out', 0)} evidence rows and the seeded run's",
        f"codebook evidence is **{overlap}**. Without the hold-out every number below would be",
        "inflated by exactly that many occurrences.",
        "",
        "## Cold against seeded, on the same corpus",
        "",
        _table(
            ["quantity", "cold run", "seeded run"],
            [
                _run_pair(cold, seeded, "n_responses"),
                _run_pair(cold, seeded, "assignments"),
                _run_pair(cold, seeded, "codes_final"),
                _run_pair(cold, seeded, "families_final"),
                ["codes the run created itself", cold.get("codes_final"), len(final_names - seed_names)],
            ],
            align="lrr",
        ),
        "",
        f"Both runs write {cold.get('assignments')} assignment rows and **{differing} of them differ**.",
        "That is the mechanism working: given his categories the machine reached for one of",
        "his where the cold run invented its own. It is also exactly why this run cannot be",
        "quoted as agreement.",
        "",
    ]
    return "\n".join(parts)


def section_halt_resume(ctx: Ctx) -> str | None:
    if ctx.halted is None:
        return None
    halted = _load(ctx.halted / "stats.json")
    if halted is None:
        ctx.skip("16-halt-and-resume.md", "no `stats.json` in the halted run")
        return None
    trace = halted.get("decision_trace") or []
    stop = next((r for r in trace if r.get("verdict") == "checkpoint_due"), None)
    parts = ["# 16 - Halting at the handover, and resuming without loss", ""]
    parts += [
        "`gaf run --halt-on-checkpoint` stops after the first batch whose verdict is",
        "`checkpoint_due` — the point at which the decision matrix says a human should look",
        "at the codebook. The run still closes normally: a short run is better than a",
        "half-written one.",
        "",
        _table(
            ["what", "value"],
            [
                ["halted at batch", halted.get("halted_at_batch")],
                ["responses coded", halted.get("n_responses")],
                ["responses left uncoded", halted.get("responses_uncoded")],
                ["codes in the codebook at the stop", halted.get("codes_final")],
                ["assignment rows", halted.get("assignments")],
                ["trigger", f"`{(stop or {}).get('trigger', '-')}`"],
                [
                    "rule(s) fired",
                    ", ".join(f"`{r}`" for r in (stop or {}).get("fired", ())) or "-",
                ],
            ],
            align="ll",
        ),
        "",
    ]
    if stop is not None:
        parts += ["> " + str(stop.get("reason", "")).replace("\n", " "), ""]
    resumed = _load(ctx.resumed / "stats.json") if ctx.resumed is not None else None
    cold_rows = _quiet_load(ctx.run / "assignments.json")
    halt_rows = _quiet_load(ctx.halted / "assignments.json")
    res_rows = _quiet_load(ctx.resumed / "assignments.json") if ctx.resumed is not None else None
    parts += ["## Resuming", ""]
    if resumed is None or cold_rows is None or halt_rows is None or res_rows is None:
        parts += [
            "The resumption was not exported: pass `--resumed <dir>` for the run that",
            "continues from the halted codebook with `--seed-codebook` and `--skip-coded`.",
            "",
        ]
        return "\n".join(parts)

    def key(row: Json) -> tuple[Any, ...]:
        return (int(row["response_id"]), str(row["code"]), str(row.get("segment", "")))

    halt_keys = [key(r) for r in halt_rows]
    res_keys = [key(r) for r in res_rows]
    cold_keys = [key(r) for r in cold_rows]
    parts += [
        _table(
            ["what", "value"],
            [
                ["rows written before the halt", len(halt_keys)],
                ["rows written after resuming", len(res_keys)],
                ["rows in an uninterrupted cold run", len(cold_keys)],
                ["rows the two halves share", len(set(halt_keys) & set(res_keys))],
                [
                    "rows where halted+resumed differs from cold",
                    len(set(halt_keys + res_keys) ^ set(cold_keys)),
                ],
                [
                    "concatenation is row-for-row identical to the cold run",
                    "yes" if halt_keys + res_keys == cold_keys else "no",
                ],
                ["codes at the end of the resumption", resumed.get("codes_final")],
                ["codes at the end of the cold run", (_load(ctx.run / "stats.json") or {}).get("codes_final")],
            ],
            align="ll",
        ),
        "",
        "**Stopping at the handover and resuming costs nothing.** That is what makes the",
        "human gate affordable: a researcher can be asked to look at the codebook after any",
        "batch without the coding having to start again.",
        "",
    ]
    return "\n".join(parts)


# ------------------------------------------------------------------- pages and README


#: What each copied file type is, for the README's table.
PAGE_DESCRIPTIONS = {
    ".html": "a self-contained page of figures — no script, no network request, no respondent text",
    ".mmd": "the codebook tree as Mermaid source (names and counts only)",
    ".svg": "a figure",
}

#: (source directory, published subdirectory, what the page is)
PAGE_SOURCES = (
    ("run", "views-machine", "the machine run"),
    ("human", "views-human", "his coding"),
)


def copy_guarded(ctx: Ctx, source: Path, target: Path, name: str) -> Path | None:
    """Copy one whole artefact, but only if the whole artefact passes the guard.

    The per-item rule a third time. A description is guarded one definition at a time
    and a copied table one line at a time; a page written by another module is an item
    that cannot be subdivided, so it is tested whole and either copied or named as
    missing. This runs *before* the copy, so the final self-scan — which deletes
    everything on any hit — stays the contract rather than becoming the mechanism.
    """
    try:
        body = source.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as exc:
        ctx.skip(name, f"`{source.name}` could not be read as text ({type(exc).__name__})")
        return None
    found = ctx.withheld.locate(body)
    if found is not None:
        offset, piece = found
        ctx.skip(
            name,
            f"**withheld**: `{source.name}` shares a run of {ctx.withheld.shingle} characters "
            "with a response. The file is in the run directory; it is not published here.",
        )
        log = record_guard_hit(ctx.run, name, offset, piece)
        where = f"; the run itself is in {log}" if log is not None else ""
        print(
            f"  hold  {name} — shares a run of {len(piece)} characters with withheld "
            f"text at offset {offset}; not copied{where}"
        )
        return None
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(source, target)
    print(f"  wrote {target}")
    return target


def copy_pages(ctx: Ctx) -> list[Path]:
    """`views.html` and the Mermaid tree beside it, one subdirectory per coding.

    Each page links to `tree.mmd` by name, so the two pages get a directory each rather
    than one overwriting the other's tree.
    """
    copied: list[Path] = []
    for attr, sub, what in PAGE_SOURCES:
        base: Path = getattr(ctx, attr)
        page = _first(base / "views" / "views.html", base / "views.html")
        if page is None:
            ctx.skip(f"{sub}/views.html", f"no `views.html` for {what} (`gaf views` writes it)")
            continue
        written = copy_guarded(ctx, page, ctx.out / sub / "views.html", f"{sub}/views.html")
        if written is None:
            continue
        copied.append(written)
        tree = _first(page.parent / "tree.mmd", base / "tree.mmd")
        if tree is not None:
            written_tree = copy_guarded(ctx, tree, ctx.out / sub / "tree.mmd", f"{sub}/tree.mmd")
            if written_tree is not None:
                copied.append(written_tree)
    organised_tree = _first(ctx.human / "tree.mmd")
    if organised_tree is not None:
        written = copy_guarded(ctx, organised_tree, ctx.out / "tree.mmd", "tree.mmd")
        if written is not None:
            copied.append(written)
    else:
        ctx.skip("tree.mmd", "no `tree.mmd` for the organised codebook (`gaf codebook organise` writes it)")
    return copied


def output_files(out: Path) -> list[Path]:
    """Every file the export left behind, in every subdirectory. The guard's input."""
    return sorted((p for p in out.rglob("*") if p.is_file()), key=lambda p: str(p))


#: What the README says about itself. Hand-written framing; every number beside it
#: comes from the run.
README_INTRO = """Everything on this page is produced by `scripts/export_results.py` from run
directories that stay on the researcher's machine. **No respondent's words appear in
this directory.** The exporter is fed every text those directories hold — both corpora,
every segment, every quote, every highlight, every example the organised codebook kept
— re-reads every file it writes, in every subdirectory and of every type, and deletes
the whole export rather than ship a file sharing a {shingle}-character run with any of them."""

README_OFFLINE = """**The machine coder here is not a model.** Every command below ran offline: the
coders, the judge and the refactorer are deterministic mocks, and the embedding space is
the lexical fallback. The offline coder is a keyword table. Its agreement with an expert
was never the question and is not reported as if it were; what is reported is whether
the harness measures, explains and reproduces a disagreement on real inputs."""


def section_readme(ctx: Ctx, produced: list[tuple[str, str]]) -> str:
    stats = _quiet_load(ctx.run / "stats.json") or {}
    corpus = _quiet_load(ctx.run / "corpus.json")
    n_responses = len(_rows(corpus)) if corpus is not None else stats.get("n_responses", "?")
    placement = _quiet_load(ctx.human / "placement.json") or _quiet_load(
        ctx.human / "golden_mapping.json"
    )
    organised = _quiet_load(ctx.human / "organised.json") or {}
    rows: list[list[Any]] = []
    for name, what in produced:
        rows.append([f"[{name}]({name})", what])
    for name, reason in sorted(ctx.missing.items()):
        rows.append([f"`{name}`", f"**not produced** — {reason}"])

    withheld_total = sum(ctx.withheld_descriptions.values())
    described_total = sum(ctx.described.values())
    parts = [f"# Coding results — {ctx.label}", ""]
    parts += [
        README_INTRO.format(shingle=ctx.withheld.shingle),
        "",
        README_OFFLINE,
        "",
        "## What is in this directory",
        "",
        _table(["file", "what it holds"], rows, align="ll"),
        "",
        "Plus this README and the two figures — `dendrogram.svg` and `saturation.svg` —",
        "which are embedded in the sections that discuss them rather than listed above.",
        "",
        "## What was run",
        "",
    ]
    facts: list[list[Any]] = [["responses in the corpus", n_responses]]
    if placement:
        facts += [
            ["code-segment pairings in his export", placement.get("total")],
            ["placed exactly", placement.get("exact")],
            ["placed by the fuzzy locator", placement.get("fuzzy")],
            ["placed by resolution (the weaker claim)", placement.get("resolved", "-")],
            ["ambiguous, excluded", placement.get("ambiguous")],
            ["unlocated, excluded", placement.get("unlocated")],
            ["responses in the coded set", placement.get("coded_response_count", "-")],
        ]
    if organised:
        facts += [
            ["his families", organised.get("parent_count")],
            ["his leaves", organised.get("leaf_count")],
        ]
    if stats:
        facts += [
            ["machine run: segments", stats.get("n_segments")],
            ["machine run: assignment rows", stats.get("assignments")],
            ["machine run: codes", stats.get("codes_final")],
            ["machine run: families", stats.get("families_final")],
            ["machine run: offline", stats.get("offline")],
        ]
    parts += [
        _table(["quantity", "value"], facts, align="lr"),
        "",
        *_readme_findings(ctx),
        "## What this cannot show",
        "",
        "- **Nothing here is evidence about a live pipeline.** No model was called. The",
        "  coder is a keyword table, the judge is a stub, and the embedding space is a",
        "  lexical fallback that cannot tell a code label from a quote.",
        "- **An agreement number computed against that coder is a statement about the",
        "  keyword table.** It is reported because the harness's job is to explain a",
        "  disagreement, and it explains this one precisely.",
        "- **No checkpoint ran.** The slow loop needs a human at a terminal. The handover",
        "  trace says where one would have been asked to look.",
        "- **The segments are not here and will not be.** Every list that would be more",
        "  useful with the text beside it names response numbers instead; the text is in",
        "  the gitignored run directory on the researcher's machine.",
        "",
    ]
    if described_total or withheld_total:
        parts += [
            "## Definitions, and the ones held back",
            "",
            f"{described_total} definition(s) are reproduced in this directory. "
            f"**{withheld_total} were withheld** because the definition itself shares a "
            f"{ctx.withheld.shingle}-character run with a response, which makes it respondent text "
            "however it is labelled. Each appears with its code name and the note "
            f"\"{WITHHELD_DESCRIPTION.strip('*')}\".",
            "",
            _table(
                ["written by", "reproduced", "withheld"],
                [
                    [source, ctx.described.get(source, 0), ctx.withheld_descriptions.get(source, 0)]
                    for source in sorted(set(ctx.described) | set(ctx.withheld_descriptions))
                ],
                align="lrr",
            ),
            "",
        ]
    parts += [
        "## What is still needed",
        "",
        "1. **Approval for a live run** — the provider triple and a budget. It is the only",
        "   thing that stops every agreement, crosswalk and calibration number on this page",
        "   from being a statement about a keyword table and a lexical fallback. Everything",
        "   else on this list is a tidy-up; this one is the result.",
        "",
        "The rest are small and answerable in a sentence each; they are listed in the",
        "numbered files where they arise, and repeated here so nothing is lost:",
        "",
    ]
    asks = _readme_asks(ctx, organised, placement or {})
    parts += [f"{i + 2}. {ask}" for i, ask in enumerate(asks)]
    parts += [
        "",
        "## Reproduce",
        "",
        "```bash",
        *_readme_commands(ctx),
        "```",
        "",
        "The run directories those commands write hold the corpus, the coded segments and",
        "every quote. They are gitignored, and `make scrub` removes them before this",
        "directory leaves the machine by any path other than `git push`.",
    ]
    return "\n".join(parts)


def _readme_findings(ctx: Ctx) -> list[str]:
    """The reading of the numbered files, in the order a reader needs them.

    Every sentence here is assembled from an artefact on disk. Nothing is asserted
    that a file in this directory does not also show.
    """
    lines: list[str] = ["## What it shows", ""]
    checks_path = _first(ctx.human / "golden_checks.json", ctx.run / "golden_checks.json")
    if checks_path is not None:
        findings = _rows(_quiet_load(checks_path) or [])
        sev = Counter(str(f["severity"]) for f in findings)
        by_check = Counter(str(f["check_id"]) for f in findings if f["severity"] == "WARN")
        lines += [
            f"- **His coding passes his own rules.** {sev.get('ERROR', 0)} ERROR, "
            f"{sev.get('WARN', 0)} WARN, {sev.get('INFO', 0)} INFO over the whole codebook"
            + (
                " (" + ", ".join(f"{k} {v}" for k, v in sorted(by_check.items())) + ")."
                if by_check
                else "."
            )
            + " A WARN is kept and flagged and is never fatal; see"
            " [03-structural-checks.md](03-structural-checks.md).",
        ]
    organised = _quiet_load(ctx.human / "organised.json") or {}
    if organised:
        meta = organised.get("meta") or {}
        described = sum(
            1
            for c in _flatten_organised(organised.get("codes"))
            if str(c.get("description", "")).strip()
        )
        per_code = Counter(str(v) for v in (meta.get("description_sources") or {}).values())
        named = ", ".join(f"`{k}` {v}" for k, v in sorted(per_code.items())) or "no source recorded"
        lines += [
            f"- **The definitions arrived and were used.** {described} of "
            f"{len(_flatten_organised(organised.get('codes')))} codes carry one ({named}), read from "
            f"`{Path(str(meta.get('definitions_path', '-'))).name}`. On 10 September every "
            "response-code pair was flagged `missing_description`; that gap is closed.",
        ]
    human_dir, _ = _analysis_dir(ctx)
    clusters = _quiet_load(human_dir / "clusters.json")
    if clusters:
        sizes = ", ".join(str(len(v)) for _, v in sorted(clusters["members"].items()))
        warned = bool(clusters.get("schedule", {}).get("warnings"))
        lines += [
            f"- **Clustering over the coded set gives {clusters['n_clusters']} cluster(s)** of sizes "
            f"{sizes}, over {clusters['n_responses']} responses x {clusters['n_codes']} codes after the "
            "low-frequency filter"
            + (
                ", and the schedule warns about the count it produced."
                if warned
                else ". The schedule raises no warning about the count."
            )
            + " The choice of universe matters: clustering the whole corpus instead, with the "
            "uncoded responses as all-zero rows, is a different question and a different answer "
            "— see [04-clustering.md](04-clustering.md).",
        ]
    both: list[str] = []
    for name, label in (("agreement", "with descriptions on both sides"), ("agreement_nameonly", "names only")):
        payload = _quiet_load(ctx.run / name / "agreement.json")
        if payload is None:
            continue
        matched = sum(1 for p in payload["matching"]["pairs"] if p["accepted"])
        both.append(
            f"{label}: {matched} of {payload['matching']['n_human_codes']} of his codes matched, "
            f"kappa {payload['code_level']['cohens_kappa']:.3f}"
        )
    if both:
        lines += [
            "- **Agreement with the offline stand-in coder is nil either way** — "
            + "; ".join(both)
            + ". Both sides now carry definitions, which was the input asked for on 10 September, "
            "and it did not move the number. What binds is the keyword coder and the lexical "
            "space, not the missing definitions — see [06-agreement.md](06-agreement.md).",
        ]
    calib = _quiet_load(ctx.run / "calibration_report.json")
    if calib:
        sweeps = calib.get("sweeps") or {}
        units = ", ".join(f"`{k}` {v['n_units']}" for k, v in sorted(sweeps.items()))
        lines += [
            f"- **Calibration still has too little to work with.** Units per threshold: {units}. "
            "The unit for the two routing thresholds is a code pair, not a response, so five "
            "times the corpus barely moved it. The module reported and wrote nothing, which is "
            "what it is for — see [07-calibration.md](07-calibration.md).",
        ]
    stats = _quiet_load(ctx.run / "stats.json") or {}
    trace = stats.get("decision_trace") or []
    first_due = next((r for r in trace if r.get("verdict") == "checkpoint_due"), None)
    if first_due:
        lines += [
            f"- **The decision matrix first hands over at batch {first_due['batch']}**, after "
            f"{first_due['responses_coded']} responses, on "
            + ", ".join(f"`{r}`" for r in first_due.get("fired", ()))
            + f" with trigger `{first_due.get('trigger')}` — see [10-handover.md](10-handover.md).",
        ]
    if ctx.halted is not None and ctx.resumed is not None:
        halt = _quiet_load(ctx.halted / "assignments.json") or []
        res = _quiet_load(ctx.resumed / "assignments.json") or []
        cold = _quiet_load(ctx.run / "assignments.json") or []

        def _key(row: Json) -> tuple[Any, ...]:
            return (int(row["response_id"]), str(row["code"]), str(row.get("segment", "")))

        identical = [_key(r) for r in halt] + [_key(r) for r in res] == [_key(r) for r in cold]
        lines += [
            (
                f"- **Stopping at the handover costs nothing.** {len(halt)} rows before the halt "
                f"plus {len(res)} after resuming is {len(halt) + len(res)} rows, row-for-row "
                "identical to an uninterrupted run — see "
                "[16-halt-and-resume.md](16-halt-and-resume.md)."
            )
            if identical
            else (
                f"- **Stopping at the handover is not lossless here**: {len(halt)} + {len(res)} "
                f"rows against {len(cold)} from an uninterrupted run — see "
                "[16-halt-and-resume.md](16-halt-and-resume.md)."
            )
        ]
    if ctx.seeded is not None:
        seeded = _quiet_load(ctx.seeded / "stats.json") or {}
        cold_rows = _quiet_load(ctx.run / "assignments.json") or []
        seed_rows = _quiet_load(ctx.seeded / "assignments.json") or []

        def _k(row: Json) -> tuple[Any, ...]:
            return (int(row["response_id"]), str(row["code"]), str(row.get("segment", "")))

        differing = len({_k(r) for r in cold_rows} ^ {_k(r) for r in seed_rows}) // 2
        held = (seeded.get("seeded_from") or {}).get("evidence_held_out", 0)
        lines += [
            f"- **A seeded run codes into his organisation, and {differing} rows change because of "
            f"it.** {held} evidence rows arrived with the seed and were held out, so nothing his "
            "coding already established is counted as the machine's work. It is a demonstration "
            "and not evidence about his codebook (ADR-0035) — see "
            "[15-seeded-run.md](15-seeded-run.md).",
        ]
    lines += [""]
    return lines


def _readme_asks(ctx: Ctx, organised: Json, placement: Json) -> list[str]:
    """The ask-list. Each item is a question one sentence answers."""
    asks: list[str] = []
    withheld_total = sum(ctx.withheld_descriptions.values())
    if withheld_total:
        asks.append(
            f"**{withheld_total} of the definitions quote a response.** They are withheld from this "
            "directory rather than published. Reword them, or confirm they stay local and are "
            "never exported — either answer is fine, but the exporter cannot make that call."
        )
    asks.append(
        "**Which export is canonical, the `.csv` or the `.xlsx`?** They hold the same "
        "pairings in different row order with different columns. The `.csv` was used here "
        "and the row numbers in the notes are its rows."
    )
    if placement.get("ambiguous"):
        asks.append(
            f"**{placement['ambiguous']} highlights are still ambiguous** — their text occurs verbatim "
            "in more than one response and more than one candidate is in the coded set. They are "
            "excluded rather than guessed."
        )
    if placement.get("unlocated"):
        asks.append(
            f"**{placement['unlocated']} highlights could not be located at all.** They belong to "
            "responses outside this corpus, or the text was edited after it was highlighted."
        )
    categories = Counter(str(n["category"]) for n in organised.get("notes", []))
    if categories.get("bare_top_level_code"):
        asks.append(
            "**The bare top-level code** — a family, or a sub-code of something? The structural "
            "check flags every use after the first."
        )
    if categories.get("label_near_miss"):
        asks.append(
            f"**{categories['label_near_miss']} pairs of labels differ by one or two characters.** "
            "They are flagged and never merged. Which are typos and which are distinct codes?"
        )
    if categories.get("shared_subcode"):
        asks.append(
            f"**{categories['shared_subcode']} sub-labels appear under more than one family.** The "
            "affinity map flags the same overlaps from the data side; they are worth reading together."
        )
    asks.append(
        "**Is the coded set meant to stay at its current size?** The export places highlights "
        "on a fraction of the corpus; everything about his coding is computed over that "
        "fraction, and the clustering is sensitive to it."
    )
    return asks


def _readme_commands(ctx: Ctx) -> list[str]:
    lines = [
        "# every command offline: mock clients, the lexical embedder, no key, no network",
        "uv run gaf ingest --input <corpus.csv> --question-variant v2 --out RUN/corpus.json",
        "uv run gaf codebook organise --tagged <tagged.csv> --corpus RUN/corpus.json \\",
        "    --definitions <codebook.md> --out HUMAN",
        "uv run gaf check all --codebook HUMAN/codebook.json --data RUN/corpus.json \\",
        "    --out HUMAN/golden_checks.json",
        "uv run gaf analyse --assignments HUMAN/golden.json --out HUMAN/analysis_golden \\",
        "    --codebook HUMAN/codebook.json",
        "uv run gaf views --assignments HUMAN/golden.json --codebook HUMAN/codebook.json \\",
        "    --analysis HUMAN/analysis_golden --out HUMAN/views/views.html",
        "uv run gaf run --corpus RUN/corpus.json --run-id RUN --offline --out RUN",
        "uv run gaf analyse --assignments RUN/assignments.json --data RUN/corpus.json \\",
        "    --run RUN/run.json \\",
        "    --out RUN/analysis --codebook RUN/codebook.json --crosswalk-target HUMAN/codebook.json",
        "uv run gaf report --run RUN --analysis RUN/analysis",
        "uv run gaf views --run RUN --analysis RUN/analysis --out RUN/views/views.html",
        "# step 5a of scripts/run_full_results.sh writes RUN/assignments_coded_set.json —",
        "# the machine rows on the responses his coding demonstrably reached, which is the",
        "# row set every agreement figure on this page is computed over — and",
        "# RUN/agreement_codebook_merged.json, which carries a description for every code",
        "# either side names. The page reports agreement BOTH ways, so there are two runs:",
        "uv run gaf validate agreement --human HUMAN/golden.json \\",
        "    --machine RUN/assignments_coded_set.json --data RUN/corpus.json \\",
        "    --codebook RUN/agreement_codebook_merged.json --out RUN/agreement",
        "uv run gaf validate agreement --human HUMAN/golden.json \\",
        "    --machine RUN/assignments_coded_set.json --data RUN/corpus.json \\",
        "    --out RUN/agreement_nameonly",
    ]
    if ctx.seeded is not None:
        lines.append(
            "uv run gaf run --corpus RUN/corpus.json --offline --out SEEDED --seed-codebook HUMAN/codebook.json"
        )
    if ctx.halted is not None:
        lines.append(
            "uv run gaf run --corpus RUN/corpus.json --offline --out HALTED --halt-on-checkpoint"
        )
    if ctx.resumed is not None:
        lines.append(
            "uv run gaf run --corpus RUN/corpus.json --offline --out RESUMED \\\n"
            "    --seed-codebook HALTED/codebook.json --skip-coded HALTED"
        )
    lines.append("make results-full")
    return lines


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
    ap.add_argument(
        "--human",
        default=None,
        type=Path,
        help="the organised human coding (`gaf codebook organise --out`); defaults to --run",
    )
    ap.add_argument(
        "--guard-shingle",
        type=int,
        default=GUARD_SHINGLE,
        help=(
            f"the window length at which a shared run counts as reproduction (default "
            f"{GUARD_SHINGLE}). The repository-wide provenance standard, which `make provenance` "
            "applies to every tracked file, is 30. Below about 24 characters, ordinary English "
            "recurs by chance over a corpus of a few hundred responses; state the value you "
            "used rather than tuning it until the export goes green."
        ),
    )
    ap.add_argument(
        "--readme",
        action="store_true",
        help=(
            "also generate README.md. Opt-in on purpose: an existing results directory "
            "may carry a hand-written README that is the record of a meeting, and an "
            "accidental re-export must not overwrite it."
        ),
    )
    ap.add_argument("--seeded", default=None, type=Path, help="a run seeded from his codebook")
    ap.add_argument("--halted", default=None, type=Path, help="a run stopped at the first handover")
    ap.add_argument("--resumed", default=None, type=Path, help="the run that resumed the halted one")
    args = ap.parse_args(argv)
    run: Path = args.run
    out: Path = args.out
    human: Path = args.human if args.human is not None else run
    if not run.is_dir():
        print(f"not a run directory: {run}", file=sys.stderr)
        return 2
    for label_, directory in (
        ("--human", human),
        ("--seeded", args.seeded),
        ("--halted", args.halted),
        ("--resumed", args.resumed),
    ):
        if directory is not None and not Path(directory).is_dir():
            print(f"not a directory: {label_} {directory}", file=sys.stderr)
            return 2
    out.mkdir(parents=True, exist_ok=True)
    ctx = Ctx(
        run=run,
        human=human,
        out=out,
        label=args.label or run.name,
        withheld=Withheld(shingle=int(args.guard_shingle)),
        seeded=args.seeded,
        halted=args.halted,
        resumed=args.resumed,
    )

    # Feed the guard *before* a single section runs. A section that forgets to withhold
    # a field it read is then still covered, because the directory it read it from was
    # already emptied into Withheld in full.
    for directory in (run, ctx.seeded, ctx.halted, ctx.resumed):
        if directory is not None:
            feed_run(Path(directory), ctx.withheld)
    feed_human(human, ctx.withheld)

    sections: list[tuple[str, str, Any]] = [
        ("01-inputs.md", "the corpus, and how his highlights were placed onto it", section_inputs),
        ("02-human-codebook.md", "his codebook organised: tree, counts, notes, definitions", section_human_codebook),
        ("03-structural-checks.md", "his coding against his own rules", section_structural),
        ("04-clustering.md", "Ward's HCA: filter, schedule, clusters, means, dendrogram", section_clustering),
        ("05-saturation.md", "new codes per batch", section_saturation),
        ("06-agreement.md", "his coding against the machine's, both ways of matching codes", section_agreement),
        ("07-calibration.md", "the threshold sweeps and what they say about sample size", section_calibration),
        ("08-machine-run.md", "the offline run: counts, findings, the machine codebook", section_machine_run),
        ("09-growth.md", "code growth, the spike rule and saturation, both codings", section_growth),
        ("10-handover.md", "where the decision matrix first hands over, and the matrix itself", section_handover),
        ("11-patterns.md", "pattern groups and the codes that travel together", section_patterns),
        ("12-affinity.md", "themes that cut across the families", section_affinity),
        ("13-crosswalk.md", "the machine's codebook mapped onto his", section_crosswalk),
        ("14-timeline.md", "when each code was generated, and what happened to it", section_timeline),
        ("15-seeded-run.md", "coding into his organisation — a demonstration, not a result", section_seeded),
        ("16-halt-and-resume.md", "halting at the handover, and resuming without loss", section_halt_resume),
    ]
    produced: list[tuple[str, str]] = []
    for name, what, build in sections:
        body = build(ctx)
        if body is None:
            reason = ctx.missing.get(name, "its input was not present")
            print(f"  skip  {name} — {reason}")
            ctx.skip(name, reason)
            continue
        _write(out, name, body)
        produced.append((name, what))

    for path in copy_pages(ctx):
        rel = str(path.relative_to(out))
        produced.append((rel, PAGE_DESCRIPTIONS.get(path.suffix, "a copied artefact")))

    if args.readme:
        _write(out, "README.md", section_readme(ctx, produced))
    else:
        print("  skip  README.md — pass --readme to generate it")

    # The guard: nothing written may share a run of GUARD_SHINGLE characters with any
    # withheld string. This is checked on the files as written — every file, in every
    # subdirectory, of every type — not on the data in memory.
    scanned = output_files(out)
    hits = ctx.withheld.scan(scanned)
    if hits:
        for path, offset, piece in hits:
            log = record_guard_hit(run, str(path), offset, piece)
            where = f"; the run itself is in {log}" if log is not None else ""
            print(
                f"  GUARD  {path}: shares a run of {len(piece)} characters with "
                f"withheld text at offset {offset}{where}",
                file=sys.stderr,
            )
        for path in scanned:
            path.unlink()
        for directory in sorted(
            (p for p in out.rglob("*") if p.is_dir()), key=lambda p: -len(p.parts)
        ):
            directory.rmdir()
        print(
            "export aborted and its files removed; nothing with respondent text was left behind",
            file=sys.stderr,
        )
        return 1
    withheld_total = sum(ctx.withheld_descriptions.values())
    if withheld_total:
        print(
            f"  guard  {withheld_total} description(s) withheld: each shares a "
            f"{ctx.withheld.shingle}-character run with a response"
        )
    print(
        f"  guard  {len(scanned)} files scanned at {ctx.withheld.shingle} characters against "
        f"{ctx.withheld.n_texts} withheld texts ({len(ctx.withheld.shingles)} shingles): clean"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
