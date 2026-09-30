from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    create_reset_token,
    decode_token,
)
from app.core.config import settings
from app.modules.auth.models import User, UserRole, RefreshToken
from app.modules.auth.schemas import RegisterIn
from app.shared.utils import utcnow


class AuthService:
    @staticmethod
    def get_by_email(db: Session, email: str) -> User | None:
        return db.query(User).filter(User.email == email.lower()).first()

    @staticmethod
    def register(db: Session, data: RegisterIn) -> User:
        if AuthService.get_by_email(db, data.email):
            raise HTTPException(400, "An account with this email already exists")
        user = User(
            email=data.email.lower(),
            password_hash=hash_password(data.password),
            full_name=data.full_name.strip(),
            role=UserRole(data.role),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def authenticate(db: Session, email: str, password: str) -> User:
        user = AuthService.get_by_email(db, email)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(401, "Invalid email or password")
        if not user.is_active:
            raise HTTPException(403, "This account has been deactivated")
        return user

    @staticmethod
    def issue_tokens(db: Session, user: User) -> dict:
        access = create_access_token(user.id, user.role.value)
        refresh, jti, expires = create_refresh_token(user.id)
        db.add(RefreshToken(user_id=user.id, jti=jti, expires_at=expires))
        db.commit()
        return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}

    @staticmethod
    def rotate_refresh(db: Session, refresh_token: str) -> dict:
        try:
            payload = decode_token(refresh_token)
        except Exception:
            raise HTTPException(401, "Invalid or expired refresh token")
        if payload.get("type") != "refresh":
            raise HTTPException(401, "Invalid token type")
        jti = payload["jti"]
        stored = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()
        if not stored or stored.revoked:
            raise HTTPException(401, "Refresh token has been revoked")
        user = db.get(User, int(payload["sub"]))
        if not user or not user.is_active:
            raise HTTPException(401, "User not found or inactive")
        # rotation: revoke old, issue new pair
        stored.revoked = True
        db.commit()
        return AuthService.issue_tokens(db, user)

    @staticmethod
    def change_password(db: Session, user: User, current: str, new: str) -> None:
        if not verify_password(current, user.password_hash):
            raise HTTPException(400, "Current password is incorrect")
        user.password_hash = hash_password(new)
        db.commit()
        # revoke all refresh sessions for security
        db.query(RefreshToken).filter(RefreshToken.user_id == user.id, RefreshToken.revoked.is_(False)).update({"revoked": True})
        db.commit()

    @staticmethod
    def forgot_password(db: Session, email: str) -> str | None:
        """In production this would email the token; we return it for the demo flow."""
        user = AuthService.get_by_email(db, email)
        if not user:
            return None
        return create_reset_token(user.id)

    @staticmethod
    def reset_password(db: Session, token: str, new_password: str) -> None:
        try:
            payload = decode_token(token)
        except Exception:
            raise HTTPException(400, "Reset link is invalid or has expired")
        if payload.get("type") != "reset":
            raise HTTPException(400, "Invalid reset token")
        user = db.get(User, int(payload["sub"]))
        if not user:
            raise HTTPException(400, "Account no longer exists")
        user.password_hash = hash_password(new_password)
        db.query(RefreshToken).filter(RefreshToken.user_id == user.id).update({"revoked": True})
        db.commit()
