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
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(admin_required),
):
    q = db.query(User)
    if search:
        like = f"%{search}%"
        q = q.filter(or_(User.full_name.ilike(like), User.email.ilike(like)))
    if role:
        try:
            role_enum = UserRole(role)
        except ValueError:
            raise HTTPException(400, f"Invalid role '{role}'. Valid roles: admin, instructor, student")
        q = q.filter(User.role == role_enum)
    items, total, page, pages = paginate(q.order_by(User.created_at.desc()), page, size)
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
        user.role = role
    if is_active is not None:
        user.is_active = is_active
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
    db.delete(user)
    db.commit()
    return {"message": f"User {user.email} deleted"}


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
    revenue = (
        db.query(func.coalesce(func.sum(Course.price), 0.0))
        .join(Enrollment, Enrollment.course_id == Course.id)
        .scalar()
    ) or 0.0
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
