from dealflow_scoring.features import FEATURE_KEYS, extract_features, to_vector


def test_feature_catalog_has_52_unique_keys() -> None:
    assert len(FEATURE_KEYS) == 52
    assert len(set(FEATURE_KEYS)) == 52


def test_extract_features_is_complete_and_ordered() -> None:
    lead = {
        "employee_count": 40,
        "revenue_millions": 5.0,
        "years_in_business": 30,
        "owner_age": 68,
        "signals": {"pre_foreclosure": 1.0, "tax_delinquent": 1.0},
    }
    features = extract_features(lead)
    assert set(features) == set(FEATURE_KEYS)
    # Retirement-age owner normalizes high; years cap at 25.
    assert features["owner_age_normalized"] > 0.5
    assert features["years_in_business"] == 1.0
    assert features["pre_foreclosure"] == 1.0
    vector = to_vector(features)
    assert len(vector) == 52


def test_missing_fields_default_to_zero() -> None:
    features = extract_features({})
    assert all(value == 0.0 for value in features.values())
