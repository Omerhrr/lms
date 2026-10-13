from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.modules.assessments.models import (
    Quiz, Question, QuestionType, QuizAttempt, Assignment, Submission,
)


class AssessmentService:

    # ---------- quizzes (instructor) ----------

    @staticmethod
    def _quiz_settings(data: dict) -> dict:
        out = {}
        try:
            if data.get("passing_score") is not None:
                out["passing_score"] = float(data["passing_score"])
                if not 0 <= out["passing_score"] <= 100:
                    raise ValueError
            if data.get("max_attempts") is not None:
                out["max_attempts"] = int(data["max_attempts"])
                if out["max_attempts"] < 0:
                    raise ValueError
            if data.get("time_limit_minutes") not in (None, "", 0):
                out["time_limit_minutes"] = int(data["time_limit_minutes"])
                if out["time_limit_minutes"] <= 0:
                    raise ValueError
        except (TypeError, ValueError):
            raise HTTPException(400, "Invalid quiz settings (passing score 0-100, attempts >= 0, time limit > 0)")
        return out

    @staticmethod
    def upsert_quiz(db: Session, lesson_id: int, data: dict) -> Quiz:
        clean = AssessmentService._quiz_settings(data)
        data = {**data, **clean}
        if data.get("time_limit_minutes") in ("", 0):
            data["time_limit_minutes"] = None
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
    def _validate_question(qtype: str, text, options, correct) -> None:
        if not isinstance(text, str) or not text.strip():
            raise HTTPException(400, "Question text is required")
        if not isinstance(correct, list) or not correct:
            raise HTTPException(400, "Mark at least one correct answer")
        if qtype in ("single_choice", "multi_choice", "true_false"):
            if not isinstance(options, list) or len(options) < 2:
                raise HTTPException(400, "Choice questions need at least two options")
            try:
                idx = [int(c) for c in correct]
            except (TypeError, ValueError):
                raise HTTPException(400, "Correct answers must be option indexes")
            if any(i < 0 or i >= len(options) for i in idx):
                raise HTTPException(400, "A correct answer points at an option that doesn't exist")
            if qtype != "multi_choice" and len(idx) != 1:
                raise HTTPException(400, "Single-choice questions have exactly one correct answer")

    @staticmethod
    def add_question(db: Session, quiz: Quiz, data: dict) -> Question:
        qtype = data.get("type", "single_choice")
        if qtype not in QuestionType.__members__:
            raise HTTPException(400, f"Unknown question type '{qtype}'")
        correct = data.get("correct")
        AssessmentService._validate_question(qtype, data.get("text"), data.get("options"), correct)
        pos = db.query(func.coalesce(func.max(Question.position), -1)).filter(Question.quiz_id == quiz.id).scalar() + 1
        q = Question(
            quiz_id=quiz.id,
            type=QuestionType(qtype),
            text=data["text"],
            options=data.get("options") or [],
            correct=correct,
            points=AssessmentService._points(data.get("points", 1.0)),
            explanation=data.get("explanation"),
            position=pos,
        )
        db.add(q)
        db.commit()
        db.refresh(q)
        return q

    @staticmethod
    def _points(value) -> float:
        try:
            v = float(value)
        except (TypeError, ValueError):
            raise HTTPException(400, "Points must be a number")
        if not 0 < v <= 1000:
            raise HTTPException(400, "Points must be between 0 and 1000")
        return v

    @staticmethod
    def update_question(db: Session, question: Question, data: dict) -> Question:
        qtype = data.get("type") or question.type.value
        if qtype not in QuestionType.__members__:
            raise HTTPException(400, f"Unknown question type '{qtype}'")
        merged = {f: data[f] if data.get(f) is not None else getattr(question, f)
                  for f in ("text", "options", "correct")}
        AssessmentService._validate_question(qtype, merged["text"], merged["options"], merged["correct"])
        question.type = QuestionType(qtype)
        for f in ("text", "options", "correct", "explanation"):
            if f in data and data[f] is not None:
                setattr(question, f, data[f])
        if data.get("points") is not None:
            question.points = AssessmentService._points(data["points"])
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
        session_token = None
        if quiz.time_limit_minutes and not blocked:
            from app.core.security import create_quiz_session_token
            session_token = create_quiz_session_token(quiz.id, user_id)
        return {
            "session_token": session_token,
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
    def _check_time_limit(quiz: Quiz, user_id: int, session_token: str | None) -> None:
        if not quiz.time_limit_minutes:
            return
        from app.core.security import decode_token
        try:
            payload = decode_token(session_token or "")
        except Exception:
            raise HTTPException(400, "This quiz is timed - reload it to start a new attempt")
        if payload.get("type") != "quiz" or payload.get("quiz") != quiz.id or payload.get("sub") != str(user_id):
            raise HTTPException(400, "This quiz is timed - reload it to start a new attempt")
        from app.shared.utils import utcnow
        started = datetime.fromtimestamp(payload["iat"], timezone.utc).replace(tzinfo=None)
        grace = timedelta(seconds=30)  # network latency allowance
        if utcnow() - started > timedelta(minutes=quiz.time_limit_minutes) + grace:
            raise HTTPException(400, "Time is up for this attempt")

    @staticmethod
    def submit_attempt(db: Session, quiz: Quiz, user_id: int, answers: dict, session_token: str | None = None) -> dict:
        attempts = db.query(QuizAttempt).filter(QuizAttempt.quiz_id == quiz.id, QuizAttempt.user_id == user_id).all()
        if any(a.passed for a in attempts):
            raise HTTPException(400, "You already passed this quiz")
        if quiz.max_attempts and len(attempts) >= quiz.max_attempts:
            raise HTTPException(400, "Maximum number of attempts reached")
        AssessmentService._check_time_limit(quiz, user_id, session_token)
        answers = {str(k): v for k, v in list(answers.items())[:500]}

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
        attempts_left = (quiz.max_attempts - len(attempts) - 1) if quiz.max_attempts else None
        # Only reveal the answer key once the learner can't use it to retake the quiz.
        reveal = passed or attempts_left == 0
        if not reveal:
            for d in detail.values():
                d.pop("correct_answers", None)
                d.pop("explanation", None)
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
                            db.commit()
                        # shared completion path: issues certificate when this
                        # quiz was the last remaining lesson
                        EnrollmentService.finalize_completion(db, enrollment)

        return {
            "attempt_id": attempt.id,
            "score": score,
            "passed": passed,
            "passing_score": quiz.passing_score,
            "answers_revealed": reveal,
            "attempts_left": attempts_left,
            "detail": detail,
        }

    # ---------- assignments ----------

    @staticmethod
    def apply_assignment_fields(a: Assignment, data: dict) -> None:
        """Validate and copy the editable assignment fields (and nothing else)."""
        if data.get("title") is not None:
            title = str(data["title"]).strip()
            if not title or len(title) > 255:
                raise HTTPException(400, "Assignment title must be 1-255 characters")
            a.title = title
        if data.get("instructions") is not None:
            a.instructions = str(data["instructions"])[:50_000]
        if data.get("max_points") is not None:
            try:
                mp = float(data["max_points"])
            except (TypeError, ValueError):
                raise HTTPException(400, "max_points must be a number")
            if not 0 < mp <= 10_000:
                raise HTTPException(400, "max_points must be between 0 and 10000")
            a.max_points = mp
        if data.get("allow_file") is not None:
            a.allow_file = bool(data["allow_file"])
        if "due_date" in data:
            due = data["due_date"]
            if due in (None, ""):
                a.due_date = None
            else:
                try:
                    a.due_date = datetime.fromisoformat(str(due).replace("Z", "+00:00")).replace(tzinfo=None)
                except ValueError:
                    raise HTTPException(400, "due_date must be an ISO date, e.g. 2026-12-31T23:59")

    @staticmethod
    def add_assignment(db: Session, course_id: int, data: dict, position: int) -> Assignment:
        a = Assignment(course_id=course_id, title="", instructions="", max_points=100.0,
                       allow_file=True, position=position)
        AssessmentService.apply_assignment_fields(a, data)
        db.add(a)
        db.commit()
        db.refresh(a)
        return a

    @staticmethod
    def submit_assignment(db: Session, assignment: Assignment, user_id: int, text_response: str | None, file_url: str | None) -> Submission:
        from app.shared.utils import safe_url
        file_url = safe_url(file_url, "file_url")
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
        cap = db.get(Assignment, submission.assignment_id).max_points
        if grade < 0 or grade > cap:
            raise HTTPException(400, f"Grade must be between 0 and {cap:g}")
        if feedback is not None:
            feedback = str(feedback)[:20_000]
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
        from app.modules.auth.models import User as _U
        from app.shared import emails
        student = db.get(_U, submission.user_id)
        if student and assignment and course:
            emails.assignment_graded(student.email, student.full_name, assignment.title,
                                     f"{grade:g}/{assignment.max_points:g}", course.slug)
        notify(db, submission.user_id, "grade", "Assignment graded",
               f"“{assignment.title}” was graded: {grade}/{assignment.max_points:.0f}.",
               "/dashboard" if not course else f"/learn/{course.slug}")
        return submission

    # ---------- gradebook ----------

    @staticmethod
    def gradebook(db: Session, course_id: int) -> dict:
        """Batched: a fixed number of queries regardless of class size."""
        from collections import defaultdict
        from app.modules.enrollments.models import Enrollment
        from app.modules.courses.models import Lesson, LessonType

        assignments = sorted(
            db.query(Assignment).filter(Assignment.course_id == course_id).all(), key=lambda a: a.position)
        quiz_rows = (
            db.query(Lesson, Quiz).join(Quiz, Quiz.lesson_id == Lesson.id)
            .filter(Lesson.course_id == course_id, Lesson.type == LessonType.quiz)
            .order_by(Lesson.position).all()
        )
        quiz_meta = [{"lesson_id": l.id, "lesson_title": l.title, "quiz_id": q.id} for l, q in quiz_rows]
        quiz_ids = [m["quiz_id"] for m in quiz_meta]

        enrollments = [
            e for e in db.query(Enrollment).options(joinedload(Enrollment.user))
            .filter(Enrollment.course_id == course_id).order_by(Enrollment.enrolled_at).all() if e.user
        ]
        attempts = defaultdict(list)   # (quiz_id, user_id) -> [attempt]
        if quiz_ids:
            for a in db.query(QuizAttempt).filter(QuizAttempt.quiz_id.in_(quiz_ids)).all():
                attempts[(a.quiz_id, a.user_id)].append(a)
        subs = {}
        if assignments:
            for sub in db.query(Submission).filter(Submission.assignment_id.in_([a.id for a in assignments])).all():
                subs[(sub.assignment_id, sub.user_id)] = sub

        rows = []
        for e in enrollments:
            uid = e.user.id
            row = {
                "user": {"id": uid, "full_name": e.user.full_name, "email": e.user.email},
                "progress": e.progress, "quizzes": [], "assignments": [],
            }
            for meta in quiz_meta:
                ats = attempts.get((meta["quiz_id"], uid), [])
                row["quizzes"].append({**meta, "best_score": max((a.score for a in ats), default=None),
                                       "passed": any(a.passed for a in ats), "attempts": len(ats)})
            for a in assignments:
                sub = subs.get((a.id, uid))
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
