"""Clerk JWT verification.

Verifies the RS256-signed session token Clerk issues, using Clerk's published
JWKS. The verifier is split so the claim-validation path can be unit tested with
a locally generated key (see tests/test_auth.py) without network access:
``_signing_key_for`` is the only method that touches the network.
"""

from __future__ import annotations

from functools import lru_cache

import jwt
from jwt import PyJWKClient

from ..config import Settings, get_settings


class ClerkVerifierError(Exception):
    """Raised when a token cannot be verified."""


class ClerkVerifier:
    def __init__(
        self,
        *,
        jwks_url: str,
        issuer: str,
        audience: str | None = None,
        leeway_seconds: int = 30,
    ) -> None:
        self._jwks_url = jwks_url
        self._issuer = issuer
        self._audience = audience
        self._leeway = leeway_seconds
        self._jwk_client: PyJWKClient | None = None

    def _signing_key_for(self, token: str):
        if self._jwk_client is None:
            self._jwk_client = PyJWKClient(self._jwks_url)
        return self._jwk_client.get_signing_key_from_jwt(token).key

    def verify(self, token: str) -> dict:
        """Validate signature + standard claims and return the payload."""
        try:
            signing_key = self._signing_key_for(token)
            return jwt.decode(
                token,
                signing_key,
                algorithms=["RS256"],
                issuer=self._issuer,
                audience=self._audience,
                leeway=self._leeway,
                options={"require": ["exp", "iat"], "verify_aud": self._audience is not None},
            )
        except jwt.PyJWTError as exc:  # invalid signature/issuer/expiry/etc.
            raise ClerkVerifierError(str(exc)) from exc


@lru_cache(maxsize=1)
def get_clerk_verifier(settings: Settings | None = None) -> ClerkVerifier | None:
    """Build the verifier from settings, or ``None`` when auth is unconfigured."""
    config = settings or get_settings()
    if not config.auth_configured:
        return None
    assert config.clerk_jwks_url is not None and config.clerk_issuer is not None
    return ClerkVerifier(
        jwks_url=config.clerk_jwks_url,
        issuer=config.clerk_issuer,
        audience=config.clerk_audience,
    )
