"""대화 맥락에서 학습 중인 개념을 감지.

v1: 키워드 부분 문자열 매칭. 각 Concept이 가진 `keywords` 리스트와
사용자 메시지를 대소문자 무시로 비교한다.

owner: learning
관련 FR: FR-02, UC-04
계획서 §3 7단계, §5 함정 2 (LLM 분류는 v2)

채점 규칙:
1. 후보(`candidates`)의 각 concept에 대해 메시지에 등장한 키워드 수를 셈
2. 가장 많이 매칭된 concept을 선택
3. 동점이면 `id` 오름차순 — 기초 개념일수록 낮은 id이므로 자연스러운 fallback
4. 매칭이 0이거나 메시지가 비어있으면 None

향후 v2 확장:
- LLM-as-classifier로 의도 분류 (호출당 토큰 +1)
- 형태소 분석기로 부분 매칭 오류 제거 ("주식회사" 안의 "주식" 같은 케이스)
- 대화 이력까지 고려한 multi-turn 추론
"""

from .curriculum import Concept


def _count_keyword_matches(message: str, keywords: list[str]) -> int:
    """대소문자 무시 부분 문자열 매칭 수."""
    if not message:
        return 0
    msg_lower = message.lower()
    return sum(1 for kw in keywords if kw.lower() in msg_lower)


def detect_concept(message: str, candidates: list[Concept]) -> Concept | None:
    """후보 중 메시지의 키워드와 가장 많이 매칭되는 개념. 동점은 id 오름차순.

    candidates는 호출자가 결정 — 보통 `list_concepts_for_strategy(strategy)`로
    전략 내 모든 개념을 넘긴다. (사용자가 locked 개념을 물어봐도 감지는 되며,
    locked 처리는 서비스 레이어의 책임.)
    """
    if not message.strip() or not candidates:
        return None

    scored = [(_count_keyword_matches(message, c.keywords), c.id, c) for c in candidates]
    matched = [s for s in scored if s[0] > 0]
    if not matched:
        return None

    matched.sort(key=lambda x: (-x[0], x[1]))
    return matched[0][2]


__all__ = ["detect_concept"]
