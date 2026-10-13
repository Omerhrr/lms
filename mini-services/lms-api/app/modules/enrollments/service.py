from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.modules.auth.models import User, UserRole
from app.modules.courses.models import Course, CourseStatus, Lesson
from app.modules.enrollments.models import Enrollment, LessonProgress
from app.shared.utils import utcnow


def lesson_unlock_at(enrollment: Enrollment | None, lesson: Lesson):
    """When a drip lesson opens for this enrollment (None = available now / not dripped)."""
    from datetime import timedelta
    if not enrollment or not lesson.drip_days or lesson.drip_days <= 0:
        return None
    return enrollment.enrolled_at + timedelta(days=lesson.drip_days)


def lesson_is_locked(enrollment: Enrollment | None, lesson: Lesson) -> bool:
    unlock = lesson_unlock_at(enrollment, lesson)
    return unlock is not None and unlock > utcnow()


def assert_lesson_unlocked(db: Session, lesson: Lesson, user: User) -> None:
    """Course owners/admins see everything; students wait for drip-released lessons."""
    course = db.get(Course, lesson.course_id)
    if user.role == UserRole.admin or (course and course.instructor_id == user.id):
        return
    enrollment = db.query(Enrollment).filter_by(course_id=lesson.course_id, user_id=user.id).first()
    if lesson_is_locked(enrollment, lesson):
        unlock = lesson_unlock_at(enrollment, lesson)
        raise HTTPException(403, f"This lesson unlocks on {unlock.strftime('%d %b %Y, %H:%M')} UTC")


def missing_prerequisites(db: Session, course: Course, user_id: int) -> list[Course]:
    """Prerequisite courses the user has not completed yet."""
    from app.modules.courses.models import CoursePrerequisite
    prereq_ids = [p.prerequisite_id for p in db.query(CoursePrerequisite).filter_by(course_id=course.id)]
    if not prereq_ids:
        return []
    done = {e.course_id for e in db.query(Enrollment).filter(
        Enrollment.user_id == user_id, Enrollment.course_id.in_(prereq_ids), Enrollment.status == "completed")}
    return [c for c in db.query(Course).filter(Course.id.in_(prereq_ids)).all() if c.id not in done]


class EnrollmentService:

    @staticmethod
    def enroll(db: Session, course: Course, user: User, target_user_id: int | None = None,
               *, paid: bool = False, quiet: bool = False) -> Enrollment:
        """Anyone may enroll themselves; instructors/admins may also enroll a student."""
        is_manager = user.role == UserRole.admin or course.instructor_id == user.id
        manual = target_user_id is not None and target_user_id != user.id
        if manual:
            # only the course's own instructor (or an admin) may enroll someone else
            if not is_manager:
                raise HTTPException(403, "You can only enroll students in courses you manage")
            student = db.get(User, target_user_id)
            if not student or student.role != UserRole.student or not student.is_active:
                raise HTTPException(404, "Student not found")
            student_id = student.id
        else:
            student_id = user.id

        if course.status != CourseStatus.published and not is_manager:
            raise HTTPException(404, "Course not found")

        if (course.price or 0) > 0 and not manual and not is_manager and not paid:
            from app.core.config import settings
            if settings.payments_enabled:
                raise HTTPException(402, "This is a paid course - complete checkout to enroll.")
            if not settings.ALLOW_UNPAID_ENROLLMENT:
                raise HTTPException(402, "Online payment isn't available yet for this course. "
                                         "Please contact the instructor to enroll.")

        existing = db.query(Enrollment).filter(Enrollment.course_id == course.id, Enrollment.user_id == student_id).first()
        if existing:
            raise HTTPException(400, "Already enrolled in this course")

        if not manual and not is_manager:
            missing = missing_prerequisites(db, course, student_id)
            if missing:
                names = ", ".join(f"“{c.title}”" for c in missing)
                raise HTTPException(403, f"Complete {names} before enrolling in this course")

        enrollment = Enrollment(course_id=course.id, user_id=student_id)
        db.add(enrollment)
        db.commit()
        db.refresh(enrollment)

        from app.modules.notifications.service import notify
        from app.shared import emails
        student = db.get(User, student_id)
        if student and not quiet:
            emails.enrolled(student.email, student.full_name, course.title, course.slug)
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
        if not course:
            return
        cert = issue_certificate(db, enrollment.user_id, enrollment.course_id)
        from app.shared import emails
        student = db.get(User, enrollment.user_id)
        if student:
            emails.certificate_issued(student.email, student.full_name, course.title, cert.serial)
        notify(db, enrollment.user_id, "certificate", "🎓 Course completed!",
               f"Congratulations! You completed “{course.title}” and earned a certificate.",
               f"/certificates/{cert.serial}")

    @staticmethod
    def complete_lesson(db: Session, course: Course, lesson: Lesson, user: User) -> dict:
        enrollment = EnrollmentService.get_enrollment(db, course.id, user.id)
        assert_lesson_unlocked(db, lesson, user)
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
        # ordered lessons per course + what this learner has completed (2 queries total)
        from app.modules.courses.models import Section
        ordered: dict[int, list] = {}
        for l, _ in (db.query(Lesson, Section.position).join(Section, Section.id == Lesson.section_id)
                     .filter(Lesson.course_id.in_(course_ids or [0]))
                     .order_by(Section.position, Lesson.position).all()):
            ordered.setdefault(l.course_id, []).append(l)
        done: dict[int, set] = {}
        for p in db.query(LessonProgress).filter(LessonProgress.enrollment_id.in_([e.id for e in enrollments] or [0])):
            done.setdefault(p.enrollment_id, set()).add(p.lesson_id)
        maps = CoursesService.aggregate_maps(db, course_ids) if course_ids else {
            "enrollments": {}, "ratings": {}, "review_counts": {}, "lesson_counts": {}, "minutes": {}}
        result = []
        for e in enrollments:
            card = CoursesService.course_to_dict(db, e.course, maps)
            lessons = ordered.get(e.course_id, [])
            finished = done.get(e.id, set())
            remaining = [l for l in lessons if l.id not in finished]
            nxt = next((l for l in remaining if not lesson_is_locked(e, l)), None)
            result.append({
                "id": e.id, "status": e.status, "progress": e.progress,
                "remaining_minutes": sum(l.duration_minutes or 0 for l in remaining),
                "remaining_lessons": len(remaining),
                "next_lesson": {"id": nxt.id, "title": nxt.title, "type": nxt.type.value,
                                "duration_minutes": nxt.duration_minutes} if nxt else None,
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
