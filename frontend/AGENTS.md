# AGENTS.md (frontend)

> Mentors 프론트엔드의 owner와 AI 코딩 에이전트가 **매 작업 시작 시 read하는 운영 룰**.
> 본 문서가 진실의 원천이다. 수정 시 §8 변경 이력에 한 줄 추가.
>
> **레포를 처음 받았다면** → `frontend/README.md` 한 번 훑고 본 문서를 §1부터 읽는다.

---

## 1. 1분 요약

- **앱 형태**: Expo + React Native (iOS/Android/Web). TypeScript strict.
- **상태**: zustand (`src/store/userStore.ts`)
- **서버 통신**: axios + TanStack Query (`src/api/`)
- **라우팅**: @react-navigation/native-stack
- **현재 구조 두 트랙**:
  1. `src/_dev-harness/` — **백엔드 dev들의 검증용 임시 화면**. 백엔드 owner 자유 추가. 진짜 frontend dev는 안 건드림.
  2. `src/features/{chat, debate-arena, explore, news-detail, profile-quest, report, scrap}/` — **진짜 frontend 자리**. 프론트엔드 owner만 수정.
  3. `src/features/{auth, growth, learning, onboarding, promotion-test}/{api,data,logic,types}.ts` — 데이터/api 레이어. **양쪽이 공유**해 쓰는 라이브러리. 백엔드 동 owner가 자기 동의 endpoint wrapper를 추가/수정.

이 3가지 자리를 어기지 않으면 백엔드 dev들과 프론트엔드 dev가 같은 PR 큐에서 작업해도 머지 충돌이 거의 없다.

---

## 2. 디렉토리 = owner

```
frontend/
├── App.tsx                              # 진입점. owner: frontend (수정 시 협의 필요)
├── src/
│   ├── _dev-harness/                    # 백엔드 owner (자유 수정)
│   ├── api/                             # frontend owner (인프라)
│   │   ├── client.ts                    # axios + JWT interceptor
│   │   ├── queryClient.ts
│   │   └── endpoints/
│   ├── constants/colors.ts              # frontend owner (디자인 토큰)
│   ├── store/userStore.ts               # frontend owner (전역 상태)
│   ├── hooks/                           # frontend owner
│   ├── features/
│   │   ├── auth/api.ts                  # 백엔드 auth owner (endpoint wrapper)
│   │   ├── growth/{api,data,logic,types}.ts    # 백엔드 growth owner
│   │   ├── learning/{api,types}.ts             # 백엔드 learning owner
│   │   ├── onboarding/{api,data,logic,types}.ts # 백엔드 onboarding owner
│   │   ├── chat/                        # frontend owner (진짜 화면 자리, .gitkeep만)
│   │   ├── debate-arena/                # frontend owner
│   │   ├── explore/                     # frontend owner
│   │   ├── news-detail/                 # frontend owner
│   │   ├── profile-quest/               # frontend owner
│   │   ├── report/                      # frontend owner
│   │   └── scrap/                       # frontend owner
│   └── ...
└── tests/
    ├── _dev-harness/                    # harness 관련 테스트
    └── {feature}Logic.test.js           # data layer 순수 함수 테스트
```

다른 사람 owner 영역의 파일을 수정하려는 충동이 들면 멈추고 **해당 owner에게 PR 리뷰 요청**한다.

---

## 3. 절대 금지

```ts
// 1. 백엔드 dev가 진짜 frontend 자리에 화면 추가
// frontend/src/features/auth/screens/MyTestScreen.tsx   ← ❌ 여기 말고
// frontend/src/_dev-harness/screens/MyTestScreen.tsx     ← ✅ 여기로

// 2. _dev-harness/가 진짜 frontend 모듈을 import
// _dev-harness/screens/Foo.tsx
import { ChatScreen } from '@/features/chat/screens/ChatScreen';  // ❌
// _dev-harness는 진짜 frontend에 의존하지 않는다 (역방향 의존 X)

// 3. 진짜 frontend가 _dev-harness/를 import
// src/features/chat/screens/ChatScreen.tsx
import { DevLoginScreen } from '@/_dev-harness/screens/DevLoginScreen';  // ❌
// 진짜 frontend는 harness를 모른다

// 4. 외부 의존성 함부로 추가 금지
// 새 라이브러리 추가 시 PR description에 "왜 필요한가, 어떤 대안을 검토했나" 명시
```

---

## 4. 권장 import

```ts
// _dev-harness 안에서:
import { colors } from '@/constants/colors';                            // 디자인 토큰
import { useUserStore } from '@/store/userStore';                       // 전역 상태
import { issueDevAccessToken } from '@/features/auth/api';              // 백엔드 동 wrapper
import { saveOnboardingProfile } from '@/features/onboarding/api';
import { GrowthProgressCard } from '../components/GrowthProgressCard';  // 같은 harness 내부
import type { RootStackParamList } from '../navigation/types';

// 진짜 frontend 안에서 (아직 없음, 채워질 예정):
import { colors } from '@/constants/colors';
import { useUserStore } from '@/store/userStore';
import { apiClient } from '@/api/client';
// 본인 화면을 import할 땐 상대 경로 또는 @/features/{본인 동}/screens/...
```

---

## 5. PR 규칙

- **라벨**:
  - `frontend/` 안의 어떤 파일이든 만지면 `frontend` 라벨 자동 부착 (GitHub Actions labeler)
  - `_dev-harness/`만 만지면 `dev-harness` 라벨도 같이
  - 두 라벨이 동시에 붙으면 frontend owner와 백엔드 owner 둘 다 리뷰 요청
- **CODEOWNERS** (`.github/CODEOWNERS`):
  - `frontend/src/_dev-harness/` 외 모든 `frontend/`는 frontend owner가 리뷰 필수
- **테스트**:
  - data layer 순수 함수는 `tests/{name}Logic.test.js`로 단위 테스트
  - 화면은 수동 검증 (Expo로 빌드 후 동작 확인) — RN testing library는 아직 미도입

---

## 6. 새 작업 시작 시 체크리스트

1. `git checkout main && git pull origin main` — 최신 main 받기
2. 본인 owner 영역 확인 (위 §2 참조)
3. 본인 영역 밖을 만져야 한다면 — 새 PR로 분리하거나 owner에게 리뷰 부탁
4. 새 외부 의존성 필요하면 PR description에 사유 명시
5. PR template 따라 작성

---

## 7. 자주 묻는 질문

### Q. `_dev-harness/`를 결국 지울 건가?

아마도. 진짜 frontend가 자기 로그인/온보딩/홈 화면을 만들고 백엔드 API 검증을 흡수하면 `_dev-harness/`는 의미가 사라진다. 그때 한 번에 폴더 삭제 PR로 정리.

### Q. 백엔드 dev가 진짜 frontend 자리(`src/features/chat/` 등)에 시각화 화면 추가해도 되나?

**❌ 안 됨.** 진짜 frontend dev의 작업 자리를 침범한다. `_dev-harness/`에 추가한다.

### Q. 진짜 frontend dev가 `_dev-harness/`의 화면을 재사용/리팩토링해도 되나?

**⭕ 가능.** 단 백엔드 owner들의 검증이 깨지지 않게 PR로 알리고 머지.

### Q. 데이터 레이어(`features/{name}/api.ts` 등)는 누가 owner인가?

**해당 백엔드 동 owner.** 그 동의 endpoint wrapper를 정의하는 책임. 진짜 frontend는 이걸 import해서 화면에 그림.

---

## 8. 변경 이력

| 날짜 | 변경 | by |
|---|---|---|
| 2026-05-24 | 초안 작성 + `_dev-harness/` 분리 컨벤션 도입 | wang-gw |
