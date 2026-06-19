from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .api.prospects import router as prospects_router
from .api.routes import api_router, router
from .config import Settings, get_settings
from .core.logging import configure_logging

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach a baseline set of hardening headers to every response."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        for header, value in SECURITY_HEADERS.items():
            response.headers.setdefault(header, value)
        return response


def create_app(settings: Settings | None = None) -> FastAPI:
    configure_logging()
    config = settings or get_settings()

    app = FastAPI(
        title="DealFlow AI API",
        version="0.1.0",
        docs_url=config.docs_url,
        openapi_url=config.openapi_url,
    )

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health/probe routes stay at the root; product routes are namespaced under
    # the configured API prefix.
    app.include_router(router)
    app.include_router(api_router)
    app.include_router(prospects_router)

    return app


app = create_app()
