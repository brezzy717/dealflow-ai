from dealflow_backend.services.assignment import (
    BrokerParams,
    Candidate,
    eligible_for_clawback,
    matches,
    select_for_broker,
)


def _candidates(tier: str, n: int, **kw) -> list[Candidate]:
    return [Candidate(lead_id=f"{tier}-{i}", tier=tier, **kw) for i in range(n)]


def test_matches_respects_gating() -> None:
    params = BrokerParams(
        min_years_in_business=10,
        max_employees=100,
        omitted_industries=frozenset({"Dry Cleaning"}),
    )
    assert matches(Candidate("a", "green", years_in_business=12, employee_count=50), params)
    assert not matches(Candidate("b", "green", years_in_business=5), params)
    assert not matches(Candidate("c", "green", years_in_business=12, employee_count=200), params)
    assert not matches(
        Candidate("d", "green", years_in_business=12, industry="Dry Cleaning"), params
    )


def test_full_supply_yields_ten_each() -> None:
    pool = _candidates("green", 15) + _candidates("yellow", 15) + _candidates("red", 15)
    selected = select_for_broker(pool, BrokerParams())
    tiers = [c.tier for c in selected]
    assert tiers.count("green") == 10
    assert tiers.count("yellow") == 10
    assert tiers.count("red") == 10
    assert len(selected) == 30


def test_color_block_fallback_fills_shortfall_from_next_tier() -> None:
    # Only 8 greens -> 2 short -> pulled from yellow (so 12 yellows total).
    pool = _candidates("green", 8) + _candidates("yellow", 15) + _candidates("red", 15)
    selected = select_for_broker(pool, BrokerParams())
    tiers = [c.tier for c in selected]
    assert tiers.count("green") == 8
    assert tiers.count("yellow") == 12
    assert tiers.count("red") == 10
    assert len(selected) == 30


def test_clawback_only_before_contact() -> None:
    assert eligible_for_clawback(broker_active=False, first_contact_made=False)
    assert not eligible_for_clawback(broker_active=False, first_contact_made=True)
    assert not eligible_for_clawback(broker_active=True, first_contact_made=False)
