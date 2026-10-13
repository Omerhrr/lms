#!/usr/bin/env python3
"""Cookie sessions, CSRF, SMTP email and Paystack checkout - fully self-contained.

Starts its own API (port 8011) on a throwaway SQLite database, a fake Paystack API and a local
SMTP catcher, so it needs no real accounts:   python3 test_platform.py
(needs: pip install aiosmtpd requests)
"""
import hashlib
import hmac
import json
import os
import re
import subprocess
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import requests
from aiosmtpd.controller import Controller

API_PORT, PAYSTACK_PORT, SMTP_PORT = 8011, 8012, 8025
BASE = f"http://127.0.0.1:{API_PORT}/api"
SECRET = "sk_test_fake_" + uuid.uuid4().hex
ok = fail = 0


def check(name, cond, extra=""):
    global ok, fail
    ok, fail = (ok + 1, fail) if cond else (ok, fail + 1)
    print(f"  {'✓' if cond else '✗'} {name} {'' if cond else extra}")


# ---------------- fake SMTP ----------------
MAILS = []


class Catcher:
    async def handle_DATA(self, server, session, envelope):
        import email as _email
        msg = _email.message_from_bytes(envelope.content)
        parts = [p.get_payload(decode=True).decode("utf8", "replace") for p in msg.walk()
                 if p.get_content_type() in ("text/plain", "text/html")]
        MAILS.append({"to": envelope.rcpt_tos, "data": str(msg["Subject"]) + "\n" + "\n".join(parts)})
        return "250 OK"


smtp = Controller(Catcher(), hostname="127.0.0.1", port=SMTP_PORT)
smtp.start()


def mails_to(addr):
    return [m for m in MAILS if addr in m["to"]]


# ---------------- fake Paystack ----------------
TX = {}   # reference -> {"amount", "currency", "status", "email"}


class FakePaystack(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, body, code=200):
        raw = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        if self.headers.get("Authorization") != f"Bearer {SECRET}":
            return self._send({"status": False, "message": "Invalid key"}, 401)
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if self.path == "/transaction/initialize":
            TX[body["reference"]] = {"amount": body["amount"], "currency": body["currency"],
                                     "status": "abandoned", "email": body["email"]}
            return self._send({"status": True, "data": {
                "authorization_url": f"https://checkout.paystack.test/{body['reference']}",
                "reference": body["reference"]}})
        self._send({"status": False}, 404)

    def do_GET(self):
        m = re.match(r"^/transaction/verify/(.+)$", self.path)
        if m and m.group(1) in TX:
            t = TX[m.group(1)]
            return self._send({"status": True, "data": {"id": 99, "reference": m.group(1), "status": t["status"],
                                                        "amount": t["amount"], "currency": t["currency"],
                                                        "channel": "card", "gateway_response": "Approved"}})
        self._send({"status": False, "message": "Transaction not found"}, 404)


paystack = ThreadingHTTPServer(("127.0.0.1", PAYSTACK_PORT), FakePaystack)
threading.Thread(target=paystack.serve_forever, daemon=True).start()

# ---------------- API under test ----------------
here = os.path.dirname(os.path.abspath(__file__))
db_file = os.path.join(here, "data", "test_platform.db")
env = {**os.environ,
       "LMS_DATABASE_URL": os.environ.get("TEST_DATABASE_URL", f"sqlite:///{db_file}"),
       "SMTP_HOST": "127.0.0.1", "SMTP_PORT": str(SMTP_PORT), "SMTP_SECURITY": "none",
       "SMTP_FROM": "Infohive <no-reply@infohive.test>",
       "PAYSTACK_ENABLED": "true", "PAYSTACK_SECRET_KEY": SECRET,
       "PAYSTACK_BASE_URL": f"http://127.0.0.1:{PAYSTACK_PORT}", "PAYMENT_CURRENCY": "NGN",
       "FRONTEND_URL": "https://lms.example.com", "AUTH_RATE_LIMIT_PER_MINUTE": "1000"}
seed_args = [sys.executable, "app/seed.py"] + ([] if env["LMS_DATABASE_URL"].startswith("sqlite") else ["--yes"])
subprocess.run(seed_args, cwd=here, env=env, check=True, capture_output=True)
api = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(API_PORT)],
                       cwd=here, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    for _ in range(60):
        try:
            if requests.get(f"{BASE}/health", timeout=1).ok:
                break
        except requests.ConnectionError:
            time.sleep(0.25)

    XHR = {"X-Requested-With": "XMLHttpRequest"}

    print("== HttpOnly cookie sessions ==")
    s = requests.Session()
    r = s.post(f"{BASE}/auth/login", json={"email": "emma@example.com", "password": "Study123!"})
    raw_cookies = r.headers.get("set-cookie", "")
    check("browser login returns no tokens in the body", r.ok and "access_token" not in r.json() and r.json()["user"])
    check("access + refresh cookies are HttpOnly",
          re.search(r"lh_access=[^,]*HttpOnly", raw_cookies, re.I) and re.search(r"lh_refresh=[^,]*HttpOnly", raw_cookies, re.I))
    check("refresh cookie is scoped to /api/auth", re.search(r"lh_refresh=[^,]*Path=/api/auth", raw_cookies))
    check("cookie session authenticates", s.get(f"{BASE}/auth/me").json().get("email") == "emma@example.com")
    r = s.put(f"{BASE}/auth/me", json={"headline": "csrf?"})
    check("state change without X-Requested-With is blocked (CSRF)", r.status_code == 403)
    r = s.put(f"{BASE}/auth/me", json={"headline": "Learner"}, headers=XHR)
    check("same request with the header works", r.ok and r.json()["headline"] == "Learner")
    old_refresh = s.cookies.get("lh_refresh", path="/api/auth")
    r = s.post(f"{BASE}/auth/refresh", headers=XHR)
    check("refresh via cookie rotates the session", r.ok and s.cookies.get("lh_refresh", path="/api/auth") != old_refresh)
    r = requests.post(f"{BASE}/auth/refresh", cookies={"lh_refresh": old_refresh}, headers=XHR)
    check("old refresh cookie can't be replayed", r.status_code == 401)
    s2 = requests.Session()
    s2.post(f"{BASE}/auth/login", json={"email": "emma@example.com", "password": "Study123!"})
    check("replay revoked every session (theft detection)", s.get(f"{BASE}/auth/me").status_code == 401)
    s2.post(f"{BASE}/auth/logout", headers=XHR)
    check("logout clears the session", s2.get(f"{BASE}/auth/me").status_code == 401 and not s2.cookies.get("lh_session"))

    print("== SMTP email ==")
    email = f"mail-{uuid.uuid4().hex[:6]}@test.io"
    s = requests.Session()
    s.post(f"{BASE}/auth/register", json={"email": email, "password": "Mailer123!", "full_name": "Mail Tester"})
    time.sleep(0.3)
    check("welcome email sent", any("Welcome to Infohive" in m["data"] for m in mails_to(email)))
    requests.post(f"{BASE}/auth/forgot-password", json={"email": email})
    time.sleep(0.3)
    reset = [m for m in mails_to(email) if "Reset your Infohive password" in m["data"]]
    link = re.search(r"https://lms\.example\.com/forgot-password\?token=([\w.\-]+)", reset[-1]["data"]) if reset else None
    check("reset email contains a link to the site", bool(link))
    if link:
        r = requests.post(f"{BASE}/auth/reset-password", json={"token": link.group(1), "new_password": "Changed123!"})
        check("emailed reset link works", r.ok)
        r = requests.post(f"{BASE}/auth/reset-password", json={"token": link.group(1), "new_password": "Again1234!"})
        check("and only once", r.status_code == 400)

    print("== Paystack ==")
    cfg = requests.get(f"{BASE}/config/public").json()
    check("public config advertises payments + currency", cfg["payments_enabled"] and cfg["currency"] == "NGN")
    buyer = requests.Session()
    bemail = f"buyer-{uuid.uuid4().hex[:6]}@test.io"
    buyer.post(f"{BASE}/auth/register", json={"email": bemail, "password": "Buyer123!", "full_name": "Ada Buyer"})
    paid = requests.get(f"{BASE}/courses", params={"price": "paid"}).json()["items"]
    course = next(c for c in paid if not c.get("prerequisites"))
    r = buyer.post(f"{BASE}/enrollments/{course['id']}", headers=XHR)
    check("paid course can't be enrolled without checkout", r.status_code == 402 and "checkout" in r.text)
    r = buyer.post(f"{BASE}/payments/checkout", json={"course_id": course["id"]}, headers=XHR)
    ref = r.json().get("reference")
    check("checkout returns a Paystack URL", r.ok and r.json()["authorization_url"].startswith("https://checkout.paystack.test/"))
    check("amount sent in kobo", TX[ref]["amount"] == round(course["price"] * 100) and TX[ref]["currency"] == "NGN")
    r = buyer.get(f"{BASE}/payments/verify/{ref}")
    check("unpaid checkout doesn't enroll", r.json()["status"] != "success"
          and not buyer.get(f"{BASE}/courses/{course['slug']}").json()["is_enrolled"])
    TX[ref]["status"] = "success"
    r = buyer.get(f"{BASE}/payments/verify/{ref}")
    check("verified payment enrolls the student", r.json()["status"] == "success"
          and buyer.get(f"{BASE}/courses/{course['slug']}").json()["is_enrolled"])
    check("verify is idempotent", buyer.get(f"{BASE}/payments/verify/{ref}").json()["status"] == "success")
    time.sleep(0.3)
    check("receipt emailed", any("Payment receipt" in m["data"] for m in mails_to(bemail)))
    other = requests.Session()
    other.post(f"{BASE}/auth/register", json={"email": f"o-{uuid.uuid4().hex[:6]}@t.io", "password": "Other123!", "full_name": "Other Person"})
    check("someone else can't view the payment", other.get(f"{BASE}/payments/verify/{ref}").status_code == 404)

    # webhook path (student closed the tab before the redirect)
    w = requests.Session()
    wemail = f"hook-{uuid.uuid4().hex[:6]}@test.io"
    w.post(f"{BASE}/auth/register", json={"email": wemail, "password": "Hooked123!", "full_name": "Web Hook"})
    ref2 = w.post(f"{BASE}/payments/checkout", json={"course_id": course["id"]}, headers=XHR).json()["reference"]
    event = json.dumps({"event": "charge.success", "data": {"reference": ref2, "status": "success",
                        "amount": TX[ref2]["amount"], "currency": "NGN", "id": 7, "channel": "bank"}}).encode()
    r = requests.post(f"{BASE}/payments/webhook", data=event, headers={"x-paystack-signature": "bad"})
    check("webhook with a bad signature is rejected", r.status_code == 401)
    sig = hmac.new(SECRET.encode(), event, hashlib.sha512).hexdigest()
    r = requests.post(f"{BASE}/payments/webhook", data=event, headers={"x-paystack-signature": sig, "Content-Type": "application/json"})
    check("signed webhook enrolls the student", r.ok and w.get(f"{BASE}/courses/{course['slug']}").json()["is_enrolled"])

    # tampered amount
    t = requests.Session()
    t.post(f"{BASE}/auth/register", json={"email": f"t-{uuid.uuid4().hex[:6]}@t.io", "password": "Tamper123!", "full_name": "Tam Per"})
    ref3 = t.post(f"{BASE}/payments/checkout", json={"course_id": course["id"]}, headers=XHR).json()["reference"]
    TX[ref3].update(status="success", amount=100)
    r = t.get(f"{BASE}/payments/verify/{ref3}")
    check("underpaid transaction is refused", r.json()["status"] == "failed"
          and not t.get(f"{BASE}/courses/{course['slug']}").json()["is_enrolled"])

    admin = requests.Session()
    admin.post(f"{BASE}/auth/login", json={"email": "admin@infohive.demo", "password": "Admin123!"})
    revenue = admin.get(f"{BASE}/admin/stats").json()["revenue"]
    check("admin revenue = real successful payments", abs(revenue - 2 * course["price"]) < 0.01, revenue)
    check("admin payments list", len(admin.get(f"{BASE}/admin/payments").json()) >= 3)
finally:
    api.terminate()
    paystack.shutdown()
    smtp.stop()

print("\n" + "=" * 40)
print(f"RESULT: {ok} passed, {fail} failed")
sys.exit(1 if fail else 0)
