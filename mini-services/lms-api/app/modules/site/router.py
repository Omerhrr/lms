"""Public website support: settings the site displays, and the Contact form."""
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import admin_required
from app.modules.auth.models import User
from app.modules.site.models import Enquiry
from app.shared.utils import client_ip, rate_limit

router = APIRouter(tags=["site"])

TOPICS = ("Technology / Software Project", "Web Development", "IT Consulting", "Digital Transformation",
          "Corporate Training", "LMS / Learning Enquiry", "Partnership", "General Enquiry")


class EnquiryIn(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=50)
    topic: str = "General Enquiry"
    subject: str = Field(default="", max_length=255)
    message: str = Field(min_length=10, max_length=5000)
    website: Optional[str] = None          # honeypot: real people never fill this hidden field


@router.get("/config/public")
def public_config():
    """Non-secret settings the website needs."""
    return {
        "payments_enabled": settings.payments_enabled, "currency": settings.PAYMENT_CURRENCY,
        "paystack_public_key": settings.PAYSTACK_PUBLIC_KEY if settings.payments_enabled else None,
        "contact": {"email": settings.CONTACT_EMAIL, "phone": settings.CONTACT_PHONE,
                    "address": settings.CONTACT_ADDRESS, "hours": settings.CONTACT_HOURS},
        "social": {k: v for k, v in {"facebook": settings.SOCIAL_FACEBOOK, "linkedin": settings.SOCIAL_LINKEDIN,
                                       "instagram": settings.SOCIAL_INSTAGRAM, "x": settings.SOCIAL_X}.items() if v},
        "enquiry_topics": list(TOPICS),
    }


@router.post("/contact", status_code=201)
def contact(data: EnquiryIn, request: Request, db: Session = Depends(get_db)):
    rate_limit(f"contact:{client_ip(request)}", 5, 600)
    if data.website:                       # bot: pretend it worked
        return {"message": "Thanks! We'll get back to you shortly."}
    if data.topic not in TOPICS:
        raise HTTPException(400, "Please choose what your message is about")
    e = Enquiry(name=data.name.strip(), email=data.email.lower(), phone=(data.phone or "").strip() or None,
                topic=data.topic, subject=data.subject.strip(), message=data.message.strip())
    db.add(e)
    db.commit()

    from app.shared import emails
    notify_to = settings.ENQUIRY_NOTIFY_EMAIL or settings.CONTACT_EMAIL
    if notify_to:
        emails.enquiry_received(notify_to, e)
    emails.enquiry_ack(e.email, e.name, e.topic)
    from app.modules.notifications.service import notify
    from app.modules.auth.models import UserRole
    for admin in db.query(User).filter(User.role == UserRole.admin, User.is_active.is_(True)):
        notify(db, admin.id, "system", f"New enquiry: {e.topic}", f"{e.name} - {e.subject or e.message[:60]}",
               "/admin/enquiries")
    return {"message": "Thanks! We'll get back to you shortly."}


@router.get("/admin/enquiries")
def list_enquiries(status: str | None = None, db: Session = Depends(get_db), _: User = Depends(admin_required)):
    q = db.query(Enquiry)
    if status in ("new", "handled"):
        q = q.filter(Enquiry.status == status)
    return [{"id": e.id, "name": e.name, "email": e.email, "phone": e.phone, "topic": e.topic,
             "subject": e.subject, "message": e.message, "status": e.status,
             "created_at": e.created_at.isoformat() + "Z"}
            for e in q.order_by(Enquiry.created_at.desc()).limit(500)]


class EnquiryUpdate(BaseModel):
    status: Literal["new", "handled"]


@router.put("/admin/enquiries/{enquiry_id}")
def update_enquiry(enquiry_id: int, data: EnquiryUpdate, db: Session = Depends(get_db),
                   _: User = Depends(admin_required)):
    e = db.get(Enquiry, enquiry_id)
    if not e:
        raise HTTPException(404, "Enquiry not found")
    e.status = data.status
    db.commit()
    return {"message": "Updated"}
