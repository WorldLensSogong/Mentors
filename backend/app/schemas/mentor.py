from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class MentorSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    one_liner: str | None
    philosophy: str | None
    strategy_name: str
    risk_profile_tag: str | None
    unlock_level_no: int | None
    is_free: bool


class RecommendedMentorSummary(BaseModel):
    id: int
    code: str
    name: str
    strategy_name: str
    reason: str

