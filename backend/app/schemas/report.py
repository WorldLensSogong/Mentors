from __future__ import annotations

from pydantic import BaseModel


class ReportPreviewRequest(BaseModel):
    user_id: int
    mentor_id: int


class ReportPreviewResult(BaseModel):
    title: str
    summary_text: str
    outlook_text: str
    learning_question_text: str

