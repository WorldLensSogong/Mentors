from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.chat import ChatMessage, ChatSession


def create_session_model(db: Session, *, user_id: int, mentor_id: int, title: str | None) -> ChatSession:
    session = ChatSession(user_id=user_id, mentor_id=mentor_id, title=title)
    db.add(session)
    db.flush()
    return session


def get_session_or_404(db: Session, session_id: int) -> ChatSession:
    session = db.get(ChatSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="chat session not found")
    return session


def create_message_model(
    db: Session,
    *,
    session_id: int,
    mentor_id: int | None,
    sender_type: str,
    content_text: str,
) -> ChatMessage:
    message = ChatMessage(
        session_id=session_id,
        mentor_id=mentor_id,
        sender_type=sender_type,
        content_text=content_text,
    )
    db.add(message)
    return message


def touch_session_last_message(db: Session, session: ChatSession) -> None:
    session.last_message_at = datetime.utcnow()
    db.add(session)

