"""학습 동 — quizzes.pick_for_user 로테이션 정책 검증.

`_pick_from_pool` 순수 함수는 단위 테스트로, `pick_for_user`는 실제 Postgres에
대고 통합 테스트로 검증한다. 각 테스트가 고유 user_id로 격리되며 자기가 INSERT한
QuizAttempt를 cleanup한다.
"""

import secrets

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.models import User
from core.contracts import ConceptId, UserId
from core.db import SessionLocal
from features.learning.models import QuizAttempt
from features.learning.quizzes import QuizItem, _pick_from_pool, pick_for_user

# --- _pick_from_pool 순수 함수 ---


def _make_item(idx: int) -> QuizItem:
    return QuizItem(
        concept_id=ConceptId(1),
        question=f"q{idx}",
        options=["a", "b", "c", "d"],
        correct_index=0,
        explanation=f"e{idx}",
    )


def test_pick_returns_none_for_empty_pool() -> None:
    assert _pick_from_pool([], set()) is None
    assert _pick_from_pool([], {0, 1, 2}) is None


def test_pick_returns_first_when_nothing_mastered() -> None:
    pool = [_make_item(0), _make_item(1), _make_item(2)]
    result = _pick_from_pool(pool, set())
    assert result is not None
    item, idx = result
    assert idx == 0
    assert item.question == "q0"


def test_pick_skips_mastered_indices() -> None:
    pool = [_make_item(0), _make_item(1), _make_item(2)]
    result = _pick_from_pool(pool, {0, 1})
    assert result is not None
    item, idx = result
    assert idx == 2
    assert item.question == "q2"


def test_pick_returns_none_when_all_mastered() -> None:
    pool = [_make_item(0), _make_item(1)]
    assert _pick_from_pool(pool, {0, 1}) is None


def test_pick_prefers_smallest_unmastered_index() -> None:
    """비연속 마스터: {1, 3} → 0 반환 (가장 작은 안 푼 것)."""
    pool = [_make_item(i) for i in range(4)]
    result = _pick_from_pool(pool, {1, 3})
    assert result is not None
    _item, idx = result
    assert idx == 0


# --- pick_for_user DB 통합 ---


@pytest.fixture
async def db_session() -> AsyncSession:  # type: ignore[misc]
    async with SessionLocal() as session:
        yield session


@pytest.fixture
async def fixture_user(db_session: AsyncSession) -> User:  # type: ignore[misc]
    """고유 email로 테스트 사용자 1명 생성. 테스트 종료 시 CASCADE로 attempts도 삭제."""
    unique = secrets.token_hex(8)
    user = User(email=f"test-{unique}@example.com", nickname=f"테스트{unique[:4]}")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    yield user
    # 사용자 삭제 → attempts CASCADE로 함께 정리
    await db_session.delete(user)
    await db_session.commit()


async def test_pick_for_user_returns_first_when_no_attempts(
    db_session: AsyncSession,
    fixture_user: User,
) -> None:
    """attempts 없는 사용자 → PER(5) 풀의 첫 퀴즈 반환."""
    result = await pick_for_user(UserId(fixture_user.id), 5, db_session)
    assert result is not None
    item, idx = result
    assert idx == 0
    assert item.concept_id == ConceptId(5)


async def test_pick_for_user_skips_correct_attempts(
    db_session: AsyncSession,
    fixture_user: User,
) -> None:
    """correct=True인 quiz_index는 후보에서 제외 (시드 1개라 None 반환)."""
    db_session.add(
        QuizAttempt(
            user_id=fixture_user.id,
            concept_id=5,
            quiz_index=0,
            correct=True,
        )
    )
    await db_session.commit()

    result = await pick_for_user(UserId(fixture_user.id), 5, db_session)
    assert result is None  # 시드 1개를 정답 처리 → 더 풀 게 없음


async def test_pick_for_user_keeps_incorrect_attempts_as_candidates(
    db_session: AsyncSession,
    fixture_user: User,
) -> None:
    """correct=False인 attempt는 마스터로 안 침 → 같은 문제 다시 후보."""
    db_session.add(
        QuizAttempt(
            user_id=fixture_user.id,
            concept_id=5,
            quiz_index=0,
            correct=False,
        )
    )
    await db_session.commit()

    result = await pick_for_user(UserId(fixture_user.id), 5, db_session)
    assert result is not None
    _item, idx = result
    assert idx == 0  # 오답 재도전


async def test_pick_for_user_returns_none_for_unknown_concept(
    db_session: AsyncSession,
    fixture_user: User,
) -> None:
    """존재하지 않는 concept_id → None (예외 아님)."""
    result = await pick_for_user(UserId(fixture_user.id), 9999, db_session)
    assert result is None


async def test_pick_for_user_isolates_per_user(
    db_session: AsyncSession,
    fixture_user: User,
) -> None:
    """한 사용자의 정답 기록은 다른 사용자의 follow-up에 영향 없음."""
    # 다른 사용자의 정답 attempt 삽입
    other_unique = secrets.token_hex(8)
    other_user = User(email=f"other-{other_unique}@example.com", nickname=f"다른{other_unique[:4]}")
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)

    db_session.add(QuizAttempt(user_id=other_user.id, concept_id=5, quiz_index=0, correct=True))
    await db_session.commit()

    # fixture_user는 자기 attempt 없으므로 여전히 첫 문제 받아야 함
    result = await pick_for_user(UserId(fixture_user.id), 5, db_session)
    assert result is not None
    _item, idx = result
    assert idx == 0

    # cleanup
    await db_session.delete(other_user)
    await db_session.commit()
