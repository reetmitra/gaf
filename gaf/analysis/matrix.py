"""The binary occurrence matrix — responses x codes — and the low-frequency filter.

This is the first stage of the deterministic analysis tail (Chan 2025). It turns the
row-oriented coding record into the one rectangular artefact everything downstream is
a pure function of: a matrix whose cell ``(r, c)`` is ``1`` when code ``c`` was applied
anywhere in response ``r`` and ``0`` otherwise. Multiplicity is deliberately discarded
— a code applied to three segments of one response is still one occurrence, because
the clustering question is *which elements co-occur in a response*, not how often a
coder repeated itself.

**Canonical input.** ``list[Assignment]`` is canonical: it is the shape the pipeline
writes, the shape the PI's golden set arrives in, and the shape a human can produce in
a spreadsheet. A :class:`~gaf.models.Codebook` is *projected* into that shape by
:func:`assignments_from_codebook`, which reads **verified** evidence only — evidence
whose quote S2 could not locate has no provenance and therefore no occurrence.

**Row and column order** (documented because the CSV is an artefact a reviewer diffs):

* rows are response ids, sorted **ascending numerically**;
* columns are code names, sorted **ascending by Unicode code point** (plain ``sorted``).

Both orders are total and independent of input order, so two runs over the same
codings produce a byte-identical CSV.

**The low-frequency filter** implements ADR-0010. Two rules exist and the stricter
always wins; both are reported, along with every code dropped and the count that
dropped it.

**Respondent metadata is joined here and only here** — never during coding.
:func:`build_matrix` accepts the corpus and copies each response's ``meta`` onto the
matrix; :func:`metadata_crosstab` cross-tabulates it against cluster labels for the
interpretation table. No model ever sees it.

Validation principles: **reliability** (deterministic order, pure function of the
codings) and **transparency** (the filter reports what it removed and why).
"""

from __future__ import annotations

import json
import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from gaf.config import AnalysisConfig
from gaf.models import Assignment, Codebook, Response

__all__ = [
    "DroppedCode",
    "FilterReport",
    "OccurrenceMatrix",
    "assignments_from_codebook",
    "build_matrix",
    "matrix_from_codebook",
    "metadata_crosstab",
    "metadata_keys",
]


# --------------------------------------------------------------------------- #
# The filter report
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class DroppedCode:
    """One code removed by the low-frequency filter, with the arithmetic that did it."""

    name: str
    n_responses: int
    threshold: int
    reason: str

    def to_json(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "n_responses": self.n_responses,
            "threshold": self.threshold,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class FilterReport:
    """What the low-frequency filter was asked to do, and what it did (ADR-0010).

    ``binding_rule`` names which of the two configured rules actually set the
    threshold: ``"absolute"`` (``min_code_frequency``), ``"fraction"``
    (``min_code_frequency_fraction`` x the sample size), or ``"both"`` when they
    coincide. ``"none"`` means no filtering was possible or requested.
    """

    n_responses: int
    min_code_frequency: int
    min_code_frequency_fraction: float | None
    fraction_threshold: int | None
    threshold: int
    binding_rule: str
    kept: tuple[str, ...]
    dropped: tuple[DroppedCode, ...]

    def to_json(self) -> dict[str, Any]:
        return {
            "n_responses": self.n_responses,
            "min_code_frequency": self.min_code_frequency,
            "min_code_frequency_fraction": self.min_code_frequency_fraction,
            "fraction_threshold": self.fraction_threshold,
            "threshold": self.threshold,
            "binding_rule": self.binding_rule,
            "n_kept": len(self.kept),
            "n_dropped": len(self.dropped),
            "kept": list(self.kept),
            "dropped": [d.to_json() for d in self.dropped],
        }

    def summary(self) -> str:
        """One sentence for the run report."""
        if not self.dropped:
            return (
                f"Low-frequency filter: threshold {self.threshold} response(s) "
                f"({self.binding_rule}); no codes dropped from {len(self.kept)}."
            )
        names = ", ".join(d.name for d in self.dropped)
        return (
            f"Low-frequency filter: threshold {self.threshold} response(s) "
            f"({self.binding_rule}); dropped {len(self.dropped)} of "
            f"{len(self.kept) + len(self.dropped)} codes: {names}."
        )


def _fraction_threshold(fraction: float, n_responses: int) -> int:
    """Smallest integer count that is *not* "less than `fraction` of the sample".

    Chan's rule is stated as a fraction — "elements that appeared in less than 5% of
    the codes (than three out of fifty articles) were filtered out" — so a code is
    kept when ``count >= fraction * n``. The integer threshold is therefore
    ``ceil(fraction * n)``, computed with a tolerance because ``0.05 * 60`` is
    ``3.0000000000000004`` in binary floating point and a naive ``ceil`` would turn
    Chan's 5% rule into a 6.7% rule on some sample sizes.
    """
    if fraction <= 0.0:
        return 0
    return max(0, math.ceil(fraction * n_responses - 1e-9))


# --------------------------------------------------------------------------- #
# The matrix
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class OccurrenceMatrix:
    """Responses x codes, binary, in a documented deterministic order.

    ``values`` is a read-only ``int8`` array of shape ``(len(response_ids),
    len(code_names))`` containing only ``0`` and ``1``. ``meta`` holds respondent
    metadata keyed by response id — the *only* place in the system where it is
    attached to anything.
    """

    response_ids: tuple[int, ...]
    code_names: tuple[str, ...]
    values: np.ndarray
    filter: FilterReport
    meta: dict[int, dict[str, Any]] = field(default_factory=dict)

    # -- shape ------------------------------------------------------------ #

    @property
    def n_responses(self) -> int:
        return len(self.response_ids)

    @property
    def n_codes(self) -> int:
        return len(self.code_names)

    @property
    def is_empty(self) -> bool:
        """True when there is nothing to analyse — no rows or no columns."""
        return self.n_responses == 0 or self.n_codes == 0

    # -- slices ----------------------------------------------------------- #

    def column(self, code: str) -> np.ndarray:
        """The occurrence column for one code name."""
        try:
            index = self.code_names.index(code)
        except ValueError:
            raise KeyError(f"code {code!r} is not a column of this matrix") from None
        return self.values[:, index]

    def row(self, response_id: int) -> np.ndarray:
        """The occurrence row for one response id."""
        try:
            index = self.response_ids.index(response_id)
        except ValueError:
            raise KeyError(f"response {response_id} is not a row of this matrix") from None
        return self.values[index, :]

    def frequencies(self) -> dict[str, int]:
        """Code name -> number of responses it occurs in, in column order."""
        if self.is_empty:
            return {}
        totals = self.values.sum(axis=0)
        return {name: int(totals[i]) for i, name in enumerate(self.code_names)}

    def codes_per_response(self) -> dict[int, int]:
        """Response id -> number of distinct codes applied, in row order."""
        if self.is_empty:
            return dict.fromkeys(self.response_ids, 0)
        totals = self.values.sum(axis=1)
        return {rid: int(totals[i]) for i, rid in enumerate(self.response_ids)}

    def as_float(self) -> np.ndarray:
        """A writable float64 copy — the shape scipy's linkage wants."""
        return self.values.astype(np.float64, copy=True)

    # -- artefacts -------------------------------------------------------- #

    def to_csv(self) -> str:
        """CSV in the documented order: header ``response_id`` then code names.

        Written by hand rather than through :mod:`csv` so the line terminator is a
        plain ``\\n`` on every platform — the file is diffed by reviewers and hashed
        into the run report, and a platform-dependent terminator would break both.
        Code names are quoted only when they need to be, by the same rule
        :func:`_csv_field` applies everywhere.
        """
        header = ",".join(["response_id", *(_csv_field(c) for c in self.code_names)])
        lines = [header]
        for i, rid in enumerate(self.response_ids):
            cells = (str(int(v)) for v in self.values[i, :])
            lines.append(",".join([str(rid), *cells]))
        return "\n".join(lines) + "\n"

    def write_csv(self, path: str | Path) -> Path:
        """Write :meth:`to_csv` to ``path`` (UTF-8, no BOM) and return the path."""
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.to_csv(), encoding="utf-8", newline="")
        return target

    def to_json(self) -> dict[str, Any]:
        """Machine-readable form for ``occurrence_matrix.json``."""
        return {
            "response_ids": list(self.response_ids),
            "code_names": list(self.code_names),
            "values": [[int(v) for v in row] for row in self.values],
            "frequencies": self.frequencies(),
            "filter": self.filter.to_json(),
            "meta": {str(k): v for k, v in sorted(self.meta.items())},
        }

    def to_json_str(self) -> str:
        return json.dumps(self.to_json(), sort_keys=True, ensure_ascii=False, indent=2)


def _csv_field(value: str) -> str:
    """Minimal RFC-4180 quoting: quote only when the field contains a delimiter."""
    if any(ch in value for ch in (",", '"', "\n", "\r")):
        return '"' + value.replace('"', '""') + '"'
    return value


# --------------------------------------------------------------------------- #
# Construction
# --------------------------------------------------------------------------- #


def assignments_from_codebook(codebook: Codebook) -> list[Assignment]:
    """Project a codebook's **verified** evidence into the canonical assignment shape.

    One :class:`~gaf.models.Assignment` per (code, evidence quote) pair, with the quote
    as the segment. Unverified evidence is skipped: S2 could not locate the quote in
    the source, so the occurrence has no provenance and must not enter the matrix.

    Output is sorted by ``(response_id, code, segment)`` so the projection is a
    deterministic function of the codebook.
    """
    rows: list[Assignment] = []
    for code in codebook.sorted_codes():
        for evidence in code.evidence:
            if not evidence.verified:
                continue
            rows.append(
                Assignment(
                    response_id=evidence.response_id,
                    segment=evidence.quote,
                    code=code.name,
                )
            )
    return sorted(rows, key=lambda a: (a.response_id, a.code, a.segment))


def build_matrix(
    assignments: Sequence[Assignment],
    *,
    config: AnalysisConfig | None = None,
    responses: Sequence[Response] | None = None,
) -> OccurrenceMatrix:
    """Build the binary occurrence matrix from the canonical assignment rows.

    ``responses`` does two things when supplied: it fixes the **row universe**, so a
    response nobody coded still appears as an all-zero row (which is what makes the
    denominator of the low-frequency fraction the sample size rather than the coded
    subset), and it supplies the respondent metadata joined onto the result. An
    assignment naming a response outside that universe is an error, not a silent
    extra row — it means the codings and the corpus disagree.

    With no assignments and no corpus the result is an empty 0x0 matrix rather than an
    exception: "nothing has been coded yet" is a legitimate state at the start of a
    run, and the emptiness is visible in :attr:`OccurrenceMatrix.is_empty`.
    """
    cfg = config or AnalysisConfig()

    if responses is not None:
        universe = sorted({r.id for r in responses})
        known = set(universe)
        unknown = sorted({a.response_id for a in assignments} - known)
        if unknown:
            raise ValueError(
                "assignments reference response ids that are not in the corpus: "
                f"{unknown[:10]}{' ...' if len(unknown) > 10 else ''}"
            )
        meta = {r.id: dict(r.meta) for r in responses}
    else:
        universe = sorted({a.response_id for a in assignments})
        meta = {}

    all_codes = sorted({a.code for a in assignments})
    row_index = {rid: i for i, rid in enumerate(universe)}
    col_index = {name: j for j, name in enumerate(all_codes)}

    full = np.zeros((len(universe), len(all_codes)), dtype=np.int8)
    for assignment in assignments:
        full[row_index[assignment.response_id], col_index[assignment.code]] = 1

    counts = full.sum(axis=0) if all_codes else np.zeros(0, dtype=np.int64)
    report = _apply_filter(all_codes, [int(c) for c in counts], len(universe), cfg)

    keep = [col_index[name] for name in report.kept]
    values = full[:, keep] if keep else np.zeros((len(universe), 0), dtype=np.int8)
    values = np.ascontiguousarray(values, dtype=np.int8)
    values.setflags(write=False)

    return OccurrenceMatrix(
        response_ids=tuple(universe),
        code_names=tuple(report.kept),
        values=values,
        filter=report,
        meta=meta,
    )


def matrix_from_codebook(
    codebook: Codebook,
    *,
    config: AnalysisConfig | None = None,
    responses: Sequence[Response] | None = None,
) -> OccurrenceMatrix:
    """Convenience: :func:`assignments_from_codebook` then :func:`build_matrix`."""
    return build_matrix(
        assignments_from_codebook(codebook), config=config, responses=responses
    )


def _apply_filter(
    code_names: Sequence[str],
    counts: Sequence[int],
    n_responses: int,
    config: AnalysisConfig,
) -> FilterReport:
    """Decide the threshold (ADR-0010: the stricter of the two rules) and apply it."""
    absolute = max(0, int(config.min_code_frequency))
    fraction = config.min_code_frequency_fraction
    fraction_threshold = (
        _fraction_threshold(float(fraction), n_responses) if fraction is not None else None
    )

    if fraction_threshold is None:
        threshold = absolute
        binding = "absolute"
    elif fraction_threshold > absolute:
        threshold = fraction_threshold
        binding = "fraction"
    elif fraction_threshold < absolute:
        threshold = absolute
        binding = "absolute"
    else:
        threshold = absolute
        binding = "both"

    # A threshold of 0 removes nothing and is recorded as such; a threshold of 1 also
    # removes nothing, because every code in the assignment rows occurs at least once.
    if threshold <= 0:
        binding = "none"

    kept: list[str] = []
    dropped: list[DroppedCode] = []
    for name, count in zip(code_names, counts, strict=True):
        if count >= threshold:
            kept.append(name)
            continue
        if binding == "fraction":
            reason = (
                f"occurs in {count} of {n_responses} responses, below "
                f"{config.min_code_frequency_fraction:.1%} of the sample "
                f"(threshold {threshold})"
            )
        else:
            reason = (
                f"occurs in {count} response(s), below min_code_frequency={threshold}"
            )
        dropped.append(
            DroppedCode(name=name, n_responses=int(count), threshold=threshold, reason=reason)
        )

    return FilterReport(
        n_responses=n_responses,
        min_code_frequency=absolute,
        min_code_frequency_fraction=fraction,
        fraction_threshold=fraction_threshold,
        threshold=threshold,
        binding_rule=binding,
        kept=tuple(kept),
        dropped=tuple(dropped),
    )


# --------------------------------------------------------------------------- #
# The metadata join — here and only here
# --------------------------------------------------------------------------- #


def metadata_crosstab(
    matrix: OccurrenceMatrix,
    labels: Sequence[int] | np.ndarray,
    key: str,
    *,
    missing: str = "(missing)",
) -> dict[int, dict[str, int]]:
    """Cross-tabulate one respondent-metadata field against cluster labels.

    ``labels[i]`` is the cluster of ``matrix.response_ids[i]`` — the shape
    :func:`gaf.analysis.hca.cluster_responses` returns. The result is
    ``{cluster: {value: count}}`` with both levels sorted, so the cluster
    interpretation table is byte-stable.

    This is the analysis tail's *only* contact with respondent metadata. Nothing here
    is ever passed to a model: the join happens after every coding decision has been
    made and recorded, which is what keeps demographic information out of the
    interpretive loop.
    """
    label_list = [int(x) for x in labels]
    if len(label_list) != matrix.n_responses:
        raise ValueError(
            f"labels has {len(label_list)} entries but the matrix has "
            f"{matrix.n_responses} rows"
        )
    table: dict[int, dict[str, int]] = {}
    for rid, cluster in zip(matrix.response_ids, label_list, strict=True):
        raw = matrix.meta.get(rid, {}).get(key)
        value = missing if raw is None else str(raw)
        bucket = table.setdefault(cluster, {})
        bucket[value] = bucket.get(value, 0) + 1
    return {c: dict(sorted(table[c].items())) for c in sorted(table)}


def metadata_keys(matrix: OccurrenceMatrix) -> list[str]:
    """Every metadata field present on any response, sorted."""
    keys: set[str] = set()
    for meta in matrix.meta.values():
        keys.update(meta)
    return sorted(keys)
