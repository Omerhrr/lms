from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.modules.auth.models import User, UserRole
from app.modules.courses.models import Course, CourseStatus, Lesson
from app.modules.enrollments.models import Enrollment, LessonProgress
from app.shared.utils import utcnow


class EnrollmentService:

    @staticmethod
    def enroll(db: Session, course: Course, user: User, target_user_id: int | None = None) -> Enrollment:
        """Anyone may enroll themselves; instructors/admins may also enroll a student."""
        if target_user_id is not None and target_user_id != user.id:
            if user.role == UserRole.student:
                raise HTTPException(403, "Students can only enroll themselves")
            student = db.get(User, target_user_id)
            if not student or student.role != UserRole.student:
                raise HTTPException(404, "Student not found")
            student_id = student.id
        else:
            student_id = user.id

        if course.status != CourseStatus.published and course.instructor_id != user.id and user.role != UserRole.admin:
            raise HTTPException(404, "Course not found")

        existing = db.query(Enrollment).filter(Enrollment.course_id == course.id, Enrollment.user_id == student_id).first()
        if existing:
            raise HTTPException(400, "Already enrolled in this course")

        enrollment = Enrollment(course_id=course.id, user_id=student_id)
        db.add(enrollment)
        db.commit()
        db.refresh(enrollment)

        from app.modules.notifications.service import notify
        notify(db, student_id, "enrollment", "Welcome aboard! 🎉",
               f"You are now enrolled in “{course.title}”. Start learning right away.",
               f"/learn/{course.slug}")
        notify(db, course.instructor_id, "enrollment", "New enrollment",
               f"A new student just enrolled in “{course.title}”.",
               f"/teach/courses/{course.id}/students")
        return enrollment

    @staticmethod
    def drop(db: Session, course: Course, user: User) -> None:
        enrollment = db.query(Enrollment).filter(Enrollment.course_id == course.id, Enrollment.user_id == user.id).first()
        if not enrollment:
            raise HTTPException(404, "You are not enrolled in this course")
        db.query(LessonProgress).filter(LessonProgress.enrollment_id == enrollment.id).delete(synchronize_session=False)
        db.delete(enrollment)
        db.commit()

    @staticmethod
    def get_enrollment(db: Session, course_id: int, user_id: int) -> Enrollment:
        enrollment = db.query(Enrollment).filter(Enrollment.course_id == course_id, Enrollment.user_id == user_id).first()
        if not enrollment:
            raise HTTPException(404, "Enrollment not found")
        return enrollment

    @staticmethod
    def recompute_progress(db: Session, enrollment: Enrollment) -> float:
        total = db.query(func.count(Lesson.id)).filter(Lesson.course_id == enrollment.course_id).scalar() or 0
        done = db.query(func.count(LessonProgress.id)).join(
            Lesson, Lesson.id == LessonProgress.lesson_id
        ).filter(LessonProgress.enrollment_id == enrollment.id, Lesson.course_id == enrollment.course_id).scalar() or 0
        progress = round(done / total * 100, 1) if total else 0.0
        enrollment.progress = progress
        return progress

    @staticmethod
    def finalize_completion(db: Session, enrollment: Enrollment) -> None:
        """Shared completion path: when progress hits 100%, mark the enrollment
        completed, issue the certificate (idempotent) and notify the student.

        Used by both complete_lesson and the quiz auto-complete flow, so a
        course whose final lesson is a quiz still yields a certificate.
        """
        progress = EnrollmentService.recompute_progress(db, enrollment)
        if progress < 100 or enrollment.status == "completed":
            return
        enrollment.status = "completed"
        enrollment.completed_at = utcnow()
        db.commit()
        # modular events: certificate issuance + congratulation notification
        from app.modules.certificates.service import issue_certificate
        from app.modules.notifications.service import notify
        from app.modules.courses.models import Course
        course = db.get(Course, enrollment.course_id)
        cert = issue_certificate(db, enrollment.user_id, enrollment.course_id)
        notify(db, enrollment.user_id, "certificate", "🎓 Course completed!",
               f"Congratulations! You completed “{course.title}” and earned a certificate.",
               f"/certificates/{cert.serial}")

    @staticmethod
    def complete_lesson(db: Session, course: Course, lesson: Lesson, user: User) -> dict:
        enrollment = EnrollmentService.get_enrollment(db, course.id, user.id)
        existing = db.query(LessonProgress).filter(
            LessonProgress.enrollment_id == enrollment.id, LessonProgress.lesson_id == lesson.id).first()
        if not existing:
            db.add(LessonProgress(enrollment_id=enrollment.id, lesson_id=lesson.id))
            db.commit()

        EnrollmentService.finalize_completion(db, enrollment)
        db.commit()
        return {"progress": enrollment.progress, "status": enrollment.status}

    @staticmethod
    def uncomplete_lesson(db: Session, course: Course, lesson: Lesson, user: User) -> dict:
        enrollment = EnrollmentService.get_enrollment(db, course.id, user.id)
        db.query(LessonProgress).filter(
            LessonProgress.enrollment_id == enrollment.id, LessonProgress.lesson_id == lesson.id
        ).delete(synchronize_session=False)
        progress = EnrollmentService.recompute_progress(db, enrollment)
        if progress < 100 and enrollment.status == "completed":
            enrollment.status = "active"
            enrollment.completed_at = None
        db.commit()
        return {"progress": progress, "status": enrollment.status}

    @staticmethod
    def completed_lesson_ids(db: Session, enrollment_id: int) -> set[int]:
        return {r.lesson_id for r in db.query(LessonProgress.lesson_id).filter(LessonProgress.enrollment_id == enrollment_id)}

    @staticmethod
    def my_enrollments(db: Session, user: User) -> list[dict]:
        from app.modules.courses.service import CoursesService

        enrollments = (
            db.query(Enrollment).options(joinedload(Enrollment.course).joinedload(Course.instructor),
                                         joinedload(Enrollment.course).joinedload(Course.category))
            .filter(Enrollment.user_id == user.id).order_by(Enrollment.enrolled_at.desc()).all()
        )
        course_ids = [e.course_id for e in enrollments]
        maps = CoursesService.aggregate_maps(db, course_ids) if course_ids else {
            "enrollments": {}, "ratings": {}, "review_counts": {}, "lesson_counts": {}, "minutes": {}}
        result = []
        for e in enrollments:
            card = CoursesService.course_to_dict(db, e.course, maps)
            result.append({
                "id": e.id, "status": e.status, "progress": e.progress,
                "enrolled_at": e.enrolled_at.isoformat(), "completed_at": e.completed_at.isoformat() if e.completed_at else None,
                "course": card,
            })
        return result

    @staticmethod
    def course_students(db: Session, course: Course) -> list[dict]:
        enrollments = (
            db.query(Enrollment).options(joinedload(Enrollment.user))
            .filter(Enrollment.course_id == course.id).order_by(Enrollment.enrolled_at.desc()).all()
        )
        return [
            {
                "user": {"id": e.user.id, "full_name": e.user.full_name, "email": e.user.email,
                         "avatar_url": e.user.avatar_url},
                "progress": e.progress, "status": e.status,
                "enrolled_at": e.enrolled_at.isoformat(),
            }
            for e in enrollments
        ]
