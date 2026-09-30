"""
LearnHub LMS — FastAPI backend (modular monolith).

Each business module lives in app/modules/<name> and owns its:
models / schemas / service / router. Cross-module features call each
other's service functions (in-process, no HTTP hop), which keeps the
deployment simple today while making a future split into services
(e.g. the SaaS evolution) a matter of swapping those call sites.
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import engine
from app.shared.base import Base

# --- import ALL models so create_all sees every table ---
from app.modules.auth import models as _auth
from app.modules.courses import models as _courses
from app.modules.enrollments import models as _enrollments
from app.modules.assessments import models as _assessments
from app.modules.discussions import models as _discussions
from app.modules.notifications import models as _notifications
from app.modules.certificates import models as _certificates  # noqa: F401

from app.modules.auth.router import router as auth_router
from app.modules.users.router import router as users_router
from app.modules.courses.router import router as courses_router
from app.modules.enrollments.router import router as enrollments_router
from app.modules.assessments.router import router as assessments_router
from app.modules.discussions.router import router as discussions_router
from app.modules.notifications.router import router as notifications_router
from app.modules.certificates.router import router as certificates_router
from app.modules.analytics.router import router as analytics_router
from app.modules.media.router import router as media_router

app = FastAPI(
    title=settings.APP_NAME,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs("data", exist_ok=True)
    Base.metadata.create_all(bind=engine)


# ---- routes (all mounted under /api) ----
app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(courses_router, prefix="/api")
app.include_router(enrollments_router, prefix="/api")
app.include_router(assessments_router, prefix="/api")
app.include_router(discussions_router, prefix="/api")
app.include_router(notifications_router, prefix="/api")
app.include_router(certificates_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(media_router, prefix="/api")

# static uploaded media (served under /api so the frontend proxy reaches it)
app.mount("/api/media/files", StaticFiles(directory=settings.UPLOAD_DIR), name="media")


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME}
