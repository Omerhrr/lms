from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.auth.schemas import (
    RegisterIn, LoginIn, RefreshIn, ProfileUpdateIn, ChangePasswordIn,
    ForgotPasswordIn, ResetPasswordIn, AuthTokensOut, RefreshedOut, UserOut,
)
from app.modules.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthTokensOut, status_code=201)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    user = AuthService.register(db, data)
    tokens = AuthService.issue_tokens(db, user)
    return {**tokens, "user": user}


@router.post("/login", response_model=AuthTokensOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = AuthService.authenticate(db, data.email, data.password)
    tokens = AuthService.issue_tokens(db, user)
    return {**tokens, "user": user}


@router.post("/refresh", response_model=RefreshedOut)
def refresh(data: RefreshIn, db: Session = Depends(get_db)):
    return AuthService.rotate_refresh(db, data.refresh_token)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.put("/me", response_model=UserOut)
def update_profile(data: ProfileUpdateIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


@router.post("/change-password", status_code=200)
def change_password(data: ChangePasswordIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    AuthService.change_password(db, user, data.current_password, data.new_password)
    return {"message": "Password updated. Please sign in again."}


@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordIn, db: Session = Depends(get_db)):
    token = AuthService.forgot_password(db, data.email)
    # In production: email the token. Demo returns it so the flow is testable.
    if token:
        return {"message": "Reset token generated", "reset_token": token}
    return {"message": "If an account exists for that email, a reset link has been sent."}


@router.post("/reset-password")
def reset_password(data: ResetPasswordIn, db: Session = Depends(get_db)):
    AuthService.reset_password(db, data.token, data.new_password)
    return {"message": "Password has been reset. You can now sign in."}
