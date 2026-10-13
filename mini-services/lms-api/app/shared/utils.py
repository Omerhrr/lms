"""Shared helpers used across modules."""
import re
import unicodedata
from datetime import datetime, timezone


def utcnow() -> datetime:
    """Naive UTC timestamp (SQLite-friendly, consistent everywhere)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    text = re.sub(r"[-_\s]+", "-", text)
    return text or "item"


def unique_slug(db, model, base_text: str, exclude_id: int | None = None) -> str:
    """Generate a unique slug for `model` (expects `.slug` column) with one query."""
    base = slugify(base_text)[:200]
    q = db.query(model.slug).filter((model.slug == base) | (model.slug.like(f"{base}-%")))
    if exclude_id:
        q = q.filter(model.id != exclude_id)
    taken = {row[0] for row in q.all()}
    if base not in taken:
        return base
    i = 2
    while f"{base}-{i}" in taken:
        i += 1
    return f"{base}-{i}"


def paginate(items_query, page: int, size: int):
    total = items_query.count()
    page = max(1, page)
    size = min(max(1, size), 100)
    items = items_query.limit(size).offset((page - 1) * size).all()
    return items, total, page, max(1, -(-total // size))


# ---------- input safety ----------

from fastapi import HTTPException  # noqa: E402

_SAFE_URL_PREFIXES = ("https://", "http://", "/api/media/files/")


def safe_url(value, field: str = "url"):
    """Allow only http(s) links and our own uploaded media. Blocks javascript:, data:, etc.
    Returns None for empty values; raises 400 for anything else."""
    if value is None:
        return None
    value = str(value).strip()
    if not value:
        return None
    if len(value) > 1000 or any(c in value for c in "\r\n\t\x00") or not value.lower().startswith(_SAFE_URL_PREFIXES):
        raise HTTPException(400, f"{field} must be an http(s) link or an uploaded file")
    if value.startswith("/api/media/files/") and (".." in value or "//" in value[1:]):
        raise HTTPException(400, f"{field} is not a valid uploaded file path")
    return value


_ALLOWED_TAGS = {
    "p", "br", "h1", "h2", "h3", "h4", "strong", "b", "em", "i", "u", "s", "ul", "ol", "li",
    "blockquote", "code", "pre", "a", "hr", "span", "img",
}


def sanitize_html(value: str | None) -> str | None:
    """Strip scripts, event handlers and dangerous URLs from instructor-authored HTML."""
    if value is None:
        return None
    import nh3
    return nh3.clean(
        value,
        tags=_ALLOWED_TAGS,
        attributes={"a": {"href", "title"}, "img": {"src", "alt"}},
        url_schemes={"http", "https", "mailto"},
        link_rel="noopener noreferrer nofollow",
    )


# ---------- tiny in-memory rate limiter (per process) ----------

import threading  # noqa: E402
import time  # noqa: E402
from collections import defaultdict, deque  # noqa: E402

_hits: dict[str, deque] = defaultdict(deque)
_hits_lock = threading.Lock()


def rate_limit(key: str, limit: int, window_seconds: int = 60) -> None:
    """Raise 429 when `key` was seen more than `limit` times in the window.
    Good enough for a single process; use Redis or a gateway when scaling out."""
    now = time.monotonic()
    with _hits_lock:
        q = _hits[key]
        while q and now - q[0] > window_seconds:
            q.popleft()
        if len(q) >= limit:
            raise HTTPException(429, "Too many attempts. Please wait a minute and try again.")
        q.append(now)


def client_ip(request) -> str:
    """Real client IP. Behind the website's /api proxy every request comes from the proxy,
    so trust its forwarded IP header - but only when it proves itself with the shared secret."""
    import hmac
    from app.core.config import settings
    if request is None:
        return "unknown"
    secret = settings.PROXY_SHARED_SECRET
    sent = request.headers.get("x-lh-proxy-secret", "")
    if secret and sent and hmac.compare_digest(sent, secret):
        forwarded = request.headers.get("x-lh-client-ip", "").strip()
        if forwarded:
            return forwarded[:64]
    return request.client.host if request.client else "unknown"


def sanitize_rich_content(value: str | None) -> str | None:
    """Lesson bodies: HTML from the rich editor is sanitized; legacy plain text is kept as-is
    (the frontend renders it as text, so it can't inject markup)."""
    if value is None or "<" not in value:
        return value
    return sanitize_html(value)
