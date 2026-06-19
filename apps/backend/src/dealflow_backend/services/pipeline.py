"""End-to-end demo pipeline: ingest -> score -> persist -> assign.

Ties the ingestion and scoring packages to the database for the Phase 2 vertical
slice. The scoring/ingestion imports are local so the backend remains importable
when those optional packages are absent; the orchestration itself requires them.
"""

from __future__ import annotations

import datetime
import uuid
from functools import lru_cache

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import models
from .assignment import BrokerParams, Candidate, select_for_broker


@lru_cache(maxsize=1)
def _get_demo_model():
    from dealflow_scoring import train_demo_model

    return train_demo_model()


def _attr_dicts(attributions) -> list[dict]:
    return [
        {"feature": a.feature, "label": a.label, "contribution": a.contribution}
        for a in attributions
    ]


def _broker_params(bp: models.BrokerParameters | None) -> BrokerParams:
    if bp is None:
        return BrokerParams()
    return BrokerParams(
        min_years_in_business=bp.min_years_in_business,
        min_employees=bp.min_employees,
        max_employees=bp.max_employees,
        min_revenue_millions=float(bp.min_revenue_millions)
        if bp.min_revenue_millions is not None
        else None,
        max_revenue_millions=float(bp.max_revenue_millions)
        if bp.max_revenue_millions is not None
        else None,
        omitted_industries=frozenset(bp.omitted_industries or []),
        omitted_locations=frozenset(bp.omitted_locations or []),
    )


async def run_demo_pipeline(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    lead_count: int = 40,
    seed: int = 13,
) -> dict[str, int]:
    """Ingest synthetic leads, score them, and assign one drop to ``user_id``."""
    from dealflow_ingestion import generate_leads
    from dealflow_scoring import score_lead

    now = datetime.datetime.now(tz=datetime.timezone.utc)
    model = _get_demo_model()
    raw_leads = generate_leads(lead_count, seed=seed)

    candidates: list[Candidate] = []
    leads_created = 0

    for raw in raw_leads:
        lead = (
            await session.execute(
                select(models.RawLead).where(models.RawLead.dedup_key == raw["dedup_key"])
            )
        ).scalar_one_or_none()
        if lead is None:
            lead = models.RawLead(
                business_name=raw["business_name"],
                address_line1=raw["address_line1"],
                city=raw["city"],
                state=raw["state"],
                postal_code=raw["postal_code"],
                apn=raw["apn"],
                industry=raw["industry"],
                employee_count=raw["employee_count"],
                revenue_millions=raw["revenue_millions"],
                years_in_business=raw["years_in_business"],
                owner_name=raw["owner_name"],
                owner_email=raw["owner_email"],
                owner_phone=raw["owner_phone"],
                owner_age=raw["owner_age"],
                dedup_key=raw["dedup_key"],
                source_payloads={"signals": raw["signals"]},
            )
            session.add(lead)
            await session.flush()
            leads_created += 1

        prediction = score_lead(model, raw)
        session.add(
            models.EnsemblePrediction(
                lead_id=lead.id,
                ensemble_score=prediction.score,
                tier=models.LeadTier(prediction.tier),
                confidence=prediction.confidence,
                prediction_variance=prediction.variance,
                model_scores=prediction.model_scores,
                top_positive=_attr_dicts(prediction.top_positive),
                top_negative=_attr_dicts(prediction.top_negative),
                explanation=prediction.explanation,
                model_version_ids=["xgboost_v1", "random_forest_v1", "neural_net_v1"],
                scored_at=now,
            )
        )
        candidates.append(
            Candidate(
                lead_id=str(lead.id),
                tier=prediction.tier,
                industry=lead.industry,
                employee_count=lead.employee_count,
                revenue_millions=float(lead.revenue_millions or 0),
                years_in_business=lead.years_in_business,
                location=lead.state,
            )
        )

    await session.flush()

    bp = (
        await session.execute(
            select(models.BrokerParameters).where(
                models.BrokerParameters.user_id == user_id
            )
        )
    ).scalar_one_or_none()
    params = _broker_params(bp)

    already_assigned = set(
        (
            await session.execute(select(models.LeadAssignment.lead_id))
        ).scalars().all()
    )
    selectable = [c for c in candidates if uuid.UUID(c.lead_id) not in already_assigned]
    chosen = select_for_broker(selectable, params)

    for candidate in chosen:
        session.add(
            models.LeadAssignment(
                tenant_id=tenant_id,
                lead_id=uuid.UUID(candidate.lead_id),
                user_id=user_id,
                tier=models.LeadTier(candidate.tier),
                assigned_at=now,
            )
        )

    await session.commit()
    return {
        "leads_created": leads_created,
        "scored": len(candidates),
        "assigned": len(chosen),
    }
