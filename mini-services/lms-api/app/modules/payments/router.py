from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import any_user, admin_required
from app.modules.auth.models import User
from app.modules.courses.service import CoursesService
from app.modules.payments import service
from app.modules.payments.models import Payment

router = APIRouter(tags=["payments"])


class CheckoutIn(BaseModel):
    course_id: int


def _payment_dict(p: Payment) -> dict:
    return {
        "reference": p.reference, "status": p.status, "amount": p.amount / 100, "currency": p.currency,
        "amount_display": service.format_amount(p.amount, p.currency), "course_id": p.course_id,
        "course_title": p.course_title, "course_slug": p.course.slug if p.course else None,
        "created_at": p.created_at.isoformat(), "paid_at": p.paid_at.isoformat() if p.paid_at else None,
        "failure_reason": p.failure_reason,
    }


@router.post("/payments/checkout")
def checkout(data: CheckoutIn, db: Session = Depends(get_db), user: User = Depends(any_user)):
    course = CoursesService.get_course(db, data.course_id)
    return service.initialize(db, course, user)


@router.get("/payments/verify/{reference}")
def verify(reference: str, db: Session = Depends(get_db), user: User = Depends(any_user)):
    return _payment_dict(service.verify(db, reference, user))


@router.post("/payments/webhook")
async def webhook(request: Request, db: Session = Depends(get_db)):
    """Paystack calls this. Set it in Paystack Dashboard -> Settings -> API Keys & Webhooks."""
    service.handle_webhook(db, await request.body(), request.headers.get("x-paystack-signature"))
    return {"ok": True}


@router.get("/payments/my")
def my_payments(db: Session = Depends(get_db), user: User = Depends(any_user)):
    rows = (db.query(Payment).options(joinedload(Payment.course)).filter(Payment.user_id == user.id)
            .order_by(Payment.created_at.desc()).limit(100).all())
    return [_payment_dict(p) for p in rows]


@router.get("/admin/payments")
def all_payments(db: Session = Depends(get_db), _: User = Depends(admin_required)):
    rows = (db.query(Payment).options(joinedload(Payment.course), joinedload(Payment.user))
            .order_by(Payment.created_at.desc()).limit(200).all())
    return [{**_payment_dict(p), "user": {"id": p.user.id, "full_name": p.user.full_name, "email": p.user.email}
             if p.user else None} for p in rows]
