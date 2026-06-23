"""Source connectors: provider response -> normalized distress signals.

Each connector maps a provider's payload to a subset of the canonical 52 feature
signal names (see dealflow_scoring.FEATURE_KEYS). The mapping (``to_signals``) is
pure and unit-tested; ``fetch`` performs the live HTTP call behind an injected
client + API key. Endpoint paths and exact field names must be confirmed against
each provider's live API before production use (coverage ledger rows 1.3-1.7).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _f(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


class HttpClient(Protocol):
    def get(self, url: str, *, params: dict | None = ..., headers: dict | None = ...) -> Any: ...


class SourceConnector(ABC):
    """Base connector: a named source with a pure signal mapper."""

    name: str

    def __init__(self, *, api_key: str | None = None, base_url: str | None = None) -> None:
        self.api_key = api_key
        self.base_url = base_url

    @abstractmethod
    def to_signals(self, payload: dict[str, Any]) -> dict[str, float]:
        """Map a provider payload to normalized [0,1] feature signals."""

    def configured(self) -> bool:
        return bool(self.api_key and self.base_url)


class YelpConnector(SourceConnector):
    name = "yelp"

    def to_signals(self, payload: dict[str, Any]) -> dict[str, float]:
        rating = _f(payload.get("rating"))
        history = [float(x) for x in payload.get("rating_history", []) if x is not None]
        signals: dict[str, float] = {"yelp_rating_normalized": _clamp(rating / 5.0)}
        if len(history) >= 2:
            first, last = history[0], history[-1]
            decline = (first - last) / first if first > 0 else 0.0
            signals["yelp_trend_risk"] = _clamp(decline)
            signals["yelp_rating_drop"] = 1.0 if last < first - 0.4 else 0.0
            signals["yelp_rating_drop_severe"] = 1.0 if last < first - 1.0 else 0.0
        counts = [float(x) for x in payload.get("review_counts", []) if x is not None]
        if len(counts) >= 2 and counts[0] > 0:
            signals["review_velocity_declining"] = _clamp(
                (counts[0] - counts[-1]) / counts[0]
            )
        signals["avg_sentiment_risk"] = _clamp(1.0 - rating / 5.0)
        return signals


class DeweyConnector(SourceConnector):
    """Dewey bundles ATTOM, Builty, People Data Labs, etc."""

    name = "dewey"

    def to_signals(self, payload: dict[str, Any]) -> dict[str, float]:
        attom = payload.get("attom", {})
        builty = payload.get("builty", {})
        pdl = payload.get("pdl", {})
        current_year = int(payload.get("as_of_year", 2026))

        signals: dict[str, float] = {
            "pre_foreclosure": 1.0 if attom.get("preforeclosure") else 0.0,
            "tax_delinquent": 1.0 if attom.get("tax_delinquent") else 0.0,
            "property_value_risk": _clamp(_f(attom.get("assessment_increase_yoy"))),
        }
        last_permit = builty.get("last_permit_year")
        if last_permit:
            years_since = max(0, current_year - int(last_permit))
            signals["permit_recency"] = _clamp(years_since / 10.0)
        employee_trend = _f(pdl.get("employee_trend_12mo"))
        if employee_trend < 0:
            signals["business_decline_score"] = _clamp(-employee_trend)
        if pdl.get("recent_exec_departure"):
            signals["owner_distress_score"] = max(
                signals.get("owner_distress_score", 0.0), 0.5
            )
        return signals


class NasdaqConnector(SourceConnector):
    name = "nasdaq"

    def to_signals(self, payload: dict[str, Any]) -> dict[str, float]:
        index_change = _f(payload.get("industry_index_change_pct"))
        signals: dict[str, float] = {}
        if index_change < 0:
            signals["business_decline_score"] = _clamp(-index_change)
        signals["new_competitors_risk"] = _clamp(_f(payload.get("sector_volatility")))
        return signals


class SecEdgarConnector(SourceConnector):
    name = "sec_edgar"

    def to_signals(self, payload: dict[str, Any]) -> dict[str, float]:
        signals: dict[str, float] = {}
        if payload.get("bankruptcy_filed"):
            signals["owner_personal_bankruptcy"] = 1.0
            signals["bankruptcy_recency"] = _clamp(
                1.0 - _f(payload.get("bankruptcy_age_years")) / 5.0
            )
        distress_filings = _f(payload.get("distress_filing_count"))
        if distress_filings > 0:
            signals["owner_distress_score"] = _clamp(distress_filings / 5.0)
        return signals


class DataGovConnector(SourceConnector):
    name = "data_gov"

    def to_signals(self, payload: dict[str, Any]) -> dict[str, float]:
        signals: dict[str, float] = {}
        zoning_changes = _f(payload.get("zoning_changes_last_year"))
        if zoning_changes > 0:
            signals["recent_zoning_change"] = 1.0
            signals["zoning_change_recency"] = _clamp(zoning_changes / 3.0)
        if payload.get("sba_loan_default"):
            signals["owner_credit_risk"] = max(signals.get("owner_credit_risk", 0.0), 0.7)
        return signals


# Registry of available connectors by source name.
CONNECTORS: dict[str, type[SourceConnector]] = {
    cls.name: cls
    for cls in (
        YelpConnector,
        DeweyConnector,
        NasdaqConnector,
        SecEdgarConnector,
        DataGovConnector,
    )
}
