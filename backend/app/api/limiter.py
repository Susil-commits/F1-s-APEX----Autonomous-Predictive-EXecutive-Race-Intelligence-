"""Enterprise Multi-Tier Distributed Rate Limiter for APEX API."""
import os
from typing import Optional
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

# Configure Redis backend if available, fallback to memory
REDIS_URL = os.getenv("REDIS_URL", "")
STORAGE_URI = REDIS_URL if REDIS_URL.startswith(("redis://", "rediss://")) else "memory://"


def get_client_identifier(request: Request) -> str:
    """Extracts client identity from JWT token, API key, or falls back to remote IP."""
    # 1. Check API Key header
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"apikey:{api_key}"

    # 2. Check Authorization Bearer token subject
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        try:
            from backend.app.core.security import decode_access_token
            payload = decode_access_token(token)
            if payload and "sub" in payload:
                return f"user:{payload['sub']}"
        except Exception:
            pass

    # 3. Fallback to IP address
    return get_remote_address(request)


# Global distributed limiter
limiter = Limiter(
    key_func=get_client_identifier,
    default_limits=["180/minute"],
    storage_uri=STORAGE_URI,
    headers_enabled=False,  # Set False so endpoints returning dicts/models do not trigger SlowAPI response type error
)

# Standard Tier Limits
TIER_ANONYMOUS = "30/minute"
TIER_TELEMETRY_VIEWER = "120/minute"
TIER_STRATEGIST = "600/minute"
TIER_ADMIN = "3000/minute"
