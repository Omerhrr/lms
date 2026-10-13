"""Admin tools for the learning platform: every course, enrollments, instructor applications,
platform reports and certificates."""
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.deps import admin_required
from app.modules.auth.models import User, UserRole
from app.modules.certificates.models import Certificate
from app.modules.courses.models import Course, CourseStatus
from app.modules.enrollments.models import Enrollment, LessonProgress
from app.modules.notifications.service import notify
from app.shared.utils import utcnow

router = APIRouter(prefix="/admin", tags=["admin"])


def _iso(dt) -> Optional[str]:
    return dt.isoformat() + "Z" if dt else None


def _like(text: str) -> str:
    text = text[:100].replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{text}%"


def _page(q, page: int, size: int):
    total = q.order_by(None).count()
    items = q.offset((page - 1) * size).limit(size).all()
    return items, total, max(1, -(-total // size))


def _last_active(db: Session, enrollment_ids: list[int]) -> dict[int, object]:
    if not enrollment_ids:
        return {}
    return dict(db.query(LessonProgress.enrollment_id, func.max(LessonProgress.completed_at))
                .filter(LessonProgress.enrollment_id.in_(enrollment_ids))
                .group_by(LessonProgress.enrollment_id).all())


# ---------------------------------------------------------------- courses
@router.get("/courses")
def all_courses(search: str = "", status: str = "", instructor_id: Optional[int] = None,
                page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
                db: Session = Depends(get_db), _: User = Depends(admin_required)):
    q = db.query(Course).options(joinedload(Course.instructor), joinedload(Course.category))
    if search.strip():
        q = q.filter(Course.title.ilike(_like(search.strip()), escape="\\"))
    if status in ("draft", "published", "archived"):
        q = q.filter(Course.status == CourseStatus(status))
    if instructor_id:
        q = q.filter(Course.instructor_id == instructor_id)
    courses, total, pages = _page(q.order_by(Course.created_at.desc(), Course.id.desc()), page, size)
    ids = [c.id for c in courses]
    counts, done, avg = {}, {}, {}
    if ids:
        for cid, n, d, a in (db.query(Enrollment.course_id, func.count(Enrollment.id),
                                      func.sum(case((Enrollment.status == "completed", 1), else_=0)),
                                      func.avg(Enrollment.progress))
                             .filter(Enrollment.course_id.in_(ids)).group_by(Enrollment.course_id).all()):
            counts[cid], done[cid], avg[cid] = n, int(d or 0), float(a or 0)
    from app.modules.payments.models import Payment
    revenue = dict(db.query(Payment.course_id, func.sum(Payment.amount))
                   .filter(Payment.course_id.in_(ids or [0]), Payment.status == "success")
                   .group_by(Payment.course_id).all())
    items = [{
        "id": c.id, "title": c.title, "slug": c.slug, "status": c.status.value, "price": c.price,
        "created_at": _iso(c.created_at),
        "instructor": {"id": c.instructor.id, "full_name": c.instructor.full_name, "email": c.instructor.email} if c.instructor else None,
        "category": c.category.name if c.category else None,
        "enrollments": counts.get(c.id, 0), "completions": done.get(c.id, 0),
        "completion_rate": round(100 * done.get(c.id, 0) / counts[c.id], 1) if counts.get(c.id) else 0,
        "avg_progress": round(avg.get(c.id, 0), 1),
        "revenue": (revenue.get(c.id) or 0) / 100,
    } for c in courses]
    return {"items": items, "total": total, "page": page, "pages": pages,
            "counts": {st.value: n for st, n in db.query(Course.status, func.count(Course.id)).group_by(Course.status).all()}}


class ReassignIn(BaseModel):
    instructor_id: int


@router.put("/courses/{course_id}/instructor")
def reassign_course(course_id: int, data: ReassignIn, db: Session = Depends(get_db), admin: User = Depends(admin_required)):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(404, "Course not found")
    new = db.get(User, data.instructor_id)
    if not new or not new.is_active or new.role not in (UserRole.instructor, UserRole.admin):
        raise HTTPException(400, "Choose an active instructor")
    old_id = course.instructor_id
    if old_id == new.id:
        return {"message": "No change"}
    course.instructor_id = new.id
    db.commit()
    notify(db, new.id, "system", f"You now teach: {course.title}",
           f"{admin.full_name} assigned this course to you.", f"/teach/courses/{course.id}/edit")
    if old_id and old_id != admin.id:
        notify(db, old_id, "system", f"Course reassigned: {course.title}",
               f"This course is now taught by {new.full_name}.", "/teach/courses")
    return {"message": f"{course.title} is now taught by {new.full_name}",
            "instructor": {"id": new.id, "full_name": new.full_name, "email": new.email}}


@router.get("/instructors")
def instructors(db: Session = Depends(get_db), _: User = Depends(admin_required)):
    rows = (db.query(User).filter(User.role.in_([UserRole.instructor, UserRole.admin]), User.is_active.is_(True))
            .order_by(User.full_name).all())
    return [{"id": u.id, "full_name": u.full_name, "email": u.email, "role": u.role.value} for u in rows]


# ---------------------------------------------------------------- enrollments
@router.get("/enrollments")
def list_enrollments(course_id: Optional[int] = None, search: str = "", status: str = "",
                     page: int = Query(1, ge=1), size: int = Query(25, ge=1, le=100),
                     db: Session = Depends(get_db), _: User = Depends(admin_required)):
    q = (db.query(Enrollment).join(User, User.id == Enrollment.user_id).join(Course, Course.id == Enrollment.course_id)
         .options(joinedload(Enrollment.user), joinedload(Enrollment.course)))
    if course_id:
        q = q.filter(Enrollment.course_id == course_id)
    if search.strip():
        like = _like(search.strip())
        q = q.filter(or_(User.full_name.ilike(like, escape="\\"), User.email.ilike(like, escape="\\")))
    if status in ("active", "completed"):
        q = q.filter(Enrollment.status == status)
    rows, total, pages = _page(q.order_by(Enrollment.enrolled_at.desc(), Enrollment.id.desc()), page, size)
    last = _last_active(db, [e.id for e in rows])
    return {"items": [{
        "id": e.id, "status": e.status, "progress": round(e.progress or 0, 1),
        "enrolled_at": _iso(e.enrolled_at), "completed_at": _iso(e.completed_at), "last_active": _iso(last.get(e.id)),
        "user": {"id": e.user.id, "full_name": e.user.full_name, "email": e.user.email},
        "course": {"id": e.course.id, "title": e.course.title, "slug": e.course.slug},
    } for e in rows], "total": total, "page": page, "pages": pages}


class BulkEnrollIn(BaseModel):
    course_id: int
    emails: list[EmailStr] = Field(min_length=1, max_length=200)
    notify: bool = True


@router.post("/enrollments", status_code=201)
def bulk_enroll(data: BulkEnrollIn, db: Session = Depends(get_db), admin: User = Depends(admin_required)):
    """Enroll existing learners by email. Unknown emails and existing enrollments are reported, not errors."""
    from app.modules.enrollments.service import EnrollmentService
    course = db.get(Course, data.course_id)
    if not course:
        raise HTTPException(404, "Course not found")
    emails = list(dict.fromkeys(e.lower() for e in data.emails))
    users = {u.email.lower(): u for u in db.query(User).filter(func.lower(User.email).in_(emails)).all()}
    result = {"enrolled": [], "already": [], "not_found": [], "not_allowed": []}
    for email in emails:
        u = users.get(email)
        if not u:
            result["not_found"].append(email)
            continue
        if u.role != UserRole.student or not u.is_active:
            result["not_allowed"].append(email)
            continue
        if db.query(Enrollment.id).filter(Enrollment.course_id == course.id, Enrollment.user_id == u.id).first():
            result["already"].append(email)
            continue
        EnrollmentService.enroll(db, course, admin, u.id, quiet=not data.notify)
        result["enrolled"].append(email)
    return result


@router.delete("/enrollments/{enrollment_id}")
def remove_enrollment(enrollment_id: int, db: Session = Depends(get_db), _: User = Depends(admin_required)):
    e = db.get(Enrollment, enrollment_id)
    if not e:
        raise HTTPException(404, "Enrollment not found")
    db.query(LessonProgress).filter(LessonProgress.enrollment_id == e.id).delete(synchronize_session=False)
    db.delete(e)
    db.commit()
    return {"message": "Enrollment removed. Any certificate already issued stays valid."}


# ---------------------------------------------------------------- instructor applications
@router.get("/instructor-requests")
def instructor_requests(db: Session = Depends(get_db), _: User = Depends(admin_required)):
    rows = (db.query(User).filter(User.instructor_requested.is_(True), User.role == UserRole.student)
            .order_by(User.created_at.asc()).all())
    return [{"id": u.id, "full_name": u.full_name, "email": u.email, "headline": u.headline, "bio": u.bio,
             "created_at": _iso(u.created_at), "is_active": u.is_active} for u in rows]


class DecisionIn(BaseModel):
    approve: bool
    message: str = Field(default="", max_length=1000)


@router.post("/instructor-requests/{user_id}")
def decide_request(user_id: int, data: DecisionIn, db: Session = Depends(get_db), _: User = Depends(admin_required)):
    from app.shared import emails
    u = db.get(User, user_id)
    if not u or not u.instructor_requested:
        raise HTTPException(404, "No pending application for this user")
    u.instructor_requested = False
    if data.approve:
        u.role = UserRole.instructor
    db.commit()
    if data.approve:
        # sessions carry the role, so sign them out everywhere to pick up teaching access
        from app.modules.auth.service import AuthService
        AuthService.revoke_all_sessions(db, u.id)
        db.commit()
    note = f" Note from the team: {data.message.strip()}" if data.message.strip() else ""
    if data.approve:
        notify(db, u.id, "system", "You're approved to teach 🎉",
               "You can now create courses from the Instructor studio." + note, "/teach")
        try:
            emails.instructor_approved(u.email, u.full_name)
        except Exception:  # noqa: BLE001 - email is best effort
            pass
    else:
        notify(db, u.id, "system", "About your instructor application",
               "We're not able to approve teaching access right now." + note, "/dashboard")
    return {"message": "Approved" if data.approve else "Declined"}


# ---------------------------------------------------------------- reports
@router.get("/reports")
def reports(days: int = Query(30, ge=7, le=365), db: Session = Depends(get_db), _: User = Depends(admin_required)):
    now = utcnow()
    since = now - timedelta(days=days)
    week_ago = now - timedelta(days=7)

    def active_learners(start):
        return (db.query(func.count(func.distinct(Enrollment.user_id)))
                .join(LessonProgress, LessonProgress.enrollment_id == Enrollment.id)
                .filter(LessonProgress.completed_at >= start).scalar() or 0)

    totals = {
        "learners": db.query(func.count(User.id)).filter(User.role == UserRole.student).scalar() or 0,
        "active_7d": active_learners(week_ago),
        "active_period": active_learners(since),
        "new_enrollments": db.query(func.count(Enrollment.id)).filter(Enrollment.enrolled_at >= since).scalar() or 0,
        "completions": db.query(func.count(Enrollment.id)).filter(Enrollment.completed_at >= since).scalar() or 0,
        "certificates": db.query(func.count(Certificate.id)).filter(Certificate.issued_at >= since).scalar() or 0,
        "lessons_completed": db.query(func.count(LessonProgress.id)).filter(LessonProgress.completed_at >= since).scalar() or 0,
    }

    # weekly series (last 12 weeks), bucketed in Python so it works the same on SQLite and Postgres
    start12 = (now - timedelta(weeks=11)).replace(hour=0, minute=0, second=0, microsecond=0)
    start12 -= timedelta(days=start12.weekday())
    weeks = [start12 + timedelta(weeks=i) for i in range(12)]

    def bucket(values):
        out = [0] * 12
        for v in values:
            if v and v >= start12:
                i = min(11, (v - start12).days // 7)
                out[i] += 1
        return out
    series = {
        "weeks": [w.date().isoformat() for w in weeks],
        "enrollments": bucket(v for (v,) in db.query(Enrollment.enrolled_at).filter(Enrollment.enrolled_at >= start12)),
        "completions": bucket(v for (v,) in db.query(Enrollment.completed_at).filter(Enrollment.completed_at >= start12)),
        "lessons": bucket(v for (v,) in db.query(LessonProgress.completed_at).filter(LessonProgress.completed_at >= start12)),
    }

    # per course
    per_course = []
    courses = db.query(Course).options(joinedload(Course.instructor)).filter(Course.status != CourseStatus.archived).all()
    rows = db.query(Enrollment.course_id, Enrollment.status, Enrollment.progress, Enrollment.id).all()
    last = _last_active(db, [r[3] for r in rows])
    by_course: dict[int, list] = {}
    for cid, st, prog, eid in rows:
        by_course.setdefault(cid, []).append((st, prog or 0, last.get(eid)))
    for c in courses:
        rs = by_course.get(c.id, [])
        n = len(rs)
        done = sum(1 for r in rs if r[0] == "completed")
        active = sum(1 for r in rs if r[2] and r[2] >= since)
        per_course.append({
            "id": c.id, "title": c.title, "status": c.status.value,
            "instructor": c.instructor.full_name if c.instructor else "",
            "enrollments": n, "active": active, "completions": done,
            "completion_rate": round(100 * done / n, 1) if n else 0,
            "avg_progress": round(sum(r[1] for r in rs) / n, 1) if n else 0,
        })
    per_course.sort(key=lambda r: -r["enrollments"])

    # learners who started but went quiet for 14+ days
    stalled = []
    q = (db.query(Enrollment).options(joinedload(Enrollment.user), joinedload(Enrollment.course))
         .filter(Enrollment.status == "active"))
    ens = q.all()
    last_all = _last_active(db, [e.id for e in ens])
    cutoff = now - timedelta(days=14)
    for e in ens:
        seen = last_all.get(e.id) or e.enrolled_at
        if seen and seen < cutoff and e.user and e.user.is_active:
            stalled.append({"enrollment_id": e.id, "student": e.user.full_name, "email": e.user.email,
                            "course_title": e.course.title, "course_id": e.course_id, "progress": round(e.progress or 0, 1),
                            "last_active": _iso(seen), "days_inactive": (now - seen).days})
    stalled.sort(key=lambda r: -r["days_inactive"])
    return {"days": days, "totals": totals, "series": series, "per_course": per_course,
            "stalled": stalled[:50], "stalled_total": len(stalled)}


# ---------------------------------------------------------------- certificates
@router.get("/certificates")
def list_certificates(search: str = "", status: str = "", page: int = Query(1, ge=1), size: int = Query(25, ge=1, le=100),
                      db: Session = Depends(get_db), _: User = Depends(admin_required)):
    q = db.query(Certificate)
    if search.strip():
        like = _like(search.strip())
        q = q.filter(or_(Certificate.serial.ilike(like, escape="\\"), Certificate.user_name.ilike(like, escape="\\"),
                         Certificate.course_title.ilike(like, escape="\\")))
    if status == "valid":
        q = q.filter(Certificate.revoked_at.is_(None))
    elif status == "revoked":
        q = q.filter(Certificate.revoked_at.isnot(None))
    rows, total, pages = _page(q.order_by(Certificate.issued_at.desc(), Certificate.id.desc()), page, size)
    return {"items": [{
        "id": c.id, "serial": c.serial, "user_name": c.user_name, "course_title": c.course_title, "course_id": c.course_id,
        "instructor_name": c.instructor_name, "issued_at": _iso(c.issued_at),
        "revoked_at": _iso(c.revoked_at), "revoke_reason": c.revoke_reason,
    } for c in rows], "total": total, "page": page, "pages": pages}


class RevokeIn(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


@router.post("/certificates/{cert_id}/revoke")
def revoke_certificate(cert_id: int, data: RevokeIn, db: Session = Depends(get_db), _: User = Depends(admin_required)):
    c = db.get(Certificate, cert_id)
    if not c:
        raise HTTPException(404, "Certificate not found")
    if c.revoked_at:
        raise HTTPException(400, "This certificate is already revoked")
    c.revoked_at = utcnow()
    c.revoke_reason = data.reason.strip()
    db.commit()
    notify(db, c.user_id, "system", f"Certificate revoked: {c.course_title}",
           f"Reason: {c.revoke_reason}. Contact us if you think this is a mistake.", "/certificates")
    return {"message": "Certificate revoked", "revoked_at": _iso(c.revoked_at)}


@router.post("/certificates/{cert_id}/restore")
def restore_certificate(cert_id: int, db: Session = Depends(get_db), _: User = Depends(admin_required)):
    c = db.get(Certificate, cert_id)
    if not c:
        raise HTTPException(404, "Certificate not found")
    c.revoked_at = None
    c.revoke_reason = None
    db.commit()
    return {"message": "Certificate restored"}
