from fastapi.testclient import TestClient

from dealflow_backend.main import app


def test_dashboard_endpoints_require_auth() -> None:
    client = TestClient(app)
    for path in ("/api/metrics", "/api/appointments", "/api/clients", "/api/tasks"):
        assert client.get(path).status_code == 401
