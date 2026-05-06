# Mentors

# 멘토스 (Mentors) 🎯

> **"막막한 당신을 위한 첫 번째 투자 전략"**
>
> 2030 초보 투자자를 위한 게이미피케이션 AI 투자 학습 서비스

---

## ✨ 주요 기능

### 1. 맞춤 투자 성향 분석
사용자의 연령, 투자 경험, 위험 감수도를 기반으로 개인화된 AI 멘토를 추천합니다.

### 2. 레벨 기반 AI 리포트
사용자 숙련도(Lv.1~5)에 따라 일일 시장 분석 리포트의 깊이를 자동 조정합니다.

### 3. AI 투기장
서로 다른 투자 철학을 가진 멘토들의 토론을 통해 입체적인 판단 기준을 제시합니다.

### 4. 대화형 멘토링
RAG 기반 챗봇으로 최신 뉴스·지표를 반영한 맥락 있는 답변을 제공합니다.

---

## 🛠️ 기술 스택

### Frontend
- **React Native** — Cross-platform 모바일 앱 (iOS/Android)
- **Recharts** — 금융 차트 시각화
- **React Query, Zustand** — 서버/클라이언트 상태 관리

### Backend
- **FastAPI** — Python 비동기 API 서버
- **PostgreSQL** — 사용자·멘토·리포트 데이터 저장
- **Redis** — 캐싱 및 Celery Broker
- **Celery** — 비동기 작업 처리 (크롤링, 일일 리포트 생성)

### AI / Data
- **OpenAI API + LangChain** — 멘토 페르소나 및 RAG 파이프라인
- **Chroma** — 벡터 DB (의미 기반 검색)
- **Playwright, BeautifulSoup4** — 동적/정적 웹 크롤링
- **Feedparser, Tavily API** — RSS 및 AI 검색

---

## 📁 프로젝트 구조

```
mentos/
├── frontend/          # React Native 앱
├── backend/           # FastAPI 서버
├── ai/                # AI 파이프라인 (RAG, Crawler, 페르소나)
├── docs/              # SRS, 기획서, API 명세
└── .github/           # 이슈/PR 템플릿, Actions
```

각 폴더의 셋업 방법은 해당 폴더의 README를 참고해주세요.

- [Frontend README](./frontend/README.md)
- [Backend README](./backend/README.md)
- [AI README](./ai/README.md)

---

## 🚀 빠른 시작

### 사전 요구사항
- Node.js 20+
- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### 설치 및 실행

```bash
# 1. 레포 클론
git clone https://github.com/WorldLens/mentos.git
cd mentos

# 2. 각 파트별 셋업 (각 폴더 README 참고)
cd frontend && npm install
cd ../backend && pip install -r requirements.txt
cd ../ai && pip install -r requirements.txt
```

> 자세한 환경 변수 설정과 실행 방법은 각 파트의 README를 확인해주세요.

---

## 📋 개발 프로세스

본 프로젝트는 **Scrum** 방식으로 운영됩니다.

- **Sprint 기간**: 1주 (매주 수요일 18시 Sprint Planning)
- **Daily Scrum**: 카카오톡 비동기 채널
- **이슈 관리**: GitHub Issues + Projects

### Sprint 일정

| Sprint | 목표 | 담당 파트 |
|---|---|---|
| S#01 | 온보딩 플로우, 뉴스 탐색 탭 | FE, BE/AI |
| S#02 | 금융 지표 시각화 | FE/BE |
| S#03 | 멘토 채팅 UI MVP | FE/BE |
| S#04 | RAG 기반 채팅 고도화 | AI |
| S#05~06 | 투기장 토론 기능 | FE/BE/AI |
| S#07 | 일일 AI 리포트 자동화 | BE/AI |
| S#08 | 스크랩 및 알림 | FE/BE |
| S#09~10 | 배포 및 최종 최적화 | 전체 |

---

## 🤝 기여 가이드

### 브랜치 전략

```
main          # 배포 가능한 안정 버전
└── develop   # 통합 개발 브랜치
    ├── feature/온보딩-플로우
    ├── feature/뉴스-크롤러
    └── fix/차트-렌더링-버그
```

### 커밋 메시지 컨벤션

```
<type>: <subject>

[type 종류]
feat:     새 기능 추가
fix:      버그 수정
docs:     문서 변경
style:    코드 포맷팅
refactor: 리팩토링
test:     테스트 추가
chore:    빌드/설정 변경
```

**예시:**
```
feat: 온보딩 단계별 화면 구현
fix: 멘토 채팅 메시지 중복 송신 버그 수정
docs: API 명세에 인증 헤더 추가
```

### Pull Request 절차

1. `develop`에서 새 브랜치 생성 (`feature/기능명`)
2. 작업 후 PR 생성
3. **최소 1명의 리뷰** 후 머지
4. 머지 후 브랜치 삭제

---

## 📊 프로젝트 현황

- **개발 시작**: 2026년 (학기 프로젝트)
- **소속**: 소프트웨어공학 03분반
- **지도**: [교수님 성함]

---

## 📝 라이선스

본 프로젝트는 학기 과제로 진행되는 비상업적 학술 프로젝트입니다.

