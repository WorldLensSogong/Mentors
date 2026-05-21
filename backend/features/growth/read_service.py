from __future__ import annotations

from sqlalchemy import func, select

from core.contracts import ConceptId, MentorStrategy, Tier, UserId
from core.db import SessionLocal
from core.user_context import user_context

from .models import ConceptMastery, TierState


class GrowthReadService:
    async def get_user_tier(self, user_id: UserId) -> Tier:
        async with SessionLocal() as session:
            state = await session.get(TierState, int(user_id))

        if state is not None:
            try:
                return Tier(state.current_tier)
            except ValueError:
                return Tier.T1

        return await user_context.get_tier(user_id)

    async def get_mastered_concepts(
        self,
        user_id: UserId,
        strategy: MentorStrategy,
    ) -> set[ConceptId]:
        if strategy is not MentorStrategy.VALUE:
            return set()

        async with SessionLocal() as session:
            result = await session.execute(
                select(ConceptMastery.concept_id).where(ConceptMastery.user_id == int(user_id))
            )

        return {ConceptId(int(concept_id)) for concept_id in result.scalars().all()}

    async def get_tier_distribution(self) -> dict[Tier, int]:
        async with SessionLocal() as session:
            result = await session.execute(
                select(TierState.current_tier, func.count(TierState.user_id)).group_by(
                    TierState.current_tier
                )
            )

        distribution: dict[Tier, int] = {}
        for tier_value, count in result.all():
            try:
                distribution[Tier(tier_value)] = int(count)
            except ValueError:
                continue
        return distribution


__all__ = ["GrowthReadService"]
