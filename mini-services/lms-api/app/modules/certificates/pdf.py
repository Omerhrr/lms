"""Render a certificate as a landscape A4 PDF (pure Python, no browser needed)."""
import io

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas

BRAND = HexColor("#059669")
BRAND_DARK = HexColor("#065f46")
INK = HexColor("#0f172a")
MUTED = HexColor("#64748b")
GOLD = HexColor("#b7791f")


def _fit(c: canvas.Canvas, text: str, font: str, size: float, max_width: float) -> float:
    """Shrink the font until `text` fits within max_width."""
    while size > 10 and c.stringWidth(text, font, size) > max_width:
        size -= 1
    return size


def render_certificate_pdf(*, user_name: str, course_title: str, instructor_name: str,
                           issued_at, serial: str, verify_url: str) -> bytes:
    buf = io.BytesIO()
    w, h = landscape(A4)
    c = canvas.Canvas(buf, pagesize=(w, h))
    c.setTitle(f"Certificate - {course_title}")
    c.setAuthor("Infohive Technology Ltd.")
    c.setSubject(f"Certificate of completion {serial}")

    # frame
    c.setFillColor(HexColor("#f8fafc"))
    c.rect(0, 0, w, h, stroke=0, fill=1)
    c.setStrokeColor(BRAND)
    c.setLineWidth(6)
    c.rect(24, 24, w - 48, h - 48, stroke=1, fill=0)
    c.setStrokeColor(HexColor("#a7f3d0"))
    c.setLineWidth(1.2)
    c.rect(36, 36, w - 72, h - 72, stroke=1, fill=0)

    # brand: hexagon mark + name
    import math
    cx, cy, r = w / 2, h - 82, 19
    path = c.beginPath()
    for i in range(6):
        a = math.radians(60 * i - 30)
        (path.moveTo if i == 0 else path.lineTo)(cx + r * math.cos(a), cy + r * math.sin(a))
    path.close()
    c.setFillColor(BRAND)
    c.drawPath(path, stroke=0, fill=1)
    c.setFillColor(HexColor("#ffffff"))
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(cx, cy - 6, "i")
    c.setFillColor(BRAND_DARK)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(w / 2, h - 122, "Infohive Technology Ltd.")

    c.setFillColor(MUTED)
    c.setFont("Helvetica", 12)
    c.drawCentredString(w / 2, h - 165, "C E R T I F I C A T E   O F   C O M P L E T I O N")

    c.setFont("Helvetica", 13)
    c.drawCentredString(w / 2, h - 205, "This certifies that")

    c.setFillColor(INK)
    size = _fit(c, user_name, "Times-BoldItalic", 42, w - 200)
    c.setFont("Times-BoldItalic", size)
    c.drawCentredString(w / 2, h - 255, user_name)
    c.setStrokeColor(HexColor("#cbd5e1"))
    c.setLineWidth(0.8)
    c.line(w / 2 - 220, h - 268, w / 2 + 220, h - 268)

    c.setFillColor(MUTED)
    c.setFont("Helvetica", 13)
    c.drawCentredString(w / 2, h - 298, "has successfully completed the course")

    c.setFillColor(BRAND_DARK)
    size = _fit(c, course_title, "Helvetica-Bold", 24, w - 200)
    c.setFont("Helvetica-Bold", size)
    c.drawCentredString(w / 2, h - 335, course_title)

    # footer: date, seal, instructor
    y = 120
    date_txt = issued_at.strftime("%d %B %Y")
    for x, value, label in ((w / 2 - 230, date_txt, "Date issued"),
                            (w / 2 + 230, instructor_name or "Infohive", "Instructor")):
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(x, y + 8, value)
        c.setStrokeColor(HexColor("#94a3b8"))
        c.line(x - 90, y, x + 90, y)
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 9)
        c.drawCentredString(x, y - 14, label.upper())

    c.setFillColor(GOLD)
    c.circle(w / 2, y + 4, 34, stroke=0, fill=1)
    c.setFillColor(HexColor("#fef3c7"))
    c.circle(w / 2, y + 4, 27, stroke=0, fill=1)
    c.setFillColor(GOLD)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(w / 2, y + 7, "VERIFIED")
    c.drawCentredString(w / 2, y - 4, "INFOHIVE")

    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8.5)
    c.drawCentredString(w / 2, 52, f"Certificate ID {serial}  ·  Verify at {verify_url}")

    c.showPage()
    c.save()
    return buf.getvalue()
