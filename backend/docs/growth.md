# 성장(growth) 구현 정리

## 1. 이 문서의 목적

이 문서는 성장 모듈이 현재 코드에서 어떤 구조로 동작하는지 빠르게 파악하기 위한 정리입니다.

특히 아래 내용을 중심으로 설명합니다.

- 진행도는 어디서 계산되는가
- `ConceptMasteredEvent`가 오면 어떤 일이 일어나는가
- 승급시험은 어떤 조건에서 열리는가
- 시험 통과 시 티어는 어디에 반영되는가
- 다른 모듈은 현재 티어를 어디서 읽는가

---

## 2. 관련 파일

### 백엔드 핵심 파일

- `backend/features/growth/router.py`
- `backend/features/growth/service.py`
- `backend/features/growth/models.py`
- `backend/features/growth/catalog.py`
- `backend/features/growth/schemas.py`
- `backend/features/growth/handlers.py`
- `backend/features/growth/bootstrap.py`
- `backend/migrations/versions/20260515_growth_create_progress_tables.py`
- `backend/core/user_context/service.py`
- `backend/main.py`

### 프론트 연결 파일

- `frontend/src/features/growth/api.ts`
- `frontend/src/features/growth/logic.ts`
- `frontend/src/features/growth/components/GrowthProgressCard.tsx`
- `frontend/src/features/promotion-test/screens/PromotionTestScreen.tsx`
- `frontend/src/navigation/RootNavigator.tsx`

---

## 3. 성장 모듈이 관리하는 데이터

성장 모듈은 아래 3개 테이블을 중심으로 동작합니다.

### 3.1 `tier_states`

사용자별 성장 상태의 현재값을 들고 있는 테이블입니다.

- 현재 티어
- 현재 티어에서 완료한 개념 수
- 현재 티어의 전체 개념 수
- 진행도 퍼센트
- 승급시험 응시 가능 시각
- 마지막 승급시험 응시 시각

이 테이블은 “현재 스냅샷”에 가깝습니다.

### 3.2 `concept_masteries`

사용자가 어떤 개념을 이미 통과했는지 저장하는 테이블입니다.

- 사용자 ID
- 티어
- 개념 ID
- 이벤트 ID
- 완료 시각

중복 방지를 위해 두 가지 제약이 걸려 있습니다.

- 같은 사용자가 같은 개념을 두 번 쌓지 못하게 하는 제약
- 같은 이벤트를 두 번 처리하지 못하게 하는 제약

### 3.3 `promotion_test_attempts`

승급시험 결과 이력을 저장하는 테이블입니다.

- 시험 당시 현재 티어
- 목표 티어
- 총 문항 수
- 정답 수
- 점수
- 통과 여부
- 제출 답안
- 응시 시각

즉 `tier_states`는 현재 상태, `promotion_test_attempts`는 이력입니다.

---

## 4. 코드 흐름 한눈에 보기

성장 모듈은 크게 두 갈래로 움직입니다.

### 4.1 조회 흐름

- `GET /api/growth/me/tier`
- `GET /api/growth/me/progress`

이 흐름은 현재 티어와 진행도를 읽어 사용자에게 보여주는 역할입니다.

### 4.2 이벤트/상태 변경 흐름

- `ConceptMasteredEvent`
- `POST /api/growth/promotion-test`

이 흐름은 실제로 진행도를 올리고, 승급시험을 처리하고, 티어를 바꾸는 역할입니다.

---

## 5. 앱 시작 시 어떤 준비를 하는가

성장 이벤트 구독은 앱 시작 시 등록됩니다.

흐름은 다음과 같습니다.

1. `backend/main.py`에서 `register_growth_subscriptions()`를 호출합니다.
2. `backend/features/growth/bootstrap.py`가 `ConceptMasteredEvent`와 `on_concept_mastered` 핸들러를 연결합니다.
3. 이후 학습 모듈이 `ConceptMasteredEvent`를 발행하면 성장 모듈이 이를 받게 됩니다.

즉 성장 모듈은 직접 학습 DB를 건드리지 않고, 이벤트를 통해 진행도를 올리도록 설계돼 있습니다.

---

## 6. 진행도는 어떻게 계산되는가

진행도 계산의 중심은 `service.compute_progress()`입니다.

계산 방식은 단순합니다.

1. 현재 티어에 속한 개념 목록을 `catalog.py`에서 가져옵니다.
2. 그 중 사용자가 이미 완료한 개념 ID 집합을 구합니다.
3. 두 집합의 교집합 개수를 셉니다.
4. `완료 개념 수 / 전체 개념 수 * 100`으로 퍼센트를 계산합니다.
5. 80% 이상이고 다음 티어가 있으면 `eligible_for_promotion = true`가 됩니다.

즉 성장의 핵심은 XP 누적이 아니라 “현재 티어 개념을 몇 개 이해했는가”입니다.

---

## 7. `ConceptMasteredEvent`가 오면 어떤 일이 일어나는가

이 흐름은 `handlers.py`와 `service.process_concept_mastered_event()`가 담당합니다.

순서는 다음과 같습니다.

1. 학습 모듈이 `ConceptMasteredEvent`를 발행합니다.
2. `handlers.on_concept_mastered()`가 새 DB 세션을 열어 서비스 함수를 호출합니다.
3. 성장 서비스는 먼저 현재 티어 상태를 가져옵니다.
   - `tier_states`가 없으면 `_ensure_tier_state()`로 만듭니다.
4. 전달받은 개념이 현재 티어에 속한 개념인지 확인합니다.
   - 다른 티어 개념이면 무시합니다.
5. 이미 처리한 개념인지 확인합니다.
   - 이미 있으면 중복 처리하지 않습니다.
6. `concept_masteries`에 개념 완료 기록을 저장합니다.
7. 저장 전/후 진행도를 각각 계산합니다.
8. `tier_states`의 완료 개수와 퍼센트를 동기화합니다.
9. 이번 이벤트로 처음 80%를 넘었다면:
   - `promotion_eligible_at`를 기록합니다.
   - `PromotionEligibleEvent`를 발행합니다.
   - 푸시 알림을 보냅니다.
10. commit 합니다.

핵심은 “개념 완료 이벤트가 쌓이면 진행도 테이블이 자동 갱신된다”는 점입니다.

---

## 8. 티어 조회는 어디서 읽는가

티어 조회는 성장 모듈 안에서만 쓰는 값이 아니라, 다른 모듈도 공통으로 읽습니다.

이를 담당하는 곳이 `backend/core/user_context/service.py`입니다.

`user_context.get_tier()`의 우선순위는 다음과 같습니다.

1. `tier_states.current_tier`
2. 없으면 `user_profiles.current_tier`
3. 둘 다 없으면 `T1`

이 우선순위가 중요한 이유는, 사용자가 승급시험에 통과한 뒤 다른 모듈이 바로 새 티어를 읽어야 하기 때문입니다.

즉 성장 모듈이 실제 티어의 최신 source of truth 역할을 하도록 맞춘 상태입니다.

---

## 9. `GET /api/growth/me/tier` 흐름

이 API는 가장 단순한 조회 API입니다.

1. `router.py`에서 요청을 받습니다.
2. 인증 사용자 ID를 가져옵니다.
3. `user_context.get_tier()`를 호출합니다.
4. 현재 티어와 다음 티어를 응답합니다.

이 API는 “사용자가 지금 어느 단계인가”만 빠르게 알고 싶을 때 쓰는 얇은 래퍼입니다.

---

## 10. `GET /api/growth/me/progress` 흐름

이 API는 홈의 성장 카드에 필요한 정보를 한 번에 내려주는 API입니다.

흐름은 다음과 같습니다.

1. `router.py`가 요청을 받습니다.
2. `service.get_growth_progress()`를 호출합니다.
3. `_ensure_tier_state()`로 상태 row를 확보합니다.
   - 없으면 현재 사용자 티어를 읽어 초기 row를 만듭니다.
4. 현재 티어의 완료 개념 목록을 읽습니다.
5. `compute_progress()`로 퍼센트를 계산합니다.
6. 필요하면 `tier_states`의 수치를 최신 값으로 맞춥니다.
7. 아래 정보를 묶어 응답합니다.
   - 현재 티어
   - 다음 티어
   - 진행도 퍼센트
   - 완료 개념 수 / 전체 개념 수
   - 승급 가능 여부
   - 현재 해금 기능
   - 다음 티어 해금 기능
   - 승급 가능하면 시험 미리보기

즉 프론트는 이 API 하나만으로 “게이지 + 해금 + 시험 진입 가능 여부”를 모두 그릴 수 있습니다.

---

## 11. 승급시험은 어떤 조건에서 열리는가

조건은 코드와 문서 모두 동일하게 2개입니다.

1. 현재 티어의 진행도가 80% 이상일 것
2. 다음 티어가 존재할 것

이 조건을 만족하면 `GET /api/growth/me/progress` 응답의 `promotion_test` 필드가 `null`이 아니라 실제 문제 목록으로 내려옵니다.

즉 시험 화면은 별도 조회 API 없이도 `progress` 응답만으로 구성할 수 있게 되어 있습니다.

---

## 12. `POST /api/growth/promotion-test` 흐름

이 API가 실제 티어 변경을 담당합니다.

흐름은 다음과 같습니다.

1. `router.py`가 답안을 받습니다.
2. `service.submit_promotion_test()`를 호출합니다.
3. 현재 성장 상태와 진행도를 다시 계산합니다.
4. 아래 조건을 검사합니다.
   - 이미 최고 티어인지
   - 아직 80%를 못 채웠는지
   - 답안이 중복되거나 빠진 문항이 없는지
5. `grade_promotion_test()`가 정답 수와 점수를 계산합니다.
6. `promotion_test_attempts`에 응시 이력을 저장합니다.
7. `PromotionTestStartedEvent`를 발행합니다.
8. 합격이면:
   - `tier_states.current_tier`를 다음 티어로 변경
   - `promotion_eligible_at` 초기화
   - 새 티어 기준 진행도 스냅샷으로 상태 필드 갱신
   - 호환성을 위해 `user_profiles.current_tier`도 같이 갱신
   - `PromotionTestPassedEvent` 발행
9. 불합격이면 현재 티어를 유지합니다.
10. commit 후 결과 응답을 반환합니다.

즉 티어 승급의 실제 기준은 “80% 도달”이 아니라 “80% 도달 후 시험 통과”입니다.

---

## 13. 해금 기능은 어디서 결정되는가

해금 규칙은 `service.py`의 `_UNLOCKS_BY_TIER`에 들어 있습니다.

현재 구현 기준:

- `T1`: 없음
- `T2`: `debate_arena`
- `T3`: `debate_arena`, `extra_mentors`
- `T4`, `T5`: 동일 유지

이 정보는 아래 두 함수로 응답에 반영됩니다.

- `get_unlocked_feature_codes()`
- `get_next_unlock_codes()`

즉 프론트는 현재 열린 기능과 다음 티어에서 열릴 기능을 모두 표시할 수 있습니다.

---

## 14. 프론트에서는 이 흐름을 어떻게 쓰는가

프론트는 홈과 승급시험 화면에서 성장 API를 사용합니다.

### 14.1 홈 화면

`RootNavigator.tsx`의 홈 화면에서 `GET /api/growth/me/progress`를 호출합니다.

이 응답으로 아래를 그립니다.

- 현재 티어
- 진행도 게이지
- 해금 기능
- 다음 해금 기능
- 승급시험 버튼 노출 여부

### 14.2 승급시험 화면

`PromotionTestScreen.tsx`는 같은 `progress` 응답의 `promotion_test`를 읽어 문제를 그립니다.

사용자가 답을 고르면 `POST /api/growth/promotion-test`를 호출하고, 결과가 성공이면 다시 progress query를 invalidate 해서 홈 상태가 새 티어 기준으로 갱신됩니다.

즉 프론트는 별도 티어 계산 없이, 백엔드가 내려주는 성장 상태를 그대로 보여주는 구조입니다.

---

## 15. 코드를 읽을 때 추천하는 순서

성장 코드를 처음 보는 사람이라면 아래 순서가 가장 이해하기 쉽습니다.

1. `router.py`
   - 어떤 API가 열려 있는지 확인
2. `schemas.py`
   - 요청/응답 구조 확인
3. `service.py`
   - 실제 핵심 로직 확인
4. `catalog.py`
   - 티어별 개념과 승급시험 문제 확인
5. `models.py`
   - DB 상태 구조 확인
6. `handlers.py` / `bootstrap.py`
   - 이벤트 연결 확인
7. `core/user_context/service.py`
   - 다른 모듈이 현재 티어를 어떻게 읽는지 확인

---

## 16. 현재 구현 범위와 남은 연동

현재 기준으로 성장 모듈 자체는 구현과 검증이 끝난 상태입니다.

이미 구현된 것:

- 성장 상태 테이블
- 개념 완료 기록
- 진행도 계산
- 80% 승급 가능 판정
- 승급시험 미리보기
- 승급시험 채점
- 티어 승급 반영
- 해금 기능 응답
- `user_context` 티어 우선 조회 반영
- 프론트 성장 카드 / 승급시험 화면 연결

다른 팀 연동이 남아 있는 부분:

- 학습 모듈이 실제로 `ConceptMasteredEvent`를 발행하는 부분
- `debate_arena`, `extra_mentors`가 티어 해금값을 실제 접근 제어에 쓰는 부분
- 최종 로그인 흐름에서 프론트 토큰 주입이 자연스럽게 되는 부분

즉 성장 모듈 owner 범위는 끝났고, 남은 것은 다른 도메인과의 연결 작업입니다.
