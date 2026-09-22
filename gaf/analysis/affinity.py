"""Affinity themes: bottom-up grouping of leaf codes, across families, ignoring the
headings they arrived under.

An affinity diagram groups notes by likeness rather than by the category they were
filed under when written. Here the notes are **leaf codes** — the codebook's most
specific concepts, at the point where they were actually applied to evidence — and the
"category they were filed under" is the family (the first-hyphen segment of the code
name). Clustering works on leaves *across* families rather than within one, because
the interesting finding this module exists to surface is exactly the case where two
leaves filed under different families turn out to belong together: the real human
codebook can carry the same subcode label under two or three different parents (see
:class:`CrossFamilySubcode`), and a family-scoped clustering would never let that
appear at all.

**The similarity.** Two parts, both reported per pair:

* ``cosine`` — cosine similarity of ``code_text(name, description)`` embeddings, the
  same rendering every other stage in this system uses (:func:`gaf.embed.protocol.code_text`);
* ``cooccurrence_jaccard`` — Jaccard index of the two codes' occurrence sets over
  responses, reusing :func:`gaf.analysis.patterns.jaccard_matrix`.

Blended as ``alpha * cosine + (1 - alpha) * cooccurrence_jaccard``. Both ``alpha``
(:data:`DEFAULT_ALPHA`) and the clustering cut (:data:`DEFAULT_SIMILARITY_THRESHOLD`)
are single constants, documented here, and **uncalibrated** — set by inspection, never
checked against a human theming, in exactly the sense `CodingRules.tau_fit` is
provisional (see its docstring in `gaf/config.py`). Grouping is average-linkage
agglomerative clustering (`scipy.cluster.hierarchy.linkage`, `method="average"`), cut
at the configured similarity threshold.

**Naming a theme is a human act.** Every group carries a ``label_suggestion``, and it
is mechanical by construction — the most frequent name tokens among the group's
members — never a proposed theme name. The field ``label_is_mechanical`` is always
``True`` and exists so a consumer of the JSON cannot mistake the suggestion for a
finding.

**The offline caveat (ADR-0019).** When the embedding space is the lexical fallback,
the cosine component measures lexical overlap, not meaning — a stand-in that makes the
method testable offline, not a claim that word overlap is the theme. Markdown output
carries this caveat whenever :attr:`AffinityResult.space_id` names the lexical space.

No respondent text enters or leaves this module: everything here is code names,
family names and response counts.

Validation principles: **interpretive depth** (grouping surfaces the cross-family
cases a family-scoped view would hide) and **transparency** (every blend, threshold
and mechanical label is named as what it is).
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform

from gaf.analysis.agreement import descriptions_from_codebook
from gaf.analysis.matrix import OccurrenceMatrix
from gaf.analysis.patterns import jaccard_matrix
from gaf.embed.matcher import cosine_matrix
from gaf.embed.protocol import Embedder, code_text
from gaf.models import Codebook, family_of, sub_of

__all__ = [
    "DEFAULT_ALPHA",
    "DEFAULT_SIMILARITY_THRESHOLD",
    "EXCLUDED_NOT_A_LEAF",
    "EXCLUDED_NOT_IN_MATRIX",
    "AffinityGroup",
    "AffinityResult",
    "CrossFamilySubcode",
    "ExcludedLeaf",
    "LeafSimilarityTable",
    "build_affinity",
]

#: Weight on the cosine component of the blend; ``1 - ALPHA`` on the co-occurrence
#: Jaccard component. Documented, not calibrated.
DEFAULT_ALPHA = 0.7

#: PROVISIONAL — a similarity cut for average-linkage clustering, not a calibrated
#: threshold. Set by inspection of the blended score's plausible range, exactly as
#: uncalibrated as `CodingRules.tau_fit`; change it through a calibration report, not
#: by hand.
DEFAULT_SIMILARITY_THRESHOLD = 0.5

_TOKEN_SPLIT_RE = re.compile(r"[-_]+")

#: How many of a group's most frequent name tokens make up its label suggestion.
_LABEL_SUGGESTION_TOKENS = 3


# --------------------------------------------------------------------------- #
# Similarity table
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class LeafSimilarityTable:
    """Pairwise similarity between clustered leaves: cosine, co-occurrence, blended.

    All three are ``(n, n)`` arrays over ``names`` in the same order. The diagonal of
    every matrix is 1.0 by convention (a code is identical to itself).
    """

    names: tuple[str, ...]
    cosine: np.ndarray
    cooccurrence_jaccard: np.ndarray
    blended: np.ndarray
    alpha: float

    def to_json(self) -> dict[str, Any]:
        return {
            "names": list(self.names),
            "alpha": self.alpha,
            "cosine": [[float(v) for v in row] for row in self.cosine],
            "cooccurrence_jaccard": [[float(v) for v in row] for row in self.cooccurrence_jaccard],
            "blended": [[float(v) for v in row] for row in self.blended],
        }


# --------------------------------------------------------------------------- #
# Groups
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class AffinityGroup:
    """Two or more leaf codes clustered together, whatever families they came from.

    ``label_suggestion`` is mechanical (the most frequent name tokens among
    ``members``) and ``label_is_mechanical`` is always ``True`` — naming a theme is a
    human act, not something this function does.
    """

    members: tuple[str, ...]
    families: tuple[str, ...]
    cross_family: bool
    total_responses: int
    per_code_frequency: dict[str, int] = field(default_factory=dict)
    label_suggestion: str = ""
    label_is_mechanical: bool = True

    @property
    def size(self) -> int:
        return len(self.members)

    def to_json(self) -> dict[str, Any]:
        return {
            "members": list(self.members),
            "families": list(self.families),
            "cross_family": self.cross_family,
            "total_responses": self.total_responses,
            "per_code_frequency": dict(sorted(self.per_code_frequency.items())),
            "label_suggestion": self.label_suggestion,
            "label_is_mechanical": self.label_is_mechanical,
            "size": self.size,
        }


#: Why a name appears in `AffinityResult.excluded`. Two directions, and both have to
#: be reported: a codebook leaf the matrix does not carry, and a matrix column that is
#: not a leaf of this codebook. The second went unreported entirely (R1 I5), so a
#: frequent column could appear in no group, no singleton and no excluded row while
#: the header said everything was accounted for.
EXCLUDED_NOT_IN_MATRIX = "not present in the occurrence matrix (filtered out, or never assigned)"
EXCLUDED_NOT_A_LEAF = "present in the occurrence matrix but not a leaf of this codebook"


@dataclass(frozen=True, slots=True)
class ExcludedLeaf:
    """A name that could not be clustered, and why. See the two reasons above."""

    name: str
    reason: str

    def to_json(self) -> dict[str, Any]:
        return {"name": self.name, "reason": self.reason}


@dataclass(frozen=True, slots=True)
class CrossFamilySubcode:
    """One sub-code label that occurs, identically, under more than one family.

    This is a structural fact about the codebook itself — computed over every leaf,
    whether or not it survived into the occurrence matrix — not a clustering result.
    It is the case ADR-0036 names as the reason affinity groups across families
    rather than within them: the real human codebook can carry the same subcode label
    under two or three different parents, and family-scoped grouping would hide it.
    """

    sub_label: str
    families: tuple[str, ...]
    codes: tuple[str, ...]

    def to_json(self) -> dict[str, Any]:
        return {
            "sub_label": self.sub_label,
            "families": list(self.families),
            "codes": list(self.codes),
        }


# --------------------------------------------------------------------------- #
# The result
# --------------------------------------------------------------------------- #

#: ADR-0019's caveat, repeated here because affinity's cosine component inherits it.
_OFFLINE_CAVEAT = (
    "Offline similarity describes the fallback lexical embedder, not meaning "
    "(ADR-0019): the cosine component of the blend is lexical overlap here, and a "
    "cluster is a starting point for a human read, not a semantic claim."
)


@dataclass(frozen=True, slots=True)
class AffinityResult:
    """The whole affinity-diagram dossier for one codebook and one occurrence matrix."""

    space_id: str
    alpha: float
    threshold: float
    n_leaves_total: int
    excluded: tuple[ExcludedLeaf, ...]
    similarity: LeafSimilarityTable
    groups: tuple[AffinityGroup, ...]
    singleton_leaves: tuple[str, ...]
    cross_family_subcodes: tuple[CrossFamilySubcode, ...]

    @property
    def n_leaves_clustered(self) -> int:
        return len(self.similarity.names)

    @property
    def n_excluded_matrix_only(self) -> int:
        """Excluded names that are matrix columns rather than codebook leaves."""
        return sum(1 for e in self.excluded if e.reason == EXCLUDED_NOT_A_LEAF)

    @property
    def offline_caveat(self) -> str | None:
        """ADR-0019's caveat, whenever the space in force is the lexical one.

        `gaf.embed.service.derive_space_id` documents an explicit label as the
        supported way to name a space for a calibration run and keeps it as a
        ``"<label>+<derived core>"`` prefix, so testing the *start* of the id
        suppressed the caveat on exactly the run where it matters most (R1 I8). The
        derived core is what says which space this is, so the core is what is read.
        """
        core = self.space_id.rsplit("+", 1)[-1]
        return _OFFLINE_CAVEAT if core.startswith("lexical-") else None

    def to_json(self) -> dict[str, Any]:
        return {
            "space_id": self.space_id,
            "alpha": self.alpha,
            "threshold": self.threshold,
            "n_leaves_total": self.n_leaves_total,
            "n_leaves_clustered": self.n_leaves_clustered,
            "offline_caveat": self.offline_caveat,
            "excluded": [e.to_json() for e in self.excluded],
            "similarity": self.similarity.to_json(),
            "groups": [g.to_json() for g in self.groups],
            "singleton_leaves": list(self.singleton_leaves),
            "cross_family_subcodes": [c.to_json() for c in self.cross_family_subcodes],
        }

    def to_json_str(self) -> str:
        return json.dumps(self.to_json(), sort_keys=True, ensure_ascii=False, indent=2)

    def to_markdown(self, *, top_n: int = 20) -> str:
        lines = [
            "## Affinity themes",
            "",
            f"{self.n_leaves_clustered} of {self.n_leaves_total} codebook leaves "
            f"clustered ({len(self.excluded) - self.n_excluded_matrix_only} excluded — "
            "see below). Blend: "
            f"alpha * cosine(code_text) + (1 - alpha) * Jaccard(co-occurrence), "
            f"alpha = {self.alpha:g}, cut at similarity >= {self.threshold:g} "
            "(average linkage; PROVISIONAL, uncalibrated).",
            "",
            "Naming a theme is a human act. `label_suggestion` below is mechanical — "
            "the most frequent name tokens among a group's members — and is not a "
            "proposed theme name.",
            "",
        ]
        if self.offline_caveat:
            lines.extend([f"> **Offline embedding space.** {self.offline_caveat}", ""])

        lines.extend(["### Groups", ""])
        if not self.groups:
            lines.append("_No group of two or more leaves met the similarity threshold._")
        else:
            lines.append("| size | members | families | cross-family | label suggestion | responses |")
            lines.append("|---:|---|---|:---:|---|---:|")
            for group in self.groups[:top_n]:
                lines.append(
                    f"| {group.size} | {', '.join(group.members)} | "
                    f"{', '.join(group.families)} | {'yes' if group.cross_family else 'no'} "
                    f"| {group.label_suggestion} (mechanical) | {group.total_responses} |"
                )
            if len(self.groups) > top_n:
                lines.append("")
                lines.append(f"_Showing the largest {top_n} of {len(self.groups)} groups._")

        lines.extend(["", "### Cross-family sub-codes", ""])
        if not self.cross_family_subcodes:
            lines.append("_No sub-code label is shared, identically, across more than one family._")
        else:
            lines.append("| sub-code label | families | codes |")
            lines.append("|---|---|---|")
            for row in self.cross_family_subcodes:
                lines.append(
                    f"| {row.sub_label} | {', '.join(row.families)} | {', '.join(row.codes)} |"
                )

        singleton_text = ", ".join(self.singleton_leaves) or "_none_"
        lines.extend(
            [
                "",
                f"### Singletons ({len(self.singleton_leaves)})",
                "",
                singleton_text,
            ]
        )

        lines.extend(["", "### Excluded", ""])
        if self.n_excluded_matrix_only:
            lines.append(
                f"{self.n_excluded_matrix_only} column(s) of the occurrence matrix are "
                "not leaves of this codebook and were not clustered either; they are "
                "listed below with the codebook leaves the matrix does not carry."
            )
            lines.append("")
        if not self.excluded:
            lines.append("_Every codebook leaf was present in the occurrence matrix._")
        else:
            lines.append("| name | reason |")
            lines.append("|---|---|")
            for excluded in self.excluded:
                lines.append(f"| {excluded.name} | {excluded.reason} |")
        return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Construction
# --------------------------------------------------------------------------- #


def _tokenize(name: str) -> set[str]:
    return {token for token in _TOKEN_SPLIT_RE.split(name) if token}


def _label_suggestion(members: tuple[str, ...]) -> str:
    """The most frequent name tokens among ``members``, mechanically, not a theme name."""
    counts: Counter[str] = Counter()
    for member in members:
        counts.update(_tokenize(member))
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    top = [token for token, _ in ranked[:_LABEL_SUGGESTION_TOKENS]]
    return "_".join(top)


def _cross_family_subcodes(codebook: Codebook) -> tuple[CrossFamilySubcode, ...]:
    by_sub: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for code in codebook.leaves():
        sub = sub_of(code.name)
        if sub:
            by_sub[sub].append((family_of(code.name), code.name))

    out: list[CrossFamilySubcode] = []
    for sub_label, entries in by_sub.items():
        families = tuple(sorted({family for family, _ in entries}))
        if len(families) < 2:
            continue
        codes = tuple(sorted({name for _, name in entries}))
        out.append(CrossFamilySubcode(sub_label=sub_label, families=families, codes=codes))
    out.sort(key=lambda row: row.sub_label)
    return tuple(out)


def build_affinity(
    codebook: Codebook,
    matrix: OccurrenceMatrix,
    embedder: Embedder,
    *,
    alpha: float = DEFAULT_ALPHA,
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> AffinityResult:
    """Cluster the codebook's leaf codes by blended cosine + co-occurrence similarity.

    ``matrix`` supplies both the occurrence-frequency and the co-occurrence Jaccard
    component of the blend; whatever low-frequency filter it was built with is
    reflected as codes simply absent from it, which this function reports as
    :class:`ExcludedLeaf` rather than silently dropping. **Both** directions of
    mismatch are reported: a codebook leaf the matrix does not carry, and a matrix
    column that is not a leaf of this codebook (a code that gained children in the
    slow loop, say). ``embedder`` renders every leaf with
    :func:`gaf.embed.protocol.code_text`, using the codebook's own descriptions
    (:func:`gaf.analysis.agreement.descriptions_from_codebook`).

    :class:`CrossFamilySubcode` is computed over **every** codebook leaf regardless of
    matrix presence, because it is a structural fact about the codebook, not a
    clustering result.
    """
    if not (0.0 <= alpha <= 1.0):
        raise ValueError(f"alpha must be in [0, 1], got {alpha}")
    # `threshold` is a similarity, cut at `1 - threshold` in distance space. Outside
    # [0, 1] the cut is vacuous in one direction or the other -- -0.5 merges every
    # leaf into one group, 1.5 makes every leaf a singleton -- and says so nowhere
    # (R1 Minor). `alpha` was range-checked and this was not.
    if not (0.0 <= threshold <= 1.0):
        raise ValueError(f"threshold must be in [0, 1], got {threshold}")

    leaves = codebook.leaves()
    all_names = tuple(sorted(c.name for c in leaves))
    in_matrix = set(matrix.code_names)

    included = tuple(name for name in all_names if name in in_matrix)
    excluded = tuple(
        [
            ExcludedLeaf(name=name, reason=EXCLUDED_NOT_IN_MATRIX)
            for name in all_names
            if name not in in_matrix
        ]
        + [
            ExcludedLeaf(name=name, reason=EXCLUDED_NOT_A_LEAF)
            for name in sorted(in_matrix - set(all_names))
        ]
    )
    cross_family_subcodes = _cross_family_subcodes(codebook)

    if not included:
        empty = np.zeros((0, 0), dtype=np.float64)
        return AffinityResult(
            space_id=embedder.space_id,
            alpha=alpha,
            threshold=threshold,
            n_leaves_total=len(all_names),
            excluded=excluded,
            similarity=LeafSimilarityTable(
                names=(), cosine=empty, cooccurrence_jaccard=empty, blended=empty, alpha=alpha
            ),
            groups=(),
            singleton_leaves=(),
            cross_family_subcodes=cross_family_subcodes,
        )

    descriptions = descriptions_from_codebook(codebook)
    texts = [code_text(name, descriptions.get(name, "")) for name in included]
    vectors = embedder.embed(texts)
    cosine = cosine_matrix(vectors, vectors)

    column_index = {name: i for i, name in enumerate(matrix.code_names)}
    sub_values = matrix.values[:, [column_index[name] for name in included]]
    coj = jaccard_matrix(sub_values)

    blended = alpha * cosine + (1.0 - alpha) * coj
    np.fill_diagonal(blended, 1.0)

    if len(included) == 1:
        return AffinityResult(
            space_id=embedder.space_id,
            alpha=alpha,
            threshold=threshold,
            n_leaves_total=len(all_names),
            excluded=excluded,
            similarity=LeafSimilarityTable(
                names=included, cosine=cosine, cooccurrence_jaccard=coj, blended=blended, alpha=alpha
            ),
            groups=(),
            singleton_leaves=included,
            cross_family_subcodes=cross_family_subcodes,
        )

    distance = np.clip(1.0 - blended, 0.0, None)
    np.fill_diagonal(distance, 0.0)
    condensed = squareform(distance, checks=False)
    tree = linkage(condensed, method="average")
    labels = fcluster(tree, t=1.0 - threshold, criterion="distance")

    by_label: dict[int, list[str]] = defaultdict(list)
    for name, label in zip(included, labels, strict=True):
        by_label[int(label)].append(name)

    groups: list[AffinityGroup] = []
    singleton_leaves: list[str] = []
    for _label, members_list in by_label.items():
        members = tuple(sorted(members_list))
        if len(members) == 1:
            singleton_leaves.append(members[0])
            continue
        families = tuple(sorted({family_of(m) for m in members}))
        touched = np.any(matrix.values[:, [column_index[m] for m in members]], axis=1)
        per_code_frequency = {m: int(matrix.column(m).sum()) for m in members}
        groups.append(
            AffinityGroup(
                members=members,
                families=families,
                cross_family=len(families) >= 2,
                total_responses=int(touched.sum()),
                per_code_frequency=per_code_frequency,
                label_suggestion=_label_suggestion(members),
            )
        )

    groups.sort(key=lambda g: (-g.size, g.members))
    singleton_leaves.sort()

    return AffinityResult(
        space_id=embedder.space_id,
        alpha=alpha,
        threshold=threshold,
        n_leaves_total=len(all_names),
        excluded=excluded,
        similarity=LeafSimilarityTable(
            names=included, cosine=cosine, cooccurrence_jaccard=coj, blended=blended, alpha=alpha
        ),
        groups=tuple(groups),
        singleton_leaves=tuple(singleton_leaves),
        cross_family_subcodes=cross_family_subcodes,
    )
