from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from core.db import Base


class TierState(Base):
    __tablename__ = "tier_states"

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    current_tier: Mapped[str] = mapped_column(String(10), nullable=False, server_default="T1")
    mastered_concepts: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    total_concepts: Mapped[int] = mapped_column(Integer, nullable=False, server_default="5")
    progress_percent: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    promotion_eligible_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_promotion_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class ConceptMastery(Base):
    __tablename__ = "concept_masteries"
    __table_args__ = (
        UniqueConstraint("user_id", "concept_id", name="uq_concept_masteries_user_concept"),
        UniqueConstraint("source_event_id", name="uq_concept_masteries_source_event"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    tier: Mapped[str] = mapped_column(String(10), nullable=False)
    concept_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    source_event_id: Mapped[str] = mapped_column(String(64), nullable=False)
    mastered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class PromotionTestAttempt(Base):
    __tablename__ = "promotion_test_attempts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    current_tier: Mapped[str] = mapped_column(String(10), nullable=False)
    target_tier: Mapped[str | None] = mapped_column(String(10), nullable=True)
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False)
    correct_answers: Mapped[int] = mapped_column(Integer, nullable=False)
    score_percent: Mapped[int] = mapped_column(Integer, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    answers_json: Mapped[str] = mapped_column(Text, nullable=False)
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


__all__ = ["ConceptMastery", "PromotionTestAttempt", "TierState"]
