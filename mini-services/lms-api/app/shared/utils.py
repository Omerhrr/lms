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
    """Generate a unique slug for `model` (expects `.slug` column)."""
    base = slugify(base_text)
    slug, i = base, 1
    q = db.query(model).filter(model.slug == slug)
    if exclude_id:
        q = q.filter(model.id != exclude_id)
    while q.first() is not None:
        i += 1
        slug = f"{base}-{i}"
        q = db.query(model).filter(model.slug == slug)
        if exclude_id:
            q = q.filter(model.id != exclude_id)
    return slug


def paginate(items_query, page: int, size: int):
    total = items_query.count()
    page = max(1, page)
    size = min(max(1, size), 100)
    items = items_query.limit(size).offset((page - 1) * size).all()
    return items, total, page, max(1, -(-total // size))
