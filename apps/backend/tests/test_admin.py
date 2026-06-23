import uuid

from fastapi.testclient import TestClient

from dealflow_backend.api.dependencies import AuthenticatedUser, get_current_user
from dealflow_backend.main import app


def test_admin_endpoints_require_admin_role() -> None:
    # Non-admin is rejected.
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        user_id="u", tenant_id="t", claims={"role": "broker"}
    )
    try:
        client = TestClient(app)
        for path in ("/api/admin/health", "/api/admin/notifications", "/api/admin/users"):
            assert client.get(path).status_code == 403
        assert client.post(f"/api/admin/clawback/{uuid.uuid4()}").status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_admin_endpoints_require_auth() -> None:
    client = TestClient(app)
    assert client.get("/api/admin/health").status_code == 401
