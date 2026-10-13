#!/usr/bin/env python3
"""Checks for drip release, prerequisites, notes, bookmarks, calendar and certificate PDFs.
Run against a freshly seeded API (see README)."""
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


S = auth("sarah@infohive.demo", "Teach123!")
email = f"learn-{uuid.uuid4().hex[:8]}@test.io"
r = requests.post(f"{BASE}/auth/register", json={"email": email, "password": "Learn123!", "full_name": "Learner"})
L = {"Authorization": f"Bearer {r.json()['access_token']}"}

print("== build two free courses: A is a prerequisite of B ==")
def make_course(title):
    cid = requests.post(f"{BASE}/teach/courses", headers=S, json={"title": title}).json()["id"]
    sec = requests.post(f"{BASE}/teach/courses/{cid}/sections", headers=S, json={"title": "Week 1"}).json()
    return cid, sec["id"]

a_id, a_sec = make_course(f"Prereq course {uuid.uuid4().hex[:4]}")
a_lesson = requests.post(f"{BASE}/teach/sections/{a_sec}/lessons", headers=S,
                         json={"title": "Intro", "type": "text", "content": "<p>Hello <b>world</b></p><script>x()</script>"}).json()
b_id, b_sec = make_course(f"Dripped course {uuid.uuid4().hex[:4]}")
b_now = requests.post(f"{BASE}/teach/sections/{b_sec}/lessons", headers=S, json={"title": "Day 0", "type": "text"}).json()
b_later = requests.post(f"{BASE}/teach/sections/{b_sec}/lessons", headers=S,
                        json={"title": "Day 7", "type": "text", "drip_days": 7}).json()
for cid in (a_id, b_id):
    requests.post(f"{BASE}/teach/courses/{cid}/publish", headers=S)

r = requests.put(f"{BASE}/teach/courses/{b_id}/prerequisites", headers=S, json={"course_ids": [a_id]})
check("set prerequisite", r.status_code == 200, r.text)
r = requests.put(f"{BASE}/teach/courses/{a_id}/prerequisites", headers=S, json={"course_ids": [b_id]})
check("circular prerequisite rejected", r.status_code == 400)
r = requests.put(f"{BASE}/teach/courses/{a_id}/prerequisites", headers=S, json={"course_ids": [a_id]})
check("self prerequisite rejected", r.status_code == 400)
edit = requests.get(f"{BASE}/teach/courses/{b_id}", headers=S).json()
check("editor sees prerequisite ids + drip days",
      edit["prerequisite_ids"] == [a_id] and any(l["drip_days"] == 7 for s in edit["sections"] for l in s["lessons"]))

print("== rich text is sanitized ==")
content = requests.get(f"{BASE}/lessons/{a_lesson['id']}", headers=S).json()["content"]
check("lesson HTML keeps formatting, drops script", "<b>world</b>" in content and "<script" not in content, content)

print("== prerequisites gate enrollment ==")
b_slug = requests.get(f"{BASE}/teach/courses/{b_id}", headers=S).json()["slug"]
detail = requests.get(f"{BASE}/courses/{b_slug}", headers=L).json()
check("course page lists unmet prerequisite", detail["prerequisites"] and not detail["prerequisites_met"])
r = requests.post(f"{BASE}/enrollments/{b_id}", headers=L)
check("enroll blocked until prerequisite completed", r.status_code == 403, r.text)
requests.post(f"{BASE}/enrollments/{a_id}", headers=L)
requests.post(f"{BASE}/enrollments/{a_id}/lessons/{a_lesson['id']}/complete", headers=L)
r = requests.post(f"{BASE}/enrollments/{b_id}", headers=L)
check("enroll allowed after completing prerequisite", r.status_code == 201, r.text)

print("== drip release ==")
detail = requests.get(f"{BASE}/courses/{b_slug}", headers=L).json()
lessons = {l["id"]: l for s in detail["sections"] for l in s["lessons"]}
check("locked lesson shows unlock date", lessons[b_later["id"]]["unlocks_at"] and not lessons[b_now["id"]]["unlocks_at"])
check("day-0 lesson opens", requests.get(f"{BASE}/lessons/{b_now['id']}", headers=L).status_code == 200)
r = requests.get(f"{BASE}/lessons/{b_later['id']}", headers=L)
check("dripped lesson locked for student", r.status_code == 403 and "unlocks" in r.text, r.text)
r = requests.post(f"{BASE}/enrollments/{b_id}/lessons/{b_later['id']}/complete", headers=L)
check("can't complete a locked lesson", r.status_code == 403)
check("instructor can still open it", requests.get(f"{BASE}/lessons/{b_later['id']}", headers=S).status_code == 200)

print("== notes & bookmarks ==")
lid = b_now["id"]
r = requests.put(f"{BASE}/lessons/{lid}/note", headers=L, json={"body": "Remember the key idea"})
check("save note", r.status_code == 200)
check("read note back", requests.get(f"{BASE}/lessons/{lid}/note", headers=L).json()["body"] == "Remember the key idea")
requests.post(f"{BASE}/lessons/{lid}/bookmark", headers=L)
check("bookmark shows on lesson", requests.get(f"{BASE}/lessons/{lid}/note", headers=L).json()["bookmarked"])
check("notes list", any(n["lesson_id"] == lid for n in requests.get(f"{BASE}/me/notes", headers=L).json()))
check("bookmarks list", any(b["lesson_id"] == lid for b in requests.get(f"{BASE}/me/bookmarks", headers=L).json()))
other = {"Authorization": requests.post(f"{BASE}/auth/register", json={
    "email": f"o-{uuid.uuid4().hex[:6]}@test.io", "password": "Other123!", "full_name": "Other"}).json()["access_token"]}
other = {"Authorization": f"Bearer {other['Authorization']}"}
check("non-enrolled user can't note a lesson", requests.put(f"{BASE}/lessons/{lid}/note", headers=other,
                                                             json={"body": "x"}).status_code == 403)
requests.delete(f"{BASE}/lessons/{lid}/bookmark", headers=L)
check("remove bookmark", not requests.get(f"{BASE}/lessons/{lid}/note", headers=L).json()["bookmarked"])

print("== calendar ==")
due = (datetime.now(timezone.utc) + timedelta(days=3)).strftime("%Y-%m-%dT17:00")
requests.post(f"{BASE}/teach/courses/{b_id}/assignments", headers=S, json={"title": "Essay", "due_date": due})
events = requests.get(f"{BASE}/me/calendar", headers=L).json()
check("assignment due date on student calendar", any(e["type"] == "assignment" and e["title"] == "Essay" for e in events))
check("drip unlock on student calendar", any(e["type"] == "unlock" and e["title"] == "Day 7" for e in events))
check("instructor sees due date as teacher",
      any(e["title"] == "Essay" and e["role"] == "teacher" for e in requests.get(f"{BASE}/me/calendar", headers=S).json()))

print("== certificate PDF ==")
certs = requests.get(f"{BASE}/certificates/my", headers=L).json()
check("certificate issued for prerequisite course", len(certs) >= 1)
r = requests.get(f"{BASE}/certificates/{certs[0]['serial']}/pdf")
check("PDF downloads", r.status_code == 200 and r.content[:4] == b"%PDF" and "attachment" in r.headers["content-disposition"])
check("unknown serial 404", requests.get(f"{BASE}/certificates/LH-NOPE/pdf").status_code == 404)

for cid in (a_id, b_id):
    requests.delete(f"{BASE}/teach/courses/{cid}", headers=S)

print("\n" + "=" * 40)
print(f"RESULT: {ok} passed, {fail} failed")

import sys as _sys
_sys.exit(1 if fail else 0)
