from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.news import NewsArticle
from app.schemas.news import NewsDetail, NewsSummary


def list_articles(db: Session, limit: int = 10, offset: int = 0) -> list[NewsSummary]:
    stmt = (
        select(NewsArticle)
        .order_by(NewsArticle.published_at.desc().nullslast(), NewsArticle.id.desc())
        .limit(limit)
        .offset(offset)
    )
    articles = db.scalars(stmt).all()
    return [NewsSummary.model_validate(article) for article in articles]


def get_article(db: Session, news_id: int) -> NewsDetail:
    article = db.get(NewsArticle, news_id)
    if article is None:
        raise HTTPException(status_code=404, detail="news article not found")
    return NewsDetail.model_validate(article)


def list_recent_article_models(db: Session, limit: int = 3) -> list[NewsArticle]:
    stmt = (
        select(NewsArticle)
        .order_by(NewsArticle.published_at.desc().nullslast(), NewsArticle.id.desc())
        .limit(limit)
    )
    return db.scalars(stmt).all()

