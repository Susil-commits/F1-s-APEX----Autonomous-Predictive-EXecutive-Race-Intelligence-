"""APEX Enterprise Gateway & HTTP Security Middleware.

Enforces:
1. Enterprise Security Headers (HSTS, CSP, X-Frame-Options, X-Content-Type-Options).
2. Tightened, environment-aware CORS policy (no wildcard origins with credentials).
3. Transport-level body size protection against buffer exhaustion attacks.
"""
from __future__ import annotations

import os
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class EnterpriseSecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects defense-in-depth security headers and validates request bounds."""

    def __init__(self, app: FastAPI, max_content_length: int = 5 * 1024 * 1024):
        super().__init__(app)
        self.max_content_length = max_content_length

    async def dispatch(self, request: Request, call_next) -> Response:
        # 1. Transport-level payload size check
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > self.max_content_length:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "error": "Payload Too Large",
                            "detail": f"Request body exceeds maximum allowed limit of {self.max_content_length // (1024 * 1024)}MB.",
                        },
                    )
            except ValueError:
                pass

        # 2. Process request through downstream pipeline
        response = await call_next(request)

        # 3. Inject hardened security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "frame-ancestors 'none'; "
            "object-src 'none'; "
            "base-uri 'self';"
        )

        is_production = os.environ.get("ENVIRONMENT", "development").lower() == "production"
        if is_production or request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        return response


def configure_enterprise_cors(app: FastAPI) -> None:
    """Configures environment-governed CORS origins."""
    env_origins = os.environ.get("APEX_ALLOWED_ORIGINS", "")
    if env_origins:
        allowed_origins = [o.strip() for o in env_origins.split(",") if o.strip()]
    else:
        # Default authorized origins for development and production Vercel frontend
        allowed_origins = [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
            "https://f1-apex.vercel.app",
            "https://f1-s-apex-autonomous-predictive-e-x.vercel.app",
        ]

    is_production = os.environ.get("ENVIRONMENT", "development").lower() == "production"

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins if is_production else ["*"],
        allow_credentials=is_production,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-API-Key", "X-Requested-With"],
    )
