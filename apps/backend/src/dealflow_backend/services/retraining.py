"""Feedback-driven retraining orchestrator.

Reads closed/lost deal outcomes, reconstructs each lead's feature vector,
retrains the ensemble, persists a new active ``model_versions`` set + adaptive
``ensemble_weights``, and raises an ``admin_notifications`` row on performance
drift. Runs as a system job (cross-tenant), so it relies on a BYPASSRLS role in
production (coverage ledger rows 2.9–2.12).
"""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import models

MODEL_NAMES = ("xgboost_v1", "random_forest_v1", "neural_net_v1")


def _lead_to_dict(lead: models.RawLead) -> dict[str, Any]:
    payload = lead.source_payloads or {}
    signals = payload.get("signals", {}) if isinstance(payload, dict) else {}
    return {
        "employee_count": lead.employee_count,
        "revenue_millions": float(lead.revenue_millions)
        if lead.revenue_millions is not None
        else 0.0,
        "years_in_business": lead.years_in_business,
        "owner_age": lead.owner_age,
        "signals": signals,
    }


async def retrain_from_feedback(
    session: AsyncSession,
    *,
    artifacts_dir: str = "artifacts",
    min_samples: int = 10,
    seed: int = 7,
) -> dict[str, Any]:
    """Retrain from recorded deal outcomes; persist version, weights, drift."""
    from dealflow_scoring import (
        extract_features,
        is_drifting,
        save_model,
        to_vector,
        train_from_samples,
    )

    rows = (
        await session.execute(
            select(models.DealOutcome, models.RawLead)
            .join(
                models.LeadAssignment,
                models.LeadAssignment.id == models.DealOutcome.assignment_id,
            )
            .join(models.RawLead, models.RawLead.id == models.LeadAssignment.lead_id)
            .where(models.DealOutcome.actual_quality_score.is_not(None))
        )
    ).all()

    samples = [
        (to_vector(extract_features(_lead_to_dict(lead))), float(outcome.actual_quality_score))
        for outcome, lead in rows
    ]
    if len(samples) < min_samples:
        return {"status": "insufficient_feedback", "samples": len(samples)}

    result = train_from_samples(samples, seed=seed)

    baseline = (
        await session.execute(
            select(models.ModelVersion)
            .where(models.ModelVersion.is_active.is_(True))
            .order_by(models.ModelVersion.created_at.desc())
        )
    ).scalars().first()
    baseline_mae = baseline.metrics.get("ensemble_mae") if baseline else None
    drifting = is_drifting(result.ensemble_mae, baseline_mae)

    now = datetime.datetime.now(tz=datetime.timezone.utc)
    version = now.strftime("v%Y%m%d%H%M%S")
    artifact = Path(artifacts_dir) / f"ensemble_{version}.joblib"
    save_model(result.model, artifact)

    # New version supersedes all previous active versions.
    await session.execute(update(models.ModelVersion).values(is_active=False))
    for name in MODEL_NAMES:
        session.add(
            models.ModelVersion(
                model_name=name,
                version=version,
                artifact_uri=str(artifact),
                metrics={
                    "per_model_mae": result.per_model_mae[name],
                    "ensemble_mae": result.ensemble_mae,
                    "disagreement": result.disagreement,
                },
                is_active=True,
                trained_at=now,
            )
        )
        session.add(
            models.EnsembleWeight(
                model_name=name,
                weight=result.weights[name],
                effective_from=now,
                rationale=f"inverse-error retrain {version}",
            )
        )

    if drifting:
        session.add(
            models.AdminNotification(
                level="warning",
                source="retraining",
                message=(
                    f"Model drift: ensemble MAE {result.ensemble_mae:.2f} "
                    f"exceeds baseline {baseline_mae:.2f}"
                    if baseline_mae
                    else "Model drift detected"
                ),
                payload={
                    "baseline_mae": baseline_mae,
                    "current_mae": result.ensemble_mae,
                },
            )
        )

    await session.commit()
    return {
        "status": "retrained",
        "version": version,
        "samples": len(samples),
        "ensemble_mae": result.ensemble_mae,
        "drifting": drifting,
        "weights": result.weights,
    }
