import bcrypt
import jwt
import uuid
from datetime import timedelta

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


# ---------- tokens ----------

def create_access_token(user_id: int, role: str) -> str:
    now = utcnow()
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def create_refresh_token(user_id: int) -> tuple[str, str, object]:
    """Returns (token, jti, expires_at)"""
    now = utcnow()
    expires = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    jti = uuid.uuid4().hex
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": now,
        "exp": expires,
        "jti": jti,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256"), jti, expires


def create_reset_token(user_id: int) -> str:
    now = utcnow()
    payload = {
        "sub": str(user_id),
        "type": "reset",
        "iat": now,
        "exp": now + timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
