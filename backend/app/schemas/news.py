from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NewsSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    summary: str | None
    original_url: str
    publisher: str | None
    published_at: datetime | None


class NewsDetail(NewsSummary):
    content_text: str | None
    author_name: str | None
    thumbnail_url: str | None
    status: str

