"""3동 — 성장 (티어·승급시험·이해도 게이지)."""

import json
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.dependencies import get_current_user
from core.auth.models import User
from core.contracts import Tier, UserId
from core.db import get_db
from core.user_context import user_context

from .catalog import list_promotion_questions
from .models import PromotionTestAttempt
from .schemas import GrowthProgressResponse, PromotionTestRequest, PromotionTestResponse
from .service import get_growth_progress, submit_promotion_test

router = APIRouter(prefix="/api/growth", tags=["growth"])


class PromotionQuestionResult(BaseModel):
    question_id: str
    prompt: str
    user_choice_id: str
    correct_choice_id: str
    is_correct: bool
    choices: dict[str, str]


class PromotionAttemptDetail(BaseModel):
    id: int
    current_tier: str
    target_tier: str | None
    total_questions: int
    correct_answers: int
    score_percent: int
    passed: bool
    attempted_at: str
    question_results: list[PromotionQuestionResult]


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


@router.get("/me/promotion-history", response_model=list[PromotionAttemptDetail])
async def promotion_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[PromotionAttemptDetail]:
    """최근 승급시험 응시 이력 (최대 10건, 최신순)."""
    result = await db.execute(
        select(PromotionTestAttempt)
        .where(PromotionTestAttempt.user_id == user.id)
        .order_by(PromotionTestAttempt.attempted_at.desc())
        .limit(10)
    )
    attempts = result.scalars().all()

    details: list[PromotionAttemptDetail] = []
    for attempt in attempts:
        try:
            tier = Tier(attempt.current_tier)
            questions = list_promotion_questions(tier)
            answers: dict[str, str] = json.loads(attempt.answers_json)
        except Exception:
            questions = ()
            answers = {}

        question_results: list[PromotionQuestionResult] = []
        for q in questions:
            user_choice = answers.get(q.id, "")
            question_results.append(
                PromotionQuestionResult(
                    question_id=q.id,
                    prompt=q.prompt,
                    user_choice_id=user_choice,
                    correct_choice_id=q.correct_choice_id,
                    is_correct=user_choice == q.correct_choice_id,
                    choices={c.id: c.text for c in q.choices},
                )
            )

        details.append(
            PromotionAttemptDetail(
                id=attempt.id,
                current_tier=attempt.current_tier,
                target_tier=attempt.target_tier,
                total_questions=attempt.total_questions,
                correct_answers=attempt.correct_answers,
                score_percent=attempt.score_percent,
                passed=attempt.passed,
                attempted_at=attempt.attempted_at.isoformat(),
                question_results=question_results,
            )
        )

    return details
