"""학습 동 — GET /api/learning/quizzes/next 라우터 핸들러 단위 테스트.

라우터 함수를 직접 호출해 target 선정 로직(current_concept → next_recommended →
None이면 404)을 검증한다. TestClient + DB·LLM 부담을 피하려고 User는
SimpleNamespace로 mock.
"""

from types import SimpleNamespace

import pytest

from core.contracts import MentorStrategy, Tier
from core.exceptions import NotFoundError
from core.read_services import register_growth_reader, registry
from features.learning.curriculum import list_concepts_for_strategy
from features.learning.router import next_quiz


@pytest.fixture(autouse=True)
def reset_growth_reader_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    """각 테스트가 미등록 상태에서 시작."""
    monkeypatch.setattr(registry, "_growth_reader", None)


class _FakeReader:
    def __init__(self, tier: Tier, mastered: set[int]) -> None:
        self._tier = tier
        self._mastered = mastered

    async def get_user_tier(self, user_id: int) -> Tier:
        return self._tier

    async def get_mastered_concepts(self, user_id: int, strategy: MentorStrategy) -> set[int]:
        return self._mastered

    async def get_tier_distribution(self) -> dict[Tier, int]:
        return {}


async def test_next_quiz_returns_first_recommended_in_dummy_env() -> None:
    """더미 환경(T1·빈셋)에서는 next_recommended가 주식(1)이므로 그 퀴즈 반환."""
    user = SimpleNamespace(id=1)
    res = await next_quiz(mentor_id=1, user=user)  # type: ignore[arg-type]

    assert res.concept_id == 1
    assert res.concept_name == "주식이란 무엇인가"
    assert len(res.options) == 4


async def test_next_quiz_404_when_all_mastered() -> None:
    """모든 개념을 마스터한 T5 사용자는 next/current가 None이라 404."""
    all_value_ids = {c.id for c in list_concepts_for_strategy(MentorStrategy.VALUE)}
    register_growth_reader(_FakeReader(Tier.T5, all_value_ids))  # type: ignore[arg-type]
    user = SimpleNamespace(id=1)

    with pytest.raises(NotFoundError):
        await next_quiz(mentor_id=1, user=user)  # type: ignore[arg-type]


async def test_next_quiz_404_for_empty_strategy() -> None:
    """시드가 빈 전략(GROWTH/DIVIDEND/MOMENTUM)은 항상 404."""
    user = SimpleNamespace(id=1)

    # mentor_id=2 (GROWTH) — MVP 시점에 시드 없음
    with pytest.raises(NotFoundError):
        await next_quiz(mentor_id=2, user=user)  # type: ignore[arg-type]


async def test_next_quiz_advances_after_partial_mastery() -> None:
    """주식(1) 마스터 후 채권/주식(2, prereq=[1])이 잠금 해제되어 next로 이동."""
    register_growth_reader(_FakeReader(Tier.T1, {1}))  # type: ignore[arg-type]
    user = SimpleNamespace(id=1)
    res = await next_quiz(mentor_id=1, user=user)  # type: ignore[arg-type]

    # mastered={1} → 채권과 주식의 차이(2, prereq=[1])가 available로 이동.
    # id 오름차순 정렬이므로 id=2가 id=3(매출과 이익)보다 먼저.
    assert res.concept_id == 2
    assert res.concept_name == "채권과 주식의 차이"
