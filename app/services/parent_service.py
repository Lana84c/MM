from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.coach_message import CoachMessage
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.progress import Progress
from app.models.simulation_session import SimulationSession
from app.models.user import User


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

    return {
        "learner": learner,
        "enrolled_courses": enrolled_courses,
        "completed_lessons": completed_lessons,
        "practice_sessions": practice_sessions,
        "recent_questions": recent_questions,
    }


def get_all_learners(db: Session) -> list[User]:
    return (
        db.query(User)
        .order_by(User.full_name.asc())
        .all()
    )