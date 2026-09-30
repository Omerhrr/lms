import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from app.core.config import settings
from app.core.deps import any_user
from app.modules.auth.models import User

router = APIRouter(prefix="/media", tags=["media"])

ALLOWED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico",
    ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".txt", ".csv",
    ".mp4", ".webm", ".mp3", ".wav", ".zip",
}


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), _: User = Depends(any_user)):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"File type '{ext or 'unknown'}' is not allowed")

    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(400, f"File exceeds the {settings.MAX_UPLOAD_MB}MB limit")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{ext}"
    with open(os.path.join(settings.UPLOAD_DIR, filename), "wb") as f:
        f.write(contents)

    url = f"/api/media/files/{filename}"
    return {"url": url, "filename": file.filename, "size": len(contents)}
