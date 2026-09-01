"""Semantic checks M1-M4: cross-coder agreement, integration routing, code<->evidence
fit and codebook semantic health.

What this module does. Everything here is **embedding-first**: a candidate, a code and
a quote are rendered into one versioned geometry (`gaf.embed.protocol.code_text` and an
`Embedder`), compared by cosine, and routed through the two-threshold band
(tau_high / tau_low / tau_fit). A frontier judge is consulted **only** where the
geometry is genuinely ambiguous, and never before the deterministic pass has run.

* **M1** matches coder A's candidates against coder B's by **Hungarian assignment**
  (optimal, not greedy) and reports agreement, dispute and the grey zone. The
  agreement rate is a first-class run statistic.
* **M2** routes each accepted candidate against the frozen snapshot's codebook —
  MERGE / CREATE / JUDGE. The **dedup gate** lives here: a CREATE is impossible while
  a near neighbour sits at or above tau_high, because the route is a pure function of
  the *best* neighbour score.
* **M3** scores each verified quote against its code and escalates a poor fit to the
  judge, whose four verdicts mirror the PI's negative-example taxonomy
  (`docs/CODING_RULES.md`): APPLIES, IMPRECISE, INCOMPLETE, UNNECESSARY. Only
  UNNECESSARY removes anything, and it removes the *quote*, by returning a new
  `Candidate` — nothing is mutated in place.
* **M4** reports near-duplicate leaves within a family and compares two codebooks
  against each other for model-vs-model and human-vs-machine reporting.

What this module never does. It does not mutate the codebook, does not write to the
store, does not call the router, and never invents a replacement code: an IMPRECISE or
INCOMPLETE verdict yields a WARN and nothing else, because refinement is slow-loop and
human work (`docs/CODING_RULES.md`, "the one category with no check").

Validation principles: **interpretive depth** — keep-and-flag over auto-resolution, and
the unmatched lists rather than the headline percentage are the output that matters;
**epistemic diversity** — meaning is validated by model-vs-model agreement in one
versioned geometry, with a third-provider judge for genuine ambiguity.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any, Protocol, runtime_checkable

import numpy as np
from scipy.optimize import linear_sum_assignment

from gaf.checks.contracts import FIT_VERDICTS, CheckReport, Severity
from gaf.config import CodingRules
from gaf.embed.protocol import Embedder, Route, code_text, route_similarity
from gaf.llm.base import validate_enum
from gaf.models import Candidate, Code, Codebook, Response, family_of, sub_of

__all__ = [
    "BAND_AGREED",
    "BAND_DISPUTED",
    "BAND_GREY",
    "DEFAULT_RULES",
    "DISPUTE_VERDICTS",
    "MARKER_KEY",
    "ROUTE_VERDICTS",
    "UNMATCHED",
    "AgreementResult",
    "CodebookComparison",
    "CodebookMatch",
    "CoderMatch",
    "FitResult",
    "FitRuling",
    "Judge",
    "LeafPair",
    "NearDuplicateResult",
    "Neighbour",
    "RoutingDecision",
    "RoutingResult",
    "assign_optimal",
    "check_code_evidence_fit",
    "check_cross_coder_agreement",
    "check_integration_routing",
    "check_near_duplicate_leaves",
    "compare_codebooks",
    "cosine_matrix",
    "pair_subject",
]

#: Stable key under which every finding records its sub-kind, so the run report, the
#: CLI and the golden-set harness can group findings across suites by one rule. The
#: structural suite defines its own constant with the same value: the two check suites
#: are peers and neither imports the other, so the convention is written down twice on
#: purpose. `tests/fixtures/candidates.py::Case.expect_subcode` reads this key.
MARKER_KEY = "marker"

#: Shared immutable default so every check in this module reads the same thresholds
#: when a caller does not supply a `CodingRules`. Frozen, therefore safe to share.
DEFAULT_RULES = CodingRules()

#: Placeholder for the missing half of a pair subject, so an unmatched candidate still
#: produces a finding whose scope is `"pair"` and whose subject is readable.
UNMATCHED = "(unmatched)"

BAND_AGREED = "agreed"  # score >= tau_high
BAND_GREY = "grey"  # tau_low <= score < tau_high — the only band that costs a call
BAND_DISPUTED = "disputed"  # score < tau_low, or no counterpart at all

#: Whitelists for the two non-`FIT_VERDICTS` judge replies. Fail-safe defaults follow
#: `gaf.llm.base.FAIL_SAFE_DEFAULTS`: keep both candidates; create rather than merge.
DISPUTE_VERDICTS: tuple[str, ...] = ("KEEP", "DROP")
ROUTE_VERDICTS: tuple[str, ...] = ("MERGE", "CREATE")


# --------------------------------------------------------------------------- #
# The judge interface
# --------------------------------------------------------------------------- #


@runtime_checkable
class Judge(Protocol):
    """The narrow slice of the Wave-2 judge agent that the semantic checks need.

    Declared here, injected optionally, and implemented by `gaf/agents/judge.py`. Every
    method returns a plain JSON-shaped dict; the checks whitelist the verdict field with
    `gaf.llm.base.validate_enum` and fail safe rather than trusting it, so a malformed
    reply can never destroy data.

    `judge=None` means **offline**: the check emits a WARN where it would have
    escalated, and never crashes for want of a judge.
    """

    def rule_on_fit(
        self,
        *,
        candidate_name: str,
        candidate_description: str,
        quote: str,
        response_text: str,
    ) -> dict:
        """-> ``{"verdict": one of FIT_VERDICTS, "reasoning": str}`` (M3)."""
        ...

    def rule_on_dispute(
        self,
        *,
        candidate_a: dict,
        candidate_b: dict,
        response_text: str,
    ) -> dict:
        """-> ``{"verdict": "KEEP" | "DROP", "reasoning": str}`` (M1 grey zone)."""
        ...

    def rule_on_route(
        self,
        *,
        candidate_name: str,
        candidate_description: str,
        neighbour_name: str,
        neighbour_description: str,
        score: float,
    ) -> dict:
        """-> ``{"route": "MERGE" | "CREATE", "reasoning": str}`` (M2 grey zone)."""
        ...


def _reply_field(reply: Any, key: str, allowed: Sequence[str], default: str) -> tuple[str, bool]:
    """Whitelist one field of a judge reply. Returns ``(value, fell_back)``.

    Tolerates a reply that is not a dict at all, because "never crash for want of a
    judge" includes a judge that answers with nonsense.
    """
    raw = reply.get(key) if isinstance(reply, Mapping) else None
    value = validate_enum(raw, allowed, default)
    return value, not (isinstance(raw, str) and value.upper() == raw.strip().upper())


def _reasoning(reply: Any) -> str:
    if isinstance(reply, Mapping):
        text = reply.get("reasoning")
        if isinstance(text, str):
            return text
    return ""


# --------------------------------------------------------------------------- #
# Geometry helpers
# --------------------------------------------------------------------------- #


def _embed_texts(embedder: Embedder, texts: Sequence[str]) -> np.ndarray:
    """Batch-embed, tolerating the empty batch (which some backends refuse)."""
    if not texts:
        return np.zeros((0, embedder.dim), dtype=np.float64)
    return np.asarray(embedder.embed(list(texts)), dtype=np.float64)


def _unit_rows(matrix: np.ndarray) -> np.ndarray:
    """Row-wise L2 normalisation with a zero-vector guard.

    The `Embedder` protocol already promises normalised vectors; this makes the cosine
    exact even for an empty string, whose vector is all zeros.
    """
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0.0] = 1.0
    return matrix / norms


def cosine_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Full cosine similarity matrix between two stacks of row vectors."""
    if a.shape[0] == 0 or b.shape[0] == 0:
        return np.zeros((a.shape[0], b.shape[0]), dtype=np.float64)
    return np.asarray(_unit_rows(a) @ _unit_rows(b).T, dtype=np.float64)


def assign_optimal(similarity: np.ndarray) -> list[tuple[int, int]]:
    """Maximum-total-similarity one-to-one assignment, by Hungarian algorithm.

    This is the mechanism ADR-0003 puts in place of the predecessor's greedy lexical
    matching: greedy takes the single best pair first and can then be forced into a
    worse global solution (or, row-wise, assign two codes from one coder to the same
    code from the other). `scipy.optimize.linear_sum_assignment` is optimal.

    Returns ``(index_a, index_b)`` pairs sorted by `index_a`, so the output is
    deterministic for identical input.
    """
    if similarity.shape[0] == 0 or similarity.shape[1] == 0:
        return []
    rows, cols = linear_sum_assignment(similarity, maximize=True)
    return sorted((int(i), int(j)) for i, j in zip(rows, cols, strict=True))


def _band(score: float, rules: CodingRules) -> str:
    if score >= rules.tau_high:
        return BAND_AGREED
    if score < rules.tau_low:
        return BAND_DISPUTED
    return BAND_GREY


def pair_subject(name_a: str, name_b: str) -> str:
    """Canonical `CheckFinding.subject` for a scope-``"pair"`` finding."""
    return f"{name_a or UNMATCHED}<->{name_b or UNMATCHED}"


def _round(value: float) -> float:
    """Scores enter `CheckFinding.data` as plain rounded floats, never numpy scalars."""
    return round(float(value), 6)


# --------------------------------------------------------------------------- #
# M1 — cross-coder agreement
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class CoderMatch:
    """One Hungarian-assigned pair of candidates, with its band and any judge ruling."""

    index_a: int
    index_b: int
    name_a: str
    name_b: str
    score: float
    band: str
    verdict: str = ""  # "KEEP" / "DROP" when the grey zone reached the judge
    reasoning: str = ""

    def to_json(self) -> dict[str, Any]:
        return {
            "index_a": self.index_a,
            "index_b": self.index_b,
            "name_a": self.name_a,
            "name_b": self.name_b,
            "score": self.score,
            "band": self.band,
            "verdict": self.verdict,
            "reasoning": self.reasoning,
        }


@dataclass(frozen=True, slots=True)
class AgreementResult:
    """M1's output: the matches, the unmatched on each side, the rate, the report.

    `agreement_rate` is the primary epistemic-diversity evidence and is defined as
    ``agreed_pairs / max(len(a), len(b))`` — the fraction of the larger coder's set
    that found a counterpart at or above tau_high. It counts only the deterministic
    `agreed` band, never a judge ruling, so the statistic is reproducible offline.
    """

    matches: list[CoderMatch]
    unmatched_a: list[Candidate]
    unmatched_b: list[Candidate]
    agreement_rate: float
    space_id: str
    report: CheckReport
    coder_a: str = ""
    coder_b: str = ""

    def agreed(self) -> list[CoderMatch]:
        return [m for m in self.matches if m.band == BAND_AGREED]

    def grey(self) -> list[CoderMatch]:
        return [m for m in self.matches if m.band == BAND_GREY]

    def disputed(self) -> list[CoderMatch]:
        return [m for m in self.matches if m.band == BAND_DISPUTED]

    def stats(self) -> dict[str, Any]:
        """The run-statistic row. `unmatched_*` names are the interpretive-depth output."""
        return {
            "space_id": self.space_id,
            "coder_a": self.coder_a,
            "coder_b": self.coder_b,
            "n_candidates_a": len(self.matches) + len(self.unmatched_a),
            "n_candidates_b": len(self.matches) + len(self.unmatched_b),
            "n_agreed": len(self.agreed()),
            "n_grey": len(self.grey()),
            "n_disputed": len(self.disputed()),
            "n_unmatched_a": len(self.unmatched_a),
            "n_unmatched_b": len(self.unmatched_b),
            "agreement_rate": self.agreement_rate,
            "unmatched_a": [c.name for c in self.unmatched_a],
            "unmatched_b": [c.name for c in self.unmatched_b],
        }


def check_cross_coder_agreement(
    candidates_a: Sequence[Candidate],
    candidates_b: Sequence[Candidate],
    embedder: Embedder,
    rules: CodingRules = DEFAULT_RULES,
    *,
    judge: Judge | None = None,
    response_text: str = "",
) -> AgreementResult:
    """M1 — match two coders' candidate sets optimally and report where they diverge.

    Both sets are rendered with `code_text` into one space, the full cosine matrix is
    built, and `assign_optimal` picks the assignment maximising total similarity. Each
    assigned pair lands in one of three bands: agreed (INFO), grey (the judge, or a
    WARN offline) or disputed (WARN). Candidates left over on either side are reported
    as disputed pairs against `UNMATCHED`, because a code one coder proposed and the
    other did not is exactly the disagreement the report exists to surface.
    """
    report = CheckReport()
    texts_a = [code_text(c.name, c.description) for c in candidates_a]
    texts_b = [code_text(c.name, c.description) for c in candidates_b]
    similarity = cosine_matrix(_embed_texts(embedder, texts_a), _embed_texts(embedder, texts_b))
    pairs = assign_optimal(similarity)

    matches: list[CoderMatch] = []
    for index_a, index_b in pairs:
        score = _round(similarity[index_a, index_b])
        band = _band(score, rules)
        cand_a, cand_b = candidates_a[index_a], candidates_b[index_b]
        verdict, reasoning, fail_safe = "", "", False
        if band == BAND_GREY and judge is not None:
            reply = judge.rule_on_dispute(
                candidate_a=cand_a.to_json(),
                candidate_b=cand_b.to_json(),
                response_text=response_text,
            )
            verdict, fail_safe = _reply_field(reply, "verdict", DISPUTE_VERDICTS, "KEEP")
            reasoning = _reasoning(reply)
        matches.append(
            CoderMatch(
                index_a=index_a,
                index_b=index_b,
                name_a=cand_a.name,
                name_b=cand_b.name,
                score=score,
                band=band,
                verdict=verdict,
                reasoning=reasoning,
            )
        )
        _report_match(report, matches[-1], rules, embedder, judge, fail_safe)

    assigned_a = {i for i, _ in pairs}
    assigned_b = {j for _, j in pairs}
    unmatched_a = [c for i, c in enumerate(candidates_a) if i not in assigned_a]
    unmatched_b = [c for j, c in enumerate(candidates_b) if j not in assigned_b]
    for candidate in unmatched_a:
        _report_unmatched(report, candidate, embedder, side="a")
    for candidate in unmatched_b:
        _report_unmatched(report, candidate, embedder, side="b")

    denominator = max(len(candidates_a), len(candidates_b))
    agreed = sum(1 for m in matches if m.band == BAND_AGREED)
    rate = _round(agreed / denominator) if denominator else 0.0
    return AgreementResult(
        matches=matches,
        unmatched_a=unmatched_a,
        unmatched_b=unmatched_b,
        agreement_rate=rate,
        space_id=embedder.space_id,
        report=report,
        coder_a=candidates_a[0].coder if candidates_a else "",
        coder_b=candidates_b[0].coder if candidates_b else "",
    )


def _report_match(
    report: CheckReport,
    match: CoderMatch,
    rules: CodingRules,
    embedder: Embedder,
    judge: Judge | None,
    fail_safe: bool,
) -> None:
    subject = pair_subject(match.name_a, match.name_b)
    shared = {
        "score": match.score,
        "band": match.band,
        "space_id": embedder.space_id,
        "name_a": match.name_a,
        "name_b": match.name_b,
        "tau_high": rules.tau_high,
        "tau_low": rules.tau_low,
    }
    if match.band == BAND_AGREED:
        report.add(
            "M1",
            Severity.INFO,
            "pair",
            subject,
            f"Coders agree: '{match.name_a}' and '{match.name_b}' match at cosine "
            f"{match.score:.3f} (>= tau_high {rules.tau_high:.2f}).",
            **{MARKER_KEY: "coders_agree"},
            **shared,
        )
        return
    if match.band == BAND_DISPUTED:
        report.add(
            "M1",
            Severity.WARN,
            "pair",
            subject,
            f"Coders dispute: '{match.name_a}' and '{match.name_b}' match at only cosine "
            f"{match.score:.3f} (< tau_low {rules.tau_low:.2f}).",
            **{MARKER_KEY: "coders_dispute"},
            **shared,
        )
        return
    if judge is None:
        report.add(
            "M1",
            Severity.WARN,
            "pair",
            subject,
            f"Grey zone unresolved offline: '{match.name_a}' and '{match.name_b}' match at "
            f"cosine {match.score:.3f}, between tau_low {rules.tau_low:.2f} and tau_high "
            f"{rules.tau_high:.2f}, and no judge was available.",
            **{MARKER_KEY: "grey_zone_unresolved_offline"},
            **shared,
        )
        return
    report.add(
        "M1",
        Severity.WARN,
        "pair",
        subject,
        f"Grey zone ruled {match.verdict}: '{match.name_a}' and '{match.name_b}' match at "
        f"cosine {match.score:.3f}, between tau_low {rules.tau_low:.2f} and tau_high "
        f"{rules.tau_high:.2f}.",
        **{MARKER_KEY: "grey_zone_judged"},
        verdict=match.verdict,
        reasoning=match.reasoning,
        fail_safe=fail_safe,
        **shared,
    )


def _report_unmatched(
    report: CheckReport, candidate: Candidate, embedder: Embedder, *, side: str
) -> None:
    subject = (
        pair_subject(candidate.name, "") if side == "a" else pair_subject("", candidate.name)
    )
    report.add(
        "M1",
        Severity.WARN,
        "pair",
        subject,
        f"Coder {side.upper()} proposed '{candidate.name}' and the other coder proposed "
        "nothing that could be assigned to it.",
        **{MARKER_KEY: "coder_unmatched"},
        side=side,
        name=candidate.name,
        coder=candidate.coder,
        band=BAND_DISPUTED,
        space_id=embedder.space_id,
    )


# --------------------------------------------------------------------------- #
# M2 — integration routing
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class Neighbour:
    """One retrieved codebook code and its cosine to the candidate."""

    code_id: str
    name: str
    score: float

    def to_json(self) -> dict[str, Any]:
        return {"code_id": self.code_id, "name": self.name, "score": self.score}


@dataclass(frozen=True, slots=True)
class RoutingDecision:
    """What M2 *reports* about one candidate. The router acts; this only describes.

    `route` is always the geometric route from `route_similarity`. When it is JUDGE and
    a judge was supplied, `verdict` carries the ruling — the route itself is not
    rewritten, so the record shows both what the geometry said and what the judge said.
    """

    candidate_name: str
    route: Route
    best: Neighbour | None
    neighbours: list[Neighbour]
    verdict: str = ""
    reasoning: str = ""

    @property
    def best_score(self) -> float:
        return self.best.score if self.best else 0.0

    def to_json(self) -> dict[str, Any]:
        return {
            "candidate_name": self.candidate_name,
            "route": self.route.value,
            "best": self.best.to_json() if self.best else None,
            "best_score": self.best_score,
            "neighbours": [n.to_json() for n in self.neighbours],
            "verdict": self.verdict,
            "reasoning": self.reasoning,
        }


@dataclass(frozen=True, slots=True)
class RoutingResult:
    """M2's output: one decision per candidate, in input order, plus the report."""

    decisions: list[RoutingDecision]
    space_id: str
    report: CheckReport

    def by_route(self) -> dict[str, list[str]]:
        grouped: dict[str, list[str]] = {r.value: [] for r in Route}
        for decision in self.decisions:
            grouped[decision.route.value].append(decision.candidate_name)
        return grouped

    def stats(self) -> dict[str, Any]:
        grouped = self.by_route()
        return {
            "space_id": self.space_id,
            "n_candidates": len(self.decisions),
            "counts": {route: len(names) for route, names in grouped.items()},
            "by_route": grouped,
        }


def check_integration_routing(
    candidates: Sequence[Candidate],
    codebook: Codebook,
    embedder: Embedder,
    rules: CodingRules = DEFAULT_RULES,
    *,
    judge: Judge | None = None,
    top_k: int = 8,
) -> RoutingResult:
    """M2 — route each accepted candidate against the frozen snapshot's codebook.

    The candidate is embedded once and compared with every code in the snapshot; the
    top-k neighbours are recorded for the audit trail and the *best* of them decides
    the route through `route_similarity`. Routing on the best neighbour rather than on
    a truncated list is what makes the **dedup gate** structural: `Route.CREATE`
    requires ``best_score < tau_low``, so no new code can be reported as creatable
    while a near neighbour sits at or above tau_high.
    """
    report = CheckReport()
    codes = codebook.sorted_codes()
    code_matrix = _embed_texts(embedder, [code_text(c.name, c.description) for c in codes])
    candidate_matrix = _embed_texts(
        embedder, [code_text(c.name, c.description) for c in candidates]
    )
    similarity = cosine_matrix(candidate_matrix, code_matrix)

    decisions: list[RoutingDecision] = []
    for index, candidate in enumerate(candidates):
        neighbours = _top_neighbours(similarity[index] if codes else None, codes, top_k)
        best = neighbours[0] if neighbours else None
        best_score = best.score if best else 0.0
        route = route_similarity(best_score, rules.tau_high, rules.tau_low)
        verdict, reasoning, fail_safe = "", "", False
        if route is Route.JUDGE and judge is not None and best is not None:
            neighbour_code = next(c for c in codes if c.id == best.code_id)
            reply = judge.rule_on_route(
                candidate_name=candidate.name,
                candidate_description=candidate.description,
                neighbour_name=neighbour_code.name,
                neighbour_description=neighbour_code.description,
                score=best_score,
            )
            verdict, fail_safe = _reply_field(reply, "route", ROUTE_VERDICTS, "CREATE")
            reasoning = _reasoning(reply)
        decision = RoutingDecision(
            candidate_name=candidate.name,
            route=route,
            best=best,
            neighbours=neighbours,
            verdict=verdict,
            reasoning=reasoning,
        )
        decisions.append(decision)
        _report_route(report, decision, rules, embedder, judge, fail_safe)

    return RoutingResult(decisions=decisions, space_id=embedder.space_id, report=report)


def _top_neighbours(row: np.ndarray | None, codes: Sequence[Code], top_k: int) -> list[Neighbour]:
    """The `top_k` nearest codes, ties broken by code name so the order is stable."""
    if row is None or not len(codes) or top_k <= 0:
        return []
    ranked = sorted(
        ((_round(row[i]), codes[i].name, codes[i].id) for i in range(len(codes))),
        key=lambda item: (-item[0], item[1], item[2]),
    )
    return [Neighbour(code_id=cid, name=name, score=score) for score, name, cid in ranked[:top_k]]


def _report_route(
    report: CheckReport,
    decision: RoutingDecision,
    rules: CodingRules,
    embedder: Embedder,
    judge: Judge | None,
    fail_safe: bool,
) -> None:
    best_name = decision.best.name if decision.best else ""
    shared: dict[str, Any] = {
        "route": decision.route.value,
        "best_score": decision.best_score,
        "best_name": best_name,
        "best_code_id": decision.best.code_id if decision.best else "",
        "neighbours": [n.to_json() for n in decision.neighbours],
        "space_id": embedder.space_id,
        "tau_high": rules.tau_high,
        "tau_low": rules.tau_low,
    }
    if decision.route is Route.MERGE:
        report.add(
            "M2",
            Severity.INFO,
            "candidate",
            decision.candidate_name,
            f"Routes MERGE into '{best_name}' at cosine {decision.best_score:.3f} "
            f"(>= tau_high {rules.tau_high:.2f}); the dedup gate blocks a new code here.",
            **{MARKER_KEY: "route_merge"},
            **shared,
        )
        return
    if decision.route is Route.CREATE:
        nearest = f"nearest '{best_name}' at {decision.best_score:.3f}" if best_name else "empty codebook"
        report.add(
            "M2",
            Severity.INFO,
            "candidate",
            decision.candidate_name,
            f"Routes CREATE: {nearest}, below tau_low {rules.tau_low:.2f}.",
            **{MARKER_KEY: "route_create"},
            **shared,
        )
        return
    if judge is None:
        report.add(
            "M2",
            Severity.WARN,
            "candidate",
            decision.candidate_name,
            f"Routes JUDGE against '{best_name}' at cosine {decision.best_score:.3f}, in the "
            f"grey zone [{rules.tau_low:.2f}, {rules.tau_high:.2f}), and no judge was available.",
            **{MARKER_KEY: "route_judge_unresolved_offline"},
            **shared,
        )
        return
    report.add(
        "M2",
        Severity.WARN,
        "candidate",
        decision.candidate_name,
        f"Routes JUDGE against '{best_name}' at cosine {decision.best_score:.3f}, in the grey "
        f"zone [{rules.tau_low:.2f}, {rules.tau_high:.2f}); the judge ruled {decision.verdict}.",
        **{MARKER_KEY: "route_judge"},
        verdict=decision.verdict,
        reasoning=decision.reasoning,
        fail_safe=fail_safe,
        **shared,
    )


# --------------------------------------------------------------------------- #
# M3 — code <-> evidence fit
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class FitRuling:
    """One (candidate, verified quote) pair and what happened to it."""

    candidate_name: str
    response_id: int
    quote: str
    fit: float
    verdict: str
    kept: bool
    escalated: bool
    fail_safe: bool = False
    reasoning: str = ""

    def to_json(self) -> dict[str, Any]:
        return {
            "candidate_name": self.candidate_name,
            "response_id": self.response_id,
            "quote": self.quote,
            "fit": self.fit,
            "verdict": self.verdict,
            "kept": self.kept,
            "escalated": self.escalated,
            "fail_safe": self.fail_safe,
            "reasoning": self.reasoning,
        }


@dataclass(frozen=True, slots=True)
class FitResult:
    """M3's output. `candidates` is the **revised** set — new objects, never mutated ones."""

    candidates: list[Candidate]
    rulings: list[FitRuling]
    dropped: list[str]
    removed_quotes: list[FitRuling]
    space_id: str
    report: CheckReport

    def stats(self) -> dict[str, Any]:
        counts: dict[str, int] = dict.fromkeys(FIT_VERDICTS, 0)
        for ruling in self.rulings:
            if ruling.verdict in counts:
                counts[ruling.verdict] += 1
        return {
            "space_id": self.space_id,
            "n_rulings": len(self.rulings),
            "n_escalated": sum(1 for r in self.rulings if r.escalated),
            "verdicts": counts,
            "n_quotes_removed": len(self.removed_quotes),
            "dropped": list(self.dropped),
        }


def check_code_evidence_fit(
    candidates: Sequence[Candidate],
    responses: Mapping[int, Response] | Sequence[Response] | None,
    embedder: Embedder,
    rules: CodingRules = DEFAULT_RULES,
    *,
    judge: Judge | None = None,
) -> FitResult:
    """M3 — score every verified quote against its code, and escalate a poor fit.

    ``fit = cosine(embed(code_text(name, description)), embed(quote))``. At or above
    `tau_fit` the pairing is accepted (INFO). Below it the judge rules, returning one of
    the four `FIT_VERDICTS` that mirror the PI's negative-example taxonomy:

    * ``APPLIES``     — keep, INFO;
    * ``IMPRECISE``   — keep, WARN. **No replacement code is invented**: refinement is
      slow-loop and human work, and the WARN is the deliverable;
    * ``INCOMPLETE``  — keep, WARN, same rule;
    * ``UNNECESSARY`` — the quote is removed. If the candidate then has no verified
      evidence left it is dropped, with an ERROR that the audit log records.

    Removal builds a **new** `Candidate` with `dataclasses.replace`; the inputs are
    never mutated. Unverified evidence is carried through untouched — provenance is
    S2's ruling, not M3's — and a candidate that arrives with no verified evidence at
    all is passed through in silence, because S1/S2 have already spoken about it.

    Offline (`judge=None`) a below-threshold fit produces a WARN instead of an
    escalation. A malformed judge reply fails safe to ``APPLIES``, so the quote
    survives: `gaf.llm.base` fixes that direction of failure and this check honours it.
    """
    report = CheckReport()
    index = _response_index(responses)
    revised: list[Candidate] = []
    rulings: list[FitRuling] = []
    removed: list[FitRuling] = []
    dropped: list[str] = []

    for candidate in candidates:
        code_vector = embedder.embed_one(code_text(candidate.name, candidate.description))
        had_verified = any(e.verified for e in candidate.evidence)
        kept_evidence = []
        for evidence in candidate.evidence:
            if not evidence.verified:
                kept_evidence.append(evidence)
                continue
            ruling, fail_safe = _rule_on_evidence(
                candidate=candidate,
                quote=evidence.quote,
                response_id=evidence.response_id,
                code_vector=code_vector,
                embedder=embedder,
                rules=rules,
                judge=judge,
                response_text=index.get(evidence.response_id, ""),
            )
            rulings.append(ruling)
            _report_fit(report, ruling, rules, embedder, judge, fail_safe)
            if ruling.kept:
                kept_evidence.append(evidence)
            else:
                removed.append(ruling)

        if had_verified and not any(e.verified for e in kept_evidence):
            dropped.append(candidate.name)
            report.add(
                "M3",
                Severity.ERROR,
                "candidate",
                candidate.name,
                f"Candidate '{candidate.name}' is dropped: every verified quote was ruled "
                "UNNECESSARY, so nothing in the corpus supports it any longer.",
                **{MARKER_KEY: "candidate_dropped_no_evidence"},
                space_id=embedder.space_id,
                removed_quotes=[r.quote for r in removed if r.candidate_name == candidate.name],
            )
            continue
        revised.append(
            candidate
            if len(kept_evidence) == len(candidate.evidence)
            else replace(candidate, evidence=kept_evidence)
        )

    return FitResult(
        candidates=revised,
        rulings=rulings,
        dropped=dropped,
        removed_quotes=removed,
        space_id=embedder.space_id,
        report=report,
    )


def _response_index(
    responses: Mapping[int, Response] | Sequence[Response] | None,
) -> dict[int, str]:
    """Response id -> content, accepting either shape and tolerating `None`."""
    if responses is None:
        return {}
    if isinstance(responses, Mapping):
        return {int(rid): r.content for rid, r in responses.items()}
    return {r.id: r.content for r in responses}


def _rule_on_evidence(
    *,
    candidate: Candidate,
    quote: str,
    response_id: int,
    code_vector: np.ndarray,
    embedder: Embedder,
    rules: CodingRules,
    judge: Judge | None,
    response_text: str,
) -> tuple[FitRuling, bool]:
    quote_vector = embedder.embed_one(quote)
    fit = _round(
        cosine_matrix(code_vector.reshape(1, -1), quote_vector.reshape(1, -1))[0, 0]
    )
    if fit >= rules.tau_fit:
        return (
            FitRuling(
                candidate_name=candidate.name,
                response_id=response_id,
                quote=quote,
                fit=fit,
                verdict="APPLIES",
                kept=True,
                escalated=False,
            ),
            False,
        )
    if judge is None:
        return (
            FitRuling(
                candidate_name=candidate.name,
                response_id=response_id,
                quote=quote,
                fit=fit,
                verdict="",
                kept=True,
                escalated=False,
            ),
            False,
        )
    reply = judge.rule_on_fit(
        candidate_name=candidate.name,
        candidate_description=candidate.description,
        quote=quote,
        response_text=response_text,
    )
    verdict, fail_safe = _reply_field(reply, "verdict", FIT_VERDICTS, "APPLIES")
    return (
        FitRuling(
            candidate_name=candidate.name,
            response_id=response_id,
            quote=quote,
            fit=fit,
            verdict=verdict,
            kept=verdict != "UNNECESSARY",
            escalated=True,
            fail_safe=fail_safe,
            reasoning=_reasoning(reply),
        ),
        fail_safe,
    )


_FIT_MARKERS: dict[str, str] = {
    "APPLIES": "fit_ok",
    "IMPRECISE": "fit_imprecise",
    "INCOMPLETE": "fit_incomplete",
    "UNNECESSARY": "quote_removed_unnecessary",
}

_FIT_SENTENCES: dict[str, str] = {
    "IMPRECISE": "the code was not precise enough for this quote; kept and flagged for the "
    "slow loop, with no replacement code invented",
    "INCOMPLETE": "the code did not describe this response segment completely; kept and "
    "flagged for the slow loop, with no replacement code invented",
    "UNNECESSARY": "the code did not have to be applied here, so the quote is removed from "
    "this candidate's evidence",
}


def _report_fit(
    report: CheckReport,
    ruling: FitRuling,
    rules: CodingRules,
    embedder: Embedder,
    judge: Judge | None,
    fail_safe: bool,
) -> None:
    shared: dict[str, Any] = {
        "fit": ruling.fit,
        "tau_fit": rules.tau_fit,
        "response_id": ruling.response_id,
        "quote": ruling.quote,
        "escalated": ruling.escalated,
        "space_id": embedder.space_id,
    }
    if judge is None and not ruling.escalated and ruling.verdict == "":
        report.add(
            "M3",
            Severity.WARN,
            "candidate",
            ruling.candidate_name,
            f"Fit of '{ruling.candidate_name}' to its quote in response {ruling.response_id} is "
            f"{ruling.fit:.3f}, below tau_fit {rules.tau_fit:.2f}, and no judge was available to "
            "rule on it.",
            **{MARKER_KEY: "fit_unresolved_offline"},
            verdict="",
            **shared,
        )
        return
    marker = _FIT_MARKERS[ruling.verdict]
    if ruling.verdict == "APPLIES":
        report.add(
            "M3",
            Severity.INFO,
            "candidate",
            ruling.candidate_name,
            f"Fit of '{ruling.candidate_name}' to its quote in response {ruling.response_id} is "
            f"{ruling.fit:.3f}"
            + (
                f" (below tau_fit {rules.tau_fit:.2f}, but the judge ruled APPLIES)."
                if ruling.escalated
                else f" (>= tau_fit {rules.tau_fit:.2f})."
            ),
            **{MARKER_KEY: marker},
            verdict="APPLIES",
            fail_safe=fail_safe,
            reasoning=ruling.reasoning,
            **shared,
        )
        return
    report.add(
        "M3",
        Severity.WARN,
        "candidate",
        ruling.candidate_name,
        f"Judge ruled {ruling.verdict} on '{ruling.candidate_name}' in response "
        f"{ruling.response_id} (fit {ruling.fit:.3f} < tau_fit {rules.tau_fit:.2f}): "
        f"{_FIT_SENTENCES[ruling.verdict]}.",
        **{MARKER_KEY: marker},
        verdict=ruling.verdict,
        fail_safe=fail_safe,
        reasoning=ruling.reasoning,
        **shared,
    )


# --------------------------------------------------------------------------- #
# M4 — codebook semantic health
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class LeafPair:
    """Two leaf codes and their cosine. Reported, never merged."""

    a_id: str
    a_name: str
    b_id: str
    b_name: str
    score: float
    family: str

    def to_json(self) -> dict[str, Any]:
        return {
            "a_id": self.a_id,
            "a_name": self.a_name,
            "b_id": self.b_id,
            "b_name": self.b_name,
            "score": self.score,
            "family": self.family,
        }


@dataclass(frozen=True, slots=True)
class NearDuplicateResult:
    """M4's near-duplicate output: the offending pairs, how many were compared, the report."""

    pairs: list[LeafPair]
    compared: int
    space_id: str
    report: CheckReport

    def stats(self) -> dict[str, Any]:
        return {
            "space_id": self.space_id,
            "n_leaf_pairs_compared": self.compared,
            "n_near_duplicate_pairs": len(self.pairs),
            "pairs": [p.to_json() for p in self.pairs],
        }


def check_near_duplicate_leaves(
    codebook: Codebook,
    embedder: Embedder,
    rules: CodingRules = DEFAULT_RULES,
) -> NearDuplicateResult:
    """M4 — pairwise cosine over leaf codes, within a family, WARNing on near duplicates.

    Leaves are compared with the other leaves of their own top-level family; a leaf
    whose family is unknown — a bare name with no sub-code, so the first-hyphen split
    yields nothing — falls back to being compared against every leaf. Any pair at or
    above tau_high produces a WARN carrying the `near_duplicate_leaves` marker.

    **Nothing is merged.** The pairs feed the slow-loop refactor proposal, where a
    human decides; auto-merging on lexical or geometric proximity is precisely the
    predecessor failure that flattened the codebook (ADR-0003, `docs/ARCHITECTURE.md`).
    """
    report = CheckReport()
    leaves = codebook.leaves()
    vectors = _embed_texts(embedder, [code_text(c.name, c.description) for c in leaves])
    similarity = cosine_matrix(vectors, vectors)

    pairs: list[LeafPair] = []
    compared = 0
    for i in range(len(leaves)):
        for j in range(i + 1, len(leaves)):
            left, right = leaves[i], leaves[j]
            if not _comparable(left, right):
                continue
            compared += 1
            score = _round(similarity[i, j])
            if score < rules.tau_high:
                continue
            family = family_of(left.name) if family_of(left.name) == family_of(right.name) else ""
            pair = LeafPair(
                a_id=left.id,
                a_name=left.name,
                b_id=right.id,
                b_name=right.name,
                score=score,
                family=family,
            )
            pairs.append(pair)
            report.add(
                "M4",
                Severity.WARN,
                "pair",
                pair_subject(left.name, right.name),
                f"Near-duplicate leaves: '{left.name}' and '{right.name}' sit at cosine "
                f"{score:.3f} (>= tau_high {rules.tau_high:.2f}). Reported for the slow-loop "
                "refactor proposal; nothing is merged here.",
                **{MARKER_KEY: "near_duplicate_leaves"},
                score=score,
                family=family,
                a_id=left.id,
                b_id=right.id,
                a_name=left.name,
                b_name=right.name,
                tau_high=rules.tau_high,
                space_id=embedder.space_id,
            )
    return NearDuplicateResult(
        pairs=pairs, compared=compared, space_id=embedder.space_id, report=report
    )


def _comparable(left: Code, right: Code) -> bool:
    """Same family, or either family unknown (a bare top-level name), in which case
    the comparison falls back to all-pairs."""
    if not sub_of(left.name) or not sub_of(right.name):
        return True
    return family_of(left.name) == family_of(right.name)


@dataclass(frozen=True, slots=True)
class CodebookMatch:
    """One Hungarian-assigned pair of codes across two codebooks."""

    name_a: str
    name_b: str
    score: float
    band: str

    def to_json(self) -> dict[str, Any]:
        return {
            "name_a": self.name_a,
            "name_b": self.name_b,
            "score": self.score,
            "band": self.band,
        }


@dataclass(frozen=True, slots=True)
class CodebookComparison:
    """M4's cross-codebook output — model-vs-model and human-vs-machine reporting."""

    matches: list[CodebookMatch]
    only_in_a: list[str]
    only_in_b: list[str]
    agreement_rate: float
    space_id: str
    report: CheckReport
    label_a: str = "A"
    label_b: str = "B"

    def stats(self) -> dict[str, Any]:
        return {
            "space_id": self.space_id,
            "label_a": self.label_a,
            "label_b": self.label_b,
            "n_codes_a": len(self.matches) + len(self.only_in_a),
            "n_codes_b": len(self.matches) + len(self.only_in_b),
            "n_agreed": sum(1 for m in self.matches if m.band == BAND_AGREED),
            "n_grey": sum(1 for m in self.matches if m.band == BAND_GREY),
            "n_disputed": sum(1 for m in self.matches if m.band == BAND_DISPUTED),
            "agreement_rate": self.agreement_rate,
            "only_in_a": list(self.only_in_a),
            "only_in_b": list(self.only_in_b),
            "matches": [m.to_json() for m in self.matches],
        }


def compare_codebooks(
    codebook_a: Codebook,
    codebook_b: Codebook,
    embedder: Embedder,
    rules: CodingRules = DEFAULT_RULES,
    *,
    label_a: str = "A",
    label_b: str = "B",
) -> CodebookComparison:
    """M4 — Hungarian comparison of two whole codebooks.

    The same geometry and the same bands as M1, applied to codebooks rather than to one
    response's candidates: this is what makes "GPT's codebook versus Gemini's" and
    "the human's codebook versus the machine's" one comparable measurement. The
    `only_in_*` lists are the interpretive-depth output — a concept one codebook holds
    and the other does not is the finding, not the headline rate.
    """
    report = CheckReport()
    codes_a, codes_b = codebook_a.sorted_codes(), codebook_b.sorted_codes()
    similarity = cosine_matrix(
        _embed_texts(embedder, [code_text(c.name, c.description) for c in codes_a]),
        _embed_texts(embedder, [code_text(c.name, c.description) for c in codes_b]),
    )
    pairs = assign_optimal(similarity)

    matches: list[CodebookMatch] = []
    for index_a, index_b in pairs:
        score = _round(similarity[index_a, index_b])
        band = _band(score, rules)
        match = CodebookMatch(
            name_a=codes_a[index_a].name, name_b=codes_b[index_b].name, score=score, band=band
        )
        matches.append(match)
        report.add(
            "M4",
            Severity.INFO if band == BAND_AGREED else Severity.WARN,
            "pair",
            pair_subject(match.name_a, match.name_b),
            f"Codebook comparison {label_a} vs {label_b}: '{match.name_a}' and "
            f"'{match.name_b}' match at cosine {score:.3f} ({band}).",
            **{MARKER_KEY: f"codebook_match_{band}"},
            score=score,
            band=band,
            label_a=label_a,
            label_b=label_b,
            name_a=match.name_a,
            name_b=match.name_b,
            space_id=embedder.space_id,
        )

    assigned_a = {i for i, _ in pairs}
    assigned_b = {j for _, j in pairs}
    only_in_a = [c.name for i, c in enumerate(codes_a) if i not in assigned_a]
    only_in_b = [c.name for j, c in enumerate(codes_b) if j not in assigned_b]
    for name, label, other in ((only_in_a, label_a, label_b), (only_in_b, label_b, label_a)):
        for code_name in name:
            report.add(
                "M4",
                Severity.WARN,
                "pair",
                pair_subject(code_name, "") if label == label_a else pair_subject("", code_name),
                f"Codebook comparison {label_a} vs {label_b}: '{code_name}' appears in "
                f"{label} and has no counterpart in {other}.",
                **{MARKER_KEY: "codebook_only_in_one"},
                name=code_name,
                label=label,
                space_id=embedder.space_id,
            )

    denominator = max(len(codes_a), len(codes_b))
    agreed = sum(1 for m in matches if m.band == BAND_AGREED)
    return CodebookComparison(
        matches=matches,
        only_in_a=only_in_a,
        only_in_b=only_in_b,
        agreement_rate=_round(agreed / denominator) if denominator else 0.0,
        space_id=embedder.space_id,
        report=report,
        label_a=label_a,
        label_b=label_b,
    )
