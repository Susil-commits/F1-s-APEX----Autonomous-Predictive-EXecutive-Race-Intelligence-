"""Authentication and RBAC Endpoints & Security Dependencies for APEX."""
from typing import Callable, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from backend.app.core.security import (
    Permission,
    ROLE_PERMISSIONS,
    Role,
    TokenUser,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_jwt,
    hash_password,
    verify_password,
)

auth_router = APIRouter(prefix="/api/auth", tags=["Authentication & RBAC"])
security_bearer = HTTPBearer(auto_error=False)

# Seed in-memory demo user credentials
DEMO_USERS: Dict[str, Dict[str, str]] = {
    "admin@apex.f1": {
        "user_id": "usr-admin-01",
        "username": "chief_strategist_admin",
        "password_hash": hash_password("apex_admin_2026"),
        "role": Role.ADMIN.value,
    },
    "strategist@apex.f1": {
        "user_id": "usr-strat-02",
        "username": "race_strategist",
        "password_hash": hash_password("strategy_win_2026"),
        "role": Role.STRATEGIST.value,
    },
    "analyst@apex.f1": {
        "user_id": "usr-analyst-03",
        "username": "telemetry_analyst",
        "password_hash": hash_password("analyst_data_2026"),
        "role": Role.ANALYST.value,
    },
    "guest@apex.f1": {
        "user_id": "usr-guest-04",
        "username": "fan_viewer",
        "password_hash": hash_password("guest_view_2026"),
        "role": Role.VIEWER.value,
    },
}


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: TokenUser


@auth_router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    """Authenticates user credentials and issues signed JWT access and refresh tokens."""
    user_record = DEMO_USERS.get(req.email.lower().strip())
    if not user_record or not verify_password(req.password, user_record["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Please verify email and password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    role = Role(user_record["role"])
    access_token = create_access_token(user_record["user_id"], user_record["username"], role)
    refresh_token = create_refresh_token(user_record["user_id"])

    token_user = TokenUser(
        user_id=user_record["user_id"],
        username=user_record["username"],
        role=role,
        permissions=list(ROLE_PERMISSIONS.get(role, set())),
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=token_user,
    )


@auth_router.post("/refresh")
async def refresh_token(req: RefreshRequest):
    """Refreshes an expired access token using a valid refresh token."""
    payload = decode_jwt(req.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )

    user_id = payload.get("sub")
    # Find matching user
    matched_user = next((u for u in DEMO_USERS.values() if u["user_id"] == user_id), None)
    if not matched_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")

    role = Role(matched_user["role"])
    new_access_token = create_access_token(matched_user["user_id"], matched_user["username"], role)
    return {"access_token": new_access_token, "token_type": "bearer"}


@auth_router.get("/demo-tokens")
async def get_demo_tokens():
    """Returns pre-generated access tokens for all RBAC roles for rapid local test evaluation."""
    tokens = {}
    for email, user in DEMO_USERS.items():
        role = Role(user["role"])
        tokens[role.value] = {
            "email": email,
            "username": user["username"],
            "role": role.value,
            "access_token": create_access_token(user["user_id"], user["username"], role),
            "permissions": [p.value for p in ROLE_PERMISSIONS.get(role, set())],
        }
    return tokens


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
) -> TokenUser:
    """FastAPI dependency to extract and validate the JWT Bearer token."""
    if not credentials or not credentials.credentials:
        # Default to Guest Viewer for unauthenticated requests
        return TokenUser(
            user_id="anon-guest",
            username="anonymous_guest",
            role=Role.VIEWER,
            permissions=list(ROLE_PERMISSIONS[Role.VIEWER]),
        )

    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    role = Role(payload.get("role", Role.VIEWER.value))
    perms = [Permission(p) for p in payload.get("permissions", [])]
    return TokenUser(
        user_id=payload.get("sub", "unknown"),
        username=payload.get("username", "unknown"),
        role=role,
        permissions=perms,
    )


def require_role(required_role: Role) -> Callable:
    """Dependency factory ensuring the user has a minimum RBAC role."""
    async def role_checker(current_user: TokenUser = Depends(get_current_user)) -> TokenUser:
        hierarchy = [Role.VIEWER, Role.ANALYST, Role.STRATEGIST, Role.ADMIN]
        user_level = hierarchy.index(current_user.role)
        required_level = hierarchy.index(required_role)

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Action requires '{required_role.value}' role. Your role is '{current_user.role.value}'.",
            )
        return current_user

    return role_checker


def require_permission(required_perm: Permission) -> Callable:
    """Dependency factory ensuring the user possesses a specific permission."""
    async def perm_checker(current_user: TokenUser = Depends(get_current_user)) -> TokenUser:
        if required_perm not in current_user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Missing permission '{required_perm.value}'.",
            )
        return current_user

    return perm_checker


@auth_router.get("/me", response_model=TokenUser)
async def get_me(current_user: TokenUser = Depends(get_current_user)):
    """Returns profile and active permissions of the authenticated user."""
    return current_user
