"""Account lifecycle: purge-on-exit (spec §9 privacy).

When a broker leaves, their personal + client data is purged but anonymized ML
training signals are retained. Deal outcomes are distilled into feature-vector +
quality samples (no PII) before the tenant row is deleted; the cascade removes
all tenant-scoped data.
"""

from __future__ import annotations

import hashlib
import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import models
from .retraining import _lead_to_dict


async def purge_tenant(session: AsyncSession, *, tenant_id: uuid.UUID) -> dict:
    """Retain anonymized training samples, then delete the tenant (cascade)."""
    from dealflow_scoring import extract_features, to_vector

    rows = (
        await session.execute(
            select(models.DealOutcome, models.RawLead)
            .join(
                models.LeadAssignment,
                models.LeadAssignment.id == models.DealOutcome.assignment_id,
            )
            .join(models.RawLead, models.RawLead.id == models.LeadAssignment.lead_id)
            .where(
                models.DealOutcome.tenant_id == tenant_id,
                models.DealOutcome.actual_quality_score.is_not(None),
            )
        )
    ).all()

    tenant_hash = hashlib.sha256(str(tenant_id).encode()).hexdigest()[:16]
    retained = 0
    for outcome, lead in rows:
        vector = to_vector(extract_features(_lead_to_dict(lead)))
        session.add(
            models.RetainedTrainingSample(
                feature_vector=vector,
                actual_quality_score=float(outcome.actual_quality_score),
                source_tenant_hash=tenant_hash,
            )
        )
        retained += 1

    await session.execute(delete(models.Tenant).where(models.Tenant.id == tenant_id))
    await session.commit()
    return {"tenant_purged": str(tenant_id), "retained_samples": retained}
