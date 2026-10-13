import hashlib
import uuid
from datetime import timedelta

import bcrypt
import jwt

from app.core.config import settings
from app.shared.utils import utcnow


# ---------- passwords ----------

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def password_fingerprint(password_hash: str) -> str:
    """Short digest of the current password hash. Embedding it in a reset token makes
    the token single-use: once the password changes, the fingerprint no longer matches."""
    return hashlib.sha256(password_hash.encode("utf-8")).hexdigest()[:16]


# ---------- tokens ----------

def _encode(payload: dict) -> str:
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def create_access_token(user_id: int, role: str, token_version: int = 0) -> str:
    now = utcnow()
    return _encode({
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "ver": token_version,
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "jti": uuid.uuid4().hex,
    })


def create_refresh_token(user_id: int) -> tuple[str, str, object]:
    """Returns (token, jti, expires_at)"""
    now = utcnow()
    expires = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    jti = uuid.uuid4().hex
    token = _encode({"sub": str(user_id), "type": "refresh", "iat": now, "exp": expires, "jti": jti})
    return token, jti, expires


def create_reset_token(user_id: int, password_hash: str) -> str:
    now = utcnow()
    return _encode({
        "sub": str(user_id),
        "type": "reset",
        "pwd": password_fingerprint(password_hash),
        "iat": now,
        "exp": now + timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES),
    })


def create_quiz_session_token(quiz_id: int, user_id: int) -> str:
    """Signed start-time for timed quizzes, so the time limit is enforced server-side."""
    now = utcnow()
    return _encode({"type": "quiz", "quiz": quiz_id, "sub": str(user_id), "iat": now,
                    "exp": now + timedelta(days=1)})


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
