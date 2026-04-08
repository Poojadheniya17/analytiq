# backend/routers/auth.py
# Analytiq — Auth router with JWT + secure cookies

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from fastapi import APIRouter, HTTPException, Response, Request, Depends
from pydantic import BaseModel
from auth.auth import login, signup
from database.connection import init_db
from auth.jwt_handler import create_access_token, get_current_user
from auth.rate_limiter import check_rate_limit

router = APIRouter()
init_db()

COOKIE_NAME  = "analytiq_token"
IS_PROD      = os.environ.get("ENV", "development") == "production"


class LoginRequest(BaseModel):
    username: str
    password: str

class SignupRequest(BaseModel):
    username: str
    email:    str
    password: str


@router.post("/login")
def login_user(req: LoginRequest, response: Response, request: Request):
    check_rate_limit(request)

    if not req.username or not req.password:
        raise HTTPException(status_code=400, detail="Username and password are required.")

    success, msg, user = login(req.username.strip(), req.password)
    if not success:
        raise HTTPException(status_code=401, detail=msg)

    # Create JWT and set as httpOnly cookie
    token = create_access_token(user["id"], user["username"])
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,           # JS cannot read this — prevents XSS
        secure=IS_PROD,          # HTTPS only in production
        samesite="lax",          # CSRF protection
        max_age=60 * 60 * 24 * 7 # 7 days
    )
    return {"user": user, "message": msg}


@router.post("/signup")
def signup_user(req: SignupRequest, request: Request):
    check_rate_limit(request)

    if not req.username or not req.email or not req.password:
        raise HTTPException(status_code=400, detail="All fields are required.")

    success, msg = signup(req.username.strip(), req.email.strip(), req.password)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg}


@router.post("/logout")
def logout_user(response: Response):
    response.delete_cookie(key=COOKIE_NAME)
    return {"message": "Logged out successfully."}


@router.get("/me")
def get_me(request: Request):
    payload = get_current_user(request)
    return {"user": {
        "id":       int(payload["sub"]),
        "username": payload["username"]
    }}