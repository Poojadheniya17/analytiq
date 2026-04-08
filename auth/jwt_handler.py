# auth/jwt_handler.py
# Analytiq — JWT token creation and verification

import os
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Request

SECRET_KEY  = os.environ.get("JWT_SECRET", "analytiq-dev-secret-change-in-production")
ALGORITHM   = "HS256"
ACCESS_EXP  = 60 * 24 * 7  # 7 days in minutes


def create_access_token(user_id: int, username: str) -> str:
    payload = {
        "sub":      str(user_id),
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_EXP),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired. Please sign in again.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token. Please sign in again.")


def get_token_from_request(request: Request) -> str | None:
    # Check cookie first (most secure)
    token = request.cookies.get("analytiq_token")
    if token:
        return token
    # Fall back to Authorization header
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return None


def get_current_user(request: Request) -> dict:
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated. Please sign in.")
    return verify_token(token)
