"""High-level scoring: lead in, prediction out, plus demo training data.

``make_training_data`` synthesizes a feature matrix with a known latent
"intent-to-sell" function so the ensemble has something real to learn until the
feedback-driven training set exists (coverage ledger row 2.3). The latent
function rewards retirement-age owners, distress signals, and urgency.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np

from .ensemble import EnsembleModel, EnsemblePrediction
from .features import FEATURE_KEYS, extract_features, to_vector

# Features that most strongly drive the latent intent signal, with weights.
_LATENT_DRIVERS: dict[str, float] = {
    "owner_age_normalized": 22.0,
    "pre_foreclosure": 18.0,
    "tax_delinquent": 10.0,
    "succession_risk": 8.0,
    "owner_personal_bankruptcy": 9.0,
    "owner_credit_risk": 6.0,
    "avg_sentiment_risk": 7.0,
    "yelp_trend_risk": 5.0,
    "new_competitors_risk": 5.0,
    "social_inactivity_score": 4.0,
    "life_event_critical": 8.0,
    "lease_critical": 6.0,
    "balloon_urgency": 5.0,
    "urgency_score": 10.0,
    "search_intent_score": 9.0,
}


def make_training_data(
    n_samples: int = 600, seed: int = 7
) -> tuple[list[list[float]], list[float]]:
    """Generate (X, y) where y is a 0–100 latent intent score."""
    rng = np.random.default_rng(seed)
    n_features = len(FEATURE_KEYS)
    X = rng.random((n_samples, n_features))
    weights = np.zeros(n_features)
    for key, weight in _LATENT_DRIVERS.items():
        weights[FEATURE_KEYS.index(key)] = weight

    raw = X @ weights
    noise = rng.normal(0.0, 3.0, size=n_samples)
    # Normalize the weighted sum to ~0–100.
    scaled = 100.0 * (raw - raw.min()) / (raw.max() - raw.min() + 1e-9) + noise
    y = np.clip(scaled, 0.0, 100.0)
    return X.tolist(), y.tolist()


def train_demo_model(seed: int = 7) -> EnsembleModel:
    """Build and fit an ensemble on synthetic data (for dev, demos, and tests)."""
    X, y = make_training_data(seed=seed)
    return EnsembleModel(random_state=seed).fit(X, y)


def score_lead(model: EnsembleModel, lead: Mapping[str, Any]) -> EnsemblePrediction:
    """Extract features from a lead and run the ensemble."""
    return model.predict_one(extract_features(lead))


__all__ = [
    "make_training_data",
    "train_demo_model",
    "score_lead",
    "to_vector",
]
