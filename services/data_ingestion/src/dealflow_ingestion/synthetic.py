"""Synthetic lead source.

A seedable stand-in for the real connectors (Dewey/Yelp/NASDAQ/SEC/Data.gov),
so the full ingest → score → assign → dashboard path can run end-to-end before
those API clients exist (coverage ledger rows 1.2–1.7). Emits normalized lead
dicts whose shape matches the ``raw_leads`` table, including a ``signals``
sub-dict of distress features the scoring engine consumes.
"""

from __future__ import annotations

import random
from collections.abc import Iterable
from typing import Any

from .base import BasePipeline
from .dedup import dedup_key

_STATES = ("AZ", "UT", "TX")
_INDUSTRIES = (
    "HVAC Services",
    "Auto Repair",
    "Family Restaurant",
    "Dental Practice",
    "Landscaping",
    "Dry Cleaning",
    "Machine Shop",
    "Veterinary Clinic",
)
_CITIES = {
    "AZ": ("Phoenix", "Tucson", "Mesa"),
    "UT": ("Salt Lake City", "Provo", "Ogden"),
    "TX": ("Austin", "Dallas", "Houston"),
}
_NAME_PREFIXES = ("Sunrise", "Summit", "Legacy", "Frontier", "Cactus", "Lone Star")
_NAME_SUFFIXES = ("Holdings", "& Sons", "Group", "Co", "Enterprises", "LLC")


def generate_leads(
    n: int = 50, *, seed: int = 13, states: tuple[str, ...] = _STATES
) -> list[dict[str, Any]]:
    """Generate ``n`` normalized lead dicts with correlated distress signals."""
    rng = random.Random(seed)
    leads: list[dict[str, Any]] = []

    for i in range(n):
        state = rng.choice(states)
        city = rng.choice(_CITIES[state])
        name = f"{rng.choice(_NAME_PREFIXES)} {rng.choice(_INDUSTRIES).split()[0]} {rng.choice(_NAME_SUFFIXES)}"
        owner_age = rng.randint(38, 78)
        years = rng.randint(2, 40)
        employees = rng.randint(3, 150)
        revenue = round(rng.uniform(0.3, 30.0), 2)

        # Older owners + longer-tenured businesses are likelier to be distressed.
        distress_bias = (owner_age - 38) / 40.0
        flag = lambda p: 1.0 if rng.random() < p else 0.0  # noqa: E731

        signals = {
            "pre_foreclosure": flag(0.10 + 0.25 * distress_bias),
            "tax_delinquent": flag(0.12 + 0.2 * distress_bias),
            "succession_risk": flag(0.2 + 0.4 * distress_bias),
            "has_successor": flag(0.4 - 0.25 * distress_bias),
            "owner_personal_bankruptcy": flag(0.05 + 0.15 * distress_bias),
            "owner_credit_risk": round(rng.uniform(0.0, distress_bias), 3),
            "life_event_critical": flag(0.08 + 0.2 * distress_bias),
            "lease_critical": flag(0.1 + 0.15 * distress_bias),
            "balloon_urgency": round(rng.uniform(0.0, 0.6 * distress_bias), 3),
            "yelp_trend_risk": round(rng.uniform(0.0, 1.0), 3),
            "avg_sentiment_risk": round(rng.uniform(0.0, 1.0), 3),
            "new_competitors_risk": round(rng.uniform(0.0, 1.0), 3),
            "social_inactivity_score": round(rng.uniform(0.0, 1.0), 3),
            "urgency_score": round(rng.uniform(0.0, 0.5) + 0.5 * distress_bias, 3),
            "search_intent_score": round(rng.uniform(0.0, distress_bias), 3),
        }

        address = f"{rng.randint(100, 9999)} {rng.choice(('Main', 'Oak', 'Industrial', 'Commerce'))} St"
        lead = {
            "business_name": name,
            "industry": rng.choice(_INDUSTRIES),
            "address_line1": address,
            "city": city,
            "state": state,
            "postal_code": f"{rng.randint(10000, 99999)}",
            "apn": f"{rng.randint(100, 999)}-{rng.randint(10, 99)}-{rng.randint(100, 999)}",
            "employee_count": employees,
            "revenue_millions": revenue,
            "years_in_business": years,
            "owner_name": f"Owner {i}",
            "owner_email": f"owner{i}@example.com",
            "owner_phone": f"555-01{i:02d}",
            "owner_age": owner_age,
            "dedup_key": dedup_key(name, address, state),
            "signals": signals,
        }
        leads.append(lead)

    return leads


class SyntheticLeadPipeline(BasePipeline):
    """BasePipeline wrapper around ``generate_leads`` with an injectable loader."""

    def __init__(
        self,
        *,
        count: int = 50,
        seed: int = 13,
        loader=None,
    ) -> None:
        self._count = count
        self._seed = seed
        self._loader = loader

    def fetch(self) -> Iterable[dict[str, Any]]:
        return generate_leads(self._count, seed=self._seed)

    def transform(self, records: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
        # Synthetic records are already normalized; dedup by key.
        seen: set[str] = set()
        out: list[dict[str, Any]] = []
        for record in records:
            key = record["dedup_key"]
            if key not in seen:
                seen.add(key)
                out.append(record)
        return out

    def load(self, records: Iterable[dict[str, Any]]) -> int:
        records = list(records)
        if self._loader is not None:
            return self._loader(records)
        return len(records)
