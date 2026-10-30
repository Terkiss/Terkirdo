---
name: agent-legion
description: STRICT SLASH-COMMAND ONLY (/agent-legion or /legion). Autonomous 3-Tier Quad-Ralph Agent Legion skill where the Legion Commander spawns and manages up to 4 concurrent Ralph Orchestrator instances, each operating its own subordinate workers and verification agents. NEVER trigger via natural language conversation.
---

# Agent Legion (에이전트 군단 — 자동 검토 사령관 × 최대 4기 동시 랄프 에이전트 × 산하 분대 총괄 체계)

에이전트 군단(`agent-legion`)은 주인님께서 중간중간 일일이 검토하거나 승인 버튼을 누르지 않아도 대규모 작업을 병렬로 끝까지 완수할 수 있도록 설계된 **3계층 무인 오케스트레이션 스킬**입니다:
1. **최상위 자동 검토 사령관 (`legion-commander`)**이 전체 과업을 비충돌 파티션으로 분할하고,
2. **하위에 `ralph-orchestrator`(랄프 에이전트)를 최대 4기(Quad-Ralph: Ralph #1 ~ #4)까지 동시에 생성·운용**하며,
3. **각각의 `ralph-orchestrator`는 자기 하위에 자체적인 워커(`legion-worker` / `agy-worker`)와 각종 검증관(`terukirdo-plan`, `first-reviewer`, `tech-expert`, `universal-final-controller`, `final-approach-control`) 분대를 생성·운용**합니다.

---

## 🚨 0. 절대 발동 규칙: 슬래시 명령 전용 (Slash-Command-Only Trigger Invariant)

> [!CAUTION]
> **대화(자연어) 발동 절대 금지!**
> 자동 검토 사령관(`legion-commander`) 및 `agent-legion` 스킬은 중간 수동 검토 없이 최대 4기의 랄프 에이전트와 산하 분대를 동시 가동하므로, **일반 자연어 대화로는 절대로 발동하지 않습니다.**

1. **오직 슬래시 명령으로만 발동**:
   - 주인님께서 명시적으로 **`/agent-legion`** 또는 **`/legion`** 슬래시 명령을 입력하신 경우에만 발동합니다.
2. **자연어 요청 시 행동 지침 (자동 발동 금지 & 슬래시 명령 안내)**:
   - 만약 주인님이 슬래시 명령 없이 일반 대화로 *"에이전트 군단 가동해줘"*, *"병렬로 다 구현해줘"*, *"중간 검토 없이 무인으로 끝내줘"*라고 말씀하시면, 테르키르도는 **절대로 `legion-commander`를 자동 호출하지 않고** 다음과 같이 안내합니다:
     > *"주인님, 자동 검토 사령관(`legion-commander`) 체제는 안전을 위해 대화로는 자동 발동되지 않으며, 오직 `/agent-legion` (또는 `/legion`) 슬래시 명령으로만 가동됩니다. `/agent-legion` 명령으로 발동해 주시겠어요?"*
3. **물리적 훅 및 인덱서 잠금**:
   - `pre_tool_use_policy.py`: `invoke_subagent(TypeName="legion-commander")` 호출 시 프롬프트에 `/agent-legion`(또는 `/legion`) 토큰이 없거나, 실제 대화 트랜스크립트(`transcript.jsonl`)의 최신 `USER_INPUT`에 `/agent-legion`(또는 `/legion`)이 없으면 즉시 **`deny`**로 물리 차단합니다.
   - `skill_indexer.py`: 검색 쿼리에 `/agent-legion` 또는 `/legion`이 없으면 SAD 라우팅 후보에서 `agent-legion`을 자동 제외합니다.

---

## 1. 3-Tier Quad-Ralph Command Hierarchy (3계층 지휘 및 예속 계통도)

```text
[Master (주인님): "/agent-legion" 또는 "/legion" 슬래시 명령 입력]
                                  │
                                  ▼ (슬래시 명령 물리 검증 통과 시에만 기동)
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│             ⚔️ Legion Commander (자동 검토 사령관 / Meta-Review Supervisor)              │
│  - 전체 과업 DAG 분해 & 비충돌 파티셔닝 (`partition_validator.py`: Wave당 최대 4개 제한) │
│  - 하위에 `ralph-orchestrator`를 최대 4기(Quad-Ralph)까지 동시 병렬 생성 및 총괄 운용     │
│  - 각 랄프 에이전트의 결과물을 주인님 대신 무인 자동 검토 & 결함 시 즉시 Auto-Rework 지시 │
└──────┬──────────────────────────┬──────────────────────────┬──────────────────────────┬─┘
       │ (동시 생성·운용 #1)       │ (동시 생성·운용 #2)       │ (동시 생성·운용 #3)       │ (동시 생성·운용 #4)
       ▼ [Partition 1]            ▼ [Partition 2]            ▼ [Partition 3]            ▼ [Partition 4]
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│ralph-orchestrator│       │ralph-orchestrator│       │ralph-orchestrator│       │ralph-orchestrator│
│   (Ralph #1)     │       │   (Ralph #2)     │       │   (Ralph #3)     │       │   (Ralph #4)     │
└────────┬─────────┘       └────────┬─────────┘       └────────┬─────────┘       └────────┬─────────┘
         │ (산하 분대 운용)          │ (산하 분대 운용)          │ (산하 분대 운용)          │ (산하 분대 운용)
         ▼                          ▼                          ▼                          ▼
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│ [Ralph #1 Squad] │       │ [Ralph #2 Squad] │       │ [Ralph #3 Squad] │       │ [Ralph #4 Squad] │
│ • terukirdo-plan │       │ • terukirdo-plan │       │ • terukirdo-plan │       │ • terukirdo-plan │
│ • legion-worker  │       │ • legion-worker  │       │ • legion-worker  │       │ • legion-worker  │
│   / agy-worker   │       │   / agy-worker   │       │   / agy-worker   │       │   / agy-worker   │
│ • first-reviewer │       │ • first-reviewer │       │ • first-reviewer │       │ • first-reviewer │
│ • tech-expert    │       │ • tech-expert    │       │ • tech-expert    │       │ • tech-expert    │
│ • UFC & FAC      │       │ • UFC & FAC      │       │ • UFC & FAC      │       │ • UFC & FAC      │
└────────┬─────────┘       └────────┬─────────┘       └────────┬─────────┘       └────────┬─────────┘
         │                          │                          │                          │
         └──────────────────────────┴─────────────┬────────────┴──────────────────────────┘
                                                  │ (결함 시 사령관이 해당 Ralph #k에 무인 Auto-Rework 하달)
                                                  ▼ (전 파티션·Wave 완수 시)
                         ┌────────────────────────────────────────────────────────┐
                         │      Consolidated Universal Final Verification         │
                         │   (사령관 통합 빌드·전역 테스트·Git 무결성 직접 검증)    │
                         └────────────────────────────┬───────────────────────────┘
                                                      ▼
                                      [완결된 단일 Evidence Bundle 상신]
```

---

## 2. Four Immutable Legion Protocols (4대 불변 원칙)

### Protocol 1: Disjoint Partitioning & Max 4 Concurrency (비충돌 배타적 파티셔닝 & 최대 4기 동시 제한)
- 사령관(`legion-commander`)은 동시에 운용할 하위 `ralph-orchestrator` 파티션(Wave)을 구성할 때:
  1. **Wave당 동시 실행 파티션 수를 최대 4개(`MAX_CONCURRENT_RALPH = 4`)로 엄격히 제한**합니다. 파티션이 5개 이상인 경우 Wave 1(최대 4개), Wave 2(최대 4개) 형태로 순차 배치합니다.
  2. 동일 Wave 내 각 파티션의 `allowed_files` 교집합이 **반드시 공집합($\emptyset$)**이 되도록 분할합니다.
- 디스패치 전 반드시 `.agents/skills/agent-legion/scripts/partition_validator.py`를 실행하여 **동시 4기 이하 여부**와 **파일 충돌 0건**을 결정론적으로 검증합니다.

### Protocol 2: Quad-Ralph Concurrent Dispatch & Squad Execution (최대 4기 랄프 동시 생성 및 분대 운용)
- 사령관은 `invoke_subagent`로 **최대 4기의 `ralph-orchestrator`(Ralph #1 ~ #4)를 동시에 병렬 호출**합니다.
- 각각의 `ralph-orchestrator`는 배정받은 파티션 내부에서 독립적으로 자기 산하 분대(`terukirdo-plan` → `legion-worker`/`agy-worker` → `first-reviewer` → `tech-expert` → `universal-final-controller` → `final-approach-control`)를 생성·운용하여 구현과 검증을 수행합니다.

### Protocol 3: Autonomous Meta-Review & Auto-Rework Gate (사령관 무인 자동 검토 및 자동 재작업)
- 각 `ralph-orchestrator`가 자기 파티션의 구현 및 산하 검증관 판정 결과를 사령관에게 보고하면, 사령관이 주인님을 대신하여 무인으로 자동 검토(Meta-Review)합니다.
- **판정 및 무인 제어**:
  - **합격**: 해당 `ralph-orchestrator` 슬롯을 완료 승인하고, 대기 중인 다음 Wave 파티션이 있으면 즉시 투입합니다.
  - **불합격 (결함/테스트 실패/경계 누수)**: 사령관이 사람에게 묻지 않고 즉시 구체적인 Finding과 수정 지침을 내려 해당 `ralph-orchestrator`가 산하 워커와 검증관을 다시 돌려 **Auto-Rework**(동일 이슈 최대 3회)를 수행하도록 명령합니다.

### Protocol 4: Consolidated Universal Verification (최종 통합 물리 검증)
- 모든 Wave의 `ralph-orchestrator`들이 완수되면, 사령관이 최종적으로 프로젝트 전체 빌드, 전역 테스트 스위트, Git 작업 트리 무결성을 직접 실행(`run_command`)하여 파티션 간 통합 회귀 결함이 0건임을 보증한 뒤 주인님께 단일 Evidence Bundle로 보고합니다.

---

## 3. Step-by-Step Execution Flow (슬래시 명령 발동 시)

1. **Step 0 (슬래시 명령 확인 및 사령관 소환)**:
   - 주인님의 입력에 `/agent-legion` 또는 `/legion`이 있는지 확인 후, `invoke_subagent(TypeName="legion-commander", Prompt="[SLASH_TRIGGER: /agent-legion] ...")`로 소환.
2. **Step 1 (사령관 파티셔닝 및 최대 4기 동시/비충돌 물리 검증)**:
   ```powershell
   python .agents/skills/agent-legion/scripts/partition_validator.py partitions.json
   ```
3. **Step 2 (최대 4기 `ralph-orchestrator` 동시 생성 및 각 산하 분대 가동)**:
   - 사령관이 `Ralph #1` ~ `Ralph #4`를 동시 생성·운용하고, 각 랄프 에이전트가 자기 산하의 워커(`legion-worker`/`agy-worker`)와 각종 검증관(`first-reviewer`, `tech-expert`, `UFC`, `FAC`)을 가동.
4. **Step 3 (사령관 무인 자동 검토 & Auto-Rework)**:
   - 각 랄프 에이전트의 보고를 사령관이 자동 심사하고 결함 시 즉시 Auto-Rework 지시.
5. **Step 4 (최종 통합 검증 및 완료 상신)**:
   - 전 과정 무인 완주 후 통합 Evidence Bundle을 주인님께 일괄 보고.
