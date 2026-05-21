"""투자 개념 확인 퀴즈 카탈로그.

owner: learning
관련 FR: FR-02, UC-04

각 퀴즈는 Concept(features/learning/curriculum.py)에 1:N으로 묶인다.
MVP 시드는 개념당 1개. 클라이언트 응답은 `QuizView`(concept_name join 포함).

향후 확장: 개념당 2~3개로 늘려 한 개념을 다각도로 검증 (계획서 §1.1).
구조는 이미 `dict[ConceptId, list[QuizItem]]`이라 데이터만 추가하면 됨.
"""

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.contracts import ConceptId, UserId
from core.exceptions import NotFoundError

from .curriculum import get_concept
from .models import QuizAttempt

# --- 모델 ---


class QuizItem(BaseModel):
    """확인 퀴즈 단건. 한 개념에 여러 개 가능 (현재 시드는 개념당 1개)."""

    concept_id: ConceptId
    question: str
    options: list[str]
    correct_index: int
    explanation: str


class QuizView(BaseModel):
    """라우터 응답용 — Concept과 QuizItem을 join한 뷰."""

    concept_id: ConceptId
    concept_name: str
    question: str
    options: list[str]
    correct_index: int
    explanation: str


# --- 시드 데이터: VALUE 23개 (개념당 1개) ---


def _cid(n: int) -> ConceptId:
    return ConceptId(n)


_QUIZZES: dict[ConceptId, list[QuizItem]] = {
    _cid(1): [
        QuizItem(
            concept_id=_cid(1),
            question="다음 중 주식의 본질에 대한 설명으로 가장 적절한 것은?",
            options=[
                "매일 사고팔며 단기 차익을 노리는 디지털 수표이다.",
                ("회사의 지분 일부를 소유하는 권리이며, 회사의 미래 이익을 나눠 받을 자격이다."),
                "정부가 발행해 원금과 이자를 보장하는 증권이다.",
                "기업이 빌린 돈을 갚겠다는 약속 증서이다.",
            ],
            correct_index=1,
            explanation=(
                "주식은 기업의 지분 소유권으로, "
                "회사가 만들어내는 미래 이익의 일부를 청구할 권리를 갖습니다."
            ),
        )
    ],
    _cid(2): [
        QuizItem(
            concept_id=_cid(2),
            question="채권과 주식의 가장 본질적인 차이는?",
            options=[
                "발행 국가가 다르다.",
                ("채권은 빌려준 돈에 대한 청구권, 주식은 회사 지분에 대한 청구권이다."),
                "채권은 가격이 변하지 않고 주식은 변한다.",
                "채권은 이자, 주식은 배당이라는 단어만 다르다.",
            ],
            correct_index=1,
            explanation=(
                "채권자는 원금과 이자를 받을 권리, 주주는 이익과 의사결정에 참여할 권리를 갖습니다."
            ),
        )
    ],
    _cid(3): [
        QuizItem(
            concept_id=_cid(3),
            question="매출과 영업이익의 관계로 가장 적절한 것은?",
            options=[
                "매출은 최종 수익, 영업이익은 받은 돈 전체이다.",
                "매출에서 매출원가와 판관비를 뺀 결과가 영업이익이다.",
                "둘은 같은 의미를 회계 기준에 따라 달리 부른다.",
                "영업이익은 매출보다 항상 크다.",
            ],
            correct_index=1,
            explanation=(
                "매출이 많아도 비용이 더 크면 영업이익은 줄어듭니다. "
                "매출 규모만으로 수익성을 판단할 수 없습니다."
            ),
        )
    ],
    _cid(4): [
        QuizItem(
            concept_id=_cid(4),
            question="인플레이션이 투자자에게 가장 중요한 의미를 갖는 이유는?",
            options=[
                "물가 상승은 곧 주식 시장의 폭락을 뜻한다.",
                ("현금의 구매력이 시간이 지나며 감소하므로, 저축만 하면 실질가치가 줄어든다."),
                "인플레이션이 발생하면 모든 자산의 가치가 똑같이 오른다.",
                "정부가 인위적으로 만들기 때문에 무시해도 좋다.",
            ],
            correct_index=1,
            explanation=(
                "인플레이션은 현금의 구매력을 좀먹습니다. "
                "그래서 단순 저축보다 자산 보유가 장기 부 보호의 핵심이 됩니다."
            ),
        )
    ],
    _cid(5): [
        QuizItem(
            concept_id=_cid(5),
            question="다음 중 PER(주가수익비율)에 대한 설명으로 가장 적절한 것은?",
            options=[
                "기업의 순자산 대비 시가총액을 나타내는 지표이다.",
                (
                    "현재 주가가 주당순이익(EPS)의 몇 배인지를 나타내며, "
                    "투자원금 회수 기간으로도 해석된다."
                ),
                "기업의 총부채를 자본으로 나눈 비율이다.",
                "기업이 1년 동안 지급한 배당금 총액을 의미한다.",
            ],
            correct_index=1,
            explanation=(
                "PER = 주가 ÷ EPS. 현재 이익이 유지된다는 가정에서 "
                "투자금을 몇 년에 회수할지의 직관적 지표입니다."
            ),
        )
    ],
    _cid(6): [
        QuizItem(
            concept_id=_cid(6),
            question="투자에서 '복리 효과'를 극대화하기 위해 가장 중요한 요소는?",
            options=[
                "최대한 잦은 단타 매매로 회전율을 극대화한다.",
                "발생한 수익을 인출하여 즉시 소비한다.",
                "수익을 재투자하여 원금을 키우고 충분한 시간을 유지한다.",
                "부채를 최대로 끌어 레버리지를 일으킨다.",
            ],
            correct_index=2,
            explanation=(
                "복리는 원금뿐 아니라 이자에도 이자가 붙는 구조입니다. "
                "재투자와 시간이 두 핵심 변수입니다."
            ),
        )
    ],
    _cid(7): [
        QuizItem(
            concept_id=_cid(7),
            question="'내재가치'와 '시장가격'의 관계로 가장 적절한 것은?",
            options=[
                "두 값은 항상 일치한다.",
                (
                    "시장은 단기적으로 비합리적일 수 있어 두 값이 괴리되는 "
                    "순간이 가치투자의 기회가 된다."
                ),
                "시장가격은 내재가치의 두 배가 정상이다.",
                "내재가치는 정부가 발표한 공식 가격이다.",
            ],
            correct_index=1,
            explanation=(
                "가치투자의 출발점입니다. "
                "가격과 가치가 다를 수 있다는 인식이 안전마진의 기반이 됩니다."
            ),
        )
    ],
    _cid(8): [
        QuizItem(
            concept_id=_cid(8),
            question="가치투자에서 말하는 '안전마진'의 개념을 올바르게 설명한 것은?",
            options=[
                "주가가 기업의 내재가치보다 충분히 낮을 때 생기는 가격의 완충 지대이다.",
                "정부가 예금자 보호법으로 보장해주는 최대 금액이다.",
                "손실 발생 시 증권사가 보전해주는 보증 비율이다.",
                "주가가 전고점 대비 50% 이상 하락했음을 확인하는 기술적 신호이다.",
            ],
            correct_index=0,
            explanation=(
                "안전마진은 내재가치와 시장가격의 격차로, "
                "분석 오류나 돌발 악재로부터 투자자를 보호합니다."
            ),
        )
    ],
    _cid(9): [
        QuizItem(
            concept_id=_cid(9),
            question="PBR이 1보다 작다는 것의 가장 적절한 해석은?",
            options=[
                "회사가 망했다는 의미이다.",
                ("시장에서 그 회사의 시가총액이 회계상 순자산보다 낮게 평가되고 있다."),
                "PBR은 1보다 작을 수 없다.",
                "배당을 주지 않는다는 의미이다.",
            ],
            correct_index=1,
            explanation=(
                "PBR = 주가 ÷ BPS. 1 미만은 청산가치보다 시가가 낮다는 뜻으로, "
                "가치투자자가 주목하는 신호입니다."
            ),
        )
    ],
    _cid(10): [
        QuizItem(
            concept_id=_cid(10),
            question="ROE 15%가 의미하는 바로 가장 적절한 것은?",
            options=[
                "부채가 자본의 15%이다.",
                ("주주가 투자한 자본 100원에 대해 회사가 1년에 15원의 순이익을 만들어냈다."),
                "매출이익률이 15%이다.",
                "배당수익률이 15%이다.",
            ],
            correct_index=1,
            explanation=(
                "ROE = 순이익 ÷ 자기자본. "
                "자본이 얼마나 효율적으로 이익을 만드는가의 핵심 지표입니다."
            ),
        )
    ],
    _cid(11): [
        QuizItem(
            concept_id=_cid(11),
            question="부채비율 200%인 기업에 대한 가치투자자의 일반적 시각은?",
            options=[
                "부채가 적어 안전하다고 본다.",
                ("부채가 자본의 2배 — 이익 감소 국면에서 위험이 커지므로 신중히 검토한다."),
                "정부 보증을 받는 우량 기업이라고 본다.",
                "부채비율과 사업 안전성은 무관하다고 본다.",
            ],
            correct_index=1,
            explanation=(
                "부채비율 = 부채 ÷ 자본. 가치투자는 불확실성에 대한 완충을 "
                "중시하기에 과도한 레버리지는 안전마진을 갉아먹습니다."
            ),
        )
    ],
    _cid(12): [
        QuizItem(
            concept_id=_cid(12),
            question="'경제적 해자(Economic Moat)'의 가장 적절한 예시는?",
            options=[
                "잠시 시장에서 1등인 점유율",
                (
                    "다른 기업이 흉내내기 어려운 지속가능한 경쟁우위 "
                    "(강한 브랜드, 네트워크 효과, 전환비용 등)"
                ),
                "정부의 일시적 보조금",
                "단기 매출 급증",
            ],
            correct_index=1,
            explanation=(
                "해자는 경쟁자의 침입을 막아주는 구조적 우위입니다. "
                "버핏 가치투자의 핵심 검색어입니다."
            ),
        )
    ],
    _cid(13): [
        QuizItem(
            concept_id=_cid(13),
            question="회사가 순이익을 전부 배당하지 않고 이익잉여금으로 쌓아두는 가장 큰 이유는?",
            options=[
                "세금을 줄이기 위해서이다.",
                "미래 성장에 재투자하거나 사업의 위험 완충을 위해서이다.",
                "주주에게 손해를 끼치기 위해서이다.",
                "회계 규정 위반을 감추기 위해서이다.",
            ],
            correct_index=1,
            explanation=(
                "배당과 재투자의 선택은 자본배분의 출발점입니다. "
                "재투자가 자본비용을 넘는 ROIC를 만든다면 주주에게 더 이익입니다."
            ),
        )
    ],
    _cid(14): [
        QuizItem(
            concept_id=_cid(14),
            question=(
                '"남들이 탐욕에 빠질 때 두려워하고, 두려워할 때 탐욕을 가져라" '
                "— 이 격언의 가치투자적 함의는?"
            ),
            options=[
                "항상 거꾸로 행동해 단기 차익을 노려야 한다.",
                (
                    "시장은 종종 비합리적이며, 군중심리에 휩쓸리지 않는 "
                    "독립적 판단이 장기 수익의 원천이다."
                ),
                "군중을 무조건 따라가야 안전하다.",
                "매일 반대 매매를 해 변동성을 활용하라는 뜻이다.",
            ],
            correct_index=1,
            explanation=(
                "시장 사이클의 광기와 공포는 가격을 가치에서 떨어뜨립니다. "
                "그 괴리가 안전마진을 키워주는 시점입니다."
            ),
        )
    ],
    _cid(15): [
        QuizItem(
            concept_id=_cid(15),
            question="ROIC가 ROE보다 자본효율성 지표로 더 정확하다고 평가되는 이유는?",
            options=[
                (
                    "ROIC는 분모에 자기자본과 차입금을 모두 포함해, "
                    "부채로 부풀려진 ROE의 착시를 보정한다."
                ),
                "ROIC는 연 단위로만 계산할 수 있다.",
                "ROIC는 배당까지 포함한 총수익률이다.",
                "둘은 완전히 같은 의미이다.",
            ],
            correct_index=0,
            explanation=(
                "ROIC = NOPAT ÷ 투하자본. 부채와 자본 모두 자본비용이라는 "
                "관점으로 자본조달 구조의 왜곡을 제거합니다."
            ),
        )
    ],
    _cid(16): [
        QuizItem(
            concept_id=_cid(16),
            question="잉여현금흐름(FCF)에 대한 가치투자자의 시각으로 가장 적절한 것은?",
            options=[
                "회계상 이익보다 현금흐름이 회사 가치를 더 잘 보여준다고 본다.",
                "매출이 클수록 FCF도 항상 같이 커진다고 본다.",
                "FCF는 회계 조작의 결과로 본다.",
                "FCF는 단기 트레이딩 지표로만 본다.",
            ],
            correct_index=0,
            explanation=(
                "영업현금흐름 - 자본적지출 = FCF. "
                "회계이익은 조정 여지가 있지만 현금흐름은 거짓말이 더 어렵습니다."
            ),
        )
    ],
    _cid(17): [
        QuizItem(
            concept_id=_cid(17),
            question="경영진의 자본배분 결정 중 가치투자자가 가장 주의 깊게 보는 것은?",
            options=[
                "무조건 배당을 늘리는 결정",
                (
                    "사업의 ROIC가 자본비용을 넘으면 재투자, "
                    "그렇지 않으면 자사주매입·배당으로 환원하는 합리성"
                ),
                "무조건 인수합병을 늘리는 결정",
                "모든 이익을 사내에 쌓아두는 결정",
            ],
            correct_index=1,
            explanation=(
                "자본배분은 경영진 실력의 가장 정직한 측정자입니다. "
                "버핏이 연차 서한에서 가장 많이 다루는 주제이기도 합니다."
            ),
        )
    ],
    _cid(18): [
        QuizItem(
            concept_id=_cid(18),
            question="워런 버핏이 강조한 투자 4원칙 중 하나가 아닌 것은?",
            options=[
                "내가 이해할 수 있는 사업",
                "장기적으로 유리한 사업 전망",
                "유능하고 정직한 경영진",
                "매일 차트를 분석해 단기 매매 신호를 잡는다",
            ],
            correct_index=3,
            explanation=(
                "버핏의 4원칙은 ① 사업 이해 ② 장기 전망 ③ 경영진 ④ 매력적 가격입니다. "
                "단기 차트는 4원칙과 정반대 관점입니다."
            ),
        )
    ],
    _cid(19): [
        QuizItem(
            concept_id=_cid(19),
            question="'가치 함정(Value Trap)'의 가장 적절한 설명은?",
            options=[
                ("PER이 낮아 싸 보이지만 사업의 구조적 쇠퇴 때문에 영원히 싸기만 한 주식"),
                "모든 저PER 주식의 별명",
                "단기간 급등하는 주식",
                "배당이 끊긴 주식",
            ],
            correct_index=0,
            explanation=(
                "단순 저평가와 가치 함정의 구분이 핵심입니다. "
                "해자가 약해지고 ROIC가 자본비용을 밑도는 사업은 싸도 사면 안 됩니다."
            ),
        )
    ],
    _cid(20): [
        QuizItem(
            concept_id=_cid(20),
            question="DCF(현금흐름할인법)의 가장 본질적인 아이디어는?",
            options=[
                (
                    "미래에 받을 현금흐름을 위험을 반영한 할인율로 "
                    "현재가치로 환산해 합한 것이 기업 가치이다."
                ),
                "1년 매출의 10배가 적정 가격이다.",
                "주가의 평균선이 곧 적정가이다.",
                "배당의 5배가 적정 가격이다.",
            ],
            correct_index=0,
            explanation=(
                "모든 자산 가치는 미래 현금흐름의 현재가치 합입니다. "
                "DCF는 그 형식화된 표현일 뿐, 입력 가정이 더 중요합니다."
            ),
        )
    ],
    _cid(21): [
        QuizItem(
            concept_id=_cid(21),
            question="무위험금리가 상승하면 일반적으로 주식의 적정가치는 어떻게 변하는가?",
            options=[
                "더 높게 평가되는 경향이 있다.",
                ("낮아지는 경향이 있다 — 할인율 상승으로 미래 현금흐름의 현재가치가 감소한다."),
                "변하지 않는다.",
                "정부가 직접 결정한다.",
            ],
            correct_index=1,
            explanation=(
                "금리는 모든 자산의 할인율 기준입니다. "
                "같은 미래 현금흐름이라도 금리 상승 시 현재가치는 낮아집니다."
            ),
        )
    ],
    _cid(22): [
        QuizItem(
            concept_id=_cid(22),
            question="가치투자자가 매크로 환경(금리·환율·사이클)을 바라보는 일반적 자세는?",
            options=[
                "매크로 예측이 투자 성과의 80%를 결정한다고 본다.",
                (
                    "매크로 예측은 어렵지만, 사업가치에 직접 영향을 미치는 "
                    "구조적 변화는 반드시 검토한다."
                ),
                "매크로는 완전히 무시한다.",
                "매크로 변동에 맞춰 매일 포지션을 바꾼다.",
            ],
            correct_index=1,
            explanation=(
                "'예측'이 아니라 '이해'입니다. 가치투자도 진공이 아닌 환경 속에서 작동합니다."
            ),
        )
    ],
    _cid(23): [
        QuizItem(
            concept_id=_cid(23),
            question="현대 시장에서 가치투자에 대해 제기되는 가장 논쟁적인 비판은?",
            options=[
                (
                    "무형자산(브랜드·소프트웨어·네트워크)이 핵심이 된 현대 경제에서 "
                    "BPS 중심의 평가가 가치를 과소측정한다."
                ),
                "가치투자는 1주 안에 큰 수익을 낸다.",
                "모든 가치투자자는 같은 종목을 산다.",
                "가치투자는 한국에서만 통한다.",
            ],
            correct_index=0,
            explanation=(
                "그레이엄식 자산기반 가치평가의 한계입니다. "
                "현대 가치투자는 무형자산과 미래 현금흐름까지 통합해 사고합니다."
            ),
        )
    ],
}


# --- 공개 API ---


def get_quiz(concept_id: int) -> QuizView:
    """개념의 (첫) 퀴즈를 concept_name과 join하여 반환. 기존 라우터 호환."""
    quizzes = _QUIZZES.get(ConceptId(concept_id))
    if not quizzes:
        raise NotFoundError("해당 개념의 퀴즈를 찾을 수 없습니다")
    concept = get_concept(concept_id)
    q = quizzes[0]
    return QuizView(
        concept_id=q.concept_id,
        concept_name=concept.name,
        question=q.question,
        options=q.options,
        correct_index=q.correct_index,
        explanation=q.explanation,
    )


def grade_quiz(
    concept_id: int,
    answer_index: int,
    quiz_index: int = 0,
) -> tuple[bool, str]:
    """퀴즈 정답 채점 + 해설 반환.

    quiz_index를 지정하면 그 인덱스의 퀴즈로 채점 (개념당 여러 문제 시).
    미지정 시 첫 번째 문제 — 기존 라우터 호환.
    """
    pool = _QUIZZES.get(ConceptId(concept_id))
    if not pool:
        raise NotFoundError("해당 개념의 퀴즈를 찾을 수 없습니다")
    if not (0 <= quiz_index < len(pool)):
        raise NotFoundError(f"개념 {concept_id}에 quiz_index={quiz_index} 퀴즈가 없습니다")
    q = pool[quiz_index]
    is_correct = q.correct_index == answer_index
    return (is_correct, q.explanation)


# --- 로테이션 정책 (follow-up 후보 결정) ---


def _pick_from_pool(
    pool: list[QuizItem],
    mastered_indices: set[int],
) -> tuple[QuizItem, int] | None:
    """pool에서 mastered 안 한 가장 작은 인덱스를 (QuizItem, index)로 반환.

    pool이 비었거나 모든 인덱스가 mastered면 None. 순수 함수 — DB 의존 없음.
    """
    if not pool:
        return None
    for idx, item in enumerate(pool):
        if idx not in mastered_indices:
            return (item, idx)
    return None


async def record_attempt(
    user_id: UserId,
    concept_id: int,
    quiz_index: int,
    correct: bool,
    db: AsyncSession,
) -> None:
    """사용자의 퀴즈 시도를 DB에 기록.

    정답·오답 모두 기록 — 오답은 재도전 후보로 남기기 위해, 정답은 마스터 판정용.
    commit은 호출자가 책임진다 (다른 INSERT와 묶을 수 있도록).
    """
    db.add(
        QuizAttempt(
            user_id=user_id,
            concept_id=concept_id,
            quiz_index=quiz_index,
            correct=correct,
        )
    )
    await db.flush()


async def pick_for_user(
    user_id: UserId,
    concept_id: int,
    db: AsyncSession,
) -> tuple[QuizItem, int] | None:
    """사용자의 follow-up 후보 퀴즈 결정.

    정책:
    - `correct=True`인 quiz_index만 마스터로 간주 (오답은 재도전 허용)
    - pool이 비어있거나 모두 마스터한 상태면 None — follow-up 안 보냄
    - 그 외에는 안 푼 가장 작은 인덱스 1개 반환
    """
    pool = _QUIZZES.get(ConceptId(concept_id))
    if not pool:
        return None

    stmt = select(QuizAttempt.quiz_index).where(
        QuizAttempt.user_id == user_id,
        QuizAttempt.concept_id == concept_id,
        QuizAttempt.correct.is_(True),
    )
    result = await db.execute(stmt)
    mastered = set(result.scalars().all())

    return _pick_from_pool(pool, mastered)


__all__ = [
    "QuizItem",
    "QuizView",
    "get_quiz",
    "grade_quiz",
    "pick_for_user",
    "record_attempt",
]
