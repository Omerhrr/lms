from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import any_user, optional_user, staff_required, admin_required
from app.modules.auth.models import User
from app.modules.courses.models import CourseStatus
from app.modules.courses.schemas import (
    CategoryIn, CategoryOut, CourseCreateIn, CourseUpdateIn, ReviewIn,
)
from app.modules.courses.service import CoursesService

router = APIRouter(tags=["courses"])


# ============ public catalog ============

@router.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    return [{"id": c.id, "name": c.name, "slug": c.slug, "description": c.description}
            for c in CoursesService.list_categories(db)]


@router.post("/categories", status_code=201)
def create_category(data: CategoryIn, db: Session = Depends(get_db), user: User = Depends(admin_required)):
    cat = CoursesService.create_category(db, data)
    return {"id": cat.id, "name": cat.name, "slug": cat.slug, "description": cat.description}


@router.put("/categories/{category_id}")
def update_category(category_id: int, data: CategoryIn, db: Session = Depends(get_db), user: User = Depends(admin_required)):
    cat = CoursesService.update_category(db, category_id, data)
    return {"id": cat.id, "name": cat.name, "slug": cat.slug, "description": cat.description}


@router.delete("/categories/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db), user: User = Depends(admin_required)):
    CoursesService.delete_category(db, category_id)
    return {"message": "Category deleted"}


@router.get("/courses/featured")
def featured_courses(db: Session = Depends(get_db)):
    return CoursesService.list_featured(db)


@router.get("/courses")
def list_courses(
    search: str | None = Query(None),
    category_id: int | None = Query(None),
    level: str | None = Query(None),
    price: str | None = Query(None),
    sort: str = Query("newest"),
    page: int = Query(1, ge=1),
    size: int = Query(12, ge=1, le=48),
    db: Session = Depends(get_db),
):
    return CoursesService.list_public_courses(
        db, search=search, category_id=category_id, level=level, price=price,
        sort=sort, page=page, size=size,
    )


@router.get("/courses/{slug}")
def course_detail(slug: str, db: Session = Depends(get_db), user: User | None = Depends(optional_user)):
    course = CoursesService.get_course_by_slug(db, slug, user)
    data = CoursesService.course_to_dict(db, course, detail=True)
    # enrollment + review flags
    if user:
        from app.modules.enrollments.models import Enrollment
        from app.modules.courses.models import Review
        data["is_enrolled"] = db.query(Enrollment).filter(
            Enrollment.course_id == course.id, Enrollment.user_id == user.id).first() is not None
        data["has_reviewed"] = db.query(Review).filter(
            Review.course_id == course.id, Review.user_id == user.id).first() is not None
    else:
        data["is_enrolled"] = False
        data["has_reviewed"] = False
    data["can_manage"] = bool(user and (user.id == course.instructor_id or user.role == "admin"))
    return data


@router.get("/courses/{slug}/reviews")
def course_reviews(slug: str, db: Session = Depends(get_db), user: User | None = Depends(optional_user)):
    course = CoursesService.get_course_by_slug(db, slug, user)
    return CoursesService.list_reviews(db, course)


@router.post("/courses/{slug}/reviews", status_code=201)
def review_course(slug: str, data: ReviewIn, db: Session = Depends(get_db), user: User = Depends(any_user)):
    course = CoursesService.get_course_by_slug(db, slug, user)
    review = CoursesService.upsert_review(db, course, user, data.rating, data.comment)
    return {"id": review.id, "rating": review.rating, "comment": review.comment}


@router.get("/lessons/{lesson_id}")
def lesson_content(lesson_id: int, db: Session = Depends(get_db), user: User | None = Depends(optional_user)):
    """Full lesson content - for enrolled students, course owner, or free previews."""
    from app.modules.courses.models import Lesson
    from app.modules.enrollments.models import Enrollment

    lesson = db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(404, "Lesson not found")
    course = CoursesService.get_course(db, lesson.course_id)

    allowed = bool(lesson.is_preview)
    if user and not allowed:
        if user.role == "admin" or course.instructor_id == user.id:
            allowed = True
        else:
            allowed = db.query(Enrollment).filter_by(course_id=course.id, user_id=user.id).first() is not None
    if not allowed:
        raise HTTPException(403, "Enroll in this course to access this lesson")

    return {
        "id": lesson.id, "section_id": lesson.section_id, "course_id": lesson.course_id,
        "title": lesson.title, "type": lesson.type.value, "content": lesson.content,
        "video_url": lesson.video_url, "file_url": lesson.file_url,
        "duration_minutes": lesson.duration_minutes, "is_preview": lesson.is_preview,
    }


# ============ instructor (teach) ============

@router.get("/teach/courses")
def my_teaching_courses(db: Session = Depends(get_db), user: User = Depends(staff_required)):
    return CoursesService.list_instructor_courses(db, user)


@router.post("/teach/courses", status_code=201)
def create_course(data: CourseCreateIn, db: Session = Depends(get_db), user: User = Depends(staff_required)):
    course = CoursesService.create_course(db, data, user)
    return {"id": course.id, "slug": course.slug}


@router.get("/teach/courses/{course_id}")
def edit_course_data(course_id: int, db: Session = Depends(get_db), user: User = Depends(staff_required)):
    course = CoursesService.get_course(db, course_id)
    CoursesService.assert_can_manage(course, user)
    return CoursesService.get_course_full_for_edit(db, course)


@router.put("/teach/courses/{course_id}")
def update_course(course_id: int, data: CourseUpdateIn, db: Session = Depends(get_db), user: User = Depends(staff_required)):
    course = CoursesService.get_course(db, course_id)
    CoursesService.assert_can_manage(course, user)
    CoursesService.update_course(db, course, data)
    return {"message": "Course updated"}


@router.post("/teach/courses/{course_id}/publish")
def publish_course(course_id: int, db: Session = Depends(get_db), user: User = Depends(staff_required)):
    course = CoursesService.get_course(db, course_id)
    CoursesService.assert_can_manage(course, user)
    if not course.sections:
        raise HTTPException(400, "Add at least one section before publishing")
    CoursesService.set_status(db, course, CourseStatus.published)
    return {"message": "Course published"}


@router.post("/teach/courses/{course_id}/unpublish")
def unpublish_course(course_id: int, db: Session = Depends(get_db), user: User = Depends(staff_required)):
    course = CoursesService.get_course(db, course_id)
    CoursesService.assert_can_manage(course, user)
    CoursesService.set_status(db, course, CourseStatus.draft)
    return {"message": "Course moved back to draft"}


@router.post("/teach/courses/{course_id}/archive")
def archive_course(course_id: int, db: Session = Depends(get_db), user: User = Depends(staff_required)):
    course = CoursesService.get_course(db, course_id)
    CoursesService.assert_can_manage(course, user)
    CoursesService.set_status(db, course, CourseStatus.archived)
    return {"message": "Course archived"}


@router.delete("/teach/courses/{course_id}")
def delete_course(course_id: int, db: Session = Depends(get_db), user: User = Depends(staff_required)):
    course = CoursesService.get_course(db, course_id)
    CoursesService.assert_can_manage(course, user)
    CoursesService.delete_course(db, course)
    return {"message": "Course deleted"}


# ---- sections ----

@router.post("/teach/courses/{course_id}/sections", status_code=201)
def add_section(course_id: int, body: dict, db: Session = Depends(get_db), user: User = Depends(staff_required)):
    course = CoursesService.get_course(db, course_id)
    CoursesService.assert_can_manage(course, user)
    title = (body.get("title") or "").strip()
    if not title:
        raise HTTPException(400, "Section title is required")
    s = CoursesService.add_section(db, course, title)
    return {"id": s.id, "title": s.title, "position": s.position}


@router.put("/teach/sections/{section_id}")
def update_section(section_id: int, body: dict, db: Session = Depends(get_db), user: User = Depends(staff_required)):
    from app.modules.courses.models import Section
    section = db.get(Section, section_id)
    if not section:
        raise HTTPException(404, "Section not found")
    course = CoursesService.get_course(db, section.course_id)
    CoursesService.assert_can_manage(course, user)
    CoursesService.update_section(db, section, (body.get("title") or section.title))
    return {"message": "Section updated"}


@router.delete("/teach/sections/{section_id}")
def delete_section(section_id: int, db: Session = Depends(get_db), user: User = Depends(staff_required)):
    from app.modules.courses.models import Section
    section = db.get(Section, section_id)
    if not section:
        raise HTTPException(404, "Section not found")
    course = CoursesService.get_course(db, section.course_id)
    CoursesService.assert_can_manage(course, user)
    CoursesService.delete_section(db, section)
    return {"message": "Section deleted"}


@router.post("/teach/sections/{section_id}/move")
def move_section(section_id: int, body: dict, db: Session = Depends(get_db), user: User = Depends(staff_required)):
    from app.modules.courses.models import Section
    section = db.get(Section, section_id)
    if not section:
        raise HTTPException(404, "Section not found")
    course = CoursesService.get_course(db, section.course_id)
    CoursesService.assert_can_manage(course, user)
    CoursesService.move_section(db, course, section, body.get("direction", "up"))
    return {"message": "Section moved"}


# ---- lessons ----

@router.post("/teach/sections/{section_id}/lessons", status_code=201)
def add_lesson(section_id: int, body: dict, db: Session = Depends(get_db), user: User = Depends(staff_required)):
    from app.modules.courses.models import Section
    section = db.get(Section, section_id)
    if not section:
        raise HTTPException(404, "Section not found")
    course = CoursesService.get_course(db, section.course_id)
    CoursesService.assert_can_manage(course, user)
    title = (body.get("title") or "").strip()
    if not title:
        raise HTTPException(400, "Lesson title is required")
    lesson = CoursesService.add_lesson(db, section, **body)
    return {"id": lesson.id, "title": lesson.title, "type": lesson.type.value, "position": lesson.position}


@router.put("/teach/lessons/{lesson_id}")
def update_lesson(lesson_id: int, body: dict, db: Session = Depends(get_db), user: User = Depends(staff_required)):
    from app.modules.courses.models import Lesson
    lesson = db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(404, "Lesson not found")
    course = CoursesService.get_course(db, lesson.course_id)
    CoursesService.assert_can_manage(course, user)
    CoursesService.update_lesson(db, lesson, body)
    return {"message": "Lesson updated"}


@router.delete("/teach/lessons/{lesson_id}")
def delete_lesson(lesson_id: int, db: Session = Depends(get_db), user: User = Depends(staff_required)):
    from app.modules.courses.models import Lesson
    lesson = db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(404, "Lesson not found")
    course = CoursesService.get_course(db, lesson.course_id)
    CoursesService.assert_can_manage(course, user)
    CoursesService.delete_lesson(db, lesson)
    return {"message": "Lesson deleted"}


@router.post("/teach/lessons/{lesson_id}/move")
def move_lesson(lesson_id: int, body: dict, db: Session = Depends(get_db), user: User = Depends(staff_required)):
    from app.modules.courses.models import Lesson
    lesson = db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(404, "Lesson not found")
    course = CoursesService.get_course(db, lesson.course_id)
    CoursesService.assert_can_manage(course, user)
    section = lesson.section
    CoursesService.move_lesson(db, section, lesson, body.get("direction", "up"))
    return {"message": "Lesson moved"}
