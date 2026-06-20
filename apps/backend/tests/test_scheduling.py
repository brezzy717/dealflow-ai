from fastapi.testclient import TestClient

from dealflow_backend.api.dependencies import AuthenticatedUser, get_current_user
from dealflow_backend.main import app
from dealflow_backend.services.scheduling import (
    CADENCE,
    JOBS,
    is_eligible_for_drop,
)


def test_cadence_and_jobs_cover_the_spec() -> None:
    assert set(CADENCE) == {"refresh", "assign", "outreach", "retrain"}
    assert set(JOBS) == {"refresh", "assign", "outreach", "retrain"}
    # Assignment runs Tuesday 06:00 per spec; ingest Mon/Wed/Fri.
    assert CADENCE["assign"] == "0 6 * * 2"
    assert CADENCE["refresh"] == "0 10 * * 1,3,5"
    for expr in CADENCE.values():
        assert len(expr.split()) == 5


def test_is_eligible_for_drop() -> None:
    assert is_eligible_for_drop(0) is True
    assert is_eligible_for_drop(1) is False
    assert is_eligible_for_drop(5) is False


def test_unknown_job_returns_404() -> None:
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        user_id="admin", tenant_id="t", claims={"role": "admin"}
    )
    try:
        client = TestClient(app)
        assert client.post("/api/admin/jobs/bogus").status_code == 404
    finally:
        app.dependency_overrides.clear()
