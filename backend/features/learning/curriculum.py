"""투자 개념 커리큘럼 — 멘토(투자 전략)별 개념 그래프.

owner: learning
관련 FR: FR-02, UC-04

각 Concept은 MentorStrategy에 귀속된다. 같은 사용자가 멘토를 바꿔
대화하면 다른 커리큘럼이 적용된다. (단, MVP 시드는 VALUE만 채워져 있고
나머지 전략은 비어있다 — 빈 전략의 채팅은 커리큘럼 컨텍스트만 빠진 채로 정상 동작.)

이 모듈은 개념 데이터·시드·조회(`get_concept`/`list_concepts_for_strategy`)
+ **위치 산정**(`get_position`)을 담당한다. 위치는 (티어 + 마스터한 개념)으로 결정되며,
티어·마스터 정보는 `growth_dep.reader()`로 위임 — 성장동 미등록 시 더미가 안전한
기본값(T1·빈셋)을 돌려준다.

**퀴즈 카탈로그는 `quizzes.py`로 분리됨** — 라우터에서는 `quizzes.get_quiz/grade_quiz`를 호출.

ID 네임스페이스 (전략별 100단위 구획):
    VALUE     1–99
    GROWTH    100–199
    DIVIDEND  200–299
    MOMENTUM  300–399
"""

from pydantic import BaseModel, Field

from core.contracts import ConceptId, MentorStrategy, Tier, UserId
from core.exceptions import NotFoundError

from . import growth_dep

# --- 모델 ---


class Concept(BaseModel):
    """학습 단위. 멘토 전략별로 분리되며 선수 관계로 그래프를 이룬다."""

    id: ConceptId
    mentor_strategy: MentorStrategy
    name: str
    tier_required: Tier
    prerequisites: list[ConceptId] = Field(default_factory=list)
    summary: str
    learning_objectives: list[str]
    keywords: list[str]


class CurriculumPosition(BaseModel):
    """사용자의 현재 커리큘럼 위치 — (티어 + 마스터한 개념)으로 산정.

    - available: 사용자의 티어 이상이고 모든 선수 개념이 마스터된 개념들
    - locked: 그 외 (티어 미달 또는 선수 미충족)
    - next_recommended: available 중 아직 마스터하지 않은 가장 앞 개념
    - current_concept: 현재 학습 중인 개념. MVP에서는 next_recommended와 동일.
      7단계 concept_detector가 들어오면 대화 맥락에서 감지된 개념으로 갱신.
    """

    tier: Tier
    mastered: set[ConceptId]
    available: list[Concept]
    locked: list[Concept]
    next_recommended: Concept | None
    current_concept: Concept | None


# --- 시드 데이터: VALUE 23개념 (T1×8, T2×6, T3×5, T4×3, T5×1) ---


def _cid(n: int) -> ConceptId:
    return ConceptId(n)


_CONCEPTS: dict[ConceptId, Concept] = {
    # ---------- T1: 기초 (8) ----------
    _cid(1): Concept(
        id=_cid(1),
        mentor_strategy=MentorStrategy.VALUE,
        name="주식이란 무엇인가",
        tier_required=Tier.T1,
        prerequisites=[],
        summary=(
            "주식은 회사의 지분 일부를 소유하는 권리로, "
            "회사가 만들어내는 미래 이익의 일부를 청구할 자격을 의미한다."
        ),
        learning_objectives=[
            "주식의 본질이 '지분 소유'임을 이해한다",
            "주가는 회사 가치의 일부를 표현하는 가격임을 안다",
        ],
        keywords=["주식", "지분", "주주", "소유권"],
    ),
    _cid(2): Concept(
        id=_cid(2),
        mentor_strategy=MentorStrategy.VALUE,
        name="채권과 주식의 차이",
        tier_required=Tier.T1,
        prerequisites=[_cid(1)],
        summary=("채권은 돈을 빌려준 채권자의 청구권, 주식은 회사 지분을 가진 주주의 청구권이다."),
        learning_objectives=[
            "채권자와 주주의 권리 차이를 구분한다",
            "자산군에 따른 위험-수익 구조의 차이를 이해한다",
        ],
        keywords=["채권", "채무", "이자", "지분"],
    ),
    _cid(3): Concept(
        id=_cid(3),
        mentor_strategy=MentorStrategy.VALUE,
        name="매출과 이익의 차이",
        tier_required=Tier.T1,
        prerequisites=[],
        summary=(
            "매출은 판매로 들어온 돈, "
            "영업이익은 그 매출에서 매출원가·판관비를 뺀 영업활동의 결과이다."
        ),
        learning_objectives=[
            "매출 → 매출총이익 → 영업이익 → 순이익의 흐름을 안다",
            "매출이 크다고 이익도 크다는 보장이 없음을 이해한다",
        ],
        keywords=["매출", "영업이익", "순이익", "원가"],
    ),
    _cid(4): Concept(
        id=_cid(4),
        mentor_strategy=MentorStrategy.VALUE,
        name="인플레이션과 화폐가치",
        tier_required=Tier.T1,
        prerequisites=[],
        summary=(
            "인플레이션은 현금의 구매력을 시간이 지날수록 줄인다. "
            "저축만으로는 실질 자산이 보호되지 않는다."
        ),
        learning_objectives=[
            "물가 상승과 구매력 감소의 관계를 안다",
            "투자가 단순 저축보다 장기 부 보호에 필요한 이유를 이해한다",
        ],
        keywords=["인플레이션", "물가", "화폐가치", "구매력"],
    ),
    _cid(5): Concept(
        id=_cid(5),
        mentor_strategy=MentorStrategy.VALUE,
        name="PER (주가수익비율)",
        tier_required=Tier.T1,
        prerequisites=[_cid(1), _cid(3)],
        summary=(
            "PER = 주가 ÷ EPS. 현재 이익이 유지된다는 가정 하에 "
            "투자금 회수에 걸리는 햇수의 직관적 지표."
        ),
        learning_objectives=[
            "PER 계산법과 직관적 의미를 안다",
            "동종 업종 비교 외에 단일 PER의 해석 한계를 이해한다",
        ],
        keywords=["PER", "주가수익비율", "EPS"],
    ),
    _cid(6): Concept(
        id=_cid(6),
        mentor_strategy=MentorStrategy.VALUE,
        name="복리의 마법",
        tier_required=Tier.T1,
        prerequisites=[],
        summary="원금에 발생한 수익이 다시 수익을 낳는 구조. 재투자와 시간이 두 핵심 변수다.",
        learning_objectives=[
            "단리와 복리의 차이를 안다",
            "장기 투자가 복리 효과를 결정하는 이유를 이해한다",
        ],
        keywords=["복리", "재투자", "장기투자"],
    ),
    _cid(7): Concept(
        id=_cid(7),
        mentor_strategy=MentorStrategy.VALUE,
        name="내재가치 vs 시장가격",
        tier_required=Tier.T1,
        prerequisites=[_cid(1)],
        summary=(
            "시장은 단기적으로 비합리적일 수 있어 가격과 가치가 괴리되며, "
            "이 괴리가 가치투자의 출발점이 된다."
        ),
        learning_objectives=[
            "가격과 가치가 다른 개념임을 안다",
            "Mr. Market 비유로 시장의 변덕을 이해한다",
        ],
        keywords=["내재가치", "시장가격", "본질가치"],
    ),
    _cid(8): Concept(
        id=_cid(8),
        mentor_strategy=MentorStrategy.VALUE,
        name="안전마진",
        tier_required=Tier.T1,
        prerequisites=[_cid(5), _cid(7)],
        summary=(
            "주가가 내재가치보다 충분히 낮을 때 생기는 가격 완충 지대. "
            "분석 오류와 돌발 악재에 대한 보호막."
        ),
        learning_objectives=[
            "안전마진이 '실수에 대한 비용'임을 이해한다",
            "확실성 vs 가격의 관계를 설명할 수 있다",
        ],
        keywords=["안전마진", "margin of safety", "그레이엄"],
    ),
    # ---------- T2: 중급 (6) ----------
    _cid(9): Concept(
        id=_cid(9),
        mentor_strategy=MentorStrategy.VALUE,
        name="EPS·PBR·BPS",
        tier_required=Tier.T2,
        prerequisites=[_cid(5)],
        summary=(
            "EPS는 주당순이익, BPS는 주당순자산, PBR은 주가/BPS. "
            "PBR 1 미만은 시가가 회계상 순자산 아래임을 의미."
        ),
        learning_objectives=[
            "BPS·EPS·PBR을 구분해 해석한다",
            "PBR 1 미만의 함의를 이해한다",
        ],
        keywords=["EPS", "PBR", "BPS", "주당순이익", "주당순자산"],
    ),
    _cid(10): Concept(
        id=_cid(10),
        mentor_strategy=MentorStrategy.VALUE,
        name="ROE (자기자본이익률)",
        tier_required=Tier.T2,
        prerequisites=[_cid(3), _cid(9)],
        summary=(
            "ROE = 순이익 ÷ 자기자본. 주주가 맡긴 자본이 얼마나 효율적으로 이익을 만드는가의 지표."
        ),
        learning_objectives=[
            "ROE의 계산과 의미를 안다",
            "ROE가 부채에 의해 부풀려질 수 있음을 인지한다",
        ],
        keywords=["ROE", "자기자본이익률"],
    ),
    _cid(11): Concept(
        id=_cid(11),
        mentor_strategy=MentorStrategy.VALUE,
        name="부채비율과 재무건전성",
        tier_required=Tier.T2,
        prerequisites=[_cid(10)],
        summary=(
            "부채비율 = 부채 ÷ 자본. "
            "과도한 레버리지는 호황엔 수익을 키우지만 불황엔 안전마진을 갉아먹는다."
        ),
        learning_objectives=[
            "부채비율을 산업 특성과 함께 해석한다",
            "재무건전성과 가치투자의 안전마진을 연결한다",
        ],
        keywords=["부채비율", "부채", "재무건전성", "레버리지"],
    ),
    _cid(12): Concept(
        id=_cid(12),
        mentor_strategy=MentorStrategy.VALUE,
        name="경제적 해자 (Economic Moat)",
        tier_required=Tier.T2,
        prerequisites=[_cid(7)],
        summary=(
            "경쟁자가 흉내내기 어려운 지속 가능한 경쟁우위. "
            "강한 브랜드, 네트워크 효과, 전환비용 등이 대표적이다."
        ),
        learning_objectives=[
            "해자의 종류 4~5가지를 안다",
            "단기 점유율과 구조적 해자를 구분한다",
        ],
        keywords=["해자", "moat", "경쟁우위", "버핏"],
    ),
    _cid(13): Concept(
        id=_cid(13),
        mentor_strategy=MentorStrategy.VALUE,
        name="배당과 이익잉여금",
        tier_required=Tier.T2,
        prerequisites=[_cid(3)],
        summary=(
            "회사는 순이익을 배당으로 환원하거나 이익잉여금으로 사내에 쌓는다. "
            "둘의 선택이 자본배분의 출발."
        ),
        learning_objectives=[
            "배당 정책과 사내유보의 트레이드오프를 안다",
            "재투자 ROIC가 자본비용을 넘는지가 핵심 판단 기준임을 이해한다",
        ],
        keywords=["배당", "이익잉여금", "사내유보", "자본"],
    ),
    _cid(14): Concept(
        id=_cid(14),
        mentor_strategy=MentorStrategy.VALUE,
        name="시장 사이클의 광기와 공포",
        tier_required=Tier.T2,
        prerequisites=[_cid(7)],
        summary=(
            "시장은 종종 비합리적이며 군중심리에 휩쓸린다. "
            "가치투자는 독립적 판단을 통해 가격-가치 괴리를 활용한다."
        ),
        learning_objectives=[
            "탐욕·공포가 가격을 가치에서 떨어뜨리는 메커니즘을 안다",
            "역발상 투자(contrarian)의 의미와 위험을 구분한다",
        ],
        keywords=["탐욕", "공포", "사이클", "변동성", "역발상"],
    ),
    # ---------- T3: 심화 (5) ----------
    _cid(15): Concept(
        id=_cid(15),
        mentor_strategy=MentorStrategy.VALUE,
        name="ROIC (투하자본이익률)",
        tier_required=Tier.T3,
        prerequisites=[_cid(10)],
        summary=(
            "ROIC = NOPAT ÷ (자기자본+차입금). "
            "자본조달 구조에 영향을 적게 받는, 사업 자체의 자본효율 지표."
        ),
        learning_objectives=[
            "ROE의 한계와 ROIC가 보정하는 지점을 안다",
            "ROIC vs 자본비용(WACC) 비교의 의미를 이해한다",
        ],
        keywords=["ROIC", "투하자본수익률", "NOPAT", "자본효율"],
    ),
    _cid(16): Concept(
        id=_cid(16),
        mentor_strategy=MentorStrategy.VALUE,
        name="FCF (잉여현금흐름)",
        tier_required=Tier.T3,
        prerequisites=[_cid(3), _cid(13)],
        summary=(
            "FCF = 영업현금흐름 - 자본적지출. 회계이익은 조정 여지가 있지만 현금은 거짓말이 어렵다."
        ),
        learning_objectives=[
            "FCF의 계산과 회계이익과의 차이를 안다",
            "FCF의 안정성·예측가능성이 가치평가의 본질임을 이해한다",
        ],
        keywords=["FCF", "잉여현금흐름", "영업현금흐름", "자본적지출"],
    ),
    _cid(17): Concept(
        id=_cid(17),
        mentor_strategy=MentorStrategy.VALUE,
        name="자본배분 (Capital Allocation)",
        tier_required=Tier.T3,
        prerequisites=[_cid(15), _cid(16)],
        summary=(
            "경영진의 자본배분 결정(재투자·인수합병·배당·자사주매입)은 "
            "경영진 실력의 가장 정직한 측정자다."
        ),
        learning_objectives=[
            "ROIC > WACC일 때 재투자, 아닐 때 환원이 합리적임을 안다",
            "자사주매입과 배당의 차이와 함의를 이해한다",
        ],
        keywords=["자본배분", "자사주매입", "재투자", "인수합병"],
    ),
    _cid(18): Concept(
        id=_cid(18),
        mentor_strategy=MentorStrategy.VALUE,
        name="워런 버핏의 4원칙",
        tier_required=Tier.T3,
        prerequisites=[_cid(12), _cid(15)],
        summary=(
            "① 내가 이해할 수 있는 사업 ② 장기적으로 유리한 사업 전망 "
            "③ 유능하고 정직한 경영진 ④ 매력적인 가격."
        ),
        learning_objectives=[
            "4원칙 각각을 설명할 수 있다",
            "4원칙이 단기 차트 분석과 정반대 관점임을 안다",
        ],
        keywords=["버핏", "4원칙", "사업이해", "장기전망", "경영진"],
    ),
    _cid(19): Concept(
        id=_cid(19),
        mentor_strategy=MentorStrategy.VALUE,
        name="가치 함정 (Value Trap)",
        tier_required=Tier.T3,
        prerequisites=[_cid(5), _cid(12)],
        summary=("PER이 낮아 싸 보이지만 사업의 구조적 쇠퇴 때문에 영원히 싸기만 한 주식."),
        learning_objectives=[
            "단순 저평가와 가치 함정을 구분한다",
            "해자 약화와 ROIC 하락이 가치 함정의 전형적 신호임을 안다",
        ],
        keywords=["가치함정", "value trap", "저PER함정", "구조적쇠퇴"],
    ),
    # ---------- T4: 고급 (3) ----------
    _cid(20): Concept(
        id=_cid(20),
        mentor_strategy=MentorStrategy.VALUE,
        name="DCF 개념 이해",
        tier_required=Tier.T4,
        prerequisites=[_cid(16)],
        summary=(
            "기업가치 = 미래에 받을 현금흐름을 위험을 반영한 할인율로 "
            "현재가치로 환산한 합. 수식보다 가정의 합리성이 더 중요."
        ),
        learning_objectives=[
            "DCF가 모든 자산 평가의 본질적 형식화임을 안다",
            "할인율과 성장률 가정의 민감도를 인지한다",
        ],
        keywords=["DCF", "현금흐름할인", "할인율", "현재가치"],
    ),
    _cid(21): Concept(
        id=_cid(21),
        mentor_strategy=MentorStrategy.VALUE,
        name="금리와 가치평가",
        tier_required=Tier.T4,
        prerequisites=[_cid(20)],
        summary=(
            "무위험금리는 모든 자산의 할인율 기준. "
            "같은 미래 현금흐름이라도 금리가 오르면 현재가치는 낮아진다."
        ),
        learning_objectives=[
            "금리 변동이 자산 가치 평가에 미치는 메커니즘을 안다",
            "성장주가 금리에 더 민감한 이유를 설명할 수 있다",
        ],
        keywords=["금리", "할인율", "무위험금리", "가치평가"],
    ),
    _cid(22): Concept(
        id=_cid(22),
        mentor_strategy=MentorStrategy.VALUE,
        name="매크로 환경 변화 대응",
        tier_required=Tier.T4,
        prerequisites=[_cid(21), _cid(14)],
        summary=(
            "가치투자도 진공이 아닌 환경에서 작동한다. "
            "예측이 아니라 '구조적 변화의 이해'에 무게를 둔다."
        ),
        learning_objectives=[
            "예측과 이해를 구분한다",
            "사업가치에 직접 영향을 미치는 매크로 변수를 식별한다",
        ],
        keywords=["매크로", "거시경제", "환율", "사이클"],
    ),
    # ---------- T5: 응용·토론 (1) ----------
    _cid(23): Concept(
        id=_cid(23),
        mentor_strategy=MentorStrategy.VALUE,
        name="가치투자의 한계와 현대적 비판",
        tier_required=Tier.T5,
        prerequisites=[_cid(18), _cid(19), _cid(22)],
        summary=(
            "무형자산이 주도하는 현대 경제에서 BPS 중심 평가의 한계, "
            "가치·성장 이분법의 해체 등 논쟁적 주제를 다룬다."
        ),
        learning_objectives=[
            "고전 가치투자의 전제와 현대 시장의 변화 지점을 비교한다",
            "가치투자를 다른 철학과 통합적으로 사고할 수 있다",
        ],
        keywords=["가치투자한계", "무형자산", "그로스", "현대가치투자"],
    ),
}


# --- 공개 API ---


def get_concept(concept_id: int) -> Concept:
    """개념 단건 조회. 없으면 NotFoundError."""
    c = _CONCEPTS.get(ConceptId(concept_id))
    if c is None:
        raise NotFoundError(f"개념 {concept_id}을(를) 찾을 수 없습니다")
    return c


def list_concepts_for_strategy(strategy: MentorStrategy) -> list[Concept]:
    """전략(멘토)에 속한 모든 개념을 tier_required 오름차순으로 반환."""
    return sorted(
        (c for c in _CONCEPTS.values() if c.mentor_strategy == strategy),
        key=lambda c: (c.tier_required.value, c.id),
    )


def _is_available(concept: Concept, user_tier: Tier, mastered: set[ConceptId]) -> bool:
    """티어 충족 + 모든 선수 마스터 시 available."""
    tier_ok = concept.tier_required.value <= user_tier.value
    prereqs_ok = all(p in mastered for p in concept.prerequisites)
    return tier_ok and prereqs_ok


async def get_position(user_id: UserId, strategy: MentorStrategy) -> CurriculumPosition:
    """사용자의 현재 커리큘럼 위치 산정.

    성장도(tier·마스터한 개념)는 growth_dep.reader()로 조회 — 성장동
    미등록 시 더미가 T1·빈셋을 반환하므로 안전하다.

    시드가 빈 전략(GROWTH/DIVIDEND/MOMENTUM 등)이면 available/locked가 빈
    리스트, next/current가 None인 빈 Position을 반환한다.
    """
    reader = growth_dep.reader()
    tier = await reader.get_user_tier(user_id)
    mastered = await reader.get_mastered_concepts(user_id, strategy)

    all_concepts = list_concepts_for_strategy(strategy)
    available: list[Concept] = []
    locked: list[Concept] = []
    for c in all_concepts:
        (available if _is_available(c, tier, mastered) else locked).append(c)

    # 다음 추천 = available 중 아직 마스터 안 한 가장 앞 개념
    # (all_concepts가 이미 tier→id 오름차순이므로 available도 동일 순서)
    next_recommended: Concept | None = next((c for c in available if c.id not in mastered), None)
    # MVP: current_concept = next_recommended. detector(7단계)가 분리 책임.
    current_concept = next_recommended

    return CurriculumPosition(
        tier=tier,
        mastered=mastered,
        available=available,
        locked=locked,
        next_recommended=next_recommended,
        current_concept=current_concept,
    )


__all__ = [
    "Concept",
    "CurriculumPosition",
    "get_concept",
    "get_position",
    "list_concepts_for_strategy",
]
