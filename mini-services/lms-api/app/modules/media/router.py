import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from app.core.config import settings
from app.core.deps import any_user
from app.modules.auth.models import User

router = APIRouter(prefix="/media", tags=["media"])

ALLOWED_EXTENSIONS = {
    # no .svg / .html: they can carry script and would run on our origin
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico",
    ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".txt", ".csv",
    ".mp4", ".webm", ".mp3", ".wav", ".zip",
}


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), _: User = Depends(any_user)):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"File type '{ext or 'unknown'}' is not allowed")

    limit = settings.MAX_UPLOAD_MB * 1024 * 1024
    contents = await file.read(limit + 1)   # never buffer more than the cap
    if len(contents) > limit:
        raise HTTPException(400, f"File exceeds the {settings.MAX_UPLOAD_MB}MB limit")

    from app.core.storage import save_upload
    filename = f"{uuid.uuid4().hex}{ext}"
    url = save_upload(filename, contents, ext)
    return {"url": url, "filename": file.filename, "size": len(contents)}
