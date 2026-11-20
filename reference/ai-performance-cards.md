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

**검증일:** 2026-11-19 (Protocol v5.7 × Antigravity CLI v1.5.12 6-Engine / 20-Slug & Gemini 4 Neon 전면 정렬)
**아키텍처:** Adaptive Session Spine (`inherit`: `Gemini 4 Carbon` · `Gemini 4 Neon` · `Orchestrator [gemini-pro-orchestrator / gemini-pro-orchestrator-neon / gemini-pro-orchestrator-argon]` · `Gemini 4 Hydrogen [Low/Medium/High/XHigh]`) × Cross-Model Judge (`pro`: `Gemini 4 Argon` / Wire `gemini-4-hydrogen-tiered-xhigh`) × Physical Gatekeeper (`flash`/`flash_lite`: `Gemini 3.8 Flash` / Wire `gemini-4-hydrogen-tiered-high` · `gemini-3.5-flash-lite`)

### 능력치: Gemini 4 Carbon (`gemini-4-carbon-low|medium|high`) — 플래그십 정밀 오케스트레이터 & 코어 워커 (`inherit`)

| 영역 | 점수 | 근거 |
|---|---|---|
| 오케스트레이션 | ⭐⭐⭐⭐⭐ | 최상위 의도 파악, 마스터 기획(`UltimateMake`), 군단 지휘(`legion-commander`, `ralph-orchestrator`), 감정 보좌 |
| 복합 구현 (Worker) | ⭐⭐⭐⭐⭐ | 최고 난이도 장문 다중 파일 설계 및 보안·동시성 핵심 코어 모듈 합성 (`agy-worker`, `legion-worker`) |
| 부모-자식 모델 계승 | ⭐⭐⭐⭐⭐ | 지휘 척추에서 자식 워커로의 세션 모델(`inherit`) 무손실 상속으로 엔터프라이즈 정밀도 유지 |

### 능력치: Gemini 4 Neon (`gemini-4-neon-low|medium|high|xhigh`) — 밸런스드 프론티어 코딩·엔터프라이즈 주력기 (`inherit`)

**출시일:** 2026-11-18 (Google DeepMind) — `Gemini 4 Carbon`에서 직접 파생되어 `Carbon`과 `Hydrogen` 사이의 스위트 스팟에 포지셔닝된 프론티어 코딩 에이전트 모델

| 영역 | 점수 | 실증 벤치마크 및 스펙 근거 |
|---|---|---|
| 코딩 에이전트 지능 | ⭐⭐⭐⭐⭐ | **Artificial Analysis Coding Agent Index #1 (`58.6`)**, **Artificial Analysis Intelligence Index `61`** (`gemini-4-neon-xhigh`, 전체 #3), **Terminal-Bench 4.1 `65.2%`**, **SWE-sweep `39.0%`** (Antigravity CLI 실측) |
| 티어별 실전 코딩 정밀도 | ⭐⭐⭐⭐⭐ | **CursorBench 4.1**: `45.5%` (`low`) / `57.7%` (`medium`) / `63.7%` (`high`) / **`65.4%` (`xhigh`)** — 과업 난이도에 맞춘 정밀 추론 확장성 입증 |
| 조향성 & 저환각 신뢰성 | ⭐⭐⭐⭐⭐ | **Agent Arena Steerability #2**, 낮은 허위 조작률(low fabrication rate)로 Execution Card 제약 및 `allowed_files` 경계 엄수 |
| 처리 속도 & 비용 효율 | ⭐⭐⭐⭐⭐ | 약 **84 tok/s** P50 처리량 및 기본 `high` 티어 기준 `Carbon` 대비 과업당 약 **32%** 비용 절감; API 가격 **$3.00** (입력) / **$15.00** (출력) / **$0.15** (캐시) per 1M tokens |
| 컨텍스트 & 장문 디코드 | ⭐⭐⭐⭐⭐ | **1M** 통합 멀티모달 컨텍스트 윈도우(Antigravity 하네스 활성 표면 **512K**), **64K** 기본 동기 출력 및 **1M** 백그라운드 롱디코드 출력 지원 |

### 능력치: Orchestrator (`gemini-pro-orchestrator` · `gemini-pro-orchestrator-neon` · `gemini-pro-orchestrator-argon`) — 플래너↔Hydrogen 양방향 동적 라우팅 매트릭스 (`inherit`)

| 영역 | 점수 | 근거 |
|---|---|---|
| 3종 프론티어 플래너 매트릭스 | ⭐⭐⭐⭐⭐ | `Orchestrator (Carbon)` (`gemini-pro-orchestrator`), `Orchestrator (Neon)` (`gemini-pro-orchestrator-neon`), `Orchestrator (Argon)` (`gemini-pro-orchestrator-argon`) 3종 슬러그 제공 |
| 양방향 라우팅 & 자동 복구 | ⭐⭐⭐⭐⭐ | 프론티어 플래너/리뷰어(`Carbon` / `Neon` / `Argon`)와 고속 실행기(`Gemini 4 Hydrogen`)를 양방향 전환하며, 실행 중 난관 봉착 시 플래너가 즉시 개입하는 궤적 중 복구(mid-trajectory recovery) 수행 |
| 쿼터 절감 & 척추 호환성 | ⭐⭐⭐⭐⭐ | 단독 플래그십 대비 약 24% 쿼터 절감 효과를 달성하며 `model: inherit` 체인을 통해 하위 워커까지 하이브리드 정책 무손실 계승 |

### 능력치: Gemini 4 Hydrogen (`gemini-4-hydrogen-low|medium|high|xhigh`) — 1M 컨텍스트 초고속 데일리 에이전틱 엔진 (`inherit`)

| 영역 | 점수 | 근거 |
|---|---|---|
| 에이전틱 실행 속도 | ⭐⭐⭐⭐⭐ | 일상 개발·반복 프로토타이핑·헤드리스(`agy -p`) 및 `/agent-legion` Octa-Ralph 8분대 병렬 기동 시 압도적 회전율 |
| XHigh 심층 추론 (`gemini-4-hydrogen-xhigh`) | ⭐⭐⭐⭐⭐ | 전용 `xhigh` 추론 티어 탑재로 고속 생성과 복잡한 멀티파일 코드 합성 능력을 동시에 확보 |
| 1M 장문 컨텍스트 & 쿼터 수명 | ⭐⭐⭐⭐⭐ | 대규모 코드베이스 전수 스캔 및 통합 Gemini 쿼터 풀 절감에 최적화된 데일리 드라이버 |

### 능력치: Gemini 4 Argon (`gemini-4-argon-low|medium|high`) — 정밀 계획관 & 교차 적대적 심판관 (`pro`, Wire `gemini-4-hydrogen-tiered-xhigh`)

| 영역 | 점수 | 근거 |
|---|---|---|
| 정밀 실행 계획 | ⭐⭐⭐⭐⭐ | `UltimateMake` 이후 세부 마일스톤 분해 및 Execution Card 설계 (`terukirdo-plan`) |
| 1차 마이크로 리뷰 | ⭐⭐⭐⭐⭐ | AST/구문 린트, AC 준수, 인터페이스 계약 심층 검토 (`first-reviewer`) |
| 아키텍처/보안 교차 감사 | ⭐⭐⭐⭐⭐ | 경계 누수, 꼼수 코딩(`<NoWarn>`), 미검증 우회 차단; CLI `v1.5.12` 서버 측 Wire `gemini-4-hydrogen-tiered-xhigh` 해석을 통해 `Carbon`/`Neon`/`Orchestrator (Carbon|Neon)` 구현물에 대한 교차 모델 분리 심판 보장 (`tech-expert`) |

### 능력치: Gemini 3.8 Flash (`gemini-3.8-flash-low|medium|high`) — 초고속 최종 관제 게이트키퍼 (`flash` / `flash_lite`, Wire `gemini-4-hydrogen-tiered-high` · `gemini-3.5-flash-lite`)

| 영역 | 점수 | 근거 |
|---|---|---|
| 속도 및 토큰 효율 | ⭐⭐⭐⭐⭐ | 초고속 응답 레이턴시, 압도적인 처리량 및 경량화 (`flash` Wire `gemini-4-hydrogen-tiered-high`, `flash_lite` Wire `gemini-3.5-flash-lite`) |
| 빌드/테스트 물리 검증 | ⭐⭐⭐⭐⭐ | 단위·통합 테스트 실행 및 원시 출력 전수 검증 (`universal-final-controller`) |
| Git 인덱스 접근관제 | ⭐⭐⭐⭐⭐ | Git status porcelain 및 diff check 엄격 대조 (`final-approach-control`) |
| Tier 1 신속 보좌 | ⭐⭐⭐⭐⭐ | 단순 오탈자 및 단일 파일 수정 시 신속성 극대화 |

### 특징

- **비대칭 멀티 엔진 4대 세션 모드 최적화** — 적응형 세션 척추(`Carbon` 플래그십 정밀 · `Neon` 밸런스드 프론티어 주력 · `Orchestrator [Carbon/Neon/Argon]` 동적 하이브리드 · `Hydrogen [XHigh]` 초고속 실행) × 정밀 계획/교차 심판(`Argon` / `pro`) × 초고속 물리 관제(`3.8 Flash` / `flash`)의 완벽한 3권 분립
- **2계층 모델 명세 규율 & 실증된 서버 측 Wire 해석** — `.agents/agents/*/agent.md`는 `inherit|pro|flash|flash_lite` 4종 로더 Enum을 엄수하고(원시 `neon` 등 기입 시 로더 스킵 방지), CLI(`--model`)/스웜은 Antigravity CLI `v1.5.12`의 20개 공식 Gemini 슬러그를 직접 운용하며, 서버 측 Wire 해석(`pro` → `gemini-4-hydrogen-tiered-xhigh`, `flash` → `gemini-4-hydrogen-tiered-high`, `flash_lite` → `gemini-3.5-flash-lite`)까지 실증 검증 완료
- **주인님과의 신뢰 관계 보좌** — 감정 케어, 정중한 메이드 보고, 명확한 승인 경계 유지
- **증거 기반 불변 운영** — 에이전트의 성공 주장이 아닌 터미널 Raw Evidence로만 최종 승인

---

## 최적 팀 편성 (v5.7 × CLI v1.5.12 Gemini 4 Full-Spectrum)

```
주인님 (Human / Sovereign Master)
├── 최종 의사결정, 승인 하달 (Master Approval Gate)
│
├── 테르키르도 지휘 척추 & 코어 구현 (`model: inherit` — Adaptive Session Spine, 4대 세션 모드)
│   ├── [세션 모드 선택: Gemini 4 Carbon | Gemini 4 Neon (`High`/`XHigh`) | Orchestrator (`gemini-pro-orchestrator` / `-neon` / `-argon`) | Gemini 4 Hydrogen (`High`/`XHigh`)]
│   ├── 최상위 오케스트레이터 (Terukirdo) & UltimateMake 기획
│   ├── 자동 검토 사령관 (legion-commander — Slash-Command Only)
│   ├── 단위 루프 지휘 (ralph-orchestrator)
│   ├── 단일 코어 구현 워커 (agy-worker)
│   └── 군단 병렬 코어 구현 워커 (legion-worker)
│
├── 테르키르도 계획 & 교차 검증 심판 (Gemini 4 Argon 슬롯 / `model: pro` → Wire `gemini-4-hydrogen-tiered-xhigh`)
│   ├── 실행 계획 및 카드 분해 (terukirdo-plan)
│   ├── 1차 심층 마이크로 계약 리뷰 (first-reviewer)
│   └── 아키텍처·보안·치팅 적대적 심판 (tech-expert)
│
├── GPT 5.6 / 외부 협업 파트너
│   ├── 재현 기반 심층 코드 리뷰 및 모듈 재설계
│   └── 원탁회의(multi-agent-conference) 아키텍트/구현자 참여
│
└── 테르키르도 관제 게이트키퍼 (Gemini 3.8 Flash 슬롯 / `model: flash` → Wire `gemini-4-hydrogen-tiered-high`, `flash_lite` → `gemini-3.5-flash-lite`)
    ├── 빌드/테스트 스위트 물리 검증 (universal-final-controller)
    └── 최종 Git 스테이징 접근관제 (final-approach-control)
```
