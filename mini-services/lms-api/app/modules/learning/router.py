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


# ---------- momentum ----------

@router.get("/me/learning-summary")
def learning_summary(db: Session = Depends(get_db), user: User = Depends(any_user)):
    """Streak and weekly activity for the learner dashboard."""
    from app.modules.enrollments.models import LessonProgress
    rows = (db.query(LessonProgress.completed_at, Lesson.duration_minutes)
            .join(Enrollment, Enrollment.id == LessonProgress.enrollment_id)
            .join(Lesson, Lesson.id == LessonProgress.lesson_id)
            .filter(Enrollment.user_id == user.id).all())
    today = utcnow().date()
    days = {r[0].date() for r in rows if r[0]}
    streak, d = 0, today if today in days else today - timedelta(days=1)
    while d in days:
        streak, d = streak + 1, d - timedelta(days=1)
    week_start = today - timedelta(days=today.weekday())   # Monday
    this_week = [r for r in rows if r[0] and r[0].date() >= week_start]
    return {
        "streak_days": streak,
        "active_today": today in days,
        "lessons_this_week": len(this_week),
        "minutes_this_week": sum(r[1] or 0 for r in this_week),
        "weekly_goal": 3,
        "week": [{"date": (week_start + timedelta(days=i)).isoformat(),
                  "active": (week_start + timedelta(days=i)) in days} for i in range(7)],
    }


@router.get("/teach/actions")
def teaching_actions(db: Session = Depends(get_db), user: User = Depends(any_user)):
    """What needs the instructor's attention: grading, learners who stalled, unfinished drafts."""
    from app.modules.assessments.models import Assignment, Submission
    from app.modules.courses.service import CoursesService
    from app.modules.enrollments.models import LessonProgress
    from sqlalchemy import func
    if user.role not in (UserRole.instructor, UserRole.admin):
        raise HTTPException(403, "Instructors only")
    courses = db.query(Course).filter(Course.instructor_id == user.id).all()
    ids = [c.id for c in courses] or [0]
    by_id = {c.id: c for c in courses}

    subs = (db.query(Submission, Assignment).join(Assignment, Assignment.id == Submission.assignment_id)
            .options(joinedload(Submission.user))
            .filter(Assignment.course_id.in_(ids), Submission.status == "submitted")
            .order_by(Submission.submitted_at.asc()).limit(50).all())
    to_grade = [{"submission_id": s.id, "assignment": a.title, "student": s.user.full_name if s.user else "",
                 "course_id": a.course_id, "course_title": by_id[a.course_id].title,
                 "submitted_at": s.submitted_at.isoformat() + "Z"} for s, a in subs]

    last = dict(db.query(LessonProgress.enrollment_id, func.max(LessonProgress.completed_at))
                .join(Enrollment, Enrollment.id == LessonProgress.enrollment_id)
                .filter(Enrollment.course_id.in_(ids)).group_by(LessonProgress.enrollment_id).all())
    cutoff = utcnow() - timedelta(days=7)
    stalled = []
    for e in (db.query(Enrollment).options(joinedload(Enrollment.user))
              .filter(Enrollment.course_id.in_(ids), Enrollment.status != "completed").all()):
        seen = last.get(e.id) or e.enrolled_at
        if seen < cutoff and e.user:
            stalled.append({"student": e.user.full_name, "email": e.user.email, "course_id": e.course_id,
                            "course_title": by_id[e.course_id].title, "progress": e.progress,
                            "last_active": seen.isoformat() + "Z", "days_inactive": (utcnow() - seen).days})
    stalled.sort(key=lambda x: -x["days_inactive"])

    drafts = []
    for c in courses:
        if c.status.value == "draft":
            todo = [i["label"] for i in CoursesService.readiness(c) if not i["ok"]]
            drafts.append({"course_id": c.id, "title": c.title, "todo": todo})
    return {"to_grade": to_grade, "stalled": stalled[:20], "stalled_total": len(stalled), "drafts": drafts}
