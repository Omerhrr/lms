#!/usr/bin/env python3
"""Security regression tests for the audit fixes. Run against a freshly seeded API:

    AUTH_RATE_LIMIT_PER_MINUTE=1000 uvicorn app.main:app --port 8000
    python3 test_security.py
"""
import io
import uuid

import requests

import _testclient  # noqa: F401  (API-client auth mode)

BASE = "http://127.0.0.1:8000/api"
ok = fail = 0


def check(name, cond, extra=""):
    global ok, fail
    if cond:
        ok += 1
        print(f"  ✓ {name}")
    else:
        fail += 1
        print(f"  ✗ {name} {extra}")


def login(email, password):
    r = requests.post(f"{BASE}/auth/login", json={"email": email, "password": password})
    return r.json(), {"Authorization": f"Bearer {r.json().get('access_token')}"}


def register(role="student"):
    email = f"sec-{uuid.uuid4().hex[:8]}@test.io"
    r = requests.post(f"{BASE}/auth/register",
                      json={"email": email, "password": "Secure123!", "full_name": "Sec Tester", "role": role})
    return email, r


_, A = login("admin@infohive.demo", "Admin123!")
_, S = login("sarah@infohive.demo", "Teach123!")

print("== password reset never leaks a token ==")
r = requests.post(f"{BASE}/auth/forgot-password", json={"email": "admin@infohive.demo"})
check("existing account: no token in response", r.status_code == 200 and "reset_token" not in r.json())
r2 = requests.post(f"{BASE}/auth/forgot-password", json={"email": "nobody@nowhere.io"})
check("unknown account: identical response (no enumeration)", r2.json() == r.json())

print("== self-registration cannot create instructors ==")
email, r = register("instructor")
user = r.json()["user"]
check("signup as instructor -> student + request flag",
      r.status_code == 201 and user["role"] == "student" and user["instructor_requested"] is True, r.text[:120])
X = {"Authorization": f"Bearer {r.json()['access_token']}"}
r = requests.post(f"{BASE}/teach/courses", headers=X, json={"title": "Evil course"})
check("requested-but-unapproved user cannot create courses", r.status_code == 403)

print("== quiz answers are not leaked ==")
r = requests.get(f"{BASE}/quizzes/1", headers=X)
check("non-enrolled user cannot open quiz", r.status_code == 403)
r = requests.post(f"{BASE}/quizzes/1/attempts", headers=X, json={"answers": {}})
check("non-enrolled user cannot submit quiz", r.status_code == 403)
_, J = login("james@infohive.demo", "Teach123!")
r = requests.post(f"{BASE}/quizzes/1/attempts", headers=J, json={"answers": {}})
check("instructor of another course cannot submit quiz", r.status_code == 403, r.text[:100])

# enroll the new student in a free course that has a quiz, fail once, and inspect the response
courses = requests.get(f"{BASE}/courses", params={"price": "free", "size": 48}).json()["items"]
free_quiz = None
for c in courses:
    detail = requests.get(f"{BASE}/courses/{c['slug']}").json()
    for s in detail["sections"]:
        for l in s["lessons"]:
            if l["type"] == "quiz":
                free_quiz = (c, l)
if free_quiz:
    c, l = free_quiz
    requests.post(f"{BASE}/enrollments/{c['id']}", headers=X)
    q = requests.get(f"{BASE}/lessons/{l['id']}/quiz", headers=X).json()
    if "id" in q and q.get("can_take"):
        res = requests.post(f"{BASE}/quizzes/{q['id']}/attempts", headers=X,
                            json={"answers": {}, "session_token": q.get("session_token")}).json()
        leaked = any("correct_answers" in d for d in res.get("detail", {}).values())
        check("failed attempt with retries left hides the answer key",
              res.get("passed") is False and (not leaked or res.get("answers_revealed")), str(res)[:150])
    else:
        print("  - (skipped: quiz not takeable)")
else:
    print("  - (skipped: no free course with a quiz in seed data)")

print("== paid courses ==")
paid = requests.get(f"{BASE}/courses", params={"price": "paid"}).json()["items"][0]
r = requests.post(f"{BASE}/enrollments/{paid['id']}", headers=X)
check("student cannot self-enroll in a paid course", r.status_code == 402, r.text[:100])
me = requests.get(f"{BASE}/auth/me", headers=X).json()
other_course = next(c for c in courses if c["instructor"]["full_name"] != "Sarah Chen") if courses else None
r = requests.post(f"{BASE}/enrollments/{paid['id']}", headers=J, json={"target_user_id": me["id"]})
if paid["instructor"]["id"] != requests.get(f"{BASE}/auth/me", headers=J).json()["id"]:
    check("instructor cannot enroll students in someone else's course", r.status_code == 403, r.text[:100])

print("== XSS sources ==")
cid = requests.post(f"{BASE}/teach/courses", headers=S, json={
    "title": "XSS probe course", "description": '<p>ok</p><script>alert(1)</script><img src=x onerror=alert(1)>'
}).json()["id"]
data = requests.get(f"{BASE}/teach/courses/{cid}", headers=S).json()
check("course description is sanitized", "<script" not in data["description"] and "onerror" not in data["description"],
      data["description"])
r = requests.put(f"{BASE}/teach/courses/{cid}", headers=S, json={"thumbnail_url": "javascript:alert(1)"})
check("javascript: thumbnail rejected", r.status_code == 400)
r = requests.put(f"{BASE}/teach/courses/{cid}", headers=S, json={"is_featured": True})
check("instructor cannot self-feature", r.status_code == 403)
sec = requests.post(f"{BASE}/teach/courses/{cid}/sections", headers=S, json={"title": "S"}).json()
r = requests.post(f"{BASE}/teach/sections/{sec['id']}/lessons", headers=S,
                  json={"title": "L", "type": "video", "video_url": "javascript:alert(1)"})
check("javascript: video_url rejected", r.status_code == 400)
lesson = requests.post(f"{BASE}/teach/sections/{sec['id']}/lessons", headers=S, json={"title": "L"}).json()
r = requests.put(f"{BASE}/teach/lessons/{lesson['id']}", headers=S, json={"course_id": 1, "section_id": 1})
after = requests.get(f"{BASE}/teach/courses/{cid}", headers=S).json()
check("lesson cannot be moved into another course via mass assignment",
      any(l["id"] == lesson["id"] for s in after["sections"] for l in s["lessons"]))
r = requests.post(f"{BASE}/media/upload", headers=S,
                  files={"file": ("x.svg", io.BytesIO(b"<svg onload='alert(1)'/>"), "image/svg+xml")})
check("SVG upload rejected", r.status_code == 400)
r = requests.post(f"{BASE}/media/upload", headers=S, files={"file": ("a.png", io.BytesIO(b"\x89PNG"), "image/png")})
f = requests.get("http://127.0.0.1:8000" + r.json()["url"])
check("uploads served with sandbox CSP + nosniff",
      "sandbox" in f.headers.get("content-security-policy", "") and f.headers.get("x-content-type-options") == "nosniff")
requests.delete(f"{BASE}/teach/courses/{cid}", headers=S)

print("== assignments & grading ==")
asg = requests.get(f"{BASE}/courses/1/assignments", headers=S).json()
if asg:
    r = requests.post(f"{BASE}/assignments/{asg[0]['id']}/submit", headers=X, json={"text_response": "x"})
    check("non-enrolled user cannot submit assignment", r.status_code == 403)

print("== sessions ==")
email, r = register()
tok = r.json()
H = {"Authorization": f"Bearer {tok['access_token']}"}
requests.post(f"{BASE}/auth/change-password", headers=H,
              json={"current_password": "Secure123!", "new_password": "Changed123!"})
check("access token dies after password change", requests.get(f"{BASE}/auth/me", headers=H).status_code == 401)
r = requests.post(f"{BASE}/auth/refresh", json={"refresh_token": tok["refresh_token"]})
check("refresh token dies after password change", r.status_code == 401)
r = requests.post(f"{BASE}/auth/register", json={"email": "short@test.io", "password": "abc123", "full_name": "Short"})
check("passwords under 8 chars rejected", r.status_code == 422)

print("== admin user deletion ==")
r = requests.get(f"{BASE}/users", headers=A, params={"search": "sarah"}).json()["items"][0]
check("cannot delete an instructor who still owns courses",
      requests.delete(f"{BASE}/users/{r['id']}", headers=A).status_code == 400)
email, r = register()
uid = r.json()["user"]["id"]
check("deleting a normal user works", requests.delete(f"{BASE}/users/{uid}", headers=A).status_code == 200)
check("catalog still loads afterwards", requests.get(f"{BASE}/courses").status_code == 200)

print("\n" + "=" * 40)
print(f"RESULT: {ok} passed, {fail} failed")

import sys as _sys
_sys.exit(1 if fail else 0)
