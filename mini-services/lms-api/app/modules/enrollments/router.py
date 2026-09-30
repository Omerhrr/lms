from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import any_user, staff_required
from app.modules.auth.models import User
from app.modules.courses.service import CoursesService
from app.modules.courses.models import Lesson
from app.modules.enrollments.service import EnrollmentService

router = APIRouter(prefix="/enrollments", tags=["enrollments"])


@router.post("/{course_id}", status_code=201)
def enroll(course_id: int, body: dict | None = None, db: Session = Depends(get_db), user: User = Depends(any_user)):
    course = CoursesService.get_course(db, course_id)
    enrollment = EnrollmentService.enroll(db, course, user, (body or {}).get("target_user_id"))
    return {"id": enrollment.id, "message": "Enrolled successfully"}


@router.delete("/{course_id}")
def drop(course_id: int, db: Session = Depends(get_db), user: User = Depends(any_user)):
    course = CoursesService.get_course(db, course_id)
    EnrollmentService.drop(db, course, user)
    return {"message": "You have dropped this course"}


@router.get("/my")
def my_courses(db: Session = Depends(get_db), user: User = Depends(any_user)):
    return EnrollmentService.my_enrollments(db, user)


@router.get("/my/{course_id}")
def my_enrollment_detail(course_id: int, db: Session = Depends(get_db), user: User = Depends(any_user)):
    """Enrollment detail: progress map used by the course player."""
    enrollment = EnrollmentService.get_enrollment(db, course_id, user.id)
    return {
        "id": enrollment.id,
        "course_id": course_id,
        "status": enrollment.status,
        "progress": enrollment.progress,
        "completed_lesson_ids": sorted(EnrollmentService.completed_lesson_ids(db, enrollment.id)),
    }


@router.post("/{course_id}/lessons/{lesson_id}/complete")
def complete_lesson(course_id: int, lesson_id: int, db: Session = Depends(get_db), user: User = Depends(any_user)):
    course = CoursesService.get_course(db, course_id)
    lesson = db.get(Lesson, lesson_id)
    if not lesson or lesson.course_id != course_id:
        raise HTTPException(404, "Lesson not found in this course")
    return EnrollmentService.complete_lesson(db, course, lesson, user)


@router.post("/{course_id}/lessons/{lesson_id}/uncomplete")
def uncomplete_lesson(course_id: int, lesson_id: int, db: Session = Depends(get_db), user: User = Depends(any_user)):
    course = CoursesService.get_course(db, course_id)
    lesson = db.get(Lesson, lesson_id)
    if not lesson or lesson.course_id != course_id:
        raise HTTPException(404, "Lesson not found in this course")
    return EnrollmentService.uncomplete_lesson(db, course, lesson, user)


@router.get("/course/{course_id}/students")
def enrolled_students(course_id: int, db: Session = Depends(get_db), user: User = Depends(staff_required)):
    course = CoursesService.get_course(db, course_id)
    CoursesService.assert_can_manage(course, user)
    return EnrollmentService.course_students(db, course)
