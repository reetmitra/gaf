"""The model-free lexical validation — L1 vocabulary extraction under three framings.

Designed by a software engineer at the Max Planck Institute, Berlin, and run during the
project. No language model is involved anywhere: this is a deterministic external check
on whether the vocabulary that drives a per-response score depends on how the score is
framed. The specification it implements, verbatim:

    "As a check on whether treating the score as continuous changes the extracted
    vocabulary compared with a simpler binary framing, two binarized cuts of the pooled
    data were also fit, each with an L1-penalized LogisticRegressionCV (liblinear,
    scored by ROC-AUC): ge1 (score >= 1 vs. score = 0, all responses) and ge3
    (score >= 3 vs. score < 3, all responses - score = 2 counts as a negative example
    rather than being dropped). Each binarized model's top-20 words were compared
    against the primary continuous model's top-20 words, and against a plain
    binary-presence feature version, using Jaccard overlap."

    "Then look at the top ten words driving the results and eyeball them."

**What the score is, is the caller's business.** It is read from a named column of the
pooled table (the primary path), or derived as the number of distinct codes on a
response, or as the number of codes from one named top-level family — see
:func:`scored_table`. Nothing here assumes a source.

**Pooled means pooled.** Every group (sample, wave) sits in one table and the group is
reported alongside, so imbalance is visible rather than averaged away. The full score
distribution and both binarised class balances are printed *before* any fit, and a cut
with fewer than ``LexicalConfig.min_class_count`` positives or negatives is **refused**
with a message naming the counts.

**Two traps this module is written to avoid.**

1. *Leakage through the vectoriser.* Fitting TF-IDF on the whole corpus before
   cross-validating leaks the held-out documents' vocabulary and inverse document
   frequencies into training and inflates the AUC. Every reported generalisation score
   here comes from ``cross_val_score`` over a :class:`~sklearn.pipeline.Pipeline` whose
   **first step is the vectoriser**, so scikit-learn clones and refits it inside each
   fold. The final coefficients are read from a full-data fit — no held-out claim is
   made about them, which is why that fit is not leakage.
2. *Dropping the 2s.* ``ge3`` is ``score >= 3`` over **all** responses. A response
   scoring 2 is a negative example. Dropping those rows would quietly change the
   question from "high versus everything else" to "high versus low", and the test suite
   counts the score-2 negatives to prove it did not happen.

**Stability is not optional.** L1 selection over a few hundred documents is unstable,
and a single top-20 list invites over-reading. Every fit is repeated over
``LexicalConfig.bootstrap`` stratified resamples; each word carries the frequency with
which it lands in the top 20, and every Jaccard overlap is reported as mean +/- SD
across resamples rather than as one number. A word in 48 of 50 resamples means
something; a word in 12 of 50 does not.

**Low overlap is a finding, not a failure.** This module raises only on malformed input
or a refused fit. High overlap (>= ``LexicalConfig.jaccard_agreement_floor``) means the
continuous and binarised framings extract the same vocabulary and the simpler binary
presentation is defensible; low overlap is reported as what it is.

ADR-0011 governs the scikit-learn pin. ``LogisticRegressionCV(penalty="l1", ...)``
emits ``FutureWarning``s under scikit-learn 1.9; that is expected and documented, and
the call is not to be "fixed" by changing it.

Validation principle: **reliability** — every fit is seeded, every resample is drawn
from a seeded generator, and two runs at one seed produce identical output.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
import scipy.sparse as sp
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LassoCV, LogisticRegressionCV
from sklearn.model_selection import KFold, StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline

from gaf.config import LexicalConfig
from gaf.models import Assignment, Codebook, family_of

__all__ = [
    "FEATURE_SPACES",
    "MODEL_STEP",
    "TARGETS",
    "VECTORIZER_STEP",
    "FeatureWeight",
    "FitResult",
    "JaccardCell",
    "LexicalError",
    "LexicalInputError",
    "LexicalReport",
    "PoissonLassoCV",
    "RefusedFitError",
    "ReviewRow",
    "ScoreDistribution",
    "ScoredResponse",
    "build_pipeline",
    "jaccard",
    "make_vectorizer",
    "run_lexical_validation",
    "score_distribution",
    "scored_table",
]

#: The three targets, in report order. "continuous" is the primary model.
TARGETS: tuple[str, ...] = ("continuous", "ge1", "ge3")

#: The two feature spaces, built from identical tokenisation and vocabulary.
FEATURE_SPACES: tuple[str, ...] = ("weighted", "binary")

#: Pipeline step names. Named constants because a test asserts on the structure.
VECTORIZER_STEP = "vectorizer"
MODEL_STEP = "model"


class LexicalError(Exception):
    """Base class for the two things this module is allowed to fail on."""


class LexicalInputError(LexicalError):
    """The pooled table is malformed — a missing column, a non-integer or negative score."""


class RefusedFitError(LexicalError):
    """A binarised cut has too few positives or negatives to be fit honestly."""


# --------------------------------------------------------------------------- #
# The pooled table and its score
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class ScoredResponse:
    """One row of the pooled table: a response, its score, and the group it came from."""

    response_id: int
    text: str
    score: int
    group: str = ""

    def to_json(self) -> dict[str, Any]:
        return {
            "response_id": self.response_id,
            "text": self.text,
            "score": self.score,
            "group": self.group,
        }


def scored_table(
    rows: Sequence[Mapping[str, Any]],
    *,
    score_source: str = "column",
    score_column: str = "score",
    id_column: str = "response_id",
    text_column: str = "text",
    group_column: str = "group",
    assignments: Sequence[Assignment] | None = None,
    family: str | None = None,
) -> list[ScoredResponse]:
    """Build the pooled scored table, with the score obtained one of three ways.

    ``score_source``:

    ``"column"``
        Read ``row[score_column]`` — the primary path, for a score computed elsewhere.
    ``"code_count"``
        The number of **distinct codes** applied to that response in ``assignments``.
    ``"family_code_count"``
        The number of distinct codes from one named top-level ``family`` applied to
        that response (family membership by the first-hyphen split, per ADR-0005).

    The score must be a non-negative integer however it is obtained; anything else
    raises :class:`LexicalInputError` rather than being coerced, because a silently
    truncated score would change the ge1/ge3 cuts without leaving a trace.

    Output is sorted by response id, so the table — and therefore every fold split
    drawn from it — is a deterministic function of the input.
    """
    if score_source not in {"column", "code_count", "family_code_count"}:
        raise LexicalInputError(
            f"unknown score_source {score_source!r}; expected 'column', 'code_count' "
            "or 'family_code_count'"
        )
    if score_source in {"code_count", "family_code_count"} and assignments is None:
        raise LexicalInputError(f"score_source={score_source!r} requires `assignments`")
    if score_source == "family_code_count" and not family:
        raise LexicalInputError("score_source='family_code_count' requires `family`")

    derived: dict[int, int] = {}
    if assignments is not None:
        by_response: dict[int, set[str]] = {}
        for assignment in assignments:
            if score_source == "family_code_count" and family_of(assignment.code) != family:
                continue
            by_response.setdefault(assignment.response_id, set()).add(assignment.code)
        derived = {rid: len(codes) for rid, codes in by_response.items()}

    out: list[ScoredResponse] = []
    for index, row in enumerate(rows):
        if id_column not in row:
            raise LexicalInputError(f"row {index} has no {id_column!r} column")
        if text_column not in row:
            raise LexicalInputError(f"row {index} has no {text_column!r} column")
        response_id = int(row[id_column])
        text = str(row[text_column])
        if score_source == "column":
            if score_column not in row:
                raise LexicalInputError(f"row {index} has no {score_column!r} column")
            score = _as_score(row[score_column], index)
        else:
            score = derived.get(response_id, 0)
        out.append(
            ScoredResponse(
                response_id=response_id,
                text=text,
                score=score,
                group=str(row.get(group_column, "") or ""),
            )
        )
    out.sort(key=lambda r: r.response_id)
    return out


def _as_score(value: Any, index: int) -> int:
    if isinstance(value, bool):
        raise LexicalInputError(f"row {index}: score is a bool, not a count")
    if isinstance(value, int):
        score = value
    elif isinstance(value, float):
        if not float(value).is_integer():
            raise LexicalInputError(f"row {index}: score {value!r} is not a whole number")
        score = int(value)
    else:
        try:
            score = int(str(value).strip())
        except ValueError:
            raise LexicalInputError(
                f"row {index}: score {value!r} is not an integer"
            ) from None
    if score < 0:
        raise LexicalInputError(f"row {index}: score {score} is negative")
    return score


@dataclass(frozen=True, slots=True)
class ScoreDistribution:
    """The counts a reader needs before deciding whether either cut is fittable."""

    n: int
    by_score: dict[int, int]
    by_group: dict[str, int]
    ge1_positive: int
    ge1_negative: int
    ge3_positive: int
    ge3_negative: int
    score_2_rows: int

    def to_json(self) -> dict[str, Any]:
        return {
            "n": self.n,
            "by_score": {str(k): v for k, v in sorted(self.by_score.items())},
            "by_group": dict(sorted(self.by_group.items())),
            "ge1": {"positive": self.ge1_positive, "negative": self.ge1_negative},
            "ge3": {"positive": self.ge3_positive, "negative": self.ge3_negative},
            "score_2_rows": self.score_2_rows,
        }

    def to_text(self) -> str:
        """The block printed before any fit is attempted."""
        lines = [
            f"Pooled scored table: {self.n} responses.",
            "  score  n",
        ]
        for score in sorted(self.by_score):
            lines.append(f"  {score:>5}  {self.by_score[score]}")
        lines.append("  groups: " + ", ".join(f"{g}={n}" for g, n in sorted(self.by_group.items())))
        lines.append(
            f"  ge1 (score >= 1): {self.ge1_positive} positive / {self.ge1_negative} negative"
        )
        lines.append(
            f"  ge3 (score >= 3): {self.ge3_positive} positive / {self.ge3_negative} negative"
        )
        lines.append(
            f"  of the ge3 negatives, {self.score_2_rows} are score == 2 "
            "(counted as negatives, never dropped)"
        )
        return "\n".join(lines)


def score_distribution(scored: Sequence[ScoredResponse]) -> ScoreDistribution:
    """Count the score distribution, the group balance and both binarised cuts."""
    by_score: dict[int, int] = {}
    by_group: dict[str, int] = {}
    for row in scored:
        by_score[row.score] = by_score.get(row.score, 0) + 1
        by_group[row.group] = by_group.get(row.group, 0) + 1
    ge1_positive = sum(1 for r in scored if r.score >= 1)
    ge3_positive = sum(1 for r in scored if r.score >= 3)
    return ScoreDistribution(
        n=len(scored),
        by_score=dict(sorted(by_score.items())),
        by_group=dict(sorted(by_group.items())),
        ge1_positive=ge1_positive,
        ge1_negative=len(scored) - ge1_positive,
        ge3_positive=ge3_positive,
        ge3_negative=len(scored) - ge3_positive,
        score_2_rows=by_score.get(2, 0),
    )


def _check_fittable(distribution: ScoreDistribution, config: LexicalConfig) -> None:
    """Refuse a cut that cannot be cross-validated honestly, naming the counts."""
    minimum = config.min_class_count
    for name, positive, negative, rule in (
        ("ge1", distribution.ge1_positive, distribution.ge1_negative, "score >= 1"),
        ("ge3", distribution.ge3_positive, distribution.ge3_negative, "score >= 3"),
    ):
        if positive < minimum or negative < minimum:
            raise RefusedFitError(
                f"refusing to fit the {name} cut ({rule}): {positive} positive(s) and "
                f"{negative} negative(s), but LexicalConfig.min_class_count is "
                f"{minimum}. A cut this unbalanced cannot support a "
                f"{config.cv_folds}-fold stratified cross-validation, and an AUC from "
                "it would not mean anything. Score distribution:\n"
                + distribution.to_text()
            )


# --------------------------------------------------------------------------- #
# Feature spaces
# --------------------------------------------------------------------------- #


def make_vectorizer(config: LexicalConfig, *, space: str) -> TfidfVectorizer:
    """One of the two feature spaces, from identical tokenisation and vocabulary.

    ``"weighted"``
        TF-IDF, word n-grams up to ``LexicalConfig.ngram_max`` (1 by default; 2 is the
        flag), lowercased, English stop words, ``min_df``, ``sublinear_tf``.
    ``"binary"``
        The **same** analyser and the same vocabulary rules, with values in {0, 1}:
        ``binary=True, use_idf=False, norm=None``. Because only the weighting differs,
        the two spaces produce the same ``vocabulary_`` on the same corpus, which is
        what makes their top-20 lists comparable.
    """
    if space not in FEATURE_SPACES:
        raise LexicalInputError(f"unknown feature space {space!r}; expected one of {FEATURE_SPACES}")
    common: dict[str, Any] = {
        "lowercase": True,
        "stop_words": config.stop_words,
        "ngram_range": (1, config.ngram_max),
        "min_df": config.min_df,
        "max_features": config.max_features,
    }
    if space == "weighted":
        return TfidfVectorizer(sublinear_tf=config.sublinear_tf, **common)
    return TfidfVectorizer(binary=True, use_idf=False, norm=None, sublinear_tf=False, **common)


# --------------------------------------------------------------------------- #
# An L1-penalised Poisson regressor with a cross-validated penalty
# --------------------------------------------------------------------------- #


class PoissonLassoCV(RegressorMixin, BaseEstimator):
    """L1-penalised Poisson regression with the penalty chosen by cross-validation.

    Offered because the score is a **count**, so a Poisson likelihood is the family
    that matches the data-generating story, and Lasso's squared-error loss is only an
    approximation to it. scikit-learn's own ``PoissonRegressor`` is L2-only (it exposes
    ``alpha``, no ``l1_ratio``), and this project adds no dependencies, so the L1
    variant is implemented here from the definition:

        minimise  (1/n) * sum_i [ exp(eta_i) - y_i * eta_i ] + alpha * ||beta||_1
        where     eta = X @ beta + intercept

    solved by FISTA — proximal gradient with Nesterov acceleration and a backtracking
    step size — with the intercept left unpenalised. ``alpha`` is chosen from a
    log-spaced path by K-fold cross-validated mean Poisson deviance, warm-started down
    the path so the whole search is one sweep.

    Deterministic: no randomness beyond the seeded fold split, and the linear exponent
    is clipped to +/-30 so an early iterate cannot overflow into a NaN and make the
    result depend on floating-point luck.

    This is the non-default branch. ``LexicalConfig.continuous_model`` is ``"lasso"``
    unless changed, and the report records which family was primary — the original
    engineer's choice of family is an unconfirmed open item.
    """

    def __init__(
        self,
        *,
        alphas: Sequence[float] | None = None,
        n_alphas: int = 20,
        eps: float = 1e-3,
        cv: int = 5,
        max_iter: int = 300,
        tol: float = 1e-5,
        random_state: int | None = None,
    ) -> None:
        self.alphas = alphas
        self.n_alphas = n_alphas
        self.eps = eps
        self.cv = cv
        self.max_iter = max_iter
        self.tol = tol
        self.random_state = random_state

    # -- the objective ---------------------------------------------------- #

    @staticmethod
    def _eta(X: Any, beta: np.ndarray, intercept: float) -> np.ndarray:
        return np.clip(np.asarray(X @ beta).ravel() + intercept, -30.0, 30.0)

    @classmethod
    def _smooth(cls, X: Any, y: np.ndarray, beta: np.ndarray, intercept: float) -> float:
        eta = cls._eta(X, beta, intercept)
        return float(np.mean(np.exp(eta) - y * eta))

    @classmethod
    def _gradient(
        cls, X: Any, y: np.ndarray, beta: np.ndarray, intercept: float
    ) -> tuple[np.ndarray, float]:
        residual = np.exp(cls._eta(X, beta, intercept)) - y
        n = y.shape[0]
        grad_beta = np.asarray(X.T @ residual).ravel() / n
        return grad_beta, float(np.mean(residual))

    @staticmethod
    def _soft_threshold(values: np.ndarray, amount: float) -> np.ndarray:
        return np.sign(values) * np.maximum(np.abs(values) - amount, 0.0)

    def _solve(
        self,
        X: Any,
        y: np.ndarray,
        alpha: float,
        beta0: np.ndarray,
        intercept0: float,
    ) -> tuple[np.ndarray, float]:
        beta = beta0.copy()
        intercept = float(intercept0)
        momentum_beta, momentum_intercept = beta.copy(), intercept
        t_step = 1.0
        theta = 1.0

        for _ in range(self.max_iter):
            grad_beta, grad_intercept = self._gradient(X, y, momentum_beta, momentum_intercept)
            base = self._smooth(X, y, momentum_beta, momentum_intercept)
            candidate_beta = momentum_beta.copy()
            candidate_intercept = momentum_intercept
            for _ in range(40):
                candidate_beta = self._soft_threshold(
                    momentum_beta - t_step * grad_beta, t_step * alpha
                )
                candidate_intercept = momentum_intercept - t_step * grad_intercept
                delta_beta = candidate_beta - momentum_beta
                delta_intercept = candidate_intercept - momentum_intercept
                quadratic = base + float(
                    grad_beta @ delta_beta + grad_intercept * delta_intercept
                ) + (float(delta_beta @ delta_beta) + delta_intercept**2) / (2.0 * t_step)
                if self._smooth(X, y, candidate_beta, candidate_intercept) <= quadratic + 1e-12:
                    break
                t_step *= 0.5
            shift = max(
                float(np.max(np.abs(candidate_beta - beta))) if beta.size else 0.0,
                abs(candidate_intercept - intercept),
            )
            theta_next = (1.0 + math.sqrt(1.0 + 4.0 * theta * theta)) / 2.0
            weight = (theta - 1.0) / theta_next
            momentum_beta = candidate_beta + weight * (candidate_beta - beta)
            momentum_intercept = candidate_intercept + weight * (candidate_intercept - intercept)
            beta, intercept = candidate_beta, float(candidate_intercept)
            theta = theta_next
            if shift < self.tol:
                break
        return beta, intercept

    def _alpha_path(self, X: Any, y: np.ndarray) -> np.ndarray:
        if self.alphas is not None:
            return np.array(sorted((float(a) for a in self.alphas), reverse=True))
        mean = float(np.mean(y)) if y.size else 0.0
        residual = np.full(y.shape, mean, dtype=np.float64) - y
        gradient = np.abs(np.asarray(X.T @ residual).ravel()) / max(1, y.shape[0])
        alpha_max = float(gradient.max()) if gradient.size else 1.0
        alpha_max = alpha_max if alpha_max > 0 else 1.0
        return np.logspace(
            np.log10(alpha_max), np.log10(alpha_max * self.eps), int(self.n_alphas)
        )

    def _path(self, X: Any, y: np.ndarray, alphas: np.ndarray) -> list[tuple[np.ndarray, float]]:
        n_features = X.shape[1]
        beta = np.zeros(n_features, dtype=np.float64)
        intercept = float(np.log(max(float(np.mean(y)), 1e-6)))
        out: list[tuple[np.ndarray, float]] = []
        for alpha in alphas:
            beta, intercept = self._solve(X, y, float(alpha), beta, intercept)
            out.append((beta.copy(), intercept))
        return out

    @staticmethod
    def _deviance(y: np.ndarray, mu: np.ndarray) -> float:
        safe_mu = np.maximum(mu, 1e-12)
        term = np.where(y > 0, y * np.log(np.maximum(y, 1e-12) / safe_mu), 0.0)
        return float(2.0 * np.mean(term - (y - safe_mu)))

    # -- the estimator interface ------------------------------------------ #

    def fit(self, X: Any, y: Any) -> PoissonLassoCV:
        """Fit the path, pick ``alpha`` by cross-validated deviance, refit on all rows."""
        matrix = sp.csr_matrix(X, dtype=np.float64) if sp.issparse(X) else np.asarray(
            X, dtype=np.float64
        )
        target = np.asarray(y, dtype=np.float64).ravel()
        alphas = self._alpha_path(matrix, target)

        folds = KFold(n_splits=self.cv, shuffle=True, random_state=self.random_state)
        deviances = np.zeros(len(alphas), dtype=np.float64)
        for train_index, test_index in folds.split(np.arange(target.shape[0])):
            fitted = self._path(matrix[train_index], target[train_index], alphas)
            for position, (beta, intercept) in enumerate(fitted):
                mu = np.exp(self._eta(matrix[test_index], beta, intercept))
                deviances[position] += self._deviance(target[test_index], mu)
        deviances /= self.cv

        best = int(np.argmin(deviances))
        final = self._path(matrix, target, alphas)
        self.alphas_ = alphas
        self.mean_deviance_path_ = deviances
        self.alpha_ = float(alphas[best])
        self.coef_ = final[best][0]
        self.intercept_ = final[best][1]
        self.n_features_in_ = int(matrix.shape[1])
        return self

    def predict(self, X: Any) -> np.ndarray:
        """Expected count ``exp(X @ coef_ + intercept_)``."""
        matrix = sp.csr_matrix(X, dtype=np.float64) if sp.issparse(X) else np.asarray(
            X, dtype=np.float64
        )
        return np.exp(self._eta(matrix, self.coef_, self.intercept_))


# --------------------------------------------------------------------------- #
# Pipelines
# --------------------------------------------------------------------------- #


def build_pipeline(
    *, target: str, space: str, config: LexicalConfig, seed: int
) -> Pipeline:
    """The vectoriser and the estimator as one :class:`~sklearn.pipeline.Pipeline`.

    The vectoriser is a **step of the pipeline**, never applied beforehand. That is the
    whole point: when this object is handed to ``cross_val_score``, scikit-learn clones
    it per fold and fits the vectoriser on the training rows alone, so the held-out
    documents contribute neither vocabulary nor document frequencies.

    The binarised cuts use the specification's estimator verbatim —
    ``LogisticRegressionCV(penalty="l1", solver="liblinear", scoring="roc_auc",
    cv=StratifiedKFold(5, shuffle=True, random_state=seed), Cs=10, max_iter=5000)`` —
    with ``random_state`` additionally fixed, because liblinear's coordinate descent
    shuffles and an unseeded run would not be reproducible. ADR-0011 pins scikit-learn
    below 1.10 so this call keeps working as written; the ``FutureWarning``s it emits
    under 1.9 are expected.
    """
    if target not in TARGETS:
        raise LexicalInputError(f"unknown target {target!r}; expected one of {TARGETS}")
    vectorizer = make_vectorizer(config, space=space)
    estimator: Any
    if target == "continuous":
        if config.continuous_model == "poisson":
            # `LexicalConfig.max_iter` is LogisticRegressionCV's cap (5000) and means
            # nothing to a proximal-gradient solver; PoissonLassoCV keeps its own,
            # which its convergence tolerance reaches long before.
            estimator = PoissonLassoCV(cv=config.cv_folds, random_state=seed)
        else:
            # The alpha grid is left at scikit-learn's default: the keyword that sizes
            # it was renamed inside the pinned range (`n_alphas` before 1.9, `alphas`
            # after), and naming it here would make the module version-fragile for no
            # gain — the default path is denser than anything this corpus needs.
            estimator = LassoCV(
                cv=KFold(config.cv_folds, shuffle=True, random_state=seed),
                max_iter=config.max_iter,
                random_state=seed,
            )
    else:
        estimator = LogisticRegressionCV(
            penalty="l1",
            solver="liblinear",
            scoring="roc_auc",
            cv=StratifiedKFold(config.cv_folds, shuffle=True, random_state=seed),
            Cs=config.cs,
            max_iter=config.max_iter,
            random_state=seed,
        )
    return Pipeline([(VECTORIZER_STEP, vectorizer), (MODEL_STEP, estimator)])


def _target_vector(scored: Sequence[ScoredResponse], target: str) -> np.ndarray:
    """The response variable for one target.

    ``ge3`` is ``score >= 3`` over **every** row. A response scoring 2 is a negative
    example here, not a dropped row — see the module docstring.
    """
    scores = np.array([r.score for r in scored], dtype=np.float64)
    if target == "continuous":
        return scores
    if target == "ge1":
        return (scores >= 1).astype(np.int64)
    return (scores >= 3).astype(np.int64)


# --------------------------------------------------------------------------- #
# Vocabulary extraction
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class FeatureWeight:
    """One selected word: its signed coefficient, its stability, its document frequency."""

    word: str
    coefficient: float
    rank: int
    selection_frequency: float
    document_frequency: int

    def to_json(self) -> dict[str, Any]:
        return {
            "word": self.word,
            "coefficient": self.coefficient,
            "rank": self.rank,
            "selection_frequency": self.selection_frequency,
            "document_frequency": self.document_frequency,
        }


def _coefficients(pipeline: Pipeline) -> tuple[list[str], np.ndarray, dict[str, float]]:
    """Feature names, signed coefficients, and the fitted hyper-parameter."""
    vectorizer = pipeline.named_steps[VECTORIZER_STEP]
    model = pipeline.named_steps[MODEL_STEP]
    names = [str(n) for n in vectorizer.get_feature_names_out()]
    raw = np.asarray(model.coef_, dtype=np.float64).ravel()
    if isinstance(model, LogisticRegressionCV):
        hyper = {"C": float(np.asarray(model.C_).ravel()[0])}
    else:
        hyper = {"alpha": float(model.alpha_)}
    return names, raw, hyper


def _top_words(names: Sequence[str], coefficients: np.ndarray, k: int) -> list[str]:
    """The ``k`` words with the largest absolute coefficient, ties broken by name.

    Zero coefficients are excluded: L1 sets them to exactly zero, and a word the model
    did not select is not part of the extracted vocabulary however the ranking sorts.
    """
    ranked = sorted(
        ((abs(float(c)), name) for name, c in zip(names, coefficients, strict=True) if c != 0.0),
        key=lambda item: (-item[0], item[1]),
    )
    return [name for _, name in ranked[:k]]


def _signed_top(
    names: Sequence[str], coefficients: np.ndarray, k: int, *, positive: bool
) -> list[tuple[str, float]]:
    pairs = [
        (name, float(c))
        for name, c in zip(names, coefficients, strict=True)
        if (c > 0.0 if positive else c < 0.0)
    ]
    pairs.sort(key=lambda item: (-item[1] if positive else item[1], item[0]))
    return pairs[:k]


def _weights(
    words: Sequence[str],
    coefficients: Mapping[str, float],
    *,
    selection: Mapping[str, int],
    n_bootstrap: int,
    document_frequency: Mapping[str, int],
) -> tuple[FeatureWeight, ...]:
    """Attach the signed coefficient, the stability and the df to a ranked word list."""
    return tuple(
        FeatureWeight(
            word=word,
            coefficient=float(coefficients.get(word, 0.0)),
            rank=index + 1,
            selection_frequency=(
                selection.get(word, 0) / n_bootstrap if n_bootstrap else 0.0
            ),
            document_frequency=document_frequency.get(word, 0),
        )
        for index, word in enumerate(words)
    )


def _jsonable(value: float) -> float | None:
    """``None`` for a non-finite score, so the JSON artefact stays valid JSON.

    A cross-validated score can be undefined — an r2 on a fold whose target has zero
    variance, for instance. ``json.dumps`` would write a bare ``NaN``, which no strict
    JSON reader accepts; ``null`` says "undefined" in a form every reader understands.
    """
    return float(value) if math.isfinite(value) else None


def jaccard(a: Sequence[str], b: Sequence[str]) -> float:
    """``|A n B| / |A u B|``; two empty sets are defined as fully overlapping."""
    left, right = set(a), set(b)
    union = left | right
    if not union:
        return 1.0
    return len(left & right) / len(union)


# --------------------------------------------------------------------------- #
# Fit results
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class ReviewRow:
    """One row of the eyeball artefact: a word, its numbers, and it in context."""

    word: str
    coefficient: float
    selection_frequency: float
    document_frequency: int
    excerpts: tuple[str, ...]
    excerpt_response_ids: tuple[int, ...]
    codes: tuple[str, ...]

    def to_json(self) -> dict[str, Any]:
        return {
            "word": self.word,
            "coefficient": self.coefficient,
            "selection_frequency": self.selection_frequency,
            "document_frequency": self.document_frequency,
            "excerpts": list(self.excerpts),
            "excerpt_response_ids": list(self.excerpt_response_ids),
            "codes": list(self.codes),
        }


@dataclass(frozen=True, slots=True)
class FitResult:
    """One of the six fits: target x feature space."""

    key: str
    target: str
    space: str
    estimator: str
    primary: bool
    n_samples: int
    n_features: int
    positives: int | None
    negatives: int | None
    hyperparameter: dict[str, float]
    cv_metric: str
    cv_mean: float
    cv_sd: float
    top: tuple[FeatureWeight, ...]
    top_positive: tuple[FeatureWeight, ...]
    top_negative: tuple[FeatureWeight, ...]
    review: tuple[ReviewRow, ...]

    def words(self) -> tuple[str, ...]:
        return tuple(f.word for f in self.top)

    def to_json(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "target": self.target,
            "space": self.space,
            "estimator": self.estimator,
            "primary": self.primary,
            "n_samples": self.n_samples,
            "n_features": self.n_features,
            "positives": self.positives,
            "negatives": self.negatives,
            "hyperparameter": self.hyperparameter,
            "cv_metric": self.cv_metric,
            "cv_mean": _jsonable(self.cv_mean),
            "cv_sd": _jsonable(self.cv_sd),
            "top": [f.to_json() for f in self.top],
            "top_positive": [f.to_json() for f in self.top_positive],
            "top_negative": [f.to_json() for f in self.top_negative],
            "review": [r.to_json() for r in self.review],
        }


@dataclass(frozen=True, slots=True)
class JaccardCell:
    """Overlap between two fits' top-k sets: the point estimate and its bootstrap spread."""

    a: str
    b: str
    jaccard: float
    bootstrap_mean: float
    bootstrap_sd: float
    n_bootstrap: int

    def to_json(self) -> dict[str, Any]:
        return {
            "a": self.a,
            "b": self.b,
            "jaccard": self.jaccard,
            "bootstrap_mean": self.bootstrap_mean,
            "bootstrap_sd": self.bootstrap_sd,
            "n_bootstrap": self.n_bootstrap,
        }


@dataclass(frozen=True, slots=True)
class LexicalReport:
    """Everything the lexical check produced, in three renderings."""

    distribution: ScoreDistribution
    config: dict[str, Any]
    seed: int
    fits: tuple[FitResult, ...]
    overlaps: tuple[JaccardCell, ...]
    headline: dict[str, float]
    interpretation: str
    n_bootstrap: int
    primary_model: str

    def fit(self, key: str) -> FitResult:
        for result in self.fits:
            if result.key == key:
                return result
        raise KeyError(f"no fit named {key!r}; have {[f.key for f in self.fits]}")

    def overlap(self, a: str, b: str) -> JaccardCell:
        for cell in self.overlaps:
            if {cell.a, cell.b} == {a, b}:
                return cell
        raise KeyError(f"no overlap recorded for {a!r} and {b!r}")

    # -- the three outputs ------------------------------------------------ #

    def to_json(self) -> dict[str, Any]:
        return {
            "seed": self.seed,
            "primary_model": self.primary_model,
            "n_bootstrap": self.n_bootstrap,
            "config": self.config,
            "distribution": self.distribution.to_json(),
            "fits": [f.to_json() for f in self.fits],
            "overlaps": [c.to_json() for c in self.overlaps],
            "headline": self.headline,
            "interpretation": self.interpretation,
        }

    def to_json_str(self) -> str:
        return json.dumps(self.to_json(), sort_keys=True, ensure_ascii=False, indent=2)

    def to_markdown(self) -> str:
        lines = [
            "# Lexical validation — continuous vs binarised targets",
            "",
            "```",
            self.distribution.to_text(),
            "```",
            "",
            f"Primary continuous model: **{self.primary_model}**. Seed {self.seed}; "
            f"{self.n_bootstrap} bootstrap resample(s).",
            "",
            "## Model diagnostics",
            "",
            "| fit | estimator | features | penalty | CV metric | mean | SD |",
            "|---|---|---:|---|---|---:|---:|",
        ]
        for result in self.fits:
            penalty = ", ".join(f"{k}={v:.4g}" for k, v in sorted(result.hyperparameter.items()))
            lines.append(
                f"| `{result.key}` | {result.estimator} | {result.n_features} | {penalty} "
                f"| {result.cv_metric} | {result.cv_mean:.3f} | {result.cv_sd:.3f} |"
            )
        lines.extend(
            [
                "",
                "Every CV score above comes from cross-validating the whole pipeline, so "
                "the vectoriser is refitted inside each fold and the held-out documents "
                "contribute no vocabulary and no document frequencies.",
                "",
                "## Jaccard overlap of top-20 vocabularies",
                "",
                "Point estimate from the full-data fits; bootstrap mean +/- SD "
                f"across {self.n_bootstrap} resample(s) in brackets.",
                "",
            ]
        )
        lines.extend(self._jaccard_matrix())
        lines.extend(["", "### Headline overlaps", "", "| comparison | Jaccard |", "|---|---:|"])
        for name, value in self.headline.items():
            lines.append(f"| {name} | {value:.3f} |")
        lines.extend(["", "### Interpretation", "", self.interpretation, ""])
        lines.append("## Eyeball sheets — the top ten words of each fit")
        for result in self.fits:
            lines.extend(
                [
                    "",
                    f"### `{result.key}`",
                    "",
                    "| word | coefficient | selected | df | codes on the quoted responses |",
                    "|---|---:|---:|---:|---|",
                ]
            )
            for row in result.review:
                codes = ", ".join(f"`{c}`" for c in row.codes) if row.codes else "—"
                lines.append(
                    f"| **{row.word}** | {row.coefficient:+.4f} | "
                    f"{row.selection_frequency:.0%} | {row.document_frequency} | {codes} |"
                )
            for row in result.review:
                if not row.excerpts:
                    continue
                lines.append("")
                lines.append(f"- **{row.word}**")
                for response_id, excerpt in zip(
                    row.excerpt_response_ids, row.excerpts, strict=True
                ):
                    lines.append(f"  - _response {response_id}_: {excerpt}")
        return "\n".join(lines)

    def _jaccard_matrix(self) -> list[str]:
        keys = [f.key for f in self.fits]
        header = "| | " + " | ".join(f"`{k}`" for k in keys) + " |"
        rule = "|---|" + "---:|" * len(keys)
        lines = [header, rule]
        for row_key in keys:
            cells: list[str] = []
            for column_key in keys:
                if row_key == column_key:
                    cells.append("—")
                    continue
                cell = self.overlap(row_key, column_key)
                cells.append(
                    f"{cell.jaccard:.2f} ({cell.bootstrap_mean:.2f}+/-{cell.bootstrap_sd:.2f})"
                )
            lines.append(f"| `{row_key}` | " + " | ".join(cells) + " |")
        return lines

    def methods_paragraph(self) -> str:
        """A paragraph of methods prose with the numbers filled in, ready to paste."""
        distribution = self.distribution
        continuous_ge1 = self.headline["continuous <-> ge1"]
        continuous_ge3 = self.headline["continuous <-> ge3"]
        ge1_ge3 = self.headline["ge1 <-> ge3"]
        weighted_binary = [
            v for k, v in self.headline.items() if k.endswith("weighted <-> binary")
        ]
        mean_wb = sum(weighted_binary) / len(weighted_binary) if weighted_binary else 0.0
        primary = self.fit("continuous:weighted")
        ge1 = self.fit("ge1:weighted")
        ge3 = self.fit("ge3:weighted")
        groups = ", ".join(f"{g} n={n}" for g, n in sorted(distribution.by_group.items()))
        return (
            f"As a check on whether treating the score as continuous changes the "
            f"extracted vocabulary compared with a simpler binary framing, the pooled "
            f"data ({distribution.n} responses; {groups}) were also fit under two "
            f"binarised cuts. The ge1 cut (score >= 1 vs. score = 0, all responses) "
            f"gave {distribution.ge1_positive} positive and {distribution.ge1_negative} "
            f"negative cases; the ge3 cut (score >= 3 vs. score < 3, all responses, with "
            f"the {distribution.score_2_rows} responses scoring 2 counted as negative "
            f"rather than dropped) gave {distribution.ge3_positive} positive and "
            f"{distribution.ge3_negative} negative cases. Each cut was fit with an "
            f"L1-penalised LogisticRegressionCV (liblinear, scored by ROC-AUC, "
            f"{self.config['cv_folds']}-fold stratified, {self.config['cs']} values of C), "
            f"and the continuous model with {primary.estimator}; in every case the "
            f"TF-IDF vectoriser was fitted inside each cross-validation fold via a "
            f"pipeline, so no held-out document contributed vocabulary or document "
            f"frequencies. Cross-validated performance was "
            f"{primary.cv_metric} = {primary.cv_mean:.3f} (SD {primary.cv_sd:.3f}) for the "
            f"continuous model, AUC = {ge1.cv_mean:.3f} (SD {ge1.cv_sd:.3f}) for ge1 and "
            f"AUC = {ge3.cv_mean:.3f} (SD {ge3.cv_sd:.3f}) for ge3. Comparing the top-"
            f"{self.config['top_k_features']} words by absolute coefficient, the Jaccard "
            f"overlap between the continuous model and ge1 was {continuous_ge1:.2f}, "
            f"between the continuous model and ge3 {continuous_ge3:.2f}, and between the "
            f"two binarised cuts {ge1_ge3:.2f}; the mean overlap between the TF-IDF and "
            f"binary-presence feature versions of the same target was {mean_wb:.2f}. "
            f"Because L1 selection is unstable at this sample size, every fit was "
            f"repeated over {self.n_bootstrap} stratified bootstrap resamples and each "
            f"word carries the frequency with which it re-entered the top "
            f"{self.config['top_k_features']}. {self.interpretation}"
        )


# --------------------------------------------------------------------------- #
# Excerpts for the eyeball step
# --------------------------------------------------------------------------- #


def _excerpt(text: str, word: str, width: int = 70) -> str | None:
    """The word in context, marked, with a window of roughly ``width`` characters."""
    pattern = re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE)
    match = pattern.search(text)
    if match is None:
        return None
    start = max(0, match.start() - width)
    end = min(len(text), match.end() + width)
    if start > 0:
        space = text.find(" ", start)
        start = space + 1 if 0 <= space < match.start() else start
    if end < len(text):
        space = text.rfind(" ", match.end(), end)
        end = space if space > match.end() else end
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(text) else ""
    return (
        prefix
        + text[start : match.start()]
        + f"**{text[match.start() : match.end()]}**"
        + text[match.end() : end]
        + suffix
    )


def _codes_by_response(codebook: Codebook | None) -> dict[int, tuple[str, ...]]:
    """Response id -> the pipeline codes attached to it, from verified evidence."""
    if codebook is None:
        return {}
    out: dict[int, set[str]] = {}
    for code in codebook.sorted_codes():
        for response_id in code.response_ids():
            out.setdefault(response_id, set()).add(code.name)
    return {rid: tuple(sorted(names)) for rid, names in out.items()}


def _review_rows(
    weights: Sequence[FeatureWeight],
    scored: Sequence[ScoredResponse],
    codes_by_response: Mapping[int, tuple[str, ...]],
    *,
    limit: int,
    excerpts_per_word: int,
) -> tuple[ReviewRow, ...]:
    """The eyeball artefact: each word with real excerpts and the codes on them.

    The codes column is the bridge back to the qualitative work — it shows at a glance
    whether the codebook covers the lexical signal or misses it. Excerpts are taken
    from the lowest response ids that contain the word, so the sheet is reproducible.
    """
    rows: list[ReviewRow] = []
    for weight in weights[:limit]:
        excerpts: list[str] = []
        ids: list[int] = []
        for response in scored:
            if len(excerpts) >= excerpts_per_word:
                break
            snippet = _excerpt(response.text, weight.word)
            if snippet is not None:
                excerpts.append(snippet)
                ids.append(response.response_id)
        attached = sorted({c for rid in ids for c in codes_by_response.get(rid, ())})
        rows.append(
            ReviewRow(
                word=weight.word,
                coefficient=weight.coefficient,
                selection_frequency=weight.selection_frequency,
                document_frequency=weight.document_frequency,
                excerpts=tuple(excerpts),
                excerpt_response_ids=tuple(ids),
                codes=tuple(attached),
            )
        )
    return tuple(rows)


# --------------------------------------------------------------------------- #
# The bootstrap
# --------------------------------------------------------------------------- #


def _bootstrap_indices(
    scores: np.ndarray, n_bootstrap: int, seed: int
) -> list[np.ndarray]:
    """Resample indices, stratified by score value, shared across all six fits.

    Stratifying by the raw score (rather than by either binarised cut) keeps every
    resample fittable for *both* cuts at once and keeps the six fits comparable: they
    all see the same rows, so a difference in their top-20 lists is a difference
    between the framings and not between the samples they happened to draw.
    """
    generator = np.random.default_rng(seed)
    strata = [np.flatnonzero(scores == value) for value in np.unique(scores)]
    out: list[np.ndarray] = []
    for _ in range(max(0, n_bootstrap)):
        picks = [generator.choice(idx, size=idx.shape[0], replace=True) for idx in strata]
        out.append(np.sort(np.concatenate(picks)) if picks else np.zeros(0, dtype=np.int64))
    return out


def _document_frequency(texts: Sequence[str], config: LexicalConfig) -> dict[str, int]:
    """Document frequency of every vocabulary term, from a full-data binary fit.

    Both feature spaces share one vocabulary by construction, so one count serves both.
    """
    vectorizer = make_vectorizer(config, space="binary")
    matrix = vectorizer.fit_transform(texts)
    names = [str(n) for n in vectorizer.get_feature_names_out()]
    counts = np.asarray((matrix > 0).sum(axis=0)).ravel()
    return {name: int(counts[i]) for i, name in enumerate(names)}


# --------------------------------------------------------------------------- #
# The run
# --------------------------------------------------------------------------- #


def run_lexical_validation(
    scored: Sequence[ScoredResponse],
    *,
    config: LexicalConfig | None = None,
    seed: int = 1729,
    codebook: Codebook | None = None,
    report: Callable[[str], None] | None = print,
) -> LexicalReport:
    """Fit all six models, compare their vocabularies, and build the review artefacts.

    Raises :class:`LexicalInputError` on a malformed table and :class:`RefusedFitError`
    when a binarised cut is too unbalanced to fit. It never raises on low Jaccard
    overlap — that is a finding about the data, reported in ``interpretation``.

    ``report`` receives the score distribution before any fitting happens; it defaults
    to :func:`print` because the specification asks for the distribution to be printed,
    and can be set to ``None`` to silence it or to a collector in a test.
    """
    cfg = config or LexicalConfig()
    if len(scored) < 2:
        raise LexicalInputError(
            f"the pooled table has {len(scored)} row(s); nothing can be fit"
        )

    distribution = score_distribution(scored)
    if report is not None:
        report(distribution.to_text())
    _check_fittable(distribution, cfg)

    texts = [r.text for r in scored]
    scores = np.array([r.score for r in scored], dtype=np.int64)
    document_frequency = _document_frequency(texts, cfg)
    codes_by_response = _codes_by_response(codebook)

    # -- the six full-data fits ------------------------------------------- #
    full_words: dict[str, list[str]] = {}
    raw_fits: dict[str, tuple[Pipeline, list[str], np.ndarray, dict[str, float]]] = {}
    for target in TARGETS:
        y = _target_vector(scored, target)
        for space in FEATURE_SPACES:
            key = f"{target}:{space}"
            pipeline = build_pipeline(target=target, space=space, config=cfg, seed=seed)
            pipeline.fit(texts, y)
            names, coefficients, hyper = _coefficients(pipeline)
            raw_fits[key] = (pipeline, names, coefficients, hyper)
            full_words[key] = _top_words(names, coefficients, cfg.top_k_features)

    # -- stability -------------------------------------------------------- #
    resamples = _bootstrap_indices(scores, cfg.bootstrap, seed)
    selection: dict[str, dict[str, int]] = {key: {} for key in raw_fits}
    bootstrap_words: dict[str, list[list[str]]] = {key: [] for key in raw_fits}
    for indices in resamples:
        subset_texts = [texts[i] for i in indices]
        for target in TARGETS:
            y_full = _target_vector(scored, target)
            y = y_full[indices]
            for space in FEATURE_SPACES:
                key = f"{target}:{space}"
                pipeline = build_pipeline(target=target, space=space, config=cfg, seed=seed)
                try:
                    pipeline.fit(subset_texts, y)
                except ValueError:
                    # A resample can leave a fold without both classes, or leave no
                    # term above min_df. That resample contributes nothing rather than
                    # failing the run; the count of usable resamples is reported.
                    bootstrap_words[key].append([])
                    continue
                names, coefficients, _ = _coefficients(pipeline)
                words = _top_words(names, coefficients, cfg.top_k_features)
                bootstrap_words[key].append(words)
                for word in words:
                    selection[key][word] = selection[key].get(word, 0) + 1

    n_bootstrap = len(resamples)

    # -- assemble the fits ------------------------------------------------ #
    fits: list[FitResult] = []
    for target in TARGETS:
        y = _target_vector(scored, target)
        metric = "r2" if target == "continuous" else "roc_auc"
        for space in FEATURE_SPACES:
            key = f"{target}:{space}"
            pipeline, names, coefficients, hyper = raw_fits[key]
            # The honest generalisation estimate: the pipeline is cross-validated as a
            # whole, on a fold split seeded differently from the estimator's own inner
            # split so the penalty selection is not evaluated on the folds that chose it.
            splitter: Any = (
                KFold(cfg.cv_folds, shuffle=True, random_state=seed + 1)
                if target == "continuous"
                else StratifiedKFold(cfg.cv_folds, shuffle=True, random_state=seed + 1)
            )
            outer = build_pipeline(target=target, space=space, config=cfg, seed=seed)
            fold_scores = cross_val_score(outer, texts, y, cv=splitter, scoring=metric)

            coefficient_of = {
                name: float(value)
                for name, value in zip(names, coefficients, strict=True)
            }
            top = _weights(
                full_words[key],
                coefficient_of,
                selection=selection[key],
                n_bootstrap=n_bootstrap,
                document_frequency=document_frequency,
            )
            positive = _weights(
                [
                    w
                    for w, _ in _signed_top(
                        names, coefficients, cfg.top_k_features, positive=True
                    )
                ],
                coefficient_of,
                selection=selection[key],
                n_bootstrap=n_bootstrap,
                document_frequency=document_frequency,
            )
            negative = _weights(
                [
                    w
                    for w, _ in _signed_top(
                        names, coefficients, cfg.top_k_features, positive=False
                    )
                ],
                coefficient_of,
                selection=selection[key],
                n_bootstrap=n_bootstrap,
                document_frequency=document_frequency,
            )
            fits.append(
                FitResult(
                    key=key,
                    target=target,
                    space=space,
                    estimator=type(pipeline.named_steps[MODEL_STEP]).__name__,
                    primary=(key == "continuous:weighted"),
                    n_samples=len(scored),
                    n_features=len(names),
                    positives=None if target == "continuous" else int(np.sum(y)),
                    negatives=None if target == "continuous" else int(len(y) - np.sum(y)),
                    hyperparameter=hyper,
                    cv_metric=metric,
                    cv_mean=float(np.mean(fold_scores)),
                    cv_sd=float(np.std(fold_scores, ddof=1)) if len(fold_scores) > 1 else 0.0,
                    top=top,
                    top_positive=positive,
                    top_negative=negative,
                    review=_review_rows(
                        top,
                        scored,
                        codes_by_response,
                        limit=cfg.review_top_n,
                        excerpts_per_word=cfg.excerpts_per_word,
                    ),
                )
            )

    # -- overlaps --------------------------------------------------------- #
    keys = [f.key for f in fits]
    overlaps: list[JaccardCell] = []
    for i, a in enumerate(keys):
        for b in keys[i + 1 :]:
            samples = [
                jaccard(x, y_words)
                for x, y_words in zip(bootstrap_words[a], bootstrap_words[b], strict=True)
                if x or y_words
            ]
            overlaps.append(
                JaccardCell(
                    a=a,
                    b=b,
                    jaccard=jaccard(full_words[a], full_words[b]),
                    bootstrap_mean=float(np.mean(samples)) if samples else 0.0,
                    bootstrap_sd=float(np.std(samples, ddof=1)) if len(samples) > 1 else 0.0,
                    n_bootstrap=len(samples),
                )
            )

    def overlap_value(a: str, b: str) -> float:
        for cell in overlaps:
            if {cell.a, cell.b} == {a, b}:
                return cell.jaccard
        return 0.0

    headline = {
        "continuous <-> ge1": overlap_value("continuous:weighted", "ge1:weighted"),
        "continuous <-> ge3": overlap_value("continuous:weighted", "ge3:weighted"),
        "ge1 <-> ge3": overlap_value("ge1:weighted", "ge3:weighted"),
    }
    for target in TARGETS:
        headline[f"{target}: weighted <-> binary"] = overlap_value(
            f"{target}:weighted", f"{target}:binary"
        )

    primary_model = (
        "PoissonLassoCV (L1-penalised Poisson)"
        if cfg.continuous_model == "poisson"
        else "LassoCV (L1, squared error)"
    )
    return LexicalReport(
        distribution=distribution,
        config=cfg.to_json(),
        seed=seed,
        fits=tuple(fits),
        overlaps=tuple(overlaps),
        headline=headline,
        interpretation=_interpret(headline, cfg),
        n_bootstrap=n_bootstrap,
        primary_model=primary_model,
    )


def _interpret(headline: Mapping[str, float], config: LexicalConfig) -> str:
    """State what the overlaps mean. Low overlap is a finding, never a failure."""
    floor = config.jaccard_agreement_floor
    continuous_ge1 = headline["continuous <-> ge1"]
    continuous_ge3 = headline["continuous <-> ge3"]
    both = min(continuous_ge1, continuous_ge3)
    if both >= floor:
        verdict = (
            f"Both continuous-to-binarised overlaps are at or above the agreement floor "
            f"of {floor:g} (ge1 {continuous_ge1:.2f}, ge3 {continuous_ge3:.2f}), so "
            "treating the score as continuous does not change the extracted vocabulary "
            "and the simpler binary presentation is defensible."
        )
    elif max(continuous_ge1, continuous_ge3) >= floor:
        verdict = (
            f"One of the two binarised cuts agrees with the continuous model at or above "
            f"the floor of {floor:g} and the other does not (ge1 {continuous_ge1:.2f}, "
            f"ge3 {continuous_ge3:.2f}). The choice of cut is doing some work: report the "
            "continuous model as primary and the disagreeing cut as a finding about "
            "where the threshold falls, not as a failed check."
        )
    else:
        verdict = (
            f"Both continuous-to-binarised overlaps fall below the agreement floor of "
            f"{floor:g} (ge1 {continuous_ge1:.2f}, ge3 {continuous_ge3:.2f}). The choice of cut "
            "does change the extracted vocabulary, so the binary presentation is not a "
            "harmless simplification here. This is a finding to report, not a failed "
            "test — the check itself has not gone wrong."
        )
    spaces = [v for k, v in headline.items() if k.endswith("weighted <-> binary")]
    if spaces and min(spaces) >= floor:
        verdict += (
            " TF-IDF weighting and plain binary presence select substantially the same "
            "words within each target, so the result is not an artefact of the weighting."
        )
    elif spaces:
        verdict += (
            " The TF-IDF and binary-presence feature versions of at least one target "
            f"disagree below the floor (minimum {min(spaces):.2f}), so part of the "
            "signal is carried by term weighting rather than by term presence."
        )
    return verdict
