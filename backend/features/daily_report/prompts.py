"""일일 리포트 생성용 프롬프트.

daily_report 동이 리포트의 '목소리'를 직접 소유한다. 학습 동의 페르소나
프롬프트(features/learning/personas)를 가져오면 동 경계(ADR-014)를 침범하므로,
전략별 해석 렌즈를 여기서 가볍게 따로 정의한다.
"""

from core.ai_pipeline import tier_overlay
from core.contracts import MentorStrategy, MessageRole, Tier
from core.llm import Message
from core.read_services import NewsRef

# 전략별 해석 렌즈 — 같은 뉴스를 어떤 관점으로 읽을지.
_STRATEGY_LENS: dict[MentorStrategy, str] = {
    MentorStrategy.VALUE: (
        "너는 가치투자 멘토다. 내재가치 대비 가격, 안전마진, 기업 펀더멘털 관점에서 "
        "오늘의 시장을 해석한다. 단기 급등락보다 장기 본질 가치에 주목한다."
    ),
    MentorStrategy.GROWTH: (
        "너는 성장투자 멘토다. 매출·이익 성장성, 시장 확장, 미래 잠재력 관점에서 "
        "오늘의 시장을 해석한다. 성장 모멘텀과 산업 트렌드에 주목한다."
    ),
    MentorStrategy.DIVIDEND: (
        "너는 배당투자 멘토다. 배당 안정성, 현금흐름, 주주환원 관점에서 오늘의 "
        "시장을 해석한다. 변동성보다 꾸준한 인컴과 재무 건전성에 주목한다."
    ),
    MentorStrategy.MOMENTUM: (
        "너는 모멘텀투자 멘토다. 가격·거래량 추세와 시장 심리 관점에서 오늘의 "
        "시장을 해석한다. 현재 흐름의 강도와 전환 신호에 주목한다."
    ),
}

_REPORT_FORMAT = (
    "출력 형식 (마크다운):\n"
    "1. 독자 닉네임을 부르는 한 문장 인사 + 오늘 전략 관점의 핵심 메시지 한 줄\n"
    "2. '## 오늘의 시장' — 아래 제공된 뉴스에 실제로 등장한 사건·기업·테마를 근거로 "
    "2~3문장 해석. 뉴스에 없는 일반론·추측은 쓰지 않는다.\n"
    "3. '## 주목할 소식' — 제공된 뉴스 중 이 전략 관점에서 가장 의미 있는 1~2개를 골라 "
    "'- ' 불릿으로, 각 1문장씩 '왜 이 전략에 중요한지'를 구체적으로 설명\n"
    "4. '## 오늘의 한 걸음' — 위 내용과 이어지는, 멘토와 대화를 시작하고 싶게 만드는 "
    "구체적 질문 한 줄\n"
    "규칙: 뉴스가 제공되면 반드시 그 내용을 근거로 쓴다('특별한 뉴스가 없다'는 식의 "
    "회피 금지). 투자 권유·단정적 수익 보장·매수매도 지시는 금지. 정보 제공과 사고 "
    "자극에 집중한다. 전체 350~600자 내외로 간결하게."
)


def _news_block(news: list[NewsRef]) -> str:
    if not news:
        return "(오늘 선별된 뉴스 없음)"
    return "\n".join(f"- [{int(n.id)}] {n.title}" for n in news)


def build_market_summary_prompt(news: list[NewsRef]) -> list[Message]:
    """멘토 무관 중립 시장 요약 (공통 코어용)."""
    system = (
        "너는 중립적인 시장 애널리스트다. 특정 투자 전략에 치우치지 않고, 아래 제공된 "
        "뉴스에 실제로 등장한 사건·기업·지표를 근거로 오늘의 흐름을 2~3문장으로 "
        "구체적으로 요약한다. 뉴스에 없는 추측이나 투자 권유는 하지 않는다."
    )
    user = f"오늘의 주요 뉴스:\n{_news_block(news)}\n\n위 흐름을 중립적으로 요약해줘."
    return [
        Message(role=MessageRole.SYSTEM, content=system),
        Message(role=MessageRole.USER, content=user),
    ]


def build_report_prompt(
    strategy: MentorStrategy,
    tier: Tier,
    nickname: str,
    news: list[NewsRef],
    market_summary: str | None,
) -> list[Message]:
    """멘토 전략 렌즈 + 티어 깊이로 개인화된 일일 브리핑."""
    lens = _STRATEGY_LENS.get(strategy, _STRATEGY_LENS[MentorStrategy.VALUE])
    system = tier_overlay.apply(f"{lens}\n\n{_REPORT_FORMAT}", tier)
    user = (
        f"독자: {nickname}님 (티어 {tier.value})\n\n"
        f"[중립 시장 요약]\n{market_summary or '(요약 없음)'}\n\n"
        f"[오늘의 뉴스]\n{_news_block(news)}\n\n"
        f"{nickname}님을 위한 오늘의 리포트를 작성해줘."
    )
    return [
        Message(role=MessageRole.SYSTEM, content=system),
        Message(role=MessageRole.USER, content=user),
    ]


__all__ = ["build_market_summary_prompt", "build_report_prompt"]
