from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base import Base
from app.shared.utils import utcnow


class Enquiry(Base):
    """A message sent from the website's Contact form."""
    __tablename__ = "enquiries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    topic: Mapped[str] = mapped_column(String(60), default="General Enquiry")
    subject: Mapped[str] = mapped_column(String(255), default="")
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="new")   # new | handled
    created_at: Mapped[object] = mapped_column(DateTime, default=utcnow, index=True)


class SiteSetting(Base):
    """One editable website section (see site/content.py), stored as JSON."""
    __tablename__ = "site_settings"

    key: Mapped[str] = mapped_column(String(40), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON)
    updated_at: Mapped[object] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    updated_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
