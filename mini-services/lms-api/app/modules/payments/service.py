"""Paystack checkout.

Flow: the student clicks Enroll -> we create a pending Payment and ask Paystack for a hosted
checkout URL -> the student pays on Paystack -> Paystack redirects back to /payments/callback
(we verify with Paystack's API) AND calls our webhook. Either path fulfils the order exactly
once: payment marked successful, student enrolled, receipt emailed.
We never trust the browser: the amount, currency and status come from Paystack's server.
"""
import hashlib
import hmac
import logging
import uuid

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.auth.models import User
from app.modules.courses.models import Course, CourseStatus
from app.modules.enrollments.models import Enrollment
from app.modules.payments.models import Payment
from app.shared.utils import utcnow

log = logging.getLogger("lms.payments")


def to_minor(amount: float) -> int:
    return int(round(float(amount) * 100))


def format_amount(minor: int, currency: str) -> str:
    symbol = {"NGN": "₦", "USD": "$", "GHS": "GH₵", "ZAR": "R", "KES": "KSh"}.get(currency, currency + " ")
    return f"{symbol}{minor / 100:,.2f}"


def _client() -> httpx.Client:
    return httpx.Client(base_url=settings.PAYSTACK_BASE_URL, timeout=20,
                        headers={"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"})


def _require_enabled():
    if not settings.payments_enabled:
        raise HTTPException(503, "Online payments are turned off")


def initialize(db: Session, course: Course, user: User) -> dict:
    _require_enabled()
    from app.modules.enrollments.service import missing_prerequisites
    if course.status != CourseStatus.published:
        raise HTTPException(404, "Course not found")
    if not course.price or course.price <= 0:
        raise HTTPException(400, "This course is free - just enroll")
    if db.query(Enrollment).filter_by(course_id=course.id, user_id=user.id).first():
        raise HTTPException(400, "Already enrolled in this course")
    missing = missing_prerequisites(db, course, user.id)
    if missing:
        raise HTTPException(403, "Complete " + ", ".join(f"“{c.title}”" for c in missing) + " first")

    payment = Payment(
        reference=f"LH-{uuid.uuid4().hex[:20].upper()}", user_id=user.id, course_id=course.id,
        course_title=course.title, amount=to_minor(course.price), currency=settings.PAYMENT_CURRENCY,
    )
    db.add(payment)
    db.commit()

    callback = settings.FRONTEND_URL.rstrip("/") + "/payments/callback"
    try:
        with _client() as c:
            r = c.post("/transaction/initialize", json={
                "email": user.email, "amount": payment.amount, "currency": payment.currency,
                "reference": payment.reference, "callback_url": callback,
                "metadata": {"course_id": course.id, "user_id": user.id, "course_title": course.title},
            })
        data = r.json()
    except (httpx.HTTPError, ValueError):
        log.exception("Paystack initialize failed")
        raise HTTPException(502, "Couldn't reach the payment provider. Please try again.")
    if not data.get("status"):
        payment.status, payment.failure_reason = "failed", str(data.get("message"))[:500]
        db.commit()
        raise HTTPException(502, f"Payment provider error: {data.get('message', 'unknown error')}")
    return {"authorization_url": data["data"]["authorization_url"], "reference": payment.reference}


def _fulfil(db: Session, payment: Payment, tx: dict) -> Payment:
    """Apply a Paystack transaction to our Payment. Idempotent."""
    if payment.status == "success":
        return payment
    status = tx.get("status")
    if status != "success":
        if status in ("failed", "abandoned", "reversed"):
            payment.status = "failed" if status != "abandoned" else "abandoned"
            payment.failure_reason = str(tx.get("gateway_response") or status)[:500]
            db.commit()
        return payment
    # never trust anything but the provider's own numbers
    if int(tx.get("amount", -1)) != payment.amount or (tx.get("currency") or "").upper() != payment.currency:
        payment.status, payment.failure_reason = "failed", "Amount or currency mismatch"
        db.commit()
        log.error("Paystack amount mismatch for %s: %s", payment.reference, tx)
        return payment

    payment.status = "success"
    payment.provider_id = str(tx.get("id") or "")
    payment.channel = tx.get("channel")
    payment.paid_at = utcnow()
    db.commit()

    course = db.get(Course, payment.course_id) if payment.course_id else None
    user = db.get(User, payment.user_id)
    if course and user and not db.query(Enrollment).filter_by(course_id=course.id, user_id=user.id).first():
        from app.modules.enrollments.service import EnrollmentService
        EnrollmentService.enroll(db, course, user, paid=True)
    if user:
        from app.shared import emails
        emails.payment_receipt(user.email, user.full_name, payment.course_title,
                               format_amount(payment.amount, payment.currency), payment.reference,
                               course.slug if course else "")
    return payment


def verify(db: Session, reference: str, user: User) -> Payment:
    _require_enabled()
    payment = db.query(Payment).filter_by(reference=reference).first()
    if not payment or (payment.user_id != user.id and user.role != "admin"):
        raise HTTPException(404, "Payment not found")
    if payment.status == "success":
        return payment
    try:
        with _client() as c:
            data = c.get(f"/transaction/verify/{reference}").json()
    except (httpx.HTTPError, ValueError):
        raise HTTPException(502, "Couldn't reach the payment provider to confirm your payment. Refresh to retry.")
    if not data.get("status"):
        raise HTTPException(502, f"Payment provider error: {data.get('message', 'unknown error')}")
    return _fulfil(db, payment, data["data"])


def handle_webhook(db: Session, raw_body: bytes, signature: str | None) -> None:
    if not settings.PAYSTACK_SECRET_KEY:
        raise HTTPException(503, "Payments not configured")
    expected = hmac.new(settings.PAYSTACK_SECRET_KEY.encode(), raw_body, hashlib.sha512).hexdigest()
    if not signature or not hmac.compare_digest(expected, signature):
        raise HTTPException(401, "Invalid signature")
    import json
    event = json.loads(raw_body or b"{}")
    if event.get("event") != "charge.success":
        return
    tx = event.get("data") or {}
    payment = db.query(Payment).filter_by(reference=tx.get("reference")).first()
    if payment:
        _fulfil(db, payment, tx)
