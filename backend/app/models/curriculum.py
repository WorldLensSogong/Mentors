from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class LearningModule(Base, TimestampMixin):
    __tablename__ = "learning_modules"

    id: Mapped[int] = mapped_column(primary_key=True)
    strategy_id: Mapped[int] = mapped_column(ForeignKey("investment_strategies.id"), nullable=False)
    level_id: Mapped[int] = mapped_column(ForeignKey("level_definitions.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    concept_summary: Mapped[str | None] = mapped_column(Text)
    quiz_question: Mapped[str | None] = mapped_column(Text)
    quiz_answer_text: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

