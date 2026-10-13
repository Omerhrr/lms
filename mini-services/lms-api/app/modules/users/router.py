from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import admin_required, staff_required
from app.modules.auth.models import User, UserRole
from app.modules.auth.schemas import UserOut
from app.modules.courses.models import Course
from app.modules.enrollments.models import Enrollment
from app.shared.utils import paginate

router = APIRouter(tags=["users"])


@router.get("/users")
def list_users(
    search: str | None = Query(None),
    role: str | None = Query(None),
    instructor_requested: bool | None = Query(None),
    sort: str = Query("newest", pattern="^(newest|oldest|name|name_desc)$"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(admin_required),
):
    q = db.query(User)
    if search:
        search = search[:100].replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        like = f"%{search}%"
        q = q.filter(or_(User.full_name.ilike(like, escape="\\"), User.email.ilike(like, escape="\\")))
    if role:
        try:
            role_enum = UserRole(role)
        except ValueError:
            raise HTTPException(400, f"Invalid role '{role}'. Valid roles: admin, instructor, student")
        q = q.filter(User.role == role_enum)
    if instructor_requested is not None:
        q = q.filter(User.instructor_requested.is_(instructor_requested))
    order = {"newest": [User.created_at.desc(), User.id.desc()], "oldest": [User.created_at.asc(), User.id.asc()],
             "name": [User.full_name.asc()], "name_desc": [User.full_name.desc()]}[sort]
    items, total, page, pages = paginate(q.order_by(*order), page, size)
    return {"items": [UserOut.model_validate(u).model_dump(mode="json") for u in items],
            "total": total, "page": page, "pages": pages}


@router.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db), _: User = Depends(staff_required)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return user


@router.put("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    role: UserRole | None = None,
    is_active: bool | None = None,
    db: Session = Depends(get_db),
    admin: User = Depends(admin_required),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    if user.id == admin.id and (role or is_active is False):
        raise HTTPException(400, "You cannot change your own role or deactivate yourself")
    if role:
        if role == UserRole.instructor and user.role != UserRole.instructor:
            from app.shared import emails
            emails.instructor_approved(user.email, user.full_name)
        user.role = role
        user.instructor_requested = False   # request handled (granted or declined)
    if is_active is not None:
        user.is_active = is_active
    if role or is_active is False:
        # role/active changes take effect immediately, not when the old token expires
        from app.modules.auth.service import AuthService
        db.commit()
        AuthService.revoke_all_sessions(db, user.id)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(admin_required)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    if user.id == admin.id:
        raise HTTPException(400, "You cannot delete your own account")
    owned = db.query(func.count(Course.id)).filter(Course.instructor_id == user.id).scalar() or 0
    if owned:
        raise HTTPException(400, f"{user.full_name} still owns {owned} course(s). "
                                 "Delete or reassign them first, or deactivate the account instead.")
    _purge_user_data(db, user.id)
    db.delete(user)
    db.commit()
    return {"message": f"User {user.email} deleted"}


def _purge_user_data(db: Session, user_id: int) -> None:
    """Remove rows other modules hold for this user so nothing is left pointing at a missing user."""
    from app.modules.assessments.models import QuizAttempt, Submission
    from app.modules.certificates.models import Certificate
    from app.modules.courses.models import Review
    from app.modules.discussions.models import Thread, Post
    from app.modules.enrollments.models import LessonProgress
    from app.modules.notifications.models import Notification, Announcement
    from app.modules.auth.models import RefreshToken

    enrollment_ids = [e.id for e in db.query(Enrollment.id).filter(Enrollment.user_id == user_id)]
    if enrollment_ids:
        db.query(LessonProgress).filter(LessonProgress.enrollment_id.in_(enrollment_ids)).delete(synchronize_session=False)
    db.query(Enrollment).filter(Enrollment.user_id == user_id).delete(synchronize_session=False)
    db.query(QuizAttempt).filter(QuizAttempt.user_id == user_id).delete(synchronize_session=False)
    db.query(Submission).filter(Submission.graded_by == user_id).update({"graded_by": None}, synchronize_session=False)
    db.query(Submission).filter(Submission.user_id == user_id).delete(synchronize_session=False)
    db.query(Certificate).filter(Certificate.user_id == user_id).delete(synchronize_session=False)
    db.query(Review).filter(Review.user_id == user_id).delete(synchronize_session=False)
    # discussion content: detach replies that point at this user's posts, then remove theirs
    own_post_ids = [p.id for p in db.query(Post.id).filter(Post.author_id == user_id)]
    own_thread_ids = [t.id for t in db.query(Thread.id).filter(Thread.author_id == user_id)]
    if own_thread_ids:
        thread_post_ids = [p.id for p in db.query(Post.id).filter(Post.thread_id.in_(own_thread_ids))]
        own_post_ids = list(set(own_post_ids) | set(thread_post_ids))
    if own_post_ids:
        db.query(Post).filter(Post.parent_id.in_(own_post_ids)).update({"parent_id": None}, synchronize_session=False)
        db.query(Post).filter(Post.id.in_(own_post_ids)).delete(synchronize_session=False)
    if own_thread_ids:
        db.query(Thread).filter(Thread.id.in_(own_thread_ids)).delete(synchronize_session=False)
    db.query(Announcement).filter(Announcement.author_id == user_id).delete(synchronize_session=False)
    db.query(Notification).filter(Notification.user_id == user_id).delete(synchronize_session=False)
    db.query(RefreshToken).filter(RefreshToken.user_id == user_id).delete(synchronize_session=False)
    from app.modules.payments.models import Payment
    db.query(Payment).filter(Payment.user_id == user_id).update({"user_id": None}, synchronize_session=False)
    db.flush()


@router.get("/stats/public")
def public_stats(db: Session = Depends(get_db)):
    """Anonymous platform stats for the landing page."""
    total_users = db.query(func.count(User.id)).scalar() or 0
    instructors = db.query(func.count(User.id)).filter(User.role == UserRole.instructor).scalar() or 0
    published = db.query(func.count(Course.id)).filter(Course.status == "published").scalar() or 0
    enrollments = db.query(func.count(Enrollment.id)).scalar() or 0
    return {
        "users": int(total_users),
        "instructors": int(instructors),
        "courses": int(published),
        "enrollments": int(enrollments),
    }


@router.get("/admin/stats")
def admin_stats(db: Session = Depends(get_db), _: User = Depends(admin_required)):
    users_by_role = dict(db.query(User.role, func.count(User.id)).group_by(User.role).all())
    total_courses = db.query(func.count(Course.id)).scalar() or 0
    published_courses = db.query(func.count(Course.id)).filter(Course.status == "published").scalar() or 0
    total_enrollments = db.query(func.count(Enrollment.id)).scalar() or 0
    completed = db.query(func.count(Enrollment.id)).filter(Enrollment.status == "completed").scalar() or 0
    from app.modules.payments.models import Payment
    revenue = (db.query(func.coalesce(func.sum(Payment.amount), 0)).filter(Payment.status == "success").scalar() or 0) / 100
    recent_users = db.query(User).order_by(User.created_at.desc()).limit(6).all()
    return {
        "users_by_role": {r.value if hasattr(r, "value") else str(r): c for r, c in users_by_role.items()},
        "total_users": sum(users_by_role.values()),
        "total_courses": total_courses,
        "published_courses": published_courses,
        "total_enrollments": total_enrollments,
        "completed_enrollments": completed,
        "revenue": float(revenue),
        "recent_users": [UserOut.model_validate(u).model_dump(mode="json") for u in recent_users],
    }
