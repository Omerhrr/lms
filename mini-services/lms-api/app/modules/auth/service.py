import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import (
    hash_password,
    verify_password,
    password_fingerprint,
    create_access_token,
    create_refresh_token,
    create_reset_token,
    decode_token,
)
from app.modules.auth.models import User, UserRole, RefreshToken
from app.modules.auth.schemas import RegisterIn

log = logging.getLogger("lms.auth")


class AuthService:
    @staticmethod
    def get_by_email(db: Session, email: str) -> User | None:
        return db.query(User).filter(User.email == email.strip().lower()).first()

    @staticmethod
    def register(db: Session, data: RegisterIn) -> User:
        if AuthService.get_by_email(db, data.email):
            raise HTTPException(400, "An account with this email already exists")
        # Self-service sign-up always creates a student. Asking to teach only flags the
        # account; an admin grants the instructor role from the user management screen.
        user = User(
            email=data.email.strip().lower(),
            password_hash=hash_password(data.password),
            full_name=data.full_name.strip(),
            role=UserRole.student,
            instructor_requested=(data.role == "instructor"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        from app.shared import emails
        emails.welcome(user.email, user.full_name, user.instructor_requested)
        if user.instructor_requested:
            from app.modules.notifications.service import notify
            for admin in db.query(User).filter(User.role == UserRole.admin, User.is_active.is_(True)).all():
                notify(db, admin.id, "system", "Instructor access requested",
                       f"{user.full_name} ({user.email}) asked to become an instructor.", "/admin/users")
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
        access = create_access_token(user.id, user.role.value, user.token_version or 0)
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
        stored = db.query(RefreshToken).filter(RefreshToken.jti == payload.get("jti")).first()
        if not stored:
            raise HTTPException(401, "Refresh token has been revoked")
        if stored.revoked:
            # A rotated token was replayed: likely stolen. Kill every session for this user.
            AuthService.revoke_all_sessions(db, stored.user_id)
            raise HTTPException(401, "Refresh token has been revoked")
        user = db.get(User, int(payload["sub"]))
        if not user or not user.is_active:
            raise HTTPException(401, "User not found or inactive")
        stored.revoked = True
        db.commit()
        return AuthService.issue_tokens(db, user)

    @staticmethod
    def revoke_refresh(db: Session, refresh_token: str | None) -> None:
        if not refresh_token:
            return
        try:
            payload = decode_token(refresh_token)
        except Exception:
            return
        db.query(RefreshToken).filter(RefreshToken.jti == payload.get("jti")).update({"revoked": True})
        db.commit()

    @staticmethod
    def revoke_all_sessions(db: Session, user_id: int) -> None:
        """Invalidate every refresh token AND every outstanding access token."""
        db.query(RefreshToken).filter(RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False)) \
            .update({"revoked": True})
        user = db.get(User, user_id)
        if user:
            user.token_version = (user.token_version or 0) + 1
        db.commit()

    @staticmethod
    def change_password(db: Session, user: User, current: str, new: str) -> None:
        if not verify_password(current, user.password_hash):
            raise HTTPException(400, "Current password is incorrect")
        user.password_hash = hash_password(new)
        db.commit()
        AuthService.revoke_all_sessions(db, user.id)

    @staticmethod
    def forgot_password(db: Session, email: str) -> None:
        """Create a reset token and email it. Never returned to the caller.
        Without SMTP configured, the email (and link) is written to the API log."""
        user = AuthService.get_by_email(db, email)
        if not user or not user.is_active:
            return
        token = create_reset_token(user.id, user.password_hash)
        from app.shared import emails
        emails.password_reset(user.email, user.full_name, token)

    @staticmethod
    def reset_password(db: Session, token: str, new_password: str) -> None:
        invalid = HTTPException(400, "Reset link is invalid or has expired")
        try:
            payload = decode_token(token)
        except Exception:
            raise invalid
        if payload.get("type") != "reset":
            raise invalid
        user = db.get(User, int(payload["sub"]))
        # fingerprint check makes the token single-use (it dies once the password changes)
        if not user or payload.get("pwd") != password_fingerprint(user.password_hash):
            raise invalid
        user.password_hash = hash_password(new_password)
        db.commit()
        AuthService.revoke_all_sessions(db, user.id)
