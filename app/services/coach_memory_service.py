from sqlalchemy.orm import Session

from app.models.coach_message import CoachMessage


def save_user_message(db: Session, user_id: int, lesson_id: int, content: str):
    msg = CoachMessage(
        user_id=user_id,
        lesson_id=lesson_id,
        role="user",
        content=content,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)   # ensures object is fully synced with DB
    return msg


def save_ai_message(db: Session, user_id: int, lesson_id: int, content: str):
    msg = CoachMessage(
        user_id=user_id,
        lesson_id=lesson_id,
        role="assistant",
        content=content,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def get_lesson_conversation(db: Session, user_id: int, lesson_id: int, limit: int = 10):
    return (
        db.query(CoachMessage)
        .filter(
            CoachMessage.user_id == user_id,
            CoachMessage.lesson_id == lesson_id,
        )
        .order_by(CoachMessage.created_at.asc())   # chronological order
        .limit(limit)
        .all()
    )