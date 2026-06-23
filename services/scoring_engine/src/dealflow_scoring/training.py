"""Feedback-driven retraining.

Builds a model from labeled samples (feature vector + observed quality score),
evaluates each sub-model on a holdout, sets inverse-error ensemble weights, and
reports drift signals so the caller can flag regressions (coverage ledger rows
2.10–2.12).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np

from .ensemble import EnsembleModel
from .weights import adapt_weights


@dataclass
class TrainingResult:
    model: EnsembleModel
    per_model_mae: dict[str, float]
    ensemble_mae: float
    weights: dict[str, float]
    disagreement: float
    n_train: int
    n_holdout: int


def _mae(predicted: np.ndarray, actual: np.ndarray) -> float:
    return float(np.abs(predicted - actual).mean())


def train_from_samples(
    samples: Sequence[tuple[Sequence[float], float]],
    *,
    seed: int = 7,
    holdout_fraction: float = 0.2,
) -> TrainingResult:
    """Retrain the ensemble from (feature_vector, quality_score) pairs."""
    if len(samples) < 10:
        raise ValueError("Need at least 10 samples to retrain.")

    rng = np.random.default_rng(seed)
    X = np.asarray([s[0] for s in samples], dtype=float)
    y = np.asarray([s[1] for s in samples], dtype=float)

    order = rng.permutation(len(samples))
    n_holdout = max(1, int(len(samples) * holdout_fraction))
    holdout_idx, train_idx = order[:n_holdout], order[n_holdout:]

    model = EnsembleModel(random_state=seed).fit(X[train_idx], y[train_idx])

    per_model_preds = model.predict_models(X[holdout_idx])
    actual = y[holdout_idx]
    per_model_mae = {name: _mae(pred, actual) for name, pred in per_model_preds.items()}

    weights = adapt_weights(per_model_mae)
    model.set_weights(weights)

    ensemble_pred = sum(
        per_model_preds[name] * weights[name] for name in per_model_preds
    )
    ensemble_mae = _mae(np.asarray(ensemble_pred), actual)

    return TrainingResult(
        model=model,
        per_model_mae=per_model_mae,
        ensemble_mae=ensemble_mae,
        weights=weights,
        disagreement=model.disagreement(X[holdout_idx]),
        n_train=len(train_idx),
        n_holdout=len(holdout_idx),
    )


def is_drifting(
    current_mae: float, baseline_mae: float | None, *, tolerance: float = 1.25
) -> bool:
    """True if error has grown beyond ``tolerance``× the baseline (perf drift)."""
    if baseline_mae is None or baseline_mae <= 0:
        return False
    return current_mae > baseline_mae * tolerance


def samples_from_outcomes(
    rows: Sequence[Mapping[str, object]],
) -> list[tuple[list[float], float]]:
    """Adapt persisted feedback rows to training samples.

    Each row needs a ``feature_vector`` (list of 52 floats) and an
    ``actual_quality_score`` (0–100). Rows missing either are skipped.
    """
    out: list[tuple[list[float], float]] = []
    for row in rows:
        vector = row.get("feature_vector")
        quality = row.get("actual_quality_score")
        if vector is None or quality is None:
            continue
        out.append(([float(v) for v in vector], float(quality)))  # type: ignore[arg-type]
    return out
