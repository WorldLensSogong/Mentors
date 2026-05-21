"""학습 동 — chat_stream 커리큘럼 컨텍스트 주입 헬퍼 검증.

service.py의 비공개 헬퍼 `_select_active_concept`/`_build_curriculum_context`를
직접 호출해, 시스템 프롬프트에 어떤 단원 정보가 어떤 조건에서 들어가는지 확인.
SSE 스트리밍 자체는 DB·LLM·이벤트 버스 의존성으로 통합 테스트 부담이 커서 보류.
"""

import pytest

from core.contracts import ConceptId, MentorStrategy
from core.read_services import registry
from features.learning.curriculum import get_concept, get_position
from features.learning.service import (
    _build_curriculum_context,
    _pick_followup_concept,
    _select_active_concept,
)


@pytest.fixture(autouse=True)
def reset_growth_reader_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(registry, "_growth_reader", None)


# --- _build_curriculum_context ---------------------------------------------


def test_build_context_returns_empty_when_no_active() -> None:
    assert _build_curriculum_context(None, False) == ""
    # is_locked 값에 상관없이 None이면 빈 문자열
    assert _build_curriculum_context(None, True) == ""


def test_build_context_includes_unit_and_summary() -> None:
    per = get_concept(5)
    block = _build_curriculum_context(per, is_locked=False)
    assert "[현재 학습 단원] PER (주가수익비율)" in block
    assert "[요약]" in block
    assert "[학습 목표]" in block
    # 학습 목표 항목들이 bullet으로 들어가야 함
    for obj in per.learning_objectives:
        assert obj in block
    # 잠긴 단원 노트는 없어야 함
    assert "잠긴 단원" not in block


def test_build_context_appends_locked_notice() -> None:
    locked = get_concept(20)  # DCF (T4)
    block = _build_curriculum_context(locked, is_locked=True)
    assert "[현재 학습 단원] DCF 개념 이해" in block
    assert "잠긴 단원" in block
    assert "선수 개념" in block


# --- _select_active_concept ------------------------------------------------


async def test_select_active_falls_back_to_next_recommended() -> None:
    """매칭 키워드 없는 메시지 → position.next_recommended (= 주식)."""
    pos = await get_position(user_id=1, strategy=MentorStrategy.VALUE)  # type: ignore[arg-type]
    active, is_locked = _select_active_concept("안녕하세요", MentorStrategy.VALUE, pos)
    assert active is not None
    assert active.id == ConceptId(1)
    # 주식(1)은 prereq=[]이라 더미 환경(T1·빈셋)에서 available → not locked
    assert is_locked is False


async def test_select_active_uses_detector_match() -> None:
    """메시지 키워드가 있으면 detector 결과 우선."""
    pos = await get_position(user_id=1, strategy=MentorStrategy.VALUE)  # type: ignore[arg-type]
    active, _is_locked = _select_active_concept("PER이 뭐야?", MentorStrategy.VALUE, pos)
    assert active is not None
    assert active.id == ConceptId(5)


async def test_select_active_flags_locked_when_prereq_unmet() -> None:
    """PER(5)는 prereq=[1,3] — 더미 환경에서 mastered 빈셋이므로 locked."""
    pos = await get_position(user_id=1, strategy=MentorStrategy.VALUE)  # type: ignore[arg-type]
    active, is_locked = _select_active_concept("PER 알려줘", MentorStrategy.VALUE, pos)
    assert active is not None
    assert active.id == ConceptId(5)
    assert is_locked is True


async def test_select_active_unlocked_when_prereq_free() -> None:
    """복리(6)는 prereq=[] — 더미 환경에서도 available, not locked."""
    pos = await get_position(user_id=1, strategy=MentorStrategy.VALUE)  # type: ignore[arg-type]
    active, is_locked = _select_active_concept("복리에 대해 설명해줘", MentorStrategy.VALUE, pos)
    assert active is not None
    assert active.id == ConceptId(6)
    assert is_locked is False


async def test_select_active_returns_none_for_empty_strategy() -> None:
    """시드 비어있는 GROWTH 전략 → active None."""
    pos = await get_position(user_id=1, strategy=MentorStrategy.GROWTH)  # type: ignore[arg-type]
    active, is_locked = _select_active_concept("성장주 어떻게 골라", MentorStrategy.GROWTH, pos)
    assert active is None
    assert is_locked is False


# --- _pick_followup_concept (fallback 없는 트리거 선정) ----------------------


def test_followup_from_user_message() -> None:
    """사용자 메시지에 키워드 → 그 개념."""
    target = _pick_followup_concept(
        user_message="PER이 뭐야?",
        mentor_answer="PER은 ...",
        strategy=MentorStrategy.VALUE,
    )
    assert target is not None
    assert target.id == ConceptId(5)


def test_followup_from_mentor_answer_when_user_has_no_keyword() -> None:
    """사용자 메시지에 키워드 없고 멘토 응답에만 있으면 멘토에서 감지."""
    target = _pick_followup_concept(
        user_message="투자 좀 알려줘",
        mentor_answer="투자의 기초로 PER이라는 지표가 있어요.",
        strategy=MentorStrategy.VALUE,
    )
    assert target is not None
    assert target.id == ConceptId(5)


def test_followup_returns_none_when_no_keyword_anywhere() -> None:
    """사용자도 멘토도 키워드 없으면 None — 퀴즈 버튼 안 뜸."""
    target = _pick_followup_concept(
        user_message="안녕하세요",
        mentor_answer="네 안녕하세요. 무엇을 도와드릴까요?",
        strategy=MentorStrategy.VALUE,
    )
    assert target is None


def test_followup_user_takes_precedence_over_mentor() -> None:
    """사용자 메시지에 매칭이 있으면 멘토 응답의 다른 키워드는 무시."""
    target = _pick_followup_concept(
        user_message="복리 알려줘",
        mentor_answer="복리는 PER과 다른 개념인데요...",  # PER도 매칭되지만 무시
        strategy=MentorStrategy.VALUE,
    )
    assert target is not None
    assert target.id == ConceptId(6)  # 복리


def test_followup_returns_none_for_empty_strategy() -> None:
    """시드 빈 전략은 매칭될 후보 자체가 없음 → None."""
    target = _pick_followup_concept(
        user_message="성장주 PER 이런 거",
        mentor_answer="설명할게요",
        strategy=MentorStrategy.GROWTH,
    )
    assert target is None
