from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.user import OnboardingSurveyAnswer, User, UserInterestTopic, UserProfile
from app.repositories.mentor_repository import get_level_one, list_recommendation_candidates
from app.repositories.user_repository import ensure_user_not_exists, get_topics_by_codes
from app.schemas.mentor import RecommendedMentorSummary
from app.schemas.onboarding import OnboardingRequest, OnboardingResult

RISK_TOLERANCE_MAP = {
    "안정형": "STABLE",
    "중립형": "BALANCED",
    "공격형": "AGGRESSIVE",
    "STABLE": "STABLE",
    "BALANCED": "BALANCED",
    "AGGRESSIVE": "AGGRESSIVE",
}


def create_onboarding_result(db: Session, payload: OnboardingRequest) -> OnboardingResult:
    ensure_user_not_exists(db, email=payload.email, nickname=payload.nickname)

    current_level = get_level_one(db)
    risk_tag = RISK_TOLERANCE_MAP.get(payload.risk_tolerance or "")

    user = User(email=payload.email, nickname=payload.nickname)
    db.add(user)
    db.flush()

    topics = get_topics_by_codes(db, payload.interest_topic_codes)
    recommended_mentors = list_recommendation_candidates(db, risk_profile_tag=risk_tag)
    selected_mentor = recommended_mentors[0] if recommended_mentors else None

    profile = UserProfile(
        user_id=user.id,
        current_level_id=current_level.id,
        current_mentor_id=selected_mentor.id if selected_mentor else None,
        age_band=payload.age_band,
        has_investment_experience=payload.has_investment_experience,
        investment_experience_months=payload.investment_experience_months,
        holdings_summary=payload.holdings_summary,
        investment_amount_band=payload.investment_amount_band,
        investment_purpose=payload.investment_purpose,
        risk_tolerance=payload.risk_tolerance,
        onboarding_completed_at=datetime.utcnow(),
    )
    db.add(profile)

    for topic in topics:
        db.add(UserInterestTopic(user_id=user.id, topic_id=topic.id))

    for answer in payload.answers:
        db.add(
            OnboardingSurveyAnswer(
                user_id=user.id,
                question_code=answer.question_code,
                question_text=answer.question_text,
                answer_value=answer.answer_value,
                answer_payload=json.dumps(answer.answer_payload, ensure_ascii=False)
                if answer.answer_payload is not None
                else None,
            )
        )

    db.commit()

    recommendation_payload = [
        RecommendedMentorSummary(
            id=mentor.id,
            code=mentor.code,
            name=mentor.name,
            strategy_name=mentor.strategy.name,
            reason=_build_recommendation_reason(mentor.strategy.name, payload.risk_tolerance),
        )
        for mentor in recommended_mentors
    ]

    return OnboardingResult(
        user_id=user.id,
        level_no=current_level.level_no,
        selected_mentor_id=selected_mentor.id if selected_mentor else None,
        recommended_mentors=recommendation_payload,
    )


def _build_recommendation_reason(strategy_name: str, risk_tolerance: str | None) -> str:
    if risk_tolerance:
        return f"{risk_tolerance} 성향과 {strategy_name} 학습 방향이 잘 맞아 우선 추천합니다."
    return f"{strategy_name} 전략을 기준으로 학습을 시작하기 좋은 멘토입니다."

