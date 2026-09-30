#!/usr/bin/env python3
"""End-to-end API smoke test for LearnHub LMS."""
import requests

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
    return r.json()["access_token"], r


print("== auth ==")
admin_tok, r = login("admin@learnhub.io", "Admin123!")
check("admin login", r.status_code == 200)
sarah_tok, r = login("sarah@learnhub.io", "Teach123!")
check("instructor login", r.status_code == 200)
stud_tok, r = login("emma@example.com", "Study123!")
check("student login", r.status_code == 200)
A = {"Authorization": f"Bearer {admin_tok}"}
S = {"Authorization": f"Bearer {sarah_tok}"}
T = {"Authorization": f"Bearer {stud_tok}"}

r = requests.post(f"{BASE}/auth/register", json={"email": "newuser@test.io", "password": "Test123!", "full_name": "New Tester", "role": "student"})
check("register new student", r.status_code == 201, r.text[:100])
new_tok = r.json()["access_token"]
N = {"Authorization": f"Bearer {new_tok}"}

print("== catalog ==")
r = requests.get(f"{BASE}/courses")
check("list published courses", r.status_code == 200 and len(r.json()["items"]) == 3)
r = requests.get(f"{BASE}/courses/python-programming-zero-to-hero")
detail = r.json()
check("course detail w/ curriculum", r.status_code == 200 and len(detail["sections"]) == 3)
check("course rating aggregated", detail["review_count"] == 2, detail["review_count"])
r = requests.get(f"{BASE}/courses?search=design&category_id=3")
check("catalog search+filter", r.status_code == 200 and r.json()["total"] == 1)
r = requests.get(f"{BASE}/categories")
check("categories", len(r.json()) == 5)

print("== enroll & progress ==")
r = requests.post(f"{BASE}/enrollments/1", headers={"Authorization": f"Bearer {new_tok}"})
check("self-enroll", r.status_code == 201, r.text[:100])
r = requests.get(f"{BASE}/enrollments/my", headers=N)
check("my enrollments", len(r.json()) == 1 and r.json()[0]["progress"] == 0)
r = requests.post(f"{BASE}/enrollments/1/lessons/1/complete", headers=N)
check("complete lesson 1", r.status_code == 200 and r.json()["progress"] > 0, r.text[:100])
r = requests.get(f"{BASE}/enrollments/my/1", headers=N)
check("lesson progress map", 1 in r.json()["completed_lesson_ids"])
r = requests.post(f"{BASE}/enrollments/1/lessons/1/uncomplete", headers=N)
check("uncomplete lesson", r.status_code == 200)
requests.post(f"{BASE}/enrollments/1/lessons/1/complete", headers=N)

print("== quiz flow (student takes quiz via api) ==")
r = requests.get(f"{BASE}/quizzes/1", headers=T)
quiz = r.json()
check("quiz payload hides answers", r.status_code == 200 and "correct" not in quiz["questions"][0])
check("already passed blocks retake", quiz["passed"] is True and quiz["can_take"] is False)
r = requests.get(f"{BASE}/quizzes/3", headers=N)   # design quiz (not enrolled)
check("non-enrolled blocked from quiz", r.status_code == 403)

print("== instructor teaches ==")
r = requests.get(f"{BASE}/teach/courses", headers=S)
check("instructor course list", r.status_code == 200 and len(r.json()) == 2)
r = requests.post(f"{BASE}/teach/courses", headers=S, json={"title": "Test Course from API", "summary": "s", "price": 9.99})
check("create course", r.status_code == 201, r.text[:100])
cid = r.json()["id"]
r = requests.post(f"{BASE}/teach/courses/{cid}/sections", headers=S, json={"title": "Intro"})
sec = r.json()
r = requests.post(f"{BASE}/teach/sections/{sec['id']}/lessons", headers=S, json={"title": "Hello Lesson", "type": "video", "video_url": "https://x.y/v", "duration_minutes": 5})
check("create section + lesson", r.status_code == 201, r.text[:100])
r = requests.post(f"{BASE}/teach/courses/{cid}/publish", headers=S)
check("publish course", r.status_code == 200)
r = requests.post(f"{BASE}/teach/courses/{cid}/assignments", headers=S, json={"title": "HW1", "instructions": "do it", "max_points": 50})
check("create assignment", r.status_code == 201, r.text[:100])
r = requests.post(f"{BASE}/teach/courses/{cid}/announcements", headers=S, json={"title": "Welcome!", "body": "Let's go"})
check("create announcement", r.status_code == 201, r.text[:100])

print("== assignment submit & grade ==")
r = requests.post(f"{BASE}/assignments/1/submit", headers=N, json={"text_response": "my solution"})
check("submit assignment", r.status_code == 201, r.text[:100])
r = requests.get(f"{BASE}/teach/assignments/1/submissions", headers=S)
check("view submissions", r.status_code == 200 and len(r.json()) >= 2)
r = requests.put(f"{BASE}/teach/submissions/2/grade", headers=S, json={"grade": 88, "feedback": "nice"})
check("grade submission", r.status_code == 200, r.text[:100])
r = requests.get(f"{BASE}/assignments/1/my-submission", headers=N)
check("student sees grade", r.json()["grade"] == 88)

print("== gradebook & analytics ==")
r = requests.get(f"{BASE}/teach/courses/1/gradebook", headers=S)
check("gradebook matrix", r.status_code == 200 and len(r.json()["students"]) >= 3)
r = requests.get(f"{BASE}/teach/analytics/overview", headers=S)
check("instructor overview", r.status_code == 200 and r.json()["totals"]["enrollments"] > 0)
r = requests.get(f"{BASE}/teach/analytics/courses/1", headers=S)
check("course analytics", r.status_code == 200 and len(r.json()["lesson_stats"]) == 7)

print("== discussions ==")
r = requests.post(f"{BASE}/courses/1/discussions", headers=N, json={"title": "Test thread", "body": "hello"})
tid = r.json()["id"]
check("create thread", r.status_code == 201)
r = requests.post(f"{BASE}/discussions/{tid}/posts", headers=S, json={"body": "instructor reply"})
check("reply to thread", r.status_code == 201, r.text[:100])
r = requests.post(f"{BASE}/discussions/{tid}/pin", headers=S)
check("pin thread", r.status_code == 200 and r.json()["is_pinned"] is True)

print("== notifications & certificates ==")
r = requests.get(f"{BASE}/notifications/unread-count", headers=S)
check("unread count", r.status_code == 200 and r.json()["count"] >= 1)
r = requests.post(f"{BASE}/notifications/read-all", headers=S)
check("read all", r.status_code == 200)
r = requests.get(f"{BASE}/certificates/my", headers=T)
check("certificates list (seeded)", len(r.json()) == 1)
serial = r.json()[0]["serial"]
r = requests.get(f"{BASE}/certificates/{serial}")
check("public certificate verify (no auth)", r.status_code == 200 and r.json()["user_name"])

print("== completion → auto certificate ==")
r = requests.post(f"{BASE}/auth/login", json={"email": "newuser@test.io", "password": "Test123!"})
for lid in [2, 3, 4, 5, 6, 7]:
    requests.post(f"{BASE}/enrollments/1/lessons/{lid}/complete", headers=N)
r = requests.get(f"{BASE}/enrollments/my", headers=N)
row = [e for e in r.json() if e["course"]["id"] == 1][0]
check("progress hits 100%", row["progress"] == 100.0 and row["status"] == "completed", row["progress"])
r = requests.get(f"{BASE}/certificates/my", headers=N)
check("certificate auto-issued", len(r.json()) == 1, r.text[:200])

print("== admin ==")
r = requests.get(f"{BASE}/admin/stats", headers=A)
check("admin stats", r.status_code == 200 and r.json()["total_users"] >= 8)
r = requests.get(f"{BASE}/users?search=emma", headers=A)
check("user search", len(r.json()["items"]) == 1)
r = requests.post(f"{BASE}/categories", headers=A, json={"name": "Music Production"})
check("create category", r.status_code == 201)
r = requests.put(f"{BASE}/users/{ [u for u in requests.get(f'{BASE}/users?search=newuser', headers=A).json()['items']][0]['id'] }", params={"is_active": False}, headers=A)
check("deactivate user", r.status_code == 200)
r = requests.get(f"{BASE}/auth/me", headers=N)
check("deactivated user blocked", r.status_code == 401)

print("== media ==")
r = requests.post(f"{BASE}/media/upload", headers=S, files={"file": ("test.txt", b"hello world", "text/plain")})
check("file upload", r.status_code == 200 and r.json()["url"], r.text[:100])
r = requests.get(f"{BASE}" + r.json()["url"].replace("/api", "", 1))
check("uploaded file served", r.status_code == 200 and b"hello world" in r.content)

print(f"\n{'='*40}\nRESULT: {ok} passed, {fail} failed")
