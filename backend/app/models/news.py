from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class NewsSource(Base, TimestampMixin):
    __tablename__ = "news_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)
    base_url: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("news_sources.id"), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    content_text: Mapped[str | None] = mapped_column(Text)
    original_url: Mapped[str] = mapped_column(String(1000), unique=True, nullable=False)
    publisher: Mapped[str | None] = mapped_column(String(100))
    author_name: Mapped[str | None] = mapped_column(String(100))
    thumbnail_url: Mapped[str | None] = mapped_column(String(1000))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")


class ArticleTopic(Base):
    __tablename__ = "article_topics"

    article_id: Mapped[int] = mapped_column(ForeignKey("news_articles.id"), primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("interest_topics.id"), primary_key=True)

