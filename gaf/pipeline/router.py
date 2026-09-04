"""The deterministic router — the component that turns check *reports* into *decisions*.

What this module does. Three questions, answered per response, in this order:

1. **Which candidates are accepted?** `accept_candidates` reads M1's Hungarian matching
   and decides what survives: an agreed pair becomes one candidate carrying both
   coders' evidence, a disputed or grey pair becomes two, and a candidate the other
   coder never proposed is accepted and flagged.
2. **What is each accepted candidate's integration action?** `integration_actions`
   reads M2's routing and resolves every decision to MERGE or CREATE — the geometry
   where the geometry is certain, the judge's verdict where it is not, and the
   non-destructive default where no judge was available.
3. **How is that action applied?** `integrate` is the *only* function in the fast loop
   that changes the codebook, and it has exactly two branches.

**Which pairs reach a model is this module's decision, and it is one rule: a score in
the grey band between tau_low and tau_high is the escalation signal.** Agreement — the
common case — costs nothing extra, because two coders landing at or above tau_high need
no third opinion. A *dispute* below tau_low is not escalated either: the coders proposed
genuinely different codes, and resolving that would mean dropping one of them on a
meaning judgment the fast loop is not allowed to make, so both are kept and flagged for
the human. Only the band in between is genuinely ambiguous. Epistemic diversity and cost
control are therefore the same mechanism rather than two competing ones: the reason to
run two coders from different providers is that their divergence is informative, and the
reason the frontier judge is affordable is that genuine ambiguity is rare. `escalates` is
that rule, written once.

**This module emits no findings.** Checks report; the router decides; the audit log
records. Every decision here is returned as a value carrying the inputs that produced
it — the score, the band, the neighbours, the snapshot id, the judge's verdict — and
the fast loop writes those into the audit log. A decision whose provenance is not in
the log did not happen.

**No decision here restructures anything.** MERGE attaches evidence to an existing
code; CREATE admits a new one. There is no split, no re-parent and no rename in this
module, and their absence is structural rather than accidental: those operations exist
only in the human-gated slow loop, because a fast loop that could restructure on a
similarity score is exactly the mechanism that flattened the predecessor's codebook
(ADR-0003, `docs/ARCHITECTURE.md`).

**Offline, the router degrades honestly.** With no judge, a grey-zone dispute keeps
both candidates and a grey-zone route creates rather than merges — the two
non-destructive directions declared in `gaf.llm.base.FAIL_SAFE_DEFAULTS`. Nothing is
dropped on a meaning judgment that could not be made, and M1 and M2 have already
recorded the unresolved ambiguity as a WARN for the human gate. Note ADR-0019 when
reading those counts back: in the offline lexical space M2's grey zone is empty and
M3 escalates almost everything, so offline routing statistics are artefacts of the
fallback embedder and are not findings about the coding.

Validation principles: **transparency** — every decision is a value with its inputs
attached, so a methods reviewer can replay it; **interpretive depth** — keep-and-flag
over auto-resolution, so a disagreement survives to the human gate instead of being
silently settled by a threshold.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from typing import Any

from gaf.checks.semantic import (
    BAND_AGREED,
    BAND_DISPUTED,
    BAND_GREY,
    AgreementResult,
    RoutingResult,
)
from gaf.embed.protocol import Route
from gaf.ids import code_id as mint_code_id
from gaf.models import Candidate, Code, Codebook, Evidence, family_of

__all__ = [
    "ORIGINS",
    "Acceptance",
    "AcceptanceResult",
    "IntegrationDecision",
    "accept_candidates",
    "escalates",
    "integrate",
    "integration_actions",
    "merge_evidence",
]

#: Where an accepted candidate came from. The first is the cheap common case; the rest
#: are the disagreements the two-coder design exists to surface.
ORIGINS: tuple[str, ...] = ("agreed", "grey", "disputed", "unmatched_a", "unmatched_b")

#: The judge's dispute verdict that removes a candidate. Every other verdict, and every
#: unreadable one, keeps both — see `gaf.llm.base.FAIL_SAFE_DEFAULTS`.
_DROP = "DROP"
_MERGE = "MERGE"


def escalates(band: str) -> bool:
    """Whether a model is consulted about a pair in this band. The escalation rule.

    Only the grey zone escalates. Agreement is settled by the geometry and costs
    nothing; a dispute below tau_low is settled too — the coders named different things
    and both readings are kept and flagged, which is a decision a frontier model would
    not improve. What is left is the band where the geometry genuinely cannot tell,
    and that is the only thing worth a frontier call.
    """
    return band == BAND_GREY


# --------------------------------------------------------------------------- #
# Evidence
# --------------------------------------------------------------------------- #


def merge_evidence(*groups: Sequence[Evidence]) -> list[Evidence]:
    """Union several evidence lists, de-duplicated and totally ordered.

    Two coders who agree on a code have usually quoted the same phrase, so the union is
    mostly a de-duplication; where they quoted different phrases, both survive, because
    discarding one coder's evidence would throw away the very independence the two-coder
    design pays for.

    The order is by content — response, span, quote — and never by which coder was
    processed first. Evidence order is part of the codebook's serialisation and
    therefore part of its snapshot id, so an insertion ordering here would make the
    snapshot sequence depend on iteration order (ADR-0017).
    """
    seen: dict[tuple[int, tuple[int, int] | None, str], Evidence] = {}
    for group in groups:
        for evidence in group:
            seen.setdefault((evidence.response_id, evidence.span, evidence.quote), evidence)
    return sorted(
        seen.values(),
        key=lambda e: (
            e.response_id,
            e.span[0] if e.span else -1,
            e.span[1] if e.span else -1,
            e.quote,
        ),
    )


# --------------------------------------------------------------------------- #
# 1. Acceptance
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class Acceptance:
    """One candidate the router accepted (or dropped), with the inputs that decided it."""

    candidate: Candidate
    origin: str
    coders: tuple[str, ...]
    score: float = 0.0
    band: str = BAND_DISPUTED
    counterpart: str = ""
    escalated: bool = False
    verdict: str = ""
    reasoning: str = ""

    @property
    def name(self) -> str:
        return self.candidate.name

    def to_json(self) -> dict[str, Any]:
        return {
            "name": self.candidate.name,
            "origin": self.origin,
            "coders": list(self.coders),
            "score": self.score,
            "band": self.band,
            "counterpart": self.counterpart,
            "escalated": self.escalated,
            "verdict": self.verdict,
            "reasoning": self.reasoning,
            "n_evidence": len(self.candidate.evidence),
        }


@dataclass(frozen=True, slots=True)
class AcceptanceResult:
    """What the router decided about one response's two candidate sets."""

    accepted: list[Acceptance] = field(default_factory=list)
    dropped: list[Acceptance] = field(default_factory=list)
    agreement_rate: float = 0.0
    space_id: str = ""

    def candidates(self) -> list[Candidate]:
        """The accepted candidates, in decision order — M3's and M2's input."""
        return [acceptance.candidate for acceptance in self.accepted]

    def escalated(self) -> list[Acceptance]:
        """The pairs that reached the judge. Empty offline, and empty when coders agree."""
        return [acceptance for acceptance in self.accepted + self.dropped if acceptance.escalated]

    def by_origin(self) -> dict[str, int]:
        counts = dict.fromkeys(ORIGINS, 0)
        for acceptance in self.accepted:
            counts[acceptance.origin] = counts.get(acceptance.origin, 0) + 1
        return counts

    def stats(self) -> dict[str, Any]:
        return {
            "space_id": self.space_id,
            "agreement_rate": self.agreement_rate,
            "n_accepted": len(self.accepted),
            "n_dropped": len(self.dropped),
            "n_escalated": len(self.escalated()),
            "by_origin": self.by_origin(),
        }


def accept_candidates(
    agreement: AgreementResult,
    candidates_a: Sequence[Candidate],
    candidates_b: Sequence[Candidate],
    *,
    judge_available: bool,
) -> AcceptanceResult:
    """Decide which of two coders' candidates survive, from M1's matching alone.

    Four cases, and only one of them costs a model call:

    * **agreed** (score >= tau_high) — one candidate, coder A's name and description,
      carrying both coders' evidence. The common case, and free;
    * **grey** — escalated. ``DROP`` accepts coder A's candidate and drops coder B's
      counterpart; anything else — including an unreadable reply and the offline case
      where there is no judge at all — accepts both;
    * **disputed** (score < tau_low) — both accepted. The coders named two different
      things and the structural layer has no basis for preferring one;
    * **unmatched** — accepted. A code one coder proposed and the other did not is the
      disagreement the report exists to surface, not a defect to be swept.

    Nothing is dropped except on an explicit ``DROP`` from a judge that actually ran.
    The candidates and the agreement result are read only; accepted objects are new.
    """
    accepted: list[Acceptance] = []
    dropped: list[Acceptance] = []

    for match in agreement.matches:
        candidate_a = candidates_a[match.index_a]
        candidate_b = candidates_b[match.index_b]
        coders = (candidate_a.coder, candidate_b.coder)
        escalated = escalates(match.band) and judge_available

        if match.band == BAND_AGREED:
            accepted.append(
                Acceptance(
                    candidate=replace(
                        candidate_a,
                        evidence=merge_evidence(candidate_a.evidence, candidate_b.evidence),
                    ),
                    origin="agreed",
                    coders=coders,
                    score=match.score,
                    band=match.band,
                    counterpart=candidate_b.name,
                )
            )
            continue

        origin = "grey" if match.band == BAND_GREY else "disputed"
        common: dict[str, Any] = {
            "origin": origin,
            "coders": coders,
            "score": match.score,
            "band": match.band,
            "escalated": escalated,
            "verdict": match.verdict,
            "reasoning": match.reasoning,
        }
        accepted.append(
            Acceptance(candidate=candidate_a, counterpart=candidate_b.name, **common)
        )
        side_b = Acceptance(candidate=candidate_b, counterpart=candidate_a.name, **common)
        (dropped if escalated and match.verdict == _DROP else accepted).append(side_b)

    for candidate in agreement.unmatched_a:
        accepted.append(
            Acceptance(candidate=candidate, origin="unmatched_a", coders=(candidate.coder,))
        )
    for candidate in agreement.unmatched_b:
        accepted.append(
            Acceptance(candidate=candidate, origin="unmatched_b", coders=(candidate.coder,))
        )

    return AcceptanceResult(
        accepted=accepted,
        dropped=dropped,
        agreement_rate=agreement.agreement_rate,
        space_id=agreement.space_id,
    )


# --------------------------------------------------------------------------- #
# 2. Integration actions
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class IntegrationDecision:
    """One candidate's integration action, and everything that produced it.

    `route` is what the geometry said, including `Route.JUDGE`; `action` is what the
    router decided to do, and is always MERGE or CREATE. Both are kept, because "the
    geometry was unsure and the judge said merge" and "the geometry was sure" are
    different facts about a codebook and a run report has to be able to tell them apart.
    """

    candidate_name: str
    action: Route
    route: Route
    score: float = 0.0
    target_code_id: str = ""
    target_code_name: str = ""
    neighbours: list[dict[str, Any]] = field(default_factory=list)
    escalated: bool = False
    verdict: str = ""
    reasoning: str = ""
    snapshot_id: str = ""
    space_id: str = ""

    def to_json(self) -> dict[str, Any]:
        return {
            "candidate_name": self.candidate_name,
            "action": self.action.value,
            "route": self.route.value,
            "score": self.score,
            "target_code_id": self.target_code_id,
            "target_code_name": self.target_code_name,
            "neighbours": list(self.neighbours),
            "escalated": self.escalated,
            "verdict": self.verdict,
            "reasoning": self.reasoning,
            "snapshot_id": self.snapshot_id,
            "space_id": self.space_id,
        }


def integration_actions(
    routing: RoutingResult,
    *,
    snapshot_id: str,
    judge_available: bool,
    top_neighbours: int = 3,
) -> list[IntegrationDecision]:
    """Resolve every M2 routing decision to a MERGE or a CREATE.

    MERGE and CREATE pass straight through — the geometry was certain and the router
    has nothing to add. A JUDGE route takes the judge's verdict when one ran, and
    otherwise **creates**: a spurious new code is visible to M4 and recoverable at the
    human gate, while a spurious merge silently destroys a distinction, which is the
    asymmetry `gaf.llm.base.FAIL_SAFE_DEFAULTS` already commits the project to.

    `top_neighbours` bounds how much of the retrieval ranking is carried into the audit
    payload; the full ranking stays in M2's own finding.
    """
    decisions: list[IntegrationDecision] = []
    for decision in routing.decisions:
        escalated = decision.route is Route.JUDGE and judge_available
        if decision.route is Route.JUDGE:
            action = Route.MERGE if (escalated and decision.verdict == _MERGE) else Route.CREATE
        else:
            action = decision.route
        best = decision.best
        decisions.append(
            IntegrationDecision(
                candidate_name=decision.candidate_name,
                action=action,
                route=decision.route,
                score=decision.best_score,
                target_code_id=best.code_id if best and action is Route.MERGE else "",
                target_code_name=best.name if best and action is Route.MERGE else "",
                neighbours=[n.to_json() for n in decision.neighbours[:top_neighbours]],
                escalated=escalated,
                verdict=decision.verdict,
                reasoning=decision.reasoning,
                snapshot_id=snapshot_id,
                space_id=routing.space_id,
            )
        )
    return decisions


# --------------------------------------------------------------------------- #
# 3. Integration — the only place the fast loop changes the codebook
# --------------------------------------------------------------------------- #


def integrate(
    codebook: Codebook,
    decision: IntegrationDecision,
    candidate: Candidate,
    *,
    snapshot_id: str,
) -> tuple[Codebook, Code, Route]:
    """Apply one integration action and return the new codebook, the code, and what happened.

    Exactly two branches, and no third is reachable:

    * **MERGE** — the target code keeps its id, its name, its description and its
      parent, and gains this candidate's evidence. Nothing about the code's *meaning*
      changes, because merging evidence is integration and rewriting a description is
      restructuring;
    * **CREATE** — a new `Code` is admitted, its id derived from its name, its
      ``created_in_snapshot`` the snapshot the batch's coders read (ADR-0007: the code's
      provenance is content-addressed, and the codebook carries no timestamps). Its
      ``parent_id`` points at the family node **only if one already exists**; the fast
      loop does not invent a parent, because creating a level of hierarchy is
      restructuring and belongs to the human gate.

    A CREATE whose name is already in the codebook is integrated as a MERGE and the
    returned `Route` says so. Names identify codes — `Codebook.by_name` assumes it and
    S6 reports a collision as an ERROR — so admitting a second code under one name is
    not an option the router is allowed to take.

    The input codebook is never mutated: a new `Codebook` is returned, which is what
    makes "the fast loop never edits the codebook structurally" checkable rather than
    promised.
    """
    if decision.action is Route.MERGE:
        target = codebook.codes.get(decision.target_code_id) or codebook.by_name(candidate.name)
    else:  # CREATE — unless the name is already taken, in which case merging is forced
        target = codebook.by_name(candidate.name)

    if target is not None:
        merged = replace(
            target, evidence=merge_evidence(target.evidence, candidate.evidence)
        )
        codes = dict(codebook.codes)
        codes[merged.id] = merged
        return Codebook(codes=codes), merged, Route.MERGE

    created = Code(
        id=mint_code_id(candidate.name),
        name=candidate.name,
        description=candidate.description,
        parent_id=_family_parent(codebook, candidate.name),
        created_in_snapshot=snapshot_id,
        evidence=merge_evidence(candidate.evidence),
    )
    codes = dict(codebook.codes)
    codes[created.id] = created
    return Codebook(codes=codes), created, Route.CREATE


def _family_parent(codebook: Codebook, name: str) -> str | None:
    """The id of the code named after this code's family, when the codebook has one.

    Family membership is derived from the name (the S3 grammar is canonical) and
    ``parent_id`` is the explicit link S6 checks against it. A code whose family node
    does not exist gets ``parent_id = None`` rather than a fabricated parent: S6 treats
    a dangling ``parent_id`` as an ERROR and a missing one as nothing at all, which is
    the correct relative severity — the family is still legible in the name.
    """
    family = family_of(name)
    if family == name:
        return None
    parent = codebook.by_name(family)
    return parent.id if parent is not None else None
