from sqlalchemy.orm import Session

from app.models.course import Course
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