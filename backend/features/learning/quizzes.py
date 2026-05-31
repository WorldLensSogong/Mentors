from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession

from core.contracts import Tier, UserId
from core.user_context import user_context

from .concept_detector import recommend_quiz_for_text
from .models import LearningQuizProgress
from .tier_quizzes import TierQuiz, get_tier_quiz, get_tier_quiz_by_concept_index, list_tier_quizzes

logger = logging.getLogger("learning.quizzes")
_QUIZ_PROGRESS_TABLE_NAME = "learning_quiz_progress"


@dataclass(frozen=True)
class TierQuizState:
    quiz: TierQuiz
    attempted: bool
    solved: bool
    last_result_correct: bool | None


@dataclass(frozen=True)
class QuizSubmissionOutcome:
    quiz: TierQuiz
    correct: bool
    explanation: str


async def list_current_tier_quizzes(
    user_id: UserId,
    db: AsyncSession,
) -> tuple[Tier, list[TierQuizState]]:
    tier = await user_context.get_tier(user_id)
    quizzes = list_tier_quizzes(tier)
    progress_by_question_id = await _load_progress_by_question_id(db, user_id, tier)
    return (
        tier,
        [
            TierQuizState(
                quiz=quiz,
                attempted=quiz.question_id in progress_by_question_id,
                solved=progress_by_question_id.get(quiz.question_id).solved
                if quiz.question_id in progress_by_question_id
                else False,
                last_result_correct=progress_by_question_id.get(quiz.question_id).last_result_correct
                if quiz.question_id in progress_by_question_id
                else None,
            )
            for quiz in quizzes
        ],
    )


async def submit_tier_quiz(
    *,
    user_id: UserId,
    question_id: str,
    answer_index: int,
    db: AsyncSession,
) -> QuizSubmissionOutcome:
    quiz = get_tier_quiz(question_id)
    is_correct = quiz.correct_index == answer_index

    try:
        progress = await db.scalar(
            select(LearningQuizProgress).where(
                LearningQuizProgress.user_id == int(user_id),
                LearningQuizProgress.question_id == question_id,
            )
        )
        if progress is None:
            progress = LearningQuizProgress(
                user_id=int(user_id),
                question_id=quiz.question_id,
                concept_id=quiz.concept_id,
                tier=_resolve_tier_for_quiz(quiz).value,
                last_answer_index=answer_index,
                last_result_correct=is_correct,
                solved=is_correct,
            )
            db.add(progress)
        else:
            progress.last_answer_index = answer_index
            progress.last_result_correct = is_correct
            progress.solved = progress.solved or is_correct

        await db.flush()
    except ProgrammingError as exc:
        if not _is_missing_quiz_progress_table_error(exc):
            raise
        await db.rollback()
        logger.warning(
            "learning.quiz_progress_table_missing",
            extra={"user_id": user_id, "question_id": question_id},
        )

    return QuizSubmissionOutcome(
        quiz=quiz,
        correct=is_correct,
        explanation=quiz.explanation,
    )


async def recommend_tier_quiz_for_chat(
    *,
    user_id: UserId,
    tier: Tier,
    text: str,
    db: AsyncSession,
) -> TierQuiz | None:
    progress_by_question_id = await _load_progress_by_question_id(db, user_id, tier)
    solved_question_ids = {
        question_id
        for question_id, progress in progress_by_question_id.items()
        if progress.solved
    }
    return recommend_quiz_for_text(tier, text, solved_question_ids)


def serialize_tier_quiz_state(state: TierQuizState) -> dict[str, Any]:
    return serialize_tier_quiz(
        state.quiz,
        attempted=state.attempted,
        solved=state.solved,
        last_result_correct=state.last_result_correct,
    )


def serialize_tier_quiz(
    quiz: TierQuiz,
    *,
    attempted: bool = False,
    solved: bool = False,
    last_result_correct: bool | None = None,
) -> dict[str, Any]:
    return {
        "question_id": quiz.question_id,
        "concept_id": quiz.concept_id,
        "concept_name": quiz.concept_name,
        "quiz_index": quiz.quiz_index,
        "question": quiz.question,
        "options": [
            {"index": index, "text": text}
            for index, text in enumerate(quiz.options)
        ],
        "attempted": attempted,
        "solved": solved,
        "last_result_correct": last_result_correct,
    }


def resolve_question_id(
    *,
    question_id: str | None,
    concept_id: int | None,
    quiz_index: int | None,
) -> str:
    if question_id is not None:
        return get_tier_quiz(question_id).question_id
    if concept_id is None:
        raise ValueError("question_id 또는 concept_id가 필요합니다.")
    return get_tier_quiz_by_concept_index(concept_id, quiz_index or 0).question_id


async def _load_progress_by_question_id(
    db: AsyncSession,
    user_id: UserId,
    tier: Tier,
) -> dict[str, LearningQuizProgress]:
    try:
        result = await db.execute(
            select(LearningQuizProgress).where(
                LearningQuizProgress.user_id == int(user_id),
                LearningQuizProgress.tier == tier.value,
            )
        )
    except ProgrammingError as exc:
        if not _is_missing_quiz_progress_table_error(exc):
            raise
        await db.rollback()
        logger.warning(
            "learning.quiz_progress_table_missing",
            extra={"user_id": user_id, "tier": tier.value},
        )
        return {}
    return {item.question_id: item for item in result.scalars().all()}


def _resolve_tier_for_quiz(quiz: TierQuiz) -> Tier:
    for tier in Tier:
        if quiz in list_tier_quizzes(tier):
            return tier
    raise ValueError(f"Unknown tier quiz: {quiz.question_id}")


def _is_missing_quiz_progress_table_error(exc: ProgrammingError) -> bool:
    return _QUIZ_PROGRESS_TABLE_NAME in str(getattr(exc, "orig", exc))


__all__ = [
    "QuizSubmissionOutcome",
    "TierQuizState",
    "list_current_tier_quizzes",
    "recommend_tier_quiz_for_chat",
    "resolve_question_id",
    "serialize_tier_quiz",
    "serialize_tier_quiz_state",
    "submit_tier_quiz",
]
