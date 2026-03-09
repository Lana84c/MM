from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Scenario(Base):
    __tablename__ = "scenarios"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id"), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(150), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    scenario_type: Mapped[str] = mapped_column(String(100), nullable=False, default="roleplay")
    ai_role: Mapped[str] = mapped_column(String(100), nullable=False, default="Conversation Partner")
    learner_objective: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(50), nullable=False, default="beginner")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    lesson = relationship("Lesson")