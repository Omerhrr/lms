import enum

from sqlalchemy import String, Text, Float, Boolean, Integer, Enum, DateTime, ForeignKey, UniqueConstraint, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.base import Base
from app.shared.utils import utcnow


class CourseStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    archived = "archived"


class CourseLevel(str, enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class LessonType(str, enum.Enum):
    video = "video"
    text = "text"
    file = "file"
    quiz = "quiz"


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    slug: Mapped[str] = mapped_column(String(140), unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime, default=utcnow)


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(280), unique=True, index=True)
    summary: Mapped[str] = mapped_column(Text, default="")
    description: Mapped[str] = mapped_column(Text, default="")
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    instructor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[CourseStatus] = mapped_column(Enum(CourseStatus), default=CourseStatus.draft)
    price: Mapped[float] = mapped_column(Float, default=0.0)  # 0 => free
    level: Mapped[CourseLevel] = mapped_column(Enum(CourseLevel), default=CourseLevel.beginner)
    language: Mapped[str] = mapped_column(String(50), default="English")
    thumbnail_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[object] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[object] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    category = relationship("Category", foreign_keys=[category_id])
    instructor = relationship("User", foreign_keys=[instructor_id])
    sections = relationship("Section", back_populates="course", order_by="Section.position", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="course", cascade="all, delete-orphan")


class Section(Base):
    __tablename__ = "sections"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    position: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[object] = mapped_column(DateTime, default=utcnow)

    course = relationship("Course", back_populates="sections")
    lessons = relationship("Lesson", back_populates="section", order_by="Lesson.position", cascade="all, delete-orphan")


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    section_id: Mapped[int] = mapped_column(ForeignKey("sections.id", ondelete="CASCADE"), index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)  # denormalized
    title: Mapped[str] = mapped_column(String(255))
    type: Mapped[LessonType] = mapped_column(Enum(LessonType), default=LessonType.video)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)       # text lessons
    video_url: Mapped[str | None] = mapped_column(String(500), nullable=True)  # video lessons (embed URL)
    file_url: Mapped[str | None] = mapped_column(String(500), nullable=True)   # downloadable resource
    duration_minutes: Mapped[int] = mapped_column(Integer, default=5)
    position: Mapped[int] = mapped_column(Integer, default=0)
    is_preview: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[object] = mapped_column(DateTime, default=utcnow)

    section = relationship("Section", back_populates="lessons")


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (UniqueConstraint("course_id", "user_id", name="uq_review_course_user"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    rating: Mapped[int] = mapped_column(Integer)  # 1..5
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime, default=utcnow)

    course = relationship("Course", back_populates="reviews")
    user = relationship("User", foreign_keys=[user_id])
