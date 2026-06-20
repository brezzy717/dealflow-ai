"""Merge multi-source signals into a lead + build provenance records.

Combines the normalized signals each connector produces into a single ``signals``
dict (taking the strongest signal when sources overlap) and emits provenance rows
matching the ``data_source_enrichment`` table (coverage ledger rows 1.8-1.9).
"""

from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any

from .connectors import SourceConnector


def merge_signals(*signal_maps: Mapping[str, float]) -> dict[str, float]:
    """Combine signal maps, keeping the maximum value per signal."""
    merged: dict[str, float] = {}
    for signals in signal_maps:
        for key, value in signals.items():
            merged[key] = max(merged.get(key, 0.0), float(value))
    return merged


def enrich_lead(
    lead: dict[str, Any],
    payloads_by_source: Mapping[str, dict[str, Any]],
    connectors: Mapping[str, SourceConnector],
    *,
    now: datetime.datetime | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Apply configured connectors to a lead; return (enriched_lead, provenance).

    ``payloads_by_source`` maps a source name to that provider's raw payload for
    this lead. Sources with no connector or no payload are skipped.
    """
    now = now or datetime.datetime.now(tz=datetime.timezone.utc)
    base_signals = dict(lead.get("signals", {}))
    per_source_signals: list[dict[str, float]] = [base_signals]
    provenance: list[dict[str, Any]] = []

    for source, payload in payloads_by_source.items():
        connector = connectors.get(source)
        if connector is None or not payload:
            continue
        signals = connector.to_signals(payload)
        if not signals:
            continue
        per_source_signals.append(signals)
        provenance.append(
            {
                "source": source,
                "fields": signals,
                "pulled_at": now,
            }
        )

    enriched = dict(lead)
    enriched["signals"] = merge_signals(*per_source_signals)
    return enriched, provenance
