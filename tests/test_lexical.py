"""The model-free lexical validation (brief §13).

The synthetic scored table plants two word sets whose injection rate is monotone in the
score and a third that is independent of it, so "did the check recover the vocabulary
that actually drives the score" is a question with a known answer.

The suite is kept fast by fitting the full six-model report **once** per session with a
small bootstrap (`BOOTSTRAP = 2` rather than the configured default of 50) and by
exercising the expensive Poisson branch as a unit rather than end to end. Bootstrap
count changes stability estimates, not the fits themselves, so nothing asserted here
depends on the reduction.
"""

from __future__ import annotations

import random

import numpy as np
import pytest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LassoCV, LogisticRegressionCV
from sklearn.model_selection import StratifiedKFold, cross_validate

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
    _target_vector,
    build_pipeline,
    jaccard,
    make_vectorizer,
    run_lexical_validation,
    score_distribution,
    scored_table,
)
from gaf.config import LexicalConfig
from gaf.models import Assignment
from tests.fixtures.codebooks import toy_codebook
from tests.fixtures.scored import (
    FILLER,
    HIGH_SIGNAL,
    LOW_SIGNAL,
    SCORE_DISTRIBUTION,
    score_counts,
    synthetic_scored_table,
)

#: Small on purpose — see the module docstring.
BOOTSTRAP = 2
SEED = 1729

PLANTED = set(HIGH_SIGNAL) | set(LOW_SIGNAL)


def table() -> list[ScoredResponse]:
    return scored_table([row.to_dict() for row in synthetic_scored_table()])


def config(**overrides: object) -> LexicalConfig:
    defaults: dict[str, object] = {"bootstrap": BOOTSTRAP}
    defaults.update(overrides)
    return LexicalConfig(**defaults)  # type: ignore[arg-type]


@pytest.fixture(scope="module")
def report() -> LexicalReport:
    """The six-model report, fitted once for the whole module."""
    return run_lexical_validation(
        table(), config=config(), seed=SEED, codebook=toy_codebook(), report=None
    )


# =========================================================================== #
# The pooled table and its score
# =========================================================================== #


def test_the_score_can_come_from_a_column_or_be_derived_from_codings() -> None:
    rows = [
        {"response_id": 203, "text": "one", "score": 4, "group": "india"},
        {"response_id": 207, "text": "two", "score": 0, "group": "singapore"},
    ]
    from_column = scored_table(rows)
    assert [(r.response_id, r.score, r.group) for r in from_column] == [
        (203, 4, "india"),
        (207, 0, "singapore"),
    ]

    assignments = [
        Assignment(203, "a", "positive_impacts-healthcare"),
        Assignment(203, "b", "positive_impacts-healthcare"),  # same code, still one
        Assignment(203, "c", "negative_impacts-misuse"),
        Assignment(207, "d", "positive_impacts-healthcare"),
    ]
    by_count = scored_table(rows, score_source="code_count", assignments=assignments)
    assert [r.score for r in by_count] == [2, 1]

    by_family = scored_table(
        rows, score_source="family_code_count", assignments=assignments, family="negative_impacts"
    )
    assert [r.score for r in by_family] == [1, 0]


def test_a_malformed_pooled_table_is_refused_rather_than_coerced() -> None:
    with pytest.raises(LexicalInputError, match="no 'score' column"):
        scored_table([{"response_id": 1, "text": "t"}])
    with pytest.raises(LexicalInputError, match="not a whole number"):
        scored_table([{"response_id": 1, "text": "t", "score": 1.5}])
    with pytest.raises(LexicalInputError, match="is negative"):
        scored_table([{"response_id": 1, "text": "t", "score": -1}])
    with pytest.raises(LexicalInputError, match="not an integer"):
        scored_table([{"response_id": 1, "text": "t", "score": "high"}])
    with pytest.raises(LexicalInputError, match="unknown score_source"):
        scored_table([{"response_id": 1, "text": "t", "score": 1}], score_source="vibes")
    with pytest.raises(LexicalInputError, match="requires `assignments`"):
        scored_table([{"response_id": 1, "text": "t", "score": 1}], score_source="code_count")
    with pytest.raises(LexicalInputError, match="requires `family`"):
        scored_table(
            [{"response_id": 1, "text": "t", "score": 1}],
            score_source="family_code_count",
            assignments=[],
        )


def test_the_distribution_is_printed_before_anything_is_fitted() -> None:
    printed: list[str] = []
    with pytest.raises(RefusedFitError):
        run_lexical_validation(
            [ScoredResponse(i, "word word", 0 if i < 5 else 3, "g") for i in range(30)],
            config=config(),
            seed=SEED,
            report=printed.append,
        )
    assert printed, "the distribution must be printed before the refusal"
    assert "ge1 (score >= 1)" in printed[0]
    assert "ge3 (score >= 3)" in printed[0]
    assert "score == 2" in printed[0]


def test_a_cut_with_too_small_a_class_is_refused_with_the_counts() -> None:
    rows = [ScoredResponse(i, "alpha beta gamma", 0 if i < 5 else 4, "g") for i in range(60)]
    distribution = score_distribution(rows)
    assert distribution.ge1_negative == 5

    with pytest.raises(RefusedFitError) as caught:
        run_lexical_validation(rows, config=config(), seed=SEED, report=None)
    message = str(caught.value)
    assert "refusing to fit the ge1 cut" in message
    assert "5 negative(s)" in message
    assert "min_class_count is 10" in message


# =========================================================================== #
# The two feature spaces
# =========================================================================== #


def test_binary_presence_shares_the_weighted_vocabulary_and_holds_only_zeros_and_ones() -> None:
    texts = [row.text for row in table()]
    cfg = config()
    weighted = make_vectorizer(cfg, space="weighted").fit(texts)
    binary = make_vectorizer(cfg, space="binary")
    values = binary.fit_transform(texts)

    assert list(weighted.get_feature_names_out()) == list(binary.get_feature_names_out())
    assert set(np.unique(values.toarray())) <= {0.0, 1.0}
    with pytest.raises(LexicalInputError, match="unknown feature space"):
        make_vectorizer(cfg, space="counts")


# =========================================================================== #
# The pipeline, and the leak it exists to prevent
# =========================================================================== #


def test_the_binarised_estimator_is_the_specified_call_verbatim() -> None:
    pipeline = build_pipeline(target="ge1", space="weighted", config=config(), seed=SEED)
    assert [name for name, _ in pipeline.steps] == [VECTORIZER_STEP, MODEL_STEP]

    model = pipeline.named_steps[MODEL_STEP]
    assert isinstance(model, LogisticRegressionCV)
    assert model.penalty == "l1"
    assert model.solver == "liblinear"
    assert model.scoring == "roc_auc"
    assert model.Cs == 10
    assert model.max_iter == 5000
    assert isinstance(model.cv, StratifiedKFold)
    assert model.cv.n_splits == 5
    assert model.cv.shuffle is True
    assert model.cv.random_state == SEED

    assert isinstance(
        build_pipeline(target="continuous", space="weighted", config=config(), seed=SEED)
        .named_steps[MODEL_STEP],
        LassoCV,
    )
    with pytest.raises(LexicalInputError, match="unknown target"):
        build_pipeline(target="ge2", space="weighted", config=config(), seed=SEED)


def test_the_vectoriser_is_fitted_inside_each_fold_not_on_the_whole_corpus() -> None:
    """The single most likely way to get this test wrong is to leak through TF-IDF.

    The proof is structural and behavioural at once: the vectoriser is a *step of the
    pipeline*, so cross-validation clones and refits it per fold, and the document
    frequencies it learns therefore differ from the ones a whole-corpus fit would give.
    """
    rows = table()[:90]
    texts = [r.text for r in rows]
    y = _target_vector(rows, "ge1")
    cfg = config()

    pipeline = build_pipeline(target="ge1", space="weighted", config=cfg, seed=SEED)
    assert isinstance(pipeline.named_steps[VECTORIZER_STEP], TfidfVectorizer), (
        "the vectoriser must live inside the pipeline, never be applied beforehand"
    )

    whole_corpus = make_vectorizer(cfg, space="weighted").fit(texts)
    leaky = dict(
        zip(whole_corpus.get_feature_names_out(), whole_corpus.idf_, strict=True)
    )

    folds = cross_validate(
        pipeline,
        texts,
        y,
        cv=StratifiedKFold(3, shuffle=True, random_state=0),
        scoring="roc_auc",
        return_estimator=True,
    )
    per_fold = [
        dict(
            zip(
                estimator.named_steps[VECTORIZER_STEP].get_feature_names_out(),
                estimator.named_steps[VECTORIZER_STEP].idf_,
                strict=True,
            )
        )
        for estimator in folds["estimator"]
    ]
    assert len(per_fold) == 3
    assert all(fitted != leaky for fitted in per_fold), (
        "every fold's document frequencies must come from its training rows alone"
    )


# =========================================================================== #
# The three targets
# =========================================================================== #


def test_every_target_recovers_the_planted_vocabulary_in_its_top_twenty(
    report: LexicalReport,
) -> None:
    for target in TARGETS:
        for space in FEATURE_SPACES:
            fit = report.fit(f"{target}:{space}")
            words = fit.words()
            recovered = [w for w in words if w in PLANTED]
            assert len(words) == 20
            assert len(recovered) >= 12, f"{fit.key} recovered only {recovered}"
            assert len(set(words[:5]) & PLANTED) >= 4, (
                f"{fit.key} filled its top five with score-independent words: "
                f"{[w for w in words[:5] if w not in PLANTED]}"
            )
        # the weighted space is the primary comparison; its top eight are all planted
        weighted = report.fit(f"{target}:weighted")
        assert not set(weighted.words()[:8]) - PLANTED, (
            f"{target}:weighted top eight: {weighted.words()[:8]}"
        )

    # filler words are score-independent and must not dominate anywhere
    for fit in report.fits:
        assert len([w for w in fit.words() if w in FILLER]) <= 8


def test_score_two_rows_are_negatives_in_ge3_and_no_row_is_dropped(
    report: LexicalReport,
) -> None:
    """The second documented way to get this wrong is to drop the 2s. Count them."""
    rows = table()
    fixture_counts = score_counts(synthetic_scored_table())
    assert fixture_counts["score_2_rows"] == SCORE_DISTRIBUTION[2] == 45

    y = _target_vector(rows, "ge3")
    assert len(y) == len(rows) == 240, "ge3 is fit on every response, not a subset"
    score_two_negatives = sum(
        1 for row, label in zip(rows, y, strict=True) if row.score == 2 and label == 0
    )
    assert score_two_negatives == 45, "every score == 2 row must be present as a negative"
    assert sum(1 for row, label in zip(rows, y, strict=True) if row.score == 2 and label == 1) == 0

    fit = report.fit("ge3:weighted")
    assert fit.n_samples == 240
    assert (fit.positives, fit.negatives) == (95, 145)
    assert fit.negatives == SCORE_DISTRIBUTION[0] + SCORE_DISTRIBUTION[1] + SCORE_DISTRIBUTION[2]

    ge1 = report.fit("ge1:weighted")
    assert (ge1.positives, ge1.negatives) == (180, 60)
    assert report.distribution.score_2_rows == 45


def test_the_diagnostics_and_stability_columns_are_populated(report: LexicalReport) -> None:
    for fit in report.fits:
        assert fit.cv_metric in {"r2", "roc_auc"}
        assert 0.0 < fit.cv_mean <= 1.0
        assert fit.cv_sd >= 0.0
        assert fit.hyperparameter, "the cross-validated penalty must be recorded"
        assert all(0.0 <= f.selection_frequency <= 1.0 for f in fit.top)
        assert all(f.document_frequency >= 2 for f in fit.top), "min_df = 2"
        assert [f.rank for f in fit.top] == list(range(1, 21))
        assert all(f.coefficient > 0 for f in fit.top_positive)
        assert all(f.coefficient < 0 for f in fit.top_negative)
        assert fit.top_positive and fit.top_negative, (
            "'drives a high score' and 'drives any score' are different questions"
        )
    assert report.fit("continuous:weighted").primary is True
    assert report.n_bootstrap == BOOTSTRAP


def test_the_review_sheet_quotes_real_excerpts_and_names_the_codes(
    report: LexicalReport,
) -> None:
    fit = report.fit("ge3:weighted")
    assert len(fit.review) == LexicalConfig().review_top_n == 10
    row = fit.review[0]
    assert 1 <= len(row.excerpts) <= LexicalConfig().excerpts_per_word
    assert len(row.excerpt_response_ids) == len(row.excerpts)
    for response_id, excerpt in zip(row.excerpt_response_ids, row.excerpts, strict=True):
        source = next(r for r in table() if r.response_id == response_id)
        assert row.word.lower() in source.text.lower()
        assert f"**{row.word}" in excerpt.lower() or f"**{row.word.capitalize()}" in excerpt
    assert row.document_frequency >= 2
    # the toy codebook covers responses 3..50, the scored table starts at 1000, so the
    # bridge column is empty here — what matters is only that the column exists
    assert isinstance(row.codes, tuple)


# =========================================================================== #
# Comparison, stability and interpretation
# =========================================================================== #


def test_jaccard_is_the_set_definition() -> None:
    assert jaccard(["a", "b"], ["a", "b"]) == 1.0
    assert jaccard(["a", "b"], ["b", "c"]) == pytest.approx(1 / 3)
    assert jaccard(["a"], ["b"]) == 0.0
    assert jaccard([], []) == 1.0


def test_every_pair_of_the_six_fits_has_an_overlap_with_a_bootstrap_spread(
    report: LexicalReport,
) -> None:
    assert len(report.fits) == 6
    assert len(report.overlaps) == 15  # 6 choose 2
    for cell in report.overlaps:
        assert 0.0 <= cell.jaccard <= 1.0
        assert 0.0 <= cell.bootstrap_mean <= 1.0
        assert cell.bootstrap_sd >= 0.0
        assert cell.n_bootstrap <= BOOTSTRAP
    for name in (
        "continuous <-> ge1",
        "continuous <-> ge3",
        "ge1 <-> ge3",
        "continuous: weighted <-> binary",
        "ge1: weighted <-> binary",
        "ge3: weighted <-> binary",
    ):
        assert 0.0 <= report.headline[name] <= 1.0

    matrix = report.to_markdown()
    for fit in report.fits:
        assert f"`{fit.key}`" in matrix
    assert "Jaccard overlap of top-20 vocabularies" in matrix


def test_low_overlap_is_a_finding_and_never_raises() -> None:
    """No signal in the text at all: the vocabularies must disagree without failing."""
    generator = random.Random(3)
    vocabulary = [f"tok{i}" for i in range(40)]
    rows: list[ScoredResponse] = []
    for index, score in enumerate([0] * 20 + [1] * 20 + [2] * 20 + [4] * 20):
        words = generator.sample(vocabulary, k=14)
        rows.append(ScoredResponse(index, " ".join(words), score, "pooled"))

    result = run_lexical_validation(rows, config=config(bootstrap=1), seed=SEED, report=None)
    assert 0.0 <= result.headline["continuous <-> ge1"] <= 1.0
    assert result.interpretation
    assert "finding" in result.interpretation or "defensible" in result.interpretation
    assert isinstance(result.to_json(), dict)


def test_the_interpretation_is_stated_in_the_output(report: LexicalReport) -> None:
    assert "floor of 0.5" in report.interpretation
    assert report.interpretation in report.to_markdown()
    # whichever branch fires, both measured overlaps are quoted and no branch calls a
    # low overlap a failure
    assert f"{report.headline['continuous <-> ge1']:.2f}" in report.interpretation
    assert f"{report.headline['continuous <-> ge3']:.2f}" in report.interpretation
    assert "the check itself has not gone wrong" in report.interpretation or (
        "not as a failed check" in report.interpretation
        or "defensible" in report.interpretation
    )


def test_the_methods_paragraph_carries_the_numbers(report: LexicalReport) -> None:
    prose = report.methods_paragraph()
    assert "240 responses" in prose
    assert "180 positive and 60 negative" in prose
    assert "45 responses scoring 2 counted as negative" in prose
    assert "rather than dropped" in prose
    assert "LogisticRegressionCV" in prose and "liblinear" in prose
    assert "fitted inside each cross-validation fold" in prose
    assert f"{report.headline['continuous <-> ge1']:.2f}" in prose
    assert f"{BOOTSTRAP} stratified bootstrap resamples" in prose


def test_two_runs_with_the_same_seed_produce_identical_output() -> None:
    rows = table()
    first = run_lexical_validation(rows, config=config(bootstrap=1), seed=SEED, report=None)
    second = run_lexical_validation(rows, config=config(bootstrap=1), seed=SEED, report=None)
    assert first.to_json_str() == second.to_json_str()
    assert first.to_markdown() == second.to_markdown()
    assert first.methods_paragraph() == second.methods_paragraph()


# =========================================================================== #
# The Poisson branch
# =========================================================================== #


def test_the_poisson_branch_is_available_and_recorded() -> None:
    pipeline = build_pipeline(
        target="continuous",
        space="weighted",
        config=config(continuous_model="poisson"),
        seed=SEED,
    )
    assert isinstance(pipeline.named_steps[MODEL_STEP], PoissonLassoCV)


def test_poisson_lasso_recovers_a_sparse_signal_from_counts() -> None:
    """Two informative columns out of twelve; the L1 penalty must find them and zero rest."""
    generator = np.random.default_rng(0)
    features = generator.normal(size=(300, 12))
    rate = np.exp(0.6 * features[:, 0] - 0.6 * features[:, 1])
    counts = generator.poisson(rate).astype(float)

    model = PoissonLassoCV(cv=3, random_state=SEED).fit(features, counts)
    assert model.coef_.shape == (12,)
    assert model.coef_[0] > 0.2
    assert model.coef_[1] < -0.2
    assert np.count_nonzero(model.coef_) <= 6, "the penalty must actually be sparsifying"
    assert np.all(model.predict(features) > 0)

    # deterministic: the same data and seed give the same fit
    again = PoissonLassoCV(cv=3, random_state=SEED).fit(features, counts)
    assert np.array_equal(model.coef_, again.coef_)
    assert model.alpha_ == again.alpha_


def test_a_table_too_small_to_fit_is_refused() -> None:
    with pytest.raises(LexicalInputError, match="nothing can be fit"):
        run_lexical_validation([ScoredResponse(1, "a", 0, "g")], config=config(), report=None)
