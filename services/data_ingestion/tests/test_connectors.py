from dealflow_ingestion.connectors import (
    CONNECTORS,
    DataGovConnector,
    DeweyConnector,
    NasdaqConnector,
    SecEdgarConnector,
    YelpConnector,
)


def test_registry_has_all_sources() -> None:
    assert set(CONNECTORS) == {"yelp", "dewey", "nasdaq", "sec_edgar", "data_gov"}


def test_yelp_maps_decline_to_risk() -> None:
    signals = YelpConnector().to_signals(
        {"rating": 3.0, "rating_history": [4.5, 4.0, 3.2, 3.0], "review_counts": [100, 40]}
    )
    assert signals["yelp_rating_normalized"] == 0.6
    assert signals["yelp_trend_risk"] > 0
    assert signals["yelp_rating_drop"] == 1.0
    assert signals["review_velocity_declining"] > 0


def test_dewey_maps_distress_flags() -> None:
    signals = DeweyConnector().to_signals(
        {
            "as_of_year": 2026,
            "attom": {"preforeclosure": True, "tax_delinquent": True, "assessment_increase_yoy": 0.3},
            "builty": {"last_permit_year": 2014},
            "pdl": {"employee_trend_12mo": -0.25, "recent_exec_departure": True},
        }
    )
    assert signals["pre_foreclosure"] == 1.0
    assert signals["tax_delinquent"] == 1.0
    assert 0 < signals["permit_recency"] <= 1.0
    assert signals["business_decline_score"] == 0.25
    assert signals["owner_distress_score"] >= 0.5


def test_nasdaq_and_sec_and_datagov() -> None:
    assert NasdaqConnector().to_signals({"industry_index_change_pct": -0.2})[
        "business_decline_score"
    ] == 0.2
    sec = SecEdgarConnector().to_signals({"bankruptcy_filed": True, "bankruptcy_age_years": 1})
    assert sec["owner_personal_bankruptcy"] == 1.0
    assert sec["bankruptcy_recency"] > 0
    gov = DataGovConnector().to_signals({"zoning_changes_last_year": 2, "sba_loan_default": True})
    assert gov["recent_zoning_change"] == 1.0
    assert gov["owner_credit_risk"] == 0.7


def test_signals_are_bounded() -> None:
    signals = YelpConnector().to_signals(
        {"rating": 10.0, "rating_history": [5.0, 0.0], "review_counts": [200, 0]}
    )
    assert all(0.0 <= v <= 1.0 for v in signals.values())
