"""Ward's hierarchical cluster analysis over the occurrence matrix, exactly as Chan (2025).

The unit of clustering is the **response**, not the code: rows of the binary occurrence
matrix are grouped by Ward's linkage, and each cluster is then characterised by the
mean occurrence of every code within it. That is the Chan method reproduced without
change; what changes here is only the *interpretation* (ADR-0005) — a cluster is a
group of responses sharing prominent grounded-theory codes, not a frame.

**Choosing the number of clusters.** Chan takes the rule from Essary (2022): find the
largest break in the agglomeration coefficients, then "the optimal number of clusters
is found by taking the sample size number and then subtracting the number at the stage
of clustering break". With ``n - 1`` merge steps numbered from 1, that is

    n_clusters = n_samples - break_stage

and it is exactly the number of clusters still standing once ``break_stage`` merges
have happened. Chan's worked example — 50 articles, break at stage 47 — gives 3, which
:func:`schedule_from_distances` reproduces and the test suite asserts. The count is
**derived from the schedule and recorded**, never hard-coded;
``AnalysisConfig.n_clusters`` overrides it and the override is recorded as such in
:attr:`ClusterResult.n_clusters_source`.

**Degenerate input is refused, not rounded off.** Fewer than three responses, fewer
than two codes, an all-zero matrix, or a matrix whose rows are all identical each
raise :class:`DegenerateMatrixError` with the reason. The seed sample is only twenty
responses, so small-*n* behaviour is exercised for real and a quietly meaningless
dendrogram would be worse than an exception.

**Figures are hand-rendered SVG.** matplotlib is not a dependency of this project, so
:func:`dendrogram_svg` takes the coordinates scipy computes with ``no_plot=True`` and
emits the SVG itself. Output is a pure function of the linkage matrix: no timestamps,
no random ids, fixed numeric formatting, byte-identical across runs.

Validation principles: **reliability** (a pure, seedless function of the matrix) and
**transparency** (the schedule is printed so a reader can check the elbow themselves).
"""

from __future__ import annotations

import html
import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.cluster.hierarchy import dendrogram, fcluster, linkage

from gaf.analysis.matrix import OccurrenceMatrix
from gaf.config import AnalysisConfig

__all__ = [
    "MIN_CODES_FOR_HCA",
    "MIN_RESPONSES_FOR_HCA",
    "AgglomerationSchedule",
    "ClusterResult",
    "CodeMean",
    "DegenerateMatrixError",
    "MergeStep",
    "SaturationCurve",
    "SaturationPoint",
    "agglomeration_schedule",
    "choose_n_clusters",
    "cluster_means",
    "cluster_responses",
    "dendrogram_svg",
    "saturation_curve",
    "saturation_svg",
    "schedule_from_distances",
    "ward_linkage",
]

#: Ward's linkage needs at least one merge that is not the whole sample; below three
#: responses the schedule has fewer than two coefficients and "the largest break" is
#: not defined.
MIN_RESPONSES_FOR_HCA = 3

#: One code column reduces every response to a single bit; the resulting "clusters"
#: restate that bit and mean nothing.
MIN_CODES_FOR_HCA = 2


class DegenerateMatrixError(ValueError):
    """The occurrence matrix cannot support a meaningful cluster analysis.

    Raised rather than returning a number, because every degenerate case here
    (too few responses, one code, an all-zero matrix, identical rows) produces a
    linkage that *looks* like an answer and is not one.
    """


# --------------------------------------------------------------------------- #
# The agglomeration schedule
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class MergeStep:
    """One row of the agglomeration schedule.

    ``stage`` is 1-indexed, matching how the schedule is printed in the literature.
    ``distance`` is the agglomeration coefficient at that stage and ``delta`` its
    change from the previous stage — the quantity whose largest value is the "break".
    Stage 1 has ``delta = 0.0``: there is no earlier coefficient to break from.
    """

    stage: int
    left: int
    right: int
    distance: float
    delta: float
    size: int

    def to_json(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "left": self.left,
            "right": self.right,
            "distance": self.distance,
            "delta": self.delta,
            "size": self.size,
        }


@dataclass(frozen=True, slots=True)
class AgglomerationSchedule:
    """The full merge schedule and the cluster count it implies.

    ``n_samples - break_stage`` is the Essary rule Chan applies. ``warnings`` records
    the cases where that arithmetic produces a degenerate answer (one cluster, or as
    many clusters as responses) — reported rather than silently clamped, because a
    clamped count would misrepresent what the data said.
    """

    n_samples: int
    steps: tuple[MergeStep, ...]
    break_stage: int
    break_delta: float
    suggested_clusters: int
    warnings: tuple[str, ...] = ()

    def __len__(self) -> int:
        return len(self.steps)

    def largest_breaks(self, k: int = 5) -> tuple[MergeStep, ...]:
        """The ``k`` stages with the largest change in coefficient, largest first.

        Ties are broken by the later stage, matching :attr:`break_stage`.
        """
        ordered = sorted(self.steps, key=lambda s: (-s.delta, -s.stage))
        return tuple(ordered[:k])

    def to_json(self) -> dict[str, Any]:
        return {
            "n_samples": self.n_samples,
            "n_steps": len(self.steps),
            "break_stage": self.break_stage,
            "break_delta": self.break_delta,
            "suggested_clusters": self.suggested_clusters,
            "rule": "n_clusters = n_samples - break_stage (Essary 2022, via Chan 2025)",
            "warnings": list(self.warnings),
            "steps": [s.to_json() for s in self.steps],
        }

    def to_markdown(self, *, limit: int | None = 20) -> str:
        """The schedule as a markdown table — the elbow evidence, in printable form."""
        rows = self.steps if limit is None else self.steps[-limit:]
        head = (
            f"Agglomeration schedule — {len(self.steps)} merge steps over "
            f"{self.n_samples} responses. Largest break at stage {self.break_stage} "
            f"(delta {self.break_delta:.4f}) -> "
            f"{self.n_samples} - {self.break_stage} = {self.suggested_clusters} clusters."
        )
        lines = [head, ""]
        if limit is not None and len(self.steps) > limit:
            lines.append(f"_Showing the last {limit} of {len(self.steps)} stages._")
            lines.append("")
        lines.append("| stage | coefficient | change | cluster size |")
        lines.append("|---:|---:|---:|---:|")
        for step in rows:
            marker = " **<- break**" if step.stage == self.break_stage else ""
            lines.append(
                f"| {step.stage} | {step.distance:.4f} | {step.delta:.4f}{marker} "
                f"| {step.size} |"
            )
        for warning in self.warnings:
            lines.append("")
            lines.append(f"> **Warning.** {warning}")
        return "\n".join(lines)


def schedule_from_distances(
    distances: Sequence[float],
    *,
    pairs: Sequence[tuple[int, int]] | None = None,
    sizes: Sequence[int] | None = None,
) -> AgglomerationSchedule:
    """Build a schedule from the agglomeration coefficients alone.

    Separated from :func:`agglomeration_schedule` so the cluster-count rule can be
    exercised against a schedule constructed by hand — which is how Chan's worked
    example (50 samples, break at stage 47, three clusters) is unit-tested without
    inventing 50 responses that happen to produce it.

    ``n_samples`` is ``len(distances) + 1``: an agglomerative clustering of *n* points
    has exactly *n - 1* merges.
    """
    if len(distances) < 2:
        raise DegenerateMatrixError(
            "an agglomeration schedule needs at least 2 merge steps "
            f"(3 responses); got {len(distances)}"
        )
    values = [float(d) for d in distances]
    n_samples = len(values) + 1

    steps: list[MergeStep] = []
    for index, distance in enumerate(values):
        stage = index + 1
        delta = 0.0 if index == 0 else distance - values[index - 1]
        left, right = pairs[index] if pairs is not None else (-1, -1)
        size = int(sizes[index]) if sizes is not None else stage + 1
        steps.append(
            MergeStep(
                stage=stage,
                left=int(left),
                right=int(right),
                distance=distance,
                delta=delta,
                size=size,
            )
        )

    # The break is the stage with the largest increase in the coefficient. Stage 1 is
    # excluded because its delta is defined as 0.0, not measured. Ties go to the later
    # stage: a break late in the schedule is the one the rule is about, and preferring
    # the earlier stage would silently inflate the cluster count.
    break_step = max(steps[1:], key=lambda s: (s.delta, s.stage))
    suggested = n_samples - break_step.stage

    warnings: list[str] = []
    if suggested < 2:
        warnings.append(
            f"the largest break is at stage {break_step.stage} of {len(steps)}, so the "
            f"Essary rule gives {suggested} cluster(s); the data does not support a "
            "cluster structure at this sample size — set AnalysisConfig.n_clusters "
            "explicitly if a partition is wanted anyway."
        )
    # There is deliberately no "every response is its own cluster" branch: `break_step`
    # is chosen from `steps[1:]`, so its stage is always >= 2, so
    # `suggested = n_samples - stage <= n_samples - 2`. That branch existed and was
    # unreachable; a search over 4000 random schedules never entered it, and the
    # arithmetic says it cannot. The reachable failure is the leaf-end break below.
    if suggested > n_samples / 2:
        # The rule assumes the largest break falls near the ROOT of the tree, as it did
        # in Chan's 50-article study (stage 47 of 49). When it falls at the leaf end
        # instead — which happens on small samples with sparse code vectors, where the
        # first merges are between near-identical rows and cost almost nothing — the
        # arithmetic reads the tree backwards and returns a count close to the sample
        # size. On the 20-response seed sample it returns 18. That is not a partition;
        # it is the rule misfiring, and the caller must be told so, because the cluster
        # count is the study's headline result. See ADR-0020.
        warnings.append(
            f"the largest break is at stage {break_step.stage} of {len(steps)} — near "
            f"the LEAF end of the tree — so the Essary rule gives {suggested} clusters "
            f"for {n_samples} responses, more than half of them. The rule assumes the "
            "largest break falls near the root; at this sample size it does not, and "
            "this count is degenerate rather than a finding. Take the count from a "
            "larger corpus, or set AnalysisConfig.n_clusters explicitly and report it "
            "as an override. Late breaks in this schedule: "
            + ", ".join(
                f"stage {st.stage} (delta {st.delta:.4f}) -> {n_samples - st.stage} clusters"
                for st in sorted(steps[1:], key=lambda x: -x.delta)[:3]
                if n_samples - st.stage <= n_samples / 2
            )
        )

    return AgglomerationSchedule(
        n_samples=n_samples,
        steps=tuple(steps),
        break_stage=break_step.stage,
        break_delta=break_step.delta,
        suggested_clusters=suggested,
        warnings=tuple(warnings),
    )


def agglomeration_schedule(linkage_matrix: np.ndarray) -> AgglomerationSchedule:
    """The schedule implied by a scipy linkage matrix of shape ``(n - 1, 4)``."""
    array = np.asarray(linkage_matrix, dtype=np.float64)
    if array.ndim != 2 or array.shape[1] != 4:
        raise ValueError(f"expected a scipy linkage matrix of shape (n-1, 4), got {array.shape}")
    return schedule_from_distances(
        [float(d) for d in array[:, 2]],
        pairs=[(int(row[0]), int(row[1])) for row in array],
        sizes=[int(row[3]) for row in array],
    )


def choose_n_clusters(
    schedule: AgglomerationSchedule, override: int | None = None
) -> tuple[int, str]:
    """Return ``(n_clusters, source)`` — the schedule's answer, or a recorded override.

    ``source`` is ``"schedule"`` or ``"config_override"``. The override is never
    applied silently: the caller stores the source on the result and the run report
    prints it, so a reader always knows whether the number came from the data.
    """
    if override is None:
        return schedule.suggested_clusters, "schedule"
    if override < 1:
        raise ValueError(f"AnalysisConfig.n_clusters must be >= 1, got {override}")
    if override > schedule.n_samples:
        raise ValueError(
            f"AnalysisConfig.n_clusters={override} exceeds the sample size "
            f"{schedule.n_samples}"
        )
    return int(override), "config_override"


# --------------------------------------------------------------------------- #
# Clustering
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class CodeMean:
    """Mean occurrence of one code inside one cluster."""

    code: str
    mean: float
    count: int
    prominent: bool

    def to_json(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "mean": self.mean,
            "count": self.count,
            "prominent": self.prominent,
        }


@dataclass(frozen=True, slots=True)
class ClusterResult:
    """Everything Ward's HCA produced, in a form a reviewer can re-derive."""

    response_ids: tuple[int, ...]
    code_names: tuple[str, ...]
    labels: np.ndarray
    n_clusters: int
    n_clusters_source: str
    schedule: AgglomerationSchedule
    linkage: np.ndarray
    means: dict[int, tuple[CodeMean, ...]]
    sizes: dict[int, int]
    highlight: float
    cut_distance: float
    warnings: tuple[str, ...] = ()

    def cluster_of(self, response_id: int) -> int:
        index = self.response_ids.index(response_id)
        return int(self.labels[index])

    def members(self, cluster: int) -> tuple[int, ...]:
        return tuple(
            rid for rid, lab in zip(self.response_ids, self.labels, strict=True)
            if int(lab) == cluster
        )

    def prominent_codes(self, cluster: int) -> tuple[CodeMean, ...]:
        """Codes at or above ``AnalysisConfig.cluster_mean_highlight`` (Chan: 0.4)."""
        return tuple(m for m in self.means[cluster] if m.prominent)

    def to_json(self) -> dict[str, Any]:
        return {
            "n_responses": len(self.response_ids),
            "n_codes": len(self.code_names),
            "n_clusters": self.n_clusters,
            "n_clusters_source": self.n_clusters_source,
            "cluster_mean_highlight": self.highlight,
            "cut_distance": self.cut_distance,
            "warnings": list(self.warnings),
            "response_ids": list(self.response_ids),
            "labels": [int(x) for x in self.labels],
            "sizes": {str(k): v for k, v in sorted(self.sizes.items())},
            "members": {
                str(c): list(self.members(c)) for c in sorted(self.sizes)
            },
            "means": {
                str(c): [m.to_json() for m in self.means[c]] for c in sorted(self.means)
            },
            "schedule": self.schedule.to_json(),
        }

    def to_json_str(self) -> str:
        return json.dumps(self.to_json(), sort_keys=True, ensure_ascii=False, indent=2)

    def to_markdown(self, *, top_n: int = 10) -> str:
        """The cluster interpretation table: sizes, then prominent codes per cluster."""
        source = (
            "derived from the agglomeration schedule"
            if self.n_clusters_source == "schedule"
            else "set explicitly in AnalysisConfig.n_clusters"
        )
        lines = [
            "## Ward's hierarchical cluster analysis",
            "",
            f"{len(self.response_ids)} responses x {len(self.code_names)} codes; "
            f"{self.n_clusters} clusters ({source}).",
            "",
        ]
        # The warnings belong in the artefact, not only on the operator's terminal.
        # clusters.md is what a reader keeps and quotes from; a caveat that scrolled
        # past in a shell is not a caveat. The cluster count is this study's headline.
        if self.warnings:
            lines.append("> **Read this before quoting the cluster count.**")
            lines.append(">")
            for warning in self.warnings:
                lines.append(f"> - {warning}")
            lines.append("")
        lines += [
            "| cluster | n | share | prominent codes (mean >= "
            f"{self.highlight:g}) |",
            "|---:|---:|---:|---|",
        ]
        total = len(self.response_ids)
        for cluster in sorted(self.sizes):
            size = self.sizes[cluster]
            prominent = self.prominent_codes(cluster)
            rendered = (
                ", ".join(f"{m.code} ({m.mean:.2f})" for m in prominent)
                if prominent
                else "_none above the highlight threshold_"
            )
            lines.append(
                f"| {cluster} | {size} | {size / total:.0%} | {rendered} |"
            )
        for cluster in sorted(self.means):
            lines.extend(
                [
                    "",
                    f"### Cluster {cluster} — code means (top {top_n})",
                    "",
                    "| code | mean | responses |",
                    "|---|---:|---:|",
                ]
            )
            for mean in self.means[cluster][:top_n]:
                marker = " **" if mean.prominent else " "
                suffix = "**" if mean.prominent else ""
                lines.append(
                    f"| {mean.code} |{marker}{mean.mean:.3f}{suffix} | {mean.count} |"
                )
        lines.extend(["", self.schedule.to_markdown()])
        for warning in self.warnings:
            lines.extend(["", f"> **Warning.** {warning}"])
        return "\n".join(lines)


def _require_analysable(matrix: OccurrenceMatrix) -> None:
    """Refuse the four degenerate shapes, each with the reason it was refused."""
    if matrix.n_responses < MIN_RESPONSES_FOR_HCA:
        raise DegenerateMatrixError(
            f"Ward's HCA needs at least {MIN_RESPONSES_FOR_HCA} responses; the matrix "
            f"has {matrix.n_responses}. With fewer, the agglomeration schedule has no "
            "break to find."
        )
    if matrix.n_codes < MIN_CODES_FOR_HCA:
        raise DegenerateMatrixError(
            f"Ward's HCA needs at least {MIN_CODES_FOR_HCA} codes; the matrix has "
            f"{matrix.n_codes}. A single column reduces each response to one bit and "
            "the clusters would only restate it. Check the low-frequency filter: "
            f"{matrix.filter.summary()}"
        )
    if not matrix.values.any():
        raise DegenerateMatrixError(
            "the occurrence matrix is all zeros — no code survived the low-frequency "
            f"filter with any occurrence. {matrix.filter.summary()}"
        )


def ward_linkage(matrix: OccurrenceMatrix, *, config: AnalysisConfig | None = None) -> np.ndarray:
    """Ward's linkage over the **rows** (responses) of the binary matrix.

    ``AnalysisConfig.linkage_method``/``linkage_metric`` are honoured, but the
    defaults — and what Chan (2025) used — are Ward's method on Euclidean distance,
    which for a binary matrix is the squared count of codes the two responses differ
    on. Anything else is a deviation and should be recorded as one.
    """
    cfg = config or AnalysisConfig()
    _require_analysable(matrix)
    data = matrix.as_float()
    matrix_linkage = linkage(data, method=cfg.linkage_method, metric=cfg.linkage_metric)
    coefficients = np.asarray(matrix_linkage, dtype=np.float64)[:, 2]
    if float(coefficients.max()) <= 0.0:
        raise DegenerateMatrixError(
            "every pair of responses has distance zero — all responses carry an "
            "identical set of codes, so there is no structure to cluster."
        )
    return matrix_linkage


def cluster_means(
    matrix: OccurrenceMatrix,
    labels: Sequence[int] | np.ndarray,
    *,
    highlight: float = 0.4,
) -> dict[int, tuple[CodeMean, ...]]:
    """Mean occurrence of every code within every cluster.

    Each cluster's table is sorted by mean descending, then code name ascending, so
    the prominent codes are at the top and the ordering is total.
    """
    label_array = np.asarray([int(x) for x in labels], dtype=np.int64)
    if label_array.shape[0] != matrix.n_responses:
        raise ValueError(
            f"labels has {label_array.shape[0]} entries but the matrix has "
            f"{matrix.n_responses} rows"
        )
    values = matrix.as_float()
    out: dict[int, tuple[CodeMean, ...]] = {}
    for cluster in sorted({int(x) for x in label_array}):
        mask = label_array == cluster
        block = values[mask, :]
        means = block.mean(axis=0)
        counts = block.sum(axis=0)
        rows = [
            CodeMean(
                code=name,
                mean=float(means[j]),
                count=int(counts[j]),
                prominent=bool(float(means[j]) >= highlight),
            )
            for j, name in enumerate(matrix.code_names)
        ]
        rows.sort(key=lambda m: (-m.mean, m.code))
        out[cluster] = tuple(rows)
    return out


def _cut_distance(linkage_matrix: np.ndarray, n_samples: int, n_clusters: int) -> float:
    """Distance at which cutting the tree yields ``n_clusters`` — for the figure.

    Midway between the coefficient of the last merge that keeps ``n_clusters`` and the
    coefficient of the merge that would collapse them to ``n_clusters - 1``. Used only
    to draw the cut line and to colour the dendrogram consistently with the reported
    partition; the partition itself comes from ``fcluster``.
    """
    coefficients = np.asarray(linkage_matrix, dtype=np.float64)[:, 2]
    if n_clusters <= 1:
        return float(coefficients[-1]) * 1.05
    if n_clusters >= n_samples:
        return 0.0
    below = float(coefficients[n_samples - n_clusters - 1])
    above = float(coefficients[n_samples - n_clusters])
    return (below + above) / 2.0


def cluster_responses(
    matrix: OccurrenceMatrix, *, config: AnalysisConfig | None = None
) -> ClusterResult:
    """The whole Chan analysis for one matrix: linkage, schedule, count, means."""
    cfg = config or AnalysisConfig()
    matrix_linkage = ward_linkage(matrix, config=cfg)
    schedule = agglomeration_schedule(matrix_linkage)
    n_clusters, source = choose_n_clusters(schedule, cfg.n_clusters)

    warnings = list(schedule.warnings) if source == "schedule" else []
    effective = max(1, min(n_clusters, matrix.n_responses))
    labels = fcluster(matrix_linkage, t=effective, criterion="maxclust")
    labels = np.asarray(labels, dtype=np.int64)

    distinct = sorted({int(x) for x in labels})
    if len(distinct) != n_clusters:
        warnings.append(
            f"{n_clusters} clusters were requested but the tree yields {len(distinct)} "
            "distinct groups — merge distances are tied at the cut."
        )

    means = cluster_means(matrix, labels, highlight=cfg.cluster_mean_highlight)
    sizes = {c: int((labels == c).sum()) for c in distinct}

    return ClusterResult(
        response_ids=matrix.response_ids,
        code_names=matrix.code_names,
        labels=labels,
        n_clusters=n_clusters,
        n_clusters_source=source,
        schedule=schedule,
        linkage=np.asarray(matrix_linkage, dtype=np.float64),
        means=means,
        sizes=sizes,
        highlight=cfg.cluster_mean_highlight,
        cut_distance=_cut_distance(matrix_linkage, matrix.n_responses, n_clusters),
        warnings=tuple(warnings),
    )


# --------------------------------------------------------------------------- #
# Saturation
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class SaturationPoint:
    """One batch of the saturation curve."""

    batch: int
    responses_in_batch: int
    cumulative_responses: int
    new_codes: int
    cumulative_codes: int
    new_code_names: tuple[str, ...]

    def to_json(self) -> dict[str, Any]:
        return {
            "batch": self.batch,
            "responses_in_batch": self.responses_in_batch,
            "cumulative_responses": self.cumulative_responses,
            "new_codes": self.new_codes,
            "cumulative_codes": self.cumulative_codes,
            "new_code_names": list(self.new_code_names),
        }


@dataclass(frozen=True, slots=True)
class SaturationCurve:
    """New codes per batch and cumulative unique codes over the run.

    Theoretical saturation is the grounded-theory claim that further sampling stops
    producing new codes, so the artefact that supports it is this curve flattening.
    ``saturated_at_batch`` is the first batch that contributed nothing new, or
    ``None`` if every batch still did.
    """

    batch_size: int
    points: tuple[SaturationPoint, ...]
    total_codes: int
    saturated_at_batch: int | None

    def to_json(self) -> dict[str, Any]:
        return {
            "batch_size": self.batch_size,
            "total_codes": self.total_codes,
            "saturated_at_batch": self.saturated_at_batch,
            "points": [p.to_json() for p in self.points],
        }

    def to_markdown(self) -> str:
        lines = [
            "## Saturation",
            "",
            f"Batch size {self.batch_size}; {self.total_codes} distinct codes in total.",
            "",
            "| batch | responses | cumulative responses | new codes | cumulative codes |",
            "|---:|---:|---:|---:|---:|",
        ]
        for point in self.points:
            lines.append(
                f"| {point.batch} | {point.responses_in_batch} | "
                f"{point.cumulative_responses} | {point.new_codes} | "
                f"{point.cumulative_codes} |"
            )
        lines.append("")
        if self.saturated_at_batch is None:
            lines.append(
                "_No batch was empty of new codes: the curve has not flattened, so "
                "theoretical saturation is not yet evidenced._"
            )
        else:
            lines.append(
                f"_First batch contributing no new code: batch "
                f"{self.saturated_at_batch}._"
            )
        return "\n".join(lines)


def saturation_curve(
    matrix: OccurrenceMatrix,
    *,
    config: AnalysisConfig | None = None,
    order: Sequence[int] | None = None,
) -> SaturationCurve:
    """New codes per batch of responses, and the cumulative unique-code count.

    Batches are consecutive runs of ``AnalysisConfig.saturation_batch_size`` responses
    taken in matrix row order — response id ascending — which is the order the fast
    loop walks a corpus. ``order`` overrides that with the real coding order when it
    is known and differs.

    Pass the **unfiltered** matrix: the low-frequency filter removes exactly the rare
    codes whose arrival is the interesting part of this curve, so a filtered matrix
    reports saturation earlier than the run actually reached it.
    """
    cfg = config or AnalysisConfig()
    batch_size = max(1, int(cfg.saturation_batch_size))

    if order is None:
        sequence = list(matrix.response_ids)
    else:
        sequence = [int(r) for r in order]
        unknown = [r for r in sequence if r not in set(matrix.response_ids)]
        if unknown:
            raise ValueError(f"order names response ids absent from the matrix: {unknown[:10]}")

    seen: set[str] = set()
    points: list[SaturationPoint] = []
    cumulative_responses = 0
    saturated_at: int | None = None

    for index in range(0, len(sequence), batch_size):
        chunk = sequence[index : index + batch_size]
        fresh: list[str] = []
        for response_id in chunk:
            row = matrix.row(response_id)
            for j, name in enumerate(matrix.code_names):
                if row[j] and name not in seen:
                    seen.add(name)
                    fresh.append(name)
        cumulative_responses += len(chunk)
        batch_number = index // batch_size + 1
        if not fresh and saturated_at is None:
            saturated_at = batch_number
        points.append(
            SaturationPoint(
                batch=batch_number,
                responses_in_batch=len(chunk),
                cumulative_responses=cumulative_responses,
                new_codes=len(fresh),
                cumulative_codes=len(seen),
                new_code_names=tuple(sorted(fresh)),
            )
        )

    return SaturationCurve(
        batch_size=batch_size,
        points=tuple(points),
        total_codes=len(seen),
        saturated_at_batch=saturated_at,
    )


# --------------------------------------------------------------------------- #
# Hand-rendered SVG (no matplotlib anywhere in this project)
# --------------------------------------------------------------------------- #

#: Deterministic stand-in for matplotlib's default cycle. scipy's `dendrogram` returns
#: colour *names* ("C0".."C9"); mapping them through a fixed table keeps the figure a
#: pure function of the linkage and independent of any plotting library's defaults.
_PALETTE: dict[str, str] = {
    "C0": "#4a5568",
    "C1": "#2b6cb0",
    "C2": "#2f855a",
    "C3": "#b7791f",
    "C4": "#9b2c2c",
    "C5": "#6b46c1",
    "C6": "#0987a0",
    "C7": "#975a16",
    "C8": "#702459",
    "C9": "#276749",
}
_DEFAULT_STROKE = "#4a5568"

_SVG_CSS = (
    "text{font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;fill:#1a202c}"
    ".axis{stroke:#a0aec0;stroke-width:1}"
    ".grid{stroke:#e2e8f0;stroke-width:1}"
    ".link{fill:none;stroke-width:1.4;stroke-linejoin:round}"
    ".cut{stroke:#c53030;stroke-width:1.2;stroke-dasharray:5 4;fill:none}"
    ".ttl{font-size:14px;font-weight:600}"
    ".lbl{font-size:9px;fill:#4a5568}"
    ".tick{font-size:10px;fill:#4a5568}"
    ".bar{fill:#90cdf4;stroke:#2b6cb0;stroke-width:0.8}"
    ".curve{fill:none;stroke:#2f855a;stroke-width:2}"
    ".dot{fill:#2f855a}"
)


def _num(value: float, places: int = 2) -> str:
    """Fixed-precision number for SVG output, with negative zero normalised.

    Byte-identical output across runs and platforms depends on never letting a
    ``-0.00`` or a repr difference into the file.
    """
    text = f"{value:.{places}f}"
    if text.startswith("-") and float(text) == 0.0:
        text = text[1:]
    return text


def _svg_open(width: int, height: int, title: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(title)}">',
        f"<title>{html.escape(title)}</title>",
        f"<style>{_SVG_CSS}</style>",
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>',
    ]


def dendrogram_svg(
    result: ClusterResult,
    *,
    width: int = 960,
    height: int = 520,
    title: str | None = None,
    label_every: int = 1,
) -> str:
    """A self-contained SVG dendrogram, rendered from scipy's plot coordinates.

    ``scipy.cluster.hierarchy.dendrogram(..., no_plot=True)`` returns ``icoord`` and
    ``dcoord`` — the four-point polyline of every link — plus the leaf order and
    per-link colours, with no plotting library involved. This function maps those into
    an SVG viewport and writes the elements out.

    The result is a pure function of ``result``: fixed viewport, fixed colour table,
    two-decimal coordinates, no timestamp, no generated id. Two calls on the same
    input produce identical bytes, which the test suite asserts.

    ``label_every`` thins the leaf labels (``2`` prints every other one) for corpora
    too large to label densely; the ticks and links are unaffected.
    """
    label_text = [str(rid) for rid in result.response_ids]
    tree = dendrogram(
        result.linkage,
        no_plot=True,
        labels=label_text,
        color_threshold=result.cut_distance,
    )
    icoord: list[list[float]] = [[float(v) for v in seg] for seg in tree["icoord"]]
    dcoord: list[list[float]] = [[float(v) for v in seg] for seg in tree["dcoord"]]
    leaf_labels: list[str] = [str(v) for v in tree["ivl"]]
    colors: list[str] = [str(c) for c in tree.get("color_list", [])]

    n_leaves = len(leaf_labels)
    x_span = 10.0 * n_leaves
    d_max = max((max(seg) for seg in dcoord), default=1.0) or 1.0

    left, right, top = 60, 24, 44
    bottom = 30 + 6 * max((len(label) for label in leaf_labels), default=2)
    plot_w = max(1, width - left - right)
    plot_h = max(1, height - top - bottom)

    def sx(value: float) -> float:
        return left + (value / x_span) * plot_w

    def sy(value: float) -> float:
        return top + plot_h * (1.0 - value / d_max)

    heading = title or (
        f"Ward's linkage — {n_leaves} responses, {result.n_clusters} clusters"
    )
    parts = _svg_open(width, height, heading)
    parts.append(f'<text class="ttl" x="{left}" y="24">{html.escape(heading)}</text>')

    # Distance axis with five ticks.
    parts.append(
        f'<line class="axis" x1="{left}" y1="{_num(sy(0.0))}" x2="{left}" '
        f'y2="{_num(sy(d_max))}"/>'
    )
    for step in range(6):
        value = d_max * step / 5.0
        y = sy(value)
        parts.append(
            f'<line class="grid" x1="{left}" y1="{_num(y)}" x2="{left + plot_w}" '
            f'y2="{_num(y)}"/>'
        )
        parts.append(
            f'<text class="tick" x="{left - 6}" y="{_num(y + 3)}" text-anchor="end">'
            f"{_num(value)}</text>"
        )

    # The links themselves.
    for index, (xs, ys) in enumerate(zip(icoord, dcoord, strict=True)):
        stroke = _PALETTE.get(colors[index] if index < len(colors) else "", _DEFAULT_STROKE)
        points = " ".join(
            f"{_num(sx(x))},{_num(sy(y))}" for x, y in zip(xs, ys, strict=True)
        )
        parts.append(f'<polyline class="link" stroke="{stroke}" points="{points}"/>')

    # The cut that produces the reported partition.
    if 1 < result.n_clusters < n_leaves:
        cut_y = sy(result.cut_distance)
        parts.append(
            f'<line class="cut" x1="{left}" y1="{_num(cut_y)}" x2="{left + plot_w}" '
            f'y2="{_num(cut_y)}"/>'
        )
        parts.append(
            f'<text class="tick" x="{left + plot_w}" y="{_num(cut_y - 4)}" '
            f'text-anchor="end" fill="#c53030">cut for k={result.n_clusters} '
            f"(d={_num(result.cut_distance, 3)})</text>"
        )

    # Leaf labels, rotated so long ids do not collide.
    every = max(1, int(label_every))
    baseline = top + plot_h + 8
    for position, label in enumerate(leaf_labels):
        if position % every:
            continue
        x = sx(10.0 * position + 5.0)
        parts.append(
            f'<text class="lbl" x="{_num(x)}" y="{_num(baseline)}" text-anchor="end" '
            f'transform="rotate(-90 {_num(x)} {_num(baseline)})">{html.escape(label)}</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def saturation_svg(
    curve: SaturationCurve,
    *,
    width: int = 760,
    height: int = 380,
    title: str = "Theoretical saturation",
) -> str:
    """A self-contained SVG of the saturation curve: bars for new codes, line for total.

    Both series share one axis because new codes per batch can never exceed the
    cumulative total, which keeps the figure readable without a second scale. Pure
    function of ``curve``; byte-identical across runs.
    """
    points = curve.points
    if not points:
        parts = _svg_open(width, height, title)
        parts.append(f'<text class="ttl" x="40" y="30">{html.escape(title)}</text>')
        parts.append(
            '<text class="tick" x="40" y="56">No batches — the matrix has no rows.</text>'
        )
        parts.append("</svg>")
        return "\n".join(parts) + "\n"

    left, right, top, bottom = 56, 24, 44, 56
    plot_w = max(1, width - left - right)
    plot_h = max(1, height - top - bottom)
    y_max = max(curve.total_codes, max(p.new_codes for p in points), 1)
    slot = plot_w / len(points)

    def sy(value: float) -> float:
        return top + plot_h * (1.0 - value / y_max)

    parts = _svg_open(width, height, title)
    parts.append(f'<text class="ttl" x="{left}" y="24">{html.escape(title)}</text>')

    for step in range(5):
        value = y_max * step / 4.0
        y = sy(value)
        parts.append(
            f'<line class="grid" x1="{left}" y1="{_num(y)}" x2="{left + plot_w}" '
            f'y2="{_num(y)}"/>'
        )
        parts.append(
            f'<text class="tick" x="{left - 6}" y="{_num(y + 3)}" text-anchor="end">'
            f"{_num(value, 0)}</text>"
        )
    parts.append(
        f'<line class="axis" x1="{left}" y1="{_num(sy(0))}" x2="{left + plot_w}" '
        f'y2="{_num(sy(0))}"/>'
    )

    bar_w = max(2.0, slot * 0.55)
    for index, point in enumerate(points):
        cx = left + slot * (index + 0.5)
        y = sy(point.new_codes)
        parts.append(
            f'<rect class="bar" x="{_num(cx - bar_w / 2)}" y="{_num(y)}" '
            f'width="{_num(bar_w)}" height="{_num(sy(0) - y)}"/>'
        )
        parts.append(
            f'<text class="lbl" x="{_num(cx)}" y="{_num(sy(0) + 14)}" '
            f'text-anchor="middle">{point.cumulative_responses}</text>'
        )

    line = " ".join(
        f"{_num(left + slot * (i + 0.5))},{_num(sy(p.cumulative_codes))}"
        for i, p in enumerate(points)
    )
    parts.append(f'<polyline class="curve" points="{line}"/>')
    for index, point in enumerate(points):
        cx = left + slot * (index + 0.5)
        parts.append(
            f'<circle class="dot" cx="{_num(cx)}" cy="{_num(sy(point.cumulative_codes))}" r="3"/>'
        )

    parts.append(
        f'<text class="tick" x="{left}" y="{height - 14}">responses coded '
        f"(batch size {curve.batch_size}) — bars: new codes; line: cumulative unique "
        f"codes</text>"
    )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"
