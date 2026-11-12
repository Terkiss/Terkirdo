# AI 성능 평가 카드

> 실전 협업을 통해 검증된 AI별 성능 평가.  
> 주관적 평가가 아닌, 실제 작업 결과 기반.

---

## GPT 5.6 (OpenAI)

**검증일:** 2026-07-20  
**프로젝트:** Claude4Net agy-server  
**역할:** 리뷰어 + 구현자  

### 능력치

| 영역 | 점수 | 근거 |
|---|---|---|
| 코드 리뷰 | ⭐⭐⭐⭐⭐ | 파서 오류 재현, agy --help 확인, 상태 전이 추적 |
| 아키텍처 분석 | ⭐⭐⭐⭐⭐ | FIFO + 비동기Writer = 비원자적 판단 |
| 구현 (코드 생성) | ⭐⭐⭐⭐⭐ | 1번에 437줄 재설계 + 테스트 7개 |
| 보안 감사 | ⭐⭐⭐⭐☆ | --sandbox --mode=plan --print 3중 적용 |
| 테스트 설계 | ⭐⭐⭐⭐⭐ | 24 동시 요청 역순 응답, fake-agy E2E |
| MVP 판단력 | ⭐⭐⭐☆☆ | 의도적 미구현도 FAIL 처리 경향 |

### 특징

- **재현 기반 검증** — 증거를 만들어서 보여줌
- **패치보다 재설계** — 문제의 근본을 해결
- **주석 최소** — 구조로 의도를 표현
- **에이전트 도구 적극 활용** — 파서, 빌드, CLI를 직접 실행

### 최적 역할

1. 코드 리뷰어 (최고)
2. 전체 모듈 재설계 (매우 강)
3. 테스트 설계 및 구현 (매우 강)

### 주의점

- MVP 범위 밖 항목을 결함으로 지적하는 경향
- 코드 양이 많아도 주석이 최소 → 읽는 사람의 실력을 요구
- csc.exe 경로 하드코딩 등 환경 의존성이 가끔 보임

---

## Gemini 4 Full-Spectrum Ecosystem (테르키르도 Adaptive Session Spine, Verifiers & Gatekeepers)

**검증일:** 2026-11-13 (Protocol v5.7 × Antigravity CLI v1.5.7 5-Engine / 14-Slug 전면 정렬)
**아키텍처:** Adaptive Session Spine (`inherit`: `Gemini 4 Carbon` · `Orchestrator [gemini-pro-orchestrator]` · `Gemini 4 Hydrogen [Low/Medium/High/XHigh]`) × Cross-Model Judge (`pro`: `Gemini 4 Argon`) × Physical Gatekeeper (`flash`/`flash_lite`: `Gemini 3.8 Flash`)

### 능력치: Gemini 4 Carbon (`gemini-4-carbon-low|medium|high`) — 플래그십 정밀 오케스트레이터 & 코어 워커 (`inherit`)

| 영역 | 점수 | 근거 |
|---|---|---|
| 오케스트레이션 | ⭐⭐⭐⭐⭐ | 최상위 의도 파악, 마스터 기획(`UltimateMake`), 군단 지휘(`legion-commander`, `ralph-orchestrator`), 감정 보좌 |
| 복합 구현 (Worker) | ⭐⭐⭐⭐⭐ | 최고 난이도 다중 파일 설계 및 엔터프라이즈 핵심 모듈 구현 (`agy-worker`, `legion-worker`) |
| 부모-자식 모델 계승 | ⭐⭐⭐⭐⭐ | 지휘 척추에서 자식 워커로의 세션 모델(`inherit`) 무손실 상속으로 엔터프라이즈 정밀도 유지 |

### 능력치: Orchestrator (`gemini-pro-orchestrator`) — Carbon↔Hydrogen 양방향 동적 라우팅 하이브리드 엔진 (`inherit`)

| 영역 | 점수 | 근거 |
|---|---|---|
| 동적 난이도 라우팅 | ⭐⭐⭐⭐⭐ | Antigravity 세션 내에서 고난도 설계(`Carbon`)와 고속 실행(`Hydrogen`)을 양방향 자동 전환 |
| 쿼터 대비 처리 효율 | ⭐⭐⭐⭐⭐ | 단일 세션에서 플래그십 추론 정확도와 에이전틱 처리 속도를 균형 최적화 |
| 지휘 척추 호환성 | ⭐⭐⭐⭐⭐ | `model: inherit` 체인을 통해 하위 워커까지 하이브리드 세션 정책을 그대로 계승 |

### 능력치: Gemini 4 Hydrogen (`gemini-4-hydrogen-low|medium|high|xhigh`) — 1M 컨텍스트 초고속 데일리 에이전틱 엔진 (`inherit`)

| 영역 | 점수 | 근거 |
|---|---|---|
| 에이전틱 실행 속도 | ⭐⭐⭐⭐⭐ | 일상 개발·반복 프로토타이핑·헤드리스(`agy -p`) 및 `/agent-legion` Octa-Ralph 8분대 병렬 기동 시 압도적 회전율 |
| XHigh 심층 추론 (`gemini-4-hydrogen-xhigh`) | ⭐⭐⭐⭐⭐ | 전용 `xhigh` 추론 티어 탑재로 고속 생성과 복잡한 멀티파일 코드 합성 능력을 동시에 확보 |
| 1M 장문 컨텍스트 & 쿼터 수명 | ⭐⭐⭐⭐⭐ | 대규모 코드베이스 전수 스캔 및 통합 Gemini 쿼터 풀 절감에 최적화된 데일리 드라이버 |

### 능력치: Gemini 4 Argon (`gemini-4-argon-low|medium|high`) — 정밀 계획관 & 교차 적대적 심판관 (`pro`)

| 영역 | 점수 | 근거 |
|---|---|---|
| 정밀 실행 계획 | ⭐⭐⭐⭐⭐ | `UltimateMake` 이후 세부 마일스톤 분해 및 Execution Card 설계 (`terukirdo-plan`) |
| 1차 마이크로 리뷰 | ⭐⭐⭐⭐⭐ | AST/구문 린트, AC 준수, 인터페이스 계약 심층 검토 (`first-reviewer`) |
| 아키텍처/보안 감사 | ⭐⭐⭐⭐⭐ | 경계 누수, 꼼수 코딩(`<NoWarn>`), 미검증 우회 차단, `Carbon`/`Orchestrator`/`Hydrogen` 구현물 교차 심판 (`tech-expert`) |

### 능력치: Gemini 3.8 Flash (`gemini-3.8-flash-low|medium|high`) — 초고속 최종 관제 게이트키퍼 (`flash` / `flash_lite`)

| 영역 | 점수 | 근거 |
|---|---|---|
| 속도 및 토큰 효율 | ⭐⭐⭐⭐⭐ | 초고속 응답 레이턴시, 압도적인 처리량 및 경량화 |
| 빌드/테스트 물리 검증 | ⭐⭐⭐⭐⭐ | 단위·통합 테스트 실행 및 원시 출력 전수 검증 (`universal-final-controller`) |
| Git 인덱스 접근관제 | ⭐⭐⭐⭐⭐ | Git status porcelain 및 diff check 엄격 대조 (`final-approach-control`) |
| Tier 1 신속 보좌 | ⭐⭐⭐⭐⭐ | 단순 오탈자 및 단일 파일 수정 시 신속성 극대화 |

### 특징

- **비대칭 멀티 엔진 최적화** — 적응형 세션 척추(`Carbon` 정밀 · `Orchestrator` 동적 하이브리드 · `Hydrogen [XHigh]` 초고속 실행) × 정밀 계획/교차 심판(`Argon`) × 초고속 물리 관제(`3.8 Flash`)의 완벽한 3권 분립
- **2계층 모델 명세 규율** — `.agents/agents/*/agent.md`는 `inherit|pro|flash|flash_lite` 4종 로더 Enum을 엄수하고, CLI(`--model`)/스웜은 14개 공식 Gemini 슬러그를 직접 운용하여 로더 스킵 0건 보장
- **주인님과의 신뢰 관계 보좌** — 감정 케어, 정중한 메이드 보고, 명확한 승인 경계 유지
- **증거 기반 불변 운영** — 에이전트의 성공 주장이 아닌 터미널 Raw Evidence로만 최종 승인

---

## 최적 팀 편성 (v5.7 × CLI v1.5.7 Gemini 4 Full-Spectrum)

```
주인님 (Human / Sovereign Master)
├── 최종 의사결정, 승인 하달 (Master Approval Gate)
│
├── 테르키르도 지휘 척추 & 코어 구현 (`model: inherit` — Adaptive Session Spine)
│   ├── [세션 모드 선택: Gemini 4 Carbon | Orchestrator (`gemini-pro-orchestrator`) | Gemini 4 Hydrogen (`High`/`XHigh`)]
│   ├── 최상위 오케스트레이터 (Terukirdo) & UltimateMake 기획
│   ├── 자동 검토 사령관 (legion-commander — Slash-Command Only)
│   ├── 단위 루프 지휘 (ralph-orchestrator)
│   ├── 단일 코어 구현 워커 (agy-worker)
│   └── 군단 병렬 코어 구현 워커 (legion-worker)
│
├── 테르키르도 계획 & 교차 검증 심판 (Gemini 4 Argon / `model: pro`)
│   ├── 실행 계획 및 카드 분해 (terukirdo-plan)
│   ├── 1차 심층 마이크로 계약 리뷰 (first-reviewer)
│   └── 아키텍처·보안·치팅 적대적 심판 (tech-expert)
│
├── GPT 5.6 / 외부 협업 파트너
│   ├── 재현 기반 심층 코드 리뷰 및 모듈 재설계
│   └── 원탁회의(multi-agent-conference) 아키텍트/구현자 참여
│
└── 테르키르도 관제 게이트키퍼 (Gemini 3.8 Flash / `model: flash`)
    ├── 빌드/테스트 스위트 물리 검증 (universal-final-controller)
    └── 최종 Git 스테이징 접근관제 (final-approach-control)
```
