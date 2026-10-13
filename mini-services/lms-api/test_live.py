#!/usr/bin/env python3
"""Live classes and the website contact form. Run against a freshly seeded API (see README)."""
import sys
import uuid
from datetime import datetime, timedelta, timezone

import requests

import _testclient  # noqa: F401  (API-client auth mode)

BASE = "http://127.0.0.1:8000/api"
ok = fail = 0


def check(name, cond, extra=""):
    global ok, fail
    ok, fail = (ok + 1, fail) if cond else (ok, fail + 1)
    print(f"  {'✓' if cond else '✗'} {name} {'' if cond else extra}")


def auth(email, password):
    r = requests.post(f"{BASE}/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def iso(dt):
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


now = datetime.now(timezone.utc)
S = auth("sarah@infohive.demo", "Teach123!")
J = auth("james@infohive.demo", "Teach123!")
A = auth("admin@infohive.demo", "Admin123!")
email = f"live-{uuid.uuid4().hex[:6]}@test.io"
r = requests.post(f"{BASE}/auth/register", json={"email": email, "password": "Learner123!", "full_name": "Live Learner"})
L = {"Authorization": f"Bearer {r.json()['access_token']}"}
r = requests.post(f"{BASE}/auth/register", json={"email": f"o-{email}", "password": "Outsider123!", "full_name": "Out Sider"})
O = {"Authorization": f"Bearer {r.json()['access_token']}"}

print("== scheduling ==")
cid = requests.post(f"{BASE}/teach/courses", headers=S, json={"title": f"Live course {uuid.uuid4().hex[:4]}"}).json()["id"]
_sec = requests.post(f"{BASE}/teach/courses/{cid}/sections", headers=S, json={"title": "Week 1"}).json()
requests.post(f"{BASE}/teach/sections/{_sec['id']}/lessons", headers=S, json={"title": "Welcome", "type": "text"})
requests.post(f"{BASE}/teach/courses/{cid}/publish", headers=S)
requests.post(f"{BASE}/enrollments/{cid}", headers=L)

r = requests.post(f"{BASE}/teach/courses/{cid}/live", headers=S, json={
    "title": "Kick-off Q&A", "starts_at": iso(now + timedelta(days=2)), "duration_minutes": 60})
later = r.json()
check("schedule a built-in room class", r.status_code == 201 and later["state"] == "upcoming", r.text)
r = requests.post(f"{BASE}/teach/courses/{cid}/live", headers=S, json={
    "title": "Office hours", "starts_at": iso(now + timedelta(minutes=5)), "duration_minutes": 45})
soon = r.json()
check("a class starting in 5 min is joinable", soon.get("state") == "starting_soon" and soon["can_join"], r.text)
r = requests.post(f"{BASE}/teach/courses/{cid}/live", headers=S, json={
    "title": "Zoom guest talk", "starts_at": iso(now + timedelta(minutes=1)), "provider": "external",
    "external_url": "https://zoom.us/j/123456789"})
ext = r.json()
check("schedule an external (Zoom) class", r.status_code == 201, r.text)
r = requests.post(f"{BASE}/teach/courses/{cid}/live", headers=S, json={
    "title": "Bad", "starts_at": iso(now + timedelta(days=1)), "provider": "external", "external_url": "javascript:alert(1)"})
check("unsafe meeting link rejected", r.status_code == 400)
r = requests.post(f"{BASE}/teach/courses/{cid}/live", headers=S, json={"title": "Past", "starts_at": iso(now - timedelta(days=1))})
check("start time in the past rejected", r.status_code == 400)
r = requests.post(f"{BASE}/teach/courses/{cid}/live", headers=J, json={"title": "Hijack", "starts_at": iso(now + timedelta(days=1))})
check("another instructor can't schedule in my course", r.status_code == 403)

print("== students ==")
lst = requests.get(f"{BASE}/courses/{cid}/live", headers=L).json()
check("enrolled student sees the schedule", len(lst) == 3)
check("students don't get the external link in listings", all(s["external_url"] is None for s in lst))
check("outsider can't see the schedule", requests.get(f"{BASE}/courses/{cid}/live", headers=O).status_code == 403)
notes = requests.get(f"{BASE}/notifications", headers=L).json()["items"]
check("students were notified", sum("Live class scheduled" in n["title"] for n in notes) >= 3)
r = requests.post(f"{BASE}/live/{later['id']}/join", headers=L)
check("can't join before doors open", r.status_code == 425, r.text)
r = requests.post(f"{BASE}/live/{soon['id']}/join", headers=L)
j = r.json()
check("join returns a Jitsi room", r.ok and j["provider"] == "jitsi" and j["room"].startswith("infohive-") and not j["moderator"], r.text)
requests.post(f"{BASE}/live/{soon['id']}/join", headers=L)
r = requests.post(f"{BASE}/live/{ext['id']}/join", headers=L)
check("external class hands out the Zoom link at join time", r.ok and r.json()["url"] == "https://zoom.us/j/123456789")
check("outsider can't join", requests.post(f"{BASE}/live/{soon['id']}/join", headers=O).status_code == 403)
r = requests.post(f"{BASE}/live/{later['id']}/join", headers=S)
check("host can open the room early, as moderator", r.ok and r.json()["moderator"], r.text)
upcoming = requests.get(f"{BASE}/me/live", headers=L).json()
check("dashboard feed lists upcoming classes", {s["id"] for s in upcoming} >= {soon["id"], later["id"]})
cal = requests.get(f"{BASE}/me/calendar", headers=L).json()
check("live classes appear on the calendar", any(e["type"] == "live" and e["title"] == "Kick-off Q&A" for e in cal))

print("== instructor tools ==")
att = requests.get(f"{BASE}/teach/live/{soon['id']}/attendance", headers=S).json()
row = next(r for r in att["rows"] if r["user"]["email"] == email)
check("attendance recorded (2 joins)", att["present"] == 1 and row["present"] and row["join_count"] == 2, att)
r = requests.put(f"{BASE}/teach/live/{later['id']}", headers=S, json={"starts_at": iso(now + timedelta(days=3))})
check("reschedule", r.ok and r.json()["starts_at"].startswith((now + timedelta(days=3)).strftime("%Y-%m-%d")))
check("students told about the new time",
      any("rescheduled" in n["title"] for n in requests.get(f"{BASE}/notifications", headers=L).json()["items"]))
r = requests.put(f"{BASE}/teach/live/{soon['id']}", headers=S, json={"recording_url": "https://www.youtube.com/watch?v=rfscVS0vtbw"})
check("add a recording link", r.ok and r.json()["recording_url"])
r = requests.post(f"{BASE}/teach/live/{later['id']}/cancel", headers=S)
check("cancel", r.ok and requests.post(f"{BASE}/live/{later['id']}/join", headers=L).status_code == 410)
tl = requests.get(f"{BASE}/teach/courses/{cid}/live", headers=S).json()
check("instructor list with attendance counts", tl["enrolled"] == 1 and any(s["attendance_count"] == 1 for s in tl["sessions"]))
check("delete", requests.delete(f"{BASE}/teach/live/{ext['id']}", headers=S).ok)

print("== contact form ==")
cfg = requests.get(f"{BASE}/config/public").json()
check("public config lists enquiry topics", "Corporate Training" in cfg["enquiry_topics"] and "contact" in cfg)
r = requests.post(f"{BASE}/contact", json={"name": "Ngozi Okafor", "email": "ngozi@example.com", "phone": "+2348000000000",
                                           "topic": "Corporate Training", "subject": "Staff onboarding",
                                           "message": "We'd like to train 40 staff on digital skills next quarter."})
check("enquiry accepted", r.status_code == 201, r.text)
r = requests.post(f"{BASE}/contact", json={"name": "Bot", "email": "bot@example.com", "topic": "General Enquiry",
                                           "message": "buy cheap stuff now!!!", "website": "http://spam"})
check("honeypot silently drops bots", r.status_code == 201)
r = requests.post(f"{BASE}/contact", json={"name": "X Y", "email": "x@example.com", "topic": "Hacking", "message": "0123456789"})
check("unknown topic rejected", r.status_code == 400)
inbox = requests.get(f"{BASE}/admin/enquiries", headers=A).json()
check("admin inbox has the enquiry (not the bot)", any(e["email"] == "ngozi@example.com" for e in inbox)
      and not any(e["email"] == "bot@example.com" for e in inbox))
check("non-admin can't read enquiries", requests.get(f"{BASE}/admin/enquiries", headers=S).status_code == 403)
eid = next(e["id"] for e in inbox if e["email"] == "ngozi@example.com")
check("mark handled", requests.put(f"{BASE}/admin/enquiries/{eid}", headers=A, json={"status": "handled"}).ok)

requests.delete(f"{BASE}/teach/courses/{cid}", headers=S)
print("\n" + "=" * 40)
print(f"RESULT: {ok} passed, {fail} failed")
sys.exit(1 if fail else 0)
