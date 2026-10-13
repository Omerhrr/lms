from fastapi import HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.modules.auth.models import User, UserRole
from app.modules.courses.models import Category, Course, CourseStatus, Section, Lesson, Review, LessonType, CoursePrerequisite
from app.modules.courses.schemas import (
    CourseCreateIn, CourseUpdateIn, CategoryIn, LessonCreateIn, LessonUpdateIn,
)
from app.shared.utils import unique_slug, utcnow, safe_url, sanitize_html, sanitize_rich_content


class CoursesService:

    # ---------- permission helpers ----------

    @staticmethod
    def get_course(db: Session, course_id: int) -> Course:
        course = db.get(Course, course_id)
        if not course:
            raise HTTPException(404, "Course not found")
        return course

    @staticmethod
    def assert_can_manage(course: Course, user: User):
        if user.role == UserRole.admin:
            return
        if course.instructor_id != user.id:
            raise HTTPException(403, "You can only manage your own courses")

    # ---------- categories ----------

    @staticmethod
    def list_categories(db: Session) -> list[Category]:
        return db.query(Category).order_by(Category.name).all()

    @staticmethod
    def create_category(db: Session, data: CategoryIn) -> Category:
        if db.query(Category).filter(func.lower(Category.name) == data.name.lower()).first():
            raise HTTPException(400, "Category already exists")
        cat = Category(name=data.name, slug=unique_slug(db, Category, data.name), description=data.description)
        db.add(cat)
        db.commit()
        db.refresh(cat)
        return cat

    @staticmethod
    def update_category(db: Session, cat_id: int, data: CategoryIn) -> Category:
        cat = db.get(Category, cat_id)
        if not cat:
            raise HTTPException(404, "Category not found")
        cat.name = data.name
        cat.description = data.description
        db.commit()
        db.refresh(cat)
        return cat

    @staticmethod
    def delete_category(db: Session, cat_id: int) -> None:
        cat = db.get(Category, cat_id)
        if not cat:
            raise HTTPException(404, "Category not found")
        count = db.query(Course).filter(Course.category_id == cat_id).count()
        if count:
            raise HTTPException(400, f"Category has {count} course(s); move them first")
        db.delete(cat)
        db.commit()

    # ---------- course CRUD ----------

    @staticmethod
    def create_course(db: Session, data: CourseCreateIn, instructor: User) -> Course:
        CoursesService._check_category(db, data.category_id)
        course = Course(
            title=data.title.strip(),
            slug=unique_slug(db, Course, data.title),
            summary=data.summary,
            description=sanitize_html(data.description) or "",
            category_id=data.category_id,
            instructor_id=instructor.id,
            price=data.price,
            level=data.level,
            language=data.language,
            thumbnail_url=safe_url(data.thumbnail_url, "thumbnail_url"),
            tags=[str(t)[:50] for t in data.tags][:20],
            outcomes=CoursesService._clean_outcomes(data.outcomes),
        )
        db.add(course)
        db.commit()
        db.refresh(course)
        return course

    @staticmethod
    def _clean_outcomes(items) -> list[str]:
        return [str(o).strip()[:200] for o in (items or []) if str(o).strip()][:12]

    @staticmethod
    def _check_category(db: Session, category_id) -> None:
        if category_id is not None and not db.get(Category, category_id):
            raise HTTPException(400, "Category not found")

    @staticmethod
    def update_course(db: Session, course: Course, data: CourseUpdateIn, user: User) -> Course:
        payload = data.model_dump(exclude_unset=True)
        if "is_featured" in payload and user.role != UserRole.admin:
            # featuring on the homepage is an editorial decision, not the instructor's
            raise HTTPException(403, "Only admins can feature courses")
        if "category_id" in payload:
            CoursesService._check_category(db, payload["category_id"])
        if "description" in payload:
            payload["description"] = sanitize_html(payload["description"]) or ""
        if "thumbnail_url" in payload:
            payload["thumbnail_url"] = safe_url(payload["thumbnail_url"], "thumbnail_url")
        if payload.get("tags") is not None:
            payload["tags"] = [str(t)[:50] for t in payload["tags"]][:20]
        if "outcomes" in payload:
            payload["outcomes"] = CoursesService._clean_outcomes(payload["outcomes"])
        if "title" in payload and payload["title"]:
            course.title = payload["title"].strip()
            course.slug = unique_slug(db, Course, course.title, exclude_id=course.id)
        for field in ("summary", "description", "category_id", "price", "level", "language",
                      "thumbnail_url", "tags", "outcomes", "is_featured"):
            if field in payload:
                setattr(course, field, payload[field])
        course.updated_at = utcnow()
        db.commit()
        db.refresh(course)
        return course

    @staticmethod
    def set_status(db: Session, course: Course, status: CourseStatus) -> Course:
        course.status = status
        db.commit()
        return course

    @staticmethod
    def delete_course(db: Session, course: Course) -> None:
        """Modular-monolith cleanup: purge rows owned by other modules that reference this course."""
        from app.modules.enrollments.models import Enrollment, LessonProgress
        from app.modules.assessments.models import Quiz, Question, QuizAttempt, Assignment, Submission
        from app.modules.discussions.models import Thread, Post
        from app.modules.notifications.models import Announcement
        from app.modules.certificates.models import Certificate

        lesson_ids = [l.id for l in db.query(Lesson.id).filter(Lesson.course_id == course.id)]
        quiz_ids = [q.id for q in db.query(Quiz.id).filter(Quiz.lesson_id.in_(lesson_ids))] if lesson_ids else []
        assignment_ids = [a.id for a in db.query(Assignment.id).filter(Assignment.course_id == course.id)]
        thread_ids = [t.id for t in db.query(Thread.id).filter(Thread.course_id == course.id)]
        enrollment_ids = [e.id for e in db.query(Enrollment.id).filter(Enrollment.course_id == course.id)]

        if quiz_ids:
            db.query(QuizAttempt).filter(QuizAttempt.quiz_id.in_(quiz_ids)).delete(synchronize_session=False)
            db.query(Question).filter(Question.quiz_id.in_(quiz_ids)).delete(synchronize_session=False)
            db.query(Quiz).filter(Quiz.id.in_(quiz_ids)).delete(synchronize_session=False)
        if assignment_ids:
            db.query(Submission).filter(Submission.assignment_id.in_(assignment_ids)).delete(synchronize_session=False)
            db.query(Assignment).filter(Assignment.id.in_(assignment_ids)).delete(synchronize_session=False)
        if thread_ids:
            # replies point at each other via parent_id; clear that first so FK order doesn't matter
            db.query(Post).filter(Post.thread_id.in_(thread_ids)).update({"parent_id": None}, synchronize_session=False)
            db.query(Post).filter(Post.thread_id.in_(thread_ids)).delete(synchronize_session=False)
            db.query(Thread).filter(Thread.id.in_(thread_ids)).delete(synchronize_session=False)
        db.query(Announcement).filter(Announcement.course_id == course.id).delete(synchronize_session=False)
        db.query(Certificate).filter(Certificate.course_id == course.id).delete(synchronize_session=False)
        db.query(Review).filter(Review.course_id == course.id).delete(synchronize_session=False)
        from app.modules.payments.models import Payment
        db.query(Payment).filter(Payment.course_id == course.id).update({"course_id": None}, synchronize_session=False)
        db.query(CoursePrerequisite).filter(
            (CoursePrerequisite.course_id == course.id) | (CoursePrerequisite.prerequisite_id == course.id)
        ).delete(synchronize_session=False)
        if lesson_ids:
            db.query(LessonProgress).filter(LessonProgress.lesson_id.in_(lesson_ids)).delete(synchronize_session=False)
        if enrollment_ids:
            db.query(LessonProgress).filter(LessonProgress.enrollment_id.in_(enrollment_ids)).delete(synchronize_session=False)
            db.query(Enrollment).filter(Enrollment.id.in_(enrollment_ids)).delete(synchronize_session=False)
        db.delete(course)
        db.commit()

    # ---------- aggregation helpers ----------

    @staticmethod
    def aggregate_maps(db: Session, course_ids: list[int]):
        from app.modules.enrollments.models import Enrollment

        maps = {"enrollments": {}, "ratings": {}, "review_counts": {}, "lesson_counts": {}, "minutes": {}}
        if not course_ids:
            return maps

        rows = (
            db.query(Enrollment.course_id, func.count(Enrollment.id))
            .filter(Enrollment.course_id.in_(course_ids)).group_by(Enrollment.course_id).all()
        )
        maps["enrollments"] = {cid: c for cid, c in rows}

        rows = (
            db.query(Review.course_id, func.avg(Review.rating), func.count(Review.id))
            .filter(Review.course_id.in_(course_ids)).group_by(Review.course_id).all()
        )
        maps["ratings"] = {cid: round(float(a) or 0, 1) for cid, a, c in rows}
        maps["review_counts"] = {cid: int(c) for cid, a, c in rows}

        rows = (
            db.query(Lesson.course_id, func.count(Lesson.id), func.coalesce(func.sum(Lesson.duration_minutes), 0))
            .filter(Lesson.course_id.in_(course_ids)).group_by(Lesson.course_id).all()
        )
        maps["lesson_counts"] = {cid: int(c) for cid, c, m in rows}
        maps["minutes"] = {cid: int(m) for cid, c, m in rows}
        return maps

    @staticmethod
    def course_to_dict(db: Session, course: Course, maps=None, detail=False) -> dict:
        if maps is None:
            maps = CoursesService.aggregate_maps(db, [course.id])
        cid = course.id
        data = {
            "id": course.id,
            "title": course.title,
            "slug": course.slug,
            "summary": course.summary,
            "description": (sanitize_html(course.description) or "") if detail else "",
            "thumbnail_url": course.thumbnail_url,
            "price": course.price,
            "level": course.level.value if hasattr(course.level, "value") else str(course.level),
            "language": course.language,
            "tags": course.tags or [],
            "is_featured": course.is_featured,
            "status": course.status.value if hasattr(course.status, "value") else str(course.status),
            "rating": maps["ratings"].get(cid, 0),
            "review_count": maps["review_counts"].get(cid, 0),
            "enrollment_count": maps["enrollments"].get(cid, 0),
            "lesson_count": maps["lesson_counts"].get(cid, 0),
            "total_minutes": maps["minutes"].get(cid, 0),
            "instructor": (
                {"id": course.instructor.id, "full_name": course.instructor.full_name,
                 "headline": course.instructor.headline, "avatar_url": course.instructor.avatar_url}
                if course.instructor else
                {"id": None, "full_name": "Former instructor", "headline": None, "avatar_url": None}
            ),
            "category": (
                {"id": course.category.id, "name": course.category.name,
                 "slug": course.category.slug, "description": course.category.description}
                if course.category else None
            ),
        }
        if detail:
            data["outcomes"] = course.outcomes or []
            if course.instructor:
                data["instructor"]["bio"] = course.instructor.bio
            data["preview"] = None
            sections = []
            for s in sorted(course.sections, key=lambda x: x.position):
                sections.append({
                    "id": s.id, "title": s.title, "position": s.position,
                    "lessons": [
                        {"id": l.id, "title": l.title, "type": l.type.value if hasattr(l.type, "value") else str(l.type),
                         "duration_minutes": l.duration_minutes, "position": l.position, "is_preview": l.is_preview,
                         "drip_days": l.drip_days}
                        for l in sorted(s.lessons, key=lambda x: x.position)
                    ],
                })
            data["sections"] = sections
            # first free-preview video, shown as the trailer on the course page
            for sec in sorted(course.sections, key=lambda x: x.position):
                for l in sorted(sec.lessons, key=lambda x: x.position):
                    if l.is_preview and l.type == LessonType.video and l.video_url and data["preview"] is None:
                        data["preview"] = {"lesson_id": l.id, "title": l.title, "video_url": l.video_url}
        return data

    # ---------- publishing ----------

    @staticmethod
    def readiness(course: Course) -> list[dict]:
        """Checklist shown before publishing. `required` items block publishing."""
        import re
        lessons = [l for s in course.sections for l in s.lessons]
        text = re.sub(r"<[^>]+>", " ", course.description or "")
        return [
            {"key": "lessons", "label": "At least one lesson", "ok": bool(lessons), "required": True},
            {"key": "summary", "label": "A one-line summary for course cards", "ok": len((course.summary or "").strip()) >= 20, "required": False},
            {"key": "description", "label": "A description of the course (80+ characters)", "ok": len(text.strip()) >= 80, "required": False},
            {"key": "outcomes", "label": "At least 3 learning outcomes", "ok": len(course.outcomes or []) >= 3, "required": False},
            {"key": "category", "label": "A category", "ok": course.category_id is not None, "required": False},
            {"key": "thumbnail", "label": "A thumbnail image", "ok": bool(course.thumbnail_url), "required": False},
            {"key": "preview", "label": "A free preview lesson", "ok": any(l.is_preview for l in lessons), "required": False},
        ]

    # ---------- listings ----------

    @staticmethod
    def list_public_courses(db: Session, *, search=None, category_id=None, level=None,
                            price=None, sort="newest", page=1, size=12) -> dict:
        q = db.query(Course).options(joinedload(Course.instructor), joinedload(Course.category)).filter(
            Course.status == CourseStatus.published
        )
        if search:
            search = search[:100].replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            like = f"%{search}%"
            q = q.filter(or_(Course.title.ilike(like, escape="\\"), Course.summary.ilike(like, escape="\\")))
        if category_id:
            q = q.filter(Course.category_id == category_id)
        if level:
            if level not in ("beginner", "intermediate", "advanced"):
                raise HTTPException(400, "Invalid level")
            q = q.filter(Course.level == level)
        if price == "free":
            q = q.filter(Course.price == 0)
        elif price == "paid":
            q = q.filter(Course.price > 0)

        total = q.count()
        from app.modules.enrollments.models import Enrollment
        if sort in ("popular", "rating"):
            # sort across the whole catalog (not just the current page)
            enr = (db.query(Enrollment.course_id.label("cid"), func.count(Enrollment.id).label("n"))
                   .group_by(Enrollment.course_id).subquery())
            rat = (db.query(Review.course_id.label("cid"), func.avg(Review.rating).label("r"))
                   .group_by(Review.course_id).subquery())
            q = q.outerjoin(enr, enr.c.cid == Course.id).outerjoin(rat, rat.c.cid == Course.id)
            n, r = func.coalesce(enr.c.n, 0), func.coalesce(rat.c.r, 0)
            q = q.order_by(*( (n.desc(), r.desc()) if sort == "popular" else (r.desc(), n.desc()) ),
                           Course.id.desc())
        else:
            order = {
                "newest": Course.created_at.desc(),
                "price_low": Course.price.asc(),
                "price_high": Course.price.desc(),
                "title": Course.title.asc(),
            }
            q = q.order_by(order.get(sort, Course.created_at.desc()), Course.id.desc())
        page = max(1, page)
        items = q.limit(size).offset((page - 1) * size).all()
        maps = CoursesService.aggregate_maps(db, [c.id for c in items])
        cards = [CoursesService.course_to_dict(db, c, maps) for c in items]

        return {"items": cards, "total": total, "page": page, "pages": max(1, -(-total // size))}

    @staticmethod
    def list_featured(db: Session, limit: int = 6) -> list[dict]:
        courses = (
            db.query(Course).options(joinedload(Course.instructor), joinedload(Course.category))
            .filter(Course.status == CourseStatus.published, Course.is_featured.is_(True))
            .order_by(Course.created_at.desc()).limit(limit).all()
        )
        maps = CoursesService.aggregate_maps(db, [c.id for c in courses])
        return [CoursesService.course_to_dict(db, c, maps) for c in courses]

    @staticmethod
    def list_instructor_courses(db: Session, user: User) -> list[dict]:
        q = db.query(Course).options(joinedload(Course.instructor), joinedload(Course.category))
        if user.role != UserRole.admin:
            q = q.filter(Course.instructor_id == user.id)
        courses = q.order_by(Course.created_at.desc()).all()
        maps = CoursesService.aggregate_maps(db, [c.id for c in courses])
        return [CoursesService.course_to_dict(db, c, maps) for c in courses]

    @staticmethod
    def get_course_by_slug(db: Session, slug: str, viewer: User | None) -> Course:
        course = (
            db.query(Course).options(joinedload(Course.instructor), joinedload(Course.category))
            .filter(Course.slug == slug).first()
        )
        if not course:
            raise HTTPException(404, "Course not found")
        is_owner = viewer and (viewer.id == course.instructor_id or viewer.role == UserRole.admin)
        if course.status != CourseStatus.published and not is_owner:
            raise HTTPException(404, "Course not found")
        return course

    @staticmethod
    def get_course_full_for_edit(db: Session, course: Course) -> dict:
        data = CoursesService.course_to_dict(db, course, detail=True)
        # full lesson bodies for the instructor's editor
        for s in data["sections"]:
            section = db.get(Section, s["id"])
            s["lessons"] = [
                {"id": l.id, "section_id": l.section_id, "title": l.title,
                 "type": l.type.value if hasattr(l.type, "value") else str(l.type),
                 "duration_minutes": l.duration_minutes, "position": l.position,
                 "is_preview": l.is_preview, "video_url": l.video_url,
                 "file_url": l.file_url, "content": sanitize_rich_content(l.content), "drip_days": l.drip_days}
                for l in sorted(section.lessons, key=lambda x: x.position)
            ]
        data["readiness"] = CoursesService.readiness(course)
        data["prerequisite_ids"] = [p.prerequisite_id for p in
                                    db.query(CoursePrerequisite).filter_by(course_id=course.id)]
        return data

    @staticmethod
    def set_prerequisites(db: Session, course: Course, course_ids: list[int]) -> None:
        ids = list(dict.fromkeys(int(i) for i in course_ids))
        if course.id in ids:
            raise HTTPException(400, "A course can't be its own prerequisite")
        found = {c.id for c in db.query(Course.id).filter(Course.id.in_(ids))} if ids else set()
        if len(found) != len(ids):
            raise HTTPException(400, "One of the prerequisite courses doesn't exist")
        # reject cycles: none of the chosen courses may (transitively) require this course
        frontier, seen = list(ids), set()
        while frontier:
            cid = frontier.pop()
            if cid == course.id:
                raise HTTPException(400, "That would create a circular prerequisite chain")
            if cid in seen:
                continue
            seen.add(cid)
            frontier += [p.prerequisite_id for p in db.query(CoursePrerequisite).filter_by(course_id=cid)]
        db.query(CoursePrerequisite).filter_by(course_id=course.id).delete(synchronize_session=False)
        for pid in ids:
            db.add(CoursePrerequisite(course_id=course.id, prerequisite_id=pid))
        db.commit()

    # ---------- sections & lessons ----------

    @staticmethod
    def add_section(db: Session, course: Course, title: str) -> Section:
        pos = db.query(func.coalesce(func.max(Section.position), -1)).filter(Section.course_id == course.id).scalar() + 1
        s = Section(course_id=course.id, title=title, position=pos)
        db.add(s)
        db.commit()
        db.refresh(s)
        return s

    @staticmethod
    def update_section(db: Session, section: Section, title: str) -> Section:
        section.title = title
        db.commit()
        return section

    @staticmethod
    def delete_section(db: Session, section: Section) -> None:
        from app.modules.assessments.models import Quiz, Question, QuizAttempt

        from app.modules.enrollments.models import LessonProgress

        lesson_ids = [l.id for l in section.lessons]
        if lesson_ids:
            db.query(LessonProgress).filter(LessonProgress.lesson_id.in_(lesson_ids)).delete(synchronize_session=False)
            quiz_ids = [q.id for q in db.query(Quiz.id).filter(Quiz.lesson_id.in_(lesson_ids))]
            if quiz_ids:
                db.query(QuizAttempt).filter(QuizAttempt.quiz_id.in_(quiz_ids)).delete(synchronize_session=False)
                db.query(Question).filter(Question.quiz_id.in_(quiz_ids)).delete(synchronize_session=False)
                db.query(Quiz).filter(Quiz.id.in_(quiz_ids)).delete(synchronize_session=False)
        db.delete(section)
        db.commit()

    @staticmethod
    def move_section(db: Session, course: Course, section: Section, direction: str) -> None:  # noqa: D401
        siblings = sorted(db.query(Section).filter(Section.course_id == course.id).all(), key=lambda s: s.position)
        idx = siblings.index(section)
        swap = idx - 1 if direction == "up" else idx + 1
        if 0 <= swap < len(siblings):
            siblings[idx], siblings[swap] = siblings[swap], siblings[idx]
            for i, s in enumerate(siblings):
                s.position = i
            db.commit()

    @staticmethod
    def add_lesson(db: Session, section: Section, data: LessonCreateIn) -> Lesson:
        pos = db.query(func.coalesce(func.max(Lesson.position), -1)).filter(Lesson.section_id == section.id).scalar() + 1
        lesson = Lesson(
            section_id=section.id, course_id=section.course_id, title=data.title.strip(),
            type=LessonType(data.type),
            content=sanitize_rich_content(data.content), video_url=safe_url(data.video_url, "video_url"),
            file_url=safe_url(data.file_url, "file_url"), duration_minutes=data.duration_minutes,
            is_preview=data.is_preview, drip_days=data.drip_days or None, position=pos,
        )
        db.add(lesson)
        db.commit()
        db.refresh(lesson)
        return lesson

    @staticmethod
    def update_lesson(db: Session, lesson: Lesson, data: LessonUpdateIn) -> Lesson:
        fields = data.model_dump(exclude_unset=True)
        for key in ("video_url", "file_url"):
            if key in fields:
                fields[key] = safe_url(fields[key], key)
        if "content" in fields:
            fields["content"] = sanitize_rich_content(fields["content"])
        if "drip_days" in fields:
            lesson.drip_days = fields.pop("drip_days") or None
        for key, value in fields.items():
            if key == "type":
                if value is not None:
                    lesson.type = LessonType(value)
            elif value is not None or key in ("content", "video_url", "file_url"):
                setattr(lesson, key, value)
        db.commit()
        db.refresh(lesson)
        return lesson

    @staticmethod
    def delete_lesson(db: Session, lesson: Lesson) -> None:
        from app.modules.assessments.models import Quiz, Question, QuizAttempt
        from app.modules.enrollments.models import LessonProgress

        quiz = db.query(Quiz).filter(Quiz.lesson_id == lesson.id).first()
        if quiz:
            db.query(QuizAttempt).filter(QuizAttempt.quiz_id == quiz.id).delete(synchronize_session=False)
            db.query(Question).filter(Question.quiz_id == quiz.id).delete(synchronize_session=False)
            db.delete(quiz)
        db.query(LessonProgress).filter(LessonProgress.lesson_id == lesson.id).delete(synchronize_session=False)
        db.delete(lesson)
        db.commit()

    @staticmethod
    def move_lesson(db: Session, section: Section, lesson: Lesson, direction: str) -> None:
        siblings = sorted(db.query(Lesson).filter(Lesson.section_id == section.id).all(), key=lambda l: l.position)
        idx = siblings.index(lesson)
        swap = idx - 1 if direction == "up" else idx + 1
        if 0 <= swap < len(siblings):
            siblings[idx], siblings[swap] = siblings[swap], siblings[idx]
            for i, l in enumerate(siblings):
                l.position = i
            db.commit()

    # ---------- reviews ----------

    @staticmethod
    def list_reviews(db: Session, course: Course) -> list[dict]:
        reviews = (
            db.query(Review).options(joinedload(Review.user))
            .filter(Review.course_id == course.id).order_by(Review.created_at.desc()).all()
        )
        return [
            {"id": r.id, "rating": r.rating, "comment": r.comment,
             "created_at": r.created_at.isoformat(),
             "user": {"id": r.user.id, "full_name": r.user.full_name, "headline": r.user.headline,
                      "avatar_url": r.user.avatar_url}}
            for r in reviews if r.user
        ]

    @staticmethod
    def upsert_review(db: Session, course: Course, user: User, rating: int, comment: str | None) -> Review:
        from app.modules.enrollments.models import Enrollment

        enrolled = db.query(Enrollment).filter(Enrollment.course_id == course.id, Enrollment.user_id == user.id).first()
        if not enrolled:
            raise HTTPException(403, "Only enrolled students can review this course")
        review = db.query(Review).filter(Review.course_id == course.id, Review.user_id == user.id).first()
        if review:
            review.rating = rating
            review.comment = comment
        else:
            review = Review(course_id=course.id, user_id=user.id, rating=rating, comment=comment)
            db.add(review)
        db.commit()
        db.refresh(review)
        return review
