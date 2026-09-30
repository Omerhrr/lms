import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.certificates.models import Certificate


def issue_certificate(db: Session, user_id: int, course_id: int) -> Certificate:
    """Idempotent: returns the existing certificate if already issued."""
    existing = db.query(Certificate).filter(Certificate.user_id == user_id, Certificate.course_id == course_id).first()
    if existing:
        return existing

    from app.modules.auth.models import User
    from app.modules.courses.models import Course

    user = db.get(User, user_id)
    course = db.get(Course, course_id)
    if not user or not course:
        raise HTTPException(404, "User or course not found")

    cert = Certificate(
        serial=f"LH-{uuid.uuid4().hex[:12].upper()}",
        course_id=course_id,
        user_id=user_id,
        course_title=course.title,
        user_name=user.full_name,
        instructor_name=course.instructor.full_name if course.instructor else "",
    )
    db.add(cert)
    db.commit()
    db.refresh(cert)
    return cert
