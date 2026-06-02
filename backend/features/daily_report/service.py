"""일일 리포트 생성 서비스 (Phase 1: 생산자).

- DailyReportCore: 사용자×날짜 1회 공통 시장 코어 (멘토 무관)
- DailyReport: 멘토 전략별 리포트 (user × strategy × date)

모든 진입점은 멱등(get-or-create)이다. cron fan-out(선택 멘토 pre-warm)과
'그날 그 멘토 첫 진입' lazy 생성이 같은 (user, strategy, date)에 동시에 와도
UNIQUE 제약 + ON CONFLICT DO NOTHING으로 안전하다.

owner: daily_report / 관련 FR: FR-03, UC-02
boundary: cross-feature read는 user_context·core.read_services 만 사용 (ADR-014).
"""

import json
import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from core.contracts import (
    DailyReportGeneratedEvent,
    MentorStrategy,
    NewsId,
    ReportId,
    Tier,
    UserId,
)
from core.db import SessionLocal
from core.event_bus import event_bus
from core.llm import llm
from core.push import push
from core.read_services import NewsRef, content_reader
from core.user_context import user_context

from .models import DailyReport, DailyReportCore
from .prompts import build_market_summary_prompt, build_report_prompt

logger = logging.getLogger("daily_report.service")

# KST는 DST가 없어 고정 UTC+9. zoneinfo/tzdata 의존 없이 '오늘(서울)'을 안전하게 계산.
_KST = timezone(timedelta(hours=9))
_NEWS_TOP_K = 3
_DEFAULT_STRATEGY = MentorStrategy.VALUE


def _today() -> date:
    return datetime.now(_KST).date()


# ----------------------------------------------------------------------
# LLM 본문 생성 (+ 무키 환경 fallback)
# ----------------------------------------------------------------------


def _fallback_market_summary(news: list[NewsRef]) -> str:
    if not news:
        return "오늘은 선별된 시장 뉴스가 없어요."
    titles = " · ".join(n.title for n in news[:_NEWS_TOP_K])
    return f"오늘 눈에 띈 소식: {titles}"


def _fallback_body(
    nickname: str,
    news: list[NewsRef],
    market_summary: str | None,
) -> str:
    lines = [
        f"{nickname}님, 오늘의 시장 브리핑이에요.",
        "",
        "## 오늘의 시장",
        market_summary or "오늘은 비교적 조용한 흐름이에요.",
    ]
    if news:
        lines += ["", "## 주목할 소식", *[f"- {n.title}" for n in news[:_NEWS_TOP_K]]]
    lines += ["", "## 오늘의 한 걸음", "이 소식, 멘토와 함께 더 깊이 들여다볼까요?"]
    return "\n".join(lines)


async def _summarize_market(news: list[NewsRef]) -> str:
    """멘토 무관 중립 시장 요약. 실패/무키 시 뉴스 제목 fallback."""
    if not news or not llm.configured:
        return _fallback_market_summary(news)
    try:
        resp = await llm.chat(
            build_market_summary_prompt(news),
            use_case="content",
            max_tokens=400,
            temperature=0.5,
        )
    except Exception:  # noqa: BLE001 — 어떤 LLM 오류여도 리포트는 생성돼야 함
        logger.warning("daily_report.market_summary_failed")
        return _fallback_market_summary(news)
    return resp.text.strip() or _fallback_market_summary(news)


async def _compose_body(
    strategy: MentorStrategy,
    tier: Tier,
    nickname: str,
    news: list[NewsRef],
    market_summary: str | None,
) -> str:
    """멘토 전략 렌즈 + 티어 깊이로 리포트 본문 생성. 실패/무키 시 템플릿 fallback."""
    if not llm.configured:
        return _fallback_body(nickname, news, market_summary)
    try:
        resp = await llm.chat(
            build_report_prompt(strategy, tier, nickname, news, market_summary),
            max_tokens=1200,
            temperature=0.7,
        )
    except Exception:  # noqa: BLE001 — 본문 생성 실패해도 fallback으로 리포트 보장
        logger.warning("daily_report.body_failed", extra={"strategy": strategy.value})
        return _fallback_body(nickname, news, market_summary)
    return resp.text.strip() or _fallback_body(nickname, news, market_summary)


# ----------------------------------------------------------------------
# get-or-create (멱등)
# ----------------------------------------------------------------------


async def _get_or_create_core(
    user_id: UserId,
    report_date: date,
    session: AsyncSession,
) -> DailyReportCore:
    """사용자×날짜 공통 코어. 없으면 뉴스 선별 + 중립 요약 후 생성."""
    existing = await session.scalar(
        select(DailyReportCore).where(
            DailyReportCore.user_id == int(user_id),
            DailyReportCore.report_date == report_date,
        )
    )
    if existing is not None:
        return existing

    news = await content_reader.get_today_news_for_user(user_id, top_k=_NEWS_TOP_K)
    market_summary = await _summarize_market(news)

    await session.execute(
        pg_insert(DailyReportCore)
        .values(
            user_id=int(user_id),
            report_date=report_date,
            news_ids_json=json.dumps([int(n.id) for n in news]),
            market_summary=market_summary,
            # TODO: LearningReader 도입 시 학습 개념 연결 (현재 boundary상 보류)
            today_concept_id=None,
        )
        .on_conflict_do_nothing(index_elements=["user_id", "report_date"])
    )

    core = await session.scalar(
        select(DailyReportCore).where(
            DailyReportCore.user_id == int(user_id),
            DailyReportCore.report_date == report_date,
        )
    )
    if core is None:  # pragma: no cover — insert/conflict 직후엔 반드시 존재
        raise RuntimeError("daily_report_core upsert로도 행이 없습니다")
    return core


async def _load_core_news(core: DailyReportCore) -> list[NewsRef]:
    """코어가 스냅샷한 뉴스 id로 NewsRef 복원 (top_k=3이라 N+1 무시 가능)."""
    try:
        ids = json.loads(core.news_ids_json or "[]")
    except json.JSONDecodeError:
        return []
    refs: list[NewsRef] = []
    for raw in ids:
        ref = await content_reader.get_news_by_id(NewsId(int(raw)))
        if ref is not None:
            refs.append(ref)
    return refs


async def _get_or_create_report(
    user_id: UserId,
    strategy: MentorStrategy,
    report_date: date,
    session: AsyncSession,
) -> tuple[DailyReport, bool]:
    """그날 그 전략 리포트. 반환: (리포트, 이번 호출이 새로 만들었는지)."""
    existing = await session.scalar(
        select(DailyReport).where(
            DailyReport.user_id == int(user_id),
            DailyReport.mentor_strategy == strategy.value,
            DailyReport.report_date == report_date,
        )
    )
    if existing is not None:
        return existing, False

    ctx = await user_context.get_for_daily_report(user_id)
    core = await _get_or_create_core(user_id, report_date, session)
    news = await _load_core_news(core)
    body = await _compose_body(strategy, ctx.tier, ctx.nickname, news, core.market_summary)
    highlights = [{"news_id": int(n.id), "title": n.title} for n in news]

    inserted_id = await session.scalar(
        pg_insert(DailyReport)
        .values(
            user_id=int(user_id),
            core_id=core.id,
            report_date=report_date,
            mentor_strategy=strategy.value,
            tier=ctx.tier.value,
            status="ready",
            body=body,
            highlights_json=json.dumps(highlights, ensure_ascii=False),
        )
        .on_conflict_do_nothing(
            index_elements=["user_id", "mentor_strategy", "report_date"]
        )
        .returning(DailyReport.id)
    )
    created = inserted_id is not None

    report = await session.scalar(
        select(DailyReport).where(
            DailyReport.user_id == int(user_id),
            DailyReport.mentor_strategy == strategy.value,
            DailyReport.report_date == report_date,
        )
    )
    if report is None:  # pragma: no cover — insert/conflict 직후엔 반드시 존재
        raise RuntimeError("daily_report upsert로도 행이 없습니다")
    return report, created


# ----------------------------------------------------------------------
# 공개 진입점
# ----------------------------------------------------------------------


async def resolve_strategy(user_id: UserId) -> MentorStrategy:
    """선택 멘토 전략 해석 (content 동과 동일 boundary 패턴).

    user_context가 아직 전략을 노출하지 않으면 기본 VALUE. 학습 동에 대한 직접
    의존(get_mentor_strategy import)을 피하려고 user_context를 거친다.
    """
    try:
        ctx = await user_context.get_for_mentor_chat(user_id)
    except Exception:  # noqa: BLE001 — 컨텍스트 조회 실패 시 기본 전략으로 진행
        return _DEFAULT_STRATEGY
    raw = getattr(ctx, "selected_mentor_strategy", None)
    if raw is None:
        return _DEFAULT_STRATEGY
    try:
        return MentorStrategy(str(raw.value) if hasattr(raw, "value") else str(raw))
    except ValueError:
        return _DEFAULT_STRATEGY


async def get_or_create_today_report(
    user_id: UserId,
    strategy: MentorStrategy,
) -> DailyReport:
    """그날 그 멘토(전략) 리포트 get-or-create. Phase 3 리더/라우터 진입점."""
    async with SessionLocal() as session:
        report, _ = await _get_or_create_report(user_id, strategy, _today(), session)
        await session.commit()
    return report


async def get_today_report(
    user_id: UserId,
    strategy: MentorStrategy,
) -> DailyReport | None:
    """오늘 리포트 조회 전용 (생성하지 않음)."""
    async with SessionLocal() as session:
        report: DailyReport | None = await session.scalar(
            select(DailyReport).where(
                DailyReport.user_id == int(user_id),
                DailyReport.mentor_strategy == strategy.value,
                DailyReport.report_date == _today(),
            )
        )
    return report


async def generate_for_user(user_id: UserId) -> None:
    """단일 사용자 pre-warm. 멱등 — 같은 날 중복 호출 안전.

    cron fan-out → 핸들러가 호출. 선택 멘토 전략 1개만 미리 생성하고, 나머지
    전략은 그날 그 멘토 첫 진입 때 lazy 생성된다. 새로 생성된 경우에만
    이벤트 발행 + 푸시(중복 알림 방지).
    """
    report_date = _today()
    strategy = await resolve_strategy(user_id)

    async with SessionLocal() as session:
        report, created = await _get_or_create_report(user_id, strategy, report_date, session)
        await session.commit()

    if not created:
        logger.info(
            "daily_report.already_exists",
            extra={"user_id": user_id, "report_id": report.id, "strategy": strategy.value},
        )
        return

    await event_bus.publish(
        DailyReportGeneratedEvent(user_id=user_id, report_id=ReportId(report.id))
    )

    ctx = await user_context.get_for_daily_report(user_id)
    await push.send_to_user(
        user_id=user_id,
        title="오늘의 리포트가 도착했어요",
        body=f"{ctx.nickname}님, 오늘의 시장 흐름을 확인해보세요.",
        data={"deeplink": f"mentors://report/{report.id}"},
    )

    logger.info(
        "daily_report.generated",
        extra={"user_id": user_id, "report_id": report.id, "strategy": strategy.value},
    )


__all__ = [
    "generate_for_user",
    "get_or_create_today_report",
    "get_today_report",
    "resolve_strategy",
]
