from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from core.contracts import Tier


@dataclass(frozen=True)
class TierConcept:
    id: int
    code: str
    title: str


@dataclass(frozen=True)
class PromotionChoice:
    id: str
    text: str


@dataclass(frozen=True)
class PromotionQuestion:
    id: str
    concept_id: int
    prompt: str
    choices: tuple[PromotionChoice, ...]
    correct_choice_id: str
    source_question_id: str | None = None
    is_application: bool = False


_PROMOTION_QUESTION_COUNT = 10
_PROMOTION_REUSE_COUNT = 8
_PROMOTION_APPLICATION_COUNT = 2
_PROMOTION_CHOICE_IDS = ("A", "B", "C", "D")
_PROMOTION_QUESTIONS_PATH = Path(__file__).resolve().parent / "data" / "promotion_questions.toml"
_PROMOTION_QUESTIONS_CACHE: dict[Tier, tuple[PromotionQuestion, ...]] | None = None
_PROMOTION_QUESTIONS_MTIME_NS: int | None = None


_TIER_CONCEPTS: dict[Tier, tuple[TierConcept, ...]] = {
    Tier.T1: (
        TierConcept(101, "margin_of_safety", "안전마진"),
        TierConcept(102, "intrinsic_value", "내재가치"),
        TierConcept(103, "long_term_horizon", "장기투자"),
        TierConcept(104, "volatility_vs_risk", "변동성과 위험"),
        TierConcept(105, "business_quality", "좋은 사업"),
    ),
    Tier.T2: (
        TierConcept(201, "debate_tradeoff", "장단점 비교"),
        TierConcept(202, "counter_argument", "반대 의견 점검"),
        TierConcept(203, "position_sizing", "비중 조절"),
        TierConcept(204, "portfolio_balance", "포트폴리오 균형"),
        TierConcept(205, "thesis_consistency", "투자 논리 점검"),
    ),
    Tier.T3: (
        TierConcept(301, "mentor_diversity", "다양한 관점 비교"),
        TierConcept(302, "sector_rotation", "섹터 순환"),
        TierConcept(303, "macro_filtering", "매크로 필터"),
        TierConcept(304, "scenario_mapping", "시나리오 설계"),
        TierConcept(305, "allocation_discipline", "자산 배분 규율"),
    ),
    Tier.T4: (
        TierConcept(401, "rate_sensitivity", "금리 민감도"),
        TierConcept(402, "macro_regime", "매크로 국면 판단"),
        TierConcept(403, "earnings_quality", "이익의 질"),
        TierConcept(404, "stress_testing", "스트레스 테스트"),
        TierConcept(405, "cross_cycle_judgment", "사이클 종합 판단"),
    ),
    Tier.T5: (
        TierConcept(501, "independent_thesis", "독립적인 투자 논리"),
        TierConcept(502, "framework_composition", "프레임워크 조합"),
        TierConcept(503, "risk_governance", "리스크 거버넌스"),
        TierConcept(504, "market_context_synthesis", "시장 맥락 종합"),
        TierConcept(505, "self_directed_reflection", "자기 점검"),
    ),
}


def list_concepts_for_tier(tier: Tier) -> tuple[TierConcept, ...]:
    return _TIER_CONCEPTS[tier]


def list_promotion_questions(tier: Tier) -> tuple[PromotionQuestion, ...]:
    return _load_promotion_questions()[tier]


def get_concept_by_id(concept_id: int) -> TierConcept | None:
    for concepts in _TIER_CONCEPTS.values():
        for concept in concepts:
            if concept.id == concept_id:
                return concept
    return None


def _load_promotion_questions() -> dict[Tier, tuple[PromotionQuestion, ...]]:
    global _PROMOTION_QUESTIONS_CACHE, _PROMOTION_QUESTIONS_MTIME_NS

    mtime_ns = _PROMOTION_QUESTIONS_PATH.stat().st_mtime_ns
    if (
        _PROMOTION_QUESTIONS_CACHE is not None
        and _PROMOTION_QUESTIONS_MTIME_NS == mtime_ns
    ):
        return _PROMOTION_QUESTIONS_CACHE

    with _PROMOTION_QUESTIONS_PATH.open("rb") as file:
        raw = tomllib.load(file)

    parsed = _parse_promotion_questions(raw)
    _PROMOTION_QUESTIONS_CACHE = parsed
    _PROMOTION_QUESTIONS_MTIME_NS = mtime_ns
    return parsed


def _parse_promotion_questions(raw: object) -> dict[Tier, tuple[PromotionQuestion, ...]]:
    if not isinstance(raw, dict):
        raise ValueError("Promotion question TOML root must be a table.")

    tiers_raw = raw.get("tiers")
    if not isinstance(tiers_raw, dict):
        raise ValueError("Promotion question TOML must define a [tiers] table.")

    parsed: dict[Tier, tuple[PromotionQuestion, ...]] = {}
    for tier in Tier:
        tier_raw = tiers_raw.get(tier.value)
        if not isinstance(tier_raw, dict):
            raise ValueError(f"{tier.value} promotion questions must be defined.")

        questions = tuple(_build_promotion_questions_for_tier(tier, tier_raw))
        ids = [question.id for question in questions]
        if len(ids) != len(set(ids)):
            raise ValueError(f"{tier.value} contains duplicate question ids.")

        parsed[tier] = questions

    return parsed


def _build_promotion_questions_for_tier(
    tier: Tier,
    tier_raw: dict[str, object],
) -> list[PromotionQuestion]:
    from features.learning.tier_quizzes import list_tier_quizzes

    valid_concept_ids = {concept.id for concept in list_concepts_for_tier(tier)}
    tier_quizzes = {quiz.question_id: quiz for quiz in list_tier_quizzes(tier)}

    reuse_ids = tier_raw.get("reuse_question_ids")
    if not isinstance(reuse_ids, list):
        raise ValueError(f"{tier.value} reuse_question_ids must be provided as an array.")
    if len(reuse_ids) != _PROMOTION_REUSE_COUNT:
        raise ValueError(
            f"{tier.value} must reuse exactly {_PROMOTION_REUSE_COUNT} follow-up quizzes."
        )

    questions: list[PromotionQuestion] = []
    for raw_id in reuse_ids:
        reuse_id = _require_non_empty_str(raw_id, f"{tier.value} reuse_question_id")
        follow_up_quiz = tier_quizzes.get(reuse_id)
        if follow_up_quiz is None:
            raise ValueError(
                f"{tier.value} reuse question {reuse_id} must exist in follow-up quizzes."
            )
        questions.append(_promotion_question_from_follow_up(follow_up_quiz))

    application_questions_raw = tier_raw.get("applied_questions")
    if not isinstance(application_questions_raw, list):
        raise ValueError(f"{tier.value} applied_questions must be provided as an array.")
    if len(application_questions_raw) != _PROMOTION_APPLICATION_COUNT:
        raise ValueError(
            f"{tier.value} must define exactly "
            f"{_PROMOTION_APPLICATION_COUNT} application questions."
        )

    for index, raw_question in enumerate(application_questions_raw, start=1):
        question = _parse_promotion_question(
            tier=tier,
            raw=raw_question,
            index=index,
            valid_concept_ids=valid_concept_ids,
        )
        questions.append(question)

    if len(questions) != _PROMOTION_QUESTION_COUNT:
        raise ValueError(
            f"{tier.value} must contain exactly {_PROMOTION_QUESTION_COUNT} questions."
        )

    return questions


def _promotion_question_from_follow_up(question: object) -> PromotionQuestion:
    from features.learning.tier_quizzes import TierQuiz

    if not isinstance(question, TierQuiz):
        raise ValueError("Follow-up quiz must be a TierQuiz instance.")

    return PromotionQuestion(
        id=question.question_id,
        concept_id=question.concept_id,
        prompt=question.question,
        choices=tuple(
            PromotionChoice(id=choice_id, text=text)
            for choice_id, text in zip(_PROMOTION_CHOICE_IDS, question.options, strict=True)
        ),
        correct_choice_id=_PROMOTION_CHOICE_IDS[question.correct_index],
        source_question_id=question.question_id,
        is_application=False,
    )


def _parse_promotion_question(
    *,
    tier: Tier,
    raw: object,
    index: int,
    valid_concept_ids: set[int],
) -> PromotionQuestion:
    if not isinstance(raw, dict):
        raise ValueError(f"{tier.value} question #{index} must be a table.")

    question_id = _require_non_empty_str(raw.get("id"), f"{tier.value} question #{index} id")
    concept_id = _require_int(raw.get("concept_id"), f"{question_id} concept_id")
    if concept_id not in valid_concept_ids:
        raise ValueError(f"{question_id} concept_id must belong to {tier.value}.")
    prompt = _require_non_empty_str(raw.get("prompt"), f"{question_id} prompt")
    correct_choice_id = _require_non_empty_str(
        raw.get("correct_choice_id"),
        f"{question_id} correct_choice_id",
    )
    choices_raw = raw.get("choices")
    if not isinstance(choices_raw, dict):
        raise ValueError(f"{question_id} choices must be a table.")

    choice_keys = tuple(sorted(choices_raw.keys()))
    if choice_keys != _PROMOTION_CHOICE_IDS:
        raise ValueError(
            f"{question_id} choices must define exactly {_PROMOTION_CHOICE_IDS}."
        )
    if correct_choice_id not in choices_raw:
        raise ValueError(f"{question_id} correct_choice_id must match one of the choices.")

    choices = tuple(
        PromotionChoice(
            id=choice_id,
            text=_require_non_empty_str(
                choices_raw.get(choice_id),
                f"{question_id} choice {choice_id}",
            ),
        )
        for choice_id in _PROMOTION_CHOICE_IDS
    )
    return PromotionQuestion(
        id=question_id,
        concept_id=concept_id,
        prompt=prompt,
        choices=choices,
        correct_choice_id=correct_choice_id,
        is_application=True,
    )


def _require_non_empty_str(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string.")
    return value.strip()


def _require_int(value: object, label: str) -> int:
    if not isinstance(value, int):
        raise ValueError(f"{label} must be an integer.")
    return value


__all__ = [
    "PromotionChoice",
    "PromotionQuestion",
    "TierConcept",
    "get_concept_by_id",
    "list_concepts_for_tier",
    "list_promotion_questions",
]
