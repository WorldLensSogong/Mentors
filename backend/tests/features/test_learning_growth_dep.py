"""학습 동 — 성장동 의존성 fallback 검증.

핵심: 성장동 미등록 시에도 학습동이 정상 동작해야 한다 (T1·빈 마스터리).
등록 후에는 등록된 구현체에 위임된다.
"""

import pytest

from core.contracts import ConceptId, MentorStrategy, Tier, UserId
from core.read_services import register_growth_reader, registry
from features.learning.growth_dep import reader


@pytest.fixture(autouse=True)
def reset_growth_reader_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    """각 테스트가 깨끗한 미등록 상태에서 시작하도록 _growth_reader를 None으로 강제."""
    monkeypatch.setattr(registry, "_growth_reader", None)


async def test_reader_returns_null_when_growth_not_registered() -> None:
    r = reader()
    # 모두 T1로 보고
    assert await r.get_user_tier(UserId(123)) == Tier.T1
    # 어떤 사용자·전략 조합도 마스터리 빈셋
    assert await r.get_mastered_concepts(UserId(123), MentorStrategy.VALUE) == set()
    assert await r.get_mastered_concepts(UserId(999), MentorStrategy.GROWTH) == set()
    # 분포도 빈 dict
    assert await r.get_tier_distribution() == {}


async def test_null_reader_is_stable_across_calls() -> None:
    # 같은 더미 인스턴스를 반환하는지 (불필요한 인스턴스 생성 회피)
    assert reader() is reader()


async def test_reader_delegates_to_registered_impl() -> None:
    class FakeReader:
        async def get_user_tier(self, user_id: UserId) -> Tier:
            return Tier.T3

        async def get_mastered_concepts(
            self, user_id: UserId, strategy: MentorStrategy
        ) -> set[ConceptId]:
            return {ConceptId(1), ConceptId(5), ConceptId(8)}

        async def get_tier_distribution(self) -> dict[Tier, int]:
            return {Tier.T1: 100, Tier.T2: 50}

    register_growth_reader(FakeReader())

    r = reader()
    assert await r.get_user_tier(UserId(1)) == Tier.T3
    mastered = await r.get_mastered_concepts(UserId(1), MentorStrategy.VALUE)
    assert mastered == {ConceptId(1), ConceptId(5), ConceptId(8)}
    dist = await r.get_tier_distribution()
    assert dist == {Tier.T1: 100, Tier.T2: 50}
