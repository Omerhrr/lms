from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import any_user, staff_required
from app.modules.auth.models import User
from app.modules.courses.service import CoursesService
from app.modules.notifications.models import Notification, Announcement
from app.modules.notifications.service import notify
from app.shared.utils import paginate

router = APIRouter(tags=["notifications"])


@router.get("/notifications")
def my_notifications(page: int = 1, size: int = 15, db: Session = Depends(get_db), user: User = Depends(any_user)):
    q = db.query(Notification).filter(Notification.user_id == user.id).order_by(Notification.created_at.desc())
    items, total, page, pages = paginate(q, page, size)
    return {
        "items": [
            {"id": n.id, "type": n.type, "title": n.title, "body": n.body, "link": n.link,
             "is_read": n.is_read, "created_at": n.created_at.isoformat()}
            for n in items
        ],
        "total": total, "page": page, "pages": pages,
    }


@router.get("/notifications/unread-count")
def unread_count(db: Session = Depends(get_db), user: User = Depends(any_user)):
    count = db.query(func.count(Notification.id)).filter(
        Notification.user_id == user.id, Notification.is_read.is_(False)).scalar() or 0
    return {"count": count}


@router.post("/notifications/{notification_id}/read")
def mark_read(notification_id: int, db: Session = Depends(get_db), user: User = Depends(any_user)):
    n = db.get(Notification, notification_id)
    if not n or n.user_id != user.id:
        raise HTTPException(404, "Notification not found")
    n.is_read = True
    db.commit()
    return {"message": "Marked as read"}


@router.post("/notifications/read-all")
def mark_all_read(db: Session = Depends(get_db), user: User = Depends(any_user)):
    db.query(Notification).filter(Notification.user_id == user.id, Notification.is_read.is_(False)).update({"is_read": True})
    db.commit()
    return {"message": "All notifications marked as read"}


# ---------- course announcements ----------

@router.get("/courses/{course_id}/announcements")
def course_announcements(course_id: int, db: Session = Depends(get_db), user: User = Depends(any_user)):
    course = CoursesService.get_course(db, course_id)
    from app.modules.discussions.router import _can_access
    if not _can_access(db, course, user):
        raise HTTPException(403, "Not allowed")
    rows = (
        db.query(Announcement).filter(Announcement.course_id == course_id)
        .order_by(Announcement.created_at.desc()).all()
    )
    return [
        {"id": a.id, "title": a.title, "body": a.body, "created_at": a.created_at.isoformat(),
         "author": {"id": a.author_id}}
        for a in rows
    ]


@router.post("/teach/courses/{course_id}/announcements", status_code=201)
def create_announcement(course_id: int, body: dict, db: Session = Depends(get_db), user: User = Depends(staff_required)):
    course = CoursesService.get_course(db, course_id)
    CoursesService.assert_can_manage(course, user)
    title = (body.get("title") or "").strip()
    if not title:
        raise HTTPException(400, "Title is required")
    a = Announcement(course_id=course_id, author_id=user.id, title=title, body=body.get("body") or "")
    db.add(a)
    db.commit()
    db.refresh(a)

    # fan out notifications to all enrolled students
    from app.modules.enrollments.models import Enrollment
    for e in db.query(Enrollment).filter(Enrollment.course_id == course_id).all():
        db.add(Notification(user_id=e.user_id, type="announcement",
                            title=f"📣 {course.title}: {title}",
                            body=body.get("body") or "",
                            link=f"/courses/{course.slug}?tab=announcements"))
    db.commit()
    return {"id": a.id, "message": "Announcement published to all enrolled students"}


@router.delete("/teach/announcements/{announcement_id}")
def delete_announcement(announcement_id: int, db: Session = Depends(get_db), user: User = Depends(staff_required)):
    a = db.get(Announcement, announcement_id)
    if not a:
        raise HTTPException(404, "Announcement not found")
    CoursesService.assert_can_manage(CoursesService.get_course(db, a.course_id), user)
    db.delete(a)
    db.commit()
    return {"message": "Announcement deleted"}
