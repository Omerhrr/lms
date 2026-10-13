"""Outgoing email over SMTP (works with Gmail app passwords, Zoho, Brevo, Mailgun, SES...).

When SMTP_HOST is empty, emails are written to the API log instead, so development and
CI never need a mail server. Sending never raises: a mail outage must not break sign-up,
password reset or checkout - failures are logged.
"""
import logging
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import make_msgid

from app.core.config import settings

log = logging.getLogger("lms.email")

# Outbox for tests and debugging (last 50 messages, in-process only).
OUTBOX: list[dict] = []


def send_email(to: str, subject: str, html: str, text: str | None = None) -> bool:
    text = text or _html_to_text(html)
    OUTBOX.append({"to": to, "subject": subject, "text": text})
    del OUTBOX[:-50]

    if not settings.email_enabled:
        log.warning("[email disabled] To: %s | %s\n%s", to, subject, text)
        return False

    msg = EmailMessage()
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to
    msg["Subject"] = subject
    msg["Message-ID"] = make_msgid(domain=settings.SMTP_FROM.split("@")[-1].strip("> ") or None)
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")

    try:
        mode = settings.SMTP_SECURITY.lower()
        if mode == "ssl":
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=settings.SMTP_TIMEOUT,
                                      context=ssl.create_default_context())
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=settings.SMTP_TIMEOUT)
            if mode == "starttls":
                server.starttls(context=ssl.create_default_context())
        with server:
            if settings.SMTP_USER:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception:  # noqa: BLE001 - never let email break the request
        log.exception("Failed to send email to %s (%s)", to, subject)
        return False


def _html_to_text(html: str) -> str:
    import re
    t = re.sub(r"<(br|/p|/h\d|/li|/tr)>", "\n", html, flags=re.I)
    t = re.sub(r'<a [^>]*href="([^"]+)"[^>]*>(.*?)</a>', r"\2 (\1)", t, flags=re.I | re.S)
    t = re.sub(r"<[^>]+>", "", t)
    return re.sub(r"\n{3,}", "\n\n", t).strip()
