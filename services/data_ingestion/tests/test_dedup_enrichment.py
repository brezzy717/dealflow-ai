from dealflow_ingestion.connectors import DeweyConnector, YelpConnector
from dealflow_ingestion.dedup import dedup_key, normalize_name
from dealflow_ingestion.enrichment import enrich_lead, merge_signals


def test_normalize_name_strips_suffixes_and_punctuation() -> None:
    assert normalize_name("Sunrise HVAC, LLC") == "sunrise hvac"
    assert normalize_name("Legacy Auto & Sons Inc.") == "legacy auto"


def test_dedup_key_matches_equivalent_records() -> None:
    a = dedup_key("Summit Machine Co.", "100 Industrial Street", "AZ")
    b = dedup_key("Summit Machine Company", "100 Industrial St", "az")
    assert a == b


def test_merge_signals_keeps_strongest() -> None:
    merged = merge_signals({"tax_delinquent": 1.0, "x": 0.2}, {"x": 0.8, "y": 0.5})
    assert merged == {"tax_delinquent": 1.0, "x": 0.8, "y": 0.5}


def test_enrich_lead_merges_sources_and_records_provenance() -> None:
    lead = {"business_name": "Acme", "signals": {"urgency_score": 0.3}}
    payloads = {
        "yelp": {"rating": 2.0, "rating_history": [4.0, 2.0]},
        "dewey": {"attom": {"preforeclosure": True}},
        "nasdaq": {},  # empty -> skipped
    }
    connectors = {"yelp": YelpConnector(), "dewey": DeweyConnector()}
    enriched, provenance = enrich_lead(lead, payloads, connectors)

    assert enriched["signals"]["pre_foreclosure"] == 1.0
    assert enriched["signals"]["urgency_score"] == 0.3  # base preserved
    assert {p["source"] for p in provenance} == {"yelp", "dewey"}
    assert all("pulled_at" in p for p in provenance)
