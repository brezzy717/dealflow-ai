"""DealFlow AI ingestion pipelines."""

from .base import BasePipeline
from .synthetic import SyntheticLeadPipeline, generate_leads

__all__ = ["BasePipeline", "SyntheticLeadPipeline", "generate_leads"]
