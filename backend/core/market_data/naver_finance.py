from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger("market_data.naver_finance")

_NAVER_FINANCE_AC_URL = "https://ac.finance.naver.com/ac"
_TIMEOUT_S = 5.0
_STOCK_CODE_PATTERN = re.compile(r"^\d{6}$")
_MARKETS = {"KOSPI", "KOSDAQ", "KONEX"}


@dataclass(frozen=True)
class NaverFinanceStock:
    code: str
    name: str
    market: str | None = None


class NaverFinanceMarketDataClient:
    async def search_stocks(self, query: str, *, limit: int = 5) -> list[NaverFinanceStock]:
        if not query.strip():
            return []

        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT_S) as client:
                response = await client.get(
                    _NAVER_FINANCE_AC_URL,
                    params={
                        "q": query,
                        "q_enc": "UTF-8",
                        "st": "111",
                        "r_format": "json",
                        "r_enc": "UTF-8",
                        "r_unicode": "0",
                        "t_koreng": "1",
                    },
                )
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("naver_finance.search_failed", extra={"query": query, "err": str(exc)})
            return []

        return _parse_stocks(payload, limit=limit)


def _parse_stocks(payload: Any, *, limit: int = 5) -> list[NaverFinanceStock]:
    stocks: list[NaverFinanceStock] = []
    seen_codes: set[str] = set()
    for node in _walk_nodes(payload):
        stock = _stock_from_node(node)
        if stock is None or stock.code in seen_codes:
            continue
        seen_codes.add(stock.code)
        stocks.append(stock)
        if len(stocks) >= limit:
            break
    return stocks


def _walk_nodes(node: Any):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk_nodes(value)
    elif isinstance(node, list):
        yield node
        for value in node:
            yield from _walk_nodes(value)


def _stock_from_node(node: Any) -> NaverFinanceStock | None:
    if isinstance(node, dict):
        return _stock_from_dict(node)
    if isinstance(node, list):
        return _stock_from_list(node)
    return None


def _stock_from_dict(node: dict[str, Any]) -> NaverFinanceStock | None:
    code = _first_stock_code(
        node.get("code"),
        node.get("itemCode"),
        node.get("symbol"),
        node.get("ticker"),
    )
    name = _first_text(node.get("name"), node.get("itemName"), node.get("nm"), node.get("title"))
    if not code or not name:
        return None
    return NaverFinanceStock(
        code=code,
        name=name,
        market=_normalize_market(_first_text(node.get("market"), node.get("typeCode"))),
    )


def _stock_from_list(node: list[Any]) -> NaverFinanceStock | None:
    values = [str(value).strip() for value in node if value is not None and str(value).strip()]
    code = _first_stock_code(*values)
    if not code:
        return None
    name = next(
        (
            value
            for value in values
            if value != code
            and not _STOCK_CODE_PATTERN.fullmatch(value)
            and value.upper() not in _MARKETS
        ),
        "",
    )
    if not name:
        return None
    market = next((value.upper() for value in values if value.upper() in _MARKETS), None)
    return NaverFinanceStock(code=code, name=name, market=market)


def _first_stock_code(*values: Any) -> str | None:
    for value in values:
        text = str(value or "").strip()
        if _STOCK_CODE_PATTERN.fullmatch(text):
            return text
    return None


def _first_text(*values: Any) -> str | None:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return None


def _normalize_market(value: str | None) -> str | None:
    if value is None:
        return None
    upper = value.upper()
    return upper if upper in _MARKETS else value


naver_finance_market_data = NaverFinanceMarketDataClient()

__all__ = [
    "NaverFinanceMarketDataClient",
    "NaverFinanceStock",
    "naver_finance_market_data",
]
