"""Security, Cryptography, JWT Token Engine, and RBAC Permissions for APEX."""
import base64
import hashlib
import hmac
import json
import os
import time
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel

SECRET_KEY = os.getenv("APEX_JWT_SECRET", "apex-secret-key-production-f1-race-intelligence-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


class Role(str, Enum):
    VIEWER = "VIEWER"
    ANALYST = "ANALYST"
    STRATEGIST = "STRATEGIST"
    ADMIN = "ADMIN"


class Permission(str, Enum):
    VIEW_TELEMETRY = "VIEW_TELEMETRY"
    SIMULATE_RACE = "SIMULATE_RACE"
    EXECUTE_STRATEGY = "EXECUTE_STRATEGY"
    INJECT_INCIDENT = "INJECT_INCIDENT"
    ADMIN_CONFIG = "ADMIN_CONFIG"
    RETRAIN_MODELS = "RETRAIN_MODELS"


ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.VIEWER: {Permission.VIEW_TELEMETRY},
    Role.ANALYST: {Permission.VIEW_TELEMETRY, Permission.SIMULATE_RACE},
    Role.STRATEGIST: {
        Permission.VIEW_TELEMETRY,
        Permission.SIMULATE_RACE,
        Permission.EXECUTE_STRATEGY,
        Permission.INJECT_INCIDENT,
    },
    Role.ADMIN: {
        Permission.VIEW_TELEMETRY,
        Permission.SIMULATE_RACE,
        Permission.EXECUTE_STRATEGY,
        Permission.INJECT_INCIDENT,
        Permission.ADMIN_CONFIG,
        Permission.RETRAIN_MODELS,
    },
}


class TokenUser(BaseModel):
    user_id: str
    username: str
    role: Role
    permissions: List[Permission]


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64decode(data: str) -> bytes:
    padding = 4 - (len(data) % 4)
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data)


def create_jwt(payload: Dict[str, Any], secret: str = SECRET_KEY) -> str:
    """Creates a signed HMAC-SHA256 JWT string without external heavy C-dependencies."""
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = _b64encode(json.dumps(header).encode("utf-8"))
    payload_b64 = _b64encode(json.dumps(payload, default=str).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    signature_b64 = _b64encode(signature)
    return f"{header_b64}.{payload_b64}.{signature_b64}"


def decode_jwt(token: str, secret: str = SECRET_KEY) -> Optional[Dict[str, Any]]:
    """Decodes and verifies HMAC-SHA256 JWT signature and expiration."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, signature_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
        expected_sig = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
        actual_sig = _b64decode(signature_b64)
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None

        payload = json.loads(_b64decode(payload_b64).decode("utf-8"))
        # Verify expiration
        if "exp" in payload and payload["exp"] < time.time():
            return None
        return payload
    except Exception:
        return None


def create_access_token(user_id: str, username: str, role: Role) -> str:
    now = time.time()
    perms = [p.value for p in ROLE_PERMISSIONS.get(role, set())]
    payload = {
        "sub": user_id,
        "username": username,
        "role": role.value,
        "permissions": perms,
        "iat": now,
        "exp": now + (ACCESS_TOKEN_EXPIRE_MINUTES * 60),
        "type": "access",
    }
    return create_jwt(payload)


def create_refresh_token(user_id: str) -> str:
    now = time.time()
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + (REFRESH_TOKEN_EXPIRE_DAYS * 86400),
        "type": "refresh",
    }
    return create_jwt(payload)


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    return decode_jwt(token)


def hash_password(password: str) -> str:
    salt = "apex_salt_f1"
    return hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password
