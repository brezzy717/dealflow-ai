from sqlalchemy import create_engine

from dealflow_backend.db import Base
from dealflow_backend.db import models  # noqa: F401  (register tables on metadata)


def test_metadata_builds_on_sqlite() -> None:
    """The full schema must be internally consistent (FKs, types) and creatable."""
    engine = create_engine("sqlite://")
    try:
        Base.metadata.create_all(engine)
    finally:
        engine.dispose()

    tables = set(Base.metadata.tables)
    # Core spec tables are present.
    for expected in (
        "tenants",
        "users",
        "raw_leads",
        "ensemble_predictions",
        "model_versions",
        "lead_assignments",
        "ai_call_outcomes",
        "deal_outcomes",
        "document_vault",
        "audit_log",
    ):
        assert expected in tables, f"missing table: {expected}"
    assert len(tables) >= 20


def test_lead_assignment_is_unique_per_lead() -> None:
    """Permanent single ownership is enforced by a unique constraint on lead_id."""
    lead_id_col = models.LeadAssignment.__table__.c.lead_id
    assert lead_id_col.unique is True
