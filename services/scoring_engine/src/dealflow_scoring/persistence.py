"""Model artifact persistence (joblib).

Serializes a fitted ``EnsembleModel`` (sub-models + scaler + weights) to bytes or
a path so a version can be stored in object storage and reloaded for scoring
(coverage ledger row 2.9). The DB's ``model_versions`` row holds the artifact URI.
"""

from __future__ import annotations

import io
from pathlib import Path

import joblib

from .ensemble import EnsembleModel


def dump_bytes(model: EnsembleModel) -> bytes:
    buffer = io.BytesIO()
    joblib.dump(model, buffer)
    return buffer.getvalue()


def load_bytes(data: bytes) -> EnsembleModel:
    model = joblib.load(io.BytesIO(data))
    if not isinstance(model, EnsembleModel):
        raise TypeError("Artifact is not an EnsembleModel")
    return model


def save_model(model: EnsembleModel, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
    return path


def load_model(path: str | Path) -> EnsembleModel:
    model = joblib.load(Path(path))
    if not isinstance(model, EnsembleModel):
        raise TypeError("Artifact is not an EnsembleModel")
    return model
