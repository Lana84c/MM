from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.coach_message import CoachMessage
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.lesson import Lesson
from app.models.progress import Progress
from app.models.simulation_session import SimulationSession
from app.models.user import User


def get_enrolled_courses(db: Session, user_id: int) -> list[str]:
    rows = (
        db.query(Course.title)
        .join(Enrollment, Enrollment.course_id == Course.id)
        .filter(Enrollment.user_id == user_id)
        .order_by(Course.title.asc())
        .all()
    )
    return [row[0] for row in rows]


def get_completed_lesson_count(db: Session, user_id: int) -> int:
    return (
        db.query(func.count(Progress.id))
        .filter(
            Progress.user_id == user_id,
            Progress.completed.is_(True),
        )
        .scalar()
        or 0
    )


def get_recent_ai_questions(db: Session, user_id: int, limit: int = 5) -> list[str]:
    rows = (
        db.query(CoachMessage.content)
        .filter(
            CoachMessage.user_id == user_id,
            CoachMessage.role == "user",
        )
        .order_by(CoachMessage.created_at.desc())
        .limit(limit)
        .all()
    )
    return [row[0] for row in rows]


def get_practice_session_count(db: Session, user_id: int) -> int:
    return (
        db.query(func.count(SimulationSession.id))
        .filter(SimulationSession.user_id == user_id)
        .scalar()
        or 0
    )


def get_next_recommended_lesson(db: Session, user_id: int) -> str | None:
    enrolled_courses = (
        db.query(Course)
        .join(Enrollment, Enrollment.course_id == Course.id)
        .filter(Enrollment.user_id == user_id)
        .order_by(Course.title.asc())
        .all()
    )

    for course in enrolled_courses:
        lessons = (
            db.query(Lesson)
            .filter(Lesson.course_id == course.id)
            .order_by(Lesson.sort_order.asc())
            .all()
        )

        for lesson in lessons:
            completed = (
                db.query(Progress)
                .filter(
                    Progress.user_id == user_id,
                    Progress.lesson_id == lesson.id,
                    Progress.completed.is_(True),
                )
                .first()
            )
            if not completed:
                return f"{course.title} -> {lesson.title}"

    return None


def build_learner_context_summary(db: Session, user: User) -> str:
    enrolled_courses = get_enrolled_courses(db, user.id)
    completed_lessons = get_completed_lesson_count(db, user.id)
    recent_questions = get_recent_ai_questions(db, user.id)
    practice_sessions = get_practice_session_count(db, user.id)
    next_lesson = get_next_recommended_lesson(db, user.id)

    lines = [
        f"Learner name: {user.full_name}",
        f"Role: {user.role}",
        f"Completed lessons: {completed_lessons}",
        f"Practice sessions: {practice_sessions}",
        f"Enrolled courses: {', '.join(enrolled_courses) if enrolled_courses else 'None'}",
        f"Recommended next lesson: {next_lesson if next_lesson else 'None'}",
    ]

    if recent_questions:
        lines.append("Recent learner questions:")
        for question in recent_questions:
            lines.append(f"- {question}")

    return "\n".join(lines)