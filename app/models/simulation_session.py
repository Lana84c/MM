from datetime import datetime, UTC

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class SimulationSession(Base):
    __tablename__ = "simulation_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id"), nullable=False, index=True)
    scenario_id: Mapped[int] = mapped_column(ForeignKey("scenarios.id"), nullable=False, index=True)

    mode: Mapped[str] = mapped_column(String(50), nullable=False, default="roleplay")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    turn_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    score: Mapped[int | None] = mapped_column(nullable=True)
    feedback_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user = relationship("User")
    lesson = relationship("Lesson")
    scenario = relationship("Scenario")
    messages = relationship(
        "SimulationMessage",
        back_populates="session",
        cascade="all, delete-orphan",
    )