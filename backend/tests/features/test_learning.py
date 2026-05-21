"""학습 순수 단위 테스트: 결정론적 로직만 검증한다."""

import pytest
from pydantic import ValidationError

from core.contracts import MentorStrategy
from core.exceptions import NotFoundError
from features.learning.curriculum import get_concept, list_concepts_for_strategy
from features.learning.personas import get_mentor_strategy, get_system_prompt
from features.learning.quizzes import get_quiz, grade_quiz
from features.learning.schemas import ChatStreamReq, SendMessageReq, SubmitQuizReq


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
    assert explanation


def test_grade_quiz_wrong_index_returns_false_with_explanation() -> None:
    quiz = get_quiz(5)
    wrong_index = (quiz.correct_index + 1) % len(quiz.options)
    is_correct, explanation = grade_quiz(5, wrong_index)
    assert is_correct is False
    assert explanation == quiz.explanation


def test_grade_quiz_unknown_concept_raises() -> None:
    with pytest.raises(NotFoundError):
        grade_quiz(999, 0)


def test_value_strategy_has_seeded_concepts() -> None:
    value_concepts = list_concepts_for_strategy(MentorStrategy.VALUE)
    assert len(value_concepts) == 23

    tier_values = [concept.tier_required.value for concept in value_concepts]
    assert tier_values == sorted(tier_values)


@pytest.mark.parametrize(
    "strategy",
    [MentorStrategy.GROWTH, MentorStrategy.DIVIDEND, MentorStrategy.MOMENTUM],
)
def test_non_value_strategies_are_empty_in_mvp(strategy: MentorStrategy) -> None:
    assert list_concepts_for_strategy(strategy) == []


def test_prerequisite_graph_is_consistent() -> None:
    value_concepts = list_concepts_for_strategy(MentorStrategy.VALUE)
    value_ids = {concept.id for concept in value_concepts}
    for concept in value_concepts:
        for prereq_id in concept.prerequisites:
            assert prereq_id in value_ids
            prereq = get_concept(prereq_id)
            assert prereq.mentor_strategy == concept.mentor_strategy
            assert prereq.tier_required.value <= concept.tier_required.value


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
    assert get_mentor_strategy(999) == MentorStrategy.VALUE
    assert get_mentor_strategy(0) == MentorStrategy.VALUE


def test_each_strategy_returns_non_empty_system_prompt() -> None:
    prompts = [get_system_prompt(strategy) for strategy in MentorStrategy]
    assert all(prompt.strip() for prompt in prompts)
    assert len(set(prompts)) == len(prompts)


def test_send_message_rejects_empty_content() -> None:
    with pytest.raises(ValidationError):
        SendMessageReq(content="")


def test_send_message_rejects_overlong_content() -> None:
    with pytest.raises(ValidationError):
        SendMessageReq(content="x" * 2001)


def test_send_message_accepts_boundary_lengths() -> None:
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
    assert req.quiz_index == 0
