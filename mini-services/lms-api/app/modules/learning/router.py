"""Learning tools: private notes, bookmarks and the student calendar."""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.deps import any_user
from app.modules.auth.models import User, UserRole
from app.modules.courses.models import Course, Lesson
from app.modules.enrollments.models import Enrollment
from app.modules.learning.models import Bookmark, LessonNote
from app.shared.utils import utcnow

router = APIRouter(tags=["learning"])


class NoteIn(BaseModel):
    body: str = Field(default="", max_length=20_000)


class BookmarkIn(BaseModel):
    label: str | None = Field(default=None, max_length=255)


def _lesson_for(db: Session, lesson_id: int, user: User) -> Lesson:
    """The lesson, if this user may study it (enrolled, owner or admin)."""
    lesson = db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(404, "Lesson not found")
    course = db.get(Course, lesson.course_id)
    if user.role != UserRole.admin and course.instructor_id != user.id:
        if not db.query(Enrollment).filter_by(course_id=course.id, user_id=user.id).first():
            raise HTTPException(403, "Enroll in this course to take notes")
    return lesson


def _lesson_ref(lesson: Lesson) -> dict:
    course = lesson.section.course if lesson.section else None
    return {
        "lesson_id": lesson.id, "lesson_title": lesson.title, "lesson_type": lesson.type.value,
        "course_id": course.id if course else None,
        "course_title": course.title if course else "",
        "course_slug": course.slug if course else "",
    }


# ---------- notes ----------

@router.get("/lessons/{lesson_id}/note")
def get_note(lesson_id: int, db: Session = Depends(get_db), user: User = Depends(any_user)):
    _lesson_for(db, lesson_id, user)
    note = db.query(LessonNote).filter_by(user_id=user.id, lesson_id=lesson_id).first()
    bookmarked = db.query(Bookmark).filter_by(user_id=user.id, lesson_id=lesson_id).first() is not None
    return {"body": note.body if note else "",
            "updated_at": note.updated_at.isoformat() if note else None,
            "bookmarked": bookmarked}


@router.put("/lessons/{lesson_id}/note")
def save_note(lesson_id: int, data: NoteIn, db: Session = Depends(get_db), user: User = Depends(any_user)):
    _lesson_for(db, lesson_id, user)
    note = db.query(LessonNote).filter_by(user_id=user.id, lesson_id=lesson_id).first()
    body = data.body.strip()
    if not body:
        if note:
            db.delete(note)
            db.commit()
        return {"body": "", "updated_at": None}
    if note:
        note.body = data.body
        note.updated_at = utcnow()
    else:
        note = LessonNote(user_id=user.id, lesson_id=lesson_id, body=data.body)
        db.add(note)
    db.commit()
    return {"body": note.body, "updated_at": note.updated_at.isoformat()}


@router.get("/me/notes")
def my_notes(db: Session = Depends(get_db), user: User = Depends(any_user)):
    notes = (db.query(LessonNote).options(joinedload(LessonNote.lesson))
             .filter(LessonNote.user_id == user.id).order_by(LessonNote.updated_at.desc()).all())
    return [{"id": n.id, "body": n.body, "updated_at": n.updated_at.isoformat(), **_lesson_ref(n.lesson)}
            for n in notes if n.lesson]


# ---------- bookmarks ----------

@router.post("/lessons/{lesson_id}/bookmark", status_code=201)
def add_bookmark(lesson_id: int, data: BookmarkIn | None = None, db: Session = Depends(get_db),
                 user: User = Depends(any_user)):
    _lesson_for(db, lesson_id, user)
    bm = db.query(Bookmark).filter_by(user_id=user.id, lesson_id=lesson_id).first()
    if not bm:
        bm = Bookmark(user_id=user.id, lesson_id=lesson_id, label=data.label if data else None)
        db.add(bm)
        db.commit()
    return {"bookmarked": True}


@router.delete("/lessons/{lesson_id}/bookmark")
def remove_bookmark(lesson_id: int, db: Session = Depends(get_db), user: User = Depends(any_user)):
    db.query(Bookmark).filter_by(user_id=user.id, lesson_id=lesson_id).delete(synchronize_session=False)
    db.commit()
    return {"bookmarked": False}


@router.get("/me/bookmarks")
def my_bookmarks(db: Session = Depends(get_db), user: User = Depends(any_user)):
    rows = (db.query(Bookmark).options(joinedload(Bookmark.lesson))
            .filter(Bookmark.user_id == user.id).order_by(Bookmark.created_at.desc()).all())
    return [{"id": b.id, "label": b.label, "created_at": b.created_at.isoformat(), **_lesson_ref(b.lesson)}
            for b in rows if b.lesson]


# ---------- calendar ----------

def _parse_day(value: str | None, default: datetime) -> datetime:
    if not value:
        return default
    try:
        return datetime.fromisoformat(value[:10])
    except ValueError:
        raise HTTPException(400, "Dates must look like 2026-10-31")


@router.get("/me/calendar")
def my_calendar(start: str | None = Query(None), end: str | None = Query(None),
                db: Session = Depends(get_db), user: User = Depends(any_user)):
    """Assignment due dates and drip-lesson unlocks for the caller's courses.

    Students see their enrolled courses; instructors also see due dates for courses they teach."""
    from app.modules.assessments.models import Assignment, Submission
    from app.modules.enrollments.service import lesson_unlock_at

    today = utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    start_dt = _parse_day(start, today - timedelta(days=31))
    end_dt = _parse_day(end, today + timedelta(days=62)) + timedelta(days=1)
    if end_dt - start_dt > timedelta(days=400):
        raise HTTPException(400, "Choose a range of at most about a year")

    enrollments = {e.course_id: e for e in db.query(Enrollment).filter(Enrollment.user_id == user.id)}
    teaching = set()
    if user.role in (UserRole.instructor, UserRole.admin):
        teaching = {c.id for c in db.query(Course.id).filter(Course.instructor_id == user.id)}
    course_ids = set(enrollments) | teaching
    if not course_ids:
        return []
    courses = {c.id: c for c in db.query(Course).filter(Course.id.in_(course_ids))}

    events = []
    assignments = (db.query(Assignment).filter(Assignment.course_id.in_(course_ids),
                   Assignment.due_date.isnot(None), Assignment.due_date >= start_dt,
                   Assignment.due_date < end_dt).all())
    my_subs = {s.assignment_id: s for s in db.query(Submission).filter(
        Submission.user_id == user.id, Submission.assignment_id.in_([a.id for a in assignments] or [0]))}
    for a in assignments:
        c = courses[a.course_id]
        is_teacher = a.course_id in teaching
        sub = my_subs.get(a.id)
        status = None if is_teacher else (sub.status if sub else ("overdue" if a.due_date < utcnow() else "todo"))
        events.append({
            "type": "assignment", "date": a.due_date.isoformat(), "title": a.title,
            "course_id": c.id, "course_title": c.title, "course_slug": c.slug,
            "status": status, "role": "teacher" if is_teacher else "student",
            "link": f"/teach/courses/{c.id}/gradebook" if is_teacher else f"/courses/{c.slug}?tab=assignments",
        })

    dripped = (db.query(Lesson).filter(Lesson.course_id.in_(list(enrollments)), Lesson.drip_days > 0).all()
               if enrollments else [])
    for l in dripped:
        unlock = lesson_unlock_at(enrollments[l.course_id], l)
        if unlock and start_dt <= unlock < end_dt:
            c = courses[l.course_id]
            events.append({
                "type": "unlock", "date": unlock.isoformat(), "title": l.title,
                "course_id": c.id, "course_title": c.title, "course_slug": c.slug,
                "status": "unlocked" if unlock <= utcnow() else "upcoming", "role": "student",
                "link": f"/learn/{c.slug}/{l.id}",
            })
    from app.modules.live.models import LiveSession
    for ls in db.query(LiveSession).filter(LiveSession.course_id.in_(course_ids), LiveSession.status == "scheduled",
                                           LiveSession.starts_at >= start_dt, LiveSession.starts_at < end_dt):
        c = courses[ls.course_id]
        events.append({
            "type": "live", "date": ls.starts_at.isoformat(), "title": ls.title,
            "course_id": c.id, "course_title": c.title, "course_slug": c.slug,
            "status": "live", "role": "teacher" if ls.course_id in teaching else "student",
            "duration_minutes": ls.duration_minutes, "link": f"/live/{ls.id}",
        })
    events.sort(key=lambda e: e["date"])
    return events
