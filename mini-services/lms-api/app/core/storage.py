"""Where uploaded files go.

Local disk (served at /api/media/files/...) for development. On Vercel the filesystem is
read-only and temporary, so set SUPABASE_URL + SUPABASE_SERVICE_KEY and files go to a public
Supabase Storage bucket instead (create the bucket once and mark it Public).
"""
import os

import httpx
from fastapi import HTTPException

from app.core.config import settings

CONTENT_TYPES = {
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif",
    ".webp": "image/webp", ".ico": "image/x-icon", ".pdf": "application/pdf",
    ".mp4": "video/mp4", ".webm": "video/webm", ".mp3": "audio/mpeg", ".wav": "audio/wav",
    ".txt": "text/plain", ".csv": "text/csv", ".zip": "application/zip",
}


def save_upload(filename: str, data: bytes, ext: str) -> str:
    """Store the bytes and return the public URL."""
    if settings.use_supabase_storage:
        base = settings.SUPABASE_URL.rstrip("/")
        path = f"uploads/{filename}"
        try:
            r = httpx.post(
                f"{base}/storage/v1/object/{settings.SUPABASE_BUCKET}/{path}", content=data, timeout=60,
                headers={"Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
                         "apikey": settings.SUPABASE_SERVICE_KEY,
                         "Content-Type": CONTENT_TYPES.get(ext, "application/octet-stream"),
                         "x-upsert": "false", "cache-control": "31536000"},
            )
        except httpx.HTTPError:
            raise HTTPException(502, "File storage is unreachable. Please try again.")
        if r.status_code >= 300:
            raise HTTPException(502, f"File storage rejected the upload ({r.status_code})")
        return f"{base}/storage/v1/object/public/{settings.SUPABASE_BUCKET}/{path}"

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    with open(os.path.join(settings.UPLOAD_DIR, filename), "wb") as f:
        f.write(data)
    return f"/api/media/files/{filename}"
