from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import staff_required
from app.modules.auth.models import User, UserRole
from app.modules.courses.models import Course, Lesson, Review
from app.modules.enrollments.models import Enrollment, LessonProgress
from app.modules.assessments.models import Quiz, QuizAttempt, Assignment, Submission
from app.shared.utils import utcnow

router = APIRouter(prefix="/teach/analytics", tags=["analytics"])


@router.get("/overview")
def instructor_overview(db: Session = Depends(get_db), user: User = Depends(staff_required)):
    q = db.query(Course)
    if user.role != UserRole.admin:
        q = q.filter(Course.instructor_id == user.id)
    courses = q.all()
    course_ids = [c.id for c in courses]

    enroll_counts = dict(
        db.query(Enrollment.course_id, func.count(Enrollment.id))
        .filter(Enrollment.course_id.in_(course_ids)).group_by(Enrollment.course_id).all()
    ) if course_ids else {}
    completed_counts = dict(
        db.query(Enrollment.course_id, func.count(Enrollment.id))
        .filter(Enrollment.course_id.in_(course_ids), Enrollment.status == "completed")
        .group_by(Enrollment.course_id).all()
    ) if course_ids else {}

    revenue = 0.0
    per_course = []
    for c in courses:
        enrolled = enroll_counts.get(c.id, 0)
        revenue += enrolled * (c.price or 0)
        per_course.append({
            "id": c.id, "title": c.title, "slug": c.slug, "status": c.status.value,
            "enrollments": enrolled,
            "completions": completed_counts.get(c.id, 0),
            "completion_rate": round(completed_counts.get(c.id, 0) / enrolled * 100, 1) if enrolled else 0,
            "revenue": round(enrolled * (c.price or 0), 2),
        })

    # last-30-day enrollment trend across own courses
    since = utcnow() - timedelta(days=30)
    trend_rows = (
        db.query(func.date(Enrollment.enrolled_at), func.count(Enrollment.id))
        .filter(Enrollment.course_id.in_(course_ids), Enrollment.enrolled_at >= since)
        .group_by(func.date(Enrollment.enrolled_at)).all()
    ) if course_ids else []
    trend = {str(d): n for d, n in trend_rows}

    return {
        "totals": {
            "courses": len(courses),
            "enrollments": sum(enroll_counts.values()),
            "completions": sum(completed_counts.values()),
            "revenue": round(revenue, 2),
        },
        "per_course": sorted(per_course, key=lambda x: -x["enrollments"]),
        "trend_30d": trend,
    }


@router.get("/courses/{course_id}")
def course_analytics(course_id: int, db: Session = Depends(get_db), user: User = Depends(staff_required)):
    course = db.get(Course, course_id)
    if not course:
        from fastapi import HTTPException
        raise HTTPException(404, "Course not found")
    if course.instructor_id != user.id and user.role != UserRole.admin:
        from fastapi import HTTPException
        raise HTTPException(403, "Not your course")

    enrolled = db.query(Enrollment).filter(Enrollment.course_id == course_id).count()
    completed = db.query(Enrollment).filter(Enrollment.course_id == course_id, Enrollment.status == "completed").count()

    # lesson completion funnel
    lessons = sorted(db.query(Lesson).filter(Lesson.course_id == course_id).all(), key=lambda l: l.position)
    lesson_stats = []
    for l in lessons:
        done = (
            db.query(func.count(LessonProgress.id))
            .join(Enrollment, Enrollment.id == LessonProgress.enrollment_id)
            .filter(LessonProgress.lesson_id == l.id, Enrollment.course_id == course_id).scalar() or 0
        )
        lesson_stats.append({
            "lesson_id": l.id, "title": l.title, "type": l.type.value,
            "completed_by": done,
            "pct": round(done / enrolled * 100, 1) if enrolled else 0,
        })

    # quiz pass rates
    quiz_rows = (
        db.query(Quiz.id, Quiz.title, func.count(QuizAttempt.id), func.avg(QuizAttempt.score))
        .join(Lesson, Lesson.id == Quiz.lesson_id)
        .outerjoin(QuizAttempt, QuizAttempt.quiz_id == Quiz.id)
        .filter(Lesson.course_id == course_id)
        .group_by(Quiz.id, Quiz.title).all()
    )
    quiz_stats = [
        {"quiz_id": qid, "title": title, "attempts": int(cnt or 0), "avg_score": round(float(avg or 0), 1)}
        for qid, title, cnt, avg in quiz_rows
    ]

    # assignment submission rates
    assignment_rows = (
        db.query(Assignment.id, Assignment.title, func.count(Submission.id))
        .outerjoin(Submission, Submission.assignment_id == Assignment.id)
        .filter(Assignment.course_id == course_id)
        .group_by(Assignment.id, Assignment.title).all()
    )
    assignment_stats = [
        {"assignment_id": aid, "title": title, "submissions": int(cnt or 0)}
        for aid, title, cnt in assignment_rows
    ]

    revenue = round(enrolled * (course.price or 0), 2)

    # enrollment trend for this course (30 days)
    since = utcnow() - timedelta(days=30)
    trend_rows = (
        db.query(func.date(Enrollment.enrolled_at), func.count(Enrollment.id))
        .filter(Enrollment.course_id == course_id, Enrollment.enrolled_at >= since)
        .group_by(func.date(Enrollment.enrolled_at)).all()
    )
    trend = {str(d): n for d, n in trend_rows}

    return {
        "course": {"id": course.id, "title": course.title, "price": course.price},
        "enrollments": enrolled,
        "completions": completed,
        "completion_rate": round(completed / enrolled * 100, 1) if enrolled else 0,
        "revenue": revenue,
        "lesson_stats": lesson_stats,
        "quiz_stats": quiz_stats,
        "assignment_stats": assignment_stats,
        "trend_30d": trend,
    }
