from sqlalchemy.orm import Session

from app.models.scenario import Scenario
from app.models.simulation_message import SimulationMessage
from app.models.simulation_session import SimulationSession
from app.models.user import User


def get_active_scenarios_for_lesson(db: Session, lesson_id: int) -> list[Scenario]:
    return (
        db.query(Scenario)
        .filter(
            Scenario.lesson_id == lesson_id,
            Scenario.is_active.is_(True),
        )
        .order_by(Scenario.title.asc())
        .all()
    )


def get_scenario_by_id(db: Session, scenario_id: int) -> Scenario | None:
    return (
        db.query(Scenario)
        .filter(
            Scenario.id == scenario_id,
            Scenario.is_active.is_(True),
        )
        .first()
    )


def create_simulation_session(
    db: Session,
    user: User,
    lesson_id: int,
    scenario_id: int,
) -> SimulationSession:
    session = SimulationSession(
        user_id=user.id,
        lesson_id=lesson_id,
        scenario_id=scenario_id,
        mode="roleplay",
        status="active",
        turn_count=0,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_simulation_session(
    db: Session,
    session_id: int,
    user_id: int,
) -> SimulationSession | None:
    return (
        db.query(SimulationSession)
        .filter(
            SimulationSession.id == session_id,
            SimulationSession.user_id == user_id,
        )
        .first()
    )


def add_simulation_message(
    db: Session,
    session_id: int,
    role: str,
    content: str,
) -> SimulationMessage:
    message = SimulationMessage(
        session_id=session_id,
        role=role,
        content=content,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_simulation_messages(
    db: Session,
    session_id: int,
) -> list[SimulationMessage]:
    return (
        db.query(SimulationMessage)
        .filter(SimulationMessage.session_id == session_id)
        .order_by(SimulationMessage.created_at.asc())
        .all()
    )


def build_simulation_history(
    messages: list[SimulationMessage],
) -> list[dict[str, str]]:
    return [
        {
            "role": message.role,
            "content": message.content,
        }
        for message in messages
    ]