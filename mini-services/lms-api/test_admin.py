#!/usr/bin/env python3
"""Admin LMS tools and website content: run against a freshly seeded database. Safe to re-run."""
import sys
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


def auth(email, pw):
    r = requests.post(f"{BASE}/auth/login", json={"email": email, "password": pw})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


A = auth("admin@infohive.demo", "Admin123!")
S = auth("sarah@infohive.demo", "Teach123!")
L = auth("emma@example.com", "Study123!")

print("== access control ==")
for path in ["/admin/courses", "/admin/enrollments", "/admin/instructor-requests", "/admin/reports",
             "/admin/certificates", "/admin/instructors", "/admin/site/content"]:
    check(f"instructor blocked from {path}", requests.get(BASE + path, headers=S).status_code == 403)
check("learner blocked from content edit",
      requests.put(f"{BASE}/admin/site/content/home", headers=L, json={}).status_code == 403)
check("anonymous blocked from admin courses", requests.get(f"{BASE}/admin/courses").status_code in (401, 403))

print("== courses ==")
r = requests.get(f"{BASE}/admin/courses?size=100", headers=A).json()
statuses = {c["status"] for c in r["items"]}
check("all courses incl. drafts", "draft" in statuses and "published" in statuses, statuses)
check("status counts", r["counts"].get("published", 0) >= 3, r["counts"])
py = next(c for c in r["items"] if c["slug"] == "python-programming-zero-to-hero")
check("learner + completion stats", py["enrollments"] >= 3 and py["completions"] >= 1, py)
r = requests.get(f"{BASE}/admin/courses?status=draft", headers=A).json()
check("filter by status", all(c["status"] == "draft" for c in r["items"]) and r["items"])
r = requests.get(f"{BASE}/admin/courses?search=python", headers=A).json()
check("search courses", len(r["items"]) == 1)

print("== reassign instructor ==")
inst = requests.get(f"{BASE}/admin/instructors", headers=A).json()
james = next(i for i in inst if i["email"] == "james@infohive.demo")
sarah = next(i for i in inst if i["email"] == "sarah@infohive.demo")
emma_id = requests.get(f"{BASE}/auth/me", headers=L).json()["id"]
r = requests.put(f"{BASE}/admin/courses/{py['id']}/instructor", headers=A, json={"instructor_id": emma_id})
check("can't assign a learner", r.status_code == 400)
r = requests.put(f"{BASE}/admin/courses/{py['id']}/instructor", headers=A, json={"instructor_id": james["id"]})
check("reassign to James", r.status_code == 200, r.text[:120])
J = auth("james@infohive.demo", "Teach123!")
check("James now manages it", any(c["id"] == py["id"] for c in requests.get(f"{BASE}/teach/courses", headers=J).json()))
check("Sarah no longer can", requests.get(f"{BASE}/teach/courses/{py['id']}", headers=S).status_code == 403)
r = requests.put(f"{BASE}/admin/courses/{py['id']}/instructor", headers=A, json={"instructor_id": sarah["id"]})
check("reassign back", r.status_code == 200)

print("== enrollments ==")
r = requests.get(f"{BASE}/admin/enrollments?course_id={py['id']}", headers=A).json()
check("list by course", r["total"] >= 3 and all(e["course"]["id"] == py["id"] for e in r["items"]))
check("rows have last activity", any(e["last_active"] for e in r["items"]))
r = requests.get(f"{BASE}/admin/enrollments?search=emma", headers=A).json()
check("search by learner", r["items"] and all("emma" in e["user"]["email"] for e in r["items"]))
email = f"bulk-{uuid.uuid4().hex[:6]}@test.io"
requests.post(f"{BASE}/auth/register", json={"email": email, "password": "Test123!", "full_name": "Bulk Learner"})
r = requests.post(f"{BASE}/admin/enrollments", headers=A, json={
    "course_id": py["id"], "emails": [email, "emma@example.com", "nobody-here@test.io", "sarah@infohive.demo"], "notify": False})
res = r.json()
check("bulk enroll", r.status_code == 201 and res["enrolled"] == [email], res)
check("reports already / unknown / staff", res["already"] == ["emma@example.com"] and res["not_found"] == ["nobody-here@test.io"]
      and res["not_allowed"] == ["sarah@infohive.demo"], res)
B = auth(email, "Test123!")
check("learner can open the course", requests.get(f"{BASE}/enrollments/my/{py['id']}", headers=B).status_code == 200)
eid = requests.get(f"{BASE}/admin/enrollments?search={email}", headers=A).json()["items"][0]["id"]
check("remove enrollment", requests.delete(f"{BASE}/admin/enrollments/{eid}", headers=A).status_code == 200)
check("learner lost access", requests.get(f"{BASE}/enrollments/my/{py['id']}", headers=B).status_code == 404)

print("== instructor applications ==")
apps = []
for name in ("Approve Me", "Decline Me"):
    em = f"apply-{uuid.uuid4().hex[:6]}@test.io"
    requests.post(f"{BASE}/auth/register", json={"email": em, "password": "Test123!", "full_name": name, "role": "instructor"})
    apps.append(em)
pending = requests.get(f"{BASE}/admin/instructor-requests", headers=A).json()
ids = {p["email"]: p["id"] for p in pending}
check("applications listed", all(e in ids for e in apps), list(ids)[:5])
r = requests.post(f"{BASE}/admin/instructor-requests/{ids[apps[0]]}", headers=A, json={"approve": True, "message": "Welcome!"})
check("approve", r.status_code == 200)
r = requests.post(f"{BASE}/admin/instructor-requests/{ids[apps[1]]}", headers=A, json={"approve": False})
check("decline", r.status_code == 200)
P = auth(apps[0], "Test123!")
check("approved user is an instructor", requests.get(f"{BASE}/auth/me", headers=P).json()["role"] == "instructor")
check("approved user notified", any("approved" in n["title"].lower() for n in requests.get(f"{BASE}/notifications", headers=P).json()["items"]))
D = auth(apps[1], "Test123!")
me = requests.get(f"{BASE}/auth/me", headers=D).json()
check("declined user stays a learner", me["role"] == "student")
left = {p["email"] for p in requests.get(f"{BASE}/admin/instructor-requests", headers=A).json()}
check("both leave the queue", not (set(apps) & left))
check("can't decide twice", requests.post(f"{BASE}/admin/instructor-requests/{ids[apps[1]]}", headers=A, json={"approve": True}).status_code == 404)

print("== reports ==")
r = requests.get(f"{BASE}/admin/reports?days=30", headers=A).json()
check("totals", r["totals"]["learners"] >= 5 and r["totals"]["lessons_completed"] > 0, r["totals"])
check("12-week series", len(r["series"]["weeks"]) == 12 and len(r["series"]["enrollments"]) == 12 and sum(r["series"]["lessons"]) > 0)
check("per-course rows", any(c["id"] == py["id"] and c["enrollments"] >= 3 for c in r["per_course"]))
check("period validated", requests.get(f"{BASE}/admin/reports?days=2", headers=A).status_code == 422)

print("== certificates ==")
r = requests.get(f"{BASE}/admin/certificates", headers=A).json()
check("list certificates", r["total"] >= 1)
cert = next(c for c in r["items"] if c["user_name"] == "Emma Wilson")
check("search by serial", requests.get(f"{BASE}/admin/certificates?search={cert['serial']}", headers=A).json()["total"] == 1)
check("revoke needs a reason", requests.post(f"{BASE}/admin/certificates/{cert['id']}/revoke", headers=A, json={"reason": ""}).status_code == 422)
r = requests.post(f"{BASE}/admin/certificates/{cert['id']}/revoke", headers=A, json={"reason": "Issued in error"})
check("revoke", r.status_code == 200)
v = requests.get(f"{BASE}/certificates/{cert['serial']}").json()
check("public verification shows revoked", v["revoked"] is True and v["revoke_reason"] == "Issued in error")
check("PDF refused when revoked", requests.get(f"{BASE}/certificates/{cert['serial']}/pdf").status_code == 410)
check("learner sees it revoked", any(c["revoked"] for c in requests.get(f"{BASE}/certificates/my", headers=L).json()))
check("filter revoked", requests.get(f"{BASE}/admin/certificates?status=revoked", headers=A).json()["total"] >= 1)
check("restore", requests.post(f"{BASE}/admin/certificates/{cert['id']}/restore", headers=A).status_code == 200)
check("PDF works again", requests.get(f"{BASE}/certificates/{cert['serial']}/pdf").status_code == 200)

print("== website content ==")
pub = requests.get(f"{BASE}/site/content").json()
check("public content has every section", {"home", "services", "reasons", "about", "contact", "social", "banner", "legal"} <= set(pub))
check("defaults present", pub["home"]["headline"] and len(pub["services"]["items"]) >= 6)
check("banner hidden by default", pub["banner"] == {"enabled": False})
home = dict(pub["home"], headline="Build the future with us")
r = requests.put(f"{BASE}/admin/site/content/home", headers=A, json=home)
check("save home", r.status_code == 200)
check("public site reflects edit", requests.get(f"{BASE}/site/content").json()["home"]["headline"] == "Build the future with us")
bad = dict(pub["services"]); bad["items"] = [dict(bad["items"][0], icon="skull")]
check("unknown icon rejected", requests.put(f"{BASE}/admin/site/content/services", headers=A, json=bad).status_code == 422)
check("too-long text rejected", requests.put(f"{BASE}/admin/site/content/home", headers=A, json=dict(home, headline="x" * 500)).status_code == 422)
check("non-https social link rejected",
      requests.put(f"{BASE}/admin/site/content/social", headers=A, json={"facebook": "javascript:alert(1)"}).status_code == 422)
check("unsafe banner link rejected",
      requests.put(f"{BASE}/admin/site/content/banner", headers=A, json={"enabled": True, "text": "x", "link_url": "//evil.example"}).status_code == 422)
r = requests.put(f"{BASE}/admin/site/content/contact", headers=A, json=dict(pub["contact"], email="hello@infohive.test", phone="+234 800 000 0000"))
check("save contact", r.status_code == 200)
cfg = requests.get(f"{BASE}/config/public").json()
check("contact feeds the footer config", cfg["contact"]["email"] == "hello@infohive.test" and cfg["contact"]["phone"])
r = requests.put(f"{BASE}/admin/site/content/legal", headers=A, json={"privacy_html": "<h2>Data</h2><p>Hi<script>alert(1)</script><img src=x onerror=alert(1)></p>", "updated": "1 Nov 2026"})
ph = r.json()["value"]["privacy_html"]
check("legal HTML sanitized", "<script" not in ph and "onerror" not in ph and "<h2>Data</h2>" in ph, ph)
requests.put(f"{BASE}/admin/site/content/banner", headers=A, json={"enabled": True, "text": "New cohort Monday", "link_label": "See courses", "link_url": "/courses"})
check("banner published", requests.get(f"{BASE}/site/content").json()["banner"]["text"] == "New cohort Monday")
meta = requests.get(f"{BASE}/admin/site/content", headers=A).json()["meta"]
check("edit history recorded", meta["home"]["customized"] and meta["home"]["updated_by"] == "Amara Okafor", meta["home"])
for sec in ("home", "contact", "legal", "banner"):
    requests.delete(f"{BASE}/admin/site/content/{sec}", headers=A)
pub2 = requests.get(f"{BASE}/site/content").json()
check("restore original", pub2["home"]["headline"] == pub["home"]["headline"] and pub2["banner"] == {"enabled": False}
      and pub2["legal"]["privacy_html"] is None)
check("unknown section 404", requests.put(f"{BASE}/admin/site/content/nope", headers=A, json={}).status_code == 404)

print(f"\n{'=' * 40}\nRESULT: {ok} passed, {fail} failed")
sys.exit(1 if fail else 0)
