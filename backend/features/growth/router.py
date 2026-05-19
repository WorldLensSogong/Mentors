"""3동 — 성장 (티어·승급시험·이해도 게이지)."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.dependencies import get_current_user
from core.auth.models import User
from core.contracts import Tier, UserId
from core.db import get_db
from core.user_context import user_context

from .schemas import GrowthProgressResponse, PromotionTestRequest, PromotionTestResponse
from .service import get_growth_progress, submit_promotion_test

router = APIRouter(prefix="/api/growth", tags=["growth"])


@router.get("/me/tier")
async def my_tier(user: User = Depends(get_current_user)) -> dict[str, str]:
    tier: Tier = await user_context.get_tier(UserId(user.id))
    return {"tier": tier.value, "next": tier.next.value if tier.next else "max"}


@router.get("/me/progress", response_model=GrowthProgressResponse)
async def progress(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GrowthProgressResponse:
    return await get_growth_progress(UserId(user.id), db)


@router.post("/promotion-test", response_model=PromotionTestResponse)
async def promotion_test(
    payload: PromotionTestRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PromotionTestResponse:
    return await submit_promotion_test(UserId(user.id), payload, db)
