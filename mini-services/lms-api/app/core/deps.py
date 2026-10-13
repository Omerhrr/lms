"""Shared auth dependencies (roles, current user)."""
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.cookies import ACCESS_COOKIE
from app.core.database import get_db
from app.core.security import decode_token
from app.modules.auth.models import User

bearer_scheme = HTTPBearer(auto_error=False)


def _token(request: Request, creds: HTTPAuthorizationCredentials | None) -> str | None:
    """Browser sessions use the HttpOnly cookie; API clients/tests may send a Bearer header."""
    if creds is not None and creds.credentials:
        return creds.credentials
    return request.cookies.get(ACCESS_COOKIE)


def get_current_user(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    token = _token(request, creds)
    if not token:
        raise unauthorized
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    if payload.get("type") != "access":
        raise unauthorized
    user = db.get(User, int(payload["sub"]))
    if user is None or not user.is_active or payload.get("ver", 0) != (user.token_version or 0):
        raise unauthorized
    return user


def require_roles(*roles: str):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not have permission to perform this action")
        return user
    return checker


def get_optional_user(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """Like get_current_user but returns None for anonymous visitors (public pages)."""
    token = _token(request, creds)
    if not token:
        return None
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            return None
        user = db.get(User, int(payload["sub"]))
        if user is None or not user.is_active or payload.get("ver", 0) != (user.token_version or 0):
            return None
        return user
    except Exception:
        return None


# Convenience guards
admin_required = require_roles("admin")
staff_required = require_roles("instructor", "admin")   # instructor OR admin
any_user = get_current_user
optional_user = get_optional_user
