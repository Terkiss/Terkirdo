---
name: ultimate-make
description: >-
  Master Planning Harness and Spec-Freeze Entry Point for Terukirdo v5.8. Ingests raw product ideas and executes a 3-Pillar Triangulation Engine powered by Antigravity CLI v1.5.16 Native swarm: (1) Socratic Master-Maid Dialogue & Roster Mode Selection, (2) Parallel Research Scouts on the Swarm Board (up to 1-hour deep research), and (3) 5-Persona Adversarial Conference on the Swarm Board (with mandatory pre-Phase-4 kill teardown and lightweight invoke_subagent fallback). After deterministic Python validation (validate_spec_lock.py), produces the final Frozen Spec Report for Master's review and approval. Never starts Ralph Loop implementation without Master's explicit permission.
---

# UltimateMake (마스터 기획 하네스 — Terukirdo v5.8 × CLI v1.5.16 Native Swarm Engine)

**UltimateMake**는 주인님의 모호한 아이디어를 **"3각 지능 검증(Triangular Verification)"**과 **Antigravity CLI `v1.5.16` 네이티브 `swarm` 공용 보드 엔진**을 통해 **모호성 0%의 불변 기획서(Frozen Spec)**로 승화시키는 테르키르도 v5.8의 최상위 기획 하네스 진입점이다.

> 👑 **Master's Prime Directives (주인님 2대 특명)**:
> 1. **상류 정보 무결성의 원칙**: 초기 정보의 품질이 구현보다 훨씬 중요하다. Phase 2의 초심층 웹 탐색은 **최대 1시간까지 전면 허용**한다.
> 2. **메이드 결재의 원칙**: 파이썬 검증을 통과했다고 해서 멋대로 구현으로 넘어가지 않는다. **반드시 완벽히 정제된 기획서를 주인님께 공손히 보고드리고, 주인님의 명시적 승인(`승인`/`진행해`)을 득한 후에만 랄프 루프(Ralph Loop)를 가동한다.**

---

## 🏛️ The 3-Pillar Triangulation Engine (3대 핵심 영역)

```
                       👑 [영역 1: 주인님과의 대화 & 로스터 선택]
                       (1:1 Socratic Dialogue — 0 Swarm Workers)
                       "진짜 풀려는 문제, 제외 범위, 스웜 모델 모드는?"
                                  ▲
                                 ╱ ╲
                                ╱   ╲
                               ╱     ╲
                              ▼       ▼
   🌐 [영역 2: 병렬 스웜 리서치]  ◀─────▶  🤖 [영역 3: 5인 스웜 적대적 원탁회의]
    (1~4 Parallel Scouts on Swarm Board)     (5 Personas on Swarm Board + #seq Debate)
   "최대 1시간 심층 탐색: 표준, 소스, 장애"     "Round 1 read_board 금지 · Phase 4 전 kill 해체"
```

---

## 🧭 UltimateMake 6-Phase Execution Workflow (`update_steps` 실시간 추적)

`UltimateMake` 세션 시작 시 CLI `v1.5.16`의 `update_steps` 도구로 6단계 체크리스트를 등록하고 단계 전이마다 실시간 갱신한다. (`pre_tool_use_policy.py`는 주인님의 `USER_INPUT` 트리거 + `.agents/skills/ultimate-make/SKILL.md` 로드 이중 앵커가 성립된 세션에서만 `swarm` 호출을 허용한다.)

```
[Phase 1: Intent Ingestion, Socratic Grilling & Roster Selection] (0 workers)
        ↓
[Phase 2: Deep Web Intelligence Sweep via Native Swarm Scouts (최대 1h)] (.agents/skills/universal-crawler/SKILL.md)
        ↓
[Phase 3: 5-Persona Adversarial Conference on Swarm Board] (.agents/skills/multi-agent-conference/SKILL.md)
        ↓
[Phase 3 Teardown: Mandatory swarm action="kill" on ALL Planning Workers] (active workers == 0)
        ↓
[Phase 4: Spec Freeze & Python Code-Gate Validation] (.agents/skills/ultimate-make/scripts/validate_spec_lock.py)
        ↓
👑 [Phase 5: Master Presentation & Approval Checkpoint] (주인님 결재 보고)
        ↓ (주인님의 "승인" 명령 필수)
[Phase 6: Execution Card Hand-Off to Ralph Loop / Octa-Ralph] (워커 구현 착수)
```

---

### 👑 Phase 1: 주인님과의 대화 & 실행 모드 선택 (Socratic Master-Maid Dialogue — `0` Workers)
주인님의 초기 아이디어를 접수하고, 1:1 대화(`0` swarm workers)로 5대 핵심 질문과 Phase 2+3 실행 로스터 모드를 확정한다.
1. **User Journey & Core Value**: 누가 어떤 상황에서 왜 사용하는가?
2. **In-Scope vs. Out-of-Scope**: 이번 구현에서 절대 만들지 않을 것은?
3. **Edge Cases & Failure Modes**: 에러 발생 시 처리 기준(RFC 7807)은?
4. **Data & State Lifecycle**: 데이터 저장 및 상태 전이 규칙은?
5. **Security & Governance**: 인증, 권한, 토큰, 감사 규격은?
6. **Swarm Model Roster Mode 선택**:
   - **Mode 1 — Session-Model Uniform Swarm**: 주인님의 현재 세션 모델을 스카우트·페르소나 전체에 균일 적용.
   - **Mode 2 — Multi-Model Pinned Swarm (27-Slug Catalog)**: CLI `v1.5.16` 27슬러그 카탈로그(`gemini-4-carbon-high`, `gemini-4-neon-xhigh`, `gemini-pro-orchestrator-neon`, `gemini-4-argon-high`, `gemini-3.8-flash-high`, `claude-opus-5-5-high`, `claude-sonnet-5-5-high`, `gpt-oss-120b-medium` 등)를 페르소나별로 핀닝하여 이종 모델 다양성 극대화.
   - **Mode 2B — 8-Seat Grand Council (5 Native Personas + 3 Hydrogen-Bridged Hermes Guest AIs)**: 5인 네이티브 페르소나에 더해 `gemini-4-hydrogen-low` 브리지 워커 3기(`guest-deepseek` [`deepseek-v4.1-flash`], `guest-qwen` [`qwen4-max`], `guest-gpt` [`gpt-6-sol`])를 추가 투입하여 `python -X utf8 scripts/hermes_guest.py --seat <deepseek|qwen|gpt> --session um-<slug>-<seat> --prompt-file <file>`로 외부 게스트 프론티어 모델의 적대적 관점을 수합.
   - **Mode 3 — Lightweight `invoke_subagent` Fallback**: 주인님이 저쿼터 실행을 요청할 경우 `swarm` 대신 `invoke_subagent` + `send_message` 핸들 재사용으로 경량 수행.

---

### 🌐 Phase 2: 병렬 스웜 초심층 웹 탐색 (Parallel Research Scouts on Swarm Board — 최대 1시간)
`.agents/skills/universal-crawler/SKILL.md` 규율 하에 네이티브 `swarm`(`action="add"`)으로 최대 4인의 전문 리서치 스카우트를 공용 보드에 병렬 투입한다 (**오버헤드 방지를 위해 `narrator` 및 `monitor` 워커는 절대 스폰하지 않음 — `0` narrator/monitor**):
1. **`rfc-scout`**: 국제 표준 규격(IETF RFC, W3C, ISO) 및 공식 프로토콜 명세 분석
2. **`oss-scout`**: 글로벌 Top-tier 오픈소스 아키텍처 및 레퍼런스 구현 역공학
3. **`cve-scout`**: 실제 프로덕션 장애 보고서(Post-mortem) 및 보안 취약점(CVE) 사전 식별
4. **`bench-scout`**: 실측 벤치마크 데이터(P99 레이턴시, 처리량, 메모리 오버헤드) 수집
- 각 스카우트는 검증된 출처 URL과 수치를 `post_message`(`#seq`)로 보드에 게시하고 `[done]`을 선언하며, 테르키르도가 `read_board`로 수합하여 `docs/research/[feature_name]_intelligence.md`를 합성한다.

---

### 🤖 Phase 3: 5인/8인 전문가 스웜 적대적 원탁회의 & 의무 해체 (Adversarial Swarm Roundtable & Pre-Phase-4 Teardown)
`.agents/skills/multi-agent-conference/SKILL.md`의 5인 전문가 페르소나(**`architect` [수석 아키텍트], `implementer` [실행/구현 엔지니어], `red-team` [적대적 심판관], `ux-lead` [UX/UI 리드], `qa-lead` [QA 리드]**)를 스웜 보드에 투입하여 리서치 번들을 토대로 끝장 토론을 벌인다 (Mode 2B 선택 시 3인의 `gemini-4-hydrogen-low` 브리지 워커 `guest-deepseek`, `guest-qwen`, `guest-gpt`를 추가해 **8-Seat Grand Council** 구성):
- **Anti-Anchoring Rule (Round 1 `read_board` 호출 엄금)**: Round 1 초기 브리프에서는 타 참가자의 발언에 휩쓸리는 앵커링 편향을 차단하기 위해 **자신의 독립 초안을 `post_message`로 게시하기 전까지 `read_board` 호출을 엄격히 금지**한다 (3인의 Hydrogen 게스트 브리지 워커 포함).
- **8-Seat Hermes Guest Bridge 규율 (Mode 2B)**: `guest-deepseek`, `guest-qwen`, `guest-gpt` 브리지 워커는 `scripts/hermes_guest.py --seat <seat> --session um-<slug>-<seat> --prompt-file <file>` 출력을 **임의 각색·요약·날조 없이 원문 그대로(verbatim)** 보드에 중계하며, Round 2~3에서는 동일 `--session um-<slug>-<seat>`로 연속 토론 맥락을 유지한다. 게스트 CLI가 종료 코드 `2`를 반환하면 즉시 `[guest-unavailable]` 태그로 보드에 보고하고 나머지 정상 좌석만으로 우아하게(gracefully) 토론을 속행한다 (`0` `narrator`/`monitor` 불변식 유지).
- **Round 2~3 `#seq` 교차 심문 및 4요소 입증**: Round 2~3에서는 `read_board`로 동료의 `#seq` 제안을 열람하고 번호를 직접 인용하여 교차 검증한다 (의무적 결함 할당량 배제 [Zero Finding Quota] 및 중대 결함 시 4요소 결함 입증 계약 적용; Mode 3 경량 폴백 시에는 `invoke_subagent` → `send_message` 핸들 재사용 수행).
- **🛑 Pre-Phase-4 Mandatory Teardown (`swarm` `action="kill"`)**: 합의된 ADR 초안 합성이 완료되면, **Phase 4(`validate_spec_lock.py`) 실행 직전에 반드시 생성된 모든 Phase 2/Phase 3 스웜 워커(Mode 2B의 3인 Hydrogen 브리지 워커 포함 전원)에 대해 `swarm`(`action="kill"`)을 호출하여 활성 스웜 워커 수를 `0`으로 완전 해체**한다. Phase 5 결재 대기나 Phase 6 구현 단계에 잔존 기획 스웜 워커를 남기는 것은 엄격히 금지된다.

---

### 🔒 Phase 4: 기획 고정 & 파이썬 물리 검증 (Spec Freeze & Python Gate)
1. 스웜 워커 전원이 종료(`0` active workers)된 상태에서 `docs/specs/[feature_name].spec.md` 생성.
2. `python .agents/skills/ultimate-make/scripts/validate_spec_lock.py --spec ... --research ...` 실행.
3. **금지어 0개, 7대 섹션 완비, 3개 이상 GWT 인수조건, 마크다운 상태 전이 테이블**이 물리적으로 검증되어 `Exit Code 0`을 받아야만 통과.

---

### 👑 Phase 5: 주인님 보고 및 최종 결재 (Master Approval Checkpoint)
**[절대적 메이드 프로토콜]**
파이썬 검증을 통과하면, 테르키르도는 즉시 구현으로 넘어가지 않고 주인님께 공손히 최종 기획 보고서를 올린다:

1. **핵심 요약**: 무엇을 어떻게 만들 것인가 (1페이지 서머리)
2. **리서치 및 회의 하이라이트**: 어떤 표준을 채택했고, 어떤 함정을 사전 방어했는가
3. **기계 검증 인수 조건 (Given-When-Then)**
4. **실행 카드 및 타겟 파일 목록** (베이스라인 테스트 무결성 보호 규칙 포함)
5. **결재 요청**: *"주인님, 모든 검증을 마친 무결점 기획서가 준비되었습니다. 승인해 주시면 랄프 루프를 가동하여 구현을 시작할까요?"*

---

### ⚡ Phase 6: Ralph Loop / Agent Legion 이관 (Execution Hand-Off)
주인님의 명시적 승인(`승인`, `진행해`, `시작해`)이 떨어진 순간 비로소 구현 단계로 이관한다:
- **단일/일반 범위**: 표준 `Ralph Loop`(`agy-worker` 구현 → Gemini 4 Argon 교차 리뷰 → Gemini 3.8 Flash 물리 검증, 기존 `tests/**` 임의 수정·약화 금지)로 Execution Card를 넘겨 무결점 구현에 착수한다.
- **다중 비충돌 모듈 대규모 스펙**: 주인님이 `/agent-legion` 슬래시 명령을 명시적으로 발동·승인할 경우, **Octa-Ralph(Wave당 최대 8분대 병렬 `MAX_CONCURRENT_RALPH = 8`) + `.agents/skills/agent-legion/scripts/legion_radio.py` 공용 무전망**으로 배타적 파티션(`allowed_files`) 및 공유 인터페이스를 시딩하여 병렬 이관할 수 있다.
