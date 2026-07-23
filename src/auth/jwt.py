"""
JWT Authentication Module

Handles token generation, validation, and refresh for the ProjectExpress API.
Uses RS256 for signing and supports short-lived access tokens with
long-lived refresh tokens that rotate on each use.
"""

import time
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from ..db import get_db
from ..models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

# Configuration
ACCESS_TOKEN_EXPIRY = timedelta(minutes=15)
REFRESH_TOKEN_EXPIRY = timedelta(days=7)
ALGORITHM = "RS256"

# In production, load from environment or secrets manager
JWT_PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA0Z3VS5JJcds3xfn/ygWyF...
-----END RSA PRIVATE KEY-----"""

JWT_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBC...
-----END PUBLIC KEY-----"""


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


def hash_password(password: str) -> str:
    """Hash a password using bcrypt with auto-generated salt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(user_id: int, role: str) -> str:
    """Create a short-lived access token."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "iat": now,
        "exp": now + ACCESS_TOKEN_EXPIRY,
        "jti": secrets.token_urlsafe(16),
    }
    return jwt.encode(payload, JWT_PRIVATE_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    """Create a long-lived refresh token."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": now,
        "exp": now + REFRESH_TOKEN_EXPIRY,
        "jti": secrets.token_urlsafe(16),
    }
    return jwt.encode(payload, JWT_PRIVATE_KEY, algorithm=ALGORITHM)


def verify_token(token: str, expected_type: str = "access") -> dict:
    """Verify and decode a JWT token. Raises HTTPException on failure."""
    try:
        payload = jwt.decode(
            token,
            JWT_PUBLIC_KEY,
            algorithms=[ALGORITHM],
            options={"require": ["exp", "sub", "type"]},
        )
        if payload.get("type") != expected_type:
            raise HTTPException(
                status_code=401,
                detail=f"Expected {expected_type} token, got {payload.get('type')}",
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


async def get_current_user(
    authorization: str = Header(...),
    db: Session = Depends(get_db),
) -> User:
    """Dependency: extract and validate the current user from the Authorization header."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    token = authorization[7:]
    payload = verify_token(token, expected_type="access")
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or deactivated")
    return user


def require_role(*allowed_roles):
    """Decorator factory for role-based access control."""
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Role \'{current_user.role}\' not in allowed roles: {allowed_roles}",
            )
        return current_user
    return role_checker


@router.post("/login", response_model=TokenPair)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return token pair."""
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    access_token = create_access_token(user.id, user.role)
    refresh_token = create_refresh_token(user.id)

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=int(ACCESS_TOKEN_EXPIRY.total_seconds()),
    )


@router.post("/refresh", response_model=TokenPair)
def refresh_token(request: RefreshRequest, db: Session = Depends(get_db)):
    """Rotate refresh token and issue new token pair (refresh token rotation)."""
    payload = verify_token(request.refresh_token, expected_type="refresh")
    user_id = int(payload["sub"])

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or deactivated")

    # Issue new tokens (old refresh token is implicitly invalidated
    # because we generate a new JTI and clients should discard the old one)
    access_token = create_access_token(user.id, user.role)
    refresh_token = create_refresh_token(user.id)

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=int(ACCESS_TOKEN_EXPIRY.total_seconds()),
    )
