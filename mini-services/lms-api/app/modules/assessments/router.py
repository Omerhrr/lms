from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.deps import any_user, staff_required
from app.modules.auth.models import User
from app.modules.courses.models import Lesson
from app.modules.courses.service import CoursesService
from app.modules.assessments.models import Assignment, Submission
from app.modules.assessments.service import AssessmentService

router = APIRouter(tags=["assessments"])


# ============ instructor ============

@router.get("/teach/lessons/{lesson_id}/quiz")
def lesson_quiz(lesson_id: int, db: Session = Depends(get_db), user: User = Depends(staff_required)):
    """Fetch (or create-none) the quiz attached to a lesson, with full question data for the editor."""
    lesson = db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(404, "Lesson not found")
    CoursesService.assert_can_manage(CoursesService.get_course(db, lesson.course_id), user)
    from app.modules.assessments.models import Quiz
    quiz = db.query(Quiz).filter(Quiz.lesson_id == lesson_id).first()
    if not quiz:
        raise HTTPException(404, "No quiz yet")
    return {
        "id": quiz.id, "lesson_id": quiz.lesson_id, "title": quiz.title,
        "description": quiz.description, "time_limit_minutes": quiz.time_limit_minutes,
        "passing_score": quiz.passing_score, "max_attempts": quiz.max_attempts,
        "questions": [
            {"id": q.id, "type": q.type.value, "text": q.text, "options": q.options,
             "correct": q.correct, "points": q.points, "explanation": q.explanation, "position": q.position}
            for q in sorted(quiz.questions, key=lambda x: x.position)
        ],
    }


@router.put("/teach/lessons/{lesson_id}/quiz")
def save_quiz(lesson_id: int, body: dict, db: Session = Depends(get_db), user: User = Depends(staff_required)):
    lesson = db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(404, "Lesson not found")
    course = CoursesService.get_course(db, lesson.course_id)
    CoursesService.assert_can_manage(course, user)
    quiz = AssessmentService.upsert_quiz(db, lesson_id, body)
    return {"id": quiz.id, "title": quiz.title}


@router.get("/teach/quizzes/{quiz_id}")
def quiz_for_editor(quiz_id: int, db: Session = Depends(get_db), user: User = Depends(staff_required)):
    quiz = AssessmentService.get_quiz(db, quiz_id)
    lesson = db.get(Lesson, quiz.lesson_id)
    course = CoursesService.get_course(db, lesson.course_id)
    CoursesService.assert_can_manage(course, user)
    return {
        "id": quiz.id, "lesson_id": quiz.lesson_id, "title": quiz.title,
        "description": quiz.description, "time_limit_minutes": quiz.time_limit_minutes,
        "passing_score": quiz.passing_score, "max_attempts": quiz.max_attempts,
        "questions": [
            {"id": q.id, "type": q.type.value, "text": q.text, "options": q.options,
             "correct": q.correct, "points": q.points, "explanation": q.explanation, "position": q.position}
            for q in sorted(quiz.questions, key=lambda x: x.position)
        ],
    }


@router.post("/teach/quizzes/{quiz_id}/questions", status_code=201)
def add_question(quiz_id: int, body: dict, db: Session = Depends(get_db), user: User = Depends(staff_required)):
    quiz = AssessmentService.get_quiz(db, quiz_id)
    lesson = db.get(Lesson, quiz.lesson_id)
    CoursesService.assert_can_manage(CoursesService.get_course(db, lesson.course_id), user)
    q = AssessmentService.add_question(db, quiz, body)
    return {"id": q.id, "message": "Question added"}


@router.put("/teach/questions/{question_id}")
def update_question(question_id: int, body: dict, db: Session = Depends(get_db), user: User = Depends(staff_required)):
    from app.modules.assessments.models import Question
    q = db.get(Question, question_id)
    if not q:
        raise HTTPException(404, "Question not found")
    lesson = db.get(Lesson, q.quiz.lesson_id)
    CoursesService.assert_can_manage(CoursesService.get_course(db, lesson.course_id), user)
    AssessmentService.update_question(db, q, body)
    return {"message": "Question updated"}


@router.delete("/teach/questions/{question_id}")
def delete_question(question_id: int, db: Session = Depends(get_db), user: User = Depends(staff_required)):
    from app.modules.assessments.models import Question
    q = db.get(Question, question_id)
    if not q:
        raise HTTPException(404, "Question not found")
    lesson = db.get(Lesson, q.quiz.lesson_id)
    CoursesService.assert_can_manage(CoursesService.get_course(db, lesson.course_id), user)
    AssessmentService.delete_question(db, q)
    return {"message": "Question deleted"}


@router.get("/teach/quizzes/{quiz_id}/attempts")
def quiz_attempts(quiz_id: int, db: Session = Depends(get_db), user: User = Depends(staff_required)):
    from app.modules.assessments.models import QuizAttempt
    quiz = AssessmentService.get_quiz(db, quiz_id)
    lesson = db.get(Lesson, quiz.lesson_id)
    CoursesService.assert_can_manage(CoursesService.get_course(db, lesson.course_id), user)
    attempts = (
        db.query(QuizAttempt).filter(QuizAttempt.quiz_id == quiz.id)
        .order_by(QuizAttempt.submitted_at.desc()).all()
    )
    return [
        {"id": a.id, "score": a.score, "passed": a.passed, "submitted_at": a.submitted_at.isoformat(),
         "user": {"id": a.user.id, "full_name": a.user.full_name, "email": a.user.email}}
        for a in attempts
    ]


# ---- assignments ----

@router.post("/teach/courses/{course_id}/assignments", status_code=201)
def add_assignment(course_id: int, body: dict, db: Session = Depends(get_db), user: User = Depends(staff_required)):
    course = CoursesService.get_course(db, course_id)
    CoursesService.assert_can_manage(course, user)
    if not body.get("title"):
        raise HTTPException(400, "Assignment title is required")
    from sqlalchemy import func
    from app.modules.assessments.models import Assignment as A
    pos = db.query(func.coalesce(func.max(A.position), -1)).filter(A.course_id == course_id).scalar() + 1
    a = AssessmentService.add_assignment(db, course_id, body, pos)
    return {"id": a.id, "title": a.title}


@router.put("/teach/assignments/{assignment_id}")
def update_assignment(assignment_id: int, body: dict, db: Session = Depends(get_db), user: User = Depends(staff_required)):
    a = db.get(Assignment, assignment_id)
    if not a:
        raise HTTPException(404, "Assignment not found")
    CoursesService.assert_can_manage(CoursesService.get_course(db, a.course_id), user)
    for f in ("title", "instructions", "max_points", "allow_file", "due_date"):
        if f in body and body[f] is not None:
            setattr(a, f, body[f])
    db.commit()
    return {"message": "Assignment updated"}


@router.delete("/teach/assignments/{assignment_id}")
def delete_assignment(assignment_id: int, db: Session = Depends(get_db), user: User = Depends(staff_required)):
    a = db.get(Assignment, assignment_id)
    if not a:
        raise HTTPException(404, "Assignment not found")
    CoursesService.assert_can_manage(CoursesService.get_course(db, a.course_id), user)
    db.delete(a)
    db.commit()
    return {"message": "Assignment deleted"}


@router.get("/teach/assignments/{assignment_id}/submissions")
def assignment_submissions(assignment_id: int, db: Session = Depends(get_db), user: User = Depends(staff_required)):
    a = db.get(Assignment, assignment_id)
    if not a:
        raise HTTPException(404, "Assignment not found")
    CoursesService.assert_can_manage(CoursesService.get_course(db, a.course_id), user)
    subs = (
        db.query(Submission).options(joinedload(Submission.user))
        .filter(Submission.assignment_id == assignment_id)
        .order_by(Submission.submitted_at.desc()).all()
    )
    return [
        {"id": s.id, "text_response": s.text_response, "file_url": s.file_url,
         "submitted_at": s.submitted_at.isoformat(), "status": s.status,
         "grade": s.grade, "feedback": s.feedback,
         "user": {"id": s.user.id, "full_name": s.user.full_name, "email": s.user.email}}
        for s in subs
    ]


@router.put("/teach/submissions/{submission_id}/grade")
def grade_submission(submission_id: int, body: dict, db: Session = Depends(get_db), user: User = Depends(staff_required)):
    sub = db.get(Submission, submission_id)
    if not sub:
        raise HTTPException(404, "Submission not found")
    a = db.get(Assignment, sub.assignment_id)
    CoursesService.assert_can_manage(CoursesService.get_course(db, a.course_id), user)
    if body.get("grade") is None:
        raise HTTPException(400, "Grade is required")
    AssessmentService.grade_submission(db, sub, float(body["grade"]), body.get("feedback"), user.id)
    return {"message": "Submission graded"}


@router.get("/teach/courses/{course_id}/gradebook")
def gradebook(course_id: int, db: Session = Depends(get_db), user: User = Depends(staff_required)):
    course = CoursesService.get_course(db, course_id)
    CoursesService.assert_can_manage(course, user)
    return AssessmentService.gradebook(db, course_id)


# ============ student ============

@router.get("/lessons/{lesson_id}/quiz")
def lesson_quiz_for_student(lesson_id: int, db: Session = Depends(get_db), user: User = Depends(any_user)):
    """Resolve the quiz attached to a lesson (student-safe payload)."""
    from app.modules.enrollments.models import Enrollment
    from app.modules.assessments.models import Quiz
    lesson = db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(404, "Lesson not found")
    course = CoursesService.get_course(db, lesson.course_id)
    if user.role == "student":
        enrolled = db.query(Enrollment).filter_by(course_id=course.id, user_id=user.id).first()
        if not enrolled:
            raise HTTPException(403, "Enroll in the course to take this quiz")
    quiz = db.query(Quiz).filter(Quiz.lesson_id == lesson_id).first()
    if not quiz:
        raise HTTPException(404, "No quiz attached to this lesson")
    return AssessmentService.quiz_public_payload(db, quiz, user.id)


@router.get("/quizzes/{quiz_id}")
def take_quiz(quiz_id: int, db: Session = Depends(get_db), user: User = Depends(any_user)):
    """Student view of a quiz (no correct answers). Must be enrolled in the parent course."""
    from app.modules.enrollments.models import Enrollment
    quiz = AssessmentService.get_quiz(db, quiz_id)
    lesson = db.get(Lesson, quiz.lesson_id)
    course = CoursesService.get_course(db, lesson.course_id)
    if user.role == "student":
        enrolled = db.query(Enrollment).filter_by(course_id=course.id, user_id=user.id).first()
        if not enrolled:
            raise HTTPException(403, "Enroll in the course to take this quiz")
    return AssessmentService.quiz_public_payload(db, quiz, user.id)


@router.post("/quizzes/{quiz_id}/attempts")
def submit_quiz(quiz_id: int, body: dict, db: Session = Depends(get_db), user: User = Depends(any_user)):
    from app.modules.enrollments.models import Enrollment
    quiz = AssessmentService.get_quiz(db, quiz_id)
    lesson = db.get(Lesson, quiz.lesson_id)
    course = CoursesService.get_course(db, lesson.course_id)
    if user.role == "student":
        enrolled = db.query(Enrollment).filter_by(course_id=course.id, user_id=user.id).first()
        if not enrolled:
            raise HTTPException(403, "Enroll in the course to take this quiz")
    result = AssessmentService.submit_attempt(db, quiz, user.id, body.get("answers") or {})
    if result["passed"] and user.role == "student":
        from app.modules.notifications.service import notify
        notify(db, user.id, "grade", "Quiz passed ✅",
               f"You scored {result['score']}% on “{quiz.title}”. Nice work!",
               f"/learn/{course.slug}")
    return result


@router.get("/quizzes/{quiz_id}/my-attempts")
def my_quiz_attempts(quiz_id: int, db: Session = Depends(get_db), user: User = Depends(any_user)):
    from app.modules.assessments.models import QuizAttempt
    attempts = (
        db.query(QuizAttempt).filter(QuizAttempt.quiz_id == quiz_id, QuizAttempt.user_id == user.id)
        .order_by(QuizAttempt.submitted_at.desc()).all()
    )
    return [{"id": a.id, "score": a.score, "passed": a.passed, "answers": a.answers,
             "submitted_at": a.submitted_at.isoformat()} for a in attempts]


@router.post("/assignments/{assignment_id}/submit", status_code=201)
def submit_assignment(assignment_id: int, body: dict, db: Session = Depends(get_db), user: User = Depends(any_user)):
    from app.modules.enrollments.models import Enrollment
    a = db.get(Assignment, assignment_id)
    if not a:
        raise HTTPException(404, "Assignment not found")
    if user.role == "student":
        enrolled = db.query(Enrollment).filter_by(course_id=a.course_id, user_id=user.id).first()
        if not enrolled:
            raise HTTPException(403, "Enroll in the course to submit assignments")
    sub = AssessmentService.submit_assignment(db, a, user.id, body.get("text_response"), body.get("file_url"))
    return {"id": sub.id, "status": sub.status, "message": "Submitted successfully"}


@router.get("/assignments/{assignment_id}/my-submission")
def my_submission(assignment_id: int, db: Session = Depends(get_db), user: User = Depends(any_user)):
    sub = (
        db.query(Submission).filter(Submission.assignment_id == assignment_id, Submission.user_id == user.id).first()
    )
    if not sub:
        return None
    return {"id": sub.id, "text_response": sub.text_response, "file_url": sub.file_url,
            "submitted_at": sub.submitted_at.isoformat(), "status": sub.status,
            "grade": sub.grade, "feedback": sub.feedback}
