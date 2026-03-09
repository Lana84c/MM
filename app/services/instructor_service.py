from sqlalchemy.orm import Session
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.user import User


def is_instructor(user: User) -> bool:
    return user.role in ["admin", "org_admin", "instructor"]


def create_course(
    db: Session,
    organization_id: int,
    title: str,
    slug: str,
    description: str,
    difficulty: str,
    published: bool,
) -> Course:

    course = Course(
        organization_id=organization_id,
        title=title,
        slug=slug,
        description=description,
        difficulty=difficulty,
        published=published,
    )

    db.add(course)
    db.commit()
    db.refresh(course)

    return course


def create_lesson(
    db: Session,
    course_id: int,
    title: str,
    slug: str,
    content: str,
    sort_order: int,
) -> Lesson:

    lesson = Lesson(
        course_id=course_id,
        title=title,
        slug=slug,
        content=content,
        sort_order=sort_order,
    )

    db.add(lesson)
    db.commit()
    db.refresh(lesson)

    return lesson


def get_org_courses(db: Session, organization_id: int):
    return (
        db.query(Course)
        .filter(Course.organization_id == organization_id)
        .order_by(Course.title)
        .all()
    )