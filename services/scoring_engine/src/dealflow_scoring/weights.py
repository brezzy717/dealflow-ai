"""Adaptive ensemble weighting.

Recent per-model error drives the weights: a model with lower holdout error gets
a larger share (inverse-error weighting). Keeps the ensemble self-correcting as
feedback accumulates (MASTER_BUILD_SPEC §3, coverage ledger row 2.10).
"""

from __future__ import annotations

from collections.abc import Mapping

_EPS = 1e-6


def adapt_weights(errors: Mapping[str, float]) -> dict[str, float]:
    """Inverse-error weights, normalized to sum to 1.0."""
    if not errors:
        return {}
    inverse = {name: 1.0 / (max(err, 0.0) + _EPS) for name, err in errors.items()}
    total = sum(inverse.values())
    if total <= 0:
        # Degenerate case: fall back to equal weights.
        equal = 1.0 / len(errors)
        return {name: equal for name in errors}
    return {name: value / total for name, value in inverse.items()}
