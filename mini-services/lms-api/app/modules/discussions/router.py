from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.deps import any_user, staff_required
from app.modules.auth.models import User, UserRole
from app.modules.courses.models import Course
from app.modules.courses.service import CoursesService
from app.modules.enrollments.models import Enrollment
from app.modules.discussions.models import Thread, Post

router = APIRouter(tags=["discussions"])


def _can_access(db: Session, course: Course, user: User) -> bool:
    if user.role == UserRole.admin or course.instructor_id == user.id:
        return True
    return db.query(Enrollment).filter_by(course_id=course.id, user_id=user.id).first() is not None


def _thread_dict(t: Thread) -> dict:
    return {
        "id": t.id, "title": t.title, "body": t.body, "is_pinned": t.is_pinned,
        "is_locked": t.is_locked, "created_at": t.created_at.isoformat(),
        "reply_count": len(t.posts),
        "author": {"id": t.author.id, "full_name": t.author.full_name,
                   "avatar_url": t.author.avatar_url, "role": t.author.role.value},
    }


@router.get("/courses/{course_id}/discussions")
def list_threads(course_id: int, db: Session = Depends(get_db), user: User = Depends(any_user)):
    course = CoursesService.get_course(db, course_id)
    if not _can_access(db, course, user):
        raise HTTPException(403, "Enroll in this course to join the discussion")
    threads = (
        db.query(Thread).options(joinedload(Thread.author), joinedload(Thread.posts))
        .filter(Thread.course_id == course_id)
        .order_by(Thread.is_pinned.desc(), Thread.created_at.desc()).all()
    )
    return [_thread_dict(t) for t in threads]


@router.post("/courses/{course_id}/discussions", status_code=201)
def create_thread(course_id: int, body: dict, db: Session = Depends(get_db), user: User = Depends(any_user)):
    course = CoursesService.get_course(db, course_id)
    if not _can_access(db, course, user):
        raise HTTPException(403, "Enroll in this course to join the discussion")
    title = (body.get("title") or "").strip()
    if not title:
        raise HTTPException(400, "Title is required")
    t = Thread(course_id=course_id, author_id=user.id, title=title, body=body.get("body") or "")
    db.add(t)
    db.commit()
    db.refresh(t)
    if user.id != course.instructor_id:
        from app.modules.notifications.service import notify
        notify(db, course.instructor_id, "discussion", "New question in {0}".format(course.title),
               "{0} asked: “{1}”".format(user.full_name, title),
               f"/courses/{course.slug}?tab=discussion")
    return _thread_dict(t)


@router.get("/discussions/{thread_id}")
def thread_detail(thread_id: int, db: Session = Depends(get_db), user: User = Depends(any_user)):
    t = db.query(Thread).options(joinedload(Thread.author), joinedload(Thread.posts).joinedload(Post.author)).filter(Thread.id == thread_id).first()
    if not t:
        raise HTTPException(404, "Thread not found")
    course = CoursesService.get_course(db, t.course_id)
    if not _can_access(db, course, user):
        raise HTTPException(403, "Not allowed")
    data = _thread_dict(t)
    data["posts"] = [
        {"id": p.id, "parent_id": p.parent_id, "body": p.body, "created_at": p.created_at.isoformat(),
         "author": {"id": p.author.id, "full_name": p.author.full_name, "avatar_url": p.author.avatar_url,
                    "role": p.author.role.value}}
        for p in sorted(t.posts, key=lambda x: x.created_at)
    ]
    data["can_moderate"] = user.id == course.instructor_id or user.role == UserRole.admin
    return data


@router.post("/discussions/{thread_id}/posts", status_code=201)
def reply(thread_id: int, body: dict, db: Session = Depends(get_db), user: User = Depends(any_user)):
    t = db.get(Thread, thread_id)
    if not t:
        raise HTTPException(404, "Thread not found")
    course = CoursesService.get_course(db, t.course_id)
    if not _can_access(db, course, user):
        raise HTTPException(403, "Not allowed")
    if t.is_locked and not (user.id == course.instructor_id or user.role == UserRole.admin):
        raise HTTPException(403, "This thread is locked")
    text = (body.get("body") or "").strip()
    if not text:
        raise HTTPException(400, "Reply body is required")
    p = Post(thread_id=thread_id, author_id=user.id, parent_id=body.get("parent_id"), body=text)
    db.add(p)
    db.commit()
    db.refresh(p)
    # notify thread author (and parent-post author) about the reply
    from app.modules.notifications.service import notify
    targets = {t.author_id}
    if body.get("parent_id"):
        parent = db.get(Post, body["parent_id"])
        if parent:
            targets.add(parent.author_id)
    targets.discard(user.id)
    for uid in targets:
        notify(db, uid, "discussion", "New reply to “{0}”".format(t.title[:40]),
               "{0} replied in the discussion.".format(user.full_name),
               f"/courses/{course.slug}?tab=discussion&thread={t.id}")
    return {"id": p.id, "message": "Reply posted"}


@router.post("/discussions/{thread_id}/pin")
def pin_thread(thread_id: int, db: Session = Depends(get_db), user: User = Depends(staff_required)):
    t = db.get(Thread, thread_id)
    if not t:
        raise HTTPException(404, "Thread not found")
    course = CoursesService.get_course(db, t.course_id)
    CoursesService.assert_can_manage(course, user)
    t.is_pinned = not t.is_pinned
    db.commit()
    return {"is_pinned": t.is_pinned}


@router.post("/discussions/{thread_id}/lock")
def lock_thread(thread_id: int, db: Session = Depends(get_db), user: User = Depends(staff_required)):
    t = db.get(Thread, thread_id)
    if not t:
        raise HTTPException(404, "Thread not found")
    course = CoursesService.get_course(db, t.course_id)
    CoursesService.assert_can_manage(course, user)
    t.is_locked = not t.is_locked
    db.commit()
    return {"is_locked": t.is_locked}


@router.delete("/discussions/{thread_id}")
def delete_thread(thread_id: int, db: Session = Depends(get_db), user: User = Depends(any_user)):
    t = db.get(Thread, thread_id)
    if not t:
        raise HTTPException(404, "Thread not found")
    course = CoursesService.get_course(db, t.course_id)
    if t.author_id != user.id and course.instructor_id != user.id and user.role != UserRole.admin:
        raise HTTPException(403, "Not allowed")
    db.delete(t)
    db.commit()
    return {"message": "Thread deleted"}
