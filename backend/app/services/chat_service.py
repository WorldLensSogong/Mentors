from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories.chat_repository import (
    create_message_model,
    create_session_model,
    get_session_or_404,
    touch_session_last_message,
)
from app.repositories.mentor_repository import get_mentor_model
from app.repositories.user_repository import get_user_or_404
from app.schemas.chat import ChatMessageCreateRequest, ChatMessageResult, ChatSessionCreateRequest, ChatSessionResult


def create_chat_session(db: Session, payload: ChatSessionCreateRequest) -> ChatSessionResult:
    get_user_or_404(db, payload.user_id)
    mentor = get_mentor_model(db, payload.mentor_id)

    session = create_session_model(
        db,
        user_id=payload.user_id,
        mentor_id=payload.mentor_id,
        title=payload.title or f"{mentor.name}와의 대화",
    )
    db.commit()

    return ChatSessionResult(
        session_id=session.id,
        user_id=session.user_id,
        mentor_id=session.mentor_id,
        title=session.title,
        session_status=session.session_status,
    )


def create_chat_message_pair(db: Session, payload: ChatMessageCreateRequest) -> ChatMessageResult:
    get_user_or_404(db, payload.user_id)
    session = get_session_or_404(db, payload.session_id)
    mentor = get_mentor_model(db, session.mentor_id)

    user_message = create_message_model(
        db,
        session_id=session.id,
        mentor_id=None,
        sender_type="USER",
        content_text=payload.content,
    )

    assistant_content = _build_mock_reply(mentor.name, mentor.strategy.name, payload.content)
    assistant_message = create_message_model(
        db,
        session_id=session.id,
        mentor_id=mentor.id,
        sender_type="ASSISTANT",
        content_text=assistant_content,
    )

    touch_session_last_message(db, session)
    db.flush()
    db.commit()

    return ChatMessageResult(
        session_id=session.id,
        user_message_id=user_message.id,
        assistant_message_id=assistant_message.id,
        assistant_content=assistant_content,
        used_mock_response=True,
    )


def _build_mock_reply(mentor_name: str, strategy_name: str, user_input: str) -> str:
    return (
        f"{mentor_name}입니다. 지금은 mock 응답이지만, "
        f"'{strategy_name}' 관점에서 질문을 이어갈 수 있도록 구조를 열어두었습니다. "
        f"질문 핵심은 '{user_input}'로 이해했고, 이후 AI 팀이 이 부분을 실제 LLM 호출로 교체하면 됩니다."
    )

