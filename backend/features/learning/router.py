"""2동 — 학습 (멘토 채팅·개념퀴즈·기록).

owner: learning
관련 FR: FR-02, UC-04, UC-10
핵심 의존성: core/ai_pipeline (RAG·Guardrail·Hallucination·Critic·TierOverlay)
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from core.ai_pipeline import guardrail
from core.auth.dependencies import get_current_user
from core.auth.models import User
from core.contracts import ConceptId, ConceptMasteredEvent, MentorId, SessionId, UserId
from core.db import get_db
from core.event_bus import event_bus
from core.exceptions import BadRequestError, NotFoundError

from . import curriculum, quizzes, service
from .personas import get_mentor_strategy
from .schemas import (
    ChatStreamReq,
    CreateSessionReq,
    MessageListRes,
    MessageRes,
    QuizOption,
    QuizRes,
    SendMessageReq,
    SessionListRes,
    SessionRes,
    SubmitQuizReq,
    SubmitQuizRes,
)

router = APIRouter(prefix="/api/learning", tags=["learning"])


@router.get("/sessions", response_model=SessionListRes)
async def list_sessions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionListRes:
    """사용자의 멘토 채팅 세션 목록 (최신순)."""
    sessions = await service.list_sessions(UserId(user.id), db)
    return SessionListRes(sessions=[SessionRes.model_validate(s) for s in sessions])


@router.post("/sessions", response_model=SessionRes)
async def create_session(
    req: CreateSessionReq,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionRes:
    """새 멘토 채팅 세션 생성."""
    session = await service.create_session(
        user_id=UserId(user.id),
        mentor_id=MentorId(req.mentor_id),
        db=db,
    )
    await db.commit()
    return SessionRes.model_validate(session)


@router.get("/sessions/{session_id}/messages", response_model=MessageListRes)
async def list_messages(
    session_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageListRes:
    """세션의 메시지 목록 (시간순)."""
    messages = await service.list_messages(
        session_id=SessionId(session_id),
        user_id=UserId(user.id),
        db=db,
    )
    return MessageListRes(messages=[MessageRes.model_validate(m) for m in messages])


@router.post("/sessions/{session_id}/messages", response_model=MessageRes)
async def send_message(
    session_id: int,
    req: SendMessageReq,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageRes:
    """메시지 전송 (단순 저장용). 실제 멘토 대화는 /chat/stream 사용을 권장."""
    message = await service.add_message(
        session_id=SessionId(session_id),
        user_id=UserId(user.id),
        role="user",
        content=req.content,
        db=db,
    )
    await db.commit()
    return MessageRes.model_validate(message)


@router.post("/chat/stream")
async def chat_stream(
    req: ChatStreamReq,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EventSourceResponse:
    """멘토와의 실시간 채팅 스트리밍 엔드포인트 (SSE).

    - 입력 가드레일 확인 후 사용자 메시지 저장.
    - AI 파이프라인(RAG → 티어 오버레이 → 스트리밍 → 후처리 검증)을 거쳐 응답 반환.
    """
    g = guardrail.check_input(req.content)
    if not g.ok:
        raise BadRequestError(g.reason or "입력 가드레일 차단")

    await service.add_message(
        session_id=SessionId(req.session_id),
        user_id=UserId(user.id),
        role="user",
        content=req.content,
        db=db,
    )
    await db.commit()

    return EventSourceResponse(
        service.stream_assistant_response(
            session_id=SessionId(req.session_id),
            user_id=UserId(user.id),
            user_content=req.content,
        )
    )


@router.get("/curriculum/me", response_model=curriculum.CurriculumPosition)
async def my_curriculum_position(
    mentor_id: int = Query(..., description="대상 멘토 ID (1=가치, 2=성장, 3=배당, 4=모멘텀)"),
    user: User = Depends(get_current_user),
) -> curriculum.CurriculumPosition:
    """사용자의 현재 커리큘럼 위치 — 멘토(투자 전략)별로 계산.

    반환 필드:
    - tier: 사용자의 현재 티어 (성장동 미등록 시 T1)
    - mastered: 마스터한 개념 ID 집합 (성장동 미등록 시 빈셋)
    - available: 티어 충족 + 선수 전부 마스터된 개념 목록
    - locked: 그 외 (티어 미달 또는 선수 미충족)
    - next_recommended: available 중 아직 마스터하지 않은 첫 개념
    - current_concept: 현재 학습 중인 개념 (MVP: next_recommended와 동일)

    MVP 시드는 가치투자(mentor_id=1)만 채워져 있다. 다른 mentor_id를
    보내면 fallback으로 VALUE 커리큘럼이 적용되며, 시드가 없는 전략은
    빈 Position을 반환한다.
    """
    strategy = get_mentor_strategy(mentor_id)
    return await curriculum.get_position(UserId(user.id), strategy)


@router.get("/quizzes/next", response_model=QuizRes)
async def next_quiz(
    mentor_id: int = Query(..., description="대상 멘토 ID (1=가치, 2=성장, 3=배당, 4=모멘텀)"),
    user: User = Depends(get_current_user),
) -> QuizRes:
    """시스템이 결정한 '지금 풀 만한 퀴즈'를 반환.

    선택 우선순위: `current_concept`(대화 맥락에서 감지된 개념, MVP는
    next_recommended와 동일) → `next_recommended`(available 중 가장 앞).

    모든 개념을 마스터했거나 시드가 빈 전략(GROWTH/DIVIDEND/MOMENTUM, MVP 시점)
    이면 404를 반환한다.
    """
    strategy = get_mentor_strategy(mentor_id)
    position = await curriculum.get_position(UserId(user.id), strategy)
    target = position.current_concept or position.next_recommended
    if target is None:
        raise NotFoundError("학습 가능한 퀴즈가 더 없습니다")

    item = quizzes.get_quiz(target.id)
    options = [QuizOption(index=idx, text=opt_text) for idx, opt_text in enumerate(item.options)]
    return QuizRes(
        concept_id=item.concept_id,
        concept_name=item.concept_name,
        question=item.question,
        options=options,
    )


@router.get("/quizzes/{concept_id}", response_model=QuizRes)
async def get_quiz(
    concept_id: int,
    user: User = Depends(get_current_user),
) -> QuizRes:
    """투자 개념 확인 퀴즈 조회."""
    item = quizzes.get_quiz(concept_id)
    options = [QuizOption(index=idx, text=opt_text) for idx, opt_text in enumerate(item.options)]
    return QuizRes(
        concept_id=item.concept_id,
        concept_name=item.concept_name,
        question=item.question,
        options=options,
    )


@router.post("/quizzes/submit", response_model=SubmitQuizRes)
async def submit_quiz(
    req: SubmitQuizReq,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SubmitQuizRes:
    """퀴즈 정답 제출 + 채점 + attempt DB 기록 + (정답 시) ConceptMasteredEvent 발행.

    - 정답·오답 모두 `learning_quiz_attempts`에 기록 — 오답은 같은 문제 재도전 후보로,
      정답은 follow-up 후보에서 영구 제외하는 기준이 된다.
    - 정답 시 `ConceptMasteredEvent` 발행. 성장동이 이를 어떻게 누적·승급 판정에
      반영할지는 성장동 책임 (학습동은 단순 발행만).
    """
    is_correct, explanation = quizzes.grade_quiz(req.concept_id, req.answer_index, req.quiz_index)

    await quizzes.record_attempt(
        user_id=UserId(user.id),
        concept_id=req.concept_id,
        quiz_index=req.quiz_index,
        correct=is_correct,
        db=db,
    )
    await db.commit()

    if is_correct:
        await event_bus.publish(
            ConceptMasteredEvent(
                user_id=UserId(user.id),
                concept_id=ConceptId(req.concept_id),
            )
        )

    return SubmitQuizRes(correct=is_correct, explanation=explanation)
