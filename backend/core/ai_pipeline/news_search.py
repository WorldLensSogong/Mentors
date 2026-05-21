from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import urlencode

import httpx

from core.config import settings
from core.exceptions import ExternalServiceError
from core.vector_store import Document


class NewsSearchClient:
    NAVER_NEWS_URL = "https://openapi.naver.com/v1/search/news.json"
    GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"

    @property
    def configured(self) -> bool:
        return bool(settings.naver_client_id and settings.naver_client_secret)

    async def search(self, query: str, top_k: int = 3) -> list[Document]:
        if self.configured:
            return await self._search_naver(query, top_k)
        return await self._search_google_rss(query, top_k)

    async def _search_naver(self, query: str, top_k: int) -> list[Document]:
        assert settings.naver_client_id is not None
        assert settings.naver_client_secret is not None
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    self.NAVER_NEWS_URL,
                    params={
                        "query": query,
                        "display": top_k,
                        "sort": "date",
                    },
                    headers={
                        "X-Naver-Client-Id": settings.naver_client_id,
                        "X-Naver-Client-Secret": settings.naver_client_secret,
                    },
                )
                response.raise_for_status()
        except httpx.HTTPError as e:
            raise ExternalServiceError(f"Naver news search failed: {e}") from e

        payload: dict[str, Any] = response.json()
        return [
            Document(
                id=f"naver_news_{idx}",
                text=_clean_text(f"{item.get('title', '')}. {item.get('description', '')}"),
                metadata={
                    "source": "naver-news",
                    "title": _clean_text(str(item.get("title", ""))),
                    "url": str(item.get("originallink") or item.get("link") or ""),
                    "published_at": str(item.get("pubDate", "")),
                },
            )
            for idx, item in enumerate(payload.get("items", []), start=1)
            if item.get("title") or item.get("description")
        ]

    async def _search_google_rss(self, query: str, top_k: int) -> list[Document]:
        params = urlencode(
            {"q": _with_recent_window(query), "hl": "ko", "gl": "KR", "ceid": "KR:ko"}
        )
        try:
            async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
                response = await client.get(
                    f"{self.GOOGLE_NEWS_RSS_URL}?{params}",
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                response.raise_for_status()
        except httpx.HTTPError as e:
            raise ExternalServiceError(f"Google News RSS search failed: {e}") from e

        try:
            root = ET.fromstring(response.text)
        except ET.ParseError as e:
            raise ExternalServiceError(f"Google News RSS parse failed: {e}") from e

        docs: list[Document] = []
        for idx, item in enumerate(root.findall("./channel/item"), start=1):
            title = _clean_text(item.findtext("title", default=""))
            description = _clean_text(item.findtext("description", default=""))
            link = item.findtext("link", default="")
            published_at = item.findtext("pubDate", default="")
            source = item.find("source")
            source_name = _clean_text(source.text if source is not None and source.text else "")
            if not title and not description:
                continue
            docs.append(
                Document(
                    id=f"google_news_{idx}",
                    text=_clean_text(f"{title}. {description}"),
                    metadata={
                        "source": source_name or "google-news",
                        "title": title,
                        "url": link,
                        "published_at": published_at,
                    },
                )
            )
            if len(docs) >= top_k:
                break
        return docs


def _clean_text(value: str) -> str:
    text = html.unescape(value)
    text = re.sub(r"<[^>]+>", "", text)
    return " ".join(text.split())


def _with_recent_window(query: str) -> str:
    if re.search(r"\bwhen:\d+[hdmy]\b", query, re.IGNORECASE):
        return query
    return f"{query} when:3d"


news_search = NewsSearchClient()

__all__ = ["NewsSearchClient", "news_search"]
