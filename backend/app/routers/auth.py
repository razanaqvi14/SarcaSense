from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..deps import get_current_user
from ..models import User
from ..ratelimit import limiter
from ..schemas import Credentials, DeleteAccountRequest, RegisterRequest, UserOut
from ..security import (
    COOKIE_NAME,
    create_access_token,
    hash_password,
    needs_rehash,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
_settings = get_settings()


def _set_session_cookie(response: Response, user_id: int) -> None:
    response.set_cookie(
        COOKIE_NAME,
        create_access_token(user_id),
        max_age=_settings.access_token_minutes * 60,
        httponly=True,
        secure=_settings.cookie_secure,
        samesite="strict",
        path="/api",
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
@limiter.limit(_settings.rate_limit_register)
def register(
    request: Request, body: RegisterRequest, response: Response, db: Session = Depends(get_db)
):
    user = User(email=body.email, password_hash=hash_password(body.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    _set_session_cookie(response, user.id)
    return user


@router.post("/login", response_model=UserOut)
@limiter.limit(_settings.rate_limit_login)
def login(
    request: Request, body: Credentials, response: Response, db: Session = Depends(get_db)
):
    user = db.scalar(select(User).where(User.email == body.email))
    ok = verify_password(body.password, user.password_hash if user else None)
    if not (user and ok and user.is_active):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(body.password)
        db.commit()
    _set_session_cookie(response, user.id)
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    # Tokens are stateless; logout clears the cookie. They expire on their own.
    response.delete_cookie(COOKIE_NAME, path="/api")
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/delete-account", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(_settings.rate_limit_login)
def delete_account(
    request: Request,
    body: DeleteAccountRequest,
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid password")
    db.delete(user)
    db.commit()
    response.delete_cookie(COOKIE_NAME, path="/api")
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
