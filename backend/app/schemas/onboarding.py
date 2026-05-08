from __future__ import annotations

from typing import Any

from pydantic import BaseModel, EmailStr, Field

from app.schemas.mentor import RecommendedMentorSummary


class OnboardingAnswerInput(BaseModel):
    question_code: str
    question_text: str | None = None
    answer_value: str | None = None
    answer_payload: dict[str, Any] | None = None


class OnboardingRequest(BaseModel):
    email: EmailStr
    nickname: str = Field(min_length=2, max_length=50)
    age_band: str | None = None
    has_investment_experience: bool = False
    investment_experience_months: int | None = None
    holdings_summary: str | None = None
    investment_amount_band: str | None = None
    investment_purpose: str | None = None
    risk_tolerance: str | None = None
    interest_topic_codes: list[str] = Field(default_factory=list)
    answers: list[OnboardingAnswerInput] = Field(default_factory=list)


class OnboardingResult(BaseModel):
    user_id: int
    level_no: int
    selected_mentor_id: int | None
    recommended_mentors: list[RecommendedMentorSummary]

