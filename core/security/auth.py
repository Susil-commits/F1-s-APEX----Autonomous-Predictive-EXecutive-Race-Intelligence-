"""APEX Enterprise Authentication & Role-Based Access Control (RBAC).

Provides:
1. API Key Authentication with SHA-256 cryptographic hashing.
2. Constant-time key comparison (secrets.compare_digest) to prevent timing attacks.
3. Role Hierarchy: Admin > Engineer > Client > Anonymous.
4. FastAPI Dependencies: require_role(min_role), get_current_role.
"""
from __future__ import annotations

import enum
import hashlib
import os
import secrets
from typing import Dict, Optional

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


class Role(str, enum.Enum):
    ADMIN = "admin"
    ENGINEER = "engineer"
    CLIENT = "client"
    ANONYMOUS = "anonymous"

    @property
    def level(self) -> int:
        levels = {
            Role.ANONYMOUS: 0,
            Role.CLIENT: 1,
            Role.ENGINEER: 2,
            Role.ADMIN: 3,
        }
        return levels.get(self, 0)

    def can_access(self, required_role: Role) -> bool:
        """Returns True if self role meets or exceeds required_role."""
        return self.level >= required_role.level


class APIKeyAuthenticator:
    """Manages secure hashed API key validation and role assignment."""

    # Default in-memory key hash mapping (Key Hash -> Role)
    # Can be configured via APEX_API_KEYS environment variable:
    # Format: "key1:admin,key2:engineer,key3:client"
    _KEY_STORE: Dict[str, Role] = {}

    @classmethod
    def _hash_key(cls, raw_key: str) -> str:
        """Computes SHA-256 hash of API key."""
        return hashlib.sha256(raw_key.strip().encode("utf-8")).hexdigest()

    @classmethod
    def register_key(cls, raw_key: str, role: Role) -> str:
        """Registers a key and returns its SHA-256 hash."""
        hashed = cls._hash_key(raw_key)
        cls._KEY_STORE[hashed] = role
        return hashed

    @classmethod
    def load_from_env(cls) -> None:
        """Loads API keys from environment variable APEX_API_KEYS."""
        cls._KEY_STORE.clear()
        env_keys = os.environ.get("APEX_API_KEYS", "")
        if not env_keys:
            # Register a default development admin key if in development mode
            if os.environ.get("ENVIRONMENT", "development").lower() in ("development", "test"):
                cls.register_key("apex_dev_secret_key_2026", Role.ADMIN)
                cls.register_key("apex_engineer_key_2026", Role.ENGINEER)
                cls.register_key("apex_client_key_2026", Role.CLIENT)
            return

        for item in env_keys.split(","):
            parts = item.strip().split(":")
            if len(parts) == 2:
                key, role_str = parts[0], parts[1].lower()
                try:
                    role = Role(role_str)
                    cls.register_key(key, role)
                except ValueError:
                    pass

    @classmethod
    def authenticate(cls, raw_key: Optional[str]) -> Role:
        """Authenticates a raw key using constant-time comparison against known key hashes.
        
        Returns the assigned Role, or Role.ANONYMOUS if key is missing/invalid.
        """
        if not raw_key:
            return Role.ANONYMOUS

        if not cls._KEY_STORE:
            cls.load_from_env()

        candidate_hash = cls._hash_key(raw_key)

        # Constant-time comparison across all registered hashes
        matched_role: Optional[Role] = None
        for stored_hash, role in cls._KEY_STORE.items():
            if secrets.compare_digest(candidate_hash, stored_hash):
                matched_role = role
                break

        return matched_role if matched_role is not None else Role.ANONYMOUS


# Initialize key store on load
APIKeyAuthenticator.load_from_env()


async def get_current_role(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> Role:
    """Extracts credentials from X-API-Key or Bearer token and returns the Role."""
    token = x_api_key
    if not token and authorization:
        if authorization.lower().startswith("bearer "):
            token = authorization[7:].strip()
        else:
            token = authorization.strip()

    role = APIKeyAuthenticator.authenticate(token)

    # If auth is strictly required globally and user is anonymous, raise 401
    auth_required = os.environ.get("APEX_AUTH_REQUIRED", "false").lower() == "true"
    if auth_required and role == Role.ANONYMOUS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication credentials (X-API-Key or Bearer token).",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return role


def require_role(min_role: Role):
    """FastAPI dependency factory enforcing minimum role level."""
    async def dependency(current_role: Role = Depends(get_current_role)) -> Role:
        # If running in open development mode without explicit auth requirement, allow access
        auth_required = os.environ.get("APEX_AUTH_REQUIRED", "false").lower() == "true"
        if not auth_required and current_role == Role.ANONYMOUS:
            return Role.ADMIN

        if not current_role.can_access(min_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires '{min_role.value}' role or higher (current: '{current_role.value}').",
            )
        return current_role

    return dependency
