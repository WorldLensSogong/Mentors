from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.contracts import (
    ConceptId,
    PromotionEligibleEvent,
    PromotionTestPassedEvent,
    PromotionTestStartedEvent,
    Tier,
    UserId,
)
from core.event_bus import event_bus
from core.exceptions import BadRequestError
from core.push import push
from core.user_context import user_context

from .catalog import get_concept_by_id, list_concepts_for_tier, list_promotion_questions
from .models import ConceptMastery, PromotionTestAttempt, TierState
from .schemas import (
    GrowthProgressResponse,
    PromotionTestChoiceResponse,
    PromotionTestPreviewResponse,
    PromotionTestQuestionResponse,
    PromotionTestRequest,
    PromotionTestResponse,
)

_PASSING_SCORE = 80
_USER_PROFILES = sa.table(
    "user_profiles",
    sa.column("user_id", sa.BigInteger),
    sa.column("current_tier", sa.String(10)),
)
_UNLOCKS_BY_TIER: dict[Tier, tuple[str, ...]] = {
    Tier.T1: (),
    Tier.T2: ("debate_arena",),
    Tier.T3: ("debate_arena", "extra_mentors"),
    Tier.T4: ("debate_arena", "extra_mentors"),
    Tier.T5: ("debate_arena", "extra_mentors"),
}


@dataclass(frozen=True)
class GrowthProgressSnapshot:
    current_tier: Tier
    mastered_concept_ids: frozenset[int]
    mastered_concepts: int
    total_concepts: int
    progress_percent: int
    eligible_for_promotion: bool


@dataclass(frozen=True)
class PromotionTestGrade:
    target_tier: Tier | None
    passed: bool
    correct_answers: int
    total_questions: int
    score_percent: int


def compute_progress(
    current_tier: Tier,
    mastered_concept_ids: set[int] | frozenset[int],
) -> GrowthProgressSnapshot:
    concept_ids = {concept.id for concept in list_concepts_for_tier(current_tier)}
    mastered = frozenset(sorted(concept_ids & set(mastered_concept_ids)))
    total = len(concept_ids)
    progress_percent = int((len(mastered) / total) * 100) if total else 0
    eligible = current_tier.next is not None and progress_percent >= _PASSING_SCORE
    return GrowthProgressSnapshot(
        current_tier=current_tier,
        mastered_concept_ids=mastered,
        mastered_concepts=len(mastered),
        total_concepts=total,
        progress_percent=progress_percent,
        eligible_for_promotion=eligible,
    )


def apply_concept_mastery(
    current_tier: Tier,
    mastered_concept_ids: set[int] | frozenset[int],
    concept_id: int,
) -> GrowthProgressSnapshot:
    concept = get_concept_by_id(concept_id)
    merged = set(mastered_concept_ids)
    if concept is not None and concept.id in {
        item.id for item in list_concepts_for_tier(current_tier)
    }:
        merged.add(concept_id)
    return compute_progress(current_tier, merged)


def get_unlocked_feature_codes(tier: Tier) -> list[str]:
    return list(_UNLOCKS_BY_TIER[tier])


def get_next_unlock_codes(tier: Tier) -> list[str]:
    next_tier = tier.next
    if next_tier is None:
        return []

    current_unlocks = set(_UNLOCKS_BY_TIER[tier])
    return [code for code in _UNLOCKS_BY_TIER[next_tier] if code not in current_unlocks]


def grade_promotion_test(current_tier: Tier, answers: dict[str, str]) -> PromotionTestGrade:
    questions = list_promotion_questions(current_tier)
    if not questions or current_tier.next is None:
        raise ValueError("Promotion test is not available for the current tier.")

    expected_ids = {question.id for question in questions}
    if set(answers) != expected_ids:
        raise ValueError("A complete answer set is required.")

    correct = sum(
        1 for question in questions if answers.get(question.id) == question.correct_choice_id
    )
    total = len(questions)
    score = int((correct / total) * 100) if total else 0
    return PromotionTestGrade(
        target_tier=current_tier.next,
        passed=score >= _PASSING_SCORE,
        correct_answers=correct,
        total_questions=total,
        score_percent=score,
    )


async def get_growth_progress(
    user_id: UserId,
    db: AsyncSession,
) -> GrowthProgressResponse:
    state, created = await _ensure_tier_state(db, user_id)
    current_tier = Tier(state.current_tier)
    mastered_ids = await _list_mastered_concept_ids(db, user_id, current_tier)
    snapshot = compute_progress(current_tier, mastered_ids)

    dirty = created or _sync_state_fields(state, snapshot)
    if dirty:
        await db.commit()

    return GrowthProgressResponse(
        current_tier=current_tier.value,
        next_tier=current_tier.next.value if current_tier.next else None,
        progress_percent=snapshot.progress_percent,
        mastered_concepts=snapshot.mastered_concepts,
        total_concepts=snapshot.total_concepts,
        eligible_for_promotion=snapshot.eligible_for_promotion,
        promotion_eligible_at=state.promotion_eligible_at,
        unlocked_features=get_unlocked_feature_codes(current_tier),
        next_unlocks=get_next_unlock_codes(current_tier),
        promotion_test=_build_promotion_test_preview(current_tier, snapshot),
    )


async def submit_promotion_test(
    user_id: UserId,
    payload: PromotionTestRequest,
    db: AsyncSession,
) -> PromotionTestResponse:
    state, _ = await _ensure_tier_state(db, user_id)
    current_tier = Tier(state.current_tier)
    mastered_ids = await _list_mastered_concept_ids(db, user_id, current_tier)
    snapshot = compute_progress(current_tier, mastered_ids)

    if current_tier.next is None:
        raise BadRequestError("You are already at the maximum tier.")
    if not snapshot.eligible_for_promotion:
        raise BadRequestError("Promotion test is not available yet.")

    answers = {answer.question_id: answer.choice_id for answer in payload.answers}
    if len(answers) != len(payload.answers):
        raise BadRequestError("Duplicate question answers are not allowed.")

    try:
        grade = grade_promotion_test(current_tier, answers)
    except ValueError as exc:
        raise BadRequestError(str(exc)) from exc

    now = datetime.now(UTC)
    state.last_promotion_attempt_at = now
    db.add(
        PromotionTestAttempt(
            user_id=int(user_id),
            current_tier=current_tier.value,
            target_tier=grade.target_tier.value if grade.target_tier else None,
            total_questions=grade.total_questions,
            correct_answers=grade.correct_answers,
            score_percent=grade.score_percent,
            passed=grade.passed,
            answers_json=json.dumps(answers, ensure_ascii=False, sort_keys=True),
        )
    )

    await event_bus.publish(
        PromotionTestStartedEvent(user_id=user_id, target_tier=current_tier.next or current_tier)
    )

    previous_tier = current_tier
    if grade.passed and grade.target_tier is not None:
        state.current_tier = grade.target_tier.value
        state.promotion_eligible_at = None
        _sync_state_fields(state, compute_progress(grade.target_tier, set()))
        await db.execute(
            sa.update(_USER_PROFILES)
            .where(_USER_PROFILES.c.user_id == int(user_id))
            .values(current_tier=grade.target_tier.value)
        )
        await event_bus.publish(
            PromotionTestPassedEvent(user_id=user_id, new_tier=grade.target_tier)
        )
        current_tier = grade.target_tier
    else:
        _sync_state_fields(state, snapshot)

    await db.commit()

    return PromotionTestResponse(
        previous_tier=previous_tier.value,
        current_tier=current_tier.value,
        target_tier=grade.target_tier.value if grade.target_tier else None,
        passed=grade.passed,
        score_percent=grade.score_percent,
        correct_answers=grade.correct_answers,
        total_questions=grade.total_questions,
        unlocked_features=get_unlocked_feature_codes(current_tier),
        message=(
            "Promotion test passed."
            if grade.passed
            else "Promotion test not passed. You can retry immediately."
        ),
    )


async def process_concept_mastered_event(
    user_id: UserId,
    concept_id: ConceptId,
    event_id: str,
    db: AsyncSession,
) -> None:
    state, _ = await _ensure_tier_state(db, user_id)
    current_tier = Tier(state.current_tier)
    concept = get_concept_by_id(int(concept_id))
    if concept is None:
        return
    if concept.id not in {item.id for item in list_concepts_for_tier(current_tier)}:
        return

    existing = await db.execute(
        select(ConceptMastery).where(
            ConceptMastery.user_id == int(user_id),
            ConceptMastery.concept_id == int(concept_id),
        )
    )
    if existing.scalar_one_or_none() is not None:
        return

    before = compute_progress(
        current_tier,
        await _list_mastered_concept_ids(db, user_id, current_tier),
    )

    db.add(
        ConceptMastery(
            user_id=int(user_id),
            tier=current_tier.value,
            concept_id=int(concept_id),
            source_event_id=event_id,
        )
    )
    await db.flush()

    after = compute_progress(
        current_tier,
        await _list_mastered_concept_ids(db, user_id, current_tier),
    )
    _sync_state_fields(state, after)

    crossed_threshold = (
        current_tier.next is not None
        and not before.eligible_for_promotion
        and after.eligible_for_promotion
        and state.promotion_eligible_at is None
    )
    if crossed_threshold:
        next_tier = current_tier.next
        assert next_tier is not None
        state.promotion_eligible_at = datetime.now(UTC)
        await event_bus.publish(PromotionEligibleEvent(user_id=user_id, current_tier=current_tier))
        await push.send_to_user(
            user_id=user_id,
            title="승급시험 응시 가능!",
            body=f"{next_tier.value}로 올라갈 준비가 되었어요.",
            data={"deeplink": "mentors://promotion-test"},
        )

    await db.commit()


def _build_promotion_test_preview(
    current_tier: Tier,
    snapshot: GrowthProgressSnapshot,
) -> PromotionTestPreviewResponse | None:
    questions = list_promotion_questions(current_tier)
    if not snapshot.eligible_for_promotion or current_tier.next is None or not questions:
        return None

    return PromotionTestPreviewResponse(
        target_tier=current_tier.next.value,
        question_count=len(questions),
        questions=[
            PromotionTestQuestionResponse(
                question_id=question.id,
                prompt=question.prompt,
                choices=[
                    PromotionTestChoiceResponse(choice_id=choice.id, text=choice.text)
                    for choice in question.choices
                ],
            )
            for question in questions
        ],
    )


def _sync_state_fields(state: TierState, snapshot: GrowthProgressSnapshot) -> bool:
    dirty = False
    updates = {
        "mastered_concepts": snapshot.mastered_concepts,
        "total_concepts": snapshot.total_concepts,
        "progress_percent": snapshot.progress_percent,
    }
    for field, value in updates.items():
        if getattr(state, field) != value:
            setattr(state, field, value)
            dirty = True
    return dirty


async def _ensure_tier_state(db: AsyncSession, user_id: UserId) -> tuple[TierState, bool]:
    state = await db.get(TierState, int(user_id))
    if state is not None:
        return state, False

    initial_tier = await user_context.get_tier(user_id)
    snapshot = compute_progress(initial_tier, set())
    state = TierState(
        user_id=int(user_id),
        current_tier=initial_tier.value,
        mastered_concepts=snapshot.mastered_concepts,
        total_concepts=snapshot.total_concepts,
        progress_percent=snapshot.progress_percent,
    )
    db.add(state)
    try:
        await db.flush()
        return state, True
    except IntegrityError:
        # A concurrent event handler may have inserted the initial tier state first.
        await db.rollback()
        state = await db.get(TierState, int(user_id))
        if state is None:
            raise
        return state, False


async def _list_mastered_concept_ids(
    db: AsyncSession,
    user_id: UserId,
    current_tier: Tier,
) -> set[int]:
    result = await db.execute(
        select(ConceptMastery.concept_id).where(
            ConceptMastery.user_id == int(user_id),
            ConceptMastery.tier == current_tier.value,
        )
    )
    return {int(concept_id) for concept_id in result.scalars().all()}


__all__ = [
    "GrowthProgressSnapshot",
    "PromotionTestGrade",
    "apply_concept_mastery",
    "compute_progress",
    "get_growth_progress",
    "get_next_unlock_codes",
    "get_unlocked_feature_codes",
    "grade_promotion_test",
    "process_concept_mastered_event",
    "submit_promotion_test",
]
