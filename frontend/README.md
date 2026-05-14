# Mentors — Frontend

React Native (Expo) + TypeScript 기반 모바일 앱.

---

## 🛠 기술 스택

- **Expo SDK 54** — 빌드/실행 환경
- **React Native** — UI 프레임워크
- **TypeScript** — 언어
- **React Navigation** — 화면 라우팅 (native-stack, bottom-tabs)
- **TanStack Query (React Query)** — 서버 상태 관리
- **Zustand** — 클라이언트 상태 관리
- **axios** — HTTP 클라이언트 (JWT 자동 부착)
- **Victory Native (예정)** — 차트 라이브러리. 페이지 작업 시작 시 추가 설치 필요.

---

## 🚀 셋업

### 사전 요구사항

- Node.js 20+
- iOS 시뮬레이터(Mac만) 또는 Android 에뮬레이터, 또는 실기기 + Expo Go 앱

### 설치 및 실행

```bash
cd frontend
npm install            # 의존성 설치 (clone 직후 1회)
cp .env.example .env   # 환경 변수 파일 복사

npm run start          # Metro bundler 실행 (= npm run dev)
# 또는 플랫폼 직접 실행
npm run ios            # iOS 시뮬레이터 (Mac)
npm run android        # Android 에뮬레이터
npm run web            # 웹 브라우저
```

---

## 🌍 환경 변수

`.env` 파일에서 관리. `.env`는 git에 커밋하지 않음 (`.env.example`만 커밋).

| Key                        | 설명                   | 예시                    |
| -------------------------- | ---------------------- | ----------------------- |
| `EXPO_PUBLIC_API_BASE_URL` | Backend API 베이스 URL | `http://localhost:8000` |

> Expo는 `EXPO_PUBLIC_` 접두사 변수만 클라이언트 코드에서 접근 가능.

---

## 📁 폴더 구조

```
frontend/
├── App.tsx                       # 엔트리 (Provider 계층)
├── src/
│   ├── api/
│   │   ├── client.ts             # axios 인스턴스 + JWT 인터셉터
│   │   ├── queryClient.ts        # React Query Client
│   │   └── endpoints/            # 도메인별 API 함수
│   ├── components/               # 공통 UI 컴포넌트 (MentorCard, XPGauge, ...)
│   ├── constants/                # colors, sizes 등 상수
│   ├── features/                 # UI 모듈 (도메인별 작업 단위)
│   │   ├── onboarding/
│   │   ├── chat/
│   │   ├── report/
│   │   ├── debate-arena/
│   │   ├── explore/
│   │   ├── news-detail/
│   │   ├── scrap/
│   │   ├── profile-quest/
│   │   └── promotion-test/
│   ├── hooks/                    # 공통 훅
│   ├── navigation/               # React Navigation 설정
│   ├── store/                    # Zustand 스토어 (UserStore 등)
│   ├── types/                    # 공통 타입
│   └── utils/                    # 공통 유틸 함수
├── assets/
├── .env.example
├── .prettierrc
├── eslint.config.js
└── tsconfig.json
```

### feature 모듈 작업 시 권장 구조

작업할 모듈 폴더(예: `features/chat/`)에 다음과 같이 추가:

```
features/chat/
├── components/   # 모듈 내부 전용 컴포넌트
├── hooks/        # 모듈 전용 훅 (useChatRoom 등)
├── screens/      # Navigation에 등록되는 화면
└── api.ts        # (선택) 모듈 API 호출 — 또는 src/api/endpoints/ 에 통합
```

---

## 🧩 사용 패턴

### API 호출 (axios + React Query)

```ts
// src/api/endpoints/chat.ts
import { apiClient } from '../client';

export const getChatRooms = () => apiClient.get('/chat/rooms');
```

```tsx
// 화면에서 사용
import { useQuery } from '@tanstack/react-query';
import { getChatRooms } from '@/api/endpoints/chat';

const { data, isLoading } = useQuery({
  queryKey: ['chat-rooms'],
  queryFn: () => getChatRooms().then((r) => r.data),
});
```

### 클라이언트 상태 (Zustand)

```ts
// src/store/userStore.ts (이미 작성됨 — JWT 토큰 관리)
import { useUserStore } from '@/store/userStore';

const token = useUserStore((s) => s.accessToken);
useUserStore.getState().setAccessToken('...');
```

새 store는 같은 패턴으로 `src/store/` 안에 추가.

### JWT 인증

`src/api/client.ts`가 모든 요청에 자동으로 `Authorization: Bearer <token>` 헤더를 부착함. 401 응답이 오면 자동으로 토큰 클리어.

로그인 후:

```ts
useUserStore.getState().setAccessToken(response.data.access_token);
```

---

## ✅ 코드 품질

```bash
npm run lint          # ESLint
npm run typecheck     # TypeScript 타입 체크
npm run format:check  # Prettier 포맷 확인
npm run format        # Prettier 자동 수정
```

PR 올리기 전 위 3개 (`lint`, `typecheck`, `format:check`) 통과 확인 권장.

---

## 📝 컨벤션

### 네이밍

- **컴포넌트 파일**: PascalCase (`MentorCard.tsx`)
- **훅 / 유틸 파일**: camelCase (`useChatRoom.ts`, `formatDate.ts`)
- **상수 / 타입**: 파일명은 camelCase, 내부 값은 UPPER_SNAKE_CASE

### Import 순서

1. React / React Native
2. 외부 라이브러리
3. 프로젝트 내부 모듈 (`@/` 또는 상대경로)
4. 스타일 / 상수

### Git

- 브랜치: `<type>/#이슈번호-설명` (루트 README 참고)
- 커밋: `<type>: <subject> (#이슈번호)`
- PR base: `main`

---

## 🎨 디자인 reference

UI 모듈 구성 (디자인 단계 기준):

| 모듈            | 폴더                      | 비고           |
| --------------- | ------------------------- | -------------- |
| Onboarding      | `features/onboarding`     | 투자 성향 분석 |
| Chat            | `features/chat`           | AI 멘토 채팅   |
| Report          | `features/report`         | 일일 AI 리포트 |
| Debate Arena    | `features/debate-arena`   | 멘토 토론      |
| Explore         | `features/explore`        | 뉴스 탐색      |
| News Detail     | `features/news-detail`    | 뉴스 상세      |
| Scrap           | `features/scrap`          | 스크랩         |
| Profile / Quest | `features/profile-quest`  | 프로필·퀘스트  |
| Promotion Test  | `features/promotion-test` | 승급 테스트    |

공통 컴포넌트 (5+):

- `MentorCard`, `XPGauge`, `QuizComponent`, `ChartComponent`, ...

Zustand 스토어 (5):

- `userStore` (작성 완료, JWT 관리)
- `chatStore`, `reportStore`, `exploreStore`, `scrapStore` (작업 시 추가)
