import uuid

from fastapi.testclient import TestClient

from dealflow_backend.main import app


def test_dealroom_endpoints_require_auth() -> None:
    client = TestClient(app)
    assert client.get("/api/pipeline").status_code == 401
    assert client.post(f"/api/pipeline/{uuid.uuid4()}/open").status_code == 401
    assert client.get(f"/api/deal-rooms/{uuid.uuid4()}").status_code == 401
