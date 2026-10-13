"""
Infohive LMS - FastAPI backend (modular monolith).

Each business module lives in app/modules/<name> and owns its:
models / schemas / service / router. Cross-module features call each
other's service functions (in-process, no HTTP hop), which keeps the
deployment simple today while making a future split into services
(e.g. the SaaS evolution) a matter of swapping those call sites.
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import engine, ensure_columns, secure_tables
from app.shared.base import Base

# --- import ALL models so create_all sees every table ---
from app.modules.auth import models as _auth
from app.modules.courses import models as _courses
from app.modules.enrollments import models as _enrollments
from app.modules.assessments import models as _assessments
from app.modules.discussions import models as _discussions
from app.modules.notifications import models as _notifications
from app.modules.certificates import models as _certificates  # noqa: F401
from app.modules.learning import models as _learning  # noqa: F401
from app.modules.payments import models as _payments  # noqa: F401
from app.modules.live import models as _live  # noqa: F401
from app.modules.site import models as _site  # noqa: F401

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
from app.modules.learning.router import router as learning_router
from app.modules.payments.router import router as payments_router
from app.modules.live.router import router as live_router
from app.modules.site.router import router as site_router
from app.modules.admin.router import router as admin_lms_router

@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Creates missing tables/columns on startup. On serverless hosts this may not run, so
    # also run `python -m app.manage init-db` once against the production database.
    if settings.AUTO_MIGRATE:
        try:
            Base.metadata.create_all(bind=engine)
            ensure_columns()
            secure_tables()
        except Exception:  # noqa: BLE001 - don't take the API down if the DB is briefly unreachable
            import logging
            logging.getLogger("lms").exception("Startup schema check failed")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)


_UNSAFE = {"POST", "PUT", "PATCH", "DELETE"}
_CSRF_EXEMPT = ("/api/payments/webhook",)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    # CSRF guard for cookie sessions: a state-changing request that relies on our cookies must
    # carry a custom header. Other sites can't add one (CORS blocks it), so forged form posts fail.
    from app.core.cookies import ACCESS_COOKIE, REFRESH_COOKIE
    if (request.method in _UNSAFE and not request.url.path.startswith(_CSRF_EXEMPT)
            and "authorization" not in request.headers
            and (ACCESS_COOKIE in request.cookies or REFRESH_COOKIE in request.cookies)
            and request.headers.get("x-requested-with", "").lower() != "xmlhttprequest"):
        from fastapi.responses import JSONResponse
        return JSONResponse({"detail": "Missing X-Requested-With header"}, status_code=403)
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    if request.url.path.startswith("/api/media/files/"):
        # user uploads must never run as part of our origin (e.g. HTML/SVG with script)
        response.headers["Content-Security-Policy"] = "default-src 'none'; img-src 'self'; media-src 'self'; sandbox"
    return response

# local uploads only (on Vercel files go to Supabase Storage; its filesystem is read-only)
_local_uploads = not settings.use_supabase_storage
if _local_uploads:
    try:
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    except OSError:
        _local_uploads = False


# ---- routes (all mounted under /api) ----
app.include_router(auth_router, prefix="/api")
app.include_router(admin_lms_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(courses_router, prefix="/api")
app.include_router(enrollments_router, prefix="/api")
app.include_router(assessments_router, prefix="/api")
app.include_router(discussions_router, prefix="/api")
app.include_router(notifications_router, prefix="/api")
app.include_router(certificates_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(media_router, prefix="/api")
app.include_router(learning_router, prefix="/api")
app.include_router(payments_router, prefix="/api")
app.include_router(live_router, prefix="/api")
app.include_router(site_router, prefix="/api")

# static uploaded media (served under /api so the frontend proxy reaches it)
if _local_uploads:
    app.mount("/api/media/files", StaticFiles(directory=settings.UPLOAD_DIR), name="media")


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME}
