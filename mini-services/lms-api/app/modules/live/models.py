from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.base import Base
from app.shared.utils import utcnow


class LiveSession(Base):
    """A scheduled live class for a course (built-in Jitsi room or an external Zoom/Meet/Teams link)."""
    __tablename__ = "live_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    host_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    starts_at: Mapped[object] = mapped_column(DateTime, index=True)       # naive UTC
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60)
    provider: Mapped[str] = mapped_column(String(20), default="jitsi")    # jitsi | external
    external_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    room: Mapped[str] = mapped_column(String(80), unique=True)            # unguessable room name
    status: Mapped[str] = mapped_column(String(20), default="scheduled")  # scheduled | cancelled
    recording_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[object] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    course = relationship("Course")
    host = relationship("User")


class LiveAttendance(Base):
    __tablename__ = "live_attendance"
    __table_args__ = (UniqueConstraint("session_id", "user_id", name="uq_live_attendance"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("live_sessions.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    first_joined_at: Mapped[object] = mapped_column(DateTime, default=utcnow)
    last_joined_at: Mapped[object] = mapped_column(DateTime, default=utcnow)
    join_count: Mapped[int] = mapped_column(Integer, default=1)

    user = relationship("User")
