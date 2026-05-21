# 학습-성장 통합 정리

이 문서는 `main` 기준으로 정리된 현재 학습-성장 연동 구조를 설명합니다.

## 핵심 요약

이제 시스템은 **하나의 개념 ID 체계**를 사용합니다.

- `learning/curriculum.py`가 개념 그래프와 티어 배치를 관리합니다.
- `learning/quizzes.py`가 해당 개념의 퀴즈를 관리합니다.
- `growth`는 더 이상 별도의 `101~505` 개념 카탈로그를 갖지 않습니다.
- `growth`는 현재 티어에 속한 **학습 개념**의 숙련 상태를 기준으로 진행도를 계산합니다.

즉, 흐름은 다음과 같습니다.

`학습 개념 -> 퀴즈 정답 -> ConceptMasteredEvent -> 성장 진행도 반영`

## 왜 바뀌었나

이전 호환 버전은 두 개의 개념 모델을 동시에 유지했습니다.

- 학습 개념: `1~23`
- 성장 개념: `101~505`

이 방식은 머지 충돌을 줄이는 데는 유리했지만, `main`의 커리큘럼 설계와 요구분석서의 의도에는 맞지 않았습니다. 요구분석서에서는 티어를 별도 개념 우주로 보지 않고, 학습 콘텐츠를 어떤 난이도와 순서로 노출할지 결정하는 축으로 다룹니다.

## 현재 기준 모델

### 학습

- `backend/features/learning/curriculum.py`
- `backend/features/learning/quizzes.py`

이 두 파일이 다음을 정의합니다.

- 어떤 개념이 존재하는지
- 각 개념이 어느 티어에 속하는지
- 각 개념에 어떤 퀴즈가 연결되는지

### 성장

- `backend/features/growth/catalog.py`
- `backend/features/growth/service.py`
- `backend/features/growth/read_service.py`

성장 모듈은 여전히 다음 책임을 가집니다.

- 진행도 계산
- 승급 가능 여부 판단
- 승급시험 제공
- 기능 해금 규칙 관리

다만 티어별 개념 목록 자체는 이제 `learning.curriculum`에서 파생됩니다.

## 백엔드 연동 흐름

### 1. 현재 티어 퀴즈 목록 조회

`GET /api/learning/me/quizzes`

처리 순서는 다음과 같습니다.

1. `GrowthReader`를 통해 사용자의 현재 티어를 읽습니다.
2. 현재 티어에 속한 학습 개념을 찾습니다.
3. 각 개념에 대응하는 퀴즈를 `learning.quizzes`에서 구성합니다.
4. `tier`와 `quizzes[]`를 응답으로 돌려줍니다.

### 2. 퀴즈 제출

`POST /api/learning/quizzes/submit`

처리 순서는 다음과 같습니다.

1. `learning.quizzes`에서 정답 여부를 채점합니다.
2. 퀴즈 시도 기록을 저장합니다.
3. 정답이면 `ConceptMasteredEvent`를 발행합니다.

### 3. 성장 진행도 반영

`features/growth/handlers.py`는 `ConceptMasteredEvent`를 구독합니다.

처리 순서는 다음과 같습니다.

1. 이벤트로 들어온 `concept_id`를 읽습니다.
2. 해당 개념이 사용자의 현재 티어에 속하는지 확인합니다.
3. 아직 저장되지 않은 숙련 정보라면 `ConceptMastery`에 기록합니다.
4. 현재 티어의 학습 개념 집합을 기준으로 진행도를 다시 계산합니다.
5. 기준선을 넘기면 승급 가능 상태를 갱신합니다.

## 읽기 연동

`backend/features/growth/read_service.py`는 `GrowthReader`의 실제 구현입니다.

이 구현을 통해 학습 모듈은 다음 정보를 읽을 수 있습니다.

- 현재 티어
- 숙련된 학습 개념 목록
- 티어 분포

덕분에 학습 모듈이 성장 상태를 추측하거나 중복 저장할 필요가 없어졌습니다. 기존 fallback은 `learning/growth_dep.py`에 남아 있지만, 실제 앱 실행 시에는 `features/growth/__init__.py`가 구체 구현을 등록합니다.

## 진행도 계산 방식

진행도는 다음 식으로 계산합니다.

`현재 티어에서 숙련한 개념 수 / 현재 티어 전체 개념 수 * 100`

현재 VALUE 커리큘럼의 티어별 개념 수는 다음과 같습니다.

- `T1`: 8개
- `T2`: 6개
- `T3`: 5개
- `T4`: 3개
- `T5`: 1개

저장값은 정수 퍼센트이므로, 실제 승급 가능 기준은 `80 이상`이 되는 최소 숙련 개수입니다.

예시:

- `T1`: `7/8 = 87%`
- `T2`: `5/6 = 83%`
- `T3`: `4/5 = 80%`

## 프론트 계약

프론트가 쓰는 API 계약 자체는 유지됩니다.

- `GET /api/learning/me/quizzes`
- `POST /api/learning/quizzes/submit`
- `GET /api/growth/me/progress`

중요한 차이는 학습 API가 더 이상 별도 호환용 티어 퀴즈 ID를 주지 않고, `learning.curriculum`의 실제 개념 ID를 그대로 반환한다는 점입니다.

## 제거된 임시 브리지

임시 호환 레이어였던 `backend/features/learning/tier_quizzes.py`는 런타임 경로에서 제거되었습니다. 현재 앱은 `main`의 학습 커리큘럼 구조를 직접 따릅니다.
