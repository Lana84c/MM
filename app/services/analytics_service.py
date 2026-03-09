from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.user import User
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.enrollment import Enrollment
from app.models.progress import Progress


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

    return {
        "total_users": total_users or 0,
        "total_courses": total_courses or 0,
        "total_lessons": total_lessons or 0,
        "total_enrollments": total_enrollments or 0,
        "completed_lessons": completed_lessons or 0,
    }