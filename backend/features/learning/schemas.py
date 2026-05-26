"""학습 동 Pydantic 스키마 — 요청/응답 모델."""

from datetime import datetime

from pydantic import BaseModel, Field


# --- 요청 ---
class CreateSessionReq(BaseModel):
    mentor_id: int = Field(..., description="선택한 멘토 ID")


class SendMessageReq(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000, description="사용자 메시지")


class ChatStreamReq(BaseModel):
    session_id: int = Field(..., description="채팅 세션 ID")
    content: str = Field(..., min_length=1, max_length=2000, description="사용자 메시지")


# --- 응답 ---
class SessionRes(BaseModel):
    id: int
    mentor_id: int
    title: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageRes(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionListRes(BaseModel):
    sessions: list[SessionRes]


class MessageListRes(BaseModel):
    messages: list[MessageRes]


# --- 퀴즈 요청/응답 ---
class SubmitQuizReq(BaseModel):
    concept_id: int = Field(..., description="투자 개념 ID")
    answer_index: int = Field(..., description="선택한 보기 인덱스 (0~3)")
    quiz_index: int = Field(
        0,
        description="개념 내 퀴즈 인덱스 (개념당 여러 문제가 있을 때 식별). 미지정 시 0",
    )


class QuizOption(BaseModel):
    index: int
    text: str


class QuizRes(BaseModel):
    concept_id: int
    concept_name: str
    question: str
    options: list[QuizOption]
    attempted: bool = False
    solved: bool = False
    last_result_correct: bool | None = None


class TierQuizCatalogRes(BaseModel):
    tier: str
    quizzes: list[QuizRes]


class SubmitQuizRes(BaseModel):
    correct: bool
    explanation: str


# --- SSE follow-up 이벤트 페이로드 ---
class FollowUpQuiz(BaseModel):
    """`/chat/stream`의 `follow_up_quiz` SSE 이벤트로 전송되는 페이로드.

    프론트가 멘토 응답 끝에 버튼을 그리기 위해 필요한 최소 필드만 노출
    (correct_index/explanation은 제외 — submit 응답에서 제공됨).
    """

    concept_id: int
    concept_name: str
    quiz_index: int
    question: str
    options: list[str]
