from __future__ import annotations

from core.contracts import Tier
from features.growth.catalog import list_concepts_for_tier

from .tier_quizzes import TierQuiz, list_tier_quizzes

_CONCEPT_KEYWORDS: dict[int, tuple[str, ...]] = {
    101: ("안전마진", "안전 마진", "싸게 사기", "할인 매수"),
    102: ("내재가치", "적정가치", "본질가치", "본질 가치"),
    103: ("장기투자", "장기 투자", "오래 보유", "복리"),
    104: ("변동성", "위험", "주가 하락", "가격 흔들림"),
    105: ("좋은 기업", "좋은 사업", "해자", "현금흐름"),
    201: ("트레이드오프", "트레이드 오프", "장단점 비교", "기회비용"),
    202: ("반대 의견", "반대 논리", "반론", "다른 관점"),
    203: ("비중", "포지션 사이즈", "한 종목 비중", "몰빵"),
    204: ("포트폴리오", "분산", "상관관계", "섹터 쏠림"),
    205: ("투자 논리", "매수 이유", "매도 기준", "가설 점검"),
    301: ("다양한 관점", "여러 멘토", "서로 다른 관점", "관점 비교"),
    302: ("섹터", "섹터 순환", "업종 순환", "업종 이동"),
    303: ("매크로", "pmi", "cpi", "실업률"),
    304: ("시나리오", "기본 시나리오", "낙관 시나리오", "비관 시나리오"),
    305: ("리밸런싱", "자산 배분", "현금 비중", "비중 조절"),
    401: ("금리", "금리 인상", "금리 인하", "금리 민감도"),
    402: ("매크로 국면", "경기 국면", "인플레이션", "경기 둔화"),
    403: ("이익의 질", "현금흐름", "재고 증가", "일회성 이익"),
    404: ("스트레스 테스트", "스트레스테스트", "최악의 경우", "가정 점검"),
    405: ("사이클", "경기 순환", "국면 판단", "사이클 판단"),
    501: ("독립적인 논리", "내 논리", "스스로 판단", "남 따라"),
    502: ("프레임워크", "틀 조합", "여러 기준", "복합 판단"),
    503: ("리스크 관리", "손실 관리", "최대 비중", "규칙"),
    504: ("시장 맥락", "시장 흐름", "큰 그림", "전체 문맥"),
    505: ("복기", "실수 점검", "왜 틀렸는지", "자기 점검"),
}


def recommend_quiz_for_text(
    tier: Tier,
    text: str,
    solved_question_ids: set[str] | frozenset[str],
) -> TierQuiz | None:
    matched_concept_ids = _rank_matched_concepts(tier, text)
    if not matched_concept_ids:
        return None

    quizzes = list_tier_quizzes(tier)
    for concept_id in matched_concept_ids:
        concept_quizzes = [
            quiz
            for quiz in quizzes
            if quiz.concept_id == concept_id and quiz.question_id not in solved_question_ids
        ]
        if concept_quizzes:
            return concept_quizzes[0]

    return None


def _rank_matched_concepts(tier: Tier, text: str) -> list[int]:
    normalized = _normalize(text)
    if not normalized:
        return []

    scored: list[tuple[int, int]] = []
    for concept in list_concepts_for_tier(tier):
        score = 0
        for keyword in _CONCEPT_KEYWORDS.get(concept.id, ()):
            if _normalize(keyword) in normalized:
                score += 2 if len(keyword) >= 4 else 1
        if score > 0:
            scored.append((concept.id, score))

    scored.sort(key=lambda item: (-item[1], item[0]))
    return [concept_id for concept_id, _score in scored]


def _normalize(text: str) -> str:
    return text.casefold().replace(" ", "")


__all__ = ["recommend_quiz_for_text"]
