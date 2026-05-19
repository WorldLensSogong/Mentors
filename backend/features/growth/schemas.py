from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PromotionTestChoiceResponse(BaseModel):
    choice_id: str
    text: str


class PromotionTestQuestionResponse(BaseModel):
    question_id: str
    prompt: str
    choices: list[PromotionTestChoiceResponse]


class PromotionTestPreviewResponse(BaseModel):
    target_tier: str
    passing_score: int = 80
    question_count: int
    questions: list[PromotionTestQuestionResponse]


class GrowthProgressResponse(BaseModel):
    current_tier: str
    next_tier: str | None
    progress_percent: int
    mastered_concepts: int
    total_concepts: int
    eligible_for_promotion: bool
    promotion_eligible_at: datetime | None
    unlocked_features: list[str]
    next_unlocks: list[str]
    promotion_test: PromotionTestPreviewResponse | None


class PromotionTestAnswerRequest(BaseModel):
    question_id: str
    choice_id: str


class PromotionTestRequest(BaseModel):
    answers: list[PromotionTestAnswerRequest] = Field(min_length=1)


class PromotionTestResponse(BaseModel):
    previous_tier: str
    current_tier: str
    target_tier: str | None
    passed: bool
    score_percent: int
    correct_answers: int
    total_questions: int
    unlocked_features: list[str]
    message: str


__all__ = [
    "GrowthProgressResponse",
    "PromotionTestAnswerRequest",
    "PromotionTestChoiceResponse",
    "PromotionTestPreviewResponse",
    "PromotionTestQuestionResponse",
    "PromotionTestRequest",
    "PromotionTestResponse",
]
