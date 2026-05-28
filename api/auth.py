from datetime import datetime, timezone
import os

from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from db.session import get_db
from models.refresh_token import RefreshToken
from models.user import User
from schemas.auth import LoginRequest, RefreshTokenRequest, TokenResponse
from core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    REFRESH_TOKEN_EXPIRE_DAYS,
    SECRET_KEY,
    create_access_token,
    create_refresh_token,
    hash_token,
    verify_password,
)

router = APIRouter()

COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
COOKIE_SAMESITE = "lax"
ACCESS_COOKIE_MAX_AGE = ACCESS_TOKEN_EXPIRE_MINUTES * 60
REFRESH_COOKIE_MAX_AGE = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60


def utc_now():
    return datetime.now(timezone.utc)


def is_expired(expires_at):
    now = utc_now() if expires_at.tzinfo else datetime.utcnow()
    return expires_at < now


def create_refresh_token_record(user: User, db: Session):
    refresh_token, jti, expires_at = create_refresh_token({
        "user_id": user.id,
        "role": user.role.name
    })

    db.add(RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        jti=jti,
        expires_at=expires_at
    ))

    return refresh_token


def build_token_response(user: User, db: Session):
    access_token = create_access_token({
        "user_id": user.id,
        "role": user.role.name
    })
    refresh_token = create_refresh_token_record(user, db)
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        role=user.role.name,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


def set_auth_cookies(response: Response, token_response: TokenResponse):
    response.set_cookie(
        key="access_token",
        value=token_response.access_token,
        max_age=ACCESS_COOKIE_MAX_AGE,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=token_response.refresh_token,
        max_age=REFRESH_COOKIE_MAX_AGE,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path="/",
    )


def clear_auth_cookies(response: Response):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")


def authenticate_user(email: str, password: str, db: Session):
    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="User inactive")

    return user


# =========================
# MOBILE / WEB LOGIN (JSON)
# =========================
@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    user = authenticate_user(payload.email, payload.password, db)

    if payload.device == "web" and user.role.name == "resident":
        raise HTTPException(
            status_code=403,
            detail="Residents cannot access CMS"
        )

    if payload.device == "mobile" and user.role.name not in ["resident", "security"]:
        raise HTTPException(
            status_code=403,
            detail="Only resident or security can login from mobile"
        )

    token_response = build_token_response(user, db)
    if payload.device == "web":
        set_auth_cookies(response, token_response)

    return token_response


# =========================
# SWAGGER LOGIN (OAUTH2)
# =========================
@router.post("/token", response_model=TokenResponse)
def login_swagger(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(form_data.username, form_data.password, db)

    if user.role.name == "resident":
        raise HTTPException(
            status_code=403,
            detail="Residents cannot access CMS"
        )

    return build_token_response(user, db)


# =========================
# REFRESH ACCESS TOKEN
# =========================
@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    request: Request,
    response: Response,
    payload: RefreshTokenRequest | None = Body(default=None),
    db: Session = Depends(get_db)
):
    refresh_token_value = (
        payload.refresh_token
        if payload and payload.refresh_token
        else request.cookies.get("refresh_token")
    )
    if not refresh_token_value:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    try:
        decoded = jwt.decode(refresh_token_value, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    if decoded.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    token_row = db.query(RefreshToken).filter(
        RefreshToken.token_hash == hash_token(refresh_token_value),
        RefreshToken.jti == decoded.get("jti")
    ).first()

    if not token_row or token_row.revoked_at is not None or is_expired(token_row.expires_at):
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user = db.query(User).filter(User.id == decoded.get("user_id")).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    token_row.revoked_at = utc_now()
    token_response = build_token_response(user, db)
    set_auth_cookies(response, token_response)

    return token_response


# =========================
# LOGOUT / REVOKE REFRESH TOKEN
# =========================
@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    payload: RefreshTokenRequest | None = Body(default=None),
    db: Session = Depends(get_db)
):
    refresh_token_value = (
        payload.refresh_token
        if payload and payload.refresh_token
        else request.cookies.get("refresh_token")
    )

    if not refresh_token_value:
        clear_auth_cookies(response)
        return {"message": "Logged out successfully"}

    token_row = db.query(RefreshToken).filter(
        RefreshToken.token_hash == hash_token(refresh_token_value)
    ).first()

    if token_row and token_row.revoked_at is None:
        token_row.revoked_at = utc_now()
        db.commit()

    clear_auth_cookies(response)

    return {"message": "Logged out successfully"}
