from fastapi.testclient import TestClient

from dealflow_backend.main import app


def test_settings_and_billing_require_auth() -> None:
    client = TestClient(app)
    assert client.get("/api/settings").status_code == 401
    assert client.put("/api/settings", json={}).status_code == 401
    assert client.post("/api/onboarding", json={}).status_code == 401
    assert client.get("/api/billing/status").status_code == 401


def test_billing_webhook_rejects_bad_secret() -> None:
    client = TestClient(app)
    # No BILLING_WEBHOOK_SECRET configured -> webhook denies.
    resp = client.post(
        "/api/billing/webhook",
        json={"tenant_id": "00000000-0000-0000-0000-000000000000", "subscription_status": "active"},
        headers={"x-billing-secret": "nope"},
    )
    assert resp.status_code == 401
