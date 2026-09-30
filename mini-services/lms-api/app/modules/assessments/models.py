import enum

from sqlalchemy import String, Text, Integer, Float, Boolean, Enum, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.base import Base
from app.shared.utils import utcnow


class QuestionType(str, enum.Enum):
    single_choice = "single_choice"
    multi_choice = "multi_choice"
    true_false = "true_false"
    short_answer = "short_answer"


class Quiz(Base):
    __tablename__ = "quizzes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    time_limit_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)  # None = untimed
    passing_score: Mapped[int] = mapped_column(Integer, default=60)                  # percent
    max_attempts: Mapped[int] = mapped_column(Integer, default=0)                    # 0 = unlimited
    created_at: Mapped[object] = mapped_column(DateTime, default=utcnow)

    questions = relationship("Question", back_populates="quiz", order_by="Question.position", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id", ondelete="CASCADE"), index=True)
    type: Mapped[QuestionType] = mapped_column(Enum(QuestionType), default=QuestionType.single_choice)
    text: Mapped[str] = mapped_column(Text)
    options: Mapped[list] = mapped_column(JSON, default=list)          # ["A", "B", ...]
    correct: Mapped[list] = mapped_column(JSON, default=list)          # indices [0] / [0,2] / ["paris"]
    points: Mapped[float] = mapped_column(Float, default=1.0)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    position: Mapped[int] = mapped_column(Integer, default=0)

    quiz = relationship("Quiz", back_populates="questions")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    answers: Mapped[dict] = mapped_column(JSON, default=dict)  # {"12": [0,2], "13": ["python"]}
    score: Mapped[float] = mapped_column(Float, default=0.0)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    submitted_at: Mapped[object] = mapped_column(DateTime, default=utcnow)

    user = relationship("User", foreign_keys=[user_id])


class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    instructions: Mapped[str] = mapped_column(Text, default="")
    due_date: Mapped[object | None] = mapped_column(DateTime, nullable=True)
    max_points: Mapped[float] = mapped_column(Float, default=100.0)
    allow_file: Mapped[bool] = mapped_column(Boolean, default=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[object] = mapped_column(DateTime, default=utcnow)


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    text_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    submitted_at: Mapped[object] = mapped_column(DateTime, default=utcnow)
    grade: Mapped[float | None] = mapped_column(Float, nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    graded_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    graded_at: Mapped[object | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="submitted")  # submitted | graded

    user = relationship("User", foreign_keys=[user_id])
