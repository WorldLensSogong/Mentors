import pytest

from core.contracts import MentorStrategy, Tier, UserId
from features.growth.read_service import GrowthReadService


class _FakeScalarResult:
    def __init__(self, values: list[int]) -> None:
        self._values = values

    def all(self) -> list[int]:
        return list(self._values)


class _FakeExecuteResult:
    def __init__(
        self,
        *,
        scalar_values: list[int] | None = None,
        grouped_rows: list[tuple[str, int]] | None = None,
    ) -> None:
        self._scalar_values = scalar_values or []
        self._grouped_rows = grouped_rows or []

    def scalars(self) -> _FakeScalarResult:
        return _FakeScalarResult(self._scalar_values)

    def all(self) -> list[tuple[str, int]]:
        return list(self._grouped_rows)


class _FakeSession:
    def __init__(
        self,
        *,
        tier_state: object | None,
        mastered_ids: list[int] | None = None,
        grouped_rows: list[tuple[str, int]] | None = None,
    ) -> None:
        self._tier_state = tier_state
        self._mastered_ids = mastered_ids or []
        self._grouped_rows = grouped_rows or []

    async def get(self, _model: object, _pk: int) -> object | None:
        return self._tier_state

    async def execute(self, _stmt: object) -> _FakeExecuteResult:
        if self._grouped_rows:
            return _FakeExecuteResult(grouped_rows=self._grouped_rows)
        return _FakeExecuteResult(scalar_values=self._mastered_ids)


class _FakeSessionContext:
    def __init__(self, session: _FakeSession) -> None:
        self._session = session

    async def __aenter__(self) -> _FakeSession:
        return self._session

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None


@pytest.mark.asyncio
async def test_growth_read_service_returns_tier_and_mastered_learning_concepts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tier_state = type("TierStateStub", (), {"current_tier": Tier.T2.value})()
    fake_session = _FakeSession(tier_state=tier_state, mastered_ids=[1, 3, 9])
    monkeypatch.setattr(
        "features.growth.read_service.SessionLocal",
        lambda: _FakeSessionContext(fake_session),
    )

    service = GrowthReadService()

    assert await service.get_user_tier(UserId(1)) == Tier.T2
    assert await service.get_mastered_concepts(UserId(1), MentorStrategy.VALUE) == {1, 3, 9}
    assert await service.get_mastered_concepts(UserId(1), MentorStrategy.GROWTH) == set()


@pytest.mark.asyncio
async def test_growth_read_service_returns_tier_distribution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_session = _FakeSession(
        tier_state=None,
        grouped_rows=[(Tier.T1.value, 2), (Tier.T2.value, 1)],
    )
    monkeypatch.setattr(
        "features.growth.read_service.SessionLocal",
        lambda: _FakeSessionContext(fake_session),
    )

    service = GrowthReadService()
    distribution = await service.get_tier_distribution()

    assert distribution == {Tier.T1: 2, Tier.T2: 1}
