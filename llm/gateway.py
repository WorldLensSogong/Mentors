"""LLM 호출 정책 레이어.

client.py는 provider별 실제 API 호출만 담당하고, 이 모듈은 provider/model 선택,
fallback, response_format 같은 공통 호출 정책을 담당한다.

chat use_case 기반 라우팅:
  - "pipeline" → Google Gemini   (뉴스 수집 → 번역/요약/키워드)
  - "debate"   → Anthropic Claude (멘토 토론)

호출 측이 use_case도 provider도 지정하지 않으면 settings.llm_provider를 따른다.
provider를 명시하면 use_case는 무시된다 (명시적 우선).

⚠️  embed()는 별도 정책으로 분리됨 (client._resolve_embedding_provider 참고).
    embedding provider는 vector dimension과 직접 연결되므로 자동 fallback / 강제
    default를 두지 않는다. gateway는 인자 그대로 client에 전달만 한다.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import Literal

from core.config import settings
from core.exceptions import ExternalServiceError

from .client import (
    DEFAULT_ANTHROPIC_MODEL,
    DEFAULT_GEMINI_MODEL,
    DEFAULT_OPENAI_CHAT_MODEL,
    LLMClient,
    llm_client,
)
from .dto import ChatResponse, Message, StreamChunk

logger = logging.getLogger("llm")

DEFAULT_GEMINI_FALLBACK_MODEL = "gemini-2.5-flash-lite"

# chat use_case → (provider, default_model). 모델이 None이면 client의 provider 기본을 사용.
# embed는 의도적으로 이 매핑에서 제외 — vector dimension 안전성 때문.
_USE_CASE_ROUTES: dict[str, tuple[str, str | None]] = {
    "pipeline": ("google", DEFAULT_GEMINI_MODEL),
    "debate": ("anthropic", DEFAULT_ANTHROPIC_MODEL),
}


class LLMGateway:
    def __init__(self, client: LLMClient | None = None) -> None:
        self._client = client or llm_client

    @property
    def configured(self) -> bool:
        return self._client.configured

    async def chat(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        response_format: str | None = None,
        provider: str | None = None,
        use_case: str | None = None,
    ) -> ChatResponse:
        selected_provider, selected_model = self._resolve_route(provider, model, use_case)
        try:
            return await self._client.chat(
                messages,
                model=selected_model,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
                provider=selected_provider,
            )
        except ExternalServiceError as error:
            if not _should_retry_with_gemini_fallback(selected_provider, selected_model, error):
                raise
            logger.info(
                "llm_gateway.google_high_demand_retry",
                extra={
                    "model": selected_model,
                    "fallback_model": DEFAULT_GEMINI_FALLBACK_MODEL,
                },
            )
            return await self._client.chat(
                messages,
                model=DEFAULT_GEMINI_FALLBACK_MODEL,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
                provider=selected_provider,
            )

    async def chat_stream(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        provider: str | None = None,
        use_case: str | None = None,
    ) -> AsyncIterator[StreamChunk]:
        selected_provider, selected_model = self._resolve_route(provider, model, use_case)
        try:
            async for chunk in self._client.chat_stream(
                messages,
                model=selected_model,
                temperature=temperature,
                max_tokens=max_tokens,
                provider=selected_provider,
            ):
                yield chunk
        except ExternalServiceError as error:
            if not _should_retry_with_gemini_fallback(selected_provider, selected_model, error):
                raise
            logger.info(
                "llm_gateway.google_stream_high_demand_retry",
                extra={
                    "model": selected_model,
                    "fallback_model": DEFAULT_GEMINI_FALLBACK_MODEL,
                },
            )
            async for chunk in self._client.chat_stream(
                messages,
                model=DEFAULT_GEMINI_FALLBACK_MODEL,
                temperature=temperature,
                max_tokens=max_tokens,
                provider=selected_provider,
            ):
                yield chunk

    async def embed(
        self,
        text: str,
        provider: Literal["openai", "google"] | None = None,
    ) -> list[float]:
        """벡터 임베딩 — 정책 없이 client로 위임.

        provider 선택 우선순위는 ``client._resolve_embedding_provider``에서 일괄
        관리한다 (1. 인자 → 2. EMBEDDING_PROVIDER → 3. LLM_PROVIDER).

        ⚠️  자동 fallback 없음. embedding provider는 vector dimension과 직결되므로
            지정된 provider가 사용 불가하면 명시적 ExternalServiceError를 던진다.
        """
        return await self._client.embed(text, provider=provider)

    # ------------------------------------------------------------------
    # 내부 라우팅 — chat 전용
    # ------------------------------------------------------------------

    def _resolve_route(
        self,
        provider: str | None,
        model: str | None,
        use_case: str | None,
    ) -> tuple[str, str | None]:
        """명시적 provider > use_case 매핑 > settings.llm_provider 순으로 결정."""
        if provider is not None:
            return provider, model or _default_chat_model(provider)

        if use_case is not None:
            route = _USE_CASE_ROUTES.get(use_case)
            if route is not None:
                route_provider, route_model = route
                return route_provider, model or route_model

        fallback_provider = settings.llm_provider
        return fallback_provider, model or _default_chat_model(fallback_provider)


def _default_chat_model(provider: str) -> str | None:
    if provider == "google":
        return DEFAULT_GEMINI_MODEL
    if provider == "anthropic":
        return DEFAULT_ANTHROPIC_MODEL
    if provider == "openai":
        return DEFAULT_OPENAI_CHAT_MODEL
    return None


def _google_chat_model_candidates(selected_model: str) -> list[str]:
    """기존 동작 + upstream 테스트(test_llm_client.py)가 import하므로 그대로 보존."""
    if selected_model == DEFAULT_GEMINI_FALLBACK_MODEL:
        return [selected_model]
    return [selected_model, DEFAULT_GEMINI_FALLBACK_MODEL]


def _is_google_high_demand_error(error: Exception) -> bool:
    status_code = getattr(error, "status_code", None)
    text = str(error).lower()
    return status_code == 503 or "503" in text or "high demand" in text or "unavailable" in text


def _should_retry_with_gemini_fallback(
    provider: str,
    model: str | None,
    error: Exception,
) -> bool:
    return (
        provider == "google"
        and model != DEFAULT_GEMINI_FALLBACK_MODEL
        and _is_google_high_demand_error(error)
    )


llm = LLMGateway()
