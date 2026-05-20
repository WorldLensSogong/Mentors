"""투자 개념 커리큘럼 및 퀴즈 카탈로그.

owner: learning
관련 FR: FR-02, UC-04
"""

from pydantic import BaseModel

from core.exceptions import NotFoundError


class QuizItem(BaseModel):
    concept_id: int
    concept_name: str
    question: str
    options: list[str]
    correct_index: int
    explanation: str


# 핵심 개념 3가지 샘플 정의
_QUIZ_CATALOG: dict[int, QuizItem] = {
    1: QuizItem(
        concept_id=1,
        concept_name="PER (주가수익비율)",
        question="다음 중 PER(Price Earning Ratio)에 대한 설명으로 가장 적절한 것은?",
        options=[
            "기업의 순자산 대비 시가총액을 나타내는 지표이다.",
            "현재 주가가 주당순이익(EPS)의 몇 배인지 나타내며, 투자원금 회수 기간을 의미한다.",
            "기업의 총부채를 자본 총계로 나눈 비율이다.",
            "기업이 1년 동안 지급한 배당금 총액을 의미한다.",
        ],
        correct_index=1,
        explanation=(
            "PER은 주가를 주당순이익으로 나눈 값으로, 현재 수익력 기준으로 "
            "투자금을 회수하는 데 걸리는 예상 연수를 나타냅니다."
        ),
    ),
    2: QuizItem(
        concept_id=2,
        concept_name="복리 (Compound Interest)",
        question="투자에서 '복리의 효과'를 극대화하기 위해 가장 중요한 요소는 무엇인가요?",
        options=[
            "최대한 잦은 단타 매매를 통한 회전율 극대화",
            "발생한 수익(배당, 이자 등)을 인출하여 소비하는 것",
            "수익금을 재투자하여 원금을 키우고 충분한 시간을 유지하는 것",
            "부채를 최대로 끌어와서 레버리지를 일으키는 것",
        ],
        correct_index=2,
        explanation=(
            "복리는 원금뿐만 아니라 이자에도 이자가 붙는 방식으로, "
            "수익의 재투자 및 장기 투자가 핵심 성공 요인입니다."
        ),
    ),
    3: QuizItem(
        concept_id=3,
        concept_name="안전마진 (Margin of Safety)",
        question="가치투자에서 말하는 '안전마진'의 개념을 올바르게 설명한 것은?",
        options=[
            "주가가 기업의 내재가치보다 충분히 낮을 때 생기는 가격의 완충 지대",
            "정부가 예금자 보호법을 통해 보장해주는 최대 금액",
            "손실이 발생했을 때 증권사가 대신 보전해주는 보증 비율",
            "주가가 전고점 대비 50% 이상 하락했음을 확인하는 기술적 신호",
        ],
        correct_index=0,
        explanation=(
            "안전마진은 내재가치와 시장 가격의 격차를 뜻하며, "
            "분석의 오류나 불의의 악재로부터 투자자를 보호하는 역할을 합니다."
        ),
    ),
}


def get_quiz(concept_id: int) -> QuizItem:
    """개념 ID에 해당하는 퀴즈를 반환한다."""
    quiz = _QUIZ_CATALOG.get(concept_id)
    if quiz is None:
        raise NotFoundError("해당 개념의 퀴즈를 찾을 수 없습니다")
    return quiz


def grade_quiz(concept_id: int, answer_index: int) -> tuple[bool, str]:
    """퀴즈 정답을 채점하고 결과 및 해설을 반환한다."""
    quiz = get_quiz(concept_id)
    is_correct = quiz.correct_index == answer_index
    return (is_correct, quiz.explanation)


__all__ = ["QuizItem", "get_quiz", "grade_quiz"]
