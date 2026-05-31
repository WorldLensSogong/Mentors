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
        question="다음 중 PER에 대한 설명으로 가장 알맞은 것은 무엇인가요?",
        options=[
            "현재 주가가 주당순자산의 몇 배인지 보여주는 지표로, 자산가치 평가에 주로 쓰인다.",
            (
                "현재 주가가 주당순이익의 몇 배 수준인지 보여주는 지표로, "
                "이익 대비 가격을 비교할 때 쓴다."
            ),
            "기업이 보유한 현금성 자산을 발행주식 수로 나눈 값으로, 유동성 평가에 주로 쓰인다.",
            "기업이 지급한 총배당금을 시가총액으로 나눈 값으로, 배당 매력만을 보여주는 지표다.",
        ],
        correct_index=1,
        explanation=(
            "PER은 현재 주가를 주당순이익(EPS)으로 나눈 값입니다. "
            "같은 산업 안에서 기업의 이익 대비 가격 수준을 비교할 때 자주 활용됩니다."
        ),
    ),
    2: QuizItem(
        concept_id=2,
        concept_name="복리 (Compound Interest)",
        question="복리 효과를 가장 잘 활용하는 투자 행동은 무엇인가요?",
        options=[
            "수익이 날 때마다 전부 실현하고 다음 기회를 새로 찾는 것",
            "배당과 이자를 계속 인출해 소비하고 원금은 그대로 두는 것",
            "발생한 수익을 다시 투자하면서 긴 시간을 확보하는 것",
            "수익률을 빠르게 높이기 위해 차입 비중을 지속적으로 키우는 것",
        ],
        correct_index=2,
        explanation=(
            "복리는 원금뿐 아니라 쌓인 수익에도 다시 수익이 붙는 구조입니다. "
            "그래서 수익 재투자와 긴 투자 기간이 핵심 조건입니다."
        ),
    ),
    3: QuizItem(
        concept_id=3,
        concept_name="안전마진 (Margin of Safety)",
        question="가치투자에서 말하는 안전마진에 대한 설명으로 가장 알맞은 것은 무엇인가요?",
        options=[
            "기업의 추정 내재가치보다 주가가 충분히 낮아, 분석 오차를 흡수할 여지를 두는 개념",
            "주가가 20일 이동평균선 아래에 있을 때 자동으로 확보되는 기술적 매수 구간",
            "손실이 발생하면 증권사가 일정 비율을 보전해 주는 제도적 안전장치",
            "배당수익률이 국채금리보다 높을 때 무조건 성립하는 가격 매력 구간",
        ],
        correct_index=0,
        explanation=(
            "안전마진은 내재가치 추정이 틀릴 가능성까지 감안해, "
            "충분히 할인된 가격에서 투자하려는 사고방식입니다."
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
