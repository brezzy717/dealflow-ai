"""Lead assignment engine (pure logic).

Implements the spec's slow-drip selection (§5): per-broker quotas (default 10
green / 10 yellow / 10 red), parameter gating, and color-block fallback where a
tier shortfall is filled from the next tier down. Kept free of I/O so it is fully
unit-testable; the DB-backed application lives in ``services/pipeline.py``.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

# Tier order for fallback: a shortfall rolls down to the next tier.
TIER_ORDER: tuple[str, ...] = ("green", "yellow", "red", "monitor")
DEFAULT_PER_TIER = 10
DROP_TIERS: tuple[str, ...] = ("green", "yellow", "red")


@dataclass(frozen=True)
class Candidate:
    lead_id: str
    tier: str
    industry: str | None = None
    employee_count: int | None = None
    revenue_millions: float | None = None
    years_in_business: int | None = None
    location: str | None = None


@dataclass(frozen=True)
class BrokerParams:
    min_years_in_business: int | None = None
    min_employees: int | None = None
    max_employees: int | None = None
    min_revenue_millions: float | None = None
    max_revenue_millions: float | None = None
    omitted_industries: frozenset[str] = field(default_factory=frozenset)
    omitted_locations: frozenset[str] = field(default_factory=frozenset)


def matches(candidate: Candidate, params: BrokerParams) -> bool:
    """True if a candidate satisfies the broker's gating parameters."""
    if params.min_years_in_business is not None and (
        candidate.years_in_business is None
        or candidate.years_in_business < params.min_years_in_business
    ):
        return False
    if params.min_employees is not None and (
        candidate.employee_count is None
        or candidate.employee_count < params.min_employees
    ):
        return False
    if params.max_employees is not None and (
        candidate.employee_count is not None
        and candidate.employee_count > params.max_employees
    ):
        return False
    if params.min_revenue_millions is not None and (
        candidate.revenue_millions is None
        or candidate.revenue_millions < params.min_revenue_millions
    ):
        return False
    if params.max_revenue_millions is not None and (
        candidate.revenue_millions is not None
        and candidate.revenue_millions > params.max_revenue_millions
    ):
        return False
    if candidate.industry and candidate.industry in params.omitted_industries:
        return False
    if candidate.location and candidate.location in params.omitted_locations:
        return False
    return True


def select_for_broker(
    candidates: Sequence[Candidate],
    params: BrokerParams,
    *,
    per_tier: int = DEFAULT_PER_TIER,
) -> list[Candidate]:
    """Select one weekly drop for a broker, applying gating + color fallback."""
    eligible = [c for c in candidates if matches(c, params)]
    pools: dict[str, list[Candidate]] = {tier: [] for tier in TIER_ORDER}
    for candidate in eligible:
        pools.get(candidate.tier, pools["monitor"]).append(candidate)

    selected: list[Candidate] = []
    carry = 0
    # Walk green -> yellow -> red, rolling any shortfall down into the next tier.
    for index, tier in enumerate(DROP_TIERS):
        quota = per_tier + carry
        take = pools[tier][:quota]
        selected.extend(take)
        pools[tier] = pools[tier][len(take):]
        carry = quota - len(take)

    # Any remaining shortfall after red draws from the monitor pool.
    if carry:
        selected.extend(pools["monitor"][:carry])

    return selected


def eligible_for_clawback(*, broker_active: bool, first_contact_made: bool) -> bool:
    """A lead is clawed back only if the broker departs before first contact."""
    return (not broker_active) and (not first_contact_made)
