from dealflow_ingestion import SyntheticLeadPipeline, generate_leads


def test_generate_is_deterministic_and_complete() -> None:
    a = generate_leads(20, seed=5)
    b = generate_leads(20, seed=5)
    assert a == b
    assert len(a) == 20
    required = {
        "business_name",
        "state",
        "employee_count",
        "revenue_millions",
        "years_in_business",
        "owner_age",
        "dedup_key",
        "signals",
    }
    for lead in a:
        assert required <= set(lead)
        assert lead["state"] in {"AZ", "UT", "TX"}


def test_pipeline_dedups_and_loads() -> None:
    captured: list = []
    pipeline = SyntheticLeadPipeline(count=15, seed=1, loader=lambda rows: captured.extend(rows) or len(rows))
    loaded = pipeline.run()
    assert loaded == len(captured)
    keys = [r["dedup_key"] for r in captured]
    assert len(keys) == len(set(keys))
