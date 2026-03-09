from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    price_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    billing_interval: Mapped[str] = mapped_column(String(20), nullable=False, default="monthly")

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    max_ai_messages_per_month: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    max_practice_sessions_per_month: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    max_learners: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    includes_org_dashboard: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    includes_advanced_analytics: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    includes_roleplay: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)