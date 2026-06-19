"""DealFlow AI scoring engine: canonical features + 3-model ensemble."""

from .ensemble import EnsembleModel, EnsemblePrediction, FeatureAttribution, tier_for
from .features import FEATURE_KEYS, extract_features, label_for, to_vector
from .registry import ModelRegistry
from .scoring import make_training_data, score_lead, train_demo_model

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
]
