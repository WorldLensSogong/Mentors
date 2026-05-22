from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base


class DebateSession(Base):
    __tablename__ = "debate_sessions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    persona_a_id: Mapped[str] = mapped_column(String(50), nullable=False)
    persona_b_id: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="created")
    error_message: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    messages: Mapped[list[DebateMessage]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="DebateMessage.turn_index",
    )


class DebateMessage(Base):
    __tablename__ = "debate_messages"
    __table_args__ = (
        UniqueConstraint("debate_session_id", "turn_index", name="uq_debate_messages_turn"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    debate_session_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("debate_sessions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    turn_index: Mapped[int] = mapped_column(Integer, nullable=False)
    speaker_id: Mapped[str] = mapped_column(String(50), nullable=False)
    turn_type: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    critic_result: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped[DebateSession] = relationship(back_populates="messages")
