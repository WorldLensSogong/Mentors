# 학습 동 — 커리큘럼 고도화 계획

> 작성일: 2026-05-20
> owner: learning
> 관련: [learning_dataflow.md](learning_dataflow.md) (현재 상태) · [1주차_인수인계서.md](1주차_인수인계서.md) §2동
> 상태: 1~12단계 전체 완료

---

## 0. 왜 이 문서가 있나

기획서에는 **"사용자 성장도 → 커리큘럼 위치 → 멘토 대화·퀴즈가 달라진다"** 는 핵심 메커니즘이 적혀 있으나, 현재 코드에는 **거의 0% 구현**되어 있다. 이 문서는 그 간극을 메우는 작업 계획이다.

- 현재 `features/learning/curriculum.py`는 **이름만 커리큘럼**인 메모리 dict 3개 (PER/복리/안전마진)
- "커리큘럼 위치"라는 개념 자체가 코드에 없음
- 시스템 프롬프트에 페르소나·티어 어휘만 반영되고, **"현재 학습 중인 개념"이 들어가지 않음**
- 퀴즈는 클라이언트가 `concept_id`를 직접 지정 — 시스템 결정 없음
- 티어는 `user_context.get_tier()`가 **항상 T1 반환** (성장동 미구현)

---

## 1. MVP 범위 결정

| 항목 | 결정 |
|---|---|
| 멘토 범위 | **가치투자(VALUE) 멘토만 MVP** — 나머지(GROWTH/DIVIDEND/MOMENTUM)는 후속 PR |
| 멘토당 커리큘럼 | 멘토마다 다른 커리큘럼 — 같은 사용자라도 가치 세션과 모멘텀 세션의 진도가 분리 |
| 성장도 연동 | **본 작업에선 학습동 코드만 수정.** 성장동은 다른 팀원 담당이므로 더미 fallback으로 미리 세팅 — 성장동이 들어오면 `register_growth_reader()` 한 줄로 자동 연결 |
| 결과 | 머지 후에도 사용자 모두 **항상 T1·빈 마스터리**로 보이지만, 흐름·UI·로직은 검증 가능 |

### 1.1 가치투자 시드 — 23개념

T1을 의도적으로 넓혀 "투자의 ABC"를 충분히 다지게 했다. 5개 정도면 T1을 너무 쉽게 통과해 게이지가 빨리 차는 문제 → 다음 두 축으로 동시에 보완:

- **개념 수 확장** (T1 5→8) — 학습 폭 확보
- **개념당 퀴즈 다중화 가능 구조** (`dict[ConceptId, list[QuizItem]]`) — MVP는 1개씩이지만 데이터만 늘리면 곧바로 풀 다중화

| 티어 | 개수 | 개념 |
|---|---|---|
| **T1** (기초) | 8 | 주식이란·채권과 주식 차이·매출과 이익의 차이·인플레이션·PER·복리·내재가치 vs 시장가격·안전마진 |
| **T2** (중급) | 6 | EPS·PBR·BPS / ROE / 부채비율 / 경제적 해자 / 배당과 이익잉여금 / 시장 사이클의 광기와 공포 |
| **T3** (심화) | 5 | ROIC / FCF / 자본배분 / 워런 버핏의 4원칙 / 가치 함정 |
| **T4** (고급) | 3 | DCF 개념 / 금리와 가치평가 / 매크로 환경 대응 |
| **T5** (응용) | 1 | 가치투자의 한계와 현대적 비판 (토론형) |

---

## 2. 의존성 끊기 패턴 — 핵심 설계

학습동을 성장동 없이 완성하려면 **두 의존성**을 인터페이스로 끊어야 한다:

1. **사용자 티어** — `user_context.get_tier()` (이미 인터페이스, 항상 T1 반환)
2. **마스터한 개념** — 현재 존재하지 않음 → `GrowthReader` Protocol 확장으로 표준화

### 2.1 Protocol 기반 fallback (이미 깔린 멍석)

[core/read_services/](../core/read_services/) 에 `GrowthReader` Protocol과 `register_growth_reader()` 패턴이 이미 존재. 성장동이 나중에 구현체를 등록하면 학습동 코드는 한 줄도 안 바뀐다.

```
[학습동]        get_position()
                    ↓
            growth_dep.reader()
                    ↓
        try: get_growth_reader()   ← 성장동 등록됐으면 진짜
        except RuntimeError:
            return _NullReader     ← 안 됐으면 더미 (T1 + 빈셋)
```

### 2.2 ID 네임스페이스 — 전략별 100단위

```
VALUE     1–99      ← 현재 23개 시드
GROWTH    100–199   ← 후속 PR
DIVIDEND  200–299
MOMENTUM  300–399
```

ID 충돌 없이 같은 `_CONCEPTS` dict에 다 들어갈 수 있고, 미래 전략 추가는 데이터만 늘리면 끝.

---

## 3. 작업 단계 (의존성순)

각 단계는 **PR 1개 단위**로 쪼개기 좋은 크기. 각 단계가 독립적으로 동작하고 검증 가능.

| # | 단계 | 산출물 | 검증 |
|---|---|---|---|
| **1** | **Concept 모델 + 시드 데이터** ✅ 완료 | [curriculum.py](../features/learning/curriculum.py) 재작성: VALUE 23개념 + 23퀴즈, `Concept`/`QuizItem`/`QuizView` 모델, 공개 API 4개 (`get_concept`, `get_quiz`, `grade_quiz`, `list_concepts_for_strategy`) | pytest 29건 통과. 선수관계·티어 무결성 자동 검증 |
| **2** | **GrowthReader Protocol 메서드 추가 + 학습동 내 fallback** ✅ 완료 | (a) [core/read_services/protocols.py](../core/read_services/protocols.py)의 `GrowthReader`에 `get_user_tier`, `get_mastered_concepts(user_id, strategy)` 추가 (b) [features/learning/growth_dep.py](../features/learning/growth_dep.py) 신규 — `reader()` 함수가 등록 안 됐을 때 `_NullGrowthReader`(모두 T1·빈셋·빈 분포) 반환 | pytest 3건 추가: 미등록 시 더미 동작·인스턴스 안정성·등록 시 위임 |
| **3** | **CurriculumService — get_position 구현** ✅ 완료 | [curriculum.py](../features/learning/curriculum.py)에 `CurriculumPosition` DTO + `get_position(user_id, strategy)` async 함수 추가. tier·mastered를 `growth_dep.reader()`로 조회 → 시드 데이터와 결합해 available/locked 분기, next_recommended 계산. MVP: `current_concept` = `next_recommended`(7단계 detector가 분기 책임) | pytest 8건 추가: T1 더미·빈 전략·prereq unlock·티어 락·모두 마스터 케이스 |
| **4** | **GET /api/learning/curriculum/me 엔드포인트** ✅ 완료 | [router.py](../features/learning/router.py)에 추가 — `mentor_id` 쿼리 파라미터 받아 `get_mentor_strategy()`로 변환 후 `get_position()` 호출. `CurriculumPosition`을 그대로 응답 모델로 사용 | pytest 1건 추가(직렬화 안전성). 라우트 등록 확인 |
| **5** | **quizzes.py 분리** ✅ 완료 | [features/learning/quizzes.py](../features/learning/quizzes.py) 신규 — `QuizItem`/`QuizView` 모델 + `_QUIZZES` 시드(23개) + `get_quiz`/`grade_quiz` 함수. [curriculum.py](../features/learning/curriculum.py) 정리 — 퀴즈 코드 제거(960→505줄). router는 `quizzes.get_quiz`/`grade_quiz` 호출로 변경 | pytest 55 passed (회귀 없음). 라우트 8개 정상 |
| **6** | **GET /api/learning/quizzes/next 엔드포인트** ✅ 완료 | [router.py](../features/learning/router.py)에 추가 — `mentor_id` 받아 `get_position()` 호출 후 `current_concept or next_recommended`로 타겟 결정. 없으면 404. 결정된 개념의 퀴즈를 `QuizRes`로 반환 | pytest 4건 추가: 더미 환경·all-mastered 404·빈 전략 404·부분 마스터 후 진행 |
| **7** | **concept_detector.py (키워드 매칭 v1)** ✅ 완료 | [features/learning/concept_detector.py](../features/learning/concept_detector.py) 신규 — `detect_concept(message, candidates) -> Concept \| None` 함수. 키워드 매칭 수 desc → id asc tiebreak. 대소문자 무시 | pytest 12건 추가: 단일 매칭 6건·빈 입력·매칭 없음·빈 후보·동점·다중 매칭·case insensitive |
| **8** | **chat_stream에 커리큘럼 컨텍스트 주입** ✅ 완료 | [service.py](../features/learning/service.py)에 `_select_active_concept`/`_build_curriculum_context` 헬퍼 추가 + `stream_assistant_response`에서 호출. 시스템 프롬프트에 `[현재 학습 단원]`·`[요약]`·`[학습 목표]` 블록 주입, locked 개념이면 "잠긴 단원" 안내 추가 | pytest 9건 추가: build_context 3건·select_active 5건·연동 1건 |

---

## 4. 새로 들어올 파일 / 변경 위치

```
backend/
├── core/
│   └── read_services/protocols.py    ← (2단계) GrowthReader에 메서드 2개 추가
├── features/learning/
│   ├── curriculum.py                 ← (1단계 ✅) 완전 재작성
│   │                                    (3단계) CurriculumService 추가
│   ├── quizzes.py                    ← (5단계) curriculum에서 분리
│   ├── growth_dep.py                 ← (2단계) 신규 — fallback reader
│   ├── concept_detector.py           ← (7단계) 신규 — 키워드 매칭
│   ├── router.py                     ← (4·6단계) 엔드포인트 2개 추가
│   └── service.py                    ← (8단계) 프롬프트 조립부 보강
└── tests/features/test_learning.py   ← 단계마다 추가
```

**손 안 댄 영역**:
- `features/growth/` — 다른 팀원 담당
- `features/learning/personas/` — 페르소나 자체는 그대로
- `core/ai_pipeline/` — RAG·guardrail·critic·hallucination·tier_overlay 그대로

---

## 5. 미리 짚어둔 함정 4개

1. **마스터리를 학습동 안에 저장하지 말 것** — `learning_concept_masteries` 같은 테이블을 임시로 만들면 성장동 들어왔을 때 데이터 마이그레이션 필요. 더미 fallback에서 항상 빈셋 받는 게 깔끔 (성장도 없으니 모두 "막 시작한 T1"으로 보이는 게 자연스러운 더미 동작).
2. **개념 감지를 너무 일찍 LLM으로 가지 말 것** — v1은 키워드 정규식. 호출당 토큰 한 번 더 쓰는 LLM 분류는 v2.
3. **`active_concept` 우선순위** — `detected → current_concept → next_recommended` 순. 사용자가 "PER 말고 복리 알려줘" 하면 detected가 바뀌어야 하니 detected 1순위. 락된 개념을 물어보면 "아직 T2부터 풀리는 개념이에요" 류 처리 필요.
4. **티어가 T1에 묶여있어도 흐름은 검증 가능** — 시드에 T1~T5 개념이 골고루 있어 "T1 available, T2 이상 locked" 상태를 눈으로 확인할 수 있음. 성장동 붙기 전부터 UI/로직 테스트 가능.

---

## 6. 후속 작업 (이 계획 바깥)

본 계획은 **"학습동 내부에서 가능한 모든 것"** 까지가 범위. 그 다음은 다른 팀의 손을 빌려야 하는 작업:

- **growth 동 실제 구현** — `ConceptMasteredEvent` 구독 → 게이지 갱신 → 80% 도달 시 `PromotionEligibleEvent` 발행. `register_growth_reader()` 호출. ← 본 계획에서 미리 깔아둔 인터페이스를 채우는 작업.
- **RAG 지식베이스 적재** — `learning_kb` Chroma 컬렉션이 현재 비어있음. 가치투자 도메인 문서 인제스트 파이프라인 필요. ← 별도 작업.
- **다른 멘토 전략의 커리큘럼 시드** — GROWTH/DIVIDEND/MOMENTUM 각 23~30개념 추가. 본 작업과 동일한 구조 위에 데이터만 추가하면 됨.
- **critic/hallucination 실제화** — 현재 더미. LLM-as-judge v2 필요. ← `core/ai_pipeline/` 영역.

---

## 7. 완료 기록

### 1단계 — Concept 모델 + 시드 데이터 (2026-05-20)

- **변경 파일**: [features/learning/curriculum.py](../features/learning/curriculum.py) (재작성), [tests/features/test_learning.py](../tests/features/test_learning.py) (보정 + 신규 4건)
- **검증**: ruff check ✓ / ruff format ✓ / mypy --strict ✓ / pytest 29 passed
- **라우터 호환성**: `get_quiz`/`grade_quiz` 시그니처 유지 — `router.py` 무변경
- **ID 마이그레이션**: 기존 1=PER, 2=복리, 3=안전마진 → 새 5=PER, 6=복리, 8=안전마진 (테스트 파라미터 보정 완료)

### 2단계 — GrowthReader Protocol 확장 + fallback (2026-05-20)

- **변경 파일**:
  - [core/read_services/protocols.py](../core/read_services/protocols.py) — `GrowthReader`에 `get_user_tier`, `get_mastered_concepts(user_id, strategy)` 추가. `ConceptId, MentorStrategy` import 추가.
  - [features/learning/growth_dep.py](../features/learning/growth_dep.py) (신규) — `_NullGrowthReader` 클래스(T1·빈셋·빈 분포) + `reader()` dispatch 함수.
  - [tests/features/test_learning_growth_dep.py](../tests/features/test_learning_growth_dep.py) (신규) — 미등록·등록 양 경로 검증 3건.
- **검증**: ruff check ✓ / ruff format ✓ / mypy --strict ✓ / pytest 46 passed (전체 회귀 없음)
- **계약**: 성장동 owner는 향후 자기 동에서 `register_growth_reader(GrowthReaderImpl())`만 호출하면 끝. 학습동 코드는 한 줄도 안 바뀜.
- **호출 규약**: 학습동 내부에서 `core.read_services.get_growth_reader()`를 **직접 호출하지 말 것**. 항상 `features.learning.growth_dep.reader()`를 통해서만 — fallback이 끊긴다.

### 3단계 — CurriculumService.get_position (2026-05-20)

- **변경 파일**:
  - [features/learning/curriculum.py](../features/learning/curriculum.py) — `CurriculumPosition` Pydantic 모델 추가, `get_position(user_id, strategy)` async 함수 + `_is_available` 헬퍼 추가. 모듈 docstring·`__all__` 갱신. `growth_dep` import 추가.
  - [tests/features/test_learning_curriculum_position.py](../tests/features/test_learning_curriculum_position.py) (신규) — 8건 (T1 더미·빈 전략 3건·prereq unlock·티어 락·all-mastered).
- **검증**: ruff check ✓ / ruff format ✓ / mypy --strict ✓ / pytest 54 passed (전체 회귀 없음)
- **MVP 단순화**: `current_concept = next_recommended`. 7단계 `concept_detector`가 들어오면 "대화에서 감지된 개념"을 `current_concept`에 우선 적용하도록 분기. 그 전에는 두 값이 항상 같다.
- **빈 전략 처리**: GROWTH/DIVIDEND/MOMENTUM은 시드가 없으므로 `available=[], locked=[], next=None, current=None`을 정상 반환 — 빈 전략 채팅 흐름이 깨지지 않는다.
- **현재 상태에서 외부에서 볼 수 있는 것**: 모든 사용자가 T1 더미. T1에서 `prereq=[]`인 4개(주식·매출과이익·인플레이션·복리)만 available, 나머지 19개는 locked. next_recommended는 항상 id=1 (주식이란 무엇인가).

### 4단계 — GET /api/learning/curriculum/me (2026-05-20)

- **변경 파일**:
  - [features/learning/router.py](../features/learning/router.py) — `Query` import 추가, `personas.get_mentor_strategy` import 추가, `my_curriculum_position` 엔드포인트 1개 추가 (채팅·퀴즈 섹션 사이). `CurriculumPosition`을 그대로 `response_model`로 사용.
  - [tests/features/test_learning_curriculum_position.py](../tests/features/test_learning_curriculum_position.py) — `test_position_is_json_serializable` 1건 추가 (set→list 직렬화 + Concept 키 노출 검증).
- **검증**: ruff check ✓ / ruff format ✓ / mypy --strict ✓ / pytest 55 passed. 라우터 inspect로 `GET /api/learning/curriculum/me` 등록 확인.
- **호출 예**:
  ```
  GET /api/learning/curriculum/me?mentor_id=1
  → CurriculumPosition (tier, mastered, available, locked, next_recommended, current_concept)
  ```
- **MVP 동작 (성장동 미연결 상태)**: 어떤 user_id로 호출해도 같은 결과. T1 4개 available + 19개 locked + next=주식(1). 데이터 시드 검증·프론트 UI 와이어링·OpenAPI 문서 확인에 충분.
- **mentor_id fallback**: 알 수 없는 mentor_id는 `personas.get_mentor_strategy`가 VALUE로 매핑 (기존 시스템 전반의 규칙과 일관). 시드 없는 전략 mentor_id가 들어오면 빈 Position을 반환.
- **통합 테스트는 보류**: get_position 자체와 응답 직렬화는 단위 테스트로 검증됨. TestClient 통합 테스트는 auth dependency mock이 필요해서 스코프 밖. 실제 동작은 swagger(`/docs`)에서 수동 확인.

### 5단계 — quizzes.py 분리 (2026-05-20)

- **변경 파일**:
  - [features/learning/quizzes.py](../features/learning/quizzes.py) (신규) — `QuizItem`/`QuizView` 모델, `_QUIZZES` 시드(23개), `get_quiz`/`grade_quiz` 공개 함수. concept_name 조회는 `curriculum.get_concept`에 위임.
  - [features/learning/curriculum.py](../features/learning/curriculum.py) — 퀴즈 관련 코드(모델·시드·함수) 제거. 960→505줄. 모듈 docstring 갱신("퀴즈 카탈로그는 quizzes.py로 분리됨"). `__all__`에서 quiz 심볼 4개 제거.
  - [features/learning/router.py](../features/learning/router.py) — `quizzes` 모듈 import 추가. `curriculum.get_quiz`/`grade_quiz` → `quizzes.get_quiz`/`grade_quiz`로 호출처 2곳 변경.
  - [tests/features/test_learning.py](../tests/features/test_learning.py) — quiz import 경로를 `features.learning.quizzes`로 보정.
- **검증**: ruff check ✓ / ruff format ✓ / mypy --strict ✓ / pytest 55 passed (회귀 없음). 라우트 8개 정상 등록.
- **의존 방향**: `quizzes → curriculum` 단방향. curriculum은 quizzes를 import하지 않으므로 순환 없음.
- **향후 확장 여지**: `_QUIZZES`가 `dict[ConceptId, list[QuizItem]]` 구조이므로 개념당 퀴즈 2~3개 추가는 데이터만 늘리면 됨. `get_quiz`는 현재 첫 번째 퀴즈만 반환하지만, 향후 랜덤화 또는 반복 학습 정책으로 확장 가능.

### 6단계 — GET /api/learning/quizzes/next (2026-05-20)

- **변경 파일**:
  - [features/learning/router.py](../features/learning/router.py) — `NotFoundError` import 추가, `next_quiz` 핸들러 1개 추가 (`/quizzes/{concept_id}` 위에 배치, 라우팅 충돌 회피).
  - [tests/features/test_learning_router_next_quiz.py](../tests/features/test_learning_router_next_quiz.py) (신규) — 라우터 핸들러 직접 호출(SimpleNamespace로 User mock) 4건.
- **검증**: ruff check ✓ / ruff format ✓ / mypy --strict ✓ / pytest 59 passed. 라우트 9개 정상 등록.
- **동작 요약**: `mentor_id` → strategy → `get_position()` → `current_concept or next_recommended`. 둘 다 None이면 404("학습 가능한 퀴즈가 더 없습니다"). 더미 환경에서는 항상 주식(1) 반환. 주식 마스터 후엔 채권/주식(2)로 자동 이동(prereq=[1] 해제).
- **에러 정책**: 404는 `core.exceptions.NotFoundError` 사용 → 등록된 글로벌 핸들러가 자동 404 응답 변환.
- **라우팅 순서**: `/quizzes/next`를 `/quizzes/{concept_id}` 앞에 배치. (실제로는 path param이 int 타입이라 "next"는 매칭 안 되지만 명시적으로 분리해 가독성 확보.)

### 7단계 — concept_detector.py (2026-05-20)

- **변경 파일**:
  - [features/learning/concept_detector.py](../features/learning/concept_detector.py) (신규) — `detect_concept(message, candidates) -> Concept | None` + 내부 `_count_keyword_matches` 헬퍼. v1 채점 규칙: 키워드 매칭 수 desc → id asc tiebreak. 대소문자 무시 부분 문자열 매칭.
  - [tests/features/test_learning_concept_detector.py](../tests/features/test_learning_concept_detector.py) (신규) — 12건 검증 (단일 명확 매칭 6·빈 입력 2·매칭 없음 1·빈 후보 1·동점 1·다중 매칭 1·case insensitive 1).
- **검증**: ruff check ✓ / ruff format ✓ / mypy --strict ✓ / pytest 71 passed (회귀 없음).
- **설계 결정**:
  - **stateless 순수 함수**: detector는 메시지+후보를 받아 결정 — 호출자(서비스)가 candidates 범위(전 개념 vs available만)를 결정.
  - **locked 감지 허용**: 사용자가 잠긴 개념을 물어볼 수 있음. 감지는 하되 "그건 아직 안 풀린 단원" 안내는 서비스(8단계)의 책임.
  - **휴리스틱의 한계**: "주식과 채권의 차이"는 동점 처리로 주식(1) 매칭 — 의도는 채권/주식차이(2)였을 수 있음. v2에서 LLM 분류로 정교화 예정.
- **활용 위치**: 다음 단계에서 [service.py](../features/learning/service.py)의 `stream_assistant_response`가 호출해 시스템 프롬프트에 `[현재 학습 단원]` 블록을 주입.

### 8단계 — chat_stream 커리큘럼 컨텍스트 주입 (2026-05-20)

- **변경 파일**:
  - [features/learning/service.py](../features/learning/service.py) — `MentorStrategy` import 추가, `curriculum`/`detect_concept` import 추가. 비공개 헬퍼 2개 추가: `_select_active_concept(message, strategy, position) -> (Concept | None, bool)`, `_build_curriculum_context(active, is_locked) -> str`. `stream_assistant_response` 본문에서 RAG 호출 직전에 두 헬퍼를 호출해 시스템 프롬프트에 `[현재 학습 단원]` 블록 주입. `learning.curriculum_active` info 로그 추가.
  - [tests/features/test_learning_chat_curriculum.py](../tests/features/test_learning_chat_curriculum.py) (신규) — 9건 (build_context None·unlocked·locked / select_active detected우선·fallback·locked감지·unlocked·빈전략).
- **검증**: ruff check ✓ / ruff format ✓ / mypy --strict ✓ / pytest 79 passed (전체 회귀 없음).
- **주입되는 프롬프트 블록 예 (unlocked)**:
  ```
  [현재 학습 단원] PER (주가수익비율)
  [요약] PER = 주가 ÷ EPS. 현재 이익이 유지된다는 가정 하에 ...
  [학습 목표]
  - PER 계산법과 직관적 의미를 안다
  - 동종 업종 비교 외에 단일 PER의 해석 한계를 이해한다

  이 대화는 위 단원을 중심으로 설명해. 사용자가 충분히 이해한 것 같으면 자연스럽게 확인 퀴즈를 권유해.
  ```
- **locked 케이스**: 위 블록 + `[잠긴 단원] ... 선수 개념부터 다져야 할지 안내해.` 추가.
- **빈 전략(GROWTH/DIVIDEND/MOMENTUM) 또는 전부 마스터**: 컨텍스트 블록을 추가하지 않음 — 기존 채팅 흐름 그대로 유지.
- **선정 우선순위**: `detected(키워드 매칭) → position.current_concept → position.next_recommended`. MVP에서 current_concept = next_recommended이므로 사실상 `detected → next_recommended` 2단계.
- **함수 분리 이유**: 헬퍼 2개를 모듈 레벨 함수로 빼서 SSE 제너레이터(DB·LLM 의존) 통합 테스트 없이도 핵심 로직을 단위 테스트로 검증 가능.

---

## 8. 최종 상태 — 학습동이 닫혔다

기획 의도 → 코드 사슬이 완성됨:

```
사용자 메시지 + 멘토 선택
    ↓
GET /curriculum/me  →  CurriculumPosition (tier·available·locked·next)
GET /quizzes/next   →  추천 퀴즈
POST /chat/stream   →  active 단원이 시스템 프롬프트에 들어간 멘토 응답
                       (필요시 [잠긴 단원] 안내 포함)
```

성장동 미연결 상태에서 보이는 동작:
- 모든 사용자가 T1 더미. T1 prereq=[] 4개(주식·매출과이익·인플레이션·복리)만 available.
- "PER 알려줘" 채팅: detector가 PER을 잡고, locked 상태로 안내 → "PER을 익히려면 먼저 주식과 매출/이익을 다져야 한다" 류 답변.
- "주식이 뭐야" 채팅: detector가 주식(1)을 잡고, unlocked 상태로 단원 중심 설명.

성장동이 `register_growth_reader()` 한 줄을 추가하면:
- 실제 티어·마스터리가 흘러옴. 학습동 코드 한 줄도 변경되지 않음.
- 사용자가 개념을 마스터할 때마다 available이 늘어나고, next_recommended가 자동 이동.
- 시스템 프롬프트가 사용자의 진도에 맞춰 자동으로 변함.

---

## 9. 추가 단계 — 대화 중 follow-up 퀴즈 (사용 흐름 정렬)

[기획자가 추가로 요구한 사용 흐름](7번 §0 위에 명시):
> 하나의 채팅 세션 안에서 → 사용자/멘토 메시지에 개념 키워드 등장이 트리거 → 멘토 응답 끝에 그 개념의 퀴즈 버튼 1개. 정답으로 풀면 그 문제는 다신 안 나옴(오답은 재도전 허용). 같은 개념 키워드 재등장해도 마스터한 퀴즈는 skip. 다른 개념 키워드 나오면 그쪽으로 진행.

### 9.1 정책 요약

```
follow-up 대상 결정:
1. 사용자 메시지에 키워드 매칭 → 그 개념
2. (없으면) 멘토 응답에 키워드 매칭 → 그 개념
3. 둘 다 None이면 follow-up 안 보냄

대상 개념이 결정되면:
- locked → follow-up 안 보냄 (멘토 본문에서 선수 안내)
- unlocked → 사용자의 quiz_attempts에서 correct=True인 quiz_index 제외 → 안 푼 가장 작은 인덱스 1개 SSE push
- 모든 퀴즈를 마스터했으면 → follow-up 안 보냄 (현 시점, 향후 SRS 확장 여지)

기록:
- POST /quizzes/submit 시 (user_id, concept_id, quiz_index, correct) DB 저장
- 같은 (concept, quiz_index)에 대해 여러 attempt 허용 (오답 후 재도전)
```

### 9.2 작업 표

| # | 단계 | 산출물 | 상태 |
|---|---|---|---|
| **9** | **`learning_quiz_attempts` 테이블 + 마이그레이션** | [models.py](../features/learning/models.py) `QuizAttempt` 모델 추가. [migrations/versions/20260520_learning_quiz_attempts.py](../migrations/versions/20260520_learning_quiz_attempts.py) — 컬럼 (id, user_id FK CASCADE, concept_id, quiz_index, correct, created_at) + (user_id, concept_id) 복합 인덱스 | ✅ 완료 (2026-05-20) |
| **10** | **로테이션 정책 함수** | [quizzes.py](../features/learning/quizzes.py) — 순수 함수 `_pick_from_pool(pool, mastered_indices)` + DB 함수 `pick_for_user(user_id, concept_id, db) -> tuple[QuizItem, int] \| None`. correct=True인 quiz_index 제외, 안 푼 가장 작은 인덱스 1개 반환 | ✅ 완료 (2026-05-20) |
| **11** | **`/quizzes/submit`이 attempt 기록** | [schemas.py](../features/learning/schemas.py)의 `SubmitQuizReq`에 `quiz_index: int = 0` 추가. [quizzes.py](../features/learning/quizzes.py)에 `record_attempt` + `grade_quiz`가 quiz_index 인자 받도록 확장. [router.py](../features/learning/router.py)의 `submit_quiz`가 채점 → `record_attempt` → commit → 정답 시 `ConceptMasteredEvent` 발행 | ✅ 완료 (2026-05-20) |
| **12** | **SSE follow-up 이벤트** | [schemas.py](../features/learning/schemas.py)에 `FollowUpQuiz` 페이로드 모델 추가. [service.py](../features/learning/service.py)에 `_pick_followup_concept` 헬퍼(fallback 없는 detector — 사용자 우선·멘토 응답 fallback). `stream_assistant_response`가 응답 종료 직후 follow-up 결정 → locked skip → `pick_for_user` → `event="follow_up_quiz"` push | ✅ 완료 (2026-05-20) |

### 9.3 9단계 완료 기록 (2026-05-20)

- **변경 파일**:
  - [features/learning/models.py](../features/learning/models.py) — `Boolean, Integer, Index` import 추가. `QuizAttempt` 모델(테이블·복합 인덱스 포함).
  - [migrations/env.py](../migrations/env.py) — `QuizAttempt` import 추가.
  - [migrations/versions/20260520_learning_quiz_attempts.py](../migrations/versions/20260520_learning_quiz_attempts.py) (신규) — `alembic revision --autogenerate`로 생성 후 파일명·revision id를 컨벤션에 맞춰 정리.
- **검증**:
  - alembic upgrade head ✓ — `20260519_learning_init_chat → 20260520_learning_quiz_attempts` 적용됨
  - downgrade -1 + upgrade head 왕복 정상
  - 실제 dev DB(Postgres 컨테이너)에 스키마 적용·`\d learning_quiz_attempts`로 컬럼·FK·인덱스 모두 의도대로 확인
  - ruff ✓ / ruff format ✓ / mypy --strict ✓ / pytest 79 passed (회귀 없음)
- **설계 결정**:
  - `user_id`에 `ForeignKey(users.id, ondelete="CASCADE")` — 기존 `ChatSession`의 패턴과 일치. 사용자 삭제 시 attempts도 자동 제거.
  - `concept_id`엔 FK 없음 — 카탈로그 데이터(코드 dict)라 DB 외래키 불가.
  - **유니크 제약 없음** — 같은 사용자가 같은 (concept_id, quiz_index)를 여러 번 attempt 가능해야 함 (오답 후 재도전 허용).
  - 복합 인덱스 `(user_id, concept_id)` — follow-up 결정의 핫 패스가 "이 사용자의 이 개념에 대한 attempts 조회"라 이걸 최적화.

### 9.4 10단계 완료 기록 (2026-05-20)

- **변경 파일**:
  - [features/learning/quizzes.py](../features/learning/quizzes.py) — `select`/`AsyncSession`/`UserId`/`QuizAttempt` import 추가. 순수 함수 `_pick_from_pool(pool, mastered_indices)` + DB 함수 `pick_for_user(user_id, concept_id, db)` 추가. `__all__`에 `pick_for_user` 노출.
  - [tests/features/test_learning_quiz_rotation.py](../tests/features/test_learning_quiz_rotation.py) (신규) — 10건 (순수 함수 5건 + DB 통합 5건). 고유 email로 fixture_user 생성·테스트 종료 시 CASCADE로 attempts 정리.
  - [pyproject.toml](../pyproject.toml) — `asyncio_default_fixture_loop_scope = "session"` + `asyncio_default_test_loop_scope = "session"` 추가. asyncpg connection pool과 이벤트 루프 lifecycle 충돌(`Event loop is closed`) 해소.
- **검증**:
  - ruff ✓ / mypy --strict ✓ / pytest 89 passed (전체 회귀 없음, 신규 10건)
  - 실제 Postgres DB에 fixture user INSERT + attempts INSERT/SELECT 정상 동작
  - CASCADE로 fixture cleanup도 정상 (테스트 격리 확인)
- **함수 분리 의도**: SQLAlchemy 쿼리 검증과 선정 알고리즘 검증을 분리. `_pick_from_pool`은 DB 없이 단위 테스트, `pick_for_user`는 통합 테스트로 한 번씩만 검증.
- **검증된 정책**:
  - attempts 없음 → 첫 퀴즈
  - correct=True인 quiz_index는 skip (시드 1개 + 정답 = None 반환)
  - correct=False는 마스터로 안 침 (오답 후 재도전 가능)
  - 모르는 concept_id → None (예외 아님)
  - 사용자 간 격리 (한 사용자의 정답이 다른 사용자에 영향 없음)

### 9.5 11단계 완료 기록 (2026-05-20)

- **변경 파일**:
  - [features/learning/schemas.py](../features/learning/schemas.py) — `SubmitQuizReq`에 `quiz_index: int = Field(0, ...)` 추가. default=0이라 기존 클라이언트 호출 호환.
  - [features/learning/quizzes.py](../features/learning/quizzes.py) — `grade_quiz`에 `quiz_index: int = 0` 인자 추가, pool 범위 체크 + 해당 인덱스 채점. `record_attempt(user_id, concept_id, quiz_index, correct, db)` 함수 신규 (flush만, commit은 호출자 책임).
  - [features/learning/router.py](../features/learning/router.py) — `submit_quiz` 핸들러에 `db: AsyncSession = Depends(get_db)` 의존성 추가. `grade_quiz` 호출에 `quiz_index` 전달, `record_attempt` 호출 + `db.commit()`. 정답 시 기존대로 `ConceptMasteredEvent` 발행.
  - [tests/features/test_learning_quiz_submit.py](../tests/features/test_learning_quiz_submit.py) (신규) — 4건 (정답 기록+이벤트 / 오답 기록+무이벤트 / 다중 attempt / quiz_index 미지정 하위 호환).
- **검증**: ruff ✓ / mypy --strict ✓ / pytest 93 passed (전체 회귀 없음, 신규 4건)
- **이벤트 테스트 방식**: `event_bus.publish`가 Redis pub/sub 기반이라 in-process `subscribe` 콜백으로는 캐치 불가. `monkeypatch.setattr(event_bus, "publish", ...)` 로 publish 자체를 가로채 호출 인자만 캡처하는 `captured_events` fixture로 단순화.
- **ConceptMasteredEvent 의미 메모**: 학습동은 정답마다 이벤트 발행 — 같은 (concept_id, quiz_index)를 여러 번 정답으로 풀어도 매번 발행됨. **"개념 마스터" 판정과 누적·dedup은 성장동 owner의 책임** (1주차_인수인계서.md §3동 명시). 학습동은 raw 신호만 송신.

### 9.6 12단계 완료 기록 (2026-05-20)

- **변경 파일**:
  - [features/learning/schemas.py](../features/learning/schemas.py) — `FollowUpQuiz` Pydantic 모델 추가 (concept_id, concept_name, quiz_index, question, options). correct_index/explanation은 노출 안 함 (submit 응답에서 제공).
  - [features/learning/service.py](../features/learning/service.py) — `quizzes` import 추가, `FollowUpQuiz` import. `_pick_followup_concept(user_message, mentor_answer, strategy)` 헬퍼 추가(fallback 없는 detector — 사용자 메시지 우선, 멘토 응답 fallback, 둘 다 없으면 None). `stream_assistant_response`의 후처리 검증 직후·DB 저장 직전에 follow-up 결정 로직 + SSE `event="follow_up_quiz"` yield 추가. `learning.follow_up_quiz_sent` info 로그.
  - [tests/features/test_learning_chat_curriculum.py](../tests/features/test_learning_chat_curriculum.py) — `_pick_followup_concept` 검증 5건 추가 (사용자 매칭·멘토 매칭·둘 다 없음·사용자 우선·빈 전략).
- **검증**: ruff ✓ / mypy --strict ✓ / pytest 98 passed (전체 회귀 없음, 신규 5건)
- **트리거 정책 (의도된 동작 확정)**:
  - 사용자 메시지에 키워드 → 그 개념의 퀴즈
  - 사용자 메시지에 키워드 없고 멘토 응답에만 → 멘토 응답에서 감지된 개념의 퀴즈
  - 둘 다 키워드 없음 → follow-up 안 보냄 (평소 일반 대화는 퀴즈 버튼 없음)
  - 감지된 개념이 locked → follow-up 안 보냄 (멘토는 본문에서 선수 안내)
  - 사용자가 그 개념을 이미 정답으로 풀음 (시드 1개 시점) → follow-up 안 보냄
- **로테이션 + 중복 회피 완성**: 정답 후 같은 개념 키워드 재등장해도 무반응 → 다른 개념 키워드 나와야 새 퀴즈. 오답이면 같은 문제 재후보. 시드가 개념당 N개로 늘어나면 자동으로 다음 quiz_index 노출 (코드 변경 X).

---

## 10. 최종 사용자 흐름 — 완성된 코드의 실제 동작

기획자가 명시한 사용 흐름:
> 사용자는 멘토와의 채팅 중에 자신의 레벨·진행도에 맞는 퀴즈를 대화 끝에 버튼 형태로 받는다.
> 한 번에 1개. 같은 문제는 다시 안 받음. 다만 틀린 경우엔 다시 받음.
> 별도 퀴즈 탭 X — 채팅 안에서 키워드가 트리거.

### 실제 동작 (성장동 미연결 = 모두 T1·빈 마스터리 상태)

```
[Turn 1] 사용자: "안녕하세요"
  detector: 매칭 없음
  → SSE: LLM 응답 청크들. follow_up_quiz 이벤트 없음.
  UI: 멘토 응답만, 퀴즈 버튼 없음.

[Turn 2] 사용자: "PER이 뭐야?"
  detector(사용자): PER(5) 매칭
  position: PER은 prereq=[1,3] 미충족 → locked
  → follow_up 안 보냄 (locked skip)
  멘토 본문: "PER을 익히려면 먼저 주식·매출과 이익부터..."
  UI: 멘토 응답만, 퀴즈 버튼 없음.

[Turn 3] 사용자: "주식이 뭐야?"
  detector(사용자): 주식(1) 매칭, prereq=[] unlocked
  pick_for_user(uid, 1, db): attempts 없음 → 주식 quiz_index=0
  → SSE follow_up_quiz: {concept=1, idx=0, question, options}
  UI: 멘토 응답 + 주식 퀴즈 버튼

[Turn 3'] 사용자가 버튼 클릭 → submit 오답
  → DB: (uid, 1, 0, correct=False)
  → 채점 응답: {correct: false, explanation}

[Turn 4] 사용자: "주식 좀 다시 설명해줘"
  detector(사용자): 주식(1) 매칭
  pick_for_user: mastered_indices={} (오답은 마스터 아님) → quiz_index=0
  → SSE follow_up_quiz: 같은 주식 퀴즈 다시
  UI: 멘토 응답 + 주식 퀴즈 버튼 (재도전)

[Turn 4'] 사용자가 다시 풀어 정답
  → DB: (uid, 1, 0, correct=True)
  → ConceptMasteredEvent 발행 (성장동 미연결이라 구독자 없음)

[Turn 5] 사용자: "주식이 좀 어렵네"
  detector(사용자): 주식(1) 매칭
  pick_for_user: mastered_indices={0} (정답) → available=[] → None
  → follow_up 안 보냄 (마스터 완료)
  UI: 멘토 응답만, 퀴즈 버튼 없음.

[Turn 6] 사용자: "복리는?"
  detector(사용자): 복리(6) 매칭, prereq=[] unlocked
  pick_for_user(uid, 6, db): attempts 없음 → 복리 quiz_index=0
  → SSE follow_up_quiz: 복리 퀴즈
  UI: 멘토 응답 + 복리 퀴즈 버튼
```

### 기획 요구사항 충족도 (재평가)

| # | 요구사항 | 상태 |
|---|---|---|
| 1 | 멘토와의 채팅 중에 | ✅ POST /chat/stream |
| 2 | 레벨·진행도에 알맞은 | ✅ `pick_for_user`가 attempts 기반 결정 (성장동 연결 시 티어도 자동 반영) |
| 3 | **자연스럽게 대화 끝에 버튼 형태로 제공** | ✅ SSE `event="follow_up_quiz"` 첨부 |
| 4 | 한 번에 1개만 | ✅ 매 응답에 최대 1개 |
| 5 | **한 대화가 끝나면 제공** | ✅ LLM 응답 종료 직후 SSE 푸시 |
| 6 | **관련된** 퀴즈 | ✅ 사용자/멘토 메시지의 키워드 매칭 |
| 7 | **로테이션 — 중복 회피, 오답은 재제공** | ✅ `pick_for_user`가 correct=True quiz_index만 skip |

이전 평가(30% 만족)에서 **모든 항목 ✅로 완전 충족**.

### 프론트엔드가 해야 할 일 (백엔드는 끝)

1. SSE 구독에서 `event: delta` 외에 `event: follow_up_quiz` 추가 처리
2. 멘토 메시지 컴포넌트 아래에 퀴즈 버튼 렌더 (concept_name + question 미리보기)
3. 버튼 클릭 → 퀴즈 모달/오버레이로 question + options 표시
4. 사용자 선택 시 `POST /api/learning/quizzes/submit` 호출 (`concept_id, answer_index, quiz_index` 포함)
5. 응답 받아 정답/해설 표시 → 다음 대화로 자연스럽게 복귀

### 성장동 owner가 해야 할 일

성장동이 `features/growth/__init__.py`에 한 줄만 추가하면 — **학습동 코드 0줄 변경 없이** — 실제 사용자 티어·마스터리가 흘러와 시스템 프롬프트와 follow-up 결정에 자동 반영됨:
```python
from core.read_services import register_growth_reader
from .read_service import GrowthReaderImpl

register_growth_reader(GrowthReaderImpl())
```

`ConceptMasteredEvent` 구독자도 등록 시 정답마다 게이지 갱신 가능 (학습동의 raw 신호 → 성장동의 누적·승급 판정).
