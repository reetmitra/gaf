"""Row-oriented assignment fixtures: a stand-in "human" coding and a "machine" coding.

Used by the agreement module (A5) and the standalone check CLI (C2). The two sets
differ on purpose, and the differences are the interesting cases for concurrent
validation:

* an exact agreement (same code, same segment);
* a **right code, wrong place** — same code, a different span of the same response,
  which code-level agreement scores as a hit and segment-level agreement must not;
* a **machine-only** code (over-coding);
* a **human-only** code (a blind spot).

Those last two lists are the most valuable output of validation for the write-up, so
the fixture makes both non-empty by construction.

Validation principle: **interpretive depth** — the point of the comparison is what the
machine missed, not the headline percentage.
"""

from __future__ import annotations

from gaf.models import Assignment

__all__ = ["HUMAN_ONLY", "MACHINE_ONLY", "human_assignments", "machine_assignments"]

#: Codes the machine applies that the human never does (over-coding).
MACHINE_ONLY = ("future-inevitability",)
#: Codes the human applies that the machine never does (blind spots).
HUMAN_ONLY = ("negative_impacts-lack_of_inclusion",)


def human_assignments() -> list[Assignment]:
    return [
        Assignment(203, "Rural clinics get diagnostic support", "positive_impacts-healthcare"),
        Assignment(203, "Clerical posts in the district office vanish quietly", "negative_impacts-job_destruction"),
        Assignment(207, "Firms will hand ticket triage and first-draft paperwork to software", "negative_impacts-job_destruction"),
        Assignment(207, "it demands qualifications most school leavers in my district never had", "negative_impacts-lack_of_inclusion"),
        Assignment(239, "Those households had one wage between four people", "negative_impacts-lack_of_inclusion"),
        Assignment(244, "these tools will help us with problems too large to hold in one head", "positive_impacts-problem-solving"),
        Assignment(245, "you discover how narrow the door has become", "negative_impacts-misuse"),
        Assignment(226, "A tutor that never tires, adjusting to one child's pace", "positive_impacts-healthcare"),
    ]


def machine_assignments() -> list[Assignment]:
    return [
        # exact agreements
        Assignment(203, "Rural clinics get diagnostic support", "positive_impacts-healthcare"),
        Assignment(207, "Firms will hand ticket triage and first-draft paperwork to software", "negative_impacts-job_destruction"),
        Assignment(244, "these tools will help us with problems too large to hold in one head", "positive_impacts-problem-solving"),
        Assignment(245, "you discover how narrow the door has become", "negative_impacts-misuse"),
        Assignment(226, "A tutor that never tires, adjusting to one child's pace", "positive_impacts-healthcare"),
        # right code, wrong place: same code and response as a human row above,
        # but a different segment
        Assignment(203, "no retraining scheme arrives", "negative_impacts-job_destruction"),
        # over-coding: a code no human row uses
        Assignment(258, "Quality of life improves on average", "future-inevitability"),
        Assignment(212, "By 2050 that reach will be wider still", "future-inevitability"),
    ]
