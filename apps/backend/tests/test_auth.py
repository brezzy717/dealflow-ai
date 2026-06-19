import datetime

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from dealflow_backend.api import dependencies
from dealflow_backend.auth.clerk import ClerkVerifier, ClerkVerifierError
from dealflow_backend.main import app

ISSUER = "https://clerk.example.com"


@pytest.fixture
def private_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _make_token(key: rsa.RSAPrivateKey, **overrides) -> str:
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    payload = {
        "sub": "user_123",
        "iss": ISSUER,
        "iat": now,
        "exp": now + datetime.timedelta(hours=1),
        "org_id": "tenant_abc",
    }
    payload.update(overrides)
    return jwt.encode(payload, key, algorithm="RS256")


def _verifier_for(key: rsa.RSAPrivateKey, **kwargs) -> ClerkVerifier:
    verifier = ClerkVerifier(jwks_url="https://unused/jwks", issuer=ISSUER, **kwargs)
    # Bypass the network JWKS fetch with the local public key.
    verifier._signing_key_for = lambda token: key.public_key()  # type: ignore[method-assign]
    return verifier


def test_verify_accepts_valid_token(private_key: rsa.RSAPrivateKey) -> None:
    claims = _verifier_for(private_key).verify(_make_token(private_key))
    assert claims["sub"] == "user_123"
    assert claims["org_id"] == "tenant_abc"


def test_verify_rejects_expired_token(private_key: rsa.RSAPrivateKey) -> None:
    expired = datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(hours=2)
    token = _make_token(private_key, exp=expired, iat=expired)
    with pytest.raises(ClerkVerifierError):
        _verifier_for(private_key).verify(token)


def test_verify_rejects_wrong_issuer(private_key: rsa.RSAPrivateKey) -> None:
    token = _make_token(private_key, iss="https://evil.example.com")
    with pytest.raises(ClerkVerifierError):
        _verifier_for(private_key).verify(token)


def test_me_requires_authorization_header() -> None:
    client = TestClient(app)
    assert client.get("/api/me").status_code == 401


def test_me_returns_503_when_auth_unconfigured(monkeypatch) -> None:
    monkeypatch.setattr(dependencies, "get_clerk_verifier", lambda: None)
    client = TestClient(app)
    resp = client.get("/api/me", headers={"Authorization": "Bearer something"})
    assert resp.status_code == 503


def test_me_resolves_user_and_tenant(monkeypatch, private_key: rsa.RSAPrivateKey) -> None:
    monkeypatch.setattr(
        dependencies, "get_clerk_verifier", lambda: _verifier_for(private_key)
    )
    client = TestClient(app)
    resp = client.get(
        "/api/me",
        headers={"Authorization": f"Bearer {_make_token(private_key)}"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"user_id": "user_123", "tenant_id": "tenant_abc"}
