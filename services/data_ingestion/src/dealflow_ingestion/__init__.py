"""DealFlow AI ingestion pipelines."""

from .base import BasePipeline
from .connectors import CONNECTORS, SourceConnector
from .dedup import dedup_key, normalize_address, normalize_name
from .enrichment import enrich_lead, merge_signals
from .synthetic import SyntheticLeadPipeline, generate_leads

__all__ = [
    "BasePipeline",
    "SyntheticLeadPipeline",
    "generate_leads",
    "CONNECTORS",
    "SourceConnector",
    "dedup_key",
    "normalize_name",
    "normalize_address",
    "enrich_lead",
    "merge_signals",
]
