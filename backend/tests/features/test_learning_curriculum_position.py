"""학습 동 — CurriculumService.get_position 검증.

티어와 마스터한 개념의 조합이 available/locked/next_recommended를 어떻게
결정하는지 시드 데이터 위에서 확인한다. 성장동 미등록 환경(_NullGrowthReader)
부터 등록된 fake reader 환경까지 케이스별로 다룬다.
"""

import pytest

from core.contracts import ConceptId, MentorStrategy, Tier, UserId
from core.read_services import register_growth_reader, registry
from features.learning.curriculum import (
    get_position,
    list_concepts_for_strategy,
)


@pytest.fixture(autouse=True)
def reset_growth_reader_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    """각 테스트가 미등록 상태에서 시작하도록 _growth_reader를 None으로 강제."""
    monkeypatch.setattr(registry, "_growth_reader", None)


# --- 더미 reader 환경 (T1·빈 마스터리) ---------------------------------------


async def test_default_t1_user_value_strategy_position() -> None:
    """성장동 미등록 = 모두 T1·빈 마스터리. T1 중 prereq=[]만 available."""
    pos = await get_position(UserId(1), MentorStrategy.VALUE)

    assert pos.tier == Tier.T1
    assert pos.mastered == set()

    avail_ids = {c.id for c in pos.available}
    locked_ids = {c.id for c in pos.locked}

    # 선수 없는 T1: 주식(1), 매출과 이익(3), 인플레이션(4), 복리(6)
    assert avail_ids == {ConceptId(1), ConceptId(3), ConceptId(4), ConceptId(6)}

    # 선수 미충족 T1 — 채권/주식 차이(2, prereq=1), PER(5, prereq=1,3),
    # 내재가치(7, prereq=1), 안전마진(8, prereq=5,7)
    for blocked_by_prereq in (2, 5, 7, 8):
        assert ConceptId(blocked_by_prereq) in locked_ids

    # T2 이상은 모두 티어 미충족으로 locked
    for tier2_plus in (9, 10, 15, 20, 23):
        assert ConceptId(tier2_plus) in locked_ids

    assert len(pos.available) + len(pos.locked) == 23


async def test_default_user_next_is_smallest_available_id() -> None:
    pos = await get_position(UserId(1), MentorStrategy.VALUE)
    assert pos.next_recommended is not None
    assert pos.next_recommended.id == ConceptId(1)  # 주식이란 무엇인가
    # MVP에서 current_concept은 next_recommended와 동일
    assert pos.current_concept is pos.next_recommended


# --- 빈 전략 (GROWTH/DIVIDEND/MOMENTUM) --------------------------------------


@pytest.mark.parametrize(
    "strategy", [MentorStrategy.GROWTH, MentorStrategy.DIVIDEND, MentorStrategy.MOMENTUM]
)
async def test_empty_strategy_returns_empty_position(strategy: MentorStrategy) -> None:
    pos = await get_position(UserId(1), strategy)
    assert pos.available == []
    assert pos.locked == []
    assert pos.next_recommended is None
    assert pos.current_concept is None


# --- 등록된 fake reader 환경 -------------------------------------------------


class _FakeReader:
    """테스트용 stub. 등록 후 reader()가 이걸 반환하도록."""

    def __init__(self, tier: Tier, mastered: set[ConceptId]) -> None:
        self._tier = tier
        self._mastered = mastered

    async def get_user_tier(self, user_id: UserId) -> Tier:
        return self._tier

    async def get_mastered_concepts(
        self, user_id: UserId, strategy: MentorStrategy
    ) -> set[ConceptId]:
        return self._mastered

    async def get_tier_distribution(self) -> dict[Tier, int]:
        return {}


async def test_mastering_prereqs_unlocks_dependent_concept() -> None:
    # 주식(1)·매출과 이익(3) 마스터 → PER(5)의 prereq 충족 → available로 이동
    register_growth_reader(_FakeReader(Tier.T1, {ConceptId(1), ConceptId(3)}))
    pos = await get_position(UserId(1), MentorStrategy.VALUE)

    avail_ids = {c.id for c in pos.available}
    assert ConceptId(5) in avail_ids  # PER 잠금 해제
    # next_recommended는 mastered 제외하고 가장 앞 (4: 인플레이션, prereq=[])
    assert pos.next_recommended is not None
    assert pos.next_recommended.id not in {ConceptId(1), ConceptId(3)}


async def test_higher_tier_locks_t4_and_t5_even_with_all_prereqs() -> None:
    # T3 사용자 + T1~T3 전부 마스터해도 T4(20,21,22)·T5(23)는 티어 미달
    t1_t3_ids = {
        c.id
        for c in list_concepts_for_strategy(MentorStrategy.VALUE)
        if c.tier_required.value <= Tier.T3.value
    }
    register_growth_reader(_FakeReader(Tier.T3, t1_t3_ids))
    pos = await get_position(UserId(1), MentorStrategy.VALUE)

    locked_ids = {c.id for c in pos.locked}
    avail_ids = {c.id for c in pos.available}

    # T4, T5 — 티어 미충족
    for high_tier in (20, 21, 22, 23):
        assert ConceptId(high_tier) in locked_ids

    # T1~T3은 전부 available (prereq 충족됐고 티어 OK)
    assert t1_t3_ids.issubset(avail_ids)
    # 모두 마스터 끝났으니 next/current = None
    assert pos.next_recommended is None
    assert pos.current_concept is None


async def test_all_mastered_t5_user_next_is_none() -> None:
    all_value_ids = {c.id for c in list_concepts_for_strategy(MentorStrategy.VALUE)}
    register_growth_reader(_FakeReader(Tier.T5, all_value_ids))
    pos = await get_position(UserId(1), MentorStrategy.VALUE)

    assert len(pos.available) == 23
    assert pos.locked == []
    assert pos.next_recommended is None
    assert pos.current_concept is None


# --- API 응답 직렬화 안전성 (GET /curriculum/me) -----------------------------


async def test_position_is_json_serializable() -> None:
    """`CurriculumPosition`이 라우터 응답 모델로 쓰이므로 set/Concept 직렬화 검증."""
    pos = await get_position(UserId(1), MentorStrategy.VALUE)
    data = pos.model_dump(mode="json")

    # 기본 필드
    assert data["tier"] == "T1"
    # set은 JSON 응답에서 list로 직렬화 (JSON 표준에 set 타입 없음)
    assert isinstance(data["mastered"], list)
    assert isinstance(data["available"], list)
    assert isinstance(data["locked"], list)
    # Concept도 dict로 직렬화돼 키들이 정상 노출
    sample = data["available"][0]
    for key in ("id", "name", "tier_required", "prerequisites", "summary", "keywords"):
        assert key in sample
