"""학습 동 — concept_detector 키워드 매칭 v1 검증.

VALUE 23개념 시드 위에서 다양한 사용자 메시지가 어떤 개념으로 매핑되는지
케이스별로 확인. v1 휴리스틱이라 100% 정확하진 않아도 명백한 단일 키워드
질문은 정확히 잡아야 한다.
"""

import pytest

from core.contracts import ConceptId, MentorStrategy
from features.learning.concept_detector import detect_concept
from features.learning.curriculum import Concept, list_concepts_for_strategy


@pytest.fixture
def value_candidates() -> list[Concept]:
    return list_concepts_for_strategy(MentorStrategy.VALUE)


# --- 단일 키워드 명확한 매칭 ---


@pytest.mark.parametrize(
    "message, expected_id",
    [
        ("PER이 뭐야?", 5),
        ("복리에 대해 알려줘", 6),
        ("안전마진이란?", 8),
        ("DCF는 어떻게 계산해", 20),
        ("FCF가 무엇인가요", 16),
        ("경제적 해자가 뭔지", 12),
    ],
)
def test_detect_single_keyword(
    message: str, expected_id: int, value_candidates: list[Concept]
) -> None:
    result = detect_concept(message, value_candidates)
    assert result is not None
    assert result.id == ConceptId(expected_id)


# --- 빈 입력 / 매칭 없음 ---


def test_empty_message_returns_none(value_candidates: list[Concept]) -> None:
    assert detect_concept("", value_candidates) is None
    assert detect_concept("   ", value_candidates) is None


def test_message_without_keywords_returns_none(value_candidates: list[Concept]) -> None:
    assert detect_concept("안녕하세요 멘토님", value_candidates) is None
    assert detect_concept("오늘 날씨가 좋네요", value_candidates) is None


def test_empty_candidates_returns_none() -> None:
    assert detect_concept("PER이 뭐야?", []) is None


# --- 동점 처리: id 오름차순 ---


def test_tiebreak_prefers_lower_id(value_candidates: list[Concept]) -> None:
    """주식(1)과 채권/주식(2) 둘 다 매칭 — id 오름차순으로 주식(1) 선택."""
    # "주식" 키워드는 concept 1에 있고, "채권" 키워드는 concept 2에 있음.
    # 메시지에 둘 다 등장하면 두 concept 모두 점수 1 → id 오름차순 → 1
    result = detect_concept("주식과 채권의 차이가 뭐야?", value_candidates)
    assert result is not None
    assert result.id == ConceptId(1)


# --- 다중 키워드 매칭 우위 ---


def test_more_keyword_matches_wins(value_candidates: list[Concept]) -> None:
    """한 concept의 키워드가 메시지에 여러 번 등장하면 우위."""
    # concept 5 (PER) keywords: ["PER", "주가수익비율", "EPS"]
    # 메시지에 "PER"과 "주가수익비율" 둘 다 등장 → 점수 2
    # concept 1 (주식) keywords에서 매칭은 0
    result = detect_concept("PER 즉 주가수익비율이 뭐야?", value_candidates)
    assert result is not None
    assert result.id == ConceptId(5)


# --- 대소문자 무시 ---


def test_case_insensitive_matching(value_candidates: list[Concept]) -> None:
    """영문 키워드는 대소문자 무시."""
    upper = detect_concept("ROE가 뭐야", value_candidates)
    lower = detect_concept("roe가 뭐야", value_candidates)
    mixed = detect_concept("Roe가 뭐야", value_candidates)
    assert upper is not None
    assert lower is not None
    assert mixed is not None
    assert upper.id == lower.id == mixed.id == ConceptId(10)
