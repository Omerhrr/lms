"""Public website support: settings the site displays, and the Contact form."""
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import admin_required
from app.modules.auth.models import User
from app.modules.site.models import Enquiry, SiteSetting
from app.modules.site import content as site_content
from app.shared.utils import utcnow
from app.shared.utils import client_ip, rate_limit

router = APIRouter(tags=["site"])

TOPICS = site_content.TOPICS


def get_content(db: Session) -> dict:
    """Defaults merged with whatever the admins have saved."""
    data = site_content.defaults()
    for row in db.query(SiteSetting).all():
        if row.key in data and isinstance(row.value, dict):
            data[row.key] = {**data[row.key], **row.value}
    return data


class EnquiryIn(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=50)
    topic: str = "General Enquiry"
    subject: str = Field(default="", max_length=255)
    message: str = Field(min_length=10, max_length=5000)
    website: Optional[str] = None          # honeypot: real people never fill this hidden field
    course_id: Optional[int] = None        # "Request access" to a paid course


@router.get("/config/public")
def public_config(db: Session = Depends(get_db)):
    """Non-secret settings the website needs."""
    c = get_content(db)
    contact = {k: c["contact"].get(k) or None for k in ("email", "phone", "address", "hours")}
    return {
        "payments_enabled": settings.payments_enabled, "currency": settings.PAYMENT_CURRENCY,
        "paystack_public_key": settings.PAYSTACK_PUBLIC_KEY if settings.payments_enabled else None,
        "contact": contact,
        "social": {k: v for k, v in c["social"].items() if v},
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
    if data.course_id:
        from app.modules.courses.models import Course
        course = db.get(Course, data.course_id)
        if course and course.instructor_id:
            notify(db, course.instructor_id, "system", f"Access request: {course.title}",
                   f"{e.name} ({e.email}) would like to enroll.", f"/teach/courses/{course.id}/students")
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


# ---------------------------------------------------------------- website content (admin-editable)
def _public(c: dict) -> dict:
    out = dict(c)
    if not out["banner"].get("enabled") or not out["banner"].get("text"):
        out["banner"] = {"enabled": False}
    return out


@router.get("/site/content")
def site_content_public(db: Session = Depends(get_db)):
    return _public(get_content(db))


@router.get("/admin/site/content")
def site_content_admin(db: Session = Depends(get_db), _: User = Depends(admin_required)):
    rows = {r.key: r for r in db.query(SiteSetting).all()}
    return {
        "content": get_content(db),
        "icons": list(site_content.ICONS),
        "topics": list(site_content.TOPICS),
        "meta": {k: {"customized": k in rows,
                     "updated_at": rows[k].updated_at.isoformat() + "Z" if k in rows and rows[k].updated_at else None,
                     "updated_by": rows[k].updated_by if k in rows else None}
                 for k in site_content.SECTIONS},
    }


@router.put("/admin/site/content/{section}")
def site_content_save(section: str, body: dict, db: Session = Depends(get_db), user: User = Depends(admin_required)):
    model = site_content.SECTIONS.get(section)
    if not model:
        raise HTTPException(404, "Unknown section")
    from pydantic import ValidationError
    try:
        data = model.model_validate(body).model_dump()
    except ValidationError as e:
        first = e.errors()[0]
        where = ".".join(str(p) for p in first.get("loc", ()))
        raise HTTPException(422, f"{where}: {first.get('msg')}" if where else first.get("msg"))
    if section == "legal":
        from app.shared.utils import sanitize_html
        for k in ("privacy_html", "terms_html"):
            v = (data.get(k) or "").strip()
            data[k] = sanitize_html(v) if v and v not in ("<p></p>",) else None
    row = db.get(SiteSetting, section)
    if row:
        row.value = data
        row.updated_at = utcnow()
        row.updated_by = user.full_name
    else:
        db.add(SiteSetting(key=section, value=data, updated_by=user.full_name))
    db.commit()
    return {"message": "Saved", "section": section, "value": get_content(db)[section]}


@router.delete("/admin/site/content/{section}")
def site_content_reset(section: str, db: Session = Depends(get_db), _: User = Depends(admin_required)):
    if section not in site_content.SECTIONS:
        raise HTTPException(404, "Unknown section")
    row = db.get(SiteSetting, section)
    if row:
        db.delete(row)
        db.commit()
    return {"message": "Restored the default", "value": get_content(db)[section]}
