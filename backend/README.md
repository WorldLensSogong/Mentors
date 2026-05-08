# Mentors Backend Scaffold

멘토스 프로젝트의 1주차 백엔드 기초 뼈대입니다.

목표는 완성형 서비스를 만드는 것이 아니라, 팀원들이 같은 DB 구조와 API 기준으로 바로 작업을 시작할 수 있게 공통 기반을 제공하는 것입니다.

## 개요

이 저장소에는 아래가 포함되어 있습니다.

- `backend/` 아래 FastAPI 모놀리식 서버 구조
- SQLAlchemy 모델
- Alembic 초기 migration
- seed 데이터 입력 스크립트
- Swagger로 확인 가능한 MVP API

현재 제공 API:

- `GET /health`
- `GET /api/v1/mentors`
- `POST /api/v1/onboarding`
- `GET /api/v1/news`
- `GET /api/v1/news/{news_id}`
- `POST /api/v1/chat/sessions`
- `POST /api/v1/chat/messages`
- `POST /api/v1/reports/preview`
- `GET /api/v1/curriculum/modules`

## 권장 개발 환경

### Python

- 권장: `Windows native Python 3.11`
- 대안: `Conda Python 3.11`
- 비권장: `MSYS / MinGW Python`

주의:

- `MSYS / MinGW Python`으로 가상환경을 만들면 `bin/` 구조가 생기고 일부 패키지 설치가 꼬일 수 있습니다.
- 가능하면 `python.org`에서 설치한 Windows Python을 사용하세요.

### Database

- `PostgreSQL 17` 또는 `PostgreSQL 18`
- 로컬 개발 기준 포트: `5432`
- DB 이름 권장: `mentors`

## 폴더 구조

```text
backend/
├── alembic/
│   ├── versions/
│   └── env.py
├── app/
│   ├── api/
│   │   ├── routes/
│   │   ├── deps.py
│   │   └── router.py
│   ├── core/
│   ├── models/
│   ├── repositories/
│   ├── schemas/
│   ├── seed/
│   ├── services/
│   └── main.py
├── .env.example
├── alembic.ini
├── init_db.py
└── requirements.txt
```

## 0. PostgreSQL 설치

아직 PostgreSQL을 설치하지 않았다면 먼저 설치합니다.

### 설치할 때 체크할 것

1. 버전은 `17` 또는 `18` 사용
2. `pgAdmin` 같이 설치해도 좋음
3. `postgres` 계정 비밀번호를 반드시 기억할 것
4. 포트는 기본값 `5432` 사용 권장
5. 설치가 끝나면 Windows 서비스에 PostgreSQL이 등록됨

추천:

- 팀 협업 중에는 비밀번호에 특수문자보다 영문/숫자를 쓰는 편이 `.env` 작성이 덜 헷갈립니다.

## 1. PostgreSQL 서버 실행

PostgreSQL 설치만 했다고 끝이 아니라, 서비스가 실제로 켜져 있어야 합니다.

### 방법 A. Windows 서비스에서 실행

1. `Win + R`
2. `services.msc` 입력
3. `PostgreSQL` 서비스 찾기
4. 상태가 `실행 중`인지 확인
5. 꺼져 있으면 `시작` 클릭

### 방법 B. PowerShell에서 확인

```powershell
Get-Service | Where-Object { $_.Name -like '*postgres*' -or $_.DisplayName -like '*PostgreSQL*' }
```

### 포트가 열렸는지 확인

```powershell
Test-NetConnection -ComputerName 127.0.0.1 -Port 5432
```

정상이라면 아래처럼 나와야 합니다.

```text
TcpTestSucceeded : True
```

## 2. 데이터베이스 생성

둘 중 하나를 선택하면 됩니다.

### 방법 A. `postgres` 계정 그대로 사용

`pgAdmin` 또는 `psql`로 `mentors` 데이터베이스를 생성합니다.

```sql
CREATE DATABASE mentors;
```

### 방법 B. 프로젝트 전용 계정 생성

더 깔끔한 방법입니다.

```sql
CREATE USER mentors_app WITH PASSWORD 'your_password';
CREATE DATABASE mentors OWNER mentors_app;
GRANT ALL PRIVILEGES ON DATABASE mentors TO mentors_app;
```

## 3. 환경 변수 파일 준비

`backend/.env.example`을 복사해서 `backend/.env`를 만듭니다.

```powershell
cd backend
Copy-Item .env.example .env
```

### 예시 1. `postgres` 계정 사용

```env
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@127.0.0.1:5432/mentors
DEBUG=true
APP_NAME=Mentors API
API_V1_PREFIX=/api/v1
```

### 예시 2. 프로젝트 전용 계정 사용

```env
DATABASE_URL=postgresql+psycopg://mentors_app:YOUR_PASSWORD@127.0.0.1:5432/mentors
DEBUG=true
APP_NAME=Mentors API
API_V1_PREFIX=/api/v1
```

중요:

- 실제 비밀번호는 GitHub에 올리지 않습니다.
- 각자 로컬 `.env`에만 저장합니다.

## 4. 가상환경 생성

Windows native Python 기준:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

가상환경이 정상이라면 아래 경로가 보여야 합니다.

```powershell
python -c "import sys; print(sys.executable)"
```

예시:

```text
C:\Users\...\backend\.venv\Scripts\python.exe
```

## 5. 패키지 설치

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

PostgreSQL 드라이버는 `psycopg[binary]` 기준입니다.

## 6. 테이블 생성

새로 시작하는 DB라면 아래 순서로 실행합니다.

```powershell
alembic upgrade head
python init_db.py
```

설명:

- `alembic upgrade head`: 테이블 생성
- `python init_db.py`: seed 데이터 입력

## 7. FastAPI 서버 실행

```powershell
uvicorn app.main:app --reload
```

이 명령은 서버를 계속 켜두는 명령이라, 터미널이 바로 끝나지 않는 것이 정상입니다.

확인 주소:

- Swagger: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

서버 종료:

```powershell
Ctrl + C
```

## 처음 세팅할 때 전체 순서 요약

처음부터 한 번에 따라가려면 아래 순서대로 하면 됩니다.

```powershell
cd "C:\Users\mrhan\Documents\New project\backend"

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

Copy-Item .env.example .env
# 여기서 .env 안의 비밀번호를 실제 PostgreSQL 비밀번호로 수정

alembic upgrade head
python init_db.py
uvicorn app.main:app --reload
```

## 기존 로컬 DB가 이미 있는 경우

예전에 `create_all()` 방식으로 이미 테이블을 만든 상태라면, 현재 DB를 첫 migration 기준으로만 맞춰주면 됩니다.

```powershell
alembic stamp head
python init_db.py
```

이후부터는 스키마 변경을 Alembic migration으로 관리합니다.

## 자주 쓰는 명령어

### PostgreSQL 포트 확인

```powershell
Test-NetConnection -ComputerName 127.0.0.1 -Port 5432
```

### 서버 실행

```powershell
uvicorn app.main:app --reload
```

### migration 현재 상태 확인

```powershell
alembic current
alembic history
```

### 모델을 수정한 뒤 새 migration 추가

```powershell
alembic revision --autogenerate -m "describe your change"
alembic upgrade head
```

### seed 다시 넣기

```powershell
python init_db.py
```

## DB 변경 규칙

앞으로 DB 스키마를 수정할 때는 아래 순서를 따릅니다.

1. `app/models` 수정
2. migration 생성
3. migration 파일 검토
4. `alembic upgrade head`
5. 필요하면 `python init_db.py`

중요:

- 테이블/컬럼 추가는 비교적 안전합니다.
- 컬럼 삭제, 타입 변경, 이름 변경은 migration 내용을 꼭 직접 확인해야 합니다.
- `init_db.py`는 seed 전용입니다. 스키마 생성 도구가 아닙니다.

## 팀원별 연결 포인트

### 박설아 - 온보딩

- 사용 API: `POST /api/v1/onboarding`
- 관련 테이블:
  - `users`
  - `user_profiles`
  - `onboarding_survey_answers`
  - `user_interest_topics`

### 정준우 - Content & News

- 사용 API:
  - `GET /api/v1/news`
  - `GET /api/v1/news/{news_id}`
- 관련 테이블:
  - `news_sources`
  - `news_articles`
  - `article_topics`

### 손은재 - AI 멘토

- 사용 API:
  - `GET /api/v1/mentors`
  - `POST /api/v1/chat/sessions`
  - `POST /api/v1/chat/messages`
- 관련 테이블:
  - `mentors`
  - `chat_sessions`
  - `chat_messages`

### 왕규원 - 커리큘럼

- 사용 API:
  - `GET /api/v1/curriculum/modules`
- 관련 테이블:
  - `learning_modules`
  - `level_definitions`
  - `investment_strategies`

### 김란주 - 화면 수정 / 기획 연결

- 주요 확인 주소:
  - Swagger: `http://127.0.0.1:8000/docs`
- 우선 볼 API:
  - `GET /api/v1/mentors`
  - `GET /api/v1/news`
  - `POST /api/v1/onboarding`

## 현재 의도적으로 단순화한 부분

- 인증은 아직 완성형 JWT가 아닙니다.
- `POST /api/v1/chat/messages`는 현재 mock 멘토 응답을 반환합니다.
- `POST /api/v1/reports/preview`는 최근 뉴스 기반 preview만 생성합니다.
- 뉴스 수집 파이프라인과 실제 AI 호출은 아직 완전 연결 상태가 아닙니다.

## GitHub 공유 규칙

올려도 되는 것:

- 소스코드
- `requirements.txt`
- `README.md`
- `.env.example`
- Alembic migration

올리면 안 되는 것:

- `.env`
- 실제 DB 비밀번호
- `.venv`
- 개인 로컬 설정 파일

## 트러블슈팅

### `ModuleNotFoundError: No module named 'sqlalchemy'`

가상환경이 활성화되지 않았거나 패키지 설치가 안 된 상태입니다.

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### `password authentication failed for user "postgres"`

`.env`의 비밀번호가 실제 PostgreSQL 비밀번호와 다릅니다.

### `connection to server at "127.0.0.1", port 5432 failed`

PostgreSQL 서비스가 꺼져 있거나 포트가 다릅니다.

### `bin/` 폴더가 생김

MSYS / MinGW Python으로 가상환경을 만든 것입니다.
Windows native Python으로 다시 만드는 것을 권장합니다.

## 다음 단계 추천

1. 현재 상태를 GitHub에 push
2. 팀원들에게 Swagger 주소와 실행 순서 공유
3. 이후 스키마 변경부터는 Alembic migration 기준으로 관리
4. 뉴스 수집, AI 응답, 온보딩 추천 로직을 각 담당자가 이어서 확장
