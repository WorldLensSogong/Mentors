from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.chat import (
    ChatMessageCreateRequest,
    ChatMessageResult,
    ChatSessionCreateRequest,
    ChatSessionResult,
)
from app.schemas.common import ResponseEnvelope
from app.services.chat_service import create_chat_message_pair, create_chat_session

router = APIRouter()


@router.post("/sessions", response_model=ResponseEnvelope[ChatSessionResult])
def create_session(
    payload: ChatSessionCreateRequest,
    db: Session = Depends(get_db),
) -> ResponseEnvelope[ChatSessionResult]:
    result = create_chat_session(db, payload)
    return ResponseEnvelope(data=result, message="chat session created")


@router.post("/messages", response_model=ResponseEnvelope[ChatMessageResult])
def create_message(
    payload: ChatMessageCreateRequest,
    db: Session = Depends(get_db),
) -> ResponseEnvelope[ChatMessageResult]:
    result = create_chat_message_pair(db, payload)
    return ResponseEnvelope(data=result, message="chat messages stored")

