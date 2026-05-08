from __future__ import annotations

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class LevelDefinition(Base, TimestampMixin):
    __tablename__ = "level_definitions"

    id: Mapped[int] = mapped_column(primary_key=True)
    level_no: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    min_xp: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unlock_summary: Mapped[str | None] = mapped_column(Text)

