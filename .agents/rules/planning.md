# Planning & Spec-Lock Rules

## Core Directive

모든 Tier 2 및 Tier 3 개발 작업은 **모호성이 0%로 제거된 불변 기획서(SPEC-LOCKED)**가 수립되기 전까지 코드를 작성하지 않는다.

---

## 1. Ambiguity Ban (모호성 금지)

기획서 및 실행 카드(Execution Card) 작성 시 다음 주관적 단어의 사용을 전면 금지한다.

* 금지어 목록: `적당히`, `빠르게`, `알아서`, `유연하게`, `기타 등등`, `필요시`, `적절한`, `상황에 따라`
* 위 단어가 발견될 경우 기획 심사에서 즉시 거부(`REWORK REQUIRED`)된다.

---

## 2. Machine-Verifiable Acceptance Criteria (기계 검증 인수 조건)

모든 요구사항은 참(True)과 거짓(False)이 명확히 판정될 수 있는 `Given-When-Then` 형식으로 작성되어야 한다.

* **Given:** 사전 조건 (시스템 상태, 인증 여부, 데이터 존재 등)
* **When:** 실행 액션 (API 호출, 사용자 인터랙션, 이벤트 발생)
* **Then:** 기대 결과 (상태 코드, 반환 데이터, 상태 전이, 이벤트 발행)

---

## 3. Decision Binding (결정 바인딩)

* 아키텍처 및 비즈니스 트레이드오프는 에이전트가 임의로 결정하지 않는다.
* 반드시 사용자에게 A/B 선택지를 제시하고, 사용자의 명시적 선택(`확정 결정:`)을 받아 스펙에 고정한다.

---

## 4. Spec Lock Lifecycle

1. `DRAFT`: 소크라테스 인터뷰 및 기획 구체화 진행 중.
2. `LOCKED`: 사용자의 승인을 받아 단일 진실 공급원(`docs/specs/*.spec.md`)으로 고정됨.
3. `IMPLEMENTING`: Ralph Loop에 의해 구현 및 검증 진행 중.
4. `COMPLETED`: UFC 및 Final Control 통과 완료.
