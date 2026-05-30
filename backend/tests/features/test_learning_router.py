import importlib
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.auth.dependencies import get_current_user
from core.contracts import UserId
from core.db import get_db
from core.exceptions import register_exception_handlers
from features.learning.tier_quizzes import get_tier_quiz


class _ExplodingUser:
    def __init__(self) -> None:
        self._reads = 0

    @property
    def id(self) -> int:
        self._reads += 1
        if self._reads > 1:
            raise RuntimeError("user.id should not be accessed twice")
        return 1


class _FakeDb:
    async def commit(self) -> None:
        return None


async def _fake_db() -> AsyncIterator[_FakeDb]:
    yield _FakeDb()


def _build_app() -> FastAPI:
    from features.learning.router import router

    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router)
    return app


def test_submit_quiz_caches_user_id_before_late_side_effects(monkeypatch) -> None:
    learning_router = importlib.import_module("features.learning.router")
    quiz = get_tier_quiz("t2-f5")

    async def fake_submit_tier_quiz(
        *,
        user_id: UserId,
        question_id: str,
        answer_index: int,
        db: object,
    ) -> object:
        assert user_id == UserId(1)
        assert question_id == quiz.question_id
        assert answer_index == quiz.correct_index
        return type(
            "Outcome",
            (),
            {
                "correct": True,
                "explanation": quiz.explanation,
                "quiz": quiz,
            },
        )()

    published_events: list[object] = []

    async def fake_publish(event: object) -> None:
        published_events.append(event)

    app = _build_app()
    app.dependency_overrides[get_current_user] = _ExplodingUser
    app.dependency_overrides[get_db] = _fake_db
    monkeypatch.setattr(learning_router.quizzes, "submit_tier_quiz", fake_submit_tier_quiz)
    monkeypatch.setattr(learning_router.event_bus, "publish", fake_publish)

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/learning/quizzes/submit",
                json={"question_id": quiz.question_id, "answer_index": quiz.correct_index},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"correct": True, "explanation": quiz.explanation}
    assert len(published_events) == 1
