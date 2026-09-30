from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import any_user
from app.modules.auth.models import User
from app.modules.certificates.models import Certificate

router = APIRouter(tags=["certificates"])


def _cert_dict(c: Certificate) -> dict:
    return {
        "serial": c.serial,
        "course_title": c.course_title,
        "user_name": c.user_name,
        "instructor_name": c.instructor_name,
        "issued_at": c.issued_at.isoformat(),
    }


@router.get("/certificates/my")
def my_certificates(db: Session = Depends(get_db), user: User = Depends(any_user)):
    certs = (
        db.query(Certificate).filter(Certificate.user_id == user.id)
        .order_by(Certificate.issued_at.desc()).all()
    )
    result = []
    for c in certs:
        d = _cert_dict(c)
        result.append(d)
    return result


@router.get("/certificates/{serial}")
def verify_certificate(serial: str, db: Session = Depends(get_db)):
    """Public verification endpoint — no auth required."""
    cert = db.query(Certificate).filter(Certificate.serial == serial.upper()).first()
    if not cert:
        raise HTTPException(404, "Certificate not found — please check the serial number")
    return _cert_dict(cert)
