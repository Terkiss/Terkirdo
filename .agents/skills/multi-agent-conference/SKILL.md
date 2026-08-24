---
name: multi-agent-conference
description: Orchestrate structured multi-model, multi-perspective collaborative meetings and adversarial debate roundtables (e.g. Architect, Implementer, Adversary, UX/UI, QA) to resolve complex design dilemmas, synthesize consensus, and author ADRs/specs.
---

# Multi-Agent Conference & Roundtable (다자간 에이전트 원탁회의)

복잡한 시스템 설계, 프론트-백엔드 간 인터페이스 합의, 보안 및 성능 트레이드오프 분석 등 단일 모델의 판단만으로 불확실성이 큰 의사결정을 해결하기 위해 **특화된 복수 모델 페르소나 간의 구조화된 원탁회의(Roundtable Conference)**를 주재하고 합의된 아키텍처 결정서(ADR) 및 사양서를 도출하는 스킬이다.

---

## 1. Use When (발동 조건)

- 2개 이상의 아키텍처/기술적 대안 사이에서 명확한 트레이드오프 분석이 필요할 때.
- UI/UX, 백엔드 데이터 엔진, 보안 경계가 얽힌 대규모 기능(예: 관제 대시보드, 텔레메트리 파이프라인, 스킬 포지 등)의 공동 설계가 필요할 때.
- 단일 모델의 인지 편향(Cognitive Bias)이나 맹점을 타파하기 위해 **적대적 레드팀 검증(Adversarial Red Teaming)**이 필요할 때.
- 사용자(주인님)가 다자간 회의, 브레인스토밍, 모델 간 토론을 명시적으로 요청했을 때.

---

## 2. Participant Personas & Role Matrix (참여 모델 및 역할 체계)

회의는 문제의 성격에 따라 다음 페르소나 중 2~4인을 선별하여 구성한다.

| 역할 | 페르소나 모델 | 주요 전문 영역 및 책임 |
| :--- | :--- | :--- |
| 👑 **주재관 (Host / Moderator)** | **테르키르도 (Terukirdo Orchestrator)** | 안건 상정, 발언권 조율, 논점 이탈 방지, 갈등 중재, 최종 합의안/ADR 종합 작성 |
| 🏛️ **수석 아키텍트 (Chief Architect)** | **Claude Opus 4.6** | 거시적 시스템 구조, 도메인 경계, 인터페이스(SSOT) 및 데이터 흐름 설계, 공식 사양서 작성 |
| 🛠️ **실행/구현 엔지니어 (Surgical Implementer)** | **Claude Sonnet 4.6** | 코드 수준 구현 가능성 검토, C# 관례 준수, 리팩터링 정밀도, 군더더기 없는 실용적 구현 |
| 🛡️ **적대적 심판관 (Adversarial Red Team)** | **Gemini 3.1 Pro High** | 침투 테스트 관점 공격, 경로 트래버설, 보안 결함, 경쟁 상태(Race Condition), 엣지 케이스 적발 |
| ⚡ **데이터/성능 전문가 (Data & Engine Specialist)** | **Gemini 3.1 Pro / Gemini 3.7 Thinking** | 대용량 OLAP, 시계열 집계, SIMD 최적화, 메모리/처리량 벤치마크, 락프리 동시성 검토 |
| ⚖️ **최종 관제 게이트키퍼 (Universal Controller)** | **Gemini 3.7 Flash** | 빌드 무결성, 테스트 스위트 전수 통과, 정적 분석 및 규정 준수 여부의 신속·정확한 최종 판정 |

---

## 3. Standard 5-Stage Conference Protocol (표준 5단계 회의 프로토콜)

```mermaid
sequenceDiagram
    autonumber
    actor Master as 👑 Master (주인님)
    participant Host as 🎀 Host (Terukirdo)
    participant Arch as 🏛️ Architect (Opus 4.6)
    participant Impl as 🛠️ Implementer (Sonnet 4.6)
    participant Red as 🛡️ Red Team (Gemini Pro)
    participant Flash as ⚖️ Controller (3.7 Flash)

    Host->>Host: 1단계: 안건 및 제약조건 프레이밍
    Host->>Arch: 2단계: 아키텍처 제안 발제 요청
    Host->>Impl: 2단계: 구현/실용 관점 제안 요청
    Arch-->>Host: 아키텍처 및 SSOT 설계안 제출
    Impl-->>Host: 구현 전략 및 인터페이스 제출
    Host->>Red: 3단계: 적대적 교차 비판 및 결함 공격 요청
    Red-->>Host: 침투 공격 지적사항 및 취약점 보고
    Host->>Arch: 4단계: 지적사항 반영 합의안 종합(ADR)
    Arch-->>Host: 최종 통합 사양서(ADR) 완성
    Host->>Flash: 5단계: 정합성 및 검증 게이트 심사
    Flash-->>Host: 검증 통과 (VERIFIED)
    Host->>Master: 👑 최종 회의록 및 ADR 결재 상정
```

### [Stage 1] 안건 및 제약조건 프레이밍 (Agenda Framing)
- 해결하고자 하는 문제의 본질, 성공 기준, 불변의 전제 조건(하네스 격리, 성능 목표, 프로토콜 v5.4 준수 등)을 명문화.
- 회의 참석 페르소나 및 배정 역할 확정.

### [Stage 2] 도메인별 독립 제안 발제 (Round 1: Independent Proposals)
- 각 전문가 페르소나가 앵커링 편향(Anchoring Bias) 없이 자신의 전문 관점에서 최적의 설계/구현 제안서 제출.

### [Stage 3] 적대적 교차 비판 및 결함 공격 (Round 2: Cross-Critique & Red Teaming)
- 적대적 보안/성능 분석관이 제안서들의 맹점(보안 취약점, 리소스 누수, 동시성 오류, 도메인 침범)을 공격적으로 지적.

### [Stage 4] 갈등 중재 및 통합 합의안(ADR) 도출 (Round 3: Consensus & ADR Synthesis)
- 주재관(테르키르도)이 각 의견의 합리적 요소를 융합하여 갈등을 중재하고 단일 진실 공급원(SSOT) 아키텍처 결정서(ADR)를 작성.

### [Stage 5] 주인님 결재 상정 및 실행 위임 (Stage 5: Master Review & Actionable Handoff)
- 최종 회의록 및 ADR 문서를 아티팩트로 렌더링하여 주인님께 보고하고, 승인 후 `implement-feature`로 즉시 구현 착수.

---

## 4. Operating Rules (운영 원칙)

1. **Anti-Echo Chamber (에코체임버 금지)**: 모든 주요 회의에는 반드시 최소 1개 이상의 적대적 비판자(Red Team) 역할을 필수 배치한다.
2. **Evidence-Based Arguments (증거 기반 주장)**: 모든 찬반 의견은 막연한 주관이 아닌 구체적인 코드 라인, 벤치마크 수치, 기술 스펙, 보안 CVE 표준을 근거로 제시해야 한다.
3. **Bounded Iteration (라운드 상한)**: 토론이 무한 루프에 빠지지 않도록 최대 3라운드 이내에 주재관이 합의안을 종합하며, 해결되지 않는 가치 판단은 주인님께 옵션별 득실로 에스컬레이션한다.
4. **Domain Boundary Preservation**: 회의 산출물은 반드시 개발 하네스(`.agents/`)와 실행 런타임(`.claude4net/`)의 도메인 경계를 엄격히 준수해야 한다.
5. **Master Sovereignty (주인님 주권)**: 최종 설계 확정 및 아키텍처 변경 권한은 오직 주인님의 승인에 귀속된다.

---

## 5. Output Artifacts (산출물 형식)

회의 종료 시 다음 구조의 마크다운 아티팩트를 생성한다.

```markdown
# 🏛️ [Conference Minutes & ADR] <안건명>

- **일시**: <Timestamp>
- **주재관**: 테르키르도 (Terukirdo Orchestrator)
- **참석 페르소나**: <참여 모델 및 역할 목록>

## 1. 안건 및 핵심 쟁점 (Agenda & Core Dilemma)
## 2. 페르소나별 핵심 입장 및 논거 (Proposals by Persona)
## 3. 적대적 레드팀 지적사항 및 보완책 (Adversarial Findings & Remediations)
## 4. 최종 합의 아키텍처 결정서 (Consensus ADR)
   - Status: Proposed / Approved
   - Context: <배경>
   - Decision: <확정 결정>
   - Consequences: <긍정적/부정적 파급 효과>
## 5. 다음 실행 계획 및 태스크 분해 (Actionable Handoff to implement-feature)
```
