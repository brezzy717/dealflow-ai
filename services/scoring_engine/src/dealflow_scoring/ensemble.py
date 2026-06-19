"""Three-model ensemble: XGBoost + RandomForest + MLP.

Produces a 0–100 likelihood-to-sell score with a tier, a model-agreement
confidence, cross-model variance, top ± feature attributions, and a plain-English
explanation. Attribution uses an importance×deviation heuristic (SHAP is tracked
as a follow-up in the coverage ledger, row 2.6).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor

from .features import FEATURE_KEYS, label_for, to_vector

# Tier bands on the 0–100 scale (MASTER_BUILD_SPEC §1).
TIER_BANDS: tuple[tuple[str, float, float], ...] = (
    ("green", 75.0, 100.01),
    ("yellow", 50.0, 75.0),
    ("red", 25.0, 50.0),
    ("monitor", 0.0, 25.0),
)

DEFAULT_WEIGHTS: dict[str, float] = {
    "xgboost_v1": 1 / 3,
    "random_forest_v1": 1 / 3,
    "neural_net_v1": 1 / 3,
}


def tier_for(score: float) -> str:
    for name, low, high in TIER_BANDS:
        if low <= score < high:
            return name
    return "monitor"


@dataclass
class FeatureAttribution:
    feature: str
    label: str
    contribution: float


@dataclass
class EnsemblePrediction:
    score: float
    tier: str
    confidence: float
    variance: float
    model_scores: dict[str, float]
    top_positive: list[FeatureAttribution] = field(default_factory=list)
    top_negative: list[FeatureAttribution] = field(default_factory=list)
    explanation: str = ""


class EnsembleModel:
    """Trainable 3-model ensemble over the canonical 52-feature vector."""

    def __init__(
        self,
        *,
        weights: Mapping[str, float] | None = None,
        random_state: int = 42,
    ) -> None:
        self.weights = dict(weights or DEFAULT_WEIGHTS)
        self._random_state = random_state
        self._scaler = StandardScaler()
        self._xgb = XGBRegressor(
            n_estimators=60,
            max_depth=4,
            learning_rate=0.1,
            random_state=random_state,
            verbosity=0,
        )
        self._rf = RandomForestRegressor(
            n_estimators=80, max_depth=8, random_state=random_state, n_jobs=1
        )
        self._mlp = MLPRegressor(
            hidden_layer_sizes=(64, 32),
            max_iter=300,
            random_state=random_state,
        )
        self._feature_means: np.ndarray | None = None
        self._fitted = False

    @property
    def fitted(self) -> bool:
        return self._fitted

    def fit(self, X: Sequence[Sequence[float]], y: Sequence[float]) -> "EnsembleModel":
        X_arr = np.asarray(X, dtype=float)
        y_arr = np.asarray(y, dtype=float)
        self._feature_means = X_arr.mean(axis=0)
        X_scaled = self._scaler.fit_transform(X_arr)
        self._xgb.fit(X_arr, y_arr)
        self._rf.fit(X_arr, y_arr)
        self._mlp.fit(X_scaled, y_arr)
        self._fitted = True
        return self

    def _model_importances(self) -> np.ndarray:
        xgb_imp = np.asarray(self._xgb.feature_importances_, dtype=float)
        rf_imp = np.asarray(self._rf.feature_importances_, dtype=float)
        combined = xgb_imp + rf_imp
        total = combined.sum()
        return combined / total if total > 0 else combined

    def _attributions(
        self, vector: np.ndarray, top_n: int = 5
    ) -> tuple[list[FeatureAttribution], list[FeatureAttribution]]:
        assert self._feature_means is not None
        importances = self._model_importances()
        deviation = vector - self._feature_means
        contributions = importances * deviation
        order = np.argsort(contributions)

        def build(indexes: np.ndarray) -> list[FeatureAttribution]:
            out: list[FeatureAttribution] = []
            for i in indexes:
                key = FEATURE_KEYS[int(i)]
                out.append(
                    FeatureAttribution(
                        feature=key,
                        label=label_for(key),
                        contribution=round(float(contributions[int(i)]), 5),
                    )
                )
            return out

        positives = build(order[::-1][:top_n])
        positives = [a for a in positives if a.contribution > 0]
        negatives = build(order[:top_n])
        negatives = [a for a in negatives if a.contribution < 0]
        return positives, negatives

    @staticmethod
    def _explain(
        score: float,
        tier: str,
        positives: list[FeatureAttribution],
        negatives: list[FeatureAttribution],
    ) -> str:
        parts = [f"Scored {score:.0f} ({tier.title()})."]
        if positives:
            parts.append(
                "Strongest sell signals: " + ", ".join(a.label for a in positives) + "."
            )
        if negatives:
            parts.append(
                "Mitigating factors: " + ", ".join(a.label for a in negatives) + "."
            )
        return " ".join(parts)

    def predict_one(self, features: Mapping[str, float]) -> EnsemblePrediction:
        if not self._fitted:
            raise RuntimeError("EnsembleModel must be fit before prediction.")
        vector = np.asarray(to_vector(features), dtype=float)
        row = vector.reshape(1, -1)

        model_scores = {
            "xgboost_v1": float(self._xgb.predict(row)[0]),
            "random_forest_v1": float(self._rf.predict(row)[0]),
            "neural_net_v1": float(self._mlp.predict(self._scaler.transform(row))[0]),
        }
        # Clamp each model to the valid 0–100 range before combining.
        clamped = {k: float(np.clip(v, 0.0, 100.0)) for k, v in model_scores.items()}

        score = sum(clamped[name] * self.weights.get(name, 0.0) for name in clamped)
        score = float(np.clip(score, 0.0, 100.0))
        values = np.array(list(clamped.values()))
        variance = float(values.var())
        # Confidence falls as the models disagree (std normalized by the scale).
        confidence = float(np.clip(1.0 - values.std() / 50.0, 0.0, 1.0))

        positives, negatives = self._attributions(vector)
        tier = tier_for(score)
        return EnsemblePrediction(
            score=round(score, 2),
            tier=tier,
            confidence=round(confidence, 4),
            variance=round(variance, 5),
            model_scores={k: round(v, 2) for k, v in clamped.items()},
            top_positive=positives,
            top_negative=negatives,
            explanation=self._explain(score, tier, positives, negatives),
        )
