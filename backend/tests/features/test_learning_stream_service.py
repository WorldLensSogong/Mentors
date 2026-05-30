import json
from types import SimpleNamespace

import pytest

from core.contracts import SessionId, Tier, UserId, UserStatus
from core.llm.dto import StreamChunk
from core.user_context.dto import MentorChatContext
from features.learning.models import ChatMessage
from features.learning.service import stream_assistant_response
from features.learning.tier_quizzes import get_tier_quiz


class _FakeStreamDb:
    def __init__(self) -> None:
        self.added: list[object] = []
        self.commits = 0

    def add(self, obj: object) -> None:
        self.added.append(obj)

    async def commit(self) -> None:
        self.commits += 1


class _FakeSessionContext:
    def __init__(self, db: _FakeStreamDb) -> None:
        self._db = db

    async def __aenter__(self) -> _FakeStreamDb:
        return self._db

    async def __aexit__(
        self,
        _exc_type: object,
        _exc: object,
        _tb: object,
    ) -> bool:
        return False


@pytest.mark.asyncio
async def test_stream_assistant_response_emits_follow_up_quiz_and_saves_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_db = _FakeStreamDb()
    recommended_quiz = get_tier_quiz("t1-f1")

    async def fake_get_for_mentor_chat(_user_id: UserId) -> MentorChatContext:
        return MentorChatContext(
            user_id=UserId(1),
            nickname="tester",
            tier=Tier.T1,
            status=UserStatus.ACTIVE,
            interests=[],
            selected_mentor_id=None,
        )

    async def fake_get_session(*_args: object, **_kwargs: object) -> SimpleNamespace:
        return SimpleNamespace(mentor_id=1)

    async def fake_list_messages(*_args: object, **_kwargs: object) -> list[object]:
        return []

    class _FakeRagContext:
        is_empty = True

        def as_context_text(self) -> str:
            return ""

    async def fake_retrieve(*_args: object, **_kwargs: object) -> _FakeRagContext:
        return _FakeRagContext()

    async def fake_verify(*_args: object, **_kwargs: object) -> bool:
        return True

    async def fake_evaluate(*_args: object, **_kwargs: object) -> SimpleNamespace:
        return SimpleNamespace(ok=True, reason=None)

    def fake_check_output(*_args: object, **_kwargs: object) -> SimpleNamespace:
        return SimpleNamespace(ok=True, reason=None)

    async def fake_chat_stream(*_args: object, **_kwargs: object):
        yield StreamChunk(delta="안전마진을 먼저 보세요.", done=False)

    async def fake_recommend(*_args: object, **_kwargs: object):
        return recommended_quiz

    monkeypatch.setattr(
        "features.learning.service.user_context.get_for_mentor_chat",
        fake_get_for_mentor_chat,
    )
    monkeypatch.setattr(
        "features.learning.service.SessionLocal",
        lambda: _FakeSessionContext(fake_db),
    )
    monkeypatch.setattr("features.learning.service.get_session", fake_get_session)
    monkeypatch.setattr("features.learning.service.list_messages", fake_list_messages)
    monkeypatch.setattr("features.learning.service.rag.retrieve", fake_retrieve)
    monkeypatch.setattr("features.learning.service.hallucination.verify", fake_verify)
    monkeypatch.setattr("features.learning.service.critic.evaluate", fake_evaluate)
    monkeypatch.setattr("features.learning.service.guardrail.check_output", fake_check_output)
    monkeypatch.setattr("features.learning.service.llm.chat_stream", fake_chat_stream)
    monkeypatch.setattr(
        "features.learning.service.recommend_tier_quiz_for_chat",
        fake_recommend,
    )

    events = [
        event
        async for event in stream_assistant_response(
            session_id=SessionId(1),
            user_id=UserId(1),
            user_content="안전마진이 왜 중요한가요?",
        )
    ]

    assert [event["event"] for event in events] == ["delta", "follow_up_quiz"]
    assert json.loads(events[0]["data"])["delta"] == "안전마진을 먼저 보세요."
    assert json.loads(events[1]["data"])["question_id"] == recommended_quiz.question_id
    assert fake_db.commits == 1
    assert len(fake_db.added) == 1
    assert isinstance(fake_db.added[0], ChatMessage)
    assert fake_db.added[0].role == "assistant"
    assert fake_db.added[0].content == "안전마진을 먼저 보세요."
