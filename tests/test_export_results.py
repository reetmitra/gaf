"""The results exporter's guard, its sections, and the files it refuses to ship.

`scripts/export_results.py` is the only path by which anything computed from a real
coding reaches a tracked directory. Everything it reads holds respondent text; nothing
it writes may. The guard is the contract: every text the run directories hold is fed to
:class:`Withheld`, every file the exporter writes is re-read against it, and a single
shared run of ``GUARD_SHINGLE`` characters deletes the whole export.

These tests are the proof of that contract, and every fixture in them is invented. The
"respondent sentences" planted below are about a harbour timetable and a bicycle
workshop; no real response, and no fragment of one, appears in this file. Two controls
(`test_the_planted_sentence_really_is_in_the_synthetic_run`, and the assertions that a
clean description *is* emitted) fail if the fixtures ever stop carrying the thing the
guard is supposed to catch.

Validation principle: **transparency** — the exporter states what it withheld and why,
and refuses rather than shipping something it cannot account for.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "gaf_export_results", REPO_ROOT / "scripts" / "export_results.py"
)
assert _SPEC is not None and _SPEC.loader is not None
xr = importlib.util.module_from_spec(_SPEC)
sys.modules["gaf_export_results"] = xr
_SPEC.loader.exec_module(xr)


# --------------------------------------------------------------------------- #
# Invented material. None of this is, or resembles, a survey response.
# --------------------------------------------------------------------------- #

#: The planted "respondent sentence". Long enough to exceed GUARD_SHINGLE several
#: times over, and about a subject no survey in this project asked about.
PLANTED = (
    "The harbour timetable was repainted in March and the ferry now leaves before dawn."
)

#: A second one, for the tests that need two distinct leaks.
PLANTED_TWO = "A bicycle workshop opened beside the lighthouse and mends wheels on Sundays."

#: A description that shares nothing with any planted sentence.
CLEAN_DESCRIPTION = "Accounts of scheduling and its effects."

#: A description that quotes the planted sentence outright.
DIRTY_DESCRIPTION = "Accounts in which " + PLANTED

QUESTION = "An invented question, asked so the fixture has one."


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _write_text(path: Path, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


# --------------------------------------------------------------------------- #
# A synthetic run directory and a synthetic organised human coding
# --------------------------------------------------------------------------- #


def build_run(root: Path, *, segment: str = PLANTED, description: str = CLEAN_DESCRIPTION) -> Path:
    """A machine run directory carrying exactly the files the exporter reads."""
    run = root / "run"
    _write_json(
        run / "corpus.json",
        {
            "responses": [
                {
                    "id": 901,
                    "content": segment + " It also mentions the quay.",
                    "question": QUESTION,
                    "source": "invented",
                    "meta": {"source_number": 901},
                },
                {
                    "id": 902,
                    "content": PLANTED_TWO + " The workshop keeps odd hours.",
                    "question": QUESTION,
                    "source": "invented",
                    "meta": {"source_number": 902, "encoding_repaired": True},
                },
            ]
        },
    )
    _write_json(
        run / "assignments.json",
        [
            {"response_id": 901, "segment": segment, "code": "harbour-timetables"},
            {"response_id": 902, "segment": PLANTED_TWO, "code": "harbour-repairs"},
        ],
    )
    _write_json(
        run / "codebook.json",
        {
            "codes": [
                {
                    "id": "code-0001",
                    "name": "harbour",
                    "parent_id": None,
                    "description": "The top-level family for harbour matters.",
                    "evidence": [],
                    "created_in_snapshot": "snap-a",
                    "meta": {},
                },
                {
                    "id": "code-0002",
                    "name": "harbour-timetables",
                    "parent_id": "code-0001",
                    "description": description,
                    "evidence": [{"response_id": 901, "quote": segment, "verified": True}],
                    "created_in_snapshot": "snap-a",
                    "meta": {},
                },
                {
                    "id": "code-0003",
                    "name": "harbour-repairs",
                    "parent_id": "code-0001",
                    "description": "Accounts of things being mended.",
                    "evidence": [{"response_id": 902, "quote": PLANTED_TWO, "verified": True}],
                    "created_in_snapshot": "snap-a",
                    "meta": {},
                },
            ]
        },
    )
    _write_json(
        run / "stats.json",
        {
            "run_id": "invented",
            "n_responses": 2,
            "n_segments": 2,
            "assignments": 2,
            "codes_final": 3,
            "families_final": 1,
            "space_id": "lexical-v1-512",
            "offline": True,
            "agreement_rate": 1.0,
            "candidates_proposed": {"coder_a": 2, "coder_b": 2},
            "candidates_accepted": 2,
            "candidates_dropped": {"structural": 0, "fit": 0, "dispute": 0},
            "routes": {"CREATE": 3, "MERGE": 1, "JUDGE": 0},
            "llm": {"calls": 4},
            "checkpoint_due": {"fires": True, "reason": "an invented reason", "batch": 1},
            "snapshot_ids": ["snap-a"],
            "findings": {"S2": {"ERROR": 0, "WARN": 0, "INFO": 2}},
            "caveats": ["An invented caveat the run printed about itself."],
            "decision_trace": [
                {
                    "batch": 1,
                    "responses_coded": 2,
                    "responses_in_batch": 2,
                    "responses_since_checkpoint": 2,
                    "new_codes": 3,
                    "cumulative_codes": 3,
                    "near_duplicate_pairs": 0,
                    "spike": {
                        "batch": 1,
                        "new_codes": 3,
                        "baseline": 0.0,
                        "ratio": None,
                        "rule": "absolute",
                        "window": 3,
                        "reason": "an invented spike reason",
                    },
                    "fired": ["handover.new_codes", "handover.spike"],
                    "held": [],
                    "trigger": "health",
                    "verdict": "checkpoint_due",
                    "reason": "an invented handover reason",
                }
            ],
            "halted_at_batch": None,
            "responses_uncoded": 0,
        },
    )
    _write_json(run / "findings.json", [])
    return run


def build_analysis(run: Path, *, name: str = "analysis") -> Path:
    """The `gaf analyse` output directory, in the shapes T2 and T3 publish."""
    adir = run / name
    _write_json(
        adir / "occurrence_matrix.json",
        {
            "response_ids": [901, 902],
            "code_names": ["harbour-repairs", "harbour-timetables"],
            "filter": {
                "n_responses": 2,
                "min_code_frequency": 1,
                "threshold": 1,
                "binding_rule": "absolute",
                "n_kept": 2,
                "n_dropped": 0,
                "kept": ["harbour-repairs", "harbour-timetables"],
                "dropped": [],
            },
        },
    )
    _write_json(
        adir / "clusters.json",
        {
            "n_responses": 2,
            "n_codes": 2,
            "n_clusters": 2,
            "cut_distance": 1.0,
            "cluster_mean_highlight": 0.4,
            "members": {"1": [901], "2": [902]},
            "means": {
                "1": [{"code": "harbour-timetables", "mean": 1.0, "count": 1, "prominent": True}],
                "2": [{"code": "harbour-repairs", "mean": 1.0, "count": 1, "prominent": True}],
            },
            "schedule": {
                "rule": "n_clusters = n_samples - break_stage",
                "break_stage": 0,
                "n_steps": 1,
                "break_delta": 1.0,
                "steps": [{"stage": 1, "distance": 1.0, "delta": 1.0, "size": 2}],
                "warnings": ["an invented warning about this partition"],
            },
        },
    )
    _write_json(
        adir / "saturation.json",
        {
            "batch_size": 10,
            "total_codes": 2,
            "saturated_at_batch": 1,
            "points": [
                {
                    "batch": 1,
                    "responses_in_batch": 2,
                    "cumulative_responses": 2,
                    "new_codes": 2,
                    "cumulative_codes": 2,
                    "new_code_names": ["harbour-repairs", "harbour-timetables"],
                }
            ],
        },
    )
    _write_json(
        adir / "growth.json",
        {
            "source": "assignments",
            "batch_size": 10,
            "total_codes": 2,
            "saturated_at_batch": 1,
            "points": [
                {
                    "batch": 1,
                    "responses_in_batch": 2,
                    "cumulative_responses": 2,
                    "new_codes": 2,
                    "cumulative_codes": 2,
                    "new_codes_per_response": 1.0,
                    "new_code_names": ["harbour-repairs", "harbour-timetables"],
                }
            ],
        },
    )
    _write_json(
        adir / "patterns.json",
        {
            "n_responses": 2,
            "n_codes": 2,
            "min_support": 2,
            "filter": {"n_kept": 2, "n_dropped": 0, "threshold": 1, "binding_rule": "absolute"},
            "responses": [
                {
                    "response_id": 901,
                    "family_signature": ["harbour"],
                    "code_set": ["harbour-timetables"],
                    "nearest": [{"response_id": 902, "jaccard": 0.0}],
                }
            ],
            "groups": [{"family_signature": ["harbour"], "response_ids": [901, 902], "size": 2}],
            "singleton_response_ids": [],
            "code_cooccurrence": {
                "names": ["harbour-repairs", "harbour-timetables"],
                "counts": [[1, 0], [0, 1]],
                "jaccard": [[1.0, 0.0], [0.0, 1.0]],
            },
            "family_cooccurrence": {"names": ["harbour"], "counts": [[2]], "jaccard": [[1.0]]},
            "combinations": {
                "min_support": 2,
                "pairs": [
                    {
                        "codes": ["harbour-repairs", "harbour-timetables"],
                        "support": 2,
                        "share": 1.0,
                        "lift": 1.0,
                    }
                ],
                "triples": [],
                "triple_bound": 20000,
                "triple_candidates_total": 0,
                "triple_candidates_considered": 0,
                "triple_bound_hit": False,
            },
        },
    )
    _write_json(
        adir / "affinity.json",
        {
            "space_id": "lexical-v1-512",
            "alpha": 0.7,
            "threshold": 0.5,
            "n_leaves_total": 2,
            "n_leaves_clustered": 2,
            "offline_caveat": "An invented caveat about the offline similarity space.",
            "excluded": [],
            "groups": [
                {
                    "members": ["harbour-repairs", "quay-repairs"],
                    "families": ["harbour", "quay"],
                    "cross_family": True,
                    "total_responses": 2,
                    "per_code_frequency": {"harbour-repairs": 1, "quay-repairs": 1},
                    "label_suggestion": "repairs",
                    "label_is_mechanical": True,
                    "size": 2,
                }
            ],
            "singleton_leaves": ["harbour-timetables"],
            "cross_family_subcodes": [
                {
                    "sub_label": "repairs",
                    "families": ["harbour", "quay"],
                    "codes": ["harbour-repairs", "quay-repairs"],
                }
            ],
        },
    )
    _write_text(adir / "dendrogram.svg", "<svg xmlns='x'><text>invented</text></svg>\n")
    _write_text(adir / "saturation.svg", "<svg xmlns='x'><text>invented</text></svg>\n")
    return adir


def build_crosswalk(adir: Path) -> Path:
    return _write_json(
        adir / "crosswalk.json",
        {
            "space_id": "lexical-v1-512",
            "names_only": False,
            "tau_high": 0.8,
            "tau_low": 0.45,
            "source_has_descriptions": True,
            "target_has_descriptions": True,
            "source_described_leaves": 2,
            "target_described_leaves": 2,
            "fair_mode_note": "An invented note about the fairness of this comparison.",
            "n_source_leaves": 2,
            "n_target_leaves": 2,
            "mappings": [
                {
                    "source": "harbour-timetables",
                    "hungarian": {"target": "quay-timetables", "score": 0.6, "band": "grey"},
                    "nearest": {"target": "quay-timetables", "score": 0.6, "band": "grey"},
                },
                {
                    "source": "harbour-repairs",
                    "hungarian": {"target": None, "score": None, "band": None},
                    "nearest": {"target": "quay-timetables", "score": 0.2, "band": "unmapped"},
                },
            ],
            "source_family_rollup": [
                {
                    "family": "harbour",
                    "n_leaves": 2,
                    "distribution": {"quay": 1},
                    "n_other_families": 1,
                    "scattered": False,
                    "n_unmapped": 1,
                }
            ],
            "target_family_rollup": [
                {
                    "family": "quay",
                    "n_leaves": 2,
                    "distribution": {"harbour": 1},
                    "n_source_leaves": 1,
                    "n_source_families": 1,
                    "drawn_from_several_families": False,
                    "n_blind_spots": 1,
                }
            ],
            "unmapped_target_leaves": ["quay-moorings"],
            "unmapped_source_leaves": ["harbour-repairs"],
        },
    )


def build_timeline(run: Path) -> Path:
    _write_json(
        run / "timeline.json",
        {
            "run_id": "invented",
            "steps": [
                {
                    "response_id": 901,
                    "batch": 1,
                    "snapshot_id": "snap-a",
                    "codes_created": ["harbour-timetables"],
                    "codes_merged": [],
                    "n_assignments": 1,
                    "duplicate_of": None,
                }
            ],
            "batches": [
                {
                    "batch": 1,
                    "snapshot_id": "snap-a",
                    "responses": [901, 902],
                    "n_responses": 2,
                    "new_codes": ["harbour-repairs", "harbour-timetables"],
                    "n_new_codes": 2,
                    "merges": 1,
                    "cumulative_codes": 3,
                    "judge_consultations": 0,
                    "handover": {
                        "batch": 1,
                        "verdict": "checkpoint_due",
                        "reason": "an invented handover reason",
                        "fired_rules": ["handover.new_codes"],
                    },
                }
            ],
            "snapshot_diffs": [
                {
                    "from_snapshot": "snap-a",
                    "to_snapshot": "snap-b",
                    "reason": "checkpoint_apply",
                    "added": ["harbour-repairs"],
                    "removed": [],
                    "renamed": [{"from": "harbour-old", "to": "harbour-repairs"}],
                }
            ],
            "biographies": {
                "code-0002": {
                    "code_id": "code-0002",
                    "name": "harbour-timetables",
                    "family": "harbour",
                    "born": {
                        "origin": "coded",
                        "response_id": 901,
                        "batch": 1,
                        "checkpoint_id": None,
                        "snapshot_id": "snap-a",
                        "coders": ["coder_a"],
                        "predecessor": None,
                    },
                    "evidence_over_time": [{"kind": "response", "ref": "901", "n_evidence": 1}],
                    "fate_kind": "alive",
                    "fate": "alive",
                    "successors": [],
                    "reparenting": [],
                }
            },
            "checkpoints": [],
        },
    )
    return _write_json(
        run / "reorganisation_trail.json",
        {"run_id": "invented", "n_checkpoints": 0, "entries": [], "lineage": []},
    )


def build_human(
    root: Path,
    *,
    segment: str = PLANTED,
    example: str = PLANTED_TWO,
    description: str = CLEAN_DESCRIPTION,
) -> Path:
    """An organised human coding, as `gaf codebook organise --out` writes it."""
    human = root / "human"
    _write_json(
        human / "golden.json",
        [
            {"response_id": 901, "segment": segment, "code": "quay-timetables"},
            {"response_id": 902, "segment": example, "code": "quay-repairs"},
        ],
    )
    _write_json(
        human / "placement.json",
        {
            "path": "invented.csv",
            "total": 5,
            "mapped": 3,
            "exact": 1,
            "fuzzy": 1,
            "resolved": 1,
            "ambiguous": 1,
            "unlocated": 1,
            "coded_response_count": 2,
            "per_response": {"901": 2, "902": 1},
            "mappings": [
                {
                    "highlight_id": "0",
                    "tag": "quay-timetables",
                    "content": segment,
                    "response_id": 901,
                    "outcome": "exact",
                    "score": 1.0,
                    "candidates": [901],
                    "span": [0, 10],
                },
                {
                    "highlight_id": "1",
                    "tag": "quay-repairs",
                    "content": example,
                    "response_id": None,
                    "outcome": "ambiguous",
                    "score": 0.9,
                    "candidates": [901, 902],
                    "span": None,
                },
                {
                    "highlight_id": "2",
                    "tag": "quay-moorings",
                    "content": "a short invented highlight",
                    "response_id": None,
                    "outcome": "unlocated",
                    "score": 0.4,
                    "candidates": [],
                    "span": None,
                },
            ],
        },
    )
    _write_json(
        human / "organised.json",
        {
            "pair_count": 5,
            "segment_count": 5,
            "parent_count": 1,
            "leaf_count": 2,
            "includes_examples": True,
            "meta": {
                "source": "human-tagged",
                "description_source": "pi-codebook-md",
                "definitions_path": "invented_codebook.md",
                "tagged_path": "invented.csv",
                "description_sources": {
                    "quay-timetables": "pi-codebook-md",
                    "quay-repairs": "pi-codebook-md",
                },
            },
            "codes": [
                {
                    "name": "quay",
                    "sub": "",
                    "level": 1,
                    "count": 5,
                    "rows": [],
                    "description": "The top-level family for quay matters.",
                    "leaf": False,
                    "children": [
                        {
                            "name": "quay-timetables",
                            "sub": "timetables",
                            "level": 2,
                            "count": 3,
                            "rows": [1, 2, 3],
                            "description": description,
                            "leaf": True,
                            "children": [],
                            "example_count": 1,
                            "example_note": "",
                            "examples": [example],
                        },
                        {
                            "name": "quay-repairs",
                            "sub": "repairs",
                            "level": 2,
                            "count": 2,
                            "rows": [4, 5],
                            "description": "Accounts of things being mended.",
                            "leaf": True,
                            "children": [],
                            "example_count": 0,
                            "example_note": "only one segment is associated with this code",
                            "examples": [],
                        },
                    ],
                }
            ],
            "consolidations": [
                {
                    "from": "quay-side-moorings",
                    "to": "quay_side-moorings",
                    "rule": "family_separator",
                    "rows": [6],
                }
            ],
            "notes": [
                {
                    "category": "single_segment_leaf",
                    "subject": "quay-repairs",
                    "message": "an invented note",
                    "data": {},
                },
                {
                    "category": "shared_subcode",
                    "subject": "repairs",
                    "message": "an invented note",
                    "data": {"sub": "repairs", "parents": ["quay", "harbour"]},
                },
            ],
        },
    )
    _write_json(
        human / "codebook.json",
        {
            "codes": [
                {
                    "id": "h-0001",
                    "name": "quay",
                    "parent_id": None,
                    "description": "The top-level family for quay matters.",
                    "evidence": [],
                    "created_in_snapshot": "human",
                    "meta": {"description_source": "pi-codebook-md"},
                },
                {
                    "id": "h-0002",
                    "name": "quay-timetables",
                    "parent_id": "h-0001",
                    "description": description,
                    "evidence": [{"response_id": 901, "quote": segment, "verified": True}],
                    "created_in_snapshot": "human",
                    "meta": {"description_source": "pi-codebook-md"},
                },
            ]
        },
    )
    _write_json(
        human / "golden_checks.json",
        [
            {
                "check_id": "S3",
                "severity": "WARN",
                "subject": "quay-repairs",
                "message": "an invented structural message",
                "data": {"marker": "sub_code_first"},
            }
        ],
    )
    _write_text(human / "tree.mmd", "flowchart LR\n  ROOT([\"Codebook\"])\n")
    return human


def build_pages(directory: Path, *, body: str = "a page with no respondent text") -> Path:
    """The `gaf views` output: one HTML page and the Mermaid tree beside it."""
    views = directory / "views"
    _write_text(views / "views.html", f"<html><body><p>{body}</p></body></html>\n")
    _write_text(views / "tree.mmd", "flowchart LR\n  ROOT([\"Codebook\"])\n")
    return views


def export(
    tmp_path: Path,
    run: Path,
    *,
    human: Path | None = None,
    out: str = "out",
    readme: bool = True,
    extra: list[str] | None = None,
) -> tuple[int, Path]:
    target = tmp_path / out
    argv = ["--run", str(run), "--out", str(target), "--label", "An invented sample"]
    if human is not None:
        argv += ["--human", str(human)]
    if readme:
        argv.append("--readme")
    argv += extra or []
    return xr.main(argv), target


def full_export(tmp_path: Path, **kwargs: Any) -> tuple[int, Path, Path, Path]:
    """The whole shape: run + analysis + crosswalk + timeline + human + both pages."""
    run = build_run(tmp_path, **kwargs)
    adir = build_analysis(run)
    build_crosswalk(adir)
    build_timeline(run)
    build_pages(run)
    human = build_human(tmp_path, **kwargs)
    build_analysis(human, name="analysis_golden")
    build_pages(human)
    code, out = export(tmp_path, run, human=human)
    return code, out, run, human


def files_under(out: Path) -> list[str]:
    return sorted(str(p.relative_to(out)) for p in out.rglob("*") if p.is_file())


# --------------------------------------------------------------------------- #
# 1. Withheld: what it collects and what it catches
# --------------------------------------------------------------------------- #


def test_withheld_catches_a_planted_sentence_and_reports_the_shingle():
    withheld = xr.Withheld()
    withheld.add(PLANTED)
    hit = withheld.first_hit("Some preamble. " + PLANTED + " Some more.")
    assert hit is not None
    assert len(hit) == xr.GUARD_SHINGLE
    assert hit in xr.Withheld._norm(PLANTED)


def test_withheld_passes_text_that_shares_nothing():
    withheld = xr.Withheld()
    withheld.add(PLANTED)
    assert withheld.first_hit(CLEAN_DESCRIPTION) is None
    assert withheld.is_clean(CLEAN_DESCRIPTION)


def test_withheld_keeps_a_short_string_whole():
    withheld = xr.Withheld()
    withheld.add("short phrase")
    assert not withheld.is_clean("short phrase")
    assert withheld.is_clean("a different short phrase entirely")


def test_withheld_sees_the_space_a_cell_puts_around_a_string():
    """A run of 19 characters plus the space before them is a 20-character hit in a file.

    The file-level `scan` found one that the per-item check had passed, because the
    per-item check trimmed the string and so never formed a window that began on the space.
    """
    withheld = xr.Withheld()
    withheld.add("so alpha beta gamma de")
    assert not withheld.is_clean("alpha beta gamma dezzz")
    assert withheld.is_clean("beta gamma dezzz")


def test_a_description_containing_a_whole_short_response_is_withheld():
    """The repository's provenance test keeps a short response whole and finds it anywhere.

    Doing that to every page aborts the export on the phrases a corpus repeats, so the exporter
    asks it only of a description, the one place text written by a model can echo a response.
    """
    withheld = xr.Withheld()
    xr._harvest({"content": "job security"}, withheld)  # 12 characters: the floor
    xr._harvest({"content": "ai jobs"}, withheld)  # below the floor: any sentence can say it
    text, clean = xr.guarded_description("the main worry is job security for many", withheld)
    assert not clean and text == xr.WITHHELD_DESCRIPTION
    assert xr.guarded_description("the main worry is ai jobs for many", withheld)[1]


def test_withheld_ignores_case_and_whitespace():
    withheld = xr.Withheld()
    withheld.add(PLANTED)
    noisy = PLANTED.upper().replace(" ", "\n   ")
    assert not withheld.is_clean(noisy)


def test_feed_run_collects_corpus_segments_and_evidence_quotes(tmp_path: Path):
    run = build_run(tmp_path)
    withheld = xr.Withheld()
    xr.feed_run(run, withheld)
    assert not withheld.is_clean(PLANTED)
    assert not withheld.is_clean(PLANTED_TWO)


def test_feed_human_collects_the_organised_examples_and_the_highlight_contents(tmp_path: Path):
    human = build_human(tmp_path, segment="A segment invented for this fixture only.")
    withheld = xr.Withheld()
    xr.feed_human(human, withheld)
    # PLANTED_TWO reaches Withheld only through organised.json's examples and through
    # placement.json's highlight contents: the golden rows carry the other string.
    assert not withheld.is_clean(PLANTED_TWO)


def test_feed_run_is_applied_to_every_run_directory_named(tmp_path: Path):
    run = build_run(tmp_path)
    seeded = build_run(tmp_path / "s", segment=PLANTED_TWO)
    withheld = xr.Withheld()
    xr.feed_run(run, withheld)
    xr.feed_run(seeded, withheld)
    assert not withheld.is_clean(PLANTED)
    assert not withheld.is_clean(PLANTED_TWO)


# --------------------------------------------------------------------------- #
# 2. The per-item description guard (the orchestrator's addendum)
# --------------------------------------------------------------------------- #


def test_a_clean_description_is_emitted_verbatim():
    withheld = xr.Withheld()
    withheld.add(PLANTED)
    text, clean = xr.guarded_description(CLEAN_DESCRIPTION, withheld)
    assert clean is True
    assert text == CLEAN_DESCRIPTION


def test_a_colliding_description_is_replaced_not_trimmed():
    withheld = xr.Withheld()
    withheld.add(PLANTED)
    text, clean = xr.guarded_description(DIRTY_DESCRIPTION, withheld)
    assert clean is False
    assert text == xr.WITHHELD_DESCRIPTION
    assert PLANTED[:30] not in text


def test_an_empty_description_is_neither_emitted_nor_flagged_as_a_collision():
    withheld = xr.Withheld()
    withheld.add(PLANTED)
    text, clean = xr.guarded_description("", withheld)
    assert clean is True
    assert text == ""


def test_the_colliding_description_never_reaches_the_export(tmp_path: Path):
    code, out, _run, _human = full_export(tmp_path, description=DIRTY_DESCRIPTION)
    assert code == 0, "a colliding description must be withheld, not abort the export"
    blob = "\n".join(p.read_text(encoding="utf-8") for p in out.rglob("*.md"))
    assert xr.WITHHELD_DESCRIPTION in blob
    assert PLANTED[:30].casefold() not in blob.casefold()


def test_a_clean_description_does_reach_the_export(tmp_path: Path):
    code, out, _run, _human = full_export(tmp_path)
    assert code == 0
    blob = "\n".join(p.read_text(encoding="utf-8") for p in out.rglob("*.md"))
    assert CLEAN_DESCRIPTION in blob, "the control: a clean description is shareable"


def test_the_export_counts_the_descriptions_it_withheld(tmp_path: Path, capsys):
    code, out, _run, _human = full_export(tmp_path, description=DIRTY_DESCRIPTION)
    assert code == 0
    printed = capsys.readouterr().out
    assert "withheld" in printed.lower()
    blob = "\n".join(p.read_text(encoding="utf-8") for p in out.rglob("*.md"))
    assert "1" in blob


# --------------------------------------------------------------------------- #
# 3. The self-scan deletes the output rather than shipping it
# --------------------------------------------------------------------------- #


def test_the_planted_sentence_really_is_in_the_synthetic_run(tmp_path: Path):
    """The control. If this fails, every leak test below is passing vacuously."""
    run = build_run(tmp_path)
    blob = "\n".join(p.read_text(encoding="utf-8") for p in run.rglob("*.json"))
    assert PLANTED in blob


def test_a_planted_sentence_in_a_markdown_file_deletes_the_whole_export(tmp_path: Path):
    run = build_run(tmp_path)
    human = build_human(tmp_path)
    build_analysis(run)
    # A check whose message quotes the text it fired on: the kind of leak the guard
    # exists for, and one the structural section does reproduce verbatim.
    checks = json.loads((human / "golden_checks.json").read_text(encoding="utf-8"))
    checks[0]["message"] = PLANTED
    _write_json(human / "golden_checks.json", checks)
    code, out = export(tmp_path, run, human=human)
    assert code == 1
    assert files_under(out) == [], "the export must delete its own output on a hit"


def test_a_planted_sentence_in_a_copied_html_page_withholds_that_page(tmp_path: Path):
    """A whole artefact written elsewhere is one item: it is tested before it is copied,
    and a failing one is named rather than published. The rest of the export stands."""
    run = build_run(tmp_path)
    build_analysis(run)
    human = build_human(tmp_path)
    build_pages(run, body=PLANTED)
    build_pages(human)
    code, out = export(tmp_path, run, human=human)
    assert code == 0
    names = files_under(out)
    assert "views-machine/views.html" not in names
    assert "views-human/views.html" in names, "the clean page is still published"
    readme = (out / "README.md").read_text(encoding="utf-8")
    assert "views-machine/views.html" in readme
    assert "withheld" in readme.lower()


def test_a_planted_sentence_in_a_copied_mermaid_tree_withholds_that_tree(tmp_path: Path):
    run = build_run(tmp_path)
    build_analysis(run)
    human = build_human(tmp_path)
    build_pages(run)
    build_pages(human)
    _write_text(human / "tree.mmd", f'flowchart LR\n  A["{PLANTED}"]\n')
    code, out = export(tmp_path, run, human=human)
    assert code == 0
    assert "tree.mmd" not in files_under(out)


def test_a_planted_sentence_in_a_copied_svg_withholds_that_figure(tmp_path: Path):
    run = build_run(tmp_path)
    adir = build_analysis(run)
    _write_text(adir / "dendrogram.svg", f"<svg><text>{PLANTED}</text></svg>\n")
    human = build_human(tmp_path)
    build_analysis(human, name="analysis_golden")
    _write_text(
        human / "analysis_golden" / "dendrogram.svg", f"<svg><text>{PLANTED}</text></svg>\n"
    )
    code, out = export(tmp_path, run, human=human)
    assert code == 0
    assert "dendrogram.svg" not in files_under(out)
    assert "saturation.svg" in files_under(out), "the clean figure is still published"


def test_a_line_of_a_copied_document_is_withheld_on_its_own(tmp_path: Path):
    run = build_run(tmp_path)
    build_analysis(run)
    _write_text(
        run / "decision_matrix.md",
        "| rule | condition |\n|---|---|\n| `fast.accept` | a clean invented condition |\n"
        f"| `fast.reject` | {PLANTED} |\n",
    )
    human = build_human(tmp_path)
    code, out = export(tmp_path, run, human=human)
    assert code == 0
    body = (out / "10-handover.md").read_text(encoding="utf-8")
    assert "`fast.accept`" in body, "the clean line survives"
    assert "`fast.reject`" not in body, "the colliding line does not"
    assert xr.WITHHELD_LINE in body
    assert PLANTED[:30].casefold() not in body.casefold()


def test_a_question_a_respondent_echoed_is_withheld(tmp_path: Path):
    run = build_run(tmp_path, segment=PLANTED)
    corpus = json.loads((run / "corpus.json").read_text(encoding="utf-8"))
    for response in corpus["responses"]:
        response["question"] = "Tell us: " + PLANTED
    _write_json(run / "corpus.json", corpus)
    build_analysis(run)
    human = build_human(tmp_path)
    code, out = export(tmp_path, run, human=human)
    assert code == 0
    body = (out / "01-inputs.md").read_text(encoding="utf-8")
    assert "wording is withheld" in body
    assert PLANTED[:30].casefold() not in body.casefold()


def test_a_clean_question_is_still_printed(tmp_path: Path):
    run = build_run(tmp_path)
    build_analysis(run)
    human = build_human(tmp_path)
    code, out = export(tmp_path, run, human=human)
    assert code == 0
    assert QUESTION in (out / "01-inputs.md").read_text(encoding="utf-8")


def test_the_guard_shingle_is_a_stated_parameter(tmp_path: Path, capsys):
    run = build_run(tmp_path)
    build_analysis(run)
    human = build_human(tmp_path)
    code, _out = export(tmp_path, run, human=human, extra=["--guard-shingle", "30"])
    assert code == 0
    assert "scanned at 30 characters" in capsys.readouterr().out


def test_the_guard_scans_files_in_subdirectories(tmp_path: Path):
    code, out, _run, _human = full_export(tmp_path)
    assert code == 0
    scanned = xr.output_files(out)
    assert any(p.parent != out for p in scanned), "the pages live one directory down"
    assert {p.suffix for p in scanned} >= {".md", ".html", ".mmd"}


def test_a_file_the_guard_cannot_read_as_text_fails_the_export(tmp_path: Path, monkeypatch):
    run = build_run(tmp_path)
    build_analysis(run)
    human = build_human(tmp_path)

    original = xr.copy_pages

    def copy_and_plant(ctx: Any) -> list[Path]:
        copied = original(ctx)
        blob = ctx.out / "unreadable.bin"
        blob.write_bytes(b"\xff\xfe\x00 not decodable as utf-8")
        return [*copied, blob]

    monkeypatch.setattr(xr, "copy_pages", copy_and_plant)
    code, out = export(tmp_path, run, human=human)
    assert code == 1
    assert files_under(out) == []


# --------------------------------------------------------------------------- #
# 4. The sections, present and absent
# --------------------------------------------------------------------------- #


def test_a_full_export_writes_every_section_and_both_pages(tmp_path: Path):
    code, out, _run, _human = full_export(tmp_path)
    assert code == 0
    names = files_under(out)
    for expected in (
        "README.md",
        "01-inputs.md",
        "02-human-codebook.md",
        "03-structural-checks.md",
        "04-clustering.md",
        "05-saturation.md",
        "08-machine-run.md",
        "09-growth.md",
        "10-handover.md",
        "11-patterns.md",
        "12-affinity.md",
        "13-crosswalk.md",
        "14-timeline.md",
    ):
        assert expected in names, f"{expected} missing from {names}"
    assert "views-machine/views.html" in names
    assert "views-machine/tree.mmd" in names
    assert "views-human/views.html" in names
    assert "views-human/tree.mmd" in names
    assert "tree.mmd" in names


def test_a_missing_input_skips_its_section_and_the_readme_says_so(tmp_path: Path, capsys):
    run = build_run(tmp_path)  # no analysis directory, no timeline, no pages
    human = build_human(tmp_path)
    code, out = export(tmp_path, run, human=human)
    assert code == 0
    names = files_under(out)
    assert "11-patterns.md" not in names
    assert "13-crosswalk.md" not in names
    readme = (out / "README.md").read_text(encoding="utf-8")
    assert "patterns" in readme.lower()
    assert "not produced" in readme.lower()
    printed = capsys.readouterr().out
    assert "skip" in printed


def test_the_seeded_run_section_appears_only_when_a_seeded_run_is_named(tmp_path: Path):
    run = build_run(tmp_path)
    build_analysis(run)
    human = build_human(tmp_path)
    code, out = export(tmp_path, run, human=human)
    assert code == 0
    assert "15-seeded-run.md" not in files_under(out)

    seeded = build_run(tmp_path / "seed_root", segment=PLANTED)
    code, out2 = export(
        tmp_path, run, human=human, out="out2", extra=["--seeded", str(seeded)]
    )
    assert code == 0
    assert "15-seeded-run.md" in files_under(out2)


def test_the_halt_and_resume_section_needs_both_halves(tmp_path: Path):
    run = build_run(tmp_path)
    build_analysis(run)
    human = build_human(tmp_path)
    halted = build_run(tmp_path / "halted_root")
    code, out = export(
        tmp_path, run, human=human, extra=["--halted", str(halted)]
    )
    assert code == 0
    body = (out / "16-halt-and-resume.md").read_text(encoding="utf-8")
    assert "resum" in body.lower()


def test_quote_placement_is_reported_as_three_separate_numbers(tmp_path: Path):
    code, out, _run, _human = full_export(tmp_path)
    assert code == 0
    body = (out / "01-inputs.md").read_text(encoding="utf-8")
    for word in ("exact", "fuzzy", "resolved", "ambiguous", "unlocated"):
        assert word in body.lower(), f"placement must name {word} on its own line"
    assert "resolved" in body.lower()
    assert "coded set" in body.lower()


def test_the_affinity_section_flags_a_group_that_spans_families(tmp_path: Path):
    code, out, _run, _human = full_export(tmp_path)
    assert code == 0
    body = (out / "12-affinity.md").read_text(encoding="utf-8")
    assert "spans" in body.lower() or "cross-family" in body.lower()
    assert "`quay-repairs`" in body


def test_the_handover_section_names_the_rule_that_fired(tmp_path: Path):
    code, out, _run, _human = full_export(tmp_path)
    assert code == 0
    body = (out / "10-handover.md").read_text(encoding="utf-8")
    assert "handover.new_codes" in body
    assert "checkpoint_due" in body


def test_the_growth_section_carries_both_codings_when_both_are_present(tmp_path: Path):
    code, out, _run, _human = full_export(tmp_path)
    assert code == 0
    body = (out / "09-growth.md").read_text(encoding="utf-8")
    assert body.lower().count("batch") >= 2


# --------------------------------------------------------------------------- #
# 5. Determinism, refusals and the README
# --------------------------------------------------------------------------- #


def test_two_exports_of_the_same_inputs_are_byte_identical(tmp_path: Path):
    code_a, out_a, run, human = full_export(tmp_path)
    assert code_a == 0
    code_b, out_b = export(tmp_path, run, human=human, out="second")
    assert code_b == 0
    assert files_under(out_a) == files_under(out_b)
    for name in files_under(out_a):
        assert (out_a / name).read_bytes() == (out_b / name).read_bytes(), name


def test_the_readme_is_not_written_unless_it_is_asked_for(tmp_path: Path):
    """An existing results directory may hold a hand-written README that records a
    meeting. Re-exporting into it must not silently replace that document."""
    run = build_run(tmp_path)
    build_analysis(run)
    human = build_human(tmp_path)
    code, out = export(tmp_path, run, human=human, readme=False)
    assert code == 0
    assert "README.md" not in files_under(out)


def test_a_missing_run_directory_is_a_usage_error(tmp_path: Path):
    assert xr.main(["--run", str(tmp_path / "nope"), "--out", str(tmp_path / "out")]) == 2


def test_a_missing_human_directory_is_a_usage_error(tmp_path: Path):
    run = build_run(tmp_path)
    code = xr.main(
        ["--run", str(run), "--out", str(tmp_path / "out"), "--human", str(tmp_path / "nope")]
    )
    assert code == 2


def test_the_readme_is_generated_and_lists_what_was_written(tmp_path: Path):
    code, out, _run, _human = full_export(tmp_path)
    assert code == 0
    readme = (out / "README.md").read_text(encoding="utf-8")
    assert "01-inputs.md" in readme
    assert "views-machine/views.html" in readme
    assert "live run" in readme.lower(), "the outstanding ask must be on the page"
    assert "keyword" in readme.lower(), "the offline coder must be named for what it is"


def test_the_readme_carries_no_respondent_text(tmp_path: Path):
    code, out, _run, _human = full_export(tmp_path)
    assert code == 0
    readme = (out / "README.md").read_text(encoding="utf-8").casefold()
    assert PLANTED.casefold()[:30] not in readme
    assert PLANTED_TWO.casefold()[:30] not in readme


def test_a_live_run_is_not_described_as_an_offline_keyword_table(tmp_path: Path):
    """The offline wording is for offline runs only; a run that called models says so."""
    run = build_run(tmp_path)
    human = build_human(tmp_path)
    build_analysis(run)
    stats = json.loads((run / "stats.json").read_text(encoding="utf-8"))
    _write_json(run / "stats.json", {**stats, "offline": False})
    code, out = export(tmp_path, run, human=human)
    assert code == 0
    body = (out / "08-machine-run.md").read_text(encoding="utf-8")
    assert "(live-model coders)" in body
    assert "offline stand-in coder" not in body


@pytest.mark.parametrize("section", ["01-inputs.md", "02-human-codebook.md", "08-machine-run.md"])
def test_no_section_reproduces_a_planted_sentence(tmp_path: Path, section: str):
    code, out, _run, _human = full_export(tmp_path)
    assert code == 0
    body = (out / section).read_text(encoding="utf-8").casefold()
    assert PLANTED.casefold()[:30] not in body
    assert PLANTED_TWO.casefold()[:30] not in body


# --------------------------------------------------------------------------- #
# R2 audit findings
# --------------------------------------------------------------------------- #


def test_the_self_scan_reports_a_hit_by_offset_and_length_not_by_quoting_it(
    tmp_path: Path, capsys
):
    """R2 M-2. A terminal and a CI log are not the run directory."""
    run = build_run(tmp_path)
    human = build_human(tmp_path)
    build_analysis(run)
    checks = json.loads((human / "golden_checks.json").read_text(encoding="utf-8"))
    checks[0]["message"] = PLANTED
    _write_json(human / "golden_checks.json", checks)

    code, out = export(tmp_path, run, human=human)
    assert code == 1
    assert files_under(out) == []

    captured = capsys.readouterr()
    printed = captured.out + captured.err
    assert PLANTED not in printed
    assert xr.Withheld._norm(PLANTED)[: xr.GUARD_SHINGLE] not in printed
    assert "GUARD" in printed
    assert "offset" in printed
    assert f"run of {xr.GUARD_SHINGLE} characters" in printed

    log = run / xr.GUARD_LOG_NAME
    assert log.exists(), "the text itself belongs in the run directory and nowhere else"
    assert xr.Withheld._norm(PLANTED)[: xr.GUARD_SHINGLE] in log.read_text(encoding="utf-8")


def test_a_held_back_page_is_reported_by_offset_and_length_too(tmp_path: Path, capsys):
    """R2 M-2. The per-item guard prints the same way the self-scan does."""
    run = build_run(tmp_path)
    build_analysis(run)
    human = build_human(tmp_path)
    build_pages(run, body=PLANTED)
    build_pages(human)

    code, out = export(tmp_path, run, human=human)
    assert code == 0
    printed = capsys.readouterr().out
    assert PLANTED not in printed
    assert xr.Withheld._norm(PLANTED)[: xr.GUARD_SHINGLE] not in printed
    assert "hold" in printed and "offset" in printed
    assert "views-machine/views.html" not in files_under(out)
    assert xr.Withheld._norm(PLANTED)[: xr.GUARD_SHINGLE] in (
        run / xr.GUARD_LOG_NAME
    ).read_text(encoding="utf-8")


def test_the_run_harvest_reaches_a_json_artefact_two_levels_down(tmp_path: Path):
    """R2 M-4. `feed_run` globbed one level; a deeper artefact was never withheld."""
    run = build_run(tmp_path)
    deep = run / "one" / "two"
    deep.mkdir(parents=True)
    _write_json(deep / "buried.json", {"quote": PLANTED_TWO})
    withheld = xr.Withheld()
    xr.feed_run(run, withheld)
    assert not withheld.is_clean(PLANTED_TWO)


def test_rationale_is_a_withheld_key(tmp_path: Path):
    """R2 C-1. The trail's own prose field is harvested the day a section emits it."""
    assert "rationale" in xr.TEXT_KEYS
    run = build_run(tmp_path)
    _write_json(run / "reorganisation_trail.json", {"entries": [{"rationale": PLANTED_TWO}]})
    withheld = xr.Withheld()
    xr.feed_run(run, withheld)
    assert not withheld.is_clean(PLANTED_TWO)


# --------------------------------------------------------------------------- #
# 6. The at-a-glance page: four figures and the rules that read the run's numbers
#
# Every number below is invented. None is, or is chosen to resemble, a real run's.
# --------------------------------------------------------------------------- #


def metrics_payload(**over: Any) -> dict[str, Any]:
    """An invented `run_metrics.json`: coders 60 of 100 model-seconds, a judge that never backs B."""
    base: dict[str, Any] = {
        "schema": "gaf.run_metrics/1",
        "coder_agreement": {
            "agreed_outright": {"count": 5},
            "grey_zone": {"count": 25},
            "disputed_or_unmatched": {"count": 10},
            "comparisons": 40,
            "unit": "M1 comparison: an invented unit of comparison",
        },
        "judge_siding": {
            "decisions": 25,
            "coder_a": {"count": 10},
            "coder_b": {"count": 0},
            "neither": {"count": 15},
            "basis": "An invented note: coder B's share is zero by construction.",
        },
        "latency": {
            "measured": True,
            "by_role_task_ms": [
                {"role": "coder_a", "task": "code", "n": 3, "total": 30000.0},
                {"role": "coder_b", "task": "code", "n": 3, "total": 30000.0},
                {"role": "judge", "task": "judge_fit", "n": 4, "total": 40000.0},
            ],
            "per_response_model_s": {"n": 3, "mean": 33.33, "median": 30.0, "max": 50.0},
        },
        "spend": {
            "calls": 10,
            "cache_hits": 4,
            "responses": 5,
            "by_role_task": [
                {"role": "coder_a", "task": "code", "model": "model-one", "calls": 3, "cache_hits": 0},
                {"role": "coder_b", "task": "code", "model": "model-two", "calls": 3, "cache_hits": 0},
                {"role": "judge", "task": "judge_fit", "model": "model-two", "calls": 4, "cache_hits": 4},
            ],
        },
    }
    return {**base, **over}


def agreement_payload(kappa: float = 0.04, f1: float = 0.1) -> dict[str, Any]:
    """An invented `agreement.json`, whole enough for the agreement section to render it too."""
    cl = {
        "cohens_kappa": kappa, "f1": f1, "precision": 0.1, "recall": 0.1, "tp": 3, "fp": 20, "fn": 22,
        "tn": 800, "n_responses": 3, "n_codes": 9, "n_cells": 27,
        "observed_agreement": 0.9, "expected_agreement": 0.9,
    }  # fmt: skip
    return {
        "code_level": cl,
        "matched_only": {**cl, "cohens_kappa": 0.5, "n_codes": 2},
        "segment_level": {
            "weighted_precision": 0.1, "weighted_recall": 0.1, "weighted_f1": 0.1,
            "strict_precision": 0.1, "strict_recall": 0.1, "strict_f1": 0.1,
            "overlap_threshold": 0.5, "right_code_wrong_place": 1, "mean_overlap_on_shared_codes": 0.4,
        },
        "matching": {
            "pairs": [], "space_id": "lexical-v1-512", "tau_high": 0.8,
            "n_human_codes": 3, "n_machine_codes": 3,
        },
        "over_coding": [],
        "blind_spots": [],
    }  # fmt: skip


def sweep_payload(*, f1: list[float], current: float, recommended: float, plateau: list[float]) -> dict[str, Any]:
    grid = [0.0, 0.25, 0.5, 0.75, 1.0]
    return {
        "name": "invented", "unit": "invented units", "positive_label": "invented positives",
        "prediction_label": "invented prediction",
        "current": current, "recommended": recommended, "changed": current != recommended,
        "best_f1": max(f1), "f1_at_current": f1[grid.index(current)], "plateau": plateau,
        "n_units": 12, "n_positive": 6,
        "curve": [
            {"threshold": t, "f1": v, "tp": 1, "fp": 1, "fn": 1, "tn": 1, "precision": 0.5, "recall": 0.5}
            for t, v in zip(grid, f1, strict=True)
        ],
    }  # fmt: skip


def calibration_payload() -> dict[str, Any]:
    """`tau_fit` peaks to the edge of the grid; `tau_low` peaks inside it and stays put."""
    return {
        "space_id": "lexical-v1-512",
        "sweeps": {
            "tau_fit": sweep_payload(f1=[0, 0.2, 0.9, 0.9, 0.9], current=0.25, recommended=0.75, plateau=[0.5, 1.0]),
            "tau_low": sweep_payload(f1=[0, 0.5, 1.0, 0.5, 0], current=0.5, recommended=0.5, plateau=[0.5, 0.5]),
        },
    }


def build_glance(run: Path, *, offline: bool = False, metrics: dict[str, Any] | None = None) -> None:
    """Write every input the page reads into a run directory built by `build_run`."""
    stats = json.loads((run / "stats.json").read_text(encoding="utf-8"))
    _write_json(run / "stats.json", {**stats, "offline": offline})
    _write_json(run / "run_metrics.json", metrics if metrics is not None else metrics_payload())
    _write_json(run / "calibration_report.json", calibration_payload())
    _write_json(run / "agreement" / "agreement.json", agreement_payload(0.04, 0.1))
    _write_json(run / "agreement_nameonly" / "agreement.json", agreement_payload(-0.02, 0.2))
    models = {"coder_a": "model-one", "coder_b": "model-two", "judge": "model-two"}
    _write_json(run / "run.json", {"config": {"models": {r: {"model": m} for r, m in models.items()}}})


def glance(live: bool = True, **over: Any) -> Any:
    """A `Glance` built in memory, for the rule tests."""
    models = {"coder_a": "model-one", "coder_b": "model-two", "judge": "model-two"}
    return xr.Glance(
        offline=not live,
        metrics=over.get("metrics", metrics_payload()),
        calibration=over.get("calibration", calibration_payload()),
        agreement=over.get("agreement", [("with descriptions", agreement_payload(0.04))]),
        models=over.get("models", models),
    )


def svg_root(svg: str) -> ET.Element:
    """Parse a figure (valid XML or the test fails) and insist on a title, a description and a scheme."""
    root = ET.fromstring(svg)
    assert root.tag.endswith("svg")
    assert root.findtext("{*}title") and root.findtext("{*}desc")
    assert "prefers-color-scheme:dark" in svg
    return root


def svg_texts(root: ET.Element) -> list[str]:
    return [(t.text or "") for t in root.iter("{http://www.w3.org/2000/svg}text")]


# -- the four figures --


def test_the_model_time_figure_is_xml_and_labels_every_bar_with_seconds_and_share():
    svg = xr.figure_model_time([("coder_a", "code", 30.0), ("judge", "judge_fit", 40.0)])
    texts = svg_texts(svg_root(svg))
    assert "judge / judge_fit" in texts and "coder_a / code" in texts
    assert "40 s (57%)" in texts and "30 s (43%)" in texts
    assert svg == xr.figure_model_time([("judge", "judge_fit", 40.0), ("coder_a", "code", 30.0)])


def test_the_agreement_figure_labels_counts_and_shares_and_shows_a_zero_share():
    svg = xr.figure_agreement(
        metrics_payload()["coder_agreement"], metrics_payload()["judge_siding"]
    )
    texts = svg_texts(svg_root(svg))
    assert "5 (12.5%)" in texts and "25 (62.5%)" in texts and "10 (25.0%)" in texts
    assert "10 (40.0%)" in texts and "0 (0.0%)" in texts and "15 (60.0%)" in texts
    assert svg.count("<rect class=") == 1 + 2 * 3 + 5  # background, swatches, and the five non-empty segments
    only = xr.figure_agreement(None, metrics_payload()["judge_siding"])
    assert "Coder A against coder B" not in only and "judge" in only


def test_the_heldout_figure_draws_a_zero_line_and_a_negative_kappa_left_of_it():
    svg = xr.figure_heldout(
        [("with descriptions", 0.05, -0.02, "3 responses"), ("by name only", 0.1, 0.04, "3 responses")]
    )
    root = svg_root(svg)
    texts = svg_texts(root)
    assert {"0.050", "-0.020", "0.100", "+0.040", "-0.2", "0"} <= set(texts)
    assert svg.count('class="zero"') == 2, "one zero line per group, drawn over the bars"
    negative = next(p for p in root.iter("{http://www.w3.org/2000/svg}path") if "-0.020" in "".join(p.itertext()))
    assert negative.get("d", "").partition("h")[2].startswith("-"), "a negative kappa grows leftwards"
    assert "-0.2" not in svg_texts(svg_root(xr.figure_heldout([("only", 0.1, 0.2, "x")]))), "no room left of zero when none is needed"


def test_the_calibration_figure_marks_the_provisional_and_the_recommended_value():
    sweeps = calibration_payload()["sweeps"]
    svg = xr.figure_calibration(sweeps)
    root = svg_root(svg)
    texts = svg_texts(root)
    assert "provisional 0.25 (F1 0.20)" in texts and "recommended 0.75 (F1 0.90)" in texts
    assert "tau_fit" in texts and "tau_low" in texts and "best F1 0.90 at 0.50-1.00" in texts
    assert svg.count("<polyline") == 2 and svg.count('class="wash"') == 2 + 1  # one band per panel, one in the key
    titles = "".join(t.text or "" for t in root.iter("{http://www.w3.org/2000/svg}title"))
    assert "tau_fit provisional 0.25: F1 0.20" in titles and "tau_low recommended 0.50: F1 1.00" in titles


# -- the rules: each fires, and each does not --


def test_model_time_rule_fires_with_the_share_and_stays_silent_without_its_input():
    (said,) = xr.rule_model_time(glance())
    assert "60 of 100 model-seconds (60%)" in said and "judge 40 (40%)" in said
    assert "coders" in said.split("Most of the time is the")[1][:8]
    assert xr.rule_model_time(glance(metrics=None)) == []
    unmeasured = metrics_payload(latency={"measured": False, "by_role_task_ms": []})
    assert xr.rule_model_time(glance(metrics=unmeasured)) == []
    even = metrics_payload(latency={"measured": True, "by_role_task_ms": [
        {"role": "coder_a", "task": "code", "total": 50000.0}, {"role": "judge", "task": "judge_fit", "total": 50000.0}]})  # fmt: skip
    assert "split about evenly" in xr.rule_model_time(glance(metrics=even))[0]


def test_judge_siding_rule_fires_on_a_zero_share_and_names_the_shared_model():
    (said,) = xr.rule_judge_siding(glance())
    assert "0 of 25 decisions" in said and "coder A in 10 (40.0%)" in said and "neither in 15 (60.0%)" in said
    assert "built into the judge's two verdicts" in said, "the note says the zero is structural"
    assert "same model as coder B (model-two), the coder it never backed" in said
    flipped = metrics_payload(judge_siding={
        "decisions": 25, "coder_a": {"count": 0}, "coder_b": {"count": 10}, "neither": {"count": 15}, "basis": ""})  # fmt: skip
    (said,) = xr.rule_judge_siding(glance(metrics=flipped))
    assert "0 of 25 decisions" in said and "arbitrating" in said and "built into" not in said
    assert "same model as coder B (model-two), so a lean towards coder B may be self-preference" in said
    assert "same model" not in xr.rule_judge_siding(glance(models={"judge": "model-three"}))[0]


def test_judge_siding_rule_needs_twenty_decisions_and_a_zero():
    few = {**metrics_payload()["judge_siding"], "decisions": 19}
    assert xr.rule_judge_siding(glance(metrics=metrics_payload(judge_siding=few))) == []
    both = {**metrics_payload()["judge_siding"], "coder_b": {"count": 3}, "neither": {"count": 12}}
    assert xr.rule_judge_siding(glance(metrics=metrics_payload(judge_siding=both))) == []
    assert xr.rule_judge_siding(glance(metrics=None)) == []


def test_chance_rule_fires_under_a_tenth_and_not_above_it():
    (said,) = xr.rule_chance_agreement(glance())
    assert "no better than chance" in said and "kappa +0.040" in said and "kappa on the 2 matched codes alone is 0.50" in said
    assert "90.0% expected by chance" in said and "F1 0.10" in said
    both = glance(agreement=[("with descriptions", agreement_payload(0.04)), ("by name only", agreement_payload(-0.02))])
    assert "kappa -0.020" in xr.rule_chance_agreement(both)[0] and "by name only" in xr.rule_chance_agreement(both)[0]
    clear = glance(agreement=[("with descriptions", agreement_payload(0.5))])
    assert xr.rule_chance_agreement(clear) == []
    assert xr.rule_chance_agreement(glance(agreement=[])) == []


def test_calibration_rule_fires_on_an_edge_or_a_flat_plateau_and_not_on_a_peak():
    said = xr.rule_calibration_plateau(glance())
    assert len(said) == 1 and said[0].startswith("tau_fit:"), "tau_low peaks inside the grid, narrowly"
    assert "holds from 0.50 to 1.00, right up to the end of the grid" in said[0]
    assert "recommended 0.75 is the middle of that range" in said[0] and "provisional 0.25 scores F1 0.20" in said[0]
    assert "6 of 12 invented units are invented positives" in said[0] and '"at least 0.50"' in said[0]
    flat = calibration_payload()
    flat["sweeps"] = {"tau_mid": sweep_payload(f1=[0, 0.9, 0.9, 0.9, 0.5], current=0.25, recommended=0.5, plateau=[0.25, 0.75])}
    (wide,) = xr.rule_calibration_plateau(glance(calibration=flat))
    assert "right up to the end" not in wide and "holds from 0.25 to 0.75" in wide, "flat, but not at the edge"
    kept = {"sweeps": {"tau_x": sweep_payload(f1=[0, 0.9, 0.9, 0.9, 0.9], current=0.25, recommended=0.25, plateau=[0.25, 1.0])}}
    assert "already inside it, so the sweep keeps it" in xr.rule_calibration_plateau(glance(calibration=kept))[0]
    assert xr.rule_calibration_plateau(glance(calibration=None)) == []


def test_cache_rule_fires_when_calls_were_replayed():
    (said,) = xr.rule_cache_replay(glance())
    assert "4 of 10 model calls (40%) were replayed" in said and "other 6 calls" in said
    none = metrics_payload(spend={"calls": 10, "cache_hits": 0, "responses": 5})
    assert xr.rule_cache_replay(glance(metrics=none)) == []
    assert xr.rule_cache_replay(glance(metrics=None)) == []


def test_response_time_rule_fires_and_counts_the_responses_it_leaves_out():
    (said,) = xr.rule_response_time(glance())
    assert "Each of the 3 responses that reached a model took 33 s" in said and "median 30 s, slowest 50 s" in said
    assert "the other 2 of 5 responses had no model time to count" in said
    assert "about 0.9 hours of model time" in said
    no_n = metrics_payload(latency={"measured": True, "per_response_model_s": {}})
    assert xr.rule_response_time(glance(metrics=no_n)) == []
    assert xr.rule_response_time(glance(metrics=None)) == []


def test_an_offline_run_never_gets_a_claim_about_a_model():
    offline = glance(live=False)
    for rule in (xr.rule_model_time, xr.rule_judge_siding, xr.rule_cache_replay, xr.rule_response_time):
        assert rule(offline) == [], rule.__name__
    assert xr._time_rows(offline) == []
    said = " ".join(line for rule in xr.RULES for line in rule(offline))
    assert "keyword table" in said and "model-seconds" not in said and "judge" not in said.lower()
    assert "the machine's coding" not in said.lower()


# -- the page: registration, absence, the guard --


def glance_export(tmp_path: Path, *, offline: bool = False, metrics: dict[str, Any] | None = None) -> tuple[int, Path, Path]:
    run = build_run(tmp_path)
    build_glance(run, offline=offline, metrics=metrics)
    code, out = export(tmp_path, run, human=build_human(tmp_path))
    return code, out, run


FIGURES = ("model-time.svg", "agreement-judge.svg", "heldout-agreement.svg", "calibration.svg")


def test_the_at_a_glance_page_is_written_listed_and_embeds_its_four_figures(tmp_path: Path):
    code, out, _run = glance_export(tmp_path)
    assert code == 0
    names = files_under(out)
    assert "00-at-a-glance.md" in names and all(f in names for f in FIGURES)
    page = (out / "00-at-a-glance.md").read_text(encoding="utf-8")
    for figure in FIGURES:
        assert f"]({figure})" in page
        svg_root((out / figure).read_text(encoding="utf-8"))
    assert page.index("## Realisations") < page.index("## Where the model's time went")
    assert "The coders took 60 of 100 model-seconds (60%)" in page
    readme = (out / "README.md").read_text(encoding="utf-8")
    assert "[00-at-a-glance.md](00-at-a-glance.md)" in readme and "00-at-a-glance.md" in readme.split("## What is in")[1]


def test_a_missing_input_skips_its_figure_and_the_readme_says_why(tmp_path: Path, capsys):
    run = build_run(tmp_path)
    build_glance(run)
    (run / "calibration_report.json").unlink()
    code, out = export(tmp_path, run, human=build_human(tmp_path))
    assert code == 0
    names = files_under(out)
    assert "calibration.svg" not in names and "heldout-agreement.svg" in names
    assert "*Not drawn: no `calibration_report.json`" in (out / "00-at-a-glance.md").read_text(encoding="utf-8")
    readme = (out / "README.md").read_text(encoding="utf-8")
    assert "`calibration.svg`" in readme and "not produced" in readme.lower()
    assert "skip  calibration.svg" in capsys.readouterr().out


def test_a_run_with_none_of_the_inputs_gets_no_page_and_says_so(tmp_path: Path):
    run = build_run(tmp_path)
    code, out = export(tmp_path, run, human=build_human(tmp_path))
    assert code == 0
    assert "00-at-a-glance.md" not in files_under(out) and not any(f in files_under(out) for f in FIGURES)
    assert "`00-at-a-glance.md`" in (out / "README.md").read_text(encoding="utf-8")


def test_the_metrics_that_stats_json_carries_are_read_when_the_file_is_absent(tmp_path: Path):
    run = build_run(tmp_path)
    stats = json.loads((run / "stats.json").read_text(encoding="utf-8"))
    _write_json(run / "stats.json", {**stats, "offline": False, "run_metrics": metrics_payload()})
    code, out = export(tmp_path, run, human=build_human(tmp_path))
    assert code == 0 and "model-time.svg" in files_under(out)


def test_an_offline_run_gets_no_model_time_figure_and_no_live_claim_on_the_page(tmp_path: Path):
    code, out, _run = glance_export(tmp_path, offline=True)  # the metrics still say "measured"
    assert code == 0
    names = files_under(out)
    assert "model-time.svg" not in names, "no model was called, so there is no model time to draw"
    page = (out / "00-at-a-glance.md").read_text(encoding="utf-8")
    assert "This is an offline run: no model was called" in page and "Models were called" not in page
    assert "model-seconds" not in page.replace("Model-seconds", "") and "replayed from the cache" not in page
    assert "sided with" not in page and "keyword table" in page
    assert "this is an offline run: no model was called, so there is no model time" in page
    assert "judge siding" not in page, "a stub judge's siding is not a finding"


def test_a_figure_that_shares_a_run_with_a_response_is_withheld_alone(tmp_path: Path):
    leaky = metrics_payload()
    leaky["latency"]["by_role_task_ms"][0]["role"] = PLANTED
    code, out, run = glance_export(tmp_path, metrics=leaky)
    assert code == 0, "the export survives: the one figure is held back, the rest are written"
    names = files_under(out)
    assert "model-time.svg" not in names and "agreement-judge.svg" in names
    page = (out / "00-at-a-glance.md").read_text(encoding="utf-8")
    assert "Not drawn: withheld by the guard" in page
    assert PLANTED.casefold()[:30] not in page.casefold()
    assert "model-time.svg" in (out / "README.md").read_text(encoding="utf-8")
    assert (run / xr.GUARD_LOG_NAME).exists()


def test_the_at_a_glance_files_are_byte_identical_and_free_of_respondent_text(tmp_path: Path):
    code, out_a, run = glance_export(tmp_path)
    assert code == 0
    code_b, out_b = export(tmp_path, run, human=tmp_path / "human", out="second")
    assert code_b == 0
    for name in ("00-at-a-glance.md", *FIGURES):
        body = (out_a / name).read_bytes()
        assert body == (out_b / name).read_bytes(), name
        text = body.decode("utf-8").casefold()
        assert PLANTED.casefold()[:30] not in text and PLANTED_TWO.casefold()[:30] not in text
