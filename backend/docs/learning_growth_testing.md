# 학습-성장 통합 테스트 가이드

이 문서는 로컬 환경에서 학습-성장 통합 흐름을 검증하는 방법을 정리합니다.

## 서비스 실행

### 백엔드

```powershell
cd C:\Users\mrhan\Documents\Mentors\backend
docker compose up -d
.\.venv\Scripts\python.exe .\dev_server.py
```

헬스 체크:

```powershell
curl http://127.0.0.1:8000/health
```

### 프론트엔드

```powershell
cd C:\Users\mrhan\Documents\Mentors\frontend
cmd /c npm run web
```

접속 주소: `http://127.0.0.1:8081`

### 한 번에 실행

```powershell
powershell.exe -ExecutionPolicy Bypass -File C:\Users\mrhan\Documents\Mentors\backend\_smoke\start_learning_growth_local.ps1
```

이 스크립트는 다음을 처리합니다.

- Docker 의존 서비스 실행
- 필요 시 `dev_server.py`로 백엔드 실행
- 필요 시 프론트 웹 서버 실행
- 백엔드와 프론트 주소가 모두 응답할 때까지 대기

코드를 수정한 뒤 완전히 다시 올리고 싶다면 다음처럼 실행합니다.

```powershell
powershell.exe -ExecutionPolicy Bypass -File C:\Users\mrhan\Documents\Mentors\backend\_smoke\start_learning_growth_local.ps1 -Restart
```

## 프론트 수동 테스트 흐름

권장 순서는 다음과 같습니다.

1. `http://127.0.0.1:8081`에 접속합니다.
2. 온보딩 전 임시 로그인 화면에서 `새 테스트 토큰 발급` 또는 토큰 직접 입력을 사용합니다.
3. 토큰 적용 후 온보딩을 완료합니다.
4. 메인 `나의 학습 기록` 화면으로 진입합니다.
5. `퀴즈` 세그먼트를 열고 현재 티어 문제를 풉니다.
6. 정답 제출 뒤 같은 화면에서 성장 진행도가 갱신되는지 확인합니다.
7. 승급 가능 상태가 되면 승급시험으로 이동합니다.
8. 승급시험 통과 후 티어와 해금 기능이 갱신되는지 확인합니다.

## T1 퀴즈 정답표

현재 T1 학습 개념은 `1~8`이며, 승급 가능 상태는 처음 `7개`를 숙련하면 열립니다. (`7/8 = 87%`)

- `1` -> `1`
- `2` -> `1`
- `3` -> `1`
- `4` -> `1`
- `5` -> `1`
- `6` -> `2`
- `7` -> `1`
- `8` -> `0`

정답을 충분히 맞히면 성장 진행도가 승급 가능 기준에 도달해야 합니다.

## T1 승급시험 정답표

- `t1-q1` -> `A`
- `t1-q2` -> `B`
- `t1-q3` -> `C`
- `t1-q4` -> `A`
- `t1-q5` -> `D`

## Postman 테스트 흐름

다음 파일을 import 합니다.

- `backend/postman/learning-growth-local.postman_collection.json`
- `backend/postman/learning-growth-local.postman_environment.json`

권장 실행 순서는 다음과 같습니다.

1. `1. Issue Fresh Dev Token`
2. `2. Get Current User`
3. `3. Growth Progress (Initial)`
4. `4. Learning Quizzes (Current Tier)`
5. 4번에서 받은 개념 ID로 퀴즈를 하나 이상 제출
6. 성장 진행도 다시 조회
7. 승급 가능 상태가 되면 승급시험 제출
8. 승급 후 성장 진행도 다시 조회

## 기대 결과

- 초기 상태에서는 현재 티어와 낮은 진행도 또는 `0%`가 내려옵니다.
- 퀴즈 목록의 개념 ID는 별도 성장 카탈로그가 아니라 학습 커리큘럼 ID를 사용합니다.
- 퀴즈 정답 제출 시 `ConceptMasteredEvent`가 발행되고, 잠시 뒤 성장 진행도가 올라갑니다.
- 승급시험 통과 후 `current_tier`가 다음 티어로 바뀌고 해금 기능도 함께 갱신됩니다.

## 자주 생기는 이슈

### 퀴즈를 맞혔는데 성장 진행도가 바로 안 바뀌는 경우

성장 업데이트는 이벤트 기반으로 반영됩니다. 퀴즈 제출 직후와 진행도 재조회 사이에 짧은 지연이 생길 수 있습니다.

### `/api/learning/me/quizzes`에서 예상과 다른 ID가 보이는 경우

현재 이 엔드포인트는 `learning.curriculum`의 실제 개념 ID를 반환합니다. `1~23` 범위의 ID가 보이는 것이 정상입니다.

### 개발용 토큰이 발급되지 않는 경우

다음을 확인합니다.

- 백엔드가 실행 중인지
- `ENV=dev`인지
- 프론트가 올바른 백엔드 주소를 바라보는지
