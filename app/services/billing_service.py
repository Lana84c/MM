from sqlalchemy.orm import Session

from app.models.coach_message import CoachMessage
from app.models.organization import Organization
from app.models.plan import Plan
from app.models.simulation_session import SimulationSession
from app.models.subscription import Subscription
from app.models.user import User


def get_active_plans(db: Session) -> list[Plan]:
    return (
        db.query(Plan)
        .filter(Plan.is_active.is_(True))
        .order_by(Plan.price_cents.asc())
        .all()
    )


def get_plan_by_slug(db: Session, slug: str) -> Plan | None:
    return db.query(Plan).filter(Plan.slug == slug, Plan.is_active.is_(True)).first()


def get_user_subscription(db: Session, user: User) -> Subscription | None:
    return (
        db.query(Subscription)
        .filter(
            Subscription.user_id == user.id,
            Subscription.status == "active",
        )
        .first()
    )


def get_org_subscription(db: Session, organization: Organization) -> Subscription | None:
    return (
        db.query(Subscription)
        .filter(
            Subscription.organization_id == organization.id,
            Subscription.status == "active",
        )
        .first()
    )


def get_user_plan(db: Session, user: User) -> Plan | None:
    subscription = get_user_subscription(db, user)
    if subscription:
        return subscription.plan

    return get_plan_by_slug(db, "free")


def has_feature_access(plan: Plan | None, feature: str) -> bool:
    if not plan:
        return False

    feature_map = {
        "org_dashboard": plan.includes_org_dashboard,
        "advanced_analytics": plan.includes_advanced_analytics,
        "roleplay": plan.includes_roleplay,
    }

    return feature_map.get(feature, False)


def get_user_ai_message_count(db: Session, user: User) -> int:
    return (
        db.query(CoachMessage)
        .filter(
            CoachMessage.user_id == user.id,
            CoachMessage.role == "user",
        )
        .count()
    )


def get_user_practice_session_count(db: Session, user: User) -> int:
    return (
        db.query(SimulationSession)
        .filter(SimulationSession.user_id == user.id)
        .count()
    )


def can_use_ai_coach(db: Session, user: User, plan: Plan | None) -> bool:
    if not plan:
        return False

    current_count = get_user_ai_message_count(db, user)
    return current_count < plan.max_ai_messages_per_month


def can_use_roleplay(db: Session, user: User, plan: Plan | None) -> bool:
    if not plan:
        return False

    if not plan.includes_roleplay:
        return False

    current_count = get_user_practice_session_count(db, user)
    return current_count < plan.max_practice_sessions_per_month


def create_user_subscription(
    db: Session,
    user_id: int,
    plan_id: int,
    provider: str = "manual",
) -> Subscription:
    subscription = Subscription(
        user_id=user_id,
        plan_id=plan_id,
        status="active",
        provider=provider,
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return subscription