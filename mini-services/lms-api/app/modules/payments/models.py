from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.base import Base
from app.shared.utils import utcnow


class Payment(Base):
    """One checkout attempt. Amounts are stored in the currency's minor unit (kobo for NGN)."""
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    reference: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    # kept for accounting even if the user or course is later deleted
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    course_id: Mapped[int | None] = mapped_column(ForeignKey("courses.id", ondelete="SET NULL"), index=True, nullable=True)
    course_title: Mapped[str] = mapped_column(String(255), default="")   # snapshot for receipts
    amount: Mapped[int] = mapped_column(Integer)                          # minor units
    currency: Mapped[str] = mapped_column(String(3), default="NGN")
    status: Mapped[str] = mapped_column(String(20), default="pending")    # pending | success | failed | abandoned
    provider: Mapped[str] = mapped_column(String(20), default="paystack")
    provider_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    channel: Mapped[str | None] = mapped_column(String(30), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime, default=utcnow)
    paid_at: Mapped[object | None] = mapped_column(DateTime, nullable=True)

    user = relationship("User")
    course = relationship("Course")
