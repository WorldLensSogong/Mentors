import pytest
from sqlalchemy.exc import IntegrityError

from core.contracts import Tier, UserId
from features.growth.models import TierState
from features.growth.service import (
    _ensure_tier_state,
    apply_concept_mastery,
    compute_progress,
    get_next_unlock_codes,
    get_unlocked_feature_codes,
    grade_promotion_test,
)


def test_compute_progress_marks_eligible_at_eighty_percent() -> None:
    snapshot = compute_progress(Tier.T1, {1, 2, 3, 4, 5, 6, 7})

    assert snapshot.mastered_concepts == 7
    assert snapshot.total_concepts == 8
    assert snapshot.progress_percent == 87
    assert snapshot.eligible_for_promotion is True


def test_apply_concept_mastery_is_idempotent_for_duplicate_concept() -> None:
    once = apply_concept_mastery(Tier.T2, {9, 10, 11, 12}, 13)
    twice = apply_concept_mastery(Tier.T2, once.mastered_concept_ids, 13)

    assert once.mastered_concepts == 5
    assert twice.mastered_concepts == 5
    assert twice.progress_percent == 83


def test_grade_promotion_test_passes_at_eighty_percent() -> None:
    grade = grade_promotion_test(
        Tier.T1,
        {
            "t1-q1": "A",
            "t1-q2": "B",
            "t1-q3": "C",
            "t1-q4": "A",
            "t1-q5": "C",
        },
    )

    assert grade.passed is True
    assert grade.correct_answers == 4
    assert grade.total_questions == 5
    assert grade.score_percent == 80


def test_grade_promotion_test_fails_below_eighty_percent() -> None:
    grade = grade_promotion_test(
        Tier.T2,
        {
            "t2-q1": "A",
            "t2-q2": "B",
            "t2-q3": "B",
            "t2-q4": "B",
            "t2-q5": "C",
        },
    )

    assert grade.passed is False
    assert grade.correct_answers == 3
    assert grade.score_percent == 60


def test_get_unlocked_feature_codes_unlocks_debate_and_extra_mentors() -> None:
    assert get_unlocked_feature_codes(Tier.T1) == []
    assert get_unlocked_feature_codes(Tier.T2) == ["debate_arena"]
    assert get_unlocked_feature_codes(Tier.T3) == ["debate_arena", "extra_mentors"]
    assert get_next_unlock_codes(Tier.T1) == ["debate_arena"]
    assert get_next_unlock_codes(Tier.T2) == ["extra_mentors"]


def test_grade_promotion_test_requires_complete_answer_set() -> None:
    with pytest.raises(ValueError):
        grade_promotion_test(
            Tier.T1,
            {
                "t1-q1": "A",
                "t1-q2": "B",
            },
        )


@pytest.mark.asyncio
async def test_ensure_tier_state_recovers_from_concurrent_insert(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    persisted_state = TierState(
        user_id=999,
        current_tier=Tier.T1.value,
        mastered_concepts=0,
        total_concepts=5,
        progress_percent=0,
    )

    class _FakeSession:
        def __init__(self) -> None:
            self.rollback_count = 0
            self.state: TierState | None = None

        async def get(self, _model: object, _pk: int) -> TierState | None:
            return self.state

        def add(self, _obj: object) -> None:
            return None

        async def flush(self) -> None:
            raise IntegrityError("insert", {}, Exception("duplicate"))

        async def rollback(self) -> None:
            self.rollback_count += 1
            self.state = persisted_state

    async def fake_get_tier(_user_id: UserId) -> Tier:
        return Tier.T1

    monkeypatch.setattr("features.growth.service.user_context.get_tier", fake_get_tier)

    fake_db = _FakeSession()
    state, created = await _ensure_tier_state(fake_db, UserId(999))

    assert created is False
    assert state is persisted_state
    assert fake_db.rollback_count == 1
