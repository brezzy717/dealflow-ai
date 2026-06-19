from dealflow_scoring import score_lead, train_demo_model
from dealflow_scoring.ensemble import EnsembleModel, tier_for


def test_tier_bands() -> None:
    assert tier_for(90) == "green"
    assert tier_for(60) == "yellow"
    assert tier_for(30) == "red"
    assert tier_for(10) == "monitor"


def test_unfitted_model_raises() -> None:
    model = EnsembleModel()
    try:
        model.predict_one({})
    except RuntimeError:
        return
    raise AssertionError("expected RuntimeError on unfitted model")


def test_demo_model_scores_within_range_and_is_deterministic() -> None:
    model = train_demo_model(seed=7)

    distressed = {
        "employee_count": 12,
        "revenue_millions": 1.2,
        "years_in_business": 30,
        "owner_age": 70,
        "signals": {
            "pre_foreclosure": 1.0,
            "tax_delinquent": 1.0,
            "succession_risk": 1.0,
            "owner_personal_bankruptcy": 1.0,
            "urgency_score": 1.0,
            "search_intent_score": 1.0,
        },
    }
    healthy = {
        "employee_count": 80,
        "revenue_millions": 20.0,
        "years_in_business": 8,
        "owner_age": 45,
        "signals": {"has_successor": 1.0},
    }

    hot = score_lead(model, distressed)
    cold = score_lead(model, healthy)

    assert 0.0 <= hot.score <= 100.0
    assert hot.tier in {"green", "yellow", "red", "monitor"}
    assert 0.0 <= hot.confidence <= 1.0
    assert set(hot.model_scores) == {"xgboost_v1", "random_forest_v1", "neural_net_v1"}
    assert hot.explanation
    # The distressed, retirement-age owner should outscore the healthy one.
    assert hot.score > cold.score
    # Deterministic with a fixed seed.
    again = score_lead(train_demo_model(seed=7), distressed)
    assert again.score == hot.score
