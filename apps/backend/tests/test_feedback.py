import uuid

from fastapi.testclient import TestClient

from dealflow_backend.api.dependencies import AuthenticatedUser, get_current_user
from dealflow_backend.main import app


def test_call_outcome_requires_auth() -> None:
    client = TestClient(app)
    resp = client.post(
        f"/api/prospects/{uuid.uuid4()}/call-outcome", json={"outcome": "booked"}
    )
    assert resp.status_code == 401


def test_retrain_requires_admin_role() -> None:
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        user_id="u", tenant_id="t", claims={"role": "broker"}
    )
    try:
        client = TestClient(app)
        assert client.post("/api/admin/retrain").status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_retrain_rejects_missing_role() -> None:
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        user_id="u", tenant_id="t", claims={}
    )
    try:
        client = TestClient(app)
        assert client.post("/api/admin/retrain").status_code == 403
    finally:
        app.dependency_overrides.clear()
