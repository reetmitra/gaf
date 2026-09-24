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
