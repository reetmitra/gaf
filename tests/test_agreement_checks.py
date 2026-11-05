"""The agreement checks are plain counts over sets; these pin the arithmetic and the figure."""

from __future__ import annotations

import importlib.util
import random
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

_spec = importlib.util.spec_from_file_location("agreement_checks", Path(__file__).parent.parent / "scripts" / "agreement_checks.py")
assert _spec and _spec.loader
ac = importlib.util.module_from_spec(_spec)
sys.modules["agreement_checks"] = ac
_spec.loader.exec_module(ac)


def test_cell_stats_known_table():
    s = ac.cell_stats(tp=5, fp=5, fn=5, n_cells=100)
    assert s["f1"] == 0.5
    assert round(s["kappa"], 4) == 0.4444  # po 0.90, pe 0.82


def test_perfect_agreement_is_f1_one_and_interval_collapses():
    human = {str(i): {"a", "b"} if i % 2 else {"b", "c"} for i in range(6)}
    res = ac.interval_and_chance(human, {r: set(c) for r, c in human.items()}, 3, random.Random(1))
    assert res["point"]["f1"] == 1.0 and res["point"]["kappa"] == 1.0
    assert res["f1_ci95"] == [1.0, 1.0]


def test_machine_that_ignores_the_response_is_not_above_chance():
    human = {str(i): {"abc"[i % 3]} for i in range(9)}
    constant = {r: {"a"} for r in human}
    res = ac.interval_and_chance(human, constant, 3, random.Random(1))
    assert res["kappa_p_at_least"] > 0.05 or res["point"]["kappa"] <= res["kappa_chance_p95"]


def test_figure_is_valid_svg_with_one_row_per_run():
    one = {"point": {"kappa": 0.1}, "kappa_ci95": [0.0, 0.2], "kappa_chance_mean": -0.05, "trivial_top_k": {"kappa": 0.2}}
    svg = ac.figure({"r1": {"agreement.code": one, "agreement.family": one}, "r2": {"agreement.code": one, "agreement.family": one}})
    root = ET.fromstring(svg)
    assert svg.count('class="dot"') == 4 and root.tag.endswith("svg")
