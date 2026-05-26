"""2동 - 학습 (멘토 채팅·개념퀴즈·기록).

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
from core.contracts import (
    ConceptId,
    ConceptMasteredEvent,
    MentorId,
    MentorStrategy,
    SessionId,
    UserId,
)
from core.db import get_db
from core.event_bus import event_bus
from core.exceptions import BadRequestError, NotFoundError

from . import curriculum, growth_dep, quizzes, service
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
    TierQuizCatalogRes,
)

router = APIRouter(prefix="/api/learning", tags=["learning"])


def _to_quiz_response(
    item: quizzes.QuizView,
    summary: quizzes.QuizAttemptSummary | None = None,
) -> QuizRes:
    return QuizRes(
        concept_id=item.concept_id,
        concept_name=item.concept_name,
        question=item.question,
        options=[QuizOption(index=idx, text=opt_text) for idx, opt_text in enumerate(item.options)],
        attempted=summary.attempted if summary else False,
        solved=summary.solved if summary else False,
        last_result_correct=summary.last_result_correct if summary else None,
    )


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
    """멘토와의 실시간 채팅 스트리밍 엔드포인트 (SSE)."""
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
    """사용자의 현재 커리큘럼 위치를 반환한다."""
    strategy = get_mentor_strategy(mentor_id)
    return await curriculum.get_position(UserId(user.id), strategy)


@router.get("/quizzes/next", response_model=QuizRes)
async def next_quiz(
    mentor_id: int = Query(..., description="대상 멘토 ID (1=가치, 2=성장, 3=배당, 4=모멘텀)"),
    user: User = Depends(get_current_user),
) -> QuizRes:
    """시스템이 결정한 현재 추천 퀴즈를 반환한다."""
    strategy = get_mentor_strategy(mentor_id)
    position = await curriculum.get_position(UserId(user.id), strategy)
    target = position.current_concept or position.next_recommended
    if target is None:
        raise NotFoundError("학습 가능한 퀴즈가 더 없습니다")

    item = quizzes.get_quiz(target.id)
    return _to_quiz_response(item)


@router.get("/me/quizzes", response_model=TierQuizCatalogRes)
async def list_current_tier_quizzes(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TierQuizCatalogRes:
    """성장 화면에서 사용하는 현재 티어 전용 퀴즈 목록."""
    current_tier = await growth_dep.reader().get_user_tier(UserId(user.id))
    current_tier_quizzes = [
        quizzes.get_quiz(concept.id)
        for concept in curriculum.list_concepts_for_strategy(MentorStrategy.VALUE)
        if concept.tier_required == current_tier
    ]
    attempt_summaries = await quizzes.summarize_attempts_for_concepts(
        user_id=UserId(user.id),
        concept_ids=[int(item.concept_id) for item in current_tier_quizzes],
        db=db,
    )
    return TierQuizCatalogRes(
        tier=current_tier.value,
        quizzes=[
            _to_quiz_response(item, attempt_summaries.get(int(item.concept_id)))
            for item in current_tier_quizzes
        ],
    )


@router.get("/quizzes/{concept_id}", response_model=QuizRes)
async def get_quiz(
    concept_id: int,
    user: User = Depends(get_current_user),
) -> QuizRes:
    """투자 개념 확인 퀴즈 조회."""
    item = quizzes.get_quiz(concept_id)
    return _to_quiz_response(item)


@router.post("/quizzes/submit", response_model=SubmitQuizRes)
async def submit_quiz(
    req: SubmitQuizReq,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SubmitQuizRes:
    """퀴즈 정답 제출 + 채점 + attempt 기록 + 정답 시 mastery 이벤트 발행."""
    is_correct, explanation = quizzes.grade_quiz(
        req.concept_id,
        req.answer_index,
        req.quiz_index,
    )

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
