"""학습 동 — submit_quiz 라우터의 attempt 기록 검증.

라우터 핸들러를 직접 호출(SimpleNamespace User mock)해서 DB INSERT와 이벤트
발행이 함께 일어나는지 확인. 정답/오답 모두 기록되며, 정답 시에만 이벤트가 발행됨.
"""

import secrets
import importlib
from types import SimpleNamespace

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.models import User
from core.contracts import ConceptId, ConceptMasteredEvent, Tier, UserId
from core.db import SessionLocal
from core.event_bus import event_bus
from features.learning.models import QuizAttempt
from features.learning.router import list_current_tier_quizzes, submit_quiz
from features.learning.schemas import SubmitQuizReq


@pytest.fixture
async def db_session() -> AsyncSession:  # type: ignore[misc]
    async with SessionLocal() as session:
        yield session


@pytest.fixture
async def fixture_user(db_session: AsyncSession) -> User:  # type: ignore[misc]
    unique = secrets.token_hex(8)
    user = User(email=f"submit-{unique}@example.com", nickname=f"제출{unique[:4]}")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    yield user
    await db_session.delete(user)
    await db_session.commit()


@pytest.fixture
def captured_events(monkeypatch: pytest.MonkeyPatch) -> list[ConceptMasteredEvent]:
    """event_bus.publish를 가로채 발행된 이벤트만 캡처. Redis pub/sub 안 거침.

    event_bus의 dispatch 메커니즘은 별도 책임 — 학습동 테스트는 publish 호출
    여부와 인자만 검증한다.
    """
    captured: list[ConceptMasteredEvent] = []

    async def _fake_publish(event: ConceptMasteredEvent) -> None:
        captured.append(event)

    monkeypatch.setattr(event_bus, "publish", _fake_publish)
    return captured


async def _attempts_for(db: AsyncSession, user_id: int, concept_id: int) -> list[QuizAttempt]:
    stmt = (
        select(QuizAttempt)
        .where(QuizAttempt.user_id == user_id, QuizAttempt.concept_id == concept_id)
        .order_by(QuizAttempt.created_at.asc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def test_submit_correct_records_attempt_and_publishes_event(
    db_session: AsyncSession,
    fixture_user: User,
    captured_events: list[ConceptMasteredEvent],
) -> None:
    """정답 제출 → attempt(correct=True) 기록 + ConceptMasteredEvent 발행."""
    # PER(5)의 정답은 index 1
    req = SubmitQuizReq(concept_id=5, answer_index=1, quiz_index=0)
    user = SimpleNamespace(id=fixture_user.id)

    res = await submit_quiz(req, user=user, db=db_session)  # type: ignore[arg-type]

    assert res.correct is True
    assert res.explanation
    # DB attempt 기록 검증
    attempts = await _attempts_for(db_session, fixture_user.id, 5)
    assert len(attempts) == 1
    assert attempts[0].quiz_index == 0
    assert attempts[0].correct is True
    # 이벤트 발행 확인
    assert len(captured_events) == 1
    assert captured_events[0].concept_id == ConceptId(5)
    assert captured_events[0].user_id == UserId(fixture_user.id)


async def test_submit_incorrect_records_attempt_but_no_event(
    db_session: AsyncSession,
    fixture_user: User,
    captured_events: list[ConceptMasteredEvent],
) -> None:
    """오답 제출 → attempt(correct=False) 기록만, 이벤트 발행 안 함."""
    # PER(5)의 오답: index 0 (정답은 1)
    req = SubmitQuizReq(concept_id=5, answer_index=0, quiz_index=0)
    user = SimpleNamespace(id=fixture_user.id)

    res = await submit_quiz(req, user=user, db=db_session)  # type: ignore[arg-type]

    assert res.correct is False
    assert res.explanation
    # DB attempt 기록 검증
    attempts = await _attempts_for(db_session, fixture_user.id, 5)
    assert len(attempts) == 1
    assert attempts[0].correct is False
    # 이벤트 발행 안 함
    assert captured_events == []


async def test_submit_multiple_attempts_all_recorded(
    db_session: AsyncSession,
    fixture_user: User,
) -> None:
    """같은 (concept, quiz_index) 여러 번 제출 → 모두 별도 attempt로 기록."""
    user = SimpleNamespace(id=fixture_user.id)

    # 첫 시도 오답
    await submit_quiz(
        SubmitQuizReq(concept_id=5, answer_index=0, quiz_index=0),
        user=user,  # type: ignore[arg-type]
        db=db_session,
    )
    # 두 번째 시도 정답
    await submit_quiz(
        SubmitQuizReq(concept_id=5, answer_index=1, quiz_index=0),
        user=user,  # type: ignore[arg-type]
        db=db_session,
    )

    attempts = await _attempts_for(db_session, fixture_user.id, 5)
    assert len(attempts) == 2
    # 시간순 정렬되므로 첫 번째가 오답, 두 번째가 정답
    assert attempts[0].correct is False
    assert attempts[1].correct is True


async def test_submit_with_default_quiz_index(
    db_session: AsyncSession,
    fixture_user: User,
) -> None:
    """quiz_index 미지정(0이 default) → 정상 동작 (하위 호환)."""
    user = SimpleNamespace(id=fixture_user.id)
    # quiz_index 생략
    req = SubmitQuizReq(concept_id=6, answer_index=2)  # 복리 정답=2
    res = await submit_quiz(req, user=user, db=db_session)  # type: ignore[arg-type]

    assert res.correct is True
    attempts = await _attempts_for(db_session, fixture_user.id, 6)
    assert len(attempts) == 1
    assert attempts[0].quiz_index == 0


async def test_quiz_catalog_reflects_attempted_and_solved_state_after_chat_quiz(
    db_session: AsyncSession,
    fixture_user: User,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    learning_router = importlib.import_module("features.learning.router")

    class _FakeGrowthReader:
        async def get_user_tier(self, _user_id: int) -> Tier:
            return Tier.T1

    monkeypatch.setattr(learning_router.growth_dep, "reader", lambda: _FakeGrowthReader())

    user = SimpleNamespace(id=fixture_user.id)

    initial_catalog = await list_current_tier_quizzes(user=user, db=db_session)  # type: ignore[arg-type]
    initial_quiz = next((quiz for quiz in initial_catalog.quizzes if quiz.concept_id == 5), None)
    assert initial_quiz is not None
    assert initial_quiz.attempted is False
    assert initial_quiz.solved is False
    assert initial_quiz.last_result_correct is None

    await submit_quiz(
        SubmitQuizReq(concept_id=5, answer_index=1, quiz_index=0),
        user=user,  # type: ignore[arg-type]
        db=db_session,
    )

    updated_catalog = await list_current_tier_quizzes(user=user, db=db_session)  # type: ignore[arg-type]
    updated_quiz = next((quiz for quiz in updated_catalog.quizzes if quiz.concept_id == 5), None)
    assert updated_quiz is not None
    assert updated_quiz.attempted is True
    assert updated_quiz.solved is True
    assert updated_quiz.last_result_correct is True
