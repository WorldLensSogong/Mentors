"""성장동 의존성을 학습동에서 끊는 fallback 레이어.

성장동(features/growth/)이 `register_growth_reader(impl)`를 호출해 구현체를
등록하면 진짜 GrowthReader가, 아직 등록 전이면 NullGrowthReader(모두 T1·
빈 마스터리)를 돌려준다. 학습동의 CurriculumService는 이 `reader()` 만 거치므로
성장동 출시 전/후로 학습동 코드는 한 줄도 변하지 않는다.

owner: learning
관련: docs/learning_curriculum_plan.md §2.1
"""

from core.contracts import ConceptId, MentorStrategy, Tier, UserId
from core.read_services import GrowthReader, get_growth_reader


class _NullGrowthReader:
    """성장동 미등록 상태의 더미. 모든 사용자를 T1·빈 마스터리로 본다.

    이 상태에서도 학습 흐름·UI·CurriculumService 로직은 완전히 검증 가능하다
    (T2~T5 개념은 항상 locked로 보임).
    """

    async def get_user_tier(self, user_id: UserId) -> Tier:
        return Tier.T1

    async def get_mastered_concepts(
        self, user_id: UserId, strategy: MentorStrategy
    ) -> set[ConceptId]:
        return set()

    async def get_tier_distribution(self) -> dict[Tier, int]:
        return {}


_NULL_READER: GrowthReader = _NullGrowthReader()


def reader() -> GrowthReader:
    """등록된 GrowthReader, 없으면 NullGrowthReader 반환.

    학습동의 모든 성장도 조회는 이 함수를 통한다. 직접
    `get_growth_reader()`를 호출하면 미등록 시 RuntimeError가 나므로 금지.
    """
    try:
        return get_growth_reader()
    except RuntimeError:
        return _NULL_READER


__all__ = ["reader"]
