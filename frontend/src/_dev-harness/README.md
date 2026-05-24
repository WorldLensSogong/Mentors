# `_dev-harness/` — 백엔드 검증용 임시 화면

> 백엔드 동(棟) 개발자들이 본인 기능을 RN 화면에서 빠르게 검증하기 위해 만든 **임시 시각화 모음**.
> **진짜 프론트엔드 코드가 아니다.** 진짜 frontend는 `src/features/{chat, debate-arena, explore, news-detail, profile-quest, report, scrap}/` 등 비어있는 자리에 들어온다.

## 무엇이 들어있나

- `HarnessNavigator.tsx` — harness 전용 navigator. `DevLogin → Onboarding → LearningRecord → PromotionTest` 단일 흐름.
- `screens/` — 4개 화면 (백엔드 PR마다 추가됨)
- `components/` — 화면 보조 UI
- `navigation/` — harness navigator가 쓰는 routing 타입/로직
- `utils/` — harness 전용 유틸 (dev 토큰 마스킹 등)

## 진짜 frontend는 어디

```
frontend/src/
├── _dev-harness/     ← 여기 (백엔드 검증용)
└── features/
    ├── chat/          ← 비어있음 (.gitkeep만)
    ├── debate-arena/  ← 진짜 frontend가 채울 자리
    ├── explore/
    ├── news-detail/
    ├── profile-quest/
    ├── report/
    └── scrap/
```

진짜 frontend 작업자는 `src/features/{chat, debate-arena, …}/` 안에 화면/컴포넌트 추가. `_dev-harness/`는 **건드리지 않는다.**

## App.tsx에서 어떻게 켜는가

지금은 기본적으로 `HarnessNavigator`가 렌더링됨 (`App.tsx`에서 직접 import). 진짜 frontend가 자체 RootNavigator를 만들어 합치는 시점에 `App.tsx`를 갈아주거나 환경변수 분기를 넣으면 됨.

## 백엔드 dev가 새 검증 화면을 추가하려면

1. `_dev-harness/screens/`에 RN 화면 추가
2. 필요하면 `_dev-harness/components/`에 보조 컴포넌트 추가
3. `HarnessNavigator.tsx`에 Stack.Screen 등록
4. 데이터/api 레이어가 필요하면 **`src/features/{본인 동}/api.ts`나 `data.ts`에 추가** (이 부분은 진짜 frontend도 재사용 가능하니까 `_dev-harness/` 밖에 둠)
5. PR 라벨: `backend` + `dev-harness` (두 개)

## 왜 이 폴더가 만들어졌나

PR #16, #18, #31이 backend 라벨로 머지되면서 `src/features/{auth, growth, onboarding, promotion-test}/screens/`에 시각화 화면을 누적해 진짜 frontend 자리(`src/features/`)와 섞였음. 진짜 frontend 작업자가 어디부터 진짜 코드인지 식별 어렵고 navigator 충돌 발생 → 본 PR(`chore(frontend): dev 시각화를 _dev-harness/로 격리`)에서 분리.

## 한 줄 요약

> **`_dev-harness/` = 백엔드 dev들의 RN 놀이터.** 진짜 frontend는 `src/features/{빈 폴더들}/`에 들어온다.
