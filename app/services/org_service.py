from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.organization import Organization
from app.models.user import User


def get_user_organization(db: Session, user: User) -> Organization | None:
    if not user.organization_id:
        return None

    return (
        db.query(Organization)
        .filter(Organization.id == user.organization_id)
        .first()
    )


def get_org_users(db: Session, organization_id: int) -> list[User]:
    return (
        db.query(User)
        .filter(User.organization_id == organization_id)
        .order_by(User.full_name.asc())
        .all()
    )


def get_org_courses(db: Session, organization_id: int) -> list[Course]:
    return (
        db.query(Course)
        .filter(Course.organization_id == organization_id)
        .order_by(Course.title.asc())
        .all()
    )


def user_belongs_to_org(user: User, organization_id: int) -> bool:
    return user.organization_id == organization_id


def is_org_admin(user: User) -> bool:
    return user.role in {"admin", "org_admin", "instructor"}


def create_org_user(
    db: Session,
    organization_id: int,
    full_name: str,
    email: str,
    hashed_password: str,
    role: str = "learner",
) -> User:
    user = User(
        organization_id=organization_id,
        full_name=full_name,
        email=email,
        hashed_password=hashed_password,
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def enroll_user_in_org_course(
    db: Session,
    user_id: int,
    course_id: int,
) -> Enrollment:
    existing = (
        db.query(Enrollment)
        .filter(
            Enrollment.user_id == user_id,
            Enrollment.course_id == course_id,
        )
        .first()
    )
    if existing:
        return existing

    enrollment = Enrollment(
        user_id=user_id,
        course_id=course_id,
    )
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment