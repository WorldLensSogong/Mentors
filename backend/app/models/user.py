from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    nickname: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")

    profile: Mapped["UserProfile"] = relationship(back_populates="user", uselist=False)
    auth_identities: Mapped[list["AuthIdentity"]] = relationship(back_populates="user")


class AuthIdentity(Base, TimestampMixin):
    __tablename__ = "auth_identities"
    __table_args__ = (UniqueConstraint("provider", "provider_user_id", name="uq_provider_user"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(30), nullable=False)
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="auth_identities")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    current_level_id: Mapped[int] = mapped_column(ForeignKey("level_definitions.id"), nullable=False)
    current_mentor_id: Mapped[int | None] = mapped_column(ForeignKey("mentors.id"))
    age_band: Mapped[str | None] = mapped_column(String(30))
    has_investment_experience: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    investment_experience_months: Mapped[int | None] = mapped_column(Integer)
    holdings_summary: Mapped[str | None] = mapped_column(Text)
    investment_amount_band: Mapped[str | None] = mapped_column(String(50))
    investment_purpose: Mapped[str | None] = mapped_column(String(100))
    risk_tolerance: Mapped[str | None] = mapped_column(String(30))
    learning_stage: Mapped[str] = mapped_column(String(30), nullable=False, default="LEARNING")
    total_xp: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    onboarding_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
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

    user: Mapped["User"] = relationship(back_populates="profile")
    current_level = relationship("LevelDefinition")
    current_mentor = relationship("Mentor")


class OnboardingSurveyAnswer(Base):
    __tablename__ = "onboarding_survey_answers"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    question_code: Mapped[str] = mapped_column(String(50), nullable=False)
    question_text: Mapped[str | None] = mapped_column(String(255))
    answer_value: Mapped[str | None] = mapped_column(Text)
    answer_payload: Mapped[str | None] = mapped_column(Text)
    answered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class UserInterestTopic(Base):
    __tablename__ = "user_interest_topics"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("interest_topics.id"), primary_key=True)

