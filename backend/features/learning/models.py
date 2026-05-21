"""학습 동 DB 모델 — 멘토 채팅 세션 + 메시지.

owner: learning
관련 FR: FR-02, UC-04, UC-10
"""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base


class ChatSession(Base):
    """멘토 채팅 세션."""

    __tablename__ = "learning_chat_sessions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    mentor_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    title: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class ChatMessage(Base):
    """채팅 메시지 (사용자 + 멘토 응답 모두 저장)."""

    __tablename__ = "learning_chat_messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("learning_chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user | assistant | system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped[ChatSession] = relationship(back_populates="messages")


class QuizAttempt(Base):
    """사용자별 퀴즈 시도 기록.

    follow-up 정책의 중복/마스터 판정 기반:
    - `correct=True`인 (concept_id, quiz_index)는 더 이상 follow-up 후보에서 제외
    - 오답은 다시 같은 문제가 제공될 수 있음
    """

    __tablename__ = "learning_quiz_attempts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    concept_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    quiz_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        # 사용자별 특정 개념 attempts 조회 최적화 (follow-up 결정 시 핫 패스)
        Index("ix_learning_quiz_attempts_user_concept", "user_id", "concept_id"),
    )
