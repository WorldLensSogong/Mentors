# AGENTS.md (repo root)

> Mentors 레포 루트에서 AI 코딩 에이전트(Codex / Claude Code 등)가 **가장 먼저 읽는 라우팅 문서**.
> 진실의 원천은 각 하위 디렉토리의 `AGENTS.md`. 본 파일은 "어디로 가야 하나"만 알려준다.

---

## 1. 이 레포는 모노레포다

```
Mentors/
├── backend/      # FastAPI + PostgreSQL + Redis + Chroma + LLM (Python 3.12+, uv)
├── frontend/     # Expo + React Native + TypeScript (iOS/Android/Web)
├── docs/         # 공용 문서
├── tests/        # env.sample (테스트 환경 변수 샘플) — 실제 테스트 코드는 backend/tests/, frontend/tests/ 에
└── .github/      # CI / labeler / CODEOWNERS
```

루트에는 `package.json`도 `pyproject.toml`도 없다. **루트에서 `npm run` / `pytest` 를 바로 돌릴 수 없다.** 반드시 작업할 하위 디렉토리로 먼저 들어간다.

---

## 2. 작업 시작 시 분기

| 작업 영역 | 들어갈 디렉토리 | 룰 문서 |
|---|---|---|
| 화면, 컴포넌트, 네비게이션, RN 관련 | `frontend/` | [frontend/AGENTS.md](frontend/AGENTS.md) |
| API, DB, LLM, 백엔드 비즈니스 로직 | `backend/` | [backend/AGENTS.md](backend/AGENTS.md) + [backend/SETUP.md](backend/SETUP.md) |
| 양쪽 다 만지는 변경 | 두 디렉토리 분리 PR 권장 | 두 AGENTS.md 모두 |

**모르겠으면 작업이 닿는 파일의 상위 디렉토리부터 본다.** 거기에 `AGENTS.md`가 있으면 그게 룰이다.

---

## 3. 실행/테스트 명령 — 어디서 무엇을

### Frontend (Expo RN)

```bash
cd frontend
npm install        # 첫 실행 시
npm run dev        # = expo start (w로 web, i로 iOS, a로 Android)
```

자세한 scripts는 `frontend/package.json`의 `scripts` 항목 참조.

### Backend (FastAPI + uv)

```bash
cd backend
# 첫 셋업 절차는 backend/SETUP.md 참조 (uv, DB, env)
# 개발 서버 / 테스트 명령도 SETUP.md 기준
```

루트에서 바로 돌리지 않는다. backend의 entry는 `backend/main.py` (서버) / `backend/dev_server.py` (개발) / `backend/alembic.ini` (마이그레이션).

---

## 4. AI 에이전트가 자주 헷갈리는 것

- **"이 레포 뭐로 돌려?"** → 모노레포다. 루트에서 단일 명령으로 안 돈다. §2 표대로 하위 디렉토리에 들어가서 그쪽 `AGENTS.md`를 읽는다.
- **`frontend/src/features/{name}/api.ts` 같은 파일은 frontend dev가 못 고친다.** owner가 백엔드 동 owner임. [frontend/AGENTS.md §2.2](frontend/AGENTS.md) 의 파일 단위 ownership 표를 본다.
- **`frontend/src/_dev-harness/`는 진짜 frontend가 아님.** 백엔드 owner들의 검증용 임시 화면 자리. 진짜 frontend ↔ harness는 양방향 import 금지.
- **백엔드는 "동(building)" 단위로 잘려 있음** — `onboarding`, `learning`, `growth`, `debate`, `content`, `daily_report`. 본인 동 외에는 `core/` 추상화 통해서만 접근.

---

## 5. PR / CODEOWNERS

- 라벨링은 GitHub Actions labeler가 경로 기반으로 자동 부착.
- `.github/CODEOWNERS`에 정의된 리뷰어가 자동 지정됨.
- 두 디렉토리(`frontend/` + `backend/`) 모두 만지는 PR이면 양쪽 owner 리뷰가 붙는다 — 가능하면 분리 PR.

---

## 6. 변경 이력

| 날짜 | 변경 | by |
|---|---|---|
| 2026-05-29 | 초안 작성 — 모노레포 라우팅 명시 (Codex가 루트에서 실행 명령 못 정하던 문제 대응) | — |
