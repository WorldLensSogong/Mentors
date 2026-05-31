"""경제 지수 실시간 조회 API.

prefix: /api/market
인증: Mentors auth — Depends(get_current_user)

Yahoo Finance Chart API(v8)를 통해 환율·금리·코스피·나스닥의
최신 가격·변동률·5일 일봉 히스토리를 반환한다.
서버 메모리에 30초 캐시 — 프론트엔드는 5초 폴링해도 무방.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from urllib.parse import quote

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from core.auth import get_current_user
from core.auth.models import User

logger = logging.getLogger("market_data.quotes")

router = APIRouter(prefix="/api/market", tags=["market"])

# ── Indicator definitions ──────────────────────────────────────────────────────

INDICATOR_SYMBOLS: dict[str, str] = {
    "환율": "USDKRW=X",   # USD/KRW 환율
    "금리": "^TNX",        # US 10-Year Treasury (글로벌 금리 방향 지표)
    "코스피": "^KS11",     # KOSPI
    "나스닥": "^IXIC",     # NASDAQ Composite
}

_YAHOO_CHART_BASE = "https://query1.finance.yahoo.com/v8/finance/chart/"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://finance.yahoo.com",
}
_TIMEOUT_S = 8.0
_CACHE_TTL_S = 30  # 30초 캐시 — 프론트 5초 폴링 버퍼


# ── Response schemas ───────────────────────────────────────────────────────────


class IndicatorQuote(BaseModel):
    name: str
    symbol: str
    value: float
    change: float
    change_pct: float
    is_up: bool
    history: list[float]   # 5일 일봉 종가 (sparkline 용)
    updated_at: str        # ISO-8601


class MarketQuotesResponse(BaseModel):
    quotes: list[IndicatorQuote]
    cached: bool
    cache_age_s: float


# ── In-memory cache ────────────────────────────────────────────────────────────

_cache: list[IndicatorQuote] = []
_cache_time: datetime | None = None
_lock = asyncio.Lock()


# ── Fetch helpers ──────────────────────────────────────────────────────────────


async def _fetch_one(
    client: httpx.AsyncClient,
    name: str,
    symbol: str,
) -> IndicatorQuote | None:
    """Yahoo Finance v8 chart API로 단일 지표 조회."""
    encoded_symbol = quote(symbol, safe="")
    url = f"{_YAHOO_CHART_BASE}{encoded_symbol}"
    try:
        resp = await client.get(
            url,
            params={"range": "5d", "interval": "1d"},
            headers=_HEADERS,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.warning(
            "market_data.quote_fetch_failed",
            extra={"symbol": symbol, "err": str(exc)},
        )
        return None

    try:
        result = data["chart"]["result"][0]
        meta = result.get("meta", {})

        price: float = float(meta.get("regularMarketPrice") or 0)
        prev_close: float = float(meta.get("previousClose") or price or 1)
        change = round(price - prev_close, 4)
        change_pct = round((change / prev_close) * 100, 2) if prev_close else 0.0

        # 5일 일봉 종가 → sparkline
        raw_closes: list = (
            result.get("indicators", {})
            .get("quote", [{}])[0]
            .get("close", [])
        )
        history = [round(float(c), 4) for c in raw_closes if c is not None]

    except (KeyError, IndexError, TypeError, ValueError) as exc:
        logger.warning(
            "market_data.quote_parse_failed",
            extra={"symbol": symbol, "err": str(exc)},
        )
        return None

    return IndicatorQuote(
        name=name,
        symbol=symbol,
        value=round(price, 4),
        change=change,
        change_pct=change_pct,
        is_up=change >= 0,
        history=history,
        updated_at=datetime.now(UTC).isoformat(),
    )


async def _fetch_all() -> list[IndicatorQuote]:
    async with httpx.AsyncClient(timeout=_TIMEOUT_S) as client:
        tasks = [
            _fetch_one(client, name, symbol)
            for name, symbol in INDICATOR_SYMBOLS.items()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if isinstance(r, IndicatorQuote)]


async def get_quotes_cached() -> tuple[list[IndicatorQuote], bool, float]:
    """캐시된 지표 반환. TTL 초과 시 재조회."""
    global _cache, _cache_time

    async with _lock:
        # 캐시가 살아있으면 바로 반환
        if _cache_time is not None and _cache:
            age = (datetime.now(UTC) - _cache_time).total_seconds()
            if age < _CACHE_TTL_S:
                return _cache, True, round(age, 1)

        # 신규 조회
        fresh = await _fetch_all()
        if fresh:
            _cache = fresh
            _cache_time = datetime.now(UTC)
            return fresh, False, 0.0

        # 조회 실패 → stale 캐시 반환
        if _cache and _cache_time:
            age = (datetime.now(UTC) - _cache_time).total_seconds()
            return _cache, True, round(age, 1)

        return [], False, 0.0


# ── Route ──────────────────────────────────────────────────────────────────────


@router.get("/quotes", response_model=MarketQuotesResponse)
async def market_quotes(
    _user: User = Depends(get_current_user),
) -> MarketQuotesResponse:
    """경제 지수 실시간 조회 (환율·금리·코스피·나스닥).

    - value: 현재 시장 가격
    - change / change_pct: 전일 종가 대비 변동
    - history: 5일 일봉 종가 배열 (sparkline 그래프용)
    - cached: True이면 서버 캐시 응답, False이면 즉시 조회 결과
    """
    quotes, cached, cache_age = await get_quotes_cached()
    return MarketQuotesResponse(
        quotes=quotes,
        cached=cached,
        cache_age_s=cache_age,
    )


__all__ = ["router"]
