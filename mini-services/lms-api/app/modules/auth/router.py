from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.cookies import REFRESH_COOKIE, clear_auth_cookies, set_auth_cookies
from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.auth.schemas import (
    RegisterIn, LoginIn, RefreshIn, LogoutIn, ProfileUpdateIn, ChangePasswordIn,
    ForgotPasswordIn, ResetPasswordIn, SessionOut, RefreshedOut, UserOut,
)
from app.modules.auth.service import AuthService
from app.shared.utils import rate_limit, client_ip, safe_url

router = APIRouter(prefix="/auth", tags=["auth"])


def _limit(request: Request, bucket: str):
    rate_limit(f"{bucket}:{client_ip(request)}", settings.AUTH_RATE_LIMIT_PER_MINUTE)


def _wants_tokens_in_body(request: Request) -> bool:
    """Browsers get HttpOnly cookies only. Non-browser API clients (mobile apps, scripts,
    tests) can opt in to receiving tokens in the JSON body with `X-Auth-Mode: bearer`."""
    return request.headers.get("x-auth-mode", "").lower() == "bearer"


def _session_response(request: Request, response: Response, tokens: dict, user: User | None = None) -> dict:
    set_auth_cookies(response, tokens["access_token"], tokens["refresh_token"])
    body: dict = {"user": user} if user is not None else {}
    if _wants_tokens_in_body(request):
        body.update(tokens)
    return body


@router.post("/register", response_model=SessionOut, response_model_exclude_none=True, status_code=201)
def register(data: RegisterIn, request: Request, response: Response, db: Session = Depends(get_db)):
    _limit(request, "register")
    user = AuthService.register(db, data)
    return _session_response(request, response, AuthService.issue_tokens(db, user), user)


@router.post("/login", response_model=SessionOut, response_model_exclude_none=True)
def login(data: LoginIn, request: Request, response: Response, db: Session = Depends(get_db)):
    _limit(request, "login")
    rate_limit(f"login-email:{data.email.lower()}", settings.AUTH_RATE_LIMIT_PER_MINUTE)
    user = AuthService.authenticate(db, data.email, data.password)
    return _session_response(request, response, AuthService.issue_tokens(db, user), user)


@router.post("/refresh", response_model=RefreshedOut, response_model_exclude_none=True)
def refresh(request: Request, response: Response, data: RefreshIn | None = None, db: Session = Depends(get_db)):
    rate_limit(f"refresh:{client_ip(request)}", 60)
    token = (data.refresh_token if data else None) or request.cookies.get(REFRESH_COOKIE)
    if not token:
        raise HTTPException(401, "No session")
    try:
        tokens = AuthService.rotate_refresh(db, token)
    except HTTPException:
        clear_auth_cookies(response)
        raise
    return _session_response(request, response, tokens)


@router.post("/logout")
def logout(request: Request, response: Response, data: LogoutIn | None = None, db: Session = Depends(get_db)):
    AuthService.revoke_refresh(db, (data.refresh_token if data else None) or request.cookies.get(REFRESH_COOKIE))
    clear_auth_cookies(response)
    return {"message": "Signed out"}


@router.post("/logout-all")
def logout_all(response: Response, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    AuthService.revoke_all_sessions(db, user.id)
    clear_auth_cookies(response)
    return {"message": "Signed out on every device"}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.put("/me", response_model=UserOut)
def update_profile(data: ProfileUpdateIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    values = data.model_dump(exclude_unset=True)
    if "avatar_url" in values:
        values["avatar_url"] = safe_url(values["avatar_url"], "avatar_url")
    for field, value in values.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


@router.post("/change-password", status_code=200)
def change_password(data: ChangePasswordIn, response: Response, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    AuthService.change_password(db, user, data.current_password, data.new_password)
    clear_auth_cookies(response)
    return {"message": "Password updated. Please sign in again."}


@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordIn, request: Request, db: Session = Depends(get_db)):
    _limit(request, "forgot")
    AuthService.forgot_password(db, data.email)
    # identical response whether or not the account exists (no user enumeration)
    return {"message": "If an account exists for that email, a reset link has been sent."}


@router.post("/reset-password")
def reset_password(data: ResetPasswordIn, request: Request, db: Session = Depends(get_db)):
    _limit(request, "reset")
    AuthService.reset_password(db, data.token, data.new_password)
    return {"message": "Password has been reset. You can now sign in."}
