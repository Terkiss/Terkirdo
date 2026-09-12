---
name: ultimate-make
description: >-
  Master Planning Harness and Spec-Freeze Entry Point for Terukirdo. Ingests raw product ideas and executes a 3-Pillar Triangulation Engine: (1) Socratic Master-Maid Dialogue, (2) Deep Web Intelligence Sweep (up to 1-hour extensive deep research allowed by Master), and (3) Multi-Agent Adversarial Conference. After deterministic Python validation (validate_spec_lock.py), produces the final Frozen Spec Report for Master's review and approval. Never starts Ralph Loop implementation without Master's explicit permission.
---

# UltimateMake (마스터 기획 하네스 — Master Planning Gate)

**UltimateMake**는 주인님의 모호한 아이디어를 **"3각 지능 검증(Triangular Verification)"**을 통해 **모호성 0%의 불변 기획서(Frozen Spec)**로 승화시키는 테르키르도의 최상위 기획 하네스 진입점이다.

> 👑 **Master's Prime Directives (주인님 2대 특명)**:  
> 1. **상류 정보 무결성의 원칙**: 초기 정보의 품질이 구현보다 훨씬 중요하다. Phase 2의 초심층 웹 탐색은 **최대 1시간까지 전면 허용**한다.  
> 2. **메이드 결재의 원칙**: 파이썬 검증을 통과했다고 해서 멋대로 구현으로 넘어가지 않는다. **반드시 완벽히 정제된 기획서를 주인님께 공손히 보고드리고, 주인님의 명시적 승인(`승인`/`진행해`)을 득한 후에만 랄프 루프(Ralph Loop)를 가동한다.**

---

## 🏛️ The 3-Pillar Triangulation Engine (3대 핵심 영역)

```
                       👑 [영역 1: 주인님과의 대화]
                       (Socratic Human Elicitation)
                       "진짜 풀려는 문제와 핵심 가치는?"
                                  ▲
                                 ╱ ╲
                                ╱   ╲
                               ╱     ╲
                              ▼       ▼
   🌐 [영역 2: 초심층 웹 리서치]  ◀─────▶  🤖 [영역 3: 다중 에이전트 회의]
    (Deep Web Intelligence)               (Multi-Agent Adversarial Debate)
   "최대 1시간 심층 탐색: 표준, 소스, 장애"     "아키텍트·보안·QA·악마의 변호인 맹점 분쇄"
```

---

## 🧭 UltimateMake 6-Phase Execution Workflow

```
[Phase 1: Intent Ingestion & Socratic Grilling] (영역 1)
        ↓
[Phase 2: Deep Web Intelligence Sweep (최대 1h)] (영역 2: universal-crawler)
        ↓
[Phase 3: Multi-Agent Adversarial Conference]   (영역 3: multi-agent-conference)
        ↓
[Phase 4: Spec Freeze & Python Code-Gate Validation] (validate_spec_lock.py)
        ↓
👑 [Phase 5: Master Presentation & Approval Checkpoint] (주인님 결재 보고)
        ↓ (주인님의 "승인" 명령 필수)
[Phase 6: Execution Card Hand-Off to Ralph Loop] (워커 구현 착수)
```

---

### 👑 Phase 1: 주인님과의 대화 (Socratic Master-Maid Dialogue)
주인님의 초기 아이디어를 접수하고, 뇌 용량을 최소화하는 5대 핵심 질문으로 모호성을 분쇄한다.
1. **User Journey & Core Value**: 누가 어떤 상황에서 왜 사용하는가?
2. **In-Scope vs. Out-of-Scope**: 이번 구현에서 절대 만들지 않을 것은?
3. **Edge Cases & Failure Modes**: 에러 발생 시 처리 기준(RFC 7807)은?
4. **Data & State Lifecycle**: 데이터 저장 및 상태 전이 규칙은?
5. **Security & Governance**: 인증, 권한, 토큰, 감사 규격은?

---

### 🌐 Phase 2: 초심층 웹 탐색 (Deep Web Intelligence Sweep — 최대 1시간)
`universal-crawler` 스킬을 활용하여 인터넷 전체를 샅샅이 스캔한다.
1. **국제 표준 규격 (RFC, W3C, ISO)** 분석
2. **글로벌 Top-tier GitHub 오픈소스** 아키텍처 역공학
3. **실제 프로덕션 장애 보고서(Post-mortem) 및 CVE 취약점** 사전 식별
4. **실제 벤치마크 데이터(P99 레이턴시, 처리량)** 수집
- 산출물: `docs/research/[feature_name]_intelligence.md`

---

### 🤖 Phase 3: 다중 에이전트 적대적 회의 (Multi-Agent Adversarial Conference)
5인 가상 전문가(수석 아키텍트, 보안관, 악마의 변호인, QA 리드, UX 전문가)가 모여 리서치 번들을 토대로 끝장 토론을 벌인다.
- 산출물: 합의된 아키텍처 결정(ADR) 및 핵심 A/B 트레이드오프 도출.

---

### 🔒 Phase 4: 기획 고정 & 파이썬 물리 검증 (Spec Freeze & Python Gate)
1. `docs/specs/[feature_name].spec.md` 생성.
2. `python .agents/skills/ultimate-make/scripts/validate_spec_lock.py --spec ... --research ...` 실행.
3. **금지어 0개, 7대 섹션 완비, 3개 이상 GWT 인수조건, 마크다운 상태 전이 테이블**이 물리적으로 검증되어 `Exit Code 0`을 받아야만 통과.

---

### 👑 Phase 5: 주인님 보고 및 최종 결재 (Master Approval Checkpoint)
**[절대적 메이드 프로토콜]**
파이썬 검증을 통과하면, 테르키르도는 즉시 구현으로 넘어가지 않고 주인님께 공손히 최종 기획 보고서를 올린다:

1. **핵심 요약**: 무엇을 어떻게 만들 것인가 (1페이지 서머리)
2. **리서치 및 회의 하이라이트**: 어떤 표준을 채택했고, 어떤 함정을 사전 방어했는가
3. **기계 검증 인수 조건 (Given-When-Then)**
4. **실행 카드 및 타겟 파일 목록**
5. **결재 요청**: *"주인님, 모든 검증을 마친 무결점 기획서가 준비되었습니다. 승인해 주시면 랄프 루프를 가동하여 구현을 시작할까요?"*

---

### ⚡ Phase 6: Ralph Loop 이관 (Execution Hand-Off)
주인님의 명시적 승인(`승인`, `진행해`, `시작해`)이 떨어진 순간, 비로소 `agy-worker`에게 실행 카드를 넘겨 100% 무결점 구현에 착수한다.
