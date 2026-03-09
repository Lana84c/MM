from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.user import User
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.enrollment import Enrollment
from app.models.progress import Progress
from app.models.simulation_session import SimulationSession
from app.models.scenario import Scenario
from app.models.coach_message import CoachMessage


def get_platform_stats(db: Session):
    total_users = db.query(func.count(User.id)).scalar()
    total_courses = db.query(func.count(Course.id)).scalar()
    total_lessons = db.query(func.count(Lesson.id)).scalar()
    total_enrollments = db.query(func.count(Enrollment.id)).scalar()

    completed_lessons = (
        db.query(func.count(Progress.id))
        .filter(Progress.completed == True)
        .scalar()
    )

    total_practice_sessions = db.query(func.count(SimulationSession.id)).scalar()

    return {
        "total_users": total_users or 0,
        "total_courses": total_courses or 0,
        "total_lessons": total_lessons or 0,
        "total_enrollments": total_enrollments or 0,
        "completed_lessons": completed_lessons or 0,
        "practice_sessions": total_practice_sessions or 0,
    }


def get_course_enrollment_stats(db: Session):
    results = (
        db.query(
            Course.title,
            func.count(Enrollment.id).label("enrollments"),
        )
        .outerjoin(Enrollment, Enrollment.course_id == Course.id)
        .group_by(Course.title)
        .all()
    )

    return [{"course": r.title, "enrollments": r.enrollments} for r in results]


def get_lesson_completion_stats(db: Session):
    results = (
        db.query(
            Lesson.title,
            func.count(Progress.id).label("completions"),
        )
        .outerjoin(
            Progress,
            (Progress.lesson_id == Lesson.id) & (Progress.completed == True),
        )
        .group_by(Lesson.title)
        .all()
    )

    return [{"lesson": r.title, "completions": r.completions} for r in results]


def get_top_coach_questions(db: Session, limit: int = 10):
    results = (
        db.query(CoachMessage.content, func.count(CoachMessage.id).label("count"))
        .filter(CoachMessage.role == "user")
        .group_by(CoachMessage.content)
        .order_by(func.count(CoachMessage.id).desc())
        .limit(limit)
        .all()
    )

    return [{"question": r.content, "count": r.count} for r in results]


def get_lesson_struggle_stats(db: Session):
    lesson_rows = (
        db.query(
            Lesson.id,
            Lesson.title,
            func.count(Progress.id).label("completion_count"),
        )
        .outerjoin(
            Progress,
            (Progress.lesson_id == Lesson.id) & (Progress.completed == True),
        )
        .group_by(Lesson.id, Lesson.title)
        .all()
    )

    enrollment_total = db.query(func.count(Enrollment.id)).scalar() or 0

    stats = []
    for row in lesson_rows:
        completion_rate = 0
        if enrollment_total > 0:
            completion_rate = round((row.completion_count / enrollment_total) * 100, 1)

        stats.append(
            {
                "lesson": row.title,
                "completion_count": row.completion_count,
                "completion_rate": completion_rate,
            }
        )

    stats.sort(key=lambda x: (x["completion_rate"], x["completion_count"]))
    return stats


def get_scenario_usage_stats(db: Session):
    results = (
        db.query(
            Scenario.title,
            func.count(SimulationSession.id).label("session_count"),
        )
        .outerjoin(SimulationSession, SimulationSession.scenario_id == Scenario.id)
        .group_by(Scenario.title)
        .order_by(func.count(SimulationSession.id).desc())
        .all()
    )

    return [{"scenario": r.title, "session_count": r.session_count} for r in results]