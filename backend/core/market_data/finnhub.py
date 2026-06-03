from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any

import httpx

from core.config import settings

logger = logging.getLogger("market_data.finnhub")

_FINNHUB_SEARCH_URL = "https://finnhub.io/api/v1/search"
_FINNHUB_PROFILE_URL = "https://finnhub.io/api/v1/stock/profile2"
_FINNHUB_COMPANY_NEWS_URL = "https://finnhub.io/api/v1/company-news"
_TIMEOUT_S = 8.0
_NEWS_LOOKBACK_DAYS = 7


@dataclass(frozen=True)
class FinnhubCompany:
    symbol: str
    display_symbol: str
    description: str
    kind: str


@dataclass(frozen=True)
class FinnhubCompanyProfile:
    symbol: str
    name: str
    exchange: str | None
    industry: str | None
    country: str | None


@dataclass(frozen=True)
class FinnhubNewsItem:
    title: str
    source: str | None
    url: str
    summary: str | None
    published_at: str | None


class FinnhubMarketDataClient:
    @property
    def enabled(self) -> bool:
        return bool(settings.finnhub_api_key)

    async def search_companies(self, query: str, *, limit: int = 5) -> list[FinnhubCompany]:
        if not self.enabled or not query.strip():
            return []

        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT_S) as client:
                response = await client.get(
                    _FINNHUB_SEARCH_URL,
                    params={"q": query, "token": settings.finnhub_api_key},
                )
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("finnhub.search_failed", extra={"query": query, "err": str(exc)})
            return []

        companies: list[FinnhubCompany] = []
        for item in payload.get("result", [])[:limit]:
            symbol = str(item.get("symbol") or "").strip().upper()
            description = str(item.get("description") or "").strip()
            if not symbol or not description:
                continue
            companies.append(
                FinnhubCompany(
                    symbol=symbol,
                    display_symbol=str(item.get("displaySymbol") or symbol).strip().upper(),
                    description=description,
                    kind=str(item.get("type") or "").strip(),
                )
            )
        return companies

    async def get_company_profile(self, symbol: str) -> FinnhubCompanyProfile | None:
        normalized = symbol.strip().upper()
        if not self.enabled or not normalized:
            return None

        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT_S) as client:
                response = await client.get(
                    _FINNHUB_PROFILE_URL,
                    params={"symbol": normalized, "token": settings.finnhub_api_key},
                )
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("finnhub.profile_failed", extra={"symbol": normalized, "err": str(exc)})
            return None

        name = str(payload.get("name") or "").strip()
        ticker = str(payload.get("ticker") or normalized).strip().upper()
        if not name:
            return None

        return FinnhubCompanyProfile(
            symbol=ticker,
            name=name,
            exchange=_optional_str(payload.get("exchange")),
            industry=_optional_str(payload.get("finnhubIndustry")),
            country=_optional_str(payload.get("country")),
        )

    async def get_company_news(self, symbol: str, *, limit: int = 5) -> list[FinnhubNewsItem]:
        normalized = symbol.strip().upper()
        if not self.enabled or not normalized:
            return []

        to_date = date.today()
        from_date = to_date - timedelta(days=_NEWS_LOOKBACK_DAYS)
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT_S) as client:
                response = await client.get(
                    _FINNHUB_COMPANY_NEWS_URL,
                    params={
                        "symbol": normalized,
                        "from": from_date.isoformat(),
                        "to": to_date.isoformat(),
                        "token": settings.finnhub_api_key,
                    },
                )
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("finnhub.news_failed", extra={"symbol": normalized, "err": str(exc)})
            return []

        items: list[FinnhubNewsItem] = []
        for item in payload[:limit]:
            title = str(item.get("headline") or "").strip()
            url = str(item.get("url") or "").strip()
            if not title or not url:
                continue
            items.append(
                FinnhubNewsItem(
                    title=title,
                    source=_optional_str(item.get("source")) or "Finnhub",
                    url=url,
                    summary=_optional_str(item.get("summary")),
                    published_at=_published_at(item.get("datetime")),
                )
            )
        return items


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _published_at(value: Any) -> str | None:
    if not isinstance(value, (int, float)):
        return None
    return datetime.fromtimestamp(int(value), tz=UTC).isoformat()


finnhub_market_data = FinnhubMarketDataClient()

__all__ = [
    "FinnhubCompany",
    "FinnhubCompanyProfile",
    "FinnhubMarketDataClient",
    "FinnhubNewsItem",
    "finnhub_market_data",
]
