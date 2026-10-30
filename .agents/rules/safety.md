# Safety Policies and Invariants

This document outlines the safety guardrails, commands classifications, and permission priorities.

## Permission Hierarchy

1. **Platform Permission Engine** (1st line of defense)
2. **PreToolUse Hook** (2nd line of defense - runtime command & subagent invocation checking)
3. **Execution Card Scope** (3rd line of defense - allowed/forbidden files check)
4. **Review/Controller Gates** (4th line of defense - evidence validation)

## Command Classification Rules

### 1. DENY (Strictly Prohibited)
The following actions must be blocked by hooks immediately:
- **Conversational / Auto-Triggering of `legion-commander` (`agent-legion`)**: Invoking `legion-commander` via natural language conversation without an explicit `/agent-legion` or `/legion` slash command from the user is strictly **DENIED** by `pre_tool_use_policy.py`.
- `rm -rf /` or `rm -rf <workspace root>`
- `git reset --hard`
- `git clean -fd` / `-fdx` / `-f` (without `-n` or `--dry-run`)
- `git checkout -- <path>`
- `Format-Volume`
- `dotnet ef database drop` or `Drop-Database`
- `terraform destroy`
- Direct modifications under `.git/` folder
- Workspace escape (modifying files outside allowed workspace folders)
- Writing literal API keys / secret tokens directly into code files (except documentation)
  - **단서**: 코드에 이미 존재하는 키/토큰이 발견되더라도 사용자의 의도적 설계일 수 있다. 기존 하드코딩 시크릿의 제거/수정은 DENY가 아니라 아래 FORCE_ASK를 따른다.

### 2. FORCE_ASK (Explicit Confirmation Required)
The following actions require explicit user review and confirmation before execution:
- Removing or modifying existing hardcoded API keys / secret tokens (사용자가 의도적으로 배치한 기본값일 수 있음)
- `terraform apply`
- `kubectl apply/delete/rollout/scale`
- `firebase deploy`
- `gcloud app deploy`
- `fastlane deliver/supply/pilot`
- `git commit`
- Database migrations (`supabase db push`, `dotnet ef database update`)
- Staging production configuration changes
- Installing new software packages (`npm install`, `pip install`, `pub get` etc.)
- **Hermes CLI 미설치 또는 미구동 시 역공학/디스어셈블 요청**: 환경에 `hermes`가 없거나 로컬 모델(`Offrail-27B-12G`) 호출이 실패할 경우(`Exit Code 2`), 에이전트가 임의로 직접 디스어셈블을 시도해서는 안 되며 **반드시 즉시 멈추고 주인님께 보고 후 어떻게 진행할지 질문(Ask)**해야 한다.

### 3. ALLOW (Automatically Permitted)
- Read-only actions (`git status`, `git diff`, `git diff --check`, `git clean -n`)
- Local build, lint, and test runs
- Filesystem editing within the authorized workspace scope

## Agent Legion Slash-Command-Only Trigger Invariant (`legion-commander`)

- **절대 대화(자연어) 발동 금지**: 자동 검토 사령관(`legion-commander`) 및 `agent-legion` 스킬은 중간 수동 검토 없이 대규모 병렬 구현과 무인 Auto-Rework 루프를 끝까지 가동하므로, 일반 대화("병렬로 구현해줘", "에이전트 군단 가동해줘", "무인으로 끝내줘" 등 자연어 발화)로는 **절대로 발동할 수 없다.**
- **슬래시 명령 전용 (`/agent-legion` 또는 `/legion`)**: 오직 주인님께서 채팅창에 명시적으로 **`/agent-legion` 또는 `/legion` 슬래시 명령**을 입력하신 경우에만 발동이 허용된다.
- **물리적 3중 차단**:
  1. `skill_indexer.py`: 쿼리에 `/agent-legion` 또는 `/legion`이 없으면 후보 스킬 검색 결과에서 `agent-legion`을 원천 제외한다.
  2. `pre_tool_use_policy.py`: `invoke_subagent(TypeName="legion-commander")` 호출 시 프롬프트 및 실제 대화 트랜스크립트(`transcript.jsonl`)의 최신 `USER_INPUT`에 `/agent-legion` 또는 `/legion` 슬래시 명령이 없으면 즉시 `deny`로 차단한다.
  3. 자연어로 군단 가동을 요청받았을 경우, 에이전트는 사령관을 소환하지 않고 주인님께 `"/agent-legion <지시사항>"` 슬래시 명령 사용을 정중히 안내해야 한다.

## Binary Disassembly & Reverse Engineering Guardrail (Hermes CLI & Sanitizer)

- **Do NOT dump raw x86/x64 native disassembly directly into the main agent context**, as raw assembly dumps trigger upstream model safety filter false positives.
- **NEVER run direct disassembly tools or raw `hermes chat` in the main shell without sanitization**, because if the model output contains assembly instruction lines or code blocks, `run_command` stdout will capture them and trip the safety filter.
- **Mandatory Disassembly Pipeline**:
  Always invoke the deterministic sanitizer wrapper `scripts/hermes_disasm.py`, which prompts the local `Offrail-27B-12G` model via Hermes CLI and deterministically redacts any remaining x86/x64 assembly instructions via regex before printing to stdout:
  - **Mode A (Fast In-Memory Capstone + Hermes)**:
    ```powershell
    python -X utf8 scripts/hermes_disasm.py --binary <path/to/binary.exe> --va <VA> -q "<역공학 분석 질의>"
    ```
  - **Mode B (Hermes + REA MCP Explicit Tool Mode)**:
    ```powershell
    python -X utf8 scripts/hermes_disasm.py --use-rea --binary <path/to/binary.exe> [--va <VA>] -q "<REA MCP 도구를 사용해 의사코드/교차참조 분석 질의>"
    ```
- **Hermes CLI 미설치 또는 미구동 시 (`FORCE_ASK`)**:
  환경에 `hermes`가 설치되어 있지 않거나 로컬 `Offrail-27B-12G` 모델(`http://127.0.0.1:8899/v1`) 호출이 실패할 경우(`Exit Code 2`), **절대로 직접 디스어셈블러를 콘솔에 실행하거나 원시 코드를 덤프하는 폴백(Fallback)을 수행해서는 안 된다.** 즉시 멈추고 `[FORCE_ASK: HERMES_UNAVAILABLE]` 상태로 주인님께 보고하여 어떻게 진행할지 명시적 지침을 질문해야 한다.
- The wrapper guarantees that zero raw assembly mnemonics or byte dumps reach the orchestrator's context, returning only high-level pseudocode, struct offsets, and packet field specifications.
