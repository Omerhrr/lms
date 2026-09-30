from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EnrollmentCardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    status: str
    progress: float
    enrolled_at: datetime
    completed_at: datetime | None = None
    course: dict  # enriched below


class EnrolledStudentOut(BaseModel):
    user: dict
    progress: float
    status: str
    enrolled_at: datetime
