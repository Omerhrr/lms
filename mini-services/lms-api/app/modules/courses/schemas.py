from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field, ConfigDict


# ---------- categories ----------

class CategoryIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: Optional[str] = None


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    description: Optional[str] = None


# ---------- courses ----------

class CourseCreateIn(BaseModel):
    title: str = Field(min_length=4, max_length=255)
    summary: str = Field(default="", max_length=500)
    description: str = ""
    category_id: Optional[int] = None
    price: float = Field(default=0.0, ge=0)
    level: Literal["beginner", "intermediate", "advanced"] = "beginner"
    language: str = "English"
    thumbnail_url: Optional[str] = None
    tags: list[str] = []


class CourseUpdateIn(BaseModel):
    title: Optional[str] = Field(default=None, min_length=4, max_length=255)
    summary: Optional[str] = Field(default=None, max_length=500)
    description: Optional[str] = None
    category_id: Optional[int] = None
    price: Optional[float] = Field(default=None, ge=0)
    level: Optional[Literal["beginner", "intermediate", "advanced"]] = None
    language: Optional[str] = None
    thumbnail_url: Optional[str] = None
    tags: Optional[list[str]] = None
    is_featured: Optional[bool] = None


class InstructorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    headline: Optional[str] = None
    avatar_url: Optional[str] = None


class LessonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    section_id: int
    title: str
    type: str
    duration_minutes: int
    position: int
    is_preview: bool
    video_url: Optional[str] = None
    file_url: Optional[str] = None
    content: Optional[str] = None


class LessonPublicOut(BaseModel):
    """Curriculum view for students — hides lesson body until enrolled."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    type: str
    duration_minutes: int
    position: int
    is_preview: bool


class SectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    position: int
    lessons: list[LessonPublicOut]


class SectionFullOut(SectionOut):
    lessons: list[LessonOut]


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rating: int
    comment: Optional[str] = None
    created_at: datetime
    user: InstructorOut


class ReviewIn(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=2000)


class CourseCardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    summary: str
    thumbnail_url: Optional[str] = None
    price: float
    level: str
    language: str
    tags: list = []
    is_featured: bool
    status: str
    rating: float = 0
    review_count: int = 0
    enrollment_count: int = 0
    total_minutes: int = 0
    lesson_count: int = 0
    instructor: InstructorOut
    category: Optional[CategoryOut] = None


class CourseDetailOut(CourseCardOut):
    description: str = ""
    sections: list[SectionOut] = []
    is_enrolled: bool = False
    has_reviewed: bool = False
