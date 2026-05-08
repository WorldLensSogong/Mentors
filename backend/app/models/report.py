from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DailyReport(Base):
    __tablename__ = "daily_reports"
    __table_args__ = (UniqueConstraint("user_id", "mentor_id", "report_date", name="uq_daily_report"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    mentor_id: Mapped[int] = mapped_column(ForeignKey("mentors.id"), nullable=False)
    level_id: Mapped[int] = mapped_column(ForeignKey("level_definitions.id"), nullable=False)
    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary_text: Mapped[str | None] = mapped_column(Text)
    outlook_text: Mapped[str | None] = mapped_column(Text)
    learning_question_text: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PUBLISHED")
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

