from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class InvestmentStrategy(Base, TimestampMixin):
    __tablename__ = "investment_strategies"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    principle_summary: Mapped[str | None] = mapped_column(Text)
    risk_profile_tag: Mapped[str | None] = mapped_column(String(30))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    mentors: Mapped[list["Mentor"]] = relationship(back_populates="strategy")


class InterestTopic(Base, TimestampMixin):
    __tablename__ = "interest_topics"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str | None] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(Text)


class Mentor(Base, TimestampMixin):
    __tablename__ = "mentors"

    id: Mapped[int] = mapped_column(primary_key=True)
    strategy_id: Mapped[int] = mapped_column(ForeignKey("investment_strategies.id"), nullable=False)
    unlock_level_id: Mapped[int | None] = mapped_column(ForeignKey("level_definitions.id"))
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    one_liner: Mapped[str | None] = mapped_column(String(255))
    philosophy: Mapped[str | None] = mapped_column(Text)
    speaking_style: Mapped[str | None] = mapped_column(Text)
    prompt_template: Mapped[str | None] = mapped_column(Text)
    is_free: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    strategy: Mapped["InvestmentStrategy"] = relationship(back_populates="mentors")
    unlock_level = relationship("LevelDefinition")


class MentorFocusTopic(Base):
    __tablename__ = "mentor_focus_topics"

    mentor_id: Mapped[int] = mapped_column(ForeignKey("mentors.id"), primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("interest_topics.id"), primary_key=True)

