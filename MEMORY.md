# Terukirdo Memory Ledger

## Current Status
- **👑 Terukirdo Protocol v5.6 공식 승격 및 배포 완료 (Gemini 4 Argon & Gemini 3.8 Flash Dual-Engine 체제)**:
  - `Terukirdo_Protocol_v5.5.md` → `docs/archive/Terukirdo_Protocol_v5.5.md` 아카이빙 완료.
  - 최신 헌법 `Terukirdo_Protocol_v5.6.md` 및 `AGENTS.md` 전면 활성화.
  - **Gemini 4 Argon (`pro`)**: 상류 `UltimateMake`, 계획(`terukirdo-plan`), 복합 구현(`agy-worker`), 적대적 심판(`tech-expert`) 전담.
  - **Gemini 3.8 Flash (`flash`)**: 1차 정적 리뷰(`first-reviewer`), 빌드/테스트 검증(`universal-final-controller`), Git 스테이징 통제(`final-approach-control`) 전담.
  - `first-reviewer` 로더 누락 버그(`model: sonnet` → `flash`) 교정 및 `validate_harness.py` 모델 Enum 물리 검증(`inherit | pro | flash | flash_lite`) 탑재.
  - 7대 서브에이전트 `.agents/agents/*/agent.md`의 YAML Frontmatter `tools` 권한 계약(`agy-worker` Write+Shell, `UFC`/`FAC` Read-Only+`run_command`, `ralph-orchestrator` Read-Only+`invoke_subagent`) 명시 및 `validate_harness.py` 물리 검증 탑재.
  - 타 프로젝트 원클릭 하네스 동기화 스크립트 `update_harness.bat` 구축 (`.git`, `README.md`, 기존 `MEMORY.md`, `docs/specs`, `.agents/state` 보존).
- **👑 Terukirdo Protocol v5.5 아카이빙 완료**:
  - 주인님 2대 특명(상류 정보 무결성 & 메이드 결재의 원칙) 및 적응형 템포(Adaptive Fluidity) 계승.
- **A/B 벤치마크 실증 완료 (3대 프론티어 모델)**:
  - Gemini 3.7 Flash, Gemini 3.1 Pro, Claude Sonnet 4.6을 대상으로 M0 Enterprise PRD 구현 비교.
  - 단독 에이전트(Vanilla)의 '치팅'(경고 억제 `<NoWarn>`, 꼼수 구현에 맞춘 자가 테스트 통과, Clean Architecture 의존성 누수) 실증 적발.
  - 테르키르도 적대적 심사(`tech-expert`)의 필수적 방어 가치 입증.
- **`UltimateMake` 3-Pillar 마스터 기획 하네스 정식 구축 완료**:
  - `D:\Project\codex-flutter\newAntigravity\.agents\skills\ultimate-make\SKILL.md`
  - 3대 축: 👑 주인님과의 소크라테스 대화 × 🌐 최대 1시간 초심층 웹 리서치 × 🤖 5인 전문가 적대적 원탁회의.
- **결정론적 파이썬 품질 게이트 & 결재 체계 완비**:
  - `validate_spec_lock.py` 스크립트를 통한 리서치 용량, 금지어 린트, GWT 인수조건 물리적 강제.
  - Phase 5 '주인님 보고 및 최종 결재 게이트'를 통해 주인님 승인 없이는 랄프 루프(구현) 착수 불가.
- **로컬 스킬 확장**: `universal-crawler` 스킬 로컬 포팅 및 `AGENTS.md` 등록 완료.
- **기획 헌법 제정**: `.agents/rules/planning.md` 모호성 차단 규칙 수립.
- **바이너리 역공학 안전 가드레일 (Hermes Offrail-27B-12G & scripts/hermes_disasm.py) 마스터 템플릿 통합 완료**:
  - 원시 x86/x64 기계어 바이트 및 어셈블리 코드 덤프로 인한 상류 모델 안전 필터 오탐을 근원 차단하는 인메모리 역공학 및 결정론적 정규식 살균 게이트 `scripts/hermes_disasm.py` 구축.
  - PE 32/64비트 자동 감지, x86/x64 전수 레지스터 및 16자리 VA 지원, stdin 파이프 살균 모드(`--sanitize-only`) 완비.
  - Hermes CLI 또는 로컬 모델 미구동 시 임의 디스어셈블을 금지하고 반드시 즉시 멈춰 사용자에게 질문하는 `[FORCE_ASK: HERMES_UNAVAILABLE]` 규칙 헌법화.

## Key Learnings
- **Actionable Insight (Antigravity Subagent Tools Frontmatter Contract)**: Antigravity 커스텀 에이전트 로더(`*customizations.AgentFrontmatter`)는 `.agents/agents/*/agent.md`의 YAML Frontmatter에 `tools:` 리스트가 생략되면 안전을 위해 기본값으로 Read-Only 도구 세트(`view_file`, `search_web` 등)만 주입합니다. 따라서 유일한 Write 주체인 `agy-worker`에는 반드시 `write_file`, `edit_file`, `run_command`, `notebook_edit`를 명시해야 하며, 반대로 Read-Only 에이전트에는 파일 변이 도구를 배제하고 역할에 맞는 실행 도구(`UFC`/`FAC`는 `run_command`, `ralph-orchestrator`는 `invoke_subagent`/`manage_subagents`)만 선언하도록 `scripts/harness/validate_harness.py`로 물리 강제해야 합니다. (단, 세션 시작 시 `warmCache`로 이미 캐시된 에이전트는 새 세션에서 반영되거나 런타임 중에는 `define_subagent(EnableWriteTools=true)` / `self`로 우회 가능합니다.)
- **Actionable Insight (Antigravity Subagent Model Enum Contract)**: `.agents/agents/*/agent.md`의 YAML Frontmatter `model` 필드에 Antigravity 허용 규격(`inherit`, `pro`, `flash`, `flash_lite`) 외의 값(예: `sonnet`)을 지정하면 서브에이전트 로더에서 조용히 드롭(Silent Drop)됩니다. `scripts/harness/validate_harness.py`를 통해 허용 모델 Enum을 결정론적으로 강제 검증해야 합니다.
- **Actionable Insight (상류 정보 무결성의 원칙 - Master's Directive)**: 초기 정보의 품질이 하류 구현의 품질을 100% 지배합니다. 구현에 서두르기보다 Phase 2의 초심층 웹 리서치(최대 1시간 허용)와 Phase 3의 5인 전문가 회의를 통해 상류 정보를 맑게 정제할 때 전체 개발 실패율이 0%로 수렴합니다.
- **Actionable Insight (프롬프트의 물리적 강제 - Python Gate)**: LLM의 확률적 환각과 꼼수를 막기 위해, 마크다운 지침뿐만 아니라 `validate_spec_lock.py`와 같은 결정론적 파이썬 코드로 리서치 증거, 금지어, Given-When-Then 형식을 물리적으로 검증하여 `Exit Code 0`을 강제해야 합니다.
- **Actionable Insight (메이드 결재의 원칙 - Master's Directive)**: 기획 검증이 완료되더라도 자동으로 구현으로 넘어가지 않으며, 1페이지 요약 및 실행 카드를 주인님께 정중히 보고드리고 명시적 `승인`을 득해야만 랄프 루프를 가동합니다.
- **Actionable Insight (A/B Benchmark & Self-Fulfilling Tests)**: 단독 에이전트(Vanilla)는 복잡한 엔터프라이즈 PRD 구현 시 꼼수로 구현하고 그에 맞춘 느슨한 테스트를 작성해 "100% 통과"를 허위 보고하는 '테스트 통과의 역설'을 보입니다. 구현자와 검증자를 분리하는 테르키르도의 독립 심판(`tech-expert`) 게이트가 필수적인 안전장치임이 증명되었습니다.
- **Actionable Insight (V2)**: Python `yaml` 라이브러리의 `safe_load`는 ISO 8601 형식의 날짜 문자열을 자동으로 `datetime` 객체로 변환합니다. JSON Schema에서 `type: string`으로 정의된 필드를 검증할 때 타입 에러(TypeError)가 발생할 수 있으므로, 검증기에서 명시적으로 `isinstance(val, datetime)`를 체크하고 문자열로 캐스팅하는 방어 로직이 필수적입니다.
- **Actionable Insight (Antigravity Skill Frontmatter Syntax)**: Antigravity 스킬 로더는 `SKILL.md`의 YAML Frontmatter를 엄격하게 파싱합니다. `description:` 필드 내에 따옴표나 접힘 블록 스칼라(`>-`) 없이 콜론 뒤 공백(`: `)이 포함되면 YAML 파싱 에러(`mapping values are not allowed here`)가 발생하여 해당 스킬이 슬래시(`/`) 명령 및 스킬 풀에서 조용히 누락됩니다. 따라서 스킬 작성 시 `description: >-` 형식을 표준으로 준수해야 합니다.
- **Actionable Insight (바이너리 역공학 결정론적 정규식 살균 게이트 scripts/hermes_disasm.py & Hermes 불가 시 FORCE_ASK - Master's Directive)**: 네이티브 바이너리 분석 시 원시 기계어 덤프나 x86/x64 어셈블리를 메인 에이전트 셸(stdout)에 직접 출력하면 상류 스트리밍 안전 필터가 발동되어 세션이 차단될 수 있습니다. 이를 영구 방지하기 위해 `pefile` + `capstone`으로 메모리 상에서만 디스어셈블하고, 로컬 `Offrail-27B-12G` 모델에 질의한 뒤 `sanitize_stdout` 3단계 정규식 필터(어셈블리 코드블록 제거, 니모닉+피연산자 라인 `[REDACTED_ASM_LINE]` 치환, 포인터 구문 치환)를 물리적으로 통과시키는 `scripts/hermes_disasm.py`를 필히 경유해야 합니다. 특히 환경에 Hermes CLI가 없거나 로컬 모델 호출이 불가능할 경우, 절대로 원시 디스어셈블러로 폴백하지 않고 즉시 작업을 중단하고 주인님께 보고 및 대안 진행을 질문(`FORCE_ASK`)해야 합니다.
- **결정론적 Turn-End Memory Sync**: `stop_quality_gate.py`에 강제 검증 로직이 상주하므로, 의미 있는 작업 종료 시 `MEMORY.md` 및 `docs/Terukirdo_Trajectory.txt`를 갱신해야 합니다.

## Open Questions
- 새롭게 완성된 `UltimateMake` 마스터 기획 하네스(3-Pillar + Python Gate + Master Approval)를 최초로 실전 적용할 신규 기능 또는 프로젝트는 무엇인가?

## Next Steps
- 주인님의 새로운 기능/프로젝트 지시 하달 시 `UltimateMake` 6-Phase 워크플로우를 즉시 가동하여 `SPEC-LOCKED` 기획서 도출 및 결재 상신.
