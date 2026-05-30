from __future__ import annotations

import logging
import re
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Protocol, TypedDict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.ai_pipeline.news_search import news_search
from core.config import settings
from core.db import transaction
from core.exceptions import ExternalServiceError
from core.market_data.finnhub import (
    FinnhubCompany,
    FinnhubCompanyProfile,
    FinnhubNewsItem,
    finnhub_market_data,
)
from core.market_data.models import MarketEntity
from core.market_data.naver_finance import NaverFinanceStock, naver_finance_market_data
from core.market_data.repository import upsert_entity, upsert_news_item

logger = logging.getLogger("market_data")

GLOBAL_STOCK_KOREAN_ALIASES: dict[str, tuple[str, ...]] = {
    "NVDA": ("엔비디아",),
    "AAPL": ("애플",),
    "MSFT": ("마이크로소프트",),
    "GOOGL": ("구글", "알파벳"),
    "META": ("메타", "페이스북"),
    "AMZN": ("아마존",),
    "TSLA": ("테슬라",),
    "NFLX": ("넷플릭스",),
    "PLTR": ("팔란티어",),
    "AVGO": ("브로드컴",),
    "LLY": ("일라이릴리",),
    "KO": ("코카콜라",),
    "MCD": ("맥도날드",),
    "QSR": ("버거킹",),
}


class MarketDataDiscoveryClient(Protocol):
    async def search_companies(self, query: str, *, limit: int = 5) -> list[FinnhubCompany]: ...

    async def get_company_profile(self, symbol: str) -> FinnhubCompanyProfile | None: ...

    async def get_company_news(self, symbol: str, *, limit: int = 5) -> list[FinnhubNewsItem]: ...


class KoreanMarketDataDiscoveryClient(Protocol):
    async def search_stocks(self, query: str, *, limit: int = 5) -> list[NaverFinanceStock]: ...


class SeedEntity(TypedDict, total=False):
    kind: str
    symbol: str
    name: str
    name_en: str
    exchange: str
    sector: str
    industry: str
    aliases: list[str]
    themes: list[str]


DEFAULT_SEED_ENTITIES: tuple[SeedEntity, ...] = (
    {
        "kind": "stock",
        "symbol": "PLTR",
        "name": "팔란티어",
        "name_en": "Palantir",
        "exchange": "NYSE",
        "sector": "software",
        "industry": "data analytics",
        "aliases": ["palantir", "pltr"],
        "themes": ["AI", "방산", "데이터 분석"],
    },
    {
        "kind": "stock",
        "symbol": "RBLX",
        "name": "로블록스",
        "name_en": "Roblox",
        "exchange": "NYSE",
        "sector": "communication services",
        "industry": "gaming platform",
        "aliases": ["roblox", "rblx"],
        "themes": ["게임", "메타버스"],
    },
    {
        "kind": "theme",
        "symbol": "SPACE_TECH",
        "name": "우주테크",
        "name_en": "space tech",
        "sector": "industrial technology",
        "aliases": ["우주항공", "항공우주", "위성", "발사체", "space economy"],
        "themes": ["방산", "위성통신", "발사체"],
    },
    {
        "kind": "theme",
        "symbol": "QUANTUM_COMPUTING",
        "name": "양자컴퓨팅",
        "name_en": "quantum computing",
        "sector": "technology",
        "aliases": ["양자컴퓨터", "퀀텀컴퓨팅", "quantum"],
        "themes": ["반도체", "클라우드", "보안"],
    },
    {
        "kind": "theme",
        "symbol": "POWER_GRID",
        "name": "전력망",
        "name_en": "power grid",
        "sector": "infrastructure",
        "aliases": ["송전망", "전력 인프라", "grid infrastructure"],
        "themes": ["전력", "AI 데이터센터", "인프라"],
    },
)


async def refresh_market_data() -> None:
    async with transaction() as db:
        await seed_market_entities(db)
        await refresh_external_market_entities(db)
        await refresh_tracked_entity_news(db)


async def seed_market_entities(db: AsyncSession) -> None:
    for seed in DEFAULT_SEED_ENTITIES:
        await upsert_entity(
            db,
            kind=seed["kind"],
            symbol=seed["symbol"],
            name=seed["name"],
            name_en=seed.get("name_en"),
            exchange=seed.get("exchange"),
            sector=seed.get("sector"),
            industry=seed.get("industry"),
            aliases=seed.get("aliases", []),
            themes=seed.get("themes", []),
            source="seed",
            confidence=90,
        )


async def refresh_external_market_entities(
    db: AsyncSession,
    *,
    client: MarketDataDiscoveryClient | None = None,
    korean_client: KoreanMarketDataDiscoveryClient | None = None,
) -> int:
    if not settings.market_data_discovery_enabled:
        return 0

    client = client or finnhub_market_data
    korean_client = korean_client or naver_finance_market_data
    refreshed = 0
    for query in _configured_seed_korean_queries():
        stocks = await korean_client.search_stocks(query, limit=1)
        for stock in stocks:
            entity = await upsert_korean_stock(db, stock)
            if entity is not None:
                refreshed += 1
    for symbol in _configured_seed_symbols():
        entity = await upsert_external_stock(db, symbol, client=client)
        if entity is not None:
            refreshed += 1
    return refreshed


async def discover_entity_from_topic(
    db: AsyncSession,
    topic: str,
    *,
    client: MarketDataDiscoveryClient | None = None,
    korean_client: KoreanMarketDataDiscoveryClient | None = None,
) -> MarketEntity | None:
    if not settings.market_data_discovery_enabled:
        return None

    client = client or finnhub_market_data
    korean_client = korean_client or naver_finance_market_data
    for query in _topic_discovery_queries(topic):
        korean_stocks = await korean_client.search_stocks(query, limit=3)
        for stock in korean_stocks:
            entity = await upsert_korean_stock(db, stock)
            if entity is not None:
                return entity

        companies = await client.search_companies(query, limit=3)
        for company in companies:
            if not _is_supported_company(company):
                continue
            entity = await upsert_external_stock(db, company.symbol, company=company, client=client)
            if entity is not None:
                return entity
    return None


async def upsert_korean_stock(db: AsyncSession, stock: NaverFinanceStock) -> MarketEntity | None:
    aliases = _unique_nonempty([stock.name, stock.code])
    themes = _unique_nonempty(["국내주식", stock.market])
    return await upsert_entity(
        db,
        kind="stock",
        symbol=stock.code,
        name=stock.name,
        name_en=stock.name,
        exchange=stock.market,
        sector=stock.market,
        aliases=aliases,
        themes=themes,
        source="naver_finance",
        confidence=85,
    )


async def upsert_external_stock(
    db: AsyncSession,
    symbol: str,
    *,
    company: FinnhubCompany | None = None,
    client: MarketDataDiscoveryClient | None = None,
) -> MarketEntity | None:
    client = client or finnhub_market_data
    profile = await client.get_company_profile(symbol)
    if profile is None:
        return None

    aliases = _unique_nonempty(
        [
            profile.symbol,
            company.display_symbol if company else None,
            company.description if company else None,
            profile.name,
            *GLOBAL_STOCK_KOREAN_ALIASES.get(profile.symbol, ()),
        ]
    )
    themes = _unique_nonempty([profile.industry, profile.country])
    entity = await upsert_entity(
        db,
        kind="stock",
        symbol=profile.symbol,
        name=profile.name,
        name_en=profile.name,
        exchange=profile.exchange,
        sector=profile.industry,
        industry=profile.industry,
        aliases=aliases,
        themes=themes,
        source="finnhub",
        confidence=80,
    )
    await upsert_profile_industry_theme(db, profile)
    await refresh_entity_company_news(db, entity, client=client)
    return entity


async def upsert_profile_industry_theme(
    db: AsyncSession,
    profile: FinnhubCompanyProfile,
) -> MarketEntity | None:
    industry = (profile.industry or "").strip()
    if not industry:
        return None

    return await upsert_entity(
        db,
        kind="theme",
        symbol=_industry_theme_symbol(industry),
        name=industry,
        name_en=industry,
        sector=industry,
        industry=industry,
        aliases=_unique_nonempty([industry, f"{industry} industry"]),
        themes=_unique_nonempty([industry, profile.country]),
        source="finnhub_profile",
        confidence=70,
    )


async def refresh_entity_company_news(
    db: AsyncSession,
    entity: MarketEntity,
    *,
    client: MarketDataDiscoveryClient | None = None,
) -> int:
    if entity.kind != "stock":
        return 0

    client = client or finnhub_market_data
    items = await client.get_company_news(entity.symbol, limit=5)
    saved = 0
    for item in items:
        saved_item = await upsert_news_item(
            db,
            entity,
            title=item.title,
            source=item.source,
            url=item.url,
            summary=item.summary,
            published_at=item.published_at,
        )
        if saved_item is not None:
            saved += 1
    if saved:
        entity.last_refreshed_at = datetime.now(UTC)
    return saved


async def refresh_tracked_entity_news(db: AsyncSession, limit: int = 30) -> int:
    result = await db.execute(select(MarketEntity).order_by(MarketEntity.id).limit(limit))
    entities = list(result.scalars().all())
    refreshed = 0
    for entity in entities:
        query = _entity_news_query(entity)
        try:
            documents = await news_search.search(query, top_k=3)
        except ExternalServiceError:
            logger.warning("market_data.news_refresh_failed", extra={"entity": entity.symbol})
            continue
        for doc in documents:
            await upsert_news_item(
                db,
                entity,
                title=str(doc.metadata.get("title") or doc.text[:120]),
                source=str(doc.metadata.get("source") or ""),
                url=str(doc.metadata.get("url") or ""),
                summary=doc.text,
                published_at=str(doc.metadata.get("published_at") or ""),
            )
        entity.last_refreshed_at = datetime.now(UTC)
        refreshed += 1
    return refreshed


def _entity_news_query(entity: MarketEntity) -> str:
    if entity.kind == "stock":
        return f"{entity.name} {entity.symbol} 실적 주가 전망"
    return f"{entity.name} 관련주 산업 전망 투자 리스크"


def _configured_seed_symbols() -> list[str]:
    return _unique_nonempty(settings.market_data_seed_symbols.split(","))


def _configured_seed_korean_queries() -> list[str]:
    return _unique_nonempty(settings.market_data_seed_korean_queries.split(","))


def _topic_discovery_queries(topic: str) -> list[str]:
    cleaned = re.sub(r"[^\w가-힣\s]", " ", topic)
    stopwords = {
        "지금",
        "전망",
        "투자",
        "주식",
        "관련주",
        "테마주",
        "수혜주",
        "살까",
        "팔까",
        "괜찮아",
        "괜찮나",
        "어때",
        "오너리스크",
        "실적",
        "주가",
    }
    candidates: list[str] = []
    for token in cleaned.split():
        token = _normalize_discovery_token(token)
        if len(token) < 2 or token in stopwords:
            continue
        if re.fullmatch(r"[A-Z]{1,6}", token):
            candidates.insert(0, token)
        else:
            candidates.append(token)
    return _unique_nonempty(candidates[:4])


def _normalize_discovery_token(token: str) -> str:
    stripped = token.strip()
    latin_prefix = re.match(r"[A-Za-z]{2,6}", stripped)
    if latin_prefix:
        return latin_prefix.group(0)
    return stripped


def _industry_theme_symbol(industry: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9가-힣]+", "_", industry.strip()).strip("_")
    return f"INDUSTRY_{normalized.upper()[:31]}" if normalized else "INDUSTRY_UNKNOWN"


def _is_supported_company(company: FinnhubCompany) -> bool:
    company_type = company.kind.lower()
    if company_type and company_type not in {"common stock", "equity", "adr"}:
        return False
    return bool(company.symbol and "." not in company.symbol)


def _unique_nonempty(values: Iterable[object]) -> list[str]:
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
