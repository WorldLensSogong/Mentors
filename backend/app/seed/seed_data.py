from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.curriculum import LearningModule
from app.models.level import LevelDefinition
from app.models.mentor import InterestTopic, InvestmentStrategy, Mentor
from app.models.news import NewsArticle, NewsSource


def seed_all(db: Session) -> None:
    if db.scalar(select(LevelDefinition.id).limit(1)) is not None:
        return

    levels = [
        LevelDefinition(level_no=1, name="Lv.1", min_xp=0, unlock_summary="멘토 채팅, 리포트, 뉴스 탐색"),
        LevelDefinition(level_no=2, name="Lv.2", min_xp=100, unlock_summary="투기장 오픈 예정"),
        LevelDefinition(level_no=3, name="Lv.3", min_xp=250, unlock_summary="추가 멘토 확장"),
        LevelDefinition(level_no=4, name="Lv.4", min_xp=450, unlock_summary="심화 분석 모듈"),
        LevelDefinition(level_no=5, name="Lv.5", min_xp=700, unlock_summary="시나리오 학습"),
    ]
    db.add_all(levels)
    db.flush()

    strategies = [
        InvestmentStrategy(
            code="VALUE",
            name="가치투자",
            description="내재가치 대비 저평가 종목을 찾는 전략",
            principle_summary="기업의 본질 가치와 안전마진을 본다.",
            risk_profile_tag="STABLE",
        ),
        InvestmentStrategy(
            code="GROWTH",
            name="성장투자",
            description="고성장 기업의 미래 확장성을 보는 전략",
            principle_summary="성장률과 산업 확장성을 본다.",
            risk_profile_tag="AGGRESSIVE",
        ),
        InvestmentStrategy(
            code="DIVIDEND",
            name="배당투자",
            description="현금흐름과 배당 지속성을 보는 전략",
            principle_summary="배당과 현금흐름의 안정성을 본다.",
            risk_profile_tag="BALANCED",
        ),
    ]
    db.add_all(strategies)
    db.flush()

    topics = [
        InterestTopic(code="MACRO", name="거시경제", category="MARKET"),
        InterestTopic(code="ETF", name="ETF", category="PRODUCT"),
        InterestTopic(code="STOCK", name="개별주", category="PRODUCT"),
        InterestTopic(code="VALUATION", name="밸류에이션", category="ANALYSIS"),
        InterestTopic(code="DIVIDEND", name="배당", category="ANALYSIS"),
    ]
    db.add_all(topics)
    db.flush()

    mentors = [
        Mentor(
            strategy_id=strategies[0].id,
            unlock_level_id=levels[0].id,
            code="WARREN_STYLE",
            name="워런형 멘토",
            one_liner="숫자와 본질가치로 판단하는 장기 투자 멘토",
            philosophy="좋은 기업을 좋은 가격에 오래 들고 가는 관점을 강조합니다.",
            speaking_style="차분하고 논리적인 설명",
            prompt_template="가치투자 관점으로 설명한다.",
            is_free=True,
        ),
        Mentor(
            strategy_id=strategies[1].id,
            unlock_level_id=levels[0].id,
            code="PETER_STYLE",
            name="피터형 멘토",
            one_liner="성장성과 스토리를 함께 보는 확장형 멘토",
            philosophy="숫자뿐 아니라 성장 동력과 시장 흐름을 함께 봅니다.",
            speaking_style="현실적이지만 빠른 전개를 좋아하는 설명",
            prompt_template="성장투자 관점으로 설명한다.",
            is_free=True,
        ),
        Mentor(
            strategy_id=strategies[2].id,
            unlock_level_id=levels[1].id,
            code="DIVIDEND_STYLE",
            name="배당형 멘토",
            one_liner="현금흐름과 안정성을 중시하는 생활형 멘토",
            philosophy="배당의 지속성과 기업의 체력을 함께 봅니다.",
            speaking_style="안정적이고 생활 밀착형 설명",
            prompt_template="배당투자 관점으로 설명한다.",
            is_free=False,
        ),
    ]
    db.add_all(mentors)
    db.flush()

    source = NewsSource(
        code="NAVER_NEWS",
        name="Naver News",
        source_type="NEWS_API",
        base_url="https://news.naver.com",
        is_active=True,
    )
    db.add(source)
    db.flush()

    now = datetime.now(timezone.utc)
    articles = [
        NewsArticle(
            source_id=source.id,
            external_id="news-001",
            title="미국 기준금리 동결 전망에 기술주 강세",
            summary="금리 동결 기대감이 커지며 성장주 중심의 반등이 나타났습니다.",
            content_text="연준의 금리 동결 가능성이 높아지며 기술주 전반의 투자심리가 회복됐습니다.",
            original_url="https://example.com/news-001",
            publisher="Mock Finance",
            published_at=now - timedelta(hours=3),
        ),
        NewsArticle(
            source_id=source.id,
            external_id="news-002",
            title="국내 ETF 시장에 월배당 상품 자금 유입 확대",
            summary="개인 투자자의 현금흐름 선호가 강해지며 월배당 ETF 수요가 늘고 있습니다.",
            content_text="배당형 ETF의 인기가 높아지면서 안정적 수익을 찾는 수요가 확대되고 있습니다.",
            original_url="https://example.com/news-002",
            publisher="Mock Finance",
            published_at=now - timedelta(hours=6),
        ),
        NewsArticle(
            source_id=source.id,
            external_id="news-003",
            title="AI 반도체 수요 증가로 성장주 기대 확대",
            summary="AI 인프라 투자 확대 기대가 반도체 섹터 전반의 성장 프리미엄을 자극했습니다.",
            content_text="데이터센터와 AI 연산 수요 증가가 반도체 업종 실적 기대를 밀어올리고 있습니다.",
            original_url="https://example.com/news-003",
            publisher="Mock Finance",
            published_at=now - timedelta(hours=12),
        ),
    ]
    db.add_all(articles)
    db.flush()

    modules = [
        LearningModule(
            strategy_id=strategies[0].id,
            level_id=levels[0].id,
            code="VALUE_L1_MARGIN_OF_SAFETY",
            title="안전마진이란 무엇인가",
            concept_summary="가치투자에서 안전마진이 왜 필요한지 이해합니다.",
            quiz_question="안전마진은 무엇을 줄이기 위한 개념인가요?",
            quiz_answer_text="기업 가치 판단의 오차와 시장 변동 위험을 줄이기 위한 개념입니다.",
            sort_order=1,
        ),
        LearningModule(
            strategy_id=strategies[1].id,
            level_id=levels[0].id,
            code="GROWTH_L1_MARKET_SIZE",
            title="성장투자에서 시장 크기 보기",
            concept_summary="성장률만이 아니라 시장의 확장 가능성을 함께 보는 법을 배웁니다.",
            quiz_question="성장투자에서 TAM을 보는 이유는 무엇인가요?",
            quiz_answer_text="기업이 앞으로 커질 수 있는 시장의 크기를 보기 위해서입니다.",
            sort_order=1,
        ),
        LearningModule(
            strategy_id=strategies[2].id,
            level_id=levels[0].id,
            code="DIVIDEND_L1_PAYOUT",
            title="배당 지속성 체크 포인트",
            concept_summary="배당이 계속 유지될 수 있는 기업의 조건을 배웁니다.",
            quiz_question="배당 지속성 판단에 중요한 지표 하나는 무엇인가요?",
            quiz_answer_text="현금흐름 또는 배당성향을 함께 보는 것이 중요합니다.",
            sort_order=1,
        ),
    ]
    db.add_all(modules)
    db.commit()
