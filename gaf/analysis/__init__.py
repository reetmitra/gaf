"""The deterministic analysis tail and the validation dossier. No models run here.

Reproduces the Chan (2025) method exactly: binary occurrence matrix, low-frequency
filter, Ward's linkage, agglomeration schedule, cluster means. Adds the Alqazlan-style
concurrent validation against the human golden set, the saturation curve that
grounded theory's theoretical sampling requires, and the model-free lexical check.

Respondent metadata is joined here, and only here — never during coding.

Validation principle: **reliability** — the entire tail is a pure function of the
occurrence matrix, so a reviewer can rerun it and get the same numbers.
"""

from __future__ import annotations

from gaf.analysis.agreement import (
    AgreementReport,
    cohens_kappa,
    concurrent_validation,
    descriptions_from_codebook,
    match_codes,
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

__all__ = [
    "FEATURE_SPACES",
    "MODEL_STEP",
    "TARGETS",
    "VECTORIZER_STEP",
    "AgreementReport",
    "DegenerateMatrixError",
    "LexicalInputError",
    "LexicalReport",
    "OccurrenceMatrix",
    "PoissonLassoCV",
    "RefusedFitError",
    "SaturationCurve",
    "ScoredResponse",
    "agglomeration_schedule",
    "assignments_from_codebook",
    "build_matrix",
    "build_pipeline",
    "choose_n_clusters",
    "cluster_means",
    "cluster_responses",
    "cohens_kappa",
    "concurrent_validation",
    "dendrogram_svg",
    "descriptions_from_codebook",
    "jaccard",
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
