"""DealFlow AI scoring engine: canonical features + 3-model ensemble."""

from .ensemble import EnsembleModel, EnsemblePrediction, FeatureAttribution, tier_for
from .features import FEATURE_KEYS, extract_features, label_for, to_vector
from .persistence import dump_bytes, load_bytes, load_model, save_model
from .registry import ModelRegistry
from .scoring import make_training_data, score_lead, train_demo_model
from .training import (
    TrainingResult,
    is_drifting,
    samples_from_outcomes,
    train_from_samples,
)
from .weights import adapt_weights

__all__ = [
    "EnsembleModel",
    "EnsemblePrediction",
    "FeatureAttribution",
    "tier_for",
    "FEATURE_KEYS",
    "extract_features",
    "label_for",
    "to_vector",
    "ModelRegistry",
    "make_training_data",
    "score_lead",
    "train_demo_model",
    "TrainingResult",
    "train_from_samples",
    "is_drifting",
    "samples_from_outcomes",
    "adapt_weights",
    "dump_bytes",
    "load_bytes",
    "save_model",
    "load_model",
]
