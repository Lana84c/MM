from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.lesson import Lesson
from app.models.progress import Progress
from app.models.user import User


def get_published_courses(db: Session) -> list[Course]:
    return (
        db.query(Course)
        .filter(Course.published.is_(True))
        .order_by(Course.title.asc())
        .all()
    )


def get_course_by_id(db: Session, course_id: int) -> Course | None:
    return (
        db.query(Course)
        .options(joinedload(Course.lessons))
        .filter(Course.id == course_id, Course.published.is_(True))
        .first()
    )


def get_course_by_slug(db: Session, slug: str) -> Course | None:
    return (
        db.query(Course)
        .options(joinedload(Course.lessons))
        .filter(Course.slug == slug, Course.published.is_(True))
        .first()
    )


def get_lesson_by_slug(db: Session, slug: str) -> Lesson | None:
    return (
        db.query(Lesson)
        .options(joinedload(Lesson.course))
        .filter(Lesson.slug == slug)
        .first()
    )


def get_user_enrolled_courses(db: Session, user: User) -> list[Course]:
    return (
        db.query(Course)
        .join(Enrollment, Enrollment.course_id == Course.id)
        .options(joinedload(Course.lessons))
        .filter(Enrollment.user_id == user.id)
        .order_by(Course.title.asc())
        .all()
    )


def is_user_enrolled_in_course(db: Session, user: User, course: Course) -> bool:
    enrollment = (
        db.query(Enrollment)
        .filter(Enrollment.user_id == user.id, Enrollment.course_id == course.id)
        .first()
    )
    return enrollment is not None


def enroll_user_in_course(db: Session, user: User, course: Course) -> Enrollment:
    existing = (
        db.query(Enrollment)
        .filter(Enrollment.user_id == user.id, Enrollment.course_id == course.id)
        .first()
    )
    if existing:
        return existing

    enrollment = Enrollment(user_id=user.id, course_id=course.id)
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment


def is_lesson_complete(db: Session, user: User, lesson: Lesson) -> bool:
    progress = (
        db.query(Progress)
        .filter(Progress.user_id == user.id, Progress.lesson_id == lesson.id, Progress.completed.is_(True))
        .first()
    )
    return progress is not None


def mark_lesson_complete(db: Session, user: User, lesson: Lesson) -> Progress:
    progress = (
        db.query(Progress)
        .filter(Progress.user_id == user.id, Progress.lesson_id == lesson.id)
        .first()
    )

    if progress:
        progress.completed = True
    else:
        progress = Progress(user_id=user.id, lesson_id=lesson.id, completed=True)
        db.add(progress)

    db.commit()
    db.refresh(progress)
    return progress


def get_completed_lesson_ids_for_course(db: Session, user: User, course: Course) -> set[int]:
    rows = (
        db.query(Progress.lesson_id)
        .join(Lesson, Lesson.id == Progress.lesson_id)
        .filter(
            Progress.user_id == user.id,
            Progress.completed.is_(True),
            Lesson.course_id == course.id,
        )
        .all()
    )
    return {row[0] for row in rows}


def get_course_progress_percent(db: Session, user: User, course: Course) -> int:
    total_lessons = (
        db.query(func.count(Lesson.id))
        .filter(Lesson.course_id == course.id)
        .scalar()
        or 0
    )

    if total_lessons == 0:
        return 0

    completed_lessons = (
        db.query(func.count(Progress.id))
        .join(Lesson, Lesson.id == Progress.lesson_id)
        .filter(
            Progress.user_id == user.id,
            Progress.completed.is_(True),
            Lesson.course_id == course.id,
        )
        .scalar()
        or 0
    )

    return int((completed_lessons / total_lessons) * 100)