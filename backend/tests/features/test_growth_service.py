import pytest

from core.contracts import Tier
from features.growth.service import (
    apply_concept_mastery,
    compute_progress,
    get_next_unlock_codes,
    get_unlocked_feature_codes,
    grade_promotion_test,
)


def test_compute_progress_marks_eligible_at_eighty_percent() -> None:
    snapshot = compute_progress(Tier.T1, {101, 102, 103, 104})

    assert snapshot.mastered_concepts == 4
    assert snapshot.total_concepts == 5
    assert snapshot.progress_percent == 80
    assert snapshot.eligible_for_promotion is True


def test_apply_concept_mastery_is_idempotent_for_duplicate_concept() -> None:
    once = apply_concept_mastery(Tier.T2, {201, 202, 203}, 204)
    twice = apply_concept_mastery(Tier.T2, once.mastered_concept_ids, 204)

    assert once.mastered_concepts == 4
    assert twice.mastered_concepts == 4
    assert twice.progress_percent == 80


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
