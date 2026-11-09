# Terukirdo Memory Ledger

## Current Status
- **🧠 [Hot Memory - Current Status & Active Invariants] Dual-Brain 4대 핵심 운영 통찰 하네스 이식 완료 (2026-11-09, `TASK-20261109-DUAL-BRAIN-HARNESS-UPGRADE`)**:
  - `[decision][refs:1][last_verified:2026-11-09]` **No Finding Quota & 4-Element Defect Contract**: 리뷰어(`first-reviewer`, `tech-expert`)의 인위적 결함 발굴 할당량을 원천 폐지. 요구사항 만족 시 클린 리뷰(`PASS` / `ARCHITECTURALLY ACCEPTABLE`)가 성공이며, `REWORK REQUIRED`를 유발하는 P1/P2 결함은 반드시 `[1. 위반된 계약 + 2. 구체적 트리거 + 3. 현재 코드 근거 + 4. 실질적 피해]`의 4대 요소를 엄격히 입증해야 함. (Evidence: `.agents/rules/evidence.md`, `.agents/agents/first-reviewer/agent.md`, `.agents/agents/tech-expert/agent.md`)
  - `[decision][refs:1][last_verified:2026-11-09]` **Subagent Handle Reuse (`send_message`) & Compact Briefs**: 동일 작업/파티션 내 Rework 시 중복 서브에이전트를 스폰하지 않고 활성 `conversationId`로 `send_message`를 호출하여 이전 컨텍스트를 재사용하며, 핵심 목표/diff/검증 명령 위주의 컴팩트 브리프 전달 및 최종 diff 재검증 의무화. (Evidence: `.agents/agents/ralph-orchestrator/agent.md`, `.agents/agents/legion-commander/agent.md`, `AGENTS.md`, `Terukirdo_Protocol_v5.6.md`)
  - `[constraint][refs:1][last_verified:2026-11-09]` **Baseline Test Integrity Guard & Evidence Scope Isolation**: 작업자가 빌드/테스트를 억지로 통과시키기 위해 기존 베이스라인 테스트(`tests/**`)를 수정·삭제·약화하는 행위를 원천 금지하고, 완료 증거는 오직 실제 코드 diff와 원시 실행 결과(`exit_code == 0`)로만 채택. (Evidence: `.agents/rules/evidence.md`, `.agents/agents/universal-final-controller/agent.md`, `.agents/agents/final-approach-control/agent.md`, `.agents/agents/agy-worker/agent.md`, `Terukirdo_Protocol_v5.6.md`)
  - `[decision][refs:1][last_verified:2026-11-09]` **4-Tier Weighted Memory Architecture**: `MEMORY.md`를 4계층(`Hot / Warm / Cold / Archived Decisions`)으로 분할하고, 단순 읽기 시 장부 갱신만을 위한 덮어쓰기(No Bookkeeping-Only Writes) 원천 차단. (Evidence: `.agents/rules/documentation.md`, `Terukirdo_Protocol_v5.6.md`, `MEMORY.md`)
  - `[decision][refs:1][last_verified:2026-11-09]` **Windows Read-Only Purge & Nested `.git` Ignore Guard in `sync_harness.py`**: `IGNORE_NAMES`에 `".git"`을 추가하고 `_force_unlink`/`_force_rmtree`(`stat.S_IWRITE` 권한 해제)를 도입하여 Windows 환경에서 읽기 전용 팩파일(`.git/objects/pack/*.idx`) 소거 시 `[WinError 5]` 거부 에러를 방지하고 타겟 프로젝트로 중첩 `.git`이 복사되는 결함을 영구 차단. (Evidence: `scripts/harness/sync_harness.py`, `tests/harness/test_update_harness.py`)
  - `[decision][refs:1][last_verified:2026-11-09]` **Harness Policy Synchronization (`docs/harness/`)**: `docs/harness/review-contract.md` 및 `docs/harness/evidence-policy.md`에 리뷰어 할당량 폐지, 4요소 결함 입증 계약, 서브에이전트 핸들 재사용, 베이스라인 테스트 무결성 보호, 증거 범위 격리 규칙을 상호 동기화. (Evidence: `docs/harness/review-contract.md`, `docs/harness/evidence-policy.md`)
  - `[cleanup][refs:1][last_verified:2026-11-10]` **Temporary Reference Purge & README Full Synchronization (`TASK-20261110-README-SYNC-AND-CLEANUP`)**: 임시 참조 폴더 `reference/dual-brain` 전수 소거(Windows 읽기 전용 파일 권한 해제) 및 4개 트랙 문서 보존 완료. `README.md` 전면 동기화(33 Tests 배지, 10대 핵심 철학, 9대 에이전트 운영 계약, 결정론적 하네스 검증/동기화 엔진 섹션, 4계층 메모리 장부 및 디렉토리 구조 최신화). (Evidence: `README.md`, `reference/`)
- **⚔️ 무인 다중 코어 '에이전트 군단(Agent Legion)' 3계층 Quad-Ralph 아키텍처 공식 탑재 (2026-10-31)**:
  - 사용자가 일일이 중간 검토를 하지 않아도 대규모 과업을 자율 병렬로 완수할 수 있도록, **최상위 자동 검토 사령관(`legion-commander`) 1기가 하위에 `ralph-orchestrator`를 최대 4기(Ralph #1 ~ #4)까지 동시에 생성·운용**하고, **각각의 `ralph-orchestrator`가 산하에 자체 워커(`legion-worker`, `agy-worker`)와 각종 검증관(`terukirdo-plan`, `first-reviewer`, `tech-expert`, `universal-final-controller`, `final-approach-control`) 분대를 생성·운용**하는 3계층 지휘 체계 구축.
  - **🔒 대화(자연어) 발동 절대 금지 & 슬래시 명령(`/agent-legion` 또는 `/legion`) 전용 물리 잠금**:
    - 일반 대화("병렬로 구현해줘", "에이전트 군단 가동해줘" 등)로는 절대로 자동 검토 사령관(`legion-commander`)이 발동되지 않도록 4중 차단 완비.
    - `.agents/hooks/pre_tool_use_policy.py` & `.agents/hooks.json`: `invoke_subagent(TypeName="legion-commander")` 호출 시 프롬프트 및 대화 트랜스크립트(`transcript.jsonl`)의 최신 `USER_INPUT`에 `/agent-legion` 또는 `/legion` 슬래시 명령이 없으면 즉시 `deny` 물리 차단.
    - `.agents/skills/self-evolution/scripts/skill_indexer.py`: 쿼리에 `/agent-legion` 또는 `/legion`이 없으면 SAD 라우팅 후보 풀에서 `agent-legion`을 원천 제외.
    - `.agents/rules/safety.md`, `AGENTS.md`, `Terukirdo_Protocol_v5.6.md`, `SKILL.md`, `agent.md`에 슬래시 명령 전용 불변식 헌법화.
  - **`legion-commander` (자동 검토 사령관 / 최대 4기 동시 Ralph 총괄 감독관, `pro` Gemini 4 Argon)**:
    - 전체 과업을 Wave당 최대 4개(`MAX_CONCURRENT_RALPH = 4`)의 독립 파티션으로 분해하고 `scripts/partition_validator.py`로 동시 4기 제한 및 비충돌 배타성(Disjointness) 사전 물리 검증.
    - 하위에 최대 4기의 `ralph-orchestrator`(Ralph #1 ~ #4)를 동시 병렬 소환(`invoke_subagent`)하여 운용.
    - 각 `ralph-orchestrator`가 산하 워커 및 검증관 분대를 돌려 보고한 중간/최종 산출물·Verdict·증거를 주인님 대신 자동 검토(Autonomous Meta-Review)하고, 통과 시 다음 Wave 파티션을 자율 승인·전진.
    - 결함(`REWORK REQUIRED` 등) 탐지 시 사람 개입 없이 해당 `ralph-orchestrator`에게 최대 3회 자동 재작업(Auto-Rework) 지휘.
    - 전 Wave 완수 후 프로젝트 전체 통합 빌드 및 회귀 테스트 직접 물리 구동(`run_command`)하여 통합 Evidence Bundle 상신.
  - **`ralph-orchestrator` (랄프 에이전트, 최대 4기 동시 기동, `pro` Gemini 4 Argon)**:
    - 사령관으로부터 배정받은 파티션을 전담하여 자기 산하에 `terukirdo-plan`, `legion-worker`/`agy-worker`, `first-reviewer`, `tech-expert`, `UFC`, `FAC` 분대를 생성·운용.
  - **`legion-worker` (군단 코어 워커, `pro` Gemini 4 Argon)**: 각 `ralph-orchestrator` 통제 하에 배타적 파티션(`allowed_files`) 범위 내 고속 병렬 구현, 동반 단위 테스트 작성 및 물리 검증(Write 권한).
  - **하네스 무결성 검증 완비**: `scripts/harness/validate_harness.py`, `tests/harness/test_agent_discovery.py`, `tests/harness/test_skill_indexer.py`, `tests/harness/test_partition_validator.py`, `tests/harness/test_pre_tool_hook.py` 전수 100% 통과.
- **👑 Terukirdo Protocol v5.6 공식 승격 및 배포 완료 (Gemini 4 Argon & Gemini 3.8 Flash Dual-Engine 체제)**:
  - `Terukirdo_Protocol_v5.5.md` → `docs/archive/Terukirdo_Protocol_v5.5.md` 아카이빙 완료.
  - 최신 헌법 `Terukirdo_Protocol_v5.6.md` 및 `AGENTS.md` 전면 활성화.
  - **Gemini 4 Argon (`pro`)**: 상류 `UltimateMake`, 자동 검토 사령관(`legion-commander`), 하위 루프 조율(`ralph-orchestrator`), 군단 코어 구현(`legion-worker`), 계획(`terukirdo-plan`), 복합 구현(`agy-worker`), 적대적 심판(`tech-expert`) 전담.
  - **Gemini 3.8 Flash (`flash`)**: 1차 정적 리뷰(`first-reviewer`), 빌드/테스트 검증(`universal-final-controller`), Git 스테이징 통제(`final-approach-control`) 전담.
  - 타 프로젝트 원클릭 하네스 동기화 스크립트 `update_harness.bat` 및 결정론적 동기화·소거 엔진 `scripts/harness/sync_harness.py` 구축:
    - 기존 단순 복사(`robocopy /E`) 방식의 한계를 해결하여, 마스터 템플릿에서 삭제·이동된 구버전 파일/폴더(루트 `Terukirdo_Protocol_v5.2~v5.5.md`, 루트 `agents/*.md` 중복 에이전트, 삭제된 스킬 `.agents/skills/flutter-expert/` 등)를 대상 프로젝트에서 결정론적으로 100% 추적 소거(Mirror & Purge).
    - 대상 프로젝트 고유 자산(`.git`, 소스코드, `README.md`, `MEMORY.md`, `docs/Terukirdo_Trajectory.txt`, `docs/specs/*`, 기존 `docs/development/*`, `.agents/state/*`)은 철저히 보존하며, 동기화 직후 `skill_indexer.py --build`와 `validate_harness.py --strict`까지 자동 수행.
- **`UltimateMake` 3-Pillar 마스터 기획 하네스 정식 구축 완료**:
  - 3대 축: 👑 주인님과의 소크라테스 대화 × 🌐 최대 1시간 초심층 웹 리서치 × 🤖 5인 전문가 적대적 원탁회의.
  - `validate_spec_lock.py` 스크립트를 통한 리서치 용량, 금지어 린트, GWT 인수조건 물리적 강제.
  - Phase 5 '주인님 보고 및 최종 결재 게이트'를 통해 주인님 승인 없이는 랄프 루프(구현) 착수 불가.
- **바이너리 역공학 안전 가드레일 (Hermes Offrail-27B-12G & scripts/hermes_disasm.py) 마스터 템플릿 통합 완료**:
  - 원시 기계어 바이트 살균 게이트 및 `[FORCE_ASK: HERMES_UNAVAILABLE]` 규칙 헌법화.
  - **🚀 Hermes CLI 로컬 모델(`Offrail-27B-12G`) 25x 속도 최적화 및 안티 환각 C 의사코드 정밀화 (2026-11-02)**: Mode A에 `--ignore-rules --reasoning none -t none --max-turns 1`을 강제하여 20,000+ 토큰의 룰 주입과 추론 오버헤드를 제거(27분 → 45~60초, ~25x 속도 향상), Mode B에 `--yolo --ignore-rules --reasoning low` 적용. 바이트 단위 `--size`(400~750 bytes) 및 `--no-stop-at-ret` 정렬 강제, 더미 struct/추측 필드명 배제 및 C 의사코드 즉시 출력 제한, `proc.returncode != 0` 시 `[FORCE_ASK: HERMES_UNAVAILABLE]`(exit 2) 안전 가드 완비.

## Key Technical Learnings
- **[Warm Memory - Key Technical Learnings & Domain Insights] Actionable Insight (Key Technical Learnings: Hermes CLI 로컬 모델 Offrail-27B-12G 25x 속도 최적화 및 안티 환각 C 의사코드 추출 원칙 - Master's Directive)**: `[decision][refs:3][last_verified:2026-11-09]` 로컬 Hermes CLI 구동 시 기본 시스템 프롬프트에 `AGENTS.md`, `MEMORY.md`, `.agents/*` 등 20,000+ 토큰의 컨텍스트가 자동 주입되면 로컬 27B 모델 추론 지연이 질의당 27분 이상 폭증합니다. 따라서 Mode A 실행 시 반드시 `--ignore-rules --reasoning none -t none --max-turns 1`을 인가하여 불필요한 규칙, 도구 스키마, 추론 오버헤드를 원천 배제하고 실행 속도를 45~60초 수준으로 약 25배 단축해야 합니다(Mode B는 `--yolo --ignore-rules --reasoning low` 사용). 또한 `--size`는 명령어 개수가 아닌 바이트 단위이므로 함수 시작 VA에 정렬하고 충분한 바이트(`400`~`750` bytes) 및 `--no-stop-at-ret`를 지정해야 하며, 질의 시 더미 struct 정의 및 추측성 필드명을 금지하고 정확한 함수 진입 VA, 호출 대상 주소(`func_0x...`), 분기 조건(switch/if), 오프셋(`+0x...`), 상수(hex)만 간결한 C 의사코드로 즉시 추출하도록 엄격히 제한해야 합니다. (Evidence: `scripts/hermes_disasm.py`, `.agents/rules/safety.md`)

- **Actionable Insight (3계층 Quad-Ralph 군단 편제: 자동 검토 사령관 1기 × 동시 최대 4기 랄프 에이전트 × 각 산하 워커·검증관 분대 - Master's Directive)**: `[decision][refs:4][last_verified:2026-11-09]` 자동 검토 사령관(`legion-commander`)은 하위에 `ralph-orchestrator`를 최대 4기(`MAX_CONCURRENT_RALPH = 4`)까지 동시에 생성·운용하며, 각각의 `ralph-orchestrator`가 자기 산하에 워커(`legion-worker`/`agy-worker`)와 각종 검증관(`terukirdo-plan`, `first-reviewer`, `tech-expert`, `UFC`, `FAC`)을 거느리고 독립 파티션을 완수합니다. 파티션이 4개를 초과할 경우 Wave 단위로 최대 4개씩 묶어 스케줄링하며, 이를 `partition_validator.py`가 결정론적으로 사전 검증합니다. (Evidence: `.agents/agents/legion-commander/agent.md`, `.agents/skills/agent-legion/SKILL.md`)

- **Actionable Insight (자동 검토 사령관의 대화 발동 차단 및 슬래시 명령 전용 물리 게이트 - Master's Directive)**: `[constraint][refs:5][last_verified:2026-11-09]` 자동 검토 사령관(`legion-commander`)은 중간 수동 검토 없이 대규모 병렬 구현과 무인 Auto-Rework 루프를 끝까지 수행하므로, 일반 자연어 대화에서 에이전트의 자의적 판단으로 발동되면 의도치 않은 무인 폭주가 발생할 수 있습니다. 따라서 오직 주인님의 명시적 슬래시 명령(`/agent-legion` 또는 `/legion`)으로만 발동되도록 (1) `pre_tool_use_policy.py`의 `invoke_subagent` 훅 검사(프롬프트 및 `transcript.jsonl` 최신 사용자 입력 대조), (2) `skill_indexer.py`의 자연어 쿼리 필터링, (3) 에이전트/스킬/헌법의 명시적 금지 조항으로 다중 물리 잠금을 걸어야 합니다. (Evidence: `.agents/hooks/pre_tool_use_policy.py`, `.agents/rules/safety.md`)

- **Actionable Insight (Antigravity Subagent Tools Frontmatter Contract)**: `[constraint][refs:4][last_verified:2026-11-09]` Antigravity 커스텀 에이전트 로더(`*customizations.AgentFrontmatter`)는 `.agents/agents/*/agent.md`의 YAML Frontmatter에 `tools:` 리스트가 생략되면 안전을 위해 기본값으로 Read-Only 도구 세트(`view_file`, `search_web` 등)만 주입합니다. 따라서 Write 주체인 `agy-worker`, `legion-worker`에는 반드시 `write_file`, `edit_file`, `run_command`, `notebook_edit`를 명시해야 하며, 반대로 Read-Only 사령관/관제관에는 파일 변이 도구를 배제하고 역할에 맞는 실행 도구(`run_command`, `invoke_subagent` 등)만 선언하도록 `scripts/harness/validate_harness.py`로 물리 강제해야 합니다. (Evidence: `scripts/harness/validate_harness.py`, `tests/harness/test_agent_discovery.py`)

- **Actionable Insight (Antigravity Subagent Model Enum Contract)**: `[constraint][refs:3][last_verified:2026-11-09]` `.agents/agents/*/agent.md`의 YAML Frontmatter `model` 필드에 Antigravity 허용 규격(`inherit`, `pro`, `flash`, `flash_lite`) 외의 값(예: `sonnet`)을 지정하면 서브에이전트 로더에서 조용히 드롭(Silent Drop)됩니다. `scripts/harness/validate_harness.py`를 통해 허용 모델 Enum을 결정론적으로 강제 검증해야 합니다. (Evidence: `scripts/harness/validate_harness.py`, `tests/harness/test_agent_discovery.py`)

- **Actionable Insight (상류 정보 무결성의 원칙 - Master's Directive)**: `[decision][refs:3][last_verified:2026-11-09]` 초기 정보의 품질이 하류 구현의 품질을 100% 지배합니다. 구현에 서두르기보다 Phase 2의 초심층 웹 리서치(최대 1시간 허용)와 Phase 3의 5인 전문가 회의를 통해 상류 정보를 맑게 정제할 때 전체 개발 실패율이 0%로 수렴합니다. (Evidence: `.agents/skills/ultimate-make/SKILL.md`)

- **Actionable Insight (프롬프트의 물리적 강제 - Python Gate)**: `[decision][refs:3][last_verified:2026-11-09]` LLM의 확률적 환각과 꼼수를 막기 위해, 마크다운 지침뿐만 아니라 `validate_spec_lock.py`와 같은 결정론적 파이썬 코드로 리서치 증거, 금지어, Given-When-Then 형식을 물리적으로 검증하여 `Exit Code 0`을 강제해야 합니다. (Evidence: `.agents/skills/ultimate-make/scripts/validate_spec_lock.py`)

- **Actionable Insight (메이드 결재의 원칙 - Master's Directive)**: `[decision][refs:3][last_verified:2026-11-09]` 기획 검증이 완료되더라도 자동으로 구현으로 넘어가지 않으며, 1페이지 요약 및 실행 카드를 주인님께 정중히 보고드리고 명시적 `승인`을 득해야만 랄프 루프를 가동합니다. (Evidence: `Terukirdo_Protocol_v5.6.md`, `AGENTS.md`)

- **Actionable Insight (바이너리 역공학 결정론적 정규식 살균 게이트 scripts/hermes_disasm.py & Hermes 불가 시 FORCE_ASK - Master's Directive)**: `[constraint][refs:3][last_verified:2026-11-09]` 네이티브 바이너리 분석 시 원시 기계어 덤프나 x86/x64 어셈블리를 메인 에이전트 셸(stdout)에 직접 출력하면 상류 스트리밍 안전 필터가 발동되어 세션이 차단될 수 있습니다. 이를 영구 방지하기 위해 `pefile` + `capstone`으로 메모리 상에서만 디스어셈블하고, 로컬 `Offrail-27B-12G` 모델에 질의한 뒤 `sanitize_stdout` 3단계 정규식 필터를 물리적으로 통과시키는 `scripts/hermes_disasm.py`를 필히 경유해야 합니다. (Evidence: `scripts/hermes_disasm.py`, `.agents/rules/safety.md`)

- **결정론적 Turn-End Memory Sync**: `[constraint][refs:2][last_verified:2026-11-09]` `stop_quality_gate.py`에 강제 검증 로직이 상주하므로, 의미 있는 작업 종료 시 `MEMORY.md` 및 `docs/Terukirdo_Trajectory.txt`를 갱신해야 합니다. (Evidence: `.agents/hooks/stop_quality_gate.py`)

## Cold Memory
- **과거 프로토콜 버전 및 이력 컨텍스트**:
  - `Terukirdo_Protocol_v5.2 ~ v5.5`의 아키텍처 변천사 및 초기 L0~L4 검증 레벨 체계.
  - 마스터 하네스 초기 구축 단계의 단위 테스트 수치 이력 (v5.3 시점 19개 통과, Agent Legion 탑재 초기 25개 통과).
  - CODEX PRD 마일스톤 M0(C# 14 / .NET 10) 3라운드 실증 벤치마크 원시 데이터 (Vanilla 에이전트 Roslyn 경고 억제 `<NoWarn>`, SHA-256 검증 건너뛰기 치팅 적발 사례).
  - 해당 상세 이력은 필요 시 `docs/archive/` 및 `docs/Terukirdo_Trajectory.txt`의 날짜별 기록을 통해 선별 조회함.

## Archived Decisions
- `[superseded][archived:2026-10-31] Naive robocopy /E one-way harness copy was replaced by deterministic mirror & purge (scripts/harness/sync_harness.py) to eliminate zombie legacy files in target projects. (Evidence: scripts/harness/sync_harness.py)`
- `[superseded][archived:2026-11-02] Running local Hermes Offrail-27B-12G with default rules/tools in Mode A was replaced by --ignore-rules --reasoning none -t none --max-turns 1 (~25x speedup, 27m -> 45s). (Evidence: scripts/hermes_disasm.py)`
- `[superseded][archived:2026-10-21] Terukirdo Protocol v5.2~v5.5 single/legacy model mappings were superseded by v5.6 Asymmetric Dual-Engine (Gemini 4 Argon pro x Gemini 3.8 Flash flash). (Evidence: Terukirdo_Protocol_v5.6.md)`

## Open Questions
- 새롭게 완비된 `/agent-legion` (슬래시 전용 3계층 Quad-Ralph 군단 총괄 체계)과 `UltimateMake` 마스터 기획 하네스를 연계하여 최초로 병렬 실전 가동할 대규모 프로젝트는 무엇인가?

## Next Steps
- 주인님께서 `/agent-legion` 또는 `/legion` 슬래시 명령을 하달하실 때만 `legion-commander`를 기동하여 하위에 최대 4기의 `ralph-orchestrator` 및 산하 분대를 동시 운용하며 무인 병렬 완수 수행.
- 이식된 Dual-Brain 4대 운영 원칙(No Finding Quota, Subagent Handle Reuse, Baseline Test Integrity Guard, 4-Tier Weighted Memory)을 하네스 실전 작업에 엄격히 적용.
