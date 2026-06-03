"""ContentReader 구현 (AGENTS.md §5.2, ADR-014).

다른 동(일일리포트, 학습)이 `from core.read_services import content_reader`로 호출.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import desc, or_, select

from core.contracts import NewsId, UserId
from core.db import SessionLocal
from core.read_services import IndustryTopicRef, NewsRef
from core.user_context import user_context

from .models import (
    ArticleKeyword,
    Industry,
    IndustryKeyword,
    MasterKeyword,
    MasterKeywordCompany,
    NewsArticle,
    UserKeyword,
)

logger = logging.getLogger("content.read_service")

# 사용자 멘토 전략과 매칭되는 기사를 최근 N일에서 가져옴
_LOOKBACK_HOURS_TODAY = 36

_TOPIC_ALIASES = {
    "ai": ["인공지능"],
    "ev": ["전기차"],
    "battery": ["배터리", "2차전지"],
    "semiconductor": ["반도체"],
    "chip": ["반도체"],
    "cloud": ["클라우드"],
    "security": ["보안"],
    "defense": ["방산"],
    "shipbuilding": ["조선"],
    "bio": ["바이오"],
    "robot": ["로봇"],
    "game": ["게임"],
}

class ContentReadServiceImpl:
    """ContentReader Protocol 구현."""

    async def get_today_news_for_user(
        self, user_id: UserId, top_k: int = 5
    ) -> list[NewsRef]:
        """오늘(±36h) 노출 가능 기사 우선순위:
          1. 사용자가 등록한 관심 키워드와 매칭되는 기사
          2. 멘토 전략 매칭 기사
          3. 일반 인기 (fallback)

        각 단계에서 중복 제거하며 top_k가 채워질 때까지 누적.
        """
        strategy = await self._resolve_user_strategy(user_id)
        cutoff = datetime.now(UTC) - timedelta(hours=_LOOKBACK_HOURS_TODAY)

        async with SessionLocal() as session:
            base_stmt = (
                select(NewsArticle)
                .where(
                    NewsArticle.is_visible.is_(True),
                    NewsArticle.published_at >= cutoff,
                )
                .order_by(desc(NewsArticle.composite_score), desc(NewsArticle.published_at))
            )

            articles: list[NewsArticle] = []
            seen_ids: set[int] = set()

            # ---- 1) 사용자 관심 키워드 매칭 ----
            user_kw_stmt = (
                select(NewsArticle)
                .join(ArticleKeyword, ArticleKeyword.article_id == NewsArticle.id)
                .join(
                    UserKeyword,
                    UserKeyword.master_keyword_id == ArticleKeyword.master_keyword_id,
                )
                .where(
                    UserKeyword.user_id == int(user_id),
                    NewsArticle.is_visible.is_(True),
                    NewsArticle.published_at >= cutoff,
                )
                .order_by(desc(NewsArticle.composite_score), desc(NewsArticle.published_at))
                .limit(top_k * 2)
            )
            result = await session.execute(user_kw_stmt)
            for a in result.scalars().all():
                if a.id in seen_ids:
                    continue
                articles.append(a)
                seen_ids.add(a.id)
                if len(articles) >= top_k:
                    return [self._to_ref(a) for a in articles[:top_k]]

            # ---- 2) 멘토 전략 매칭 ----
            if strategy is not None and len(articles) < top_k:
                stmt = base_stmt.where(NewsArticle.strategies.ilike(f"%{strategy}%")).limit(
                    top_k * 2
                )
                result = await session.execute(stmt)
                for a in result.scalars().all():
                    if a.id in seen_ids:
                        continue
                    articles.append(a)
                    seen_ids.add(a.id)
                    if len(articles) >= top_k:
                        break

            # ---- 3) 일반 인기 fallback ----
            if len(articles) < top_k:
                fallback_stmt = base_stmt.limit(top_k * 2)
                result = await session.execute(fallback_stmt)
                for a in result.scalars().all():
                    if a.id in seen_ids:
                        continue
                    articles.append(a)
                    seen_ids.add(a.id)
                    if len(articles) >= top_k:
                        break

            return [self._to_ref(a) for a in articles[:top_k]]

    async def get_news_by_id(self, news_id: NewsId) -> NewsRef | None:
        async with SessionLocal() as session:
            article = await session.scalar(
                select(NewsArticle).where(NewsArticle.id == int(news_id))
            )
            return self._to_ref(article) if article else None

    async def find_industry_topic(self, topic: str) -> IndustryTopicRef | None:
        """콘텐츠 산업 키워드 풀에서 토론 주제와 가장 가까운 산업/테마를 찾는다."""
        tokens = _topic_tokens(topic)
        if not tokens:
            return None

        async with SessionLocal() as session:
            result = await session.execute(
                select(Industry, IndustryKeyword, MasterKeywordCompany)
                .join(IndustryKeyword, IndustryKeyword.industry_id == Industry.id)
                .outerjoin(
                    MasterKeyword,
                    MasterKeyword.industry_keyword_id == IndustryKeyword.id,
                )
                .outerjoin(
                    MasterKeywordCompany,
                    MasterKeywordCompany.master_keyword_id == MasterKeyword.id,
                )
                .where(or_(*_industry_filters(tokens)))
                .order_by(Industry.display_order, IndustryKeyword.display_order)
                .limit(80)
            )

            candidates: dict[tuple[str, str], dict[str, object]] = {}
            for industry, keyword, company in result.all():
                key = (industry.name_ko, keyword.label_ko)
                candidate = candidates.setdefault(
                    key,
                    {
                        "industry": industry,
                        "keyword": keyword,
                        "companies": [],
                        "score": _industry_score(industry, keyword, topic, tokens),
                    },
                )
                if company is not None:
                    companies = candidate["companies"]
                    if isinstance(companies, list):
                        companies.append(company.company_name_ko or company.company_name)

            if not candidates:
                return None

            best = max(candidates.values(), key=lambda item: int(item["score"]))
            if int(best["score"]) <= 0:
                return None

            industry = best["industry"]
            keyword = best["keyword"]
            companies = best["companies"]
            assert isinstance(industry, Industry)
            assert isinstance(keyword, IndustryKeyword)
            assert isinstance(companies, list)
            return IndustryTopicRef(
                industry=industry.name_ko,
                keyword=keyword.label_ko,
                aliases=_unique_nonempty(
                    [industry.name_ko, industry.name_en, keyword.label_ko, keyword.keyword_en]
                ),
                companies=_unique_nonempty(companies)[:8],
            )

    async def search_news_for_topic(
        self,
        topic: str,
        keywords: list[str],
        top_k: int = 5,
    ) -> list[NewsRef]:
        """수집·AI 처리된 content 뉴스 중 토론 주제와 맞는 기사만 반환한다."""
        terms = _unique_nonempty([topic, *keywords, *_topic_tokens(topic)])[:8]
        if not terms:
            return []

        async with SessionLocal() as session:
            stmt = (
                select(NewsArticle)
                .where(
                    NewsArticle.is_visible.is_(True),
                    NewsArticle.is_duplicate.is_(False),
                    or_(*_article_filters(terms)),
                )
                .order_by(desc(NewsArticle.composite_score), desc(NewsArticle.published_at))
                .limit(top_k * 3)
            )
            result = await session.execute(stmt)
            articles = list(result.scalars().unique().all())
            scored = [
                (_article_score(article, terms), article)
                for article in articles
                if _article_score(article, terms) > 0
            ]
            scored.sort(
                key=lambda item: (
                    item[0],
                    item[1].composite_score or 0,
                    item[1].published_at or item[1].created_at,
                ),
                reverse=True,
            )
            return [self._to_ref(article) for _, article in scored[:top_k]]

    # ------------------------------------------------------------------
    # internals
    # ------------------------------------------------------------------

    @staticmethod
    async def _resolve_user_strategy(user_id: UserId) -> str | None:
        """user_context에서 선택 멘토 → 멘토 전략으로 변환.

        멘토 모델(학습 동)에 대한 직접 의존을 피하려고 user_context를 거친다.
        user_context에 전략까지 노출돼 있지 않으면 None 반환 (호출자가 fallback).
        """
        try:
            ctx = await user_context.get_for_mentor_chat(user_id)
        except Exception:
            logger.warning("content.user_context_failed", extra={"user_id": int(user_id)})
            return None
        # user_context DTO에 strategy 필드가 있는지 확인. 없으면 None.
        strategy = getattr(ctx, "selected_mentor_strategy", None)
        if strategy is None:
            return None
        return str(strategy.value) if hasattr(strategy, "value") else str(strategy)

    @staticmethod
    def _to_ref(article: NewsArticle) -> NewsRef:
        return NewsRef(
            id=NewsId(article.id),
            title=article.title_translated or article.title_original,
            url=article.original_url,
            published_at=article.published_at or article.created_at,
            source=article.source_name,
            summary=article.summary_ko or article.summary or article.content_translated,
            keywords=_split_csv(article.related_keywords) + _split_csv(article.related_industries),
        )


__all__ = ["ContentReadServiceImpl"]


def _topic_tokens(topic: str) -> list[str]:
    cleaned = " ".join(topic.replace("/", " ").split())
    tokens = []
    for token in cleaned.split():
        token = token.strip(".,!?()[]{}\"'“”‘’")
        if len(token) < 2 or token in {"전망", "투자", "관련주", "산업", "테마", "주식"}:
            continue
        tokens.append(token)
        tokens.extend(_TOPIC_ALIASES.get(token.lower(), []))
    return _unique_nonempty(tokens)


def _industry_filters(tokens: list[str]) -> list[object]:
    filters = []
    for token in tokens[:6]:
        like = f"%{token}%"
        filters.extend(
            [
                Industry.name_ko.ilike(like),
                Industry.name_en.ilike(like),
                IndustryKeyword.label_ko.ilike(like),
                IndustryKeyword.keyword_en.ilike(like),
                MasterKeywordCompany.company_name.ilike(like),
                MasterKeywordCompany.company_name_ko.ilike(like),
            ]
        )
    return filters


def _article_filters(terms: list[str]) -> list[object]:
    filters = []
    for term in terms[:8]:
        like = f"%{term}%"
        filters.extend(
            [
                NewsArticle.title_original.ilike(like),
                NewsArticle.title_translated.ilike(like),
                NewsArticle.summary.ilike(like),
                NewsArticle.summary_ko.ilike(like),
                NewsArticle.ai_keywords.ilike(like),
                NewsArticle.related_tickers.ilike(like),
                NewsArticle.related_industries.ilike(like),
                NewsArticle.related_keywords.ilike(like),
            ]
        )
    return filters


def _industry_score(
    industry: Industry,
    keyword: IndustryKeyword,
    topic: str,
    tokens: list[str],
) -> int:
    compact = topic.lower()
    fields = [
        (industry.name_ko, 70),
        (industry.name_en, 50),
        (keyword.label_ko, 100),
        (keyword.keyword_en, 70),
    ]
    score = 0
    for value, weight in fields:
        text = (value or "").lower()
        if not text:
            continue
        if text in compact:
            score += weight
        if any(token.lower() == text for token in tokens):
            score += weight
        elif any(token.lower() in text or text in token.lower() for token in tokens):
            score += weight // 2
    return score


def _article_score(article: NewsArticle, terms: list[str]) -> int:
    title = f"{article.title_translated or ''} {article.title_original or ''}".lower()
    body = f"{article.summary_ko or ''} {article.summary or ''}".lower()
    tags = " ".join(
        [
            article.ai_keywords or "",
            article.related_tickers or "",
            article.related_industries or "",
            article.related_keywords or "",
        ]
    ).lower()
    score = 0
    for term in terms:
        key = term.lower()
        if key in title:
            score += 5
        if key in tags:
            score += 4
        if key in body:
            score += 2
    return score


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return _unique_nonempty(value.split(","))


def _unique_nonempty(values: list[object]) -> list[str]:
    result = []
    seen = set()
    for value in values:
        text = str(value or "").strip()
        key = text.lower()
        if not text or key in seen:
            continue
        seen.add(key)
        result.append(text)
    return result
