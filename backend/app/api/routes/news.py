from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.repositories.news_repository import get_article, list_articles
from app.schemas.common import ListPayload, ResponseEnvelope
from app.schemas.news import NewsDetail, NewsSummary

router = APIRouter()


@router.get("", response_model=ResponseEnvelope[ListPayload[NewsSummary]])
def get_news_list(
    limit: int = Query(default=10, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> ResponseEnvelope[ListPayload[NewsSummary]]:
    items = list_articles(db, limit=limit, offset=offset)
    payload = ListPayload[NewsSummary](items=items, total=len(items))
    return ResponseEnvelope(data=payload, message="news fetched")


@router.get("/{news_id}", response_model=ResponseEnvelope[NewsDetail])
def get_news_detail(
    news_id: int,
    db: Session = Depends(get_db),
) -> ResponseEnvelope[NewsDetail]:
    article = get_article(db, news_id)
    return ResponseEnvelope(data=article, message="news detail fetched")

