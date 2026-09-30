import uuid

from sqlalchemy import DateTime, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.base import Base
from app.shared.utils import utcnow


class Certificate(Base):
    __tablename__ = "certificates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    serial: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    # snapshots keep the certificate valid even if names change later
    course_title: Mapped[str] = mapped_column(String(255))
    user_name: Mapped[str] = mapped_column(String(255))
    instructor_name: Mapped[str] = mapped_column(String(255), default="")
    issued_at: Mapped[object] = mapped_column(DateTime, default=utcnow)
