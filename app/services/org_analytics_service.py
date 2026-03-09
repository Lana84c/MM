from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.coach_message import CoachMessage
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.lesson import Lesson
from app.models.progress import Progress
from app.models.simulation_session import SimulationSession
from app.models.user import User


def get_org_platform_stats(db: Session, organization_id: int) -> dict:
    total_users = (
        db.query(func.count(User.id))
        .filter(User.organization_id == organization_id)
        .scalar()
        or 0
    )

    total_courses = (
        db.query(func.count(Course.id))
        .filter(Course.organization_id == organization_id)
        .scalar()
        or 0
    )

    total_enrollments = (
        db.query(func.count(Enrollment.id))
        .join(User, User.id == Enrollment.user_id)
        .filter(User.organization_id == organization_id)
        .scalar()
        or 0
    )

    completed_lessons = (
        db.query(func.count(Progress.id))
        .join(User, User.id == Progress.user_id)
        .filter(
            User.organization_id == organization_id,
            Progress.completed.is_(True),
        )
        .scalar()
        or 0
    )

    practice_sessions = (
        db.query(func.count(SimulationSession.id))
        .join(User, User.id == SimulationSession.user_id)
        .filter(User.organization_id == organization_id)
        .scalar()
        or 0
    )

    return {
        "total_users": total_users,
        "total_courses": total_courses,
        "total_enrollments": total_enrollments,
        "completed_lessons": completed_lessons,
        "practice_sessions": practice_sessions,
    }


def get_org_course_enrollment_stats(db: Session, organization_id: int) -> list[dict]:
    rows = (
        db.query(
            Course.title,
            func.count(Enrollment.id).label("enrollments"),
        )
        .outerjoin(Enrollment, Enrollment.course_id == Course.id)
        .filter(Course.organization_id == organization_id)
        .group_by(Course.title)
        .order_by(Course.title.asc())
        .all()
    )

    return [{"course": row.title, "enrollments": row.enrollments} for row in rows]


def get_org_top_coach_questions(db: Session, organization_id: int, limit: int = 10) -> list[dict]:
    rows = (
        db.query(
            CoachMessage.content,
            func.count(CoachMessage.id).label("count"),
        )
        .join(User, User.id == CoachMessage.user_id)
        .filter(
            User.organization_id == organization_id,
            CoachMessage.role == "user",
        )
        .group_by(CoachMessage.content)
        .order_by(func.count(CoachMessage.id).desc())
        .limit(limit)
        .all()
    )

    return [{"question": row.content, "count": row.count} for row in rows]


def get_org_lesson_completion_stats(db: Session, organization_id: int) -> list[dict]:
    rows = (
        db.query(
            Lesson.title,
            func.count(Progress.id).label("completions"),
        )
        .join(Course, Course.id == Lesson.course_id)
        .outerjoin(
            Progress,
            (Progress.lesson_id == Lesson.id) & (Progress.completed.is_(True)),
        )
        .filter(Course.organization_id == organization_id)
        .group_by(Lesson.title)
        .order_by(Lesson.title.asc())
        .all()
    )

    return [{"lesson": row.title, "completions": row.completions} for row in rows]