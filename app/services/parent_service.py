from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.coach_message import CoachMessage
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.lesson import Lesson
from app.models.progress import Progress
from app.models.simulation_session import SimulationSession
from app.models.user import User


def get_all_learners(db: Session) -> list[User]:
    return db.query(User).order_by(User.full_name.asc()).all()


def get_next_lesson_recommendation(db: Session, learner_id: int) -> dict | None:
    enrolled_courses = (
        db.query(Course)
        .join(Enrollment, Enrollment.course_id == Course.id)
        .filter(Enrollment.user_id == learner_id)
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
                    Progress.user_id == learner_id,
                    Progress.lesson_id == lesson.id,
                    Progress.completed.is_(True),
                )
                .first()
            )
            if not completed:
                return {
                    "course_title": course.title,
                    "lesson_title": lesson.title,
                    "lesson_slug": lesson.slug,
                }

    return None


def get_low_engagement_flag(
    completed_lessons: int,
    practice_sessions: int,
    recent_question_count: int,
) -> str | None:
    activity_score = completed_lessons + practice_sessions + recent_question_count

    if activity_score == 0:
        return "No activity recorded yet."
    if activity_score <= 2:
        return "Low recent engagement."
    return None


def get_parent_summary_text(
    learner_name: str,
    completed_lessons: int,
    practice_sessions: int,
    enrolled_course_count: int,
    low_engagement_flag: str | None,
    recommendation: dict | None,
) -> str:
    summary = (
        f"{learner_name} is enrolled in {enrolled_course_count} course(s), "
        f"has completed {completed_lessons} lesson(s), and has used practice mode "
        f"{practice_sessions} time(s)."
    )

    if low_engagement_flag:
        summary += f" Attention: {low_engagement_flag}"

    if recommendation:
        summary += (
            f" Recommended next step: {recommendation['lesson_title']} "
            f"in {recommendation['course_title']}."
        )

    return summary


def get_learner_summary(db: Session, learner_id: int) -> dict:
    learner = db.query(User).filter(User.id == learner_id).first()
    if not learner:
        return {}

    enrolled_courses = (
        db.query(Course)
        .join(Enrollment, Enrollment.course_id == Course.id)
        .filter(Enrollment.user_id == learner_id)
        .order_by(Course.title.asc())
        .all()
    )

    completed_lessons = (
        db.query(func.count(Progress.id))
        .filter(
            Progress.user_id == learner_id,
            Progress.completed.is_(True),
        )
        .scalar()
        or 0
    )

    practice_sessions = (
        db.query(func.count(SimulationSession.id))
        .filter(SimulationSession.user_id == learner_id)
        .scalar()
        or 0
    )

    recent_questions = (
        db.query(CoachMessage)
        .filter(
            CoachMessage.user_id == learner_id,
            CoachMessage.role == "user",
        )
        .order_by(CoachMessage.created_at.desc())
        .limit(5)
        .all()
    )

    recommendation = get_next_lesson_recommendation(db, learner_id)
    low_engagement_flag = get_low_engagement_flag(
        completed_lessons=completed_lessons,
        practice_sessions=practice_sessions,
        recent_question_count=len(recent_questions),
    )

    parent_summary = get_parent_summary_text(
        learner_name=learner.full_name,
        completed_lessons=completed_lessons,
        practice_sessions=practice_sessions,
        enrolled_course_count=len(enrolled_courses),
        low_engagement_flag=low_engagement_flag,
        recommendation=recommendation,
    )

    return {
        "learner": learner,
        "enrolled_courses": enrolled_courses,
        "completed_lessons": completed_lessons,
        "practice_sessions": practice_sessions,
        "recent_questions": recent_questions,
        "recommendation": recommendation,
        "low_engagement_flag": low_engagement_flag,
        "parent_summary": parent_summary,
    }