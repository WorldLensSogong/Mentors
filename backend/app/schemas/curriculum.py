from __future__ import annotations

from pydantic import BaseModel


class CurriculumModuleSummary(BaseModel):
    id: int
    code: str
    title: str
    strategy_id: int
    level_no: int
    concept_summary: str | None
    sort_order: int

