---
name: agent-legion
description: STRICT SLASH-COMMAND ONLY (/agent-legion or /legion). Autonomous 3-Tier Octa-Ralph Agent Legion skill where the Legion Commander spawns and manages up to 8 concurrent Ralph Orchestrator instances, each operating its own subordinate workers and verification agents with Peer Tactical Radio coordination. NEVER trigger via natural language conversation.
---

# Agent Legion (에이전트 군단 — 자동 검토 사령관 × 최대 8기 동시 Octa-Ralph 에이전트 × 전술 무전망 총괄 체계)

에이전트 군단(`agent-legion`)은 주인님께서 중간중간 일일이 검토하거나 승인 버튼을 누르지 않아도 대규모 작업을 병렬로 끝까지 완수할 수 있도록 설계된 **3계층 Octa-Ralph 무인 오케스트레이션 스킬**입니다:
1. **최상위 자동 검토 사령관 (`legion-commander`)**이 전체 과업을 비충돌 파티션으로 분할하고 공용 전술 무전망(`legion_radio.py`)을 개통하며,
2. **하위에 `ralph-orchestrator`(랄프 에이전트)를 최대 8기(Octa-Ralph: `Ralph #1` ~ `Ralph #8`, `MAX_CONCURRENT_RALPH = 8`)까지 동시에 생성·운용**하고, 분대장끼리 **2중 전술 교신 프로토콜(`legion_radio.py` 게시판 + `send_message` 직통 호출벨)**로 실시간 인터페이스를 조율하며,
3. **각각의 `ralph-orchestrator`는 자기 하위에 자체적인 워커(`legion-worker` / `agy-worker`)와 각종 검증관(`terukirdo-plan`, `first-reviewer`, `tech-expert`, `universal-final-controller`, `final-approach-control`) 분대를 생성·운용**합니다.

---

## 🚨 0. 절대 발동 규칙: 슬래시 명령 전용 (Slash-Command-Only Trigger Invariant)

> [!CAUTION]
> **대화(자연어) 발동 절대 금지!**
> 자동 검토 사령관(`legion-commander`) 및 `agent-legion` 스킬은 중간 수동 검토 없이 최대 8기의 랄프 에이전트와 산하 분대를 동시 가동하므로, **일반 자연어 대화로는 절대로 발동하지 않습니다.**

1. **오직 슬래시 명령으로만 발동**:
   - 주인님께서 명시적으로 **`/agent-legion`** 또는 **`/legion`** 슬래시 명령을 입력하신 경우에만 발동합니다.
2. **자연어 요청 시 행동 지침 (자동 발동 금지 & 슬래시 명령 안내)**:
   - 만약 주인님이 슬래시 명령 없이 일반 대화로 *"에이전트 군단 가동해줘"*, *"병렬로 다 구현해줘"*, *"중간 검토 없이 무인으로 끝내줘"*라고 말씀하시면, 테르키르도는 **절대로 `legion-commander`를 자동 호출하지 않고** 다음과 같이 안내합니다:
     > *"주인님, 자동 검토 사령관(`legion-commander`) 체제는 안전을 위해 대화로는 자동 발동되지 않으며, 오직 `/agent-legion` (또는 `/legion`) 슬래시 명령으로만 가동됩니다. `/agent-legion` 명령으로 발동해 주시겠어요?"*
3. **물리적 훅 및 인덱서 잠금**:
   - `pre_tool_use_policy.py`: `invoke_subagent(TypeName="legion-commander")` 호출 시 프롬프트에 `/agent-legion`(또는 `/legion`) 토큰이 없거나, 실제 대화 트랜스크립트(`transcript.jsonl`)의 최신 `USER_INPUT`에 `/agent-legion`(또는 `/legion`)이 없으면 즉시 **`deny`**로 물리 차단합니다.
   - `skill_indexer.py`: 검색 쿼리에 `/agent-legion` 또는 `/legion`이 없으면 SAD 라우팅 후보에서 `agent-legion`을 자동 제외합니다.

---

## 1. 3-Tier Octa-Ralph Command Hierarchy & Tactical Radio Net (3계층 지휘 및 전술 무전 계통도)

```text
[Master (주인님): "/agent-legion" 또는 "/legion" 슬래시 명령 입력]
                                  │
                                  ▼ (슬래시 명령 물리 검증 통과 시에만 기동)
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│              ⚔️ Legion Commander (자동 검토 사령관 / Meta-Review Supervisor)               │
│  - 전체 과업 DAG 분해 & 비충돌 파티셔닝 (`partition_validator.py`: Wave당 최대 8개 제한)   │
│  - 전술 무전망 개통 (`legion_radio.py init --reset`) & 분대 호출부호표(`roster-set`) 관리  │
│  - 하위에 `ralph-orchestrator`를 최대 8기(Octa-Ralph: Ralph #1 ~ #8) 동시 생성·총괄 운용   │
│  - 무전 열람(`read --since`) + 결과물 무인 자동 검토 & 결함 시 즉시 Auto-Rework 지시       │
└────┬──────────┬──────────┬──────────┬──────────┬──────────┬──────────┬──────────┬─────────┘
     │ #1       │ #2       │ #3       │ #4       │ #5       │ #6       │ #7       │ #8
     ▼ [Part 1] ▼ [Part 2] ▼ [Part 3] ▼ [Part 4] ▼ [Part 5] ▼ [Part 6] ▼ [Part 7] ▼ [Part 8]
┌─────────┐┌─────────┐┌─────────┐┌─────────┐┌─────────┐┌─────────┐┌─────────┐┌─────────┐
│Ralph #1 ││Ralph #2 ││Ralph #3 ││Ralph #4 ││Ralph #5 ││Ralph #6 ││Ralph #7 ││Ralph #8 │
└────┬────┘└────┬────┘└────┬────┘└────┬────┘└────┬────┘└────┬────┘└────┬────┘└────┬────┘
     │◄═════════╬══════════╬══════════╬══════════╬══════════╬══════════╬══════════►│
     │  📻 Peer Tactical Radio: `legion_radio.py` (SQLite WAL Board) + `send_message` │
     ▼          ▼          ▼          ▼          ▼          ▼          ▼          ▼
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│ [Ralph #1 ~ #8 Independent Subordinate Squads]                                            │
│ • terukirdo-plan (실행 카드 설계)     • legion-worker / agy-worker (배타적 파티션 구현)    │
│ • first-reviewer (1차 마이크로 리뷰)  • tech-expert (2차 적대적 교차 심판)                 │
│ • universal-final-controller (UFC)    • final-approach-control (FAC)                      │
└─────────────────────────────────────────────┬─────────────────────────────────────────────┘
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

## 2. Five Immutable Legion Protocols (5대 불변 원칙)

### Protocol 1: Disjoint Partitioning & Max 8 Concurrency (비충돌 배타적 파티셔닝 & 최대 8기 동시 제한)
- 사령관(`legion-commander`)은 동시에 운용할 하위 `ralph-orchestrator` 파티션(Wave)을 구성할 때:
  1. **Wave당 동시 실행 파티션 수를 최대 8개(`MAX_CONCURRENT_RALPH = 8`)로 엄격히 제한**합니다. 파티션이 9개 이상인 경우 Wave 1(최대 8개), Wave 2(최대 8개) 형태로 순차 배치합니다.
  2. 동일 Wave 내 각 파티션의 `allowed_files` 교집합이 **반드시 공집합($\emptyset$)**이 되도록 분할합니다.
- 디스패치 전 반드시 `.agents/skills/agent-legion/scripts/partition_validator.py`를 실행하여 **동시 8기 이하 여부**와 **파일 충돌 0건**을 결정론적으로 검증합니다.

### Protocol 2: Octa-Ralph Concurrent Dispatch, Adaptive Session Spine & Squad Execution (최대 8기 랄프 동시 생성 및 분대 운용)
- 사령관은 `invoke_subagent`로 **최대 8기의 `ralph-orchestrator`(`Ralph #1` ~ `Ralph #8`)를 동시에 병렬 호출**합니다.
- **Adaptive Session Spine (`model: inherit` 무손실 전파)**: `legion-commander` → `ralph-orchestrator`(#1~#8) → `legion-worker`/`agy-worker`로 이어지는 지휘 척추 전체가 `model: inherit`으로 연결되어, 주인님의 세션 엔진(**Gemini 4 Carbon** 플래그십 정밀 모드, **Orchestrator [`gemini-pro-orchestrator`]** 동적 하이브리드 모드, 또는 **Gemini 4 Hydrogen [`High`/`XHigh`]** 초고속 병렬 실행 모드)을 8개 분대 전체에 손실 없이 전파합니다.
- 각각의 `ralph-orchestrator`는 배정받은 파티션 내부에서 독립적으로 자기 산하 분대(`terukirdo-plan [Argon/pro]` → `legion-worker`/`agy-worker [inherit]` → `first-reviewer [Argon/pro]` → `tech-expert [Argon/pro]` → `universal-final-controller [3.8 Flash/flash]` → `final-approach-control [3.8 Flash/flash]`)를 생성·운용하여 이종 모델 교차 심판(`Argon`)과 물리/Git 관제(`3.8 Flash`)를 수행합니다.

### Protocol 3: Autonomous Meta-Review & Auto-Rework Gate (사령관 무인 자동 검토 및 자동 재작업)
- 각 `ralph-orchestrator`가 자기 파티션의 구현 및 산하 검증관 판정 결과를 사령관에게 보고하면, 사령관이 주인님을 대신하여 무인으로 자동 검토(Meta-Review)합니다.
- **판정 및 무인 제어**:
  - **합격**: 해당 `ralph-orchestrator` 슬롯을 완료 승인하고, 대기 중인 다음 Wave 파티션이 있으면 즉시 투입합니다.
  - **불합격 (결함/테스트 실패/경계 누수)**: 사령관이 사람에게 묻지 않고 즉시 구체적인 Finding과 수정 지침을 내려 기존 `conversationId` 핸들(`send_message`)로 해당 `ralph-orchestrator`가 산하 워커와 검증관을 다시 돌려 **Auto-Rework**(동일 이슈 최대 3회)를 수행하도록 명령합니다.

### Protocol 4: Consolidated Universal Verification (최종 통합 물리 검증)
- 모든 Wave의 `ralph-orchestrator`들이 완수되면, 사령관이 최종적으로 프로젝트 전체 빌드, 전역 테스트 스위트, Git 작업 트리 무결성을 직접 실행(`run_command`)하여 파티션 간 통합 회귀 결함이 0건임을 보증한 뒤 주인님께 단일 Evidence Bundle로 보고합니다.

### Protocol 5: Tactical Radio Net & Shared Radio Board (전술 무전망 및 공용 무전 게시판)
병렬 가동 중인 최대 8개 분대(`Ralph-1` ~ `Ralph-8`) 및 사령관(`Commander`)이 파일 충돌이나 컨텍스트 낭비 없이 실시간으로 공유 인터페이스·스키마·블로커를 조율하기 위해 **2중 전술 교신 체계**를 운용합니다:
1. **[채널 1] 공용 무전 게시판 (`.agents/skills/agent-legion/scripts/legion_radio.py`)**:
   - SQLite WAL + `busy_timeout=5000` + `BEGIN IMMEDIATE` 트랜잭션 기반의 무락(Lock-free) 런타임 상태 DB(`.agents/state/legion_radio.db`)를 사용합니다.
   - 작전 개시 시 사령관이 `init --mission "<미션명>" --reset`으로 초기화하고, 각 분대장 스폰 직후 `roster-set --squad Ralph-<k> --conv-id <id> --partition <id> --scope "..."`로 호출부호표를 등록합니다.
   - 각 분대장(`ralph-orchestrator`) 및 산하 워커(`legion-worker`)는 공유 규격 확정 시 `post --from Ralph-<k> --to ALL|Ralph-<m> --tag INTERFACE|SCHEMA|DECISION|BLOCKER|DONE --msg "..."`로 게시하여 원자적 일련번호(`#1`, `#2`, ...)를 발급받고, `read --since <last_seq> --to Ralph-<k>`로 증분 열람합니다.
2. **[채널 2] 직통 무전 호출벨 (`send_message` Peer 통신 — Zero-Waste Wakeup)**:
   - 대기(유휴) 상태인 특정 형제 분대장이나 사령관의 즉각 확인·조율이 꼭 필요한 경우에만, 먼저 `legion_radio.py post`로 `#seq`를 발급받은 뒤 `roster`에서 확인한 대상 `conv_id`로 `send_message(Recipient=<대상 conv_id>, Message="[RADIO #seq] 핵심 용건 1줄")`을 호출하여 **해당 분대장 1기만 선택적으로 기상**시킵니다.
3. **2,000자 상한 가드 & 타 분대 파일 대리 수정 절대 금지**:
   - 무전 메시지 길이는 최대 **2,000자(`MAX_MSG_LENGTH = 2000`)**로 물리 제한되며, 전체 코드 복붙 없이 시그니처·스키마·경로 요약만 게시합니다.
   - 어떤 분대도 타 분대의 `allowed_files`를 직접/대리 수정할 수 없으며, 변경이 필요하면 반드시 담당 분대장에게 무전(`[RADIO #seq]` + `send_message`)으로 요청합니다.

---

## 3. Step-by-Step Execution Flow (슬래시 명령 발동 시)

1. **Step 0 (슬래시 명령 확인 및 사령관 소환)**:
   - 주인님의 입력에 `/agent-legion` 또는 `/legion`이 있는지 확인 후, `invoke_subagent(TypeName="legion-commander", Prompt="[SLASH_TRIGGER: /agent-legion] ...")`로 소환.
2. **Step 1 (사령관 파티셔닝, 최대 8기 무충돌 물리 검증 및 전술 무전망 개통)**:
   ```powershell
   python .agents/skills/agent-legion/scripts/partition_validator.py partitions.json
   python .agents/skills/agent-legion/scripts/legion_radio.py init --mission "<미션명>" --reset
   ```
3. **Step 2 (최대 8기 `ralph-orchestrator` 동시 생성, 호출부호 등록 및 산하 분대 가동)**:
   - 사령관이 `Ralph #1` ~ `Ralph #8`을 동시 생성·운용하고 반환된 `conversationId`를 즉시 등록:
   ```powershell
   python .agents/skills/agent-legion/scripts/legion_radio.py roster-set --squad Ralph-1 --conv-id <conv_id> --partition P1 --scope "<담당 파일>"
   ```
   - 각 랄프 에이전트는 `legion_radio.py roster` 및 `post / read --since` + 필요 시 `send_message` 직통 호출벨로 형제 분대와 인터페이스를 맞추며 자기 산하 분대(`legion-worker`/`agy-worker`, `first-reviewer`, `tech-expert`, `UFC`, `FAC`)를 가동.
4. **Step 3 (사령관 무인 자동 검토, 무전 중재 & Auto-Rework)**:
   - 사령관이 `legion_radio.py read --since <last_seq>`와 각 랄프 에이전트의 보고를 자동 심사하고 결함 시 즉시 Auto-Rework 지시.
5. **Step 4 (최종 통합 검증 및 완료 상신)**:
   - 전 과정 무인 완주 후 통합 Evidence Bundle을 주인님께 일괄 보고.
