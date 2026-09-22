"""The deterministic analysis tail and the validation dossier. No models run here.

Reproduces the Chan (2025) method exactly: binary occurrence matrix, low-frequency
filter, Ward's linkage, agglomeration schedule, cluster means. Adds the Alqazlan-style
concurrent validation against the human golden set, the saturation curve that
grounded theory's theoretical sampling requires, the model-free lexical check, pattern
mapping and frequent code combinations, bottom-up affinity themes across families, and
the crosswalk that maps one codebook's organisation onto another's.

Respondent metadata is joined here, and only here — never during coding.

Validation principle: **reliability** — the entire tail is a pure function of the
occurrence matrix, so a reviewer can rerun it and get the same numbers.
"""

from __future__ import annotations

from gaf.analysis.affinity import (
    DEFAULT_ALPHA,
    DEFAULT_SIMILARITY_THRESHOLD,
    AffinityGroup,
    AffinityResult,
    CrossFamilySubcode,
    ExcludedLeaf,
    LeafSimilarityTable,
    build_affinity,
)
from gaf.analysis.agreement import (
    AgreementReport,
    cohens_kappa,
    concurrent_validation,
    descriptions_from_codebook,
    match_codes,
)
from gaf.analysis.crosswalk import (
    Band,
    Crosswalk,
    CrosswalkMatch,
    FamilyRollup,
    LeafMapping,
    build_crosswalk,
)
from gaf.analysis.hca import (
    DegenerateMatrixError,
    SaturationCurve,
    agglomeration_schedule,
    choose_n_clusters,
    cluster_means,
    cluster_responses,
    dendrogram_svg,
    saturation_curve,
    saturation_svg,
    schedule_from_distances,
    ward_linkage,
)
from gaf.analysis.lexical import (
    FEATURE_SPACES,
    MODEL_STEP,
    TARGETS,
    VECTORIZER_STEP,
    LexicalInputError,
    LexicalReport,
    PoissonLassoCV,
    RefusedFitError,
    ScoredResponse,
    build_pipeline,
    jaccard,
    make_vectorizer,
    run_lexical_validation,
    score_distribution,
    scored_table,
)
from gaf.analysis.matrix import (
    OccurrenceMatrix,
    assignments_from_codebook,
    build_matrix,
    matrix_from_codebook,
    metadata_crosstab,
)
from gaf.analysis.patterns import (
    DEFAULT_MIN_SUPPORT,
    MAX_TRIPLE_CANDIDATES,
    TOP_K_PATTERN_MATES,
    Combination,
    CombinationReport,
    CooccurrenceTable,
    NearestMate,
    PatternGroup,
    PatternReport,
    ResponsePattern,
    build_patterns,
    jaccard_matrix,
)

__all__ = [
    "DEFAULT_ALPHA",
    "DEFAULT_MIN_SUPPORT",
    "DEFAULT_SIMILARITY_THRESHOLD",
    "FEATURE_SPACES",
    "MAX_TRIPLE_CANDIDATES",
    "MODEL_STEP",
    "TARGETS",
    "TOP_K_PATTERN_MATES",
    "VECTORIZER_STEP",
    "AffinityGroup",
    "AffinityResult",
    "AgreementReport",
    "Band",
    "Combination",
    "CombinationReport",
    "CooccurrenceTable",
    "CrossFamilySubcode",
    "Crosswalk",
    "CrosswalkMatch",
    "DegenerateMatrixError",
    "ExcludedLeaf",
    "FamilyRollup",
    "LeafMapping",
    "LeafSimilarityTable",
    "LexicalInputError",
    "LexicalReport",
    "NearestMate",
    "OccurrenceMatrix",
    "PatternGroup",
    "PatternReport",
    "PoissonLassoCV",
    "RefusedFitError",
    "ResponsePattern",
    "SaturationCurve",
    "ScoredResponse",
    "agglomeration_schedule",
    "assignments_from_codebook",
    "build_affinity",
    "build_crosswalk",
    "build_matrix",
    "build_patterns",
    "build_pipeline",
    "choose_n_clusters",
    "cluster_means",
    "cluster_responses",
    "cohens_kappa",
    "concurrent_validation",
    "dendrogram_svg",
    "descriptions_from_codebook",
    "jaccard",
    "jaccard_matrix",
    "make_vectorizer",
    "match_codes",
    "matrix_from_codebook",
    "metadata_crosstab",
    "run_lexical_validation",
    "saturation_curve",
    "saturation_svg",
    "schedule_from_distances",
    "score_distribution",
    "scored_table",
    "ward_linkage",
]
