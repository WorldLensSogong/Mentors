"""core.llm.client embedding provider 선택 로직 테스트.

목표: `_resolve_embedding_provider`와 `LLMClient.embed`가 다음 우선순위를 정확히
지키는지, 그리고 자동 fallback 없이 명시적 에러를 내는지 검증.

우선순위:
    1. embed(provider=...) 명시 인자
    2. settings.embedding_provider  (env: EMBEDDING_PROVIDER)
    3. settings.llm_provider        (env: LLM_PROVIDER) — backward compat

핵심 안전성 보장:
    - LLM_PROVIDER=google 인 기존 프로젝트의 embed() 결과가 갑자기 OpenAI로
      바뀌지 않는다.
    - 지정한 provider의 API 키가 없으면 다른 provider로 조용히 fallback하지 않고
      ExternalServiceError로 즉시 실패한다 (vector dimension mismatch 방지).
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from core.exceptions import ExternalServiceError
from core.llm import client as client_module
from core.llm.client import LLMClient, _resolve_embedding_provider


# --------------------------------------------------------------------------
# settings monkeypatch helper
# --------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _baseline_settings(monkeypatch: pytest.MonkeyPatch):
    """모든 테스트가 시작할 때 client 모듈에 API 키가 비어있는 fake settings를 깐다.

    autouse라 개별 테스트는 fake_settings로 provider만 골라 덮어쓰면 된다.
    """
    fake = SimpleNamespace(
        llm_provider="openai",
        embedding_provider=None,
        openai_api_key=None,
        anthropic_api_key=None,
        gemini_api_key=None,
        llm_stream_timeout_s=30.0,
    )
    monkeypatch.setattr(client_module, "settings", fake)
    return fake


@pytest.fixture
def fake_settings(monkeypatch: pytest.MonkeyPatch):
    """client 모듈의 settings를 가짜로 교체. 호출 시 provider만 지정."""

    def _make(*, llm_provider: str, embedding_provider: str | None = None):
        fake = SimpleNamespace(
            llm_provider=llm_provider,
            embedding_provider=embedding_provider,
            openai_api_key=None,
            anthropic_api_key=None,
            gemini_api_key=None,
            llm_stream_timeout_s=30.0,
        )
        monkeypatch.setattr(client_module, "settings", fake)
        return fake

    return _make


@pytest.fixture
def make_client():
    """LLMClient를 만들고 provider별 stub을 꽂는다.

    fake_settings가 먼저 호출돼 있어야 한다. __init__은 _baseline_settings에 의해
    이미 키가 비어있는 상태로 동작하므로 SDK import도 일어나지 않는다.
    """

    def _make(*, openai: bool = False, google: bool = False, anthropic: bool = False):
        c = LLMClient()
        if openai:
            c._openai = SimpleNamespace(embeddings=SimpleNamespace())  # type: ignore[assignment]
        if google:
            c._google = SimpleNamespace()  # type: ignore[assignment]
        if anthropic:
            c._anthropic = SimpleNamespace()  # type: ignore[assignment]
        return c

    return _make


# --------------------------------------------------------------------------
# _resolve_embedding_provider — 순수 함수 우선순위 테스트
# --------------------------------------------------------------------------


class TestResolveEmbeddingProvider:
    def test_falls_back_to_llm_provider_when_embedding_unset_and_llm_is_google(
        self, fake_settings
    ):
        """EMBEDDING_PROVIDER 없으면 LLM_PROVIDER=google → google."""
        fake_settings(llm_provider="google", embedding_provider=None)
        assert _resolve_embedding_provider(None) == "google"

    def test_falls_back_to_llm_provider_when_embedding_unset_and_llm_is_openai(
        self, fake_settings
    ):
        """EMBEDDING_PROVIDER 없으면 LLM_PROVIDER=openai → openai."""
        fake_settings(llm_provider="openai", embedding_provider=None)
        assert _resolve_embedding_provider(None) == "openai"

    def test_embedding_provider_overrides_llm_provider(self, fake_settings):
        """EMBEDDING_PROVIDER=openai가 LLM_PROVIDER=google보다 우선."""
        fake_settings(llm_provider="google", embedding_provider="openai")
        assert _resolve_embedding_provider(None) == "openai"

    def test_explicit_arg_overrides_settings(self, fake_settings):
        """embed(provider="google") 인자가 EMBEDDING_PROVIDER=openai보다 우선."""
        fake_settings(llm_provider="openai", embedding_provider="openai")
        assert _resolve_embedding_provider("google") == "google"

    def test_explicit_arg_overrides_llm_provider(self, fake_settings):
        fake_settings(llm_provider="google", embedding_provider=None)
        assert _resolve_embedding_provider("openai") == "openai"

    def test_empty_string_embedding_provider_treated_as_unset(self, fake_settings):
        """빈 문자열은 unset 취급 (.env에서 EMBEDDING_PROVIDER= 만 적은 경우)."""
        fake_settings(llm_provider="google", embedding_provider="")
        assert _resolve_embedding_provider(None) == "google"


# --------------------------------------------------------------------------
# LLMClient.embed — 에러 경로 + provider 라우팅
# --------------------------------------------------------------------------


@pytest.mark.asyncio
class TestEmbedErrors:
    async def test_anthropic_raises_clear_error(self, make_client, fake_settings):
        """anthropic은 native 임베딩이 없으므로 명확한 에러."""
        fake_settings(llm_provider="anthropic", embedding_provider=None)
        client = make_client(anthropic=True)
        with pytest.raises(ExternalServiceError) as exc:
            await client.embed("hi")
        msg = str(exc.value)
        assert "Anthropic" in msg
        assert "EMBEDDING_PROVIDER" in msg

    async def test_openai_selected_but_key_missing_no_silent_fallback(
        self, make_client, fake_settings
    ):
        """OpenAI 선택됐는데 키 없으면 Google이 있어도 자동 fallback X."""
        fake_settings(llm_provider="openai", embedding_provider=None)
        # google은 살아있지만 openai 키가 없는 상황
        client = make_client(openai=False, google=True)
        with pytest.raises(ExternalServiceError) as exc:
            await client.embed("hi")
        msg = str(exc.value)
        assert "OpenAI embed not configured" in msg
        assert "EMBEDDING_PROVIDER=google" in msg  # 사용자에게 대안 안내

    async def test_google_selected_but_key_missing_no_silent_fallback(
        self, make_client, fake_settings
    ):
        """Google 선택됐는데 키 없으면 OpenAI가 있어도 자동 fallback X."""
        fake_settings(llm_provider="google", embedding_provider=None)
        client = make_client(openai=True, google=False)
        with pytest.raises(ExternalServiceError) as exc:
            await client.embed("hi")
        msg = str(exc.value)
        assert "Google Gemini embed not configured" in msg
        assert "EMBEDDING_PROVIDER=openai" in msg

    async def test_explicit_provider_arg_used_even_when_other_keys_present(
        self, make_client, fake_settings
    ):
        """embed(provider='google') 명시 시, OpenAI 키만 있으면 Google 에러."""
        fake_settings(llm_provider="openai", embedding_provider="openai")
        client = make_client(openai=True, google=False)
        with pytest.raises(ExternalServiceError) as exc:
            await client.embed("hi", provider="google")
        assert "Google Gemini embed not configured" in str(exc.value)


@pytest.mark.asyncio
class TestEmbedRouting:
    async def test_openai_path_calls_openai_helper(self, make_client, fake_settings):
        fake_settings(llm_provider="openai", embedding_provider=None)
        client = make_client(openai=True)
        client._openai_embed = AsyncMock(return_value=[0.1, 0.2, 0.3])  # type: ignore[method-assign]

        out = await client.embed("hello")

        assert out == [0.1, 0.2, 0.3]
        client._openai_embed.assert_awaited_once_with("hello")

    async def test_google_path_calls_google_helper(self, make_client, fake_settings):
        """기존 LLM_PROVIDER=google 흐름 보존 — 자동으로 _google_embed 호출."""
        fake_settings(llm_provider="google", embedding_provider=None)
        client = make_client(google=True)
        client._google_embed = AsyncMock(return_value=[0.9, 0.8])  # type: ignore[method-assign]

        out = await client.embed("hello")

        assert out == [0.9, 0.8]
        client._google_embed.assert_awaited_once_with("hello")

    async def test_embedding_provider_override_routes_to_openai(
        self, make_client, fake_settings
    ):
        """LLM_PROVIDER=google인 상황에서 EMBEDDING_PROVIDER=openai로 명시적 분리."""
        fake_settings(llm_provider="google", embedding_provider="openai")
        client = make_client(openai=True, google=True)
        client._openai_embed = AsyncMock(return_value=[1.0])  # type: ignore[method-assign]
        client._google_embed = AsyncMock(return_value=[2.0])  # type: ignore[method-assign]

        out = await client.embed("hello")

        assert out == [1.0]
        client._openai_embed.assert_awaited_once()
        client._google_embed.assert_not_awaited()

    async def test_explicit_arg_routes_independently_of_settings(
        self, make_client, fake_settings
    ):
        """embed(provider='google') 호출이 settings를 모두 덮어쓴다."""
        fake_settings(llm_provider="openai", embedding_provider="openai")
        client = make_client(openai=True, google=True)
        client._openai_embed = AsyncMock(return_value=[1.0])  # type: ignore[method-assign]
        client._google_embed = AsyncMock(return_value=[2.0])  # type: ignore[method-assign]

        out = await client.embed("hello", provider="google")

        assert out == [2.0]
        client._google_embed.assert_awaited_once()
        client._openai_embed.assert_not_awaited()
