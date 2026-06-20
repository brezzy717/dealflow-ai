import numpy as np

from dealflow_scoring import (
    adapt_weights,
    dump_bytes,
    is_drifting,
    load_bytes,
    make_training_data,
    samples_from_outcomes,
    score_lead,
    train_from_samples,
)


def test_adapt_weights_favors_lower_error_and_normalizes() -> None:
    weights = adapt_weights(
        {"xgboost_v1": 1.0, "random_forest_v1": 2.0, "neural_net_v1": 10.0}
    )
    assert abs(sum(weights.values()) - 1.0) < 1e-9
    assert weights["xgboost_v1"] > weights["random_forest_v1"] > weights["neural_net_v1"]


def test_adapt_weights_handles_zero_error() -> None:
    weights = adapt_weights({"a": 0.0, "b": 0.0})
    assert abs(sum(weights.values()) - 1.0) < 1e-9


def test_train_from_samples_learns_and_weights_sum_to_one() -> None:
    X, y = make_training_data(n_samples=400, seed=3)
    samples = list(zip(X, y))
    result = train_from_samples(samples, seed=3)

    assert abs(sum(result.weights.values()) - 1.0) < 1e-9
    assert set(result.per_model_mae) == {
        "xgboost_v1",
        "random_forest_v1",
        "neural_net_v1",
    }
    # A learned model should beat predicting the mean.
    baseline_mae = float(np.abs(np.asarray(y) - np.mean(y)).mean())
    assert result.ensemble_mae < baseline_mae
    assert result.disagreement >= 0.0


def test_drift_detection() -> None:
    assert is_drifting(10.0, 5.0) is True
    assert is_drifting(5.5, 5.0) is False
    assert is_drifting(5.0, None) is False


def test_samples_from_outcomes_skips_incomplete_rows() -> None:
    rows = [
        {"feature_vector": [0.0] * 52, "actual_quality_score": 80.0},
        {"feature_vector": None, "actual_quality_score": 50.0},
        {"actual_quality_score": 50.0},
        {"feature_vector": [1.0] * 52},
    ]
    samples = samples_from_outcomes(rows)
    assert len(samples) == 1
    assert samples[0][1] == 80.0


def test_model_round_trips_through_bytes() -> None:
    X, y = make_training_data(n_samples=120, seed=1)
    model = train_from_samples(list(zip(X, y)), seed=1).model
    restored = load_bytes(dump_bytes(model))
    lead = {"owner_age": 70, "years_in_business": 30, "signals": {"pre_foreclosure": 1.0}}
    assert score_lead(restored, lead).score == score_lead(model, lead).score
