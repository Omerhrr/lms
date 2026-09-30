from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.modules.assessments.models import (
    Quiz, Question, QuestionType, QuizAttempt, Assignment, Submission,
)


class AssessmentService:

    # ---------- quizzes (instructor) ----------

    @staticmethod
    def upsert_quiz(db: Session, lesson_id: int, data: dict) -> Quiz:
        quiz = db.query(Quiz).filter(Quiz.lesson_id == lesson_id).first()
        if quiz:
            quiz.title = data.get("title") or quiz.title
            quiz.description = data.get("description")
            quiz.time_limit_minutes = data.get("time_limit_minutes")
            quiz.passing_score = data.get("passing_score", quiz.passing_score)
            quiz.max_attempts = data.get("max_attempts", quiz.max_attempts)
        else:
            quiz = Quiz(
                lesson_id=lesson_id,
                title=data.get("title") or "Quiz",
                description=data.get("description"),
                time_limit_minutes=data.get("time_limit_minutes"),
                passing_score=data.get("passing_score", 60),
                max_attempts=data.get("max_attempts", 0),
            )
            db.add(quiz)
        db.commit()
        db.refresh(quiz)
        return quiz

    @staticmethod
    def get_quiz(db: Session, quiz_id: int) -> Quiz:
        quiz = db.get(Quiz, quiz_id)
        if not quiz:
            raise HTTPException(404, "Quiz not found")
        return quiz

    @staticmethod
    def add_question(db: Session, quiz: Quiz, data: dict) -> Question:
        qtype = data.get("type", "single_choice")
        if qtype not in QuestionType.__members__:
            raise HTTPException(400, f"Unknown question type '{qtype}'")
        if qtype in ("single_choice", "multi_choice", "true_false") and not data.get("options"):
            raise HTTPException(400, "Options are required for choice questions")
        correct = data.get("correct")
        if not correct:
            raise HTTPException(400, "Mark at least one correct answer")
        pos = db.query(func.coalesce(func.max(Question.position), -1)).filter(Question.quiz_id == quiz.id).scalar() + 1
        q = Question(
            quiz_id=quiz.id,
            type=QuestionType(qtype),
            text=data["text"],
            options=data.get("options") or [],
            correct=correct,
            points=data.get("points", 1.0),
            explanation=data.get("explanation"),
            position=pos,
        )
        db.add(q)
        db.commit()
        db.refresh(q)
        return q

    @staticmethod
    def update_question(db: Session, question: Question, data: dict) -> Question:
        if "type" in data and data["type"]:
            question.type = QuestionType(data["type"])
        for f in ("text", "options", "correct", "points", "explanation"):
            if f in data and data[f] is not None:
                setattr(question, f, data[f])
        db.commit()
        return question

    @staticmethod
    def delete_question(db: Session, question: Question) -> None:
        db.delete(question)
        db.commit()

    # ---------- quiz taking (student) ----------

    @staticmethod
    def quiz_public_payload(db: Session, quiz: Quiz, user_id: int) -> dict:
        """Questions WITHOUT correct answers + attempt state for the taker."""
        attempts = (
            db.query(QuizAttempt).filter(QuizAttempt.quiz_id == quiz.id, QuizAttempt.user_id == user_id)
            .order_by(QuizAttempt.submitted_at.desc()).all()
        )
        best = max((a.score for a in attempts), default=None)
        passed_before = any(a.passed for a in attempts)
        blocked = passed_before or (quiz.max_attempts and len(attempts) >= quiz.max_attempts)
        return {
            "id": quiz.id,
            "title": quiz.title,
            "description": quiz.description,
            "time_limit_minutes": quiz.time_limit_minutes,
            "passing_score": quiz.passing_score,
            "max_attempts": quiz.max_attempts,
            "questions": [
                {"id": q.id, "type": q.type.value, "text": q.text, "options": q.options, "points": q.points}
                for q in sorted(quiz.questions, key=lambda x: x.position)
            ],
            "attempt_count": len(attempts),
            "best_score": best,
            "passed": passed_before,
            "can_take": not blocked,
        }

    @staticmethod
    def grade_answer(question: Question, answer) -> bool:
        if answer is None:
            return False
        if question.type in (QuestionType.single_choice, QuestionType.true_false):
            try:
                return int(answer[0] if isinstance(answer, list) else answer) == int(question.correct[0])
            except (ValueError, TypeError, IndexError):
                return False
        if question.type == QuestionType.multi_choice:
            try:
                given = sorted(int(a) for a in (answer if isinstance(answer, list) else [answer]))
            except (ValueError, TypeError):
                return False
            expected = sorted(int(c) for c in question.correct)
            return given == expected
        # short_answer: case-insensitive match against any accepted answer
        given = (answer[0] if isinstance(answer, list) else str(answer)).strip().lower()
        return any(given == str(c).strip().lower() for c in question.correct)

    @staticmethod
    def submit_attempt(db: Session, quiz: Quiz, user_id: int, answers: dict) -> dict:
        attempts = db.query(QuizAttempt).filter(QuizAttempt.quiz_id == quiz.id, QuizAttempt.user_id == user_id).all()
        if any(a.passed for a in attempts):
            raise HTTPException(400, "You already passed this quiz")
        if quiz.max_attempts and len(attempts) >= quiz.max_attempts:
            raise HTTPException(400, "Maximum number of attempts reached")

        total_points = sum(q.points for q in quiz.questions) or 1
        earned = 0.0
        detail = {}
        for q in quiz.questions:
            raw = answers.get(str(q.id), answers.get(q.id))
            ok = AssessmentService.grade_answer(q, raw)
            if ok:
                earned += q.points
            detail[str(q.id)] = {"correct": ok, "correct_answers": q.correct, "explanation": q.explanation}

        score = round(earned / total_points * 100, 1)
        passed = score >= quiz.passing_score
        attempt = QuizAttempt(quiz_id=quiz.id, user_id=user_id, answers=answers, score=score, passed=passed)
        db.add(attempt)
        db.commit()
        db.refresh(attempt)

        # auto-complete the quiz lesson on pass (modular event)
        if passed:
            from app.modules.enrollments.models import Enrollment, LessonProgress
            from app.modules.enrollments.service import EnrollmentService
            from app.modules.courses.models import Lesson

            lesson = db.get(Lesson, quiz.lesson_id)
            if lesson:
                course = lesson.section.course if lesson.section else None
                if course:
                    enrollment = db.query(Enrollment).filter_by(course_id=course.id, user_id=user_id).first()
                    if enrollment:
                        already = db.query(LessonProgress).filter_by(
                            enrollment_id=enrollment.id, lesson_id=lesson.id).first()
                        if not already:
                            db.add(LessonProgress(enrollment_id=enrollment.id, lesson_id=lesson.id))
                            EnrollmentService.recompute_progress(db, enrollment)
                            db.commit()

        return {
            "attempt_id": attempt.id,
            "score": score,
            "passed": passed,
            "passing_score": quiz.passing_score,
            "detail": detail,
        }

    # ---------- assignments ----------

    @staticmethod
    def add_assignment(db: Session, course_id: int, data: dict, position: int) -> Assignment:
        a = Assignment(
            course_id=course_id,
            title=data["title"],
            instructions=data.get("instructions", ""),
            due_date=data.get("due_date"),
            max_points=data.get("max_points", 100.0),
            allow_file=data.get("allow_file", True),
            position=position,
        )
        db.add(a)
        db.commit()
        db.refresh(a)
        return a

    @staticmethod
    def submit_assignment(db: Session, assignment: Assignment, user_id: int, text_response: str | None, file_url: str | None) -> Submission:
        if not text_response and not file_url:
            raise HTTPException(400, "Provide a written response or attach a file")
        if file_url and not assignment.allow_file:
            raise HTTPException(400, "This assignment does not accept file uploads")
        sub = db.query(Submission).filter(
            Submission.assignment_id == assignment.id, Submission.user_id == user_id).first()
        if sub:
            if sub.status == "graded":
                raise HTTPException(400, "This assignment has already been graded and cannot be resubmitted")
            sub.text_response = text_response
            sub.file_url = file_url
            sub.submitted_at = func.now()
            sub.status = "submitted"
        else:
            sub = Submission(assignment_id=assignment.id, user_id=user_id,
                             text_response=text_response, file_url=file_url)
            db.add(sub)
        db.commit()
        db.refresh(sub)

        from app.modules.notifications.service import notify
        from app.modules.courses.models import Course
        course = db.get(Course, assignment.course_id)
        if course:
            notify(db, course.instructor_id, "submission", "New submission to grade",
                   f"“{assignment.title}” received a new submission.",
                   f"/teach/courses/{course.id}/gradebook")
        return sub

    @staticmethod
    def grade_submission(db: Session, submission: Submission, grade: float, feedback: str | None, grader_id: int) -> Submission:
        if grade < 0 or grade > 1_000_000:
            raise HTTPException(400, "Invalid grade")
        submission.grade = grade
        submission.feedback = feedback
        submission.graded_by = grader_id
        submission.graded_at = func.now()
        submission.status = "graded"
        db.commit()
        db.refresh(submission)

        from app.modules.notifications.service import notify
        from app.modules.courses.models import Course
        assignment = db.get(Assignment, submission.assignment_id)
        course = db.get(Course, assignment.course_id) if assignment else None
        notify(db, submission.user_id, "grade", "Assignment graded",
               f"“{assignment.title}” was graded: {grade}/{assignment.max_points:.0f}.",
               "/dashboard" if not course else f"/learn/{course.slug}")
        return submission

    # ---------- gradebook ----------

    @staticmethod
    def gradebook(db: Session, course_id: int) -> dict:
        from app.modules.enrollments.models import Enrollment
        from app.modules.courses.models import Lesson, LessonType

        rows = []
        assignments = sorted(
            db.query(Assignment).filter(Assignment.course_id == course_id).all(), key=lambda a: a.position)
        quiz_lessons = (
            db.query(Lesson).filter(Lesson.course_id == course_id, Lesson.type == LessonType.quiz).all()
        )
        quizzes = {l.id: db.query(Quiz).filter(Quiz.lesson_id == l.id).first() for l in quiz_lessons}
        quiz_meta = [{"lesson_id": l.id, "lesson_title": l.title, "quiz_id": quizzes[l.id].id}
                     for l in quiz_lessons if quizzes[l.id]]

        enrollments = (
            db.query(Enrollment).options(joinedload(Enrollment.user))
            .filter(Enrollment.course_id == course_id).order_by(Enrollment.enrolled_at).all()
        )
        for e in enrollments:
            row = {
                "user": {"id": e.user.id, "full_name": e.user.full_name, "email": e.user.email},
                "progress": e.progress,
                "quizzes": [],
                "assignments": [],
            }
            for meta in quiz_meta:
                attempts = (
                    db.query(QuizAttempt).filter(
                        QuizAttempt.quiz_id == meta["quiz_id"], QuizAttempt.user_id == e.user.id).all()
                )
                best = max((a.score for a in attempts), default=None)
                row["quizzes"].append({**meta, "best_score": best,
                                       "passed": any(a.passed for a in attempts),
                                       "attempts": len(attempts)})
            for a in assignments:
                sub = db.query(Submission).filter(
                    Submission.assignment_id == a.id, Submission.user_id == e.user.id).first()
                row["assignments"].append({
                    "assignment_id": a.id, "title": a.title, "max_points": a.max_points,
                    "status": sub.status if sub else None,
                    "grade": sub.grade if sub else None,
                    "submitted_at": sub.submitted_at.isoformat() if sub else None,
                    "submission_id": sub.id if sub else None,
                })
            rows.append(row)

        return {"students": rows,
                "quiz_columns": quiz_meta,
                "assignment_columns": [{"id": a.id, "title": a.title, "max_points": a.max_points} for a in assignments]}
