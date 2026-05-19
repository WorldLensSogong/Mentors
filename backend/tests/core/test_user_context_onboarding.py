from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from core.contracts import Tier, UserId
from core.user_context.service import UserContextService


@pytest.mark.asyncio
async def test_user_context_reads_onboarding_profile_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = UserContextService()

    async def fake_load_growth_state(_user_id: UserId) -> None:
        return None

    async def fake_load_profile(_user_id: UserId) -> SimpleNamespace:
        return SimpleNamespace(
            current_tier="T2",
            interests_json='["value", "macro"]',
            selected_mentor_id=3,
        )

    monkeypatch.setattr(service, "_load_growth_state", fake_load_growth_state)
    monkeypatch.setattr(service, "_load_profile", fake_load_profile)

    assert await service.get_tier(UserId(1)) == Tier.T2
    assert await service.get_interests(UserId(1)) == ["value", "macro"]
    assert await service._get_selected_mentor(UserId(1)) == 3


@pytest.mark.asyncio
async def test_user_context_falls_back_when_profile_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = UserContextService()

    async def fake_load_growth_state(_user_id: UserId) -> None:
        return None

    async def fake_load_profile(_user_id: UserId) -> None:
        return None

    monkeypatch.setattr(service, "_load_growth_state", fake_load_growth_state)
    monkeypatch.setattr(service, "_load_profile", fake_load_profile)

    assert await service.get_tier(UserId(1)) == Tier.T1
    assert await service.get_interests(UserId(1)) == []
    assert await service._get_selected_mentor(UserId(1)) is None


@pytest.mark.asyncio
async def test_user_context_prefers_growth_tier_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = UserContextService()

    async def fake_load_growth_state(_user_id: UserId) -> SimpleNamespace:
        return SimpleNamespace(current_tier="T3", last_promotion_attempt_at=None)

    async def fake_load_profile(_user_id: UserId) -> SimpleNamespace:
        return SimpleNamespace(
            current_tier="T1",
            interests_json="[]",
            selected_mentor_id=None,
        )

    monkeypatch.setattr(service, "_load_growth_state", fake_load_growth_state)
    monkeypatch.setattr(service, "_load_profile", fake_load_profile)

    assert await service.get_tier(UserId(1)) == Tier.T3


@pytest.mark.asyncio
async def test_user_context_promotion_context_reads_growth_attempt_timestamp(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = UserContextService()
    last_attempt = datetime(2026, 5, 15, 9, 30, tzinfo=UTC)

    async def fake_load_growth_state(_user_id: UserId) -> SimpleNamespace:
        return SimpleNamespace(
            current_tier="T2",
            last_promotion_attempt_at=last_attempt,
        )

    async def fake_load_user(_user_id: UserId) -> SimpleNamespace:
        return SimpleNamespace(nickname="tester", status="active")

    monkeypatch.setattr(service, "_load_growth_state", fake_load_growth_state)
    monkeypatch.setattr(service, "_load_user", fake_load_user)

    ctx = await service.get_for_promotion_test(UserId(1))

    assert ctx.tier == Tier.T2
    assert ctx.last_promotion_attempt_at == last_attempt
