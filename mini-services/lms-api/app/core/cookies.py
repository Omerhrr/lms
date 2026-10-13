"""Session cookies.

Tokens live only in HttpOnly cookies, so JavaScript on the page (including any injected
script) can't read or steal them. A third, non-secret cookie `lh_session=1` just tells the
frontend "a session probably exists" so it can skip a pointless /auth/me call for visitors.
"""
from fastapi import Response

from app.core.config import settings

ACCESS_COOKIE = "lh_access"
REFRESH_COOKIE = "lh_refresh"
HINT_COOKIE = "lh_session"


def _common() -> dict:
    return {"secure": settings.cookie_secure, "samesite": settings.COOKIE_SAMESITE}


def set_auth_cookies(response: Response, access: str, refresh: str) -> None:
    response.set_cookie(ACCESS_COOKIE, access, httponly=True, path="/api",
                        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, **_common())
    # the refresh token is only ever sent to the auth endpoints
    response.set_cookie(REFRESH_COOKIE, refresh, httponly=True, path="/api/auth",
                        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400, **_common())
    response.set_cookie(HINT_COOKIE, "1", httponly=False, path="/",
                        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400, **_common())


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE, path="/api", **_common())
    response.delete_cookie(REFRESH_COOKIE, path="/api/auth", **_common())
    response.delete_cookie(HINT_COOKIE, path="/", **_common())
