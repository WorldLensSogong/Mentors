# 학습 동(Learning) 데이터 흐름도

> 본 문서는 `features/learning/` 모듈의 실제 코드를 기준으로 한 데이터 흐름 시각화이다.
> 기준 시점: 2026-05-20 / 로컬 워크스페이스 (`coreinfra/`) 기준.
> Mermaid 다이어그램은 GitHub·VS Code Preview·대부분 마크다운 뷰어에서 자동 렌더링된다.

---

## 1. 한눈에 — 학습 동의 우주

학습 동은 **자체 비즈니스 로직 (3 파일) + core/ 의존성 (8 모듈) + 외부 인프라 (4종)** 의 조합이다.

```mermaid
graph LR
    subgraph CLIENT[" 클라이언트 "]
        APP[모바일 앱 / Smoke HTML]
    end

    subgraph LEARNING[" features/learning/ "]
        ROUTER[router.py<br/>7 endpoints]
        SERVICE[service.py<br/>SSE 제너레이터]
        CURRIC[curriculum.py<br/>퀴즈 카탈로그]
        PERSONA[personas/<br/>4 멘토 프롬프트]
        SCHEMAS[schemas.py<br/>Pydantic DTO]
        MODELS[models.py<br/>ChatSession/Message]
    end

    subgraph CORE[" core/ 의존성 "]
        AUTH[auth<br/>JWT + User]
        DB[db<br/>SessionLocal]
        LLM_M[llm<br/>Gemini client]
        AIP[ai_pipeline<br/>guardrail·rag·tier·hallucination·critic]
        VS[vector_store<br/>Chroma 래퍼]
        EB[event_bus<br/>pub/sub]
        UC[user_context<br/>티어·취향]
        CON[contracts<br/>이벤트 타입]
    end

    subgraph INFRA[" 외부 인프라 "]
        PG[(Postgres)]
        CH[(Chroma)]
        RD[(Redis)]
        GEM[Gemini API<br/>chat+embed]
    end

    APP -->|HTTPS + JWT| ROUTER
    ROUTER --> AUTH
    ROUTER --> SERVICE
    ROUTER --> CURRIC
    ROUTER --> EB
    SERVICE --> PERSONA
    SERVICE --> AIP
    SERVICE --> LLM_M
    SERVICE --> UC
    SERVICE --> DB
    AIP --> VS
    AIP --> LLM_M
    VS --> LLM_M
    LLM_M --> GEM
    VS --> CH
    DB --> PG
    EB --> RD
    AUTH --> PG
```

---

## 2. 데이터 모델

```mermaid
erDiagram
    users ||--o{ learning_chat_sessions : "1:N (논리적 FK)"
    learning_chat_sessions ||--o{ learning_chat_messages : "1:N (cascade)"

    users {
        bigint id PK
        string email
        string nickname
        string status
    }

    learning_chat_sessions {
        bigint id PK
        bigint user_id FK
        bigint mentor_id "1~4 (가치/성장/배당/모멘텀)"
        string title "첫 메시지 50자 자동 생성"
        timestamp created_at
        timestamp updated_at
    }

    learning_chat_messages {
        bigint id PK
        bigint session_id FK
        string role "user / assistant / system"
        text content
        timestamp created_at
    }
```

> **핵심 원칙** — `users.id`는 학습 동에서 **논리적 참조만**. 다른 동(growth, debate 등)과 직접 JOIN 금지. 동 간 통신은 `core.event_bus` 통해서만.

---

## 3. 7 엔드포인트 한눈에

| # | 메서드·경로 | 무엇 | 핵심 흐름 |
|---|---|---|---|
| 1 | `GET /api/learning/sessions` | 내 세션 목록 | DB 단순 조회 |
| 2 | `POST /api/learning/sessions` | 새 세션 생성 | DB INSERT |
| 3 | `GET /api/learning/sessions/{id}/messages` | 메시지 이력 | 소유 확인 + DB 조회 |
| 4 | `POST /api/learning/sessions/{id}/messages` | 메시지 저장(전용) | DB INSERT + `MessageSentEvent` |
| 5 | **`POST /api/learning/chat/stream`** | **실시간 멘토링 (SSE)** | **5단계 AI 파이프라인 → §4** |
| 6 | `GET /api/learning/quizzes/{concept_id}` | 퀴즈 조회 | 메모리 카탈로그 + 정답 숨김 |
| 7 | `POST /api/learning/quizzes/submit` | 퀴즈 채점 | 채점 + 정답시 `ConceptMasteredEvent` → §5 |

1~3·6은 단순 CRUD/조회라 별도 그림 없이 충분하다. 4·5·7만 다이어그램이 필요하다.

---

## 4. 핵심 흐름 A — 채팅 스트림 (`POST /chat/stream`)

가장 복잡한 경로. **입력 가드레일 → 사용자 메시지 저장 → SSE 제너레이터 시작 → 별도 DB 세션 진입 → RAG → 티어 오버레이 → Gemini 스트리밍 → 3중 후처리 검증 → 어시스턴트 답변 저장**.

```mermaid
sequenceDiagram
    autonumber
    actor U as 사용자
    participant R as router.chat_stream
    participant G as guardrail
    participant DB1 as Postgres<br/>(요청 세션)
    participant EB as event_bus
    participant S as service.stream_<br/>assistant_response
    participant UC as user_context
    participant DB2 as Postgres<br/>(SessionLocal 격리)
    participant RAG as rag.retrieve
    participant V as Chroma
    participant LE as llm.embed
    participant TO as tier_overlay
    participant LS as llm.chat_stream
    participant GEM as Gemini API
    participant H as hallucination
    participant C as critic
    participant GO as guardrail.<br/>check_output

    U->>R: POST /chat/stream<br/>{session_id, content}
    R->>G: check_input(content)
    G-->>R: ok / blocked

    alt 가드레일 차단
        R-->>U: 400 BadRequest
    else 통과
        R->>DB1: add_message(role="user")
        DB1-->>R: persisted
        R->>EB: publish(MessageSentEvent)
        R->>DB1: commit
        R->>S: stream_assistant_response(generator)
        R-->>U: EventSourceResponse 시작 (200 OK)
    end

    Note over S,DB2: 여기서부터는 SSE 제너레이터 컨텍스트<br/>요청 컨텍스트의 DB1은 이미 닫힘
    S->>UC: get_for_mentor_chat(user_id)<br/>→ 티어 T1~T5 + 취향
    UC-->>S: UserContext

    S->>DB2: async with SessionLocal() as db
    DB2-->>S: 새 격리 세션
    S->>DB2: get_session + list_messages
    DB2-->>S: 세션 + 메시지 이력

    Note over S: 시스템 프롬프트 조립
    S->>S: get_mentor_strategy(mentor_id)<br/>→ VALUE / GROWTH / DIVIDEND / MOMENTUM
    S->>S: get_system_prompt(strategy)
    S->>TO: apply(prompt, tier)
    TO-->>S: 티어 강화 프롬프트

    Note over S,V: RAG 지식 보강
    S->>RAG: retrieve("learning_kb", query)
    RAG->>LE: embed(query)
    LE->>GEM: embed_content<br/>(gemini-embedding-001)
    GEM-->>LE: 임베딩 벡터
    LE-->>RAG: vector
    RAG->>V: query(vector, top_k=5)
    V-->>RAG: documents
    RAG-->>S: RAGContext

    alt RAG 문서 있음
        S->>S: 시스템 프롬프트에 출처 표기 지시 + 컨텍스트 첨부
    end

    Note over S,GEM: LLM 스트리밍
    S->>LS: chat_stream(system + history + user)
    LS->>GEM: streamGenerateContent<br/>(gemini-2.5-flash)
    loop 청크별
        GEM-->>LS: SSE chunk
        LS-->>S: StreamChunk(delta)
        S-->>U: event: delta<br/>data: {delta, done:false}
    end
    GEM-->>LS: 종료 + usage
    LS-->>S: StreamChunk(done=true, usage)
    S-->>U: event: delta<br/>data: {done:true, usage}

    Note over S,GO: 3중 후처리 검증 (실패해도 응답은 이미 나감 — warning만)
    S->>H: verify(full_answer, rag_ctx)
    H-->>S: bool
    S->>C: evaluate(full_answer, strategy, rag_ctx)
    C-->>S: CriticResult(ok, reason)
    S->>GO: check_output(full_answer)
    GO-->>S: GuardrailResult(ok, reason)

    Note over S,DB2: 어시스턴트 메시지 영속화
    S->>DB2: add ChatMessage(role="assistant")
    S->>DB2: commit
    DB2-->>S: persisted
    S->>S: async with 종료 → 세션 자동 close
```

### 4.1 왜 별도 `SessionLocal`을 여는가 (§5.2 설계 결정)

```mermaid
flowchart TD
    A[HTTP 요청 도달] --> B[FastAPI가 db: AsyncSession 주입]
    B --> C[router 핸들러 실행]
    C --> D[EventSourceResponse 반환]
    D -->|HTTP 요청 컨텍스트 종료| E[주입된 db 세션 close 됨]
    D -->|동시에| F[SSE 제너레이터는 별도 task로 계속 실행]
    F --> G{만약 주입된 db를<br/>그대로 쓰면?}
    G -->|YES| H[💥 ClosedSession 에러]
    G -->|NO, SessionLocal 새로 엶| I[✅ 안전한 트랜잭션]

    style H fill:#fee,stroke:#c33
    style I fill:#efe,stroke:#3a3
```

**규칙**: SSE/long-running 제너레이터 안에선 절대 의존성 주입된 `db`를 사용하지 말 것. `async with SessionLocal() as db:`로 새로 열어라.

---

## 5. 핵심 흐름 B — 퀴즈 채점 + 이벤트 발행 (`POST /quizzes/submit`)

가장 단순하면서도 **동 간 디커플링 패턴의 시범 케이스**.

```mermaid
sequenceDiagram
    autonumber
    actor U as 사용자
    participant R as router.submit_quiz
    participant CU as curriculum.grade_quiz
    participant EB as event_bus
    participant RD as Redis<br/>(pub/sub)
    participant GR as growth handler<br/>(다른 동)

    U->>R: POST /quizzes/submit<br/>{concept_id, answer_index}
    R->>CU: grade_quiz(concept_id, answer_index)
    CU-->>R: (is_correct, explanation)

    alt is_correct
        R->>EB: publish(ConceptMasteredEvent<br/>{user_id, concept_id})
        EB->>RD: Redis pub
        Note over RD,GR: 비동기 fan-out
        RD-->>GR: subscribe 수신
        GR->>GR: 멱등성 보장 + 이해도 게이지 +1
    end

    R-->>U: {correct, explanation}
```

**관찰 포인트**:
- 학습 동은 **growth 동의 코드를 직접 import 하지 않는다.** `core/contracts/`에 정의된 이벤트 타입(`ConceptMasteredEvent`)만 알 뿐.
- 정답 사용자가 즉시 응답을 받는 흐름은 이벤트 fan-out과 **독립적**이다. growth 동이 잠시 죽어 있어도 학습 동의 응답은 정상.
- 같은 사용자가 같은 개념 퀴즈를 여러 번 풀어도 growth 동이 **멱등성 키**로 한 번만 카운트해야 함 (학습 동의 책임 아님).

---

## 6. 단순 흐름 C — 세션·메시지 CRUD (1~4번 엔드포인트)

```mermaid
flowchart LR
    Client[클라이언트] --> R[router]
    R --> GA{get_current_user}
    GA -->|토큰 없음/만료| E401[401]
    GA -->|OK| SV[service 함수]
    SV --> DB[(Postgres)]
    DB --> SV
    SV --> R
    R --> Client

    SV -.첫 user 메시지일 때.-> EB[event_bus]
    EB -.MessageSentEvent.-> RD[(Redis)]

    style E401 fill:#fee
```

**짚을 점**:
- `list_messages`는 호출 전에 `get_session()`으로 **소유 확인** — 남의 세션 ID를 알아도 메시지를 읽을 수 없다. (`router.py` 75행과 `service.py` 78행)
- `add_message`가 **첫 사용자 메시지**일 때 세션 `title`을 자동 설정(첫 50자). 그래서 Swagger에서 본 세션 목록 제목 "PER이 뭐야? 두 문장으로..."이 자동 생성된 것.

---

## 7. 어디서 무엇이 결정되는가 — 한 줄 매핑

| 행동 | 결정 위치 | 비고 |
|---|---|---|
| "직접 추천 차단" | `core.ai_pipeline.guardrail.check_input` + `check_output` | 입력·출력 **양쪽** 검사 |
| "어떤 페르소나로 답하는가" | `features.learning.personas.get_mentor_strategy(mentor_id)` | 1→가치, 2→성장, 3→배당, 4→모멘텀, 그 외→가치 fallback |
| "어느 정도 난이도로 설명하는가" | `core.ai_pipeline.tier_overlay.apply(prompt, user_ctx.tier)` | T1~T5 |
| "어떤 지식을 참조할 것인가" | `core.ai_pipeline.rag.retrieve("learning_kb", query)` | Chroma 컬렉션 `learning_kb` |
| "어떤 모델로 응답할 것인가" | `core.llm.llm.chat_stream` + `core.config.settings.llm_provider` | provider="google" → gemini-2.5-flash |
| "정답인가" | `features.learning.curriculum.grade_quiz` | 단순 인덱스 비교 |
| "이해도 게이지 +1" | `growth` 동 핸들러 (학습 동은 알 바 아님) | 이벤트 구독 측 책임 |

---

## 8. 한계 / 향후 작업 (스냅샷 시점)

- **`hallucination.verify` / `critic.evaluate` / `guardrail.check_output`는 실패해도 warning만 남기고 응답은 그대로 사용자에게 보낸다.** 운영 모니터링 시점에 패턴이 잡히면 차단 모드로 전환 검토.
- **`learning_kb` Chroma 컬렉션은 비어 있다** (스모크 시점 기준 — `vector_store.upsert`를 부르는 코드 경로가 학습 동에 없음). RAG는 호출은 되지만 빈 결과를 받음. 운영 전에 초기 지식 베이스 적재 작업 필요.
- **`MessageSentEvent`의 구독자**가 아직 없다 (단순 발행만). 학습 분석/이해도 추정 용도로 활용 여지.
- **이벤트 멱등성** — `ConceptMasteredEvent`의 멱등성 키 정책은 growth 동에서 정해야 함. 학습 동은 단지 발행만.

---

## 9. 시각화 갱신 규칙

1. `features/learning/` 또는 `core/ai_pipeline/`에 새 단계가 추가되면 §4 sequence diagram을 갱신한다.
2. 새 엔드포인트가 추가되면 §3 표에 줄 추가, 필요시 §4·5 같은 핵심 흐름 다이어그램 추가.
3. 동 간 이벤트가 추가되면 §5와 §7 표에 반영.
4. 본 문서는 코드의 GA 시점 진실을 따라간다. 의도와 실제가 다르면 코드를 고치고 본 문서를 갱신.
