from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
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
    """Public verification endpoint - no auth required."""
    cert = db.query(Certificate).filter(Certificate.serial == serial.upper()).first()
    if not cert:
        raise HTTPException(404, "Certificate not found - please check the serial number")
    return _cert_dict(cert)


@router.get("/certificates/{serial}/pdf")
def certificate_pdf(serial: str, request: Request, db: Session = Depends(get_db)):
    """Downloadable PDF. Public like the verification page: the serial is the credential."""
    from app.modules.certificates.pdf import render_certificate_pdf
    cert = db.query(Certificate).filter(Certificate.serial == serial.upper()).first()
    if not cert:
        raise HTTPException(404, "Certificate not found - please check the serial number")
    origin = request.headers.get("x-forwarded-host") or request.headers.get("host") or "infohive"
    pdf = render_certificate_pdf(
        user_name=cert.user_name, course_title=cert.course_title, instructor_name=cert.instructor_name,
        issued_at=cert.issued_at, serial=cert.serial, verify_url=f"{origin}/certificates/{cert.serial}",
    )
    filename = f"Infohive-certificate-{cert.serial}.pdf"
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'})
