"""Pytest suite for JWT authentication, refresh tokens, and RBAC permission enforcement."""
import time
import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.core.security import (
    Permission,
    ROLE_PERMISSIONS,
    Role,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_jwt,
    hash_password,
    verify_password,
)
from backend.app.main import app


def test_password_hashing():
    pwd = "secret_pitwall_password_2026"
    hashed = hash_password(pwd)
    assert verify_password(pwd, hashed) is True
    assert verify_password("wrong_password", hashed) is False


def test_jwt_token_generation_and_decoding():
    token = create_access_token("usr-123", "lewis_hamilton", Role.STRATEGIST)
    assert isinstance(token, str)
    assert len(token.split(".")) == 3

    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "usr-123"
    assert payload["username"] == "lewis_hamilton"
    assert payload["role"] == Role.STRATEGIST.value
    assert Permission.EXECUTE_STRATEGY.value in payload["permissions"]


def test_rbac_permission_matrix():
    admin_perms = ROLE_PERMISSIONS[Role.ADMIN]
    assert Permission.ADMIN_CONFIG in admin_perms
    assert Permission.RETRAIN_MODELS in admin_perms
    assert Permission.EXECUTE_STRATEGY in admin_perms

    viewer_perms = ROLE_PERMISSIONS[Role.VIEWER]
    assert Permission.VIEW_TELEMETRY in viewer_perms
    assert Permission.EXECUTE_STRATEGY not in viewer_perms
    assert Permission.ADMIN_CONFIG not in viewer_perms


@pytest.mark.asyncio
async def test_auth_api_login_and_me():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Test valid login
        res = await ac.post(
            "/api/auth/login",
            json={"email": "admin@apex.f1", "password": "apex_admin_2026"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["role"] == "ADMIN"

        # Test authenticated /api/auth/me
        token = data["access_token"]
        me_res = await ac.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_res.status_code == 200
        me_data = me_res.json()
        assert me_data["username"] == "chief_strategist_admin"

        # Test invalid credentials
        bad_res = await ac.post(
            "/api/auth/login",
            json={"email": "admin@apex.f1", "password": "wrong_password"},
        )
        assert bad_res.status_code == 401
