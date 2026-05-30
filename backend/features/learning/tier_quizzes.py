from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from core.contracts import Tier
from core.exceptions import NotFoundError
from features.growth.catalog import list_concepts_for_tier


@dataclass(frozen=True)
class TierQuiz:
    question_id: str
    concept_id: int
    concept_name: str
    quiz_index: int
    question: str
    options: tuple[str, ...]
    correct_index: int
    explanation: str


_TIER_QUIZ_COUNT = 10
_OPTIONS_PER_QUIZ = 4
_QUIZZES_PATH = Path(__file__).resolve().parent / "data" / "followup_quizzes.toml"
_QUIZZES_CACHE: dict[Tier, tuple[TierQuiz, ...]] | None = None
_QUIZZES_MTIME_NS: int | None = None


def list_tier_quizzes(tier: Tier) -> tuple[TierQuiz, ...]:
    return _load_tier_quizzes()[tier]


def get_tier_quiz(question_id: str) -> TierQuiz:
    for quizzes in _load_tier_quizzes().values():
        for quiz in quizzes:
            if quiz.question_id == question_id:
                return quiz
    raise NotFoundError("해당 팔로우업 퀴즈를 찾을 수 없습니다")


def get_tier_quiz_by_concept_index(concept_id: int, quiz_index: int) -> TierQuiz:
    for quizzes in _load_tier_quizzes().values():
        for quiz in quizzes:
            if quiz.concept_id == concept_id and quiz.quiz_index == quiz_index:
                return quiz
    raise NotFoundError("해당 개념의 팔로우업 퀴즈를 찾을 수 없습니다")


def _load_tier_quizzes() -> dict[Tier, tuple[TierQuiz, ...]]:
    global _QUIZZES_CACHE, _QUIZZES_MTIME_NS

    mtime_ns = _QUIZZES_PATH.stat().st_mtime_ns
    if _QUIZZES_CACHE is not None and _QUIZZES_MTIME_NS == mtime_ns:
        return _QUIZZES_CACHE

    with _QUIZZES_PATH.open("rb") as file:
        raw = tomllib.load(file)

    parsed = _parse_tier_quizzes(raw)
    _QUIZZES_CACHE = parsed
    _QUIZZES_MTIME_NS = mtime_ns
    return parsed


def _parse_tier_quizzes(raw: object) -> dict[Tier, tuple[TierQuiz, ...]]:
    if not isinstance(raw, dict):
        raise ValueError("Tier quiz TOML root must be a table.")

    tiers_raw = raw.get("tiers")
    if not isinstance(tiers_raw, dict):
        raise ValueError("Tier quiz TOML must define a [tiers] table.")

    parsed: dict[Tier, tuple[TierQuiz, ...]] = {}
    seen_question_ids: set[str] = set()

    for tier in Tier:
        tier_raw = tiers_raw.get(tier.value)
        if not isinstance(tier_raw, dict):
            raise ValueError(f"{tier.value} tier quizzes must be defined.")

        questions_raw = tier_raw.get("questions")
        if not isinstance(questions_raw, list):
            raise ValueError(f"{tier.value} questions must be provided as an array.")
        if len(questions_raw) != _TIER_QUIZ_COUNT:
            raise ValueError(f"{tier.value} must contain exactly {_TIER_QUIZ_COUNT} quizzes.")

        valid_concept_ids = {concept.id for concept in list_concepts_for_tier(tier)}
        concept_counts = {concept_id: 0 for concept_id in valid_concept_ids}
        quizzes: list[TierQuiz] = []

        for index, question_raw in enumerate(questions_raw, start=1):
            quiz = _parse_tier_quiz(
                tier=tier,
                raw=question_raw,
                index=index,
                valid_concept_ids=valid_concept_ids,
                concept_counts=concept_counts,
            )
            if quiz.question_id in seen_question_ids:
                raise ValueError(f"Duplicate tier quiz id found: {quiz.question_id}.")
            seen_question_ids.add(quiz.question_id)
            quizzes.append(quiz)

        if any(count != 2 for count in concept_counts.values()):
            raise ValueError(f"{tier.value} must define exactly two quizzes per concept.")

        parsed[tier] = tuple(quizzes)

    return parsed


def _parse_tier_quiz(
    *,
    tier: Tier,
    raw: object,
    index: int,
    valid_concept_ids: set[int],
    concept_counts: dict[int, int],
) -> TierQuiz:
    if not isinstance(raw, dict):
        raise ValueError(f"{tier.value} quiz #{index} must be a table.")

    question_id = _require_non_empty_str(raw.get("id"), f"{tier.value} quiz #{index} id")
    concept_id = _require_int(raw.get("concept_id"), f"{question_id} concept_id")
    if concept_id not in valid_concept_ids:
        raise ValueError(f"{question_id} concept_id must belong to {tier.value}.")

    concept_name = _require_non_empty_str(raw.get("concept_name"), f"{question_id} concept_name")
    question = _require_non_empty_str(raw.get("question"), f"{question_id} question")
    options = _parse_options(raw.get("options"), question_id)
    correct_index = _require_int(raw.get("correct_index"), f"{question_id} correct_index")
    if correct_index < 0 or correct_index >= len(options):
        raise ValueError(f"{question_id} correct_index must be within the options range.")

    explanation = _require_non_empty_str(raw.get("explanation"), f"{question_id} explanation")
    quiz_index = concept_counts[concept_id]
    concept_counts[concept_id] += 1

    return TierQuiz(
        question_id=question_id,
        concept_id=concept_id,
        concept_name=concept_name,
        quiz_index=quiz_index,
        question=question,
        options=options,
        correct_index=correct_index,
        explanation=explanation,
    )


def _parse_options(raw: object, question_id: str) -> tuple[str, ...]:
    if not isinstance(raw, list):
        raise ValueError(f"{question_id} options must be an array.")
    if len(raw) != _OPTIONS_PER_QUIZ:
        raise ValueError(f"{question_id} must contain exactly {_OPTIONS_PER_QUIZ} options.")

    options: list[str] = []
    for index, value in enumerate(raw, start=1):
        options.append(_require_non_empty_str(value, f"{question_id} option #{index}"))
    return tuple(options)


def _require_non_empty_str(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string.")
    return value.strip()


def _require_int(value: object, label: str) -> int:
    if not isinstance(value, int):
        raise ValueError(f"{label} must be an integer.")
    return value


__all__ = [
    "TierQuiz",
    "get_tier_quiz",
    "get_tier_quiz_by_concept_index",
    "list_tier_quizzes",
]
