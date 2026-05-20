import importlib

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.auth.dependencies import get_current_user
from core.auth.models import User
from core.exceptions import BadRequestError, register_exception_handlers


def _fake_user() -> User:
    return User(id=1, email="user@example.com", nickname="tester", status="active")


def _build_app() -> FastAPI:
    from features.growth.router import router

    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router)
    return app


def test_growth_progress_route_requires_auth() -> None:
    with TestClient(_build_app()) as client:
        response = client.get("/api/growth/me/progress")

    assert response.status_code == 401


def test_growth_promotion_test_route_requires_auth() -> None:
    with TestClient(_build_app()) as client:
        response = client.post("/api/growth/promotion-test", json={"answers": []})

    assert response.status_code == 401


def test_growth_progress_route_returns_service_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    growth_router = importlib.import_module("features.growth.router")

    async def fake_get_progress(*_args: object, **_kwargs: object) -> dict[str, object]:
        return {
            "current_tier": "T2",
            "next_tier": "T3",
            "progress_percent": 80,
            "mastered_concepts": 4,
            "total_concepts": 5,
            "eligible_for_promotion": True,
            "promotion_eligible_at": "2026-05-15T00:00:00Z",
            "unlocked_features": ["debate_arena"],
            "next_unlocks": ["extra_mentors"],
            "promotion_test": {
                "target_tier": "T3",
                "passing_score": 80,
                "question_count": 5,
                "questions": [
                    {
                        "question_id": "t2-q1",
                        "prompt": "What matters most in a debate unlock?",
                        "choices": [
                            {"choice_id": "A", "text": "Current tier progress"},
                            {"choice_id": "B", "text": "Random timing"},
                        ],
                    }
                ],
            },
        }

    app = _build_app()
    app.dependency_overrides[get_current_user] = _fake_user
    monkeypatch.setattr(growth_router, "get_growth_progress", fake_get_progress)

    try:
        with TestClient(app) as client:
            response = client.get("/api/growth/me/progress")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["current_tier"] == "T2"
    assert body["promotion_test"]["target_tier"] == "T3"
    assert body["unlocked_features"] == ["debate_arena"]


def test_growth_promotion_test_route_returns_result(monkeypatch: pytest.MonkeyPatch) -> None:
    growth_router = importlib.import_module("features.growth.router")

    async def fake_submit_test(*_args: object, **_kwargs: object) -> dict[str, object]:
        return {
            "previous_tier": "T1",
            "current_tier": "T2",
            "target_tier": "T2",
            "passed": True,
            "score_percent": 80,
            "correct_answers": 4,
            "total_questions": 5,
            "unlocked_features": ["debate_arena"],
            "message": "Promotion test passed.",
        }

    app = _build_app()
    app.dependency_overrides[get_current_user] = _fake_user
    monkeypatch.setattr(growth_router, "submit_promotion_test", fake_submit_test)

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/growth/promotion-test",
                json={
                    "answers": [
                        {"question_id": "t1-q1", "choice_id": "A"},
                        {"question_id": "t1-q2", "choice_id": "B"},
                    ]
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["passed"] is True
    assert body["current_tier"] == "T2"
    assert body["score_percent"] == 80


def test_growth_promotion_test_route_returns_domain_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    growth_router = importlib.import_module("features.growth.router")

    async def fake_submit_test(*_args: object, **_kwargs: object) -> dict[str, object]:
        raise BadRequestError("Promotion test is not available yet.")

    app = _build_app()
    app.dependency_overrides[get_current_user] = _fake_user
    monkeypatch.setattr(growth_router, "submit_promotion_test", fake_submit_test)

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/growth/promotion-test",
                json={"answers": [{"question_id": "t1-q1", "choice_id": "A"}]},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["code"] == "bad_request"
