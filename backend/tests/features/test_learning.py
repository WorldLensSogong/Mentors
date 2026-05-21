"""학습 동 단위 테스트 — 결정론적 로직만 (curriculum / personas / schemas).

DB·LLM·이벤트 버스 의존성 없음. SSE 스트리밍 및 라우터 통합 테스트는 별도.
"""

import pytest
from pydantic import ValidationError

from core.contracts import MentorStrategy
from core.exceptions import NotFoundError
from features.learning.curriculum import (
    get_concept,
    list_concepts_for_strategy,
)
from features.learning.personas import get_mentor_strategy, get_system_prompt
from features.learning.quizzes import get_quiz, grade_quiz
from features.learning.schemas import ChatStreamReq, SendMessageReq, SubmitQuizReq

# --- curriculum ---------------------------------------------------------------


@pytest.mark.parametrize(
    "concept_id, expected_name",
    [
        (1, "주식이란 무엇인가"),
        (5, "PER (주가수익비율)"),
        (6, "복리의 마법"),
        (8, "안전마진"),
        (23, "가치투자의 한계와 현대적 비판"),
    ],
)
def test_get_quiz_returns_catalogued_concept(concept_id: int, expected_name: str) -> None:
    quiz = get_quiz(concept_id)
    assert quiz.concept_id == concept_id
    assert quiz.concept_name == expected_name
    # 카탈로그 정합성: 모든 문항은 정확히 4지선다, 정답 인덱스가 옵션 범위 내
    assert len(quiz.options) == 4
    assert 0 <= quiz.correct_index < len(quiz.options)


def test_get_quiz_raises_not_found_for_unknown_concept() -> None:
    with pytest.raises(NotFoundError):
        get_quiz(999)


@pytest.mark.parametrize("concept_id", [1, 5, 8, 15, 23])
def test_grade_quiz_correct_index_returns_true(concept_id: int) -> None:
    quiz = get_quiz(concept_id)
    is_correct, explanation = grade_quiz(concept_id, quiz.correct_index)
    assert is_correct is True
    assert explanation  # 해설은 비어있지 않아야 함


def test_grade_quiz_wrong_index_returns_false_with_explanation() -> None:
    quiz = get_quiz(5)  # PER
    wrong_index = (quiz.correct_index + 1) % len(quiz.options)
    is_correct, explanation = grade_quiz(5, wrong_index)
    assert is_correct is False
    assert explanation == quiz.explanation


def test_grade_quiz_unknown_concept_raises() -> None:
    with pytest.raises(NotFoundError):
        grade_quiz(999, 0)


def test_value_strategy_has_seeded_concepts() -> None:
    # MVP 시드: VALUE만 채워져 있고 나머지 전략은 비어있다.
    value_concepts = list_concepts_for_strategy(MentorStrategy.VALUE)
    assert len(value_concepts) == 23

    # 정렬 보장: tier_required 오름차순
    tier_values = [c.tier_required.value for c in value_concepts]
    assert tier_values == sorted(tier_values)


@pytest.mark.parametrize(
    "strategy",
    [MentorStrategy.GROWTH, MentorStrategy.DIVIDEND, MentorStrategy.MOMENTUM],
)
def test_non_value_strategies_are_empty_in_mvp(strategy: MentorStrategy) -> None:
    assert list_concepts_for_strategy(strategy) == []


def test_prerequisite_graph_is_consistent() -> None:
    # 모든 prereq가 (1) 같은 전략의 (2) 실존하는 개념 id를 가리켜야 한다.
    value_concepts = list_concepts_for_strategy(MentorStrategy.VALUE)
    value_ids = {c.id for c in value_concepts}
    for c in value_concepts:
        for prereq_id in c.prerequisites:
            assert prereq_id in value_ids, (
                f"개념 {c.id}({c.name})의 선수 {prereq_id}가 VALUE 그래프에 없음"
            )
            prereq = get_concept(prereq_id)
            assert prereq.mentor_strategy == c.mentor_strategy
            # 선수의 티어는 본인보다 같거나 낮아야 한다 (역방향 의존 금지)
            assert prereq.tier_required.value <= c.tier_required.value


# --- personas -----------------------------------------------------------------


@pytest.mark.parametrize(
    "mentor_id, expected",
    [
        (1, MentorStrategy.VALUE),
        (2, MentorStrategy.GROWTH),
        (3, MentorStrategy.DIVIDEND),
        (4, MentorStrategy.MOMENTUM),
    ],
)
def test_mentor_id_maps_to_strategy(mentor_id: int, expected: MentorStrategy) -> None:
    assert get_mentor_strategy(mentor_id) == expected


def test_unknown_mentor_id_defaults_to_value() -> None:
    # 방어적 fallback — 알 수 없는 ID는 가치투자 페르소나
    assert get_mentor_strategy(999) == MentorStrategy.VALUE
    assert get_mentor_strategy(0) == MentorStrategy.VALUE


def test_each_strategy_returns_non_empty_system_prompt() -> None:
    prompts = [get_system_prompt(s) for s in MentorStrategy]
    # 모든 페르소나에 시스템 프롬프트가 있고
    assert all(p.strip() for p in prompts)
    # 네 페르소나의 프롬프트는 서로 달라야 한다 (= 페르소나가 실제로 분리되어 있음)
    assert len(set(prompts)) == len(prompts)


# --- schemas (Pydantic validation) --------------------------------------------


def test_send_message_rejects_empty_content() -> None:
    with pytest.raises(ValidationError):
        SendMessageReq(content="")


def test_send_message_rejects_overlong_content() -> None:
    with pytest.raises(ValidationError):
        SendMessageReq(content="x" * 2001)


def test_send_message_accepts_boundary_lengths() -> None:
    # 1자, 2000자 경계값 모두 허용
    SendMessageReq(content="a")
    SendMessageReq(content="a" * 2000)


def test_chat_stream_requires_both_session_id_and_content() -> None:
    with pytest.raises(ValidationError):
        ChatStreamReq(content="hello")  # type: ignore[call-arg]
    with pytest.raises(ValidationError):
        ChatStreamReq(session_id=1)  # type: ignore[call-arg]


def test_submit_quiz_accepts_int_indices() -> None:
    req = SubmitQuizReq(concept_id=1, answer_index=0)
    assert req.concept_id == 1
    assert req.answer_index == 0
