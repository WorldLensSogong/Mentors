from __future__ import annotations

from pydantic import BaseModel, Field


class ChatSessionCreateRequest(BaseModel):
    user_id: int
    mentor_id: int
    title: str | None = None


class ChatSessionResult(BaseModel):
    session_id: int
    user_id: int
    mentor_id: int
    title: str | None
    session_status: str


class ChatMessageCreateRequest(BaseModel):
    session_id: int
    user_id: int
    content: str = Field(min_length=1)


class ChatMessageResult(BaseModel):
    session_id: int
    user_message_id: int
    assistant_message_id: int
    assistant_content: str
    used_mock_response: bool

