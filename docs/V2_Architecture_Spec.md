# V2 초경량 템플릿 아키텍처 상세 설계서 (Architecture Spec)

## 1. 시스템 개요 (System Overview)
본 설계는 무거운 외부 데이터베이스나 인프라 없이 **순수 파일 시스템(Markdown, YAML, Script)**과 **Git Hooks**만을 활용하여 테르키르도 V2 코어(예지형 동기화, 면역 체계, 메모리 스케이프)를 구현하는 범용 템플릿 아키텍처입니다.

---

## 2. 디렉토리 구조 (Directory Structure)
템플릿이 프로젝트에 이식될 때 생성되는 핵심 폴더 구조입니다.

```text
.agents/
├── memory/                  # 마크다운 기반 메모리 스케이프 (지식 그래프)
│   ├── meta_schema.yaml     # 메모리 메타데이터 스키마 정의
│   ├── index.md             # 메모리 루트 인덱스
│   └── 2026/                # 연도별/월별 아카이브된 메모리 노드들
├── mcp/                     # Python 기반 MCP (보안 미들웨어 및 서버)
│   ├── main.py              # MCP 서버 진입점 (STDIO/HTTP)
│   ├── security_hook.py     # 명령어 및 I/O 정규식 검증 모듈
│   └── rules.yaml           # 면역 체계 화이트리스트/블랙리스트 룰셋
├── hooks/                   # Git Hook 쉘 스크립트 모음
│   ├── pre-commit           # 로컬 커밋 전 코드 검증 및 보안 체크
│   └── post-merge           # Pull 이후 예지형 동기화(Pre-fetch) 스크립트
└── state/                   # 런타임 상태 및 동기화 캐시
    └── .terkirdo_pre_cache.md # 예지형 동기화 예측 상태 캐시
```

---

## 3. 핵심 모듈 상세 설계 (Module Boundaries)

### 3.1. 면역 체계: MCP 보안 미들웨어 (`.agents/mcp/security_hook.py`)
*   **역할:** LLM 에이전트가 실행하려는 모든 터미널 명령어와 파일 쓰기 요청을 중간에서 가로채어 검증합니다.
*   **검증 로직 (Regex & Rule-based):**
    *   **Blacklist:** `rm -rf /`, `rm -rf .*`, 외부 미인가 도메인 `curl/wget` 요청 등 파괴적 명령어 정규식 매칭.
    *   **Whitelist:** `.agents/` 디렉토리 외부의 특정 보호 구역(예: `src/core/`)에 대한 쓰기 권한 통제.
*   **Data Flow:** 
    `Agent Command -> MCP Server (STDIO) -> rules.yaml 대조 -> [PASS] -> OS Execution -> Result -> Agent`

### 3.2. 메모리 스케이프: 마크다운 지식 그래프 (`.agents/memory/`)
*   **역할:** 데이터베이스(Neo4j/Milvus)를 대체하는 순수 텍스트 기반의 시맨틱(Semantic) 기억 장소.
*   **데이터 스키마 (YAML Frontmatter):**
    모든 `.md` 파일은 최상단에 다음과 같은 메타데이터를 갖습니다.
    ```yaml
    ---
    id: mem-20260817-001
    timestamp: 2026-08-17T21:00:00Z
    type: [decision, emotion, error_fix]
    emotion_tone: neutral
    related_files: ["src/main.py", "docs/architecture.md"]
    tags: ["architecture", "v2", "lightweight"]
    ---
    ```
*   **탐색 로직:** Python 스크립트(`os.walk` 및 `yaml` 파서) 또는 표준 `grep` 명령어를 통해 특정 태그나 시간대의 기억을 추출하여 프롬프트에 주입(RAG)합니다.

### 3.3. 예지형 동기화: Git Hook 파이프라인 (`.agents/hooks/`)
*   **역할:** 타 기기 또는 다른 클론(Clone) 환경에서 최신 상태를 즉각적으로 동기화하고 환경을 준비합니다.
*   **Pre-commit Hook:** 
    커밋 생성 시 변경된 파일 목록과 `memory/` 폴더의 변동 사항을 요약하여 `.terkirdo_pre_cache.md`에 기록합니다.
*   **Post-merge Hook:** 
    `git pull` 완료 직후 실행되며, `.terkirdo_pre_cache.md`를 파싱하여 필요한 npm 패키지 설치(`npm install`), 파이썬 의존성 설치, 또는 개발 서버 자동 재시작을 백그라운드에서 트리거합니다.

---

## 4. 보안 및 권한 (Security & Permissions)
*   **Zero-Trust:** MCP 서버를 거치지 않은 Agent의 직접적인 Shell 접근은 불가능하도록 샌드박싱합니다.
*   **룰셋 분리:** 보안 룰(`rules.yaml`)은 Agent가 수정할 수 없도록 Read-only 권한으로 고정하며, 오직 사용자(Human)만 수정 가능하게 설정합니다.
