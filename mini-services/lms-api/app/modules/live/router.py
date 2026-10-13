"""Live classes: scheduling, joining (with a join window), attendance and recordings."""
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import any_user, staff_required
from app.modules.auth.models import User, UserRole
from app.modules.courses.models import Course, CourseStatus
from app.modules.courses.service import CoursesService
from app.modules.enrollments.models import Enrollment
from app.modules.live.models import LiveAttendance, LiveSession
from app.shared.utils import safe_url, utcnow

router = APIRouter(tags=["live"])

GRACE_AFTER_END = timedelta(minutes=30)   # late joiners / overrunning classes


# ---------- schemas ----------

class LiveIn(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    description: Optional[str] = Field(default=None, max_length=5000)
    starts_at: datetime                              # ISO with timezone (e.g. 2026-10-12T15:00:00Z)
    duration_minutes: int = Field(default=60, ge=10, le=600)
    provider: Literal["jitsi", "external"] = "jitsi"
    external_url: Optional[str] = None


class LiveUpdateIn(BaseModel):
    title: Optional[str] = Field(default=None, min_length=2, max_length=255)
    description: Optional[str] = Field(default=None, max_length=5000)
    starts_at: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(default=None, ge=10, le=600)
    provider: Optional[Literal["jitsi", "external"]] = None
    external_url: Optional[str] = None
    recording_url: Optional[str] = None


# ---------- helpers ----------

def _utc_naive(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        raise HTTPException(400, "starts_at must include a timezone (e.g. 2026-10-12T15:00:00Z)")
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def _ends_at(s: LiveSession):
    return s.starts_at + timedelta(minutes=s.duration_minutes)


def _state(s: LiveSession) -> str:
    if s.status == "cancelled":
        return "cancelled"
    now = utcnow()
    if now < s.starts_at - timedelta(minutes=settings.LIVE_JOIN_EARLY_MINUTES):
        return "upcoming"
    if now <= _ends_at(s) + GRACE_AFTER_END:
        return "live" if now >= s.starts_at else "starting_soon"
    return "ended"


def _is_manager(course: Course, user: User) -> bool:
    return user.role == UserRole.admin or course.instructor_id == user.id


def _assert_participant(db: Session, course: Course, user: User) -> None:
    if _is_manager(course, user):
        return
    if course.status != CourseStatus.published:
        raise HTTPException(404, "Course not found")
    if not db.query(Enrollment).filter_by(course_id=course.id, user_id=user.id).first():
        raise HTTPException(403, "Enroll in this course to join its live classes")


def _session_dict(s: LiveSession, *, attended_ids: set[int] | None = None, manager: bool = False) -> dict:
    st = _state(s)
    return {
        "id": s.id, "course_id": s.course_id, "title": s.title, "description": s.description,
        "starts_at": s.starts_at.isoformat() + "Z", "ends_at": _ends_at(s).isoformat() + "Z",
        "duration_minutes": s.duration_minutes, "provider": s.provider,
        "status": s.status, "state": st,
        "can_join": st in ("starting_soon", "live") or (manager and st == "upcoming" and s.status != "cancelled"),
        "recording_url": s.recording_url,
        "host": {"id": s.host.id, "full_name": s.host.full_name} if s.host else None,
        "attended": (s.id in attended_ids) if attended_ids is not None else None,
        "course": {"id": s.course.id, "title": s.course.title, "slug": s.course.slug} if s.course else None,
        # managers see the external link so they can check it; students only get it via /join
        "external_url": s.external_url if manager else None,
    }


def _get_session(db: Session, session_id: int) -> LiveSession:
    s = db.get(LiveSession, session_id, options=[joinedload(LiveSession.course), joinedload(LiveSession.host)])
    if not s:
        raise HTTPException(404, "Live class not found")
    return s


def _notify_students(db: Session, course: Course, title: str, body: str, link: str, email_fn=None) -> None:
    from app.modules.notifications.models import Notification
    students = (db.query(User).join(Enrollment, Enrollment.user_id == User.id)
                .filter(Enrollment.course_id == course.id, User.is_active.is_(True)).all())
    for u in students:
        db.add(Notification(user_id=u.id, type="live", title=title, body=body, link=link))
    db.commit()
    if email_fn:
        for u in students:
            email_fn(u)


def _fmt_when(s: LiveSession) -> str:
    return s.starts_at.strftime("%a %d %b %Y, %H:%M") + " UTC"


def _jaas_token(user: User, moderator: bool) -> str:
    key = settings.JAAS_PRIVATE_KEY.replace("\\n", "\n")
    now = int(time.time())
    payload = {
        "aud": "jitsi", "iss": "chat", "sub": settings.JAAS_APP_ID, "room": "*",
        "iat": now, "nbf": now - 10, "exp": now + 3 * 3600,
        "context": {
            "user": {"id": str(user.id), "name": user.full_name, "email": user.email,
                     "avatar": user.avatar_url or "", "moderator": "true" if moderator else "false"},
            "features": {"livestreaming": "false", "recording": "true" if moderator else "false",
                         "transcription": "false", "outbound-call": "false"},
        },
    }
    return jwt.encode(payload, key, algorithm="RS256", headers={"kid": settings.JAAS_KID})


# ---------- instructor ----------

@router.post("/teach/courses/{course_id}/live", status_code=201)
def schedule(course_id: int, data: LiveIn, db: Session = Depends(get_db), user: User = Depends(staff_required)):
    course = CoursesService.get_course(db, course_id)
    CoursesService.assert_can_manage(course, user)
    starts = _utc_naive(data.starts_at)
    if starts < utcnow() - timedelta(minutes=5):
        raise HTTPException(400, "Pick a start time in the future")
    url = safe_url(data.external_url, "external_url") if data.provider == "external" else None
    if data.provider == "external" and not (url and url.startswith("https://")):
        raise HTTPException(400, "Paste the https:// meeting link (Zoom, Google Meet, Teams…)")
    s = LiveSession(course_id=course.id, host_id=user.id, title=data.title.strip(), description=data.description,
                    starts_at=starts, duration_minutes=data.duration_minutes, provider=data.provider,
                    external_url=url, room=f"infohive-{course.id}-{secrets.token_urlsafe(12)}")
    db.add(s)
    db.commit()
    db.refresh(s)
    from app.shared import emails
    _notify_students(db, course, f"🎥 Live class scheduled: {s.title}", f"{course.title} · {_fmt_when(s)}",
                     f"/live/{s.id}", lambda u: emails.live_scheduled(u.email, u.full_name, course.title, s.title,
                                                                         _fmt_when(s), s.id))
    return _session_dict(_get_session(db, s.id), manager=True)


@router.put("/teach/live/{session_id}")
def update(session_id: int, data: LiveUpdateIn, db: Session = Depends(get_db), user: User = Depends(staff_required)):
    s = _get_session(db, session_id)
    CoursesService.assert_can_manage(s.course, user)
    fields = data.model_dump(exclude_unset=True)
    moved = False
    if "starts_at" in fields and fields["starts_at"] is not None:
        new_start = _utc_naive(fields.pop("starts_at"))
        moved = new_start != s.starts_at
        s.starts_at = new_start
    if "recording_url" in fields:
        s.recording_url = safe_url(fields.pop("recording_url"), "recording_url")
    if "external_url" in fields:
        s.external_url = safe_url(fields.pop("external_url"), "external_url")
    for k, v in fields.items():
        if v is not None:
            setattr(s, k, v.strip() if isinstance(v, str) and k == "title" else v)
    if s.provider == "external" and not (s.external_url or "").startswith("https://"):
        raise HTTPException(400, "External live classes need an https:// meeting link")
    db.commit()
    if moved and s.status == "scheduled":
        from app.shared import emails
        _notify_students(db, s.course, f"🕑 Live class rescheduled: {s.title}", f"New time: {_fmt_when(s)}",
                         f"/live/{s.id}", lambda u: emails.live_scheduled(u.email, u.full_name, s.course.title,
                                                                             s.title, _fmt_when(s), s.id, rescheduled=True))
    return _session_dict(_get_session(db, s.id), manager=True)


@router.post("/teach/live/{session_id}/cancel")
def cancel(session_id: int, db: Session = Depends(get_db), user: User = Depends(staff_required)):
    s = _get_session(db, session_id)
    CoursesService.assert_can_manage(s.course, user)
    if s.status != "cancelled":
        s.status = "cancelled"
        db.commit()
        _notify_students(db, s.course, f"Live class cancelled: {s.title}", f"It was planned for {_fmt_when(s)}.",
                         f"/courses/{s.course.slug}?tab=live")
    return {"message": "Live class cancelled"}


@router.delete("/teach/live/{session_id}")
def delete(session_id: int, db: Session = Depends(get_db), user: User = Depends(staff_required)):
    s = _get_session(db, session_id)
    CoursesService.assert_can_manage(s.course, user)
    db.query(LiveAttendance).filter_by(session_id=s.id).delete(synchronize_session=False)
    db.delete(s)
    db.commit()
    return {"message": "Live class deleted"}


@router.get("/teach/courses/{course_id}/live")
def course_sessions_for_teacher(course_id: int, db: Session = Depends(get_db), user: User = Depends(staff_required)):
    course = CoursesService.get_course(db, course_id)
    CoursesService.assert_can_manage(course, user)
    rows = (db.query(LiveSession).options(joinedload(LiveSession.course), joinedload(LiveSession.host))
            .filter_by(course_id=course.id).order_by(LiveSession.starts_at.desc()).all())
    counts = dict(db.query(LiveAttendance.session_id, func.count(LiveAttendance.id))
                  .filter(LiveAttendance.session_id.in_([r.id for r in rows] or [0]))
                  .group_by(LiveAttendance.session_id).all())
    enrolled = db.query(Enrollment).filter_by(course_id=course.id).count()
    return {"enrolled": enrolled,
            "sessions": [{**_session_dict(r, manager=True), "attendance_count": counts.get(r.id, 0)} for r in rows]}


@router.get("/teach/live/{session_id}/attendance")
def attendance(session_id: int, db: Session = Depends(get_db), user: User = Depends(staff_required)):
    s = _get_session(db, session_id)
    CoursesService.assert_can_manage(s.course, user)
    present = {a.user_id: a for a in db.query(LiveAttendance).options(joinedload(LiveAttendance.user))
               .filter_by(session_id=s.id)}
    students = (db.query(User).join(Enrollment, Enrollment.user_id == User.id)
                .filter(Enrollment.course_id == s.course_id).order_by(User.full_name).all())
    rows = []
    for u in students:
        a = present.get(u.id)
        rows.append({"user": {"id": u.id, "full_name": u.full_name, "email": u.email}, "present": bool(a),
                     "first_joined_at": a.first_joined_at.isoformat() + "Z" if a else None,
                     "join_count": a.join_count if a else 0})
    return {"session": _session_dict(s, manager=True), "rows": rows,
            "present": sum(r["present"] for r in rows), "total": len(rows)}


# ---------- students (and hosts) ----------

@router.get("/courses/{course_id}/live")
def course_sessions(course_id: int, db: Session = Depends(get_db), user: User = Depends(any_user)):
    course = CoursesService.get_course(db, course_id)
    _assert_participant(db, course, user)
    rows = (db.query(LiveSession).options(joinedload(LiveSession.course), joinedload(LiveSession.host))
            .filter_by(course_id=course.id).order_by(LiveSession.starts_at.asc()).all())
    attended = {a.session_id for a in db.query(LiveAttendance).filter(
        LiveAttendance.user_id == user.id, LiveAttendance.session_id.in_([r.id for r in rows] or [0]))}
    manager = _is_manager(course, user)
    return [_session_dict(r, attended_ids=attended, manager=manager) for r in rows]


@router.get("/me/live")
def my_upcoming(db: Session = Depends(get_db), user: User = Depends(any_user)):
    """Upcoming and in-progress live classes across my courses (enrolled or teaching)."""
    enrolled = [e.course_id for e in db.query(Enrollment.course_id).filter(Enrollment.user_id == user.id)]
    teaching = [c.id for c in db.query(Course.id).filter(Course.instructor_id == user.id)]
    ids = set(enrolled) | set(teaching)
    if not ids:
        return []
    rows = (db.query(LiveSession).options(joinedload(LiveSession.course), joinedload(LiveSession.host))
            .filter(LiveSession.course_id.in_(ids), LiveSession.status == "scheduled",
                    LiveSession.starts_at >= utcnow() - timedelta(hours=12))
            .order_by(LiveSession.starts_at.asc()).limit(20).all())
    return [_session_dict(r, manager=r.course_id in teaching) for r in rows if _state(r) != "ended"]


@router.get("/live/{session_id}")
def session_detail(session_id: int, db: Session = Depends(get_db), user: User = Depends(any_user)):
    s = _get_session(db, session_id)
    _assert_participant(db, s.course, user)
    attended = {a.session_id for a in db.query(LiveAttendance).filter_by(session_id=s.id, user_id=user.id)}
    return {**_session_dict(s, attended_ids=attended, manager=_is_manager(s.course, user)),
            "is_host": _is_manager(s.course, user)}


@router.post("/live/{session_id}/join")
def join(session_id: int, db: Session = Depends(get_db), user: User = Depends(any_user)):
    s = _get_session(db, session_id)
    _assert_participant(db, s.course, user)
    host = _is_manager(s.course, user)
    st = _state(s)
    if st == "cancelled":
        raise HTTPException(410, "This live class was cancelled")
    if st == "ended":
        raise HTTPException(410, "This live class has ended" + (" - a recording is available" if s.recording_url else ""))
    if st == "upcoming" and not host:
        opens = s.starts_at - timedelta(minutes=settings.LIVE_JOIN_EARLY_MINUTES)
        raise HTTPException(425, f"Doors open at {opens.strftime('%H:%M')} UTC, "
                                 f"{settings.LIVE_JOIN_EARLY_MINUTES} minutes before the class")

    if not host:   # attendance for learners
        a = db.query(LiveAttendance).filter_by(session_id=s.id, user_id=user.id).first()
        if a:
            a.last_joined_at, a.join_count = utcnow(), a.join_count + 1
        else:
            db.add(LiveAttendance(session_id=s.id, user_id=user.id))
        db.commit()

    if s.provider == "external":
        return {"provider": "external", "url": s.external_url}
    if settings.jaas_enabled:
        return {"provider": "jitsi", "domain": "8x8.vc", "room": f"{settings.JAAS_APP_ID}/{s.room}",
                "jwt": _jaas_token(user, moderator=host), "display_name": user.full_name,
                "email": user.email, "moderator": host, "subject": s.title}
    return {"provider": "jitsi", "domain": settings.JITSI_DOMAIN, "room": s.room, "jwt": None,
            "display_name": user.full_name, "email": user.email, "moderator": host, "subject": s.title,
            "limited": settings.JITSI_DOMAIN == "meet.jit.si"}
