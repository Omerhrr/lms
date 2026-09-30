"""
Seed the LMS with a realistic demo dataset.
Run:  cd mini-services/lms-api && python3 app/seed.py
"""
import os
import sys
from datetime import timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # cwd = lms-api/

from app.core.database import SessionLocal, engine  # noqa: E402
from app.core.security import hash_password        # noqa: E402
from app.shared.utils import utcnow                # noqa: E402
import app.modules.auth.models as m_auth           # noqa: E402
import app.modules.courses.models as m_course      # noqa: E402
import app.modules.enrollments.models as m_enroll  # noqa: E402
import app.modules.assessments.models as m_assess  # noqa: E402
import app.modules.discussions.models as m_disc    # noqa: E402
import app.modules.notifications.models as m_notif # noqa: E402
import app.modules.certificates.models as m_cert   # noqa: E402

from app.modules.certificates.service import issue_certificate  # noqa: E402


def reset():
    Base_metadata = m_auth.Base.metadata
    Base_metadata.drop_all(bind=engine)
    Base_metadata.create_all(bind=engine)


def main():
    reset()
    db = SessionLocal()
    now = utcnow()

    # ---------- users ----------
    admin = m_auth.User(email="admin@learnhub.io", password_hash=hash_password("Admin123!"),
                        full_name="Amara Okafor", role=m_auth.UserRole.admin,
                        headline="Platform administrator")
    sarah = m_auth.User(email="sarah@learnhub.io", password_hash=hash_password("Teach123!"),
                        full_name="Sarah Johnson", role=m_auth.UserRole.instructor,
                        headline="Senior Software Engineer & Educator",
                        bio="Sarah has 12 years of industry experience and has taught over 50,000 students how to code. She focuses on practical, project-driven learning.")
    james = m_auth.User(email="james@learnhub.io", password_hash=hash_password("Teach123!"),
                        full_name="James Chen", role=m_auth.UserRole.instructor,
                        headline="Marketing Strategist & Designer",
                        bio="James has led growth teams at three startups and now teaches marketing and design."
                        )
    students = [
        m_auth.User(email="michael@example.com", password_hash=hash_password("Study123!"),
                    full_name="Michael Brown", role=m_auth.UserRole.student),
        m_auth.User(email="emma@example.com", password_hash=hash_password("Study123!"),
                    full_name="Emma Wilson", role=m_auth.UserRole.student),
        m_auth.User(email="liam@example.com", password_hash=hash_password("Study123!"),
                    full_name="Liam Garcia", role=m_auth.UserRole.student),
        m_auth.User(email="olivia@example.com", password_hash=hash_password("Study123!"),
                    full_name="Olivia Martinez", role=m_auth.UserRole.student),
        m_auth.User(email="noah@example.com", password_hash=hash_password("Study123!"),
                    full_name="Noah Davis", role=m_auth.UserRole.student),
    ]
    db.add_all([admin, sarah, james] + students)
    db.commit()

    # ---------- categories ----------
    cats = {}
    for name, desc in [
        ("Development", "Programming, web & software engineering"),
        ("Business", "Entrepreneurship, finance and management"),
        ("Design", "UI/UX, graphic design and branding"),
        ("Marketing", "Digital marketing, SEO and growth"),
        ("Data Science", "Analytics, ML and visualization"),
    ]:
        slug = name.lower().replace(" ", "-").replace("/", "-")
        cats[name] = m_course.Category(name=name, slug=slug, description=desc)
    db.add_all(cats.values())
    db.commit()

    # ---------- course 1: Python ----------
    c1 = m_course.Course(
        title="Python Programming: Zero to Hero",
        slug="python-programming-zero-to-hero",
        summary="Master Python from the very basics to building real applications - no prior experience needed.",
        description=(
            "<h2>Why this course?</h2>"
            "<p>Python is the most beginner-friendly, in-demand programming language in the world. "
            "This course takes you from absolute zero to confidently building your own applications.</p>"
            "<h3>What you will learn</h3>"
            "<ul><li>Python syntax, variables and data types</li>"
            "<li>Control flow, loops and functions</li>"
            "<li>Object-oriented programming fundamentals</li>"
            "<li>Working with files, errors and modules</li>"
            "<li>Building a complete capstone project</li></ul>"
            "<p>Every section includes practical exercises and quizzes to lock in your knowledge.</p>"
        ),
        category_id=cats["Development"].id, instructor_id=sarah.id,
        status=m_course.CourseStatus.published, price=49.99,
        level=m_course.CourseLevel.beginner, is_featured=True,
        tags=["python", "programming", "beginner-friendly"],
    )
    db.add(c1)
    db.commit()

    s1 = m_course.Section(course_id=c1.id, title="Getting Started", position=0)
    s2 = m_course.Section(course_id=c1.id, title="Python Fundamentals", position=1)
    s3 = m_course.Section(course_id=c1.id, title="Leveling Up", position=2)
    db.add_all([s1, s2, s3]); db.commit()

    l1 = m_course.Lesson(section_id=s1.id, course_id=c1.id, title="Welcome & Course Roadmap", type=m_course.LessonType.text,
                         content="Welcome to the course!\n\nIn this short lesson we map out the entire journey: from installing Python to shipping a real application.\n\n## What to expect\n- Short, focused video lessons\n- Hands-on exercises after each section\n- Quizzes to reinforce key concepts\n\nTake your time and enjoy the ride!", duration_minutes=4, is_preview=True, position=0)
    l2 = m_course.Lesson(section_id=s1.id, course_id=c1.id, title="Installing Python & Your Editor", type=m_course.LessonType.video,
                         video_url="https://www.youtube.com/embed/rfscVS0vtbw", duration_minutes=9, is_preview=True, position=1)
    l3 = m_course.Lesson(section_id=s2.id, course_id=c1.id, title="Variables & Data Types", type=m_course.LessonType.text,
                         content="Variables are containers for storing data values.\n\n## Core data types\n- int - whole numbers (42)\n- float - decimals (3.14)\n- str - text (\"hello\")\n- bool - True / False\n\nPython is dynamically typed, so you never declare a type explicitly - the interpreter figures it out.\n\nname = \"Ada\"\nage = 36\npi = 3.14159", duration_minutes=12, position=0)
    l4 = m_course.Lesson(section_id=s2.id, course_id=c1.id, title="Control Flow: If, Elif, Else", type=m_course.LessonType.text,
                         content="Programs make decisions using conditional statements.\n\nscore = 85\nif score >= 90:\n    print(\"A\")\nelif score >= 80:\n    print(\"B\")\nelse:\n    print(\"Keep practicing!\")\n\nIndentation matters in Python - it defines code blocks.", duration_minutes=11, position=1)
    l5 = m_course.Lesson(section_id=s2.id, course_id=c1.id, title="Fundamentals Check-up", type=m_course.LessonType.quiz,
                         duration_minutes=10, position=2)
    l6 = m_course.Lesson(section_id=s3.id, course_id=c1.id, title="Functions & Reusable Code", type=m_course.LessonType.video,
                         video_url="https://www.youtube.com/embed/rfscVS0vtbw", duration_minutes=14, position=0)
    l7 = m_course.Lesson(section_id=s3.id, course_id=c1.id, title="Course Downloads & Cheat Sheet", type=m_course.LessonType.file,
                         file_url="/api/media/files/cheatsheet.pdf", duration_minutes=2, position=1)
    db.add_all([l1, l2, l3, l4, l5, l6, l7]); db.commit()

    quiz1 = m_assess.Quiz(lesson_id=l5.id, title="Python Fundamentals Quiz", description="Test what you learned about variables, types and control flow.",
                          passing_score=60, max_attempts=3)
    db.add(quiz1); db.commit()
    q1 = m_assess.Question(quiz_id=quiz1.id, type=m_assess.QuestionType.single_choice,
                           text="Which data type would you use to store the value 3.14?",
                           options=["int", "float", "str", "bool"], correct=[1], points=1,
                           explanation="3.14 is a decimal number, which is stored as a float.", position=0)
    q2 = m_assess.Question(quiz_id=quiz1.id, type=m_assess.QuestionType.true_false,
                           text="Python requires you to declare the type of a variable before using it.",
                           options=["True", "False"], correct=[1], points=1,
                           explanation="Python is dynamically typed - no declaration needed.", position=1)
    q3 = m_assess.Question(quiz_id=quiz1.id, type=m_assess.QuestionType.multi_choice,
                           text="Which of the following are valid Python variable names?",
                           options=["my_var", "2cool", "_hidden", "class"], correct=[0, 2], points=2,
                           explanation="Names can't start with a digit, and 'class' is a reserved keyword.", position=2)
    q4 = m_assess.Question(quiz_id=quiz1.id, type=m_assess.QuestionType.short_answer,
                           text="What keyword defines a function in Python?", correct=["def"], points=2,
                           explanation="def is used to define functions.", position=3)
    db.add_all([q1, q2, q3, q4]); db.commit()

    a1 = m_assess.Assignment(course_id=c1.id, title="Build a Number Guessing Game",
                             instructions="Write a small Python program that picks a random number and lets the user guess it with hints ('higher' / 'lower'). Submit your .py file or paste the code as text.",
                             max_points=100, allow_file=True, position=0)
    db.add(a1); db.commit()

    # ---------- course 2: Marketing ----------
    c2 = m_course.Course(
        title="Digital Marketing Masterclass 2026",
        slug="digital-marketing-masterclass-2026",
        summary="Grow any business with proven digital marketing systems: SEO, social media, email funnels and paid ads.",
        description=(
            "<h2>Marketing that actually converts</h2>"
            "<p>Learn the exact playbooks used by high-growth startups. This masterclass covers the full funnel: "
            "attract, engage, convert and retain.</p>"
            "<ul><li>Build a marketing strategy from scratch</li>"
            "<li>SEO fundamentals that still work in 2026</li>"
            "<li>Email sequences that generate revenue</li>"
            "<li> Paid ads on a bootstrap budget</li></ul>"
        ),
        category_id=cats["Marketing"].id, instructor_id=james.id,
        status=m_course.CourseStatus.published, price=29.99,
        level=m_course.CourseLevel.intermediate, is_featured=True,
        tags=["marketing", "seo", "growth"],
    )
    db.add(c2); db.commit()
    ms1 = m_course.Section(course_id=c2.id, title="Marketing Foundations", position=0)
    ms2 = m_course.Section(course_id=c2.id, title="Channels & Funnels", position=1)
    db.add_all([ms1, ms2]); db.commit()
    ml1 = m_course.Lesson(section_id=ms1.id, course_id=c2.id, title="The Modern Marketing Landscape", type=m_course.LessonType.video,
                          video_url="https://www.youtube.com/embed/nU-IIXBWlS4", duration_minutes=13, is_preview=True, position=0)
    ml2 = m_course.Lesson(section_id=ms1.id, course_id=c2.id, title="Defining Your Ideal Customer", type=m_course.LessonType.text,
                          content="Before spending a single dollar on ads, you must know exactly who you are talking to.\n\nBuild a one-page ICP (Ideal Customer Profile):\n- Demographics\n- Pain points\n- Where they hang out online\n- The message that makes them click", duration_minutes=8, position=1)
    ml3 = m_course.Lesson(section_id=ms2.id, course_id=c2.id, title="SEO That Still Works", type=m_course.LessonType.video,
                          video_url="https://www.youtube.com/embed/nU-IIXBWlS4", duration_minutes=16, position=0)
    ml4 = m_course.Lesson(section_id=ms2.id, course_id=c2.id, title="Channel Strategy Quiz", type=m_course.LessonType.quiz, duration_minutes=8, position=1)
    db.add_all([ml1, ml2, ml3, ml4]); db.commit()

    mquiz = m_assess.Quiz(lesson_id=ml4.id, title="Channel Strategy Quiz", passing_score=50, max_attempts=0)
    db.add(mquiz); db.commit()
    mq1 = m_assess.Question(quiz_id=mquiz.id, type=m_assess.QuestionType.single_choice,
                            text="What does SEO stand for?", options=["Social Engagement Optimization", "Search Engine Optimization", "Sales Enablement Operations", "Search Email Outreach"],
                            correct=[1], points=1, position=0)
    mq2 = m_assess.Question(quiz_id=mquiz.id, type=m_assess.QuestionType.short_answer,
                            text="Name the marketing funnel stage where a visitor first learns about your brand.", correct=["awareness", "awareness stage", "top of funnel", "tofu"], points=1, position=1)
    db.add_all([mq1, mq2]); db.commit()

    # ---------- course 3: Design (free) ----------
    c3 = m_course.Course(
        title="UI/UX Design Fundamentals",
        slug="ui-ux-design-fundamentals",
        summary="Learn the core principles of beautiful, usable interfaces: layout, typography, color and user research.",
        description=(
            "<h2>Design for humans</h2>"
            "<p>Great products feel effortless. This free course teaches the timeless principles behind great interfaces "
            "and shows you how to apply them immediately.</p>"
            "<ul><li>Visual hierarchy and layout systems</li>"
            "<li>Typography that communicates</li>"
            "<li>Color theory in practice</li>"
            "<li>Usability heuristics and user testing basics</li></ul>"
        ),
        category_id=cats["Design"].id, instructor_id=sarah.id,
        status=m_course.CourseStatus.published, price=0,
        level=m_course.CourseLevel.beginner, is_featured=True,
        tags=["design", "ui", "ux", "free"],
    )
    db.add(c3); db.commit()
    ds1 = m_course.Section(course_id=c3.id, title="Foundations", position=0)
    db.add(ds1); db.commit()
    dl1 = m_course.Lesson(section_id=ds1.id, course_id=c3.id, title="What Makes Design 'Good'?", type=m_course.LessonType.text,
                          content="Good design is invisible. Users don't notice it - they just accomplish their goals.\n\n## The four pillars\n- Clarity: users instantly understand\n- Consistency: similar things look and behave similarly\n- Feedback: every action has a visible reaction\n- Simplicity: remove everything that doesn't help", duration_minutes=7, is_preview=True, position=0)
    dl2 = m_course.Lesson(section_id=ds1.id, course_id=c3.id, title="Typography & Spacing Systems", type=m_course.LessonType.video,
                          video_url="https://www.youtube.com/embed/_6jK-2nHc1M", duration_minutes=12, position=1)
    dl3 = m_course.Lesson(section_id=ds1.id, course_id=c3.id, title="Design Principles Quiz", type=m_course.LessonType.quiz, duration_minutes=6, position=2)
    db.add_all([dl1, dl2, dl3]); db.commit()
    dquiz = m_assess.Quiz(lesson_id=dl3.id, title="Design Principles Quiz", passing_score=60)
    db.add(dquiz); db.commit()
    dq1 = m_assess.Question(quiz_id=dquiz.id, type=m_assess.QuestionType.single_choice,
                            text="Which principle says 'similar elements should look and behave similarly'?",
                            options=["Contrast", "Consistency", "Randomness", "Density"], correct=[1], points=1, position=0)
    db.add(dq1); db.commit()

    # ---------- course 4: draft ----------
    c4 = m_course.Course(
        title="Data Analysis with Spreadsheets",
        slug="data-analysis-with-spreadsheets",
        summary="Turn raw data into decisions using spreadsheets: cleaning, pivot tables, charts and dashboards.",
        description="<h2>Coming soon</h2><p>This hands-on course is being prepared. Watch this space!</p>",
        category_id=cats["Data Science"].id, instructor_id=james.id,
        status=m_course.CourseStatus.draft, price=19.99, level=m_course.CourseLevel.beginner,
        tags=["data", "spreadsheets", "excel"],
    )
    db.add(c4); db.commit()
    xs1 = m_course.Section(course_id=c4.id, title="Spreadsheet Basics", position=0)
    db.add(xs1); db.commit()
    xl1 = m_course.Lesson(section_id=xs1.id, course_id=c4.id, title="Formulas Every Analyst Needs", type=m_course.LessonType.text,
                          content="SUM, AVERAGE, VLOOKUP, INDEX/MATCH and friends - the daily toolkit of every analyst.", duration_minutes=10, position=0)
    db.add(xl1); db.commit()

    # ---------- enrollments & progress ----------
    def enroll(course, user, days_ago=5):
        e = m_enroll.Enrollment(course_id=course.id, user_id=user.id,
                                enrolled_at=now - timedelta(days=days_ago))
        db.add(e); db.commit(); db.refresh(e)
        return e

    e1 = enroll(c1, students[0], 20)   # Michael - python, 40%
    for lid in [l1.id, l2.id, l3.id]:
        db.add(m_enroll.LessonProgress(enrollment_id=e1.id, lesson_id=lid))
    e1.progress = round(3 / 7 * 100, 1)
    db.commit()

    e2 = enroll(c1, students[1], 35)   # Emma - python, completed
    for lid in [l1.id, l2.id, l3.id, l4.id, l5.id, l6.id, l7.id]:
        db.add(m_enroll.LessonProgress(enrollment_id=e2.id, lesson_id=lid))
    e2.progress = 100.0; e2.status = "completed"; e2.completed_at = now - timedelta(days=2)
    db.commit()

    e3 = enroll(c2, students[1], 10)   # Emma - marketing 25%
    for lid in [ml1.id]:
        db.add(m_enroll.LessonProgress(enrollment_id=e3.id, lesson_id=lid))
    e3.progress = round(1 / 4 * 100, 1)
    db.commit()

    e4 = enroll(c3, students[2], 8)    # Liam - design 33%
    for lid in [dl1.id]:
        db.add(m_enroll.LessonProgress(enrollment_id=e4.id, lesson_id=lid))
    e4.progress = round(1 / 3 * 100, 1)
    db.commit()

    e5 = enroll(c3, students[3], 15)   # Olivia - design completed
    for lid in [dl1.id, dl2.id, dl3.id]:
        db.add(m_enroll.LessonProgress(enrollment_id=e5.id, lesson_id=lid))
    e5.progress = 100.0; e5.status = "completed"; e5.completed_at = now - timedelta(days=1)
    db.commit()

    e6 = enroll(c2, students[4], 3)    # Noah - marketing, just started
    e7 = enroll(c1, students[2], 12)   # Liam - python, 14%
    db.add(m_enroll.LessonProgress(enrollment_id=e7.id, lesson_id=l1.id))
    e7.progress = round(1 / 7 * 100, 1)
    db.commit()

    # ---------- quiz attempts ----------
    db.add(m_assess.QuizAttempt(quiz_id=quiz1.id, user_id=students[1].id,
                                answers={str(q1.id): [1], str(q2.id): [1], str(q3.id): [0, 2], str(q4.id): ["def"]},
                                score=100.0, passed=True, submitted_at=now - timedelta(days=3)))
    db.add(m_assess.QuizAttempt(quiz_id=quiz1.id, user_id=students[0].id,
                                answers={str(q1.id): [1], str(q2.id): [0], str(q3.id): [0], str(q4.id): ["func"]},
                                score=50.0, passed=False, submitted_at=now - timedelta(days=1)))
    db.commit()

    # ---------- assignment submission ----------
    db.add(m_assess.Submission(assignment_id=a1.id, user_id=students[1].id,
                               text_response="import random\nsecret = random.randint(1, 100)\n# ... game loop with hints\nclass full solution attached",
                               submitted_at=now - timedelta(days=4), status="submitted"))
    db.commit()

    # ---------- reviews ----------
    db.add_all([
        m_course.Review(course_id=c1.id, user_id=students[1].id, rating=5,
                        comment="Sarah explains complex topics so clearly. The quizzes really helped me retain everything!", created_at=now - timedelta(days=2)),
        m_course.Review(course_id=c1.id, user_id=students[0].id, rating=4,
                        comment="Great content so far. Would love even more exercises.", created_at=now - timedelta(days=1)),
        m_course.Review(course_id=c2.id, user_id=students[1].id, rating=4,
                        comment="Solid frameworks I could apply the same week.", created_at=now - timedelta(days=6)),
        m_course.Review(course_id=c3.id, user_id=students[3].id, rating=5,
                        comment="Free course with paid-course quality. Highly recommended!", created_at=now - timedelta(days=1)),
    ]); db.commit()

    # ---------- discussions ----------
    t1 = m_disc.Thread(course_id=c1.id, author_id=students[0].id, title="Stuck on the guessing game exercise",
                       body="When the user types a non-number my program crashes. How do I handle bad input?",
                       created_at=now - timedelta(days=2))
    db.add(t1); db.commit()
    p1 = m_disc.Post(thread_id=t1.id, author_id=sarah.id,
                     body="Great question! Wrap the input in a try/except block:\n\ntry:\n    guess = int(input())\nexcept ValueError:\n    print('Please enter a number')", created_at=now - timedelta(days=2))
    p2 = m_disc.Post(thread_id=t1.id, author_id=students[0].id, parent_id=p1.id,
                     body="That fixed it - thank you so much! 🙌", created_at=now - timedelta(days=1))
    db.add_all([p1, p2])
    t2 = m_disc.Thread(course_id=c1.id, author_id=students[2].id, title="Study group for this course?",
                       body="Anyone want to review the fundamentals section together this weekend?", created_at=now - timedelta(days=3))
    db.add(t2); db.commit()

    # ---------- announcements ----------
    db.add(m_notif.Announcement(course_id=c1.id, author_id=sarah.id,
                                title="New: cheat sheet added to the last lesson",
                                body="I just uploaded a printable Python cheat sheet at the end of the course. Download it from the 'Course Downloads' lesson.",
                                created_at=now - timedelta(days=4)))
    db.add(m_notif.Announcement(course_id=c2.id, author_id=james.id,
                                title="Live Q&A session this Friday",
                                body="Bring your questions about SEO - we'll do a 60-minute live teardown of student websites.",
                                created_at=now - timedelta(days=2)))
    db.commit()

    # ---------- notifications ----------
    def n(user, type, title, body, link, days_ago=1, read=False):
        db.add(m_notif.Notification(user_id=user.id, type=type, title=title, body=body, link=link,
                                    is_read=read, created_at=now - timedelta(days=days_ago)))
    n(students[0], "enrollment", "Welcome aboard! 🎉", "You are now enrolled in “Python Programming: Zero to Hero”.", "/learn/python-programming-zero-to-hero", 20, True)
    n(students[1], "certificate", "🎓 Course completed!", "Congratulations! You completed “Python Programming: Zero to Hero”.", "#", 2)
    n(students[0], "grade", "Quiz results available", "You scored 50% on “Python Fundamentals Quiz”. Review and try again!", "/learn/python-programming-zero-to-hero", 1)
    n(sarah, "discussion", "New question in Python Programming", "Michael Brown asked: “Stuck on the guessing game exercise”", "/courses/python-programming-zero-to-hero", 2, True)
    n(admin, "system", "👋 Welcome to LearnHub", "Your platform is ready. Explore the admin area to manage users and courses.", "/admin", 25, True)
    db.commit()

    # ---------- certificates ----------
    issue_certificate(db, students[1].id, c1.id)   # Emma × Python
    issue_certificate(db, students[3].id, c3.id)   # Olivia × Design

    db.close()
    print("✅ Seed complete!")
    print("   admin     : admin@learnhub.io / Admin123!")
    print("   instructor: sarah@learnhub.io / Teach123!")
    print("   instructor: james@learnhub.io / Teach123!")
    print("   student   : michael@example.com / Study123!")
    print("   student   : emma@example.com / Study123!  (completed Python course)")


if __name__ == "__main__":
    main()
