"""Email templates. Plain, table-free HTML that renders well in every client."""
from html import escape

from app.core.config import settings
from app.core.email import send_email


def _url(path: str) -> str:
    return settings.FRONTEND_URL.rstrip("/") + path


def _layout(title: str, body: str, cta: tuple[str, str] | None = None) -> str:
    button = ""
    if cta:
        label, link = cta
        button = (f'<p style="margin:28px 0"><a href="{escape(link)}" style="background:#059669;color:#fff;'
                  f'padding:12px 22px;border-radius:10px;text-decoration:none;font-weight:600">{escape(label)}</a></p>'
                  f'<p style="color:#64748b;font-size:12px">Or open this link: {escape(link)}</p>')
    return f"""<div style="font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;max-width:560px;margin:0 auto;padding:24px;color:#0f172a">
<p style="font-weight:800;font-size:18px;color:#059669;margin:0 0 20px">Infohive</p>
<h1 style="font-size:20px;margin:0 0 12px">{escape(title)}</h1>
{body}{button}
<hr style="border:none;border-top:1px solid #e2e8f0;margin:28px 0 12px">
<p style="color:#94a3b8;font-size:12px">You're receiving this because you have a Infohive account.</p></div>"""


def _p(text: str) -> str:
    return f'<p style="line-height:1.6;margin:0 0 12px">{text}</p>'


def password_reset(to: str, name: str, token: str) -> None:
    link = _url(f"/forgot-password?token={token}")
    minutes = settings.RESET_TOKEN_EXPIRE_MINUTES
    send_email(to, "Reset your Infohive password", _layout(
        "Reset your password",
        _p(f"Hi {escape(name)},") + _p(f"Someone asked to reset your password. The link works once and expires in {minutes} minutes.")
        + _p("If this wasn't you, you can ignore this email - your password stays the same."),
        ("Choose a new password", link)))


def welcome(to: str, name: str, instructor_requested: bool) -> None:
    extra = _p("You asked to teach on Infohive. An admin will review your request; meanwhile you can start learning.") \
        if instructor_requested else ""
    send_email(to, "Welcome to Infohive", _layout(
        f"Welcome, {name.split(' ')[0]}!", _p("Your account is ready.") + extra, ("Browse courses", _url("/courses"))))


def enrolled(to: str, name: str, course_title: str, course_slug: str) -> None:
    send_email(to, f"You're enrolled: {course_title}", _layout(
        "You're in!", _p(f"Hi {escape(name)}, you're now enrolled in <b>{escape(course_title)}</b>."),
        ("Start learning", _url(f"/learn/{course_slug}"))))


def payment_receipt(to: str, name: str, course_title: str, amount: str, reference: str, course_slug: str) -> None:
    send_email(to, f"Payment receipt - {course_title}", _layout(
        "Payment received",
        _p(f"Hi {escape(name)}, thanks for your payment.")
        + _p(f"<b>Course:</b> {escape(course_title)}<br><b>Amount:</b> {escape(amount)}<br><b>Reference:</b> {escape(reference)}"),
        ("Go to the course", _url(f"/learn/{course_slug}"))))


def assignment_graded(to: str, name: str, assignment: str, grade: str, course_slug: str) -> None:
    send_email(to, f"Graded: {assignment}", _layout(
        "Your assignment was graded", _p(f"Hi {escape(name)}, <b>{escape(assignment)}</b> was graded: <b>{escape(grade)}</b>."),
        ("See feedback", _url(f"/courses/{course_slug}?tab=assignments"))))


def certificate_issued(to: str, name: str, course_title: str, serial: str) -> None:
    send_email(to, f"Your certificate: {course_title}", _layout(
        "Congratulations! 🎓", _p(f"Hi {escape(name)}, you completed <b>{escape(course_title)}</b>."),
        ("Download your certificate", _url(f"/certificates/{serial}"))))


def instructor_approved(to: str, name: str) -> None:
    send_email(to, "You can now teach on Infohive", _layout(
        "Instructor access approved", _p(f"Hi {escape(name)}, an admin approved your instructor access."),
        ("Create your first course", _url("/teach/courses/new"))))


def live_scheduled(to: str, name: str, course_title: str, title: str, when: str, session_id: int,
                   rescheduled: bool = False) -> None:
    head = "Live class rescheduled" if rescheduled else "New live class"
    send_email(to, f"{head}: {title}", _layout(
        head, _p(f"Hi {escape(name)}, <b>{escape(title)}</b> for <b>{escape(course_title)}</b> is "
                 f"{'now ' if rescheduled else ''}scheduled for <b>{escape(when)}</b>.")
        + _p("You can join from 15 minutes before it starts."),
        ("View live class", _url(f"/live/{session_id}"))))


def enquiry_received(to: str, e) -> None:
    body = (_p(f"<b>From:</b> {escape(e.name)} &lt;{escape(e.email)}&gt;" + (f"<br><b>Phone:</b> {escape(e.phone)}" if e.phone else ""))
            + _p(f"<b>Topic:</b> {escape(e.topic)}<br><b>Subject:</b> {escape(e.subject or '-')}")
            + f'<div style="white-space:pre-wrap;background:#f8fafc;border-radius:10px;padding:14px;line-height:1.6">{escape(e.message)}</div>')
    send_email(to, f"New website enquiry: {e.topic}", _layout("New enquiry from the website", body,
                                                               ("Open enquiries", _url("/admin/enquiries"))))


def enquiry_ack(to: str, name: str, topic: str) -> None:
    send_email(to, "We've received your message - Infohive Technology", _layout(
        "Thanks for reaching out",
        _p(f"Hi {escape(name.split(' ')[0])}, thanks for contacting Infohive Technology Ltd. about "
           f"<b>{escape(topic)}</b>. Our team will get back to you shortly.")
        + _p("In the meantime, you can explore our courses."), ("Explore courses", _url("/courses"))))
