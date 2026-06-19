"""Canonical 52-feature catalog and extraction.

``FEATURE_KEYS`` is the single source of truth for feature order (resolves the
two divergent lists in the source docs, per MASTER_BUILD_SPEC §3). A lead is a
mapping of business fields plus a ``signals`` sub-mapping of raw distress signals
(the ingestion layer populates it). Missing values default to 0.0 so the vector
is always complete and aligned to ``FEATURE_KEYS``.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

# --- 52 canonical features, grouped as in the spec --------------------------

FEATURE_KEYS: tuple[str, ...] = (
    # Financial / business (14)
    "revenue_millions",
    "revenue_per_employee",
    "employee_count",
    "years_in_business",
    "maturity_score",
    "owner_age_normalized",
    "has_successor",
    "succession_risk",
    "pre_foreclosure",
    "tax_delinquent",
    "lease_urgency",
    "lease_critical",
    "balloon_urgency",
    "permit_recency",
    # Owner life events (6)
    "recent_divorce",
    "recent_spouse_death",
    "recent_health_event",
    "life_event_recency",
    "life_event_critical",
    "has_major_life_event",
    # Personal financial distress (6)
    "owner_personal_bankruptcy",
    "owner_lien_count",
    "owner_lien_amount_normalized",
    "owner_recent_lien_count",
    "bankruptcy_recency",
    "owner_credit_risk",
    # Online sentiment (10)
    "yelp_rating_normalized",
    "yelp_trend_risk",
    "yelp_rating_drop",
    "yelp_rating_drop_severe",
    "google_rating_normalized",
    "google_trend_risk",
    "avg_online_rating",
    "avg_sentiment_risk",
    "review_velocity_declining",
    "negative_review_spike",
    # Market dynamics (6)
    "new_competitors_risk",
    "recent_competitors_count",
    "nearby_competitors_count",
    "recent_zoning_change",
    "zoning_change_recency",
    "property_value_risk",
    # Social media (5)
    "social_inactivity_score",
    "social_abandoned",
    "social_frequency_drop",
    "social_frequency_drop_severe",
    "social_engagement_risk",
    # Composite (4)
    "distress_intensity",
    "owner_distress_score",
    "business_decline_score",
    "urgency_score",
    # Search intent (1)
    "search_intent_score",
)

assert len(FEATURE_KEYS) == 52, "FEATURE_KEYS must hold exactly 52 features"

# Human-readable phrasing for explanations.
FEATURE_LABELS: dict[str, str] = {
    "owner_age_normalized": "owner at/near retirement age",
    "pre_foreclosure": "active pre-foreclosure",
    "tax_delinquent": "delinquent property taxes",
    "succession_risk": "no clear successor",
    "has_successor": "has an identified successor",
    "lease_urgency": "lease nearing expiry",
    "lease_critical": "lease critically close to expiry",
    "balloon_urgency": "balloon payment approaching",
    "permit_recency": "no recent building permits",
    "recent_divorce": "recent owner divorce",
    "recent_spouse_death": "recent loss of spouse",
    "recent_health_event": "recent owner health event",
    "life_event_critical": "major recent life event",
    "has_major_life_event": "significant life event on record",
    "owner_personal_bankruptcy": "owner bankruptcy",
    "owner_lien_count": "liens against the owner",
    "owner_credit_risk": "elevated owner credit risk",
    "bankruptcy_recency": "recent bankruptcy filing",
    "yelp_trend_risk": "declining Yelp trajectory",
    "yelp_rating_drop_severe": "severe Yelp rating drop",
    "google_trend_risk": "declining Google rating trajectory",
    "avg_sentiment_risk": "deteriorating online sentiment",
    "review_velocity_declining": "slowing review activity",
    "negative_review_spike": "spike in negative reviews",
    "new_competitors_risk": "new competition nearby",
    "recent_zoning_change": "recent zoning change",
    "property_value_risk": "property value pressure",
    "social_inactivity_score": "social media inactivity",
    "social_abandoned": "abandoned social presence",
    "social_frequency_drop_severe": "sharp drop in posting",
    "social_engagement_risk": "falling social engagement",
    "distress_intensity": "overall distress intensity",
    "owner_distress_score": "owner-level distress",
    "business_decline_score": "business decline signals",
    "urgency_score": "time-sensitivity of the opportunity",
    "search_intent_score": "exit-related search activity",
    "revenue_per_employee": "low revenue per employee",
    "years_in_business": "long-established business",
    "maturity_score": "business maturity",
}


def label_for(key: str) -> str:
    return FEATURE_LABELS.get(key, key.replace("_", " "))


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _get(lead: Mapping[str, Any], key: str, default: float = 0.0) -> float:
    signals = lead.get("signals")
    if isinstance(signals, Mapping) and key in signals:
        return float(signals[key])
    if key in lead:
        return float(lead[key])
    return default


def extract_features(lead: Mapping[str, Any]) -> dict[str, float]:
    """Map a lead to the complete, ordered 52-feature dict.

    A handful of features are derived from core business fields; the rest are
    read from the lead's ``signals`` (or default to 0.0). Derivation here is the
    "core features" path tracked in the coverage ledger (row 2.2).
    """
    features = {key: _get(lead, key) for key in FEATURE_KEYS}

    employee_count = float(lead.get("employee_count") or 0.0)
    revenue_millions = float(lead.get("revenue_millions") or 0.0)
    years = float(lead.get("years_in_business") or 0.0)
    owner_age = float(lead.get("owner_age") or 0.0)

    # Derived, normalized features (override the raw read where we can compute).
    features["employee_count"] = _clamp(employee_count / 200.0)
    features["revenue_millions"] = _clamp(revenue_millions / 50.0)
    if employee_count > 0:
        features["revenue_per_employee"] = _clamp(
            (revenue_millions * 1_000_000 / employee_count) / 500_000.0
        )
    features["years_in_business"] = _clamp(min(years, 25.0) / 25.0)
    features["maturity_score"] = _clamp(min(years, 25.0) / 25.0)
    if owner_age > 0:
        # Retirement-age owners score higher; ramps from 40 to 85.
        features["owner_age_normalized"] = _clamp((owner_age - 40.0) / 45.0)

    return features


def to_vector(features: Mapping[str, float]) -> list[float]:
    """Return feature values in canonical ``FEATURE_KEYS`` order."""
    return [float(features.get(key, 0.0)) for key in FEATURE_KEYS]
