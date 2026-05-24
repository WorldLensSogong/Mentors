# 2026-05-24 — Frontend dev 시각화 격리 + 거버넌스 도입

> Sprint #3 회고 백로그. 본 세션에서 발견한 문제, 해결한 작업, 남은 후속 액션을 기록.

## 1. 한 줄 요약

Backend 라벨 PR이 frontend 시각화를 누적해 진짜 frontend 자리를 잠식한 사고를 정리. 시각화를 `frontend/src/_dev-harness/`로 격리하고 CODEOWNERS + 자동 라벨러로 재발 방지.

---

## 2. 문제 진단

### 발견 경위

진짜 frontend 작업자(pasasdf)의 PR #21, #23, #25가 base `79c33f4` 위에서 만들어졌는데, 그 이후 backend 라벨 PR들이 frontend를 광범위하게 만지면서 `frontend/src/navigation/RootNavigator.tsx`, `frontend/package.json`에서 머지 충돌. 본질 추적해보니 시각화 누적이 원인.

### 머지 PR 감사 결과 (13개 전체)

```
PR #1   issue-template            be=0   fe=0    ✅ 인프라
PR #8   discord-alert-trigger     be=0   fe=0    ✅ 워크플로
PR #10  frontend-init             be=0   fe=35   ✅ frontend 셋업 (정상)
PR #12  core-infra-setup          be=92  fe=30   ⚠️ 인프라 PR이라 양쪽 정상
PR #16  feat/onboarding           be=12  fe=16   ❌ backend 라벨인데 frontend 16파일
PR #18  feat/growth               be=14  fe=9    ❌ backend 라벨인데 frontend 9파일
PR #20  feat/learning-module      be=21  fe=0    ✅ 백엔드만
PR #28  feat/dev-environment      be=8   fe=0    ✅ 백엔드만
PR #30  feat/learning-curriculum  be=20  fe=0    ✅ 백엔드만
PR #31  feat/learning_growth      be=21  fe=20   ❌ backend 라벨인데 frontend 20파일
PR #33  chore/dedup-dev-token     be=14  fe=0    ✅ 백엔드만
PR #36  features/debate           be=12  fe=0    ✅ 백엔드만
PR #38  feat/login                be=11  fe=0    ✅ 백엔드만
PR #40  features/debate-quality   be=4   fe=0    ✅ 백엔드만
```

→ **PR #16, #18, #31 (3개)** 가 backend 라벨로 frontend에 누적 +5764줄/45파일을 들고 옴.

### 잠식된 frontend 영역

```
PR #16   features/onboarding/screens/OnboardingScreen.tsx (475줄)
         + MentorRecommendationCard, SelectionChip, DevAccessTokenCard, userStore
         + RootNavigator 첫 대규모 수정
PR #18   features/promotion-test/screens/PromotionTestScreen.tsx (489줄)
         + GrowthProgressCard (334줄)
PR #31   features/auth/screens/DevLoginScreen.tsx (385줄)
         + LearningRecordScreen.tsx (1078줄)
         + OnboardingScreen 대규모 재작성 (+846줄)
         + RootNavigator 거의 통째 재작성
```

### 근본 원인

- **frontend에 분업 규칙이 없었음** — `backend/AGENTS.md`는 모듈 owner와 import 룰을 명문화했지만 frontend는 비어있는 공간이라 backend dev들이 자기 검증용 화면을 자유롭게 추가
- **PR 라벨이 수동** — backend라고 적었으면 frontend owner 리뷰 없이 머지
- **PR #16/#18/#31 작성자들이 frontend dev 영역을 의식 못함** — 진짜 frontend 작업자가 별도로 있다는 것을 모름

---

## 3. 해결 작업

### A. 즉시 정리 (이번 세션, 완료)

**Issue #32, PR #33** — dev 토큰 엔드포인트 중복 정리 (이미 머지)
- `/auth/dev/login` (PR #28) vs `/auth/dev-token` (PR #31) 두 개 공존
- `/dev-token`이 기능적으로 더 풍부해서 그쪽으로 흡수
- `_smoke/index.html`, `.env.example`, `SETUP.md` 갱신

**Issue #41, PR (작업 중)** — frontend dev 시각화 격리 + 거버넌스
- `frontend/src/_dev-harness/`로 14 rename (screens 4개, components 4개, navigator, navigation/{logic,types}, utils/devAccessToken)
- 테스트 2개 `tests/_dev-harness/`로 이동
- `App.tsx` 진입점 `HarnessNavigator`로 교체, `package.json` `test:navigation` 스크립트 경로 갱신
- 데이터/api 레이어(`features/{name}/{api,data,logic,types}.ts`)는 그대로 두어 진짜 frontend도 재사용

### B. 거버넌스 (이번 세션, 완료)

- **`frontend/AGENTS.md`** 신규 — backend AGENTS.md 패턴 따라 owner 분업 명문화. 새 작업자가 본 문서를 진입점으로 사용.
- **`frontend/src/_dev-harness/README.md`** 신규 — 폴더 격리 배경, 무엇이 들어있는지, 진짜 frontend 자리는 어디인지 설명
- **`.github/CODEOWNERS`** 신규 — `frontend/`는 `@pasasdf`, `_dev-harness/`는 backend owners. PR 만들 때 GitHub이 자동으로 적절한 리뷰어 지정
- **`.github/labeler.yml` + workflow** 신규 — `actions/labeler@v5`로 파일 경로 기반 자동 라벨. backend 라벨 PR에 frontend 변경 들어가도 frontend 라벨이 강제 부착

### C. 부가 정리 (이번 세션, 완료)

- Issue #26/#27 + PR #28/#30 — Windows 개발 환경 + 학습 커리큘럼 1~12단계 (이전 세션부터 이어진 작업)
- PR #31 충돌 분석 (작성자가 결국 자기 브랜치에서 main rebase 후 머지 — `da1546f`)
- PR #21/#23/#25 (frontend) 상호 관계 분석 — `#21 ⊂ #23 ⊂ #25` 누적 stack 확인

---

## 4. 검증

| 항목 | 결과 |
|---|---|
| 머지된 PR 13개 frontend/backend 변경 통계 | 표 작성 완료 (위 §2) |
| 시각화 격리 후 정적 import grep 잔여 broken 경로 | 0건 |
| backend `ruff` / `mypy --strict` / `pytest` (PR #30, #33) | 통과 (DB 통합 테스트는 컨테이너 필요) |
| `frontend/` typecheck | node_modules 미설치라 미실행 — 리뷰어 로컬 검증 필요 |

---

## 5. 남은 후속 액션

### 즉시

- [ ] PR #41 (frontend harness separation) 리뷰 + 머지
- [ ] CODEOWNERS의 GitHub 사용자명 정확성 검증 (`@wang-gw`, `@cataiers`, `@Hanhoseok`, `@pasasdf`)

### 단기 (Sprint 내)

- [ ] PR #21/#23/#25 작성자(pasasdf)와 충돌 해결 방향 협의
  - 옵션 A: PR #25만 main rebase 후 `_dev-harness/`는 안 건드리고 `src/features/{빈 폴더들}/`에 작업
  - 옵션 B: PR #21/#23/#25 다 close하고 새 PR로 다시
- [ ] PR #21/#23이 PR #25에 누적된 stack이라 정리

### 중기 (1~2주)

- [ ] 진짜 frontend가 자체 RootNavigator 만들면 `App.tsx` 환경변수 분기 도입 또는 `HarnessNavigator` 교체
- [ ] 진짜 frontend가 dev 토큰 발급/온보딩/홈 화면을 흡수하면 `_dev-harness/` 폴더 폐기 (별도 cleanup PR)
- [ ] 새 backend PR이 또 frontend를 만지는지 자동 라벨러가 잡아주는지 모니터링

### 장기

- [ ] `frontend/AGENTS.md`를 frontend 팀 실제 작업 흐름에 맞춰 업데이트 (현재는 추정)
- [ ] PR template에 CODEOWNERS/라벨러 명시 가이드 추가 검토

---

## 6. 학습 포인트

1. **공간이 비어있으면 누구든 채운다.** Backend AGENTS.md가 있어서 backend 분업은 깨끗했지만, frontend는 규칙이 없으니 backend dev들이 자기 시각화를 자유롭게 추가. **컨벤션 부재 = 사고의 시작.**

2. **수동 라벨은 결국 누락된다.** PR #31은 제목에 "프론트엔드 수정"이라고 명시했지만 라벨은 backend만. 사람이 수동으로 라벨링하면 빠지기 마련이라 **`actions/labeler`로 강제**해야 함.

3. **base가 옛 main이면 충돌이 누적된다.** PR #21/#23/#25/#31 모두 `79c33f4` base였는데 그 사이 다른 PR이 같은 파일을 만지면서 충돌. **작업 시작 전 무조건 `git pull origin main`** 컨벤션 명문화 필요.

4. **stack PR을 인지하지 못한 채 누적되면 리뷰 비용이 폭증한다.** PR #21 ⊂ #23 ⊂ #25가 stack인지 모르고 리뷰할 뻔. **PR description에 "이 PR은 #X에 의존" 명시**하거나, 머지 순서를 강제하는 자동화 필요.

---

## 7. 관련 자료

- [`frontend/AGENTS.md`](../../frontend/AGENTS.md) — frontend 분업 룰 (이번 세션에 도입)
- [`frontend/src/_dev-harness/README.md`](../../frontend/src/_dev-harness/README.md) — 폴더 격리 배경
- [`.github/CODEOWNERS`](../../.github/CODEOWNERS) — owner 정의
- [`.github/labeler.yml`](../../.github/labeler.yml) — 자동 라벨 룰
- [`backend/AGENTS.md`](../../backend/AGENTS.md) — 참고한 backend 분업 모델

---

## 8. 변경 이력

| 날짜 | 변경 | by |
|---|---|---|
| 2026-05-24 | 초안 작성 (Sprint #3 회고) | wang-gw |
