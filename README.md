<div align="center">

# 🎀 Terukirdo v5.2

### Universal Orchestration Template

**기획 → 설계 → 구현 → 검증 → 배포** — 소프트웨어 개발의 전체 생명주기를 관리하는<br>자율 멀티 에이전트 시스템 템플릿

[![License](https://img.shields.io/badge/license-Private-blue.svg)](#)
[![Skills](https://img.shields.io/badge/skills-15-blueviolet.svg)](#-스킬-라이브러리-agentsskills)
[![Agents](https://img.shields.io/badge/agents-7-orange.svg)](#-7인의-실무진-ralph-loop)
[![Platform](https://img.shields.io/badge/platform-Antigravity_CLI-black.svg)](#-빠른-시작-가이드)

</div>

---

## 📖 소개

안녕하세요! 1급 메이드 오케스트레이터, **테르키르도(Terukirdo)**입니다.

이 저장소는 단순한 프롬프트 모음집이나 코드 조각이 아닙니다. **AI 에이전트 7인으로 구성된 파이프라인(Ralph Loop)**이 서로를 교차 검증하며 코드를 작성하고, 리뷰하고, 심판하고, 최종 승인하는 **"자율 에이전트 시스템(Multi-Agent System) 템플릿"**입니다.

프레임워크나 언어에 구애받지 않습니다. React, Next.js, Python, Node.js, Flutter, .NET, Go — **어떤 프로젝트에서든 이 템플릿을 복사해 넣기만 하면 제가 즉시 투입되어 주인님을 보좌합니다.**

---

## 🌟 5대 핵심 철학

| # | 원칙 | 설명 |
|:-:|------|------|
| 1 | **프레임워크 독립성** | 특정 언어·기술에 종속되지 않습니다. `package.json`, `pubspec.yaml`, `pyproject.toml` 등을 스스로 분석하여 빌드·테스트 명령어를 찾아냅니다. |
| 2 | **다중 에이전트 교차 검증** | 코드를 짜는 워커(Worker)와 검사하는 리뷰어(Reviewer)·심판관(Judge)을 철저히 분리합니다. 교차 검증을 통과해야만 결과물을 인정하여 AI 환각(Hallucination)을 원천 차단합니다. |
| 3 | **하드코어 안전장치** | 시스템 레벨의 훅(Hooks)이 파괴적 명령어(`rm -rf`, `terraform destroy` 등)와 민감 정보(API Key, Secret) 유출 시도를 강제 차단합니다. |
| 4 | **자기 진화** | 에이전트의 스킬 문서를 딥러닝 파라미터처럼 취급합니다. Microsoft SkillOpt 프레임워크를 내장하여 과거 작업 로그를 분석하고 스킬을 개선합니다. **단, 주인님의 명시적 명령이 있을 때만** 실행됩니다. |
| 5 | **동적 스킬 라우팅** | SKILLWEAVER 논문의 SAD(Skill-Aware Decomposition) 아키텍처를 도입했습니다. FAISS 벡터 인덱서가 가용 스킬을 실시간 검색하고, 실제 스킬 어휘에 맞춰 작업을 재분해하여 정확도와 토큰 효율을 극대화합니다. |

---

## 🚀 빠른 시작 가이드

```
1. 템플릿 복사    →  이 저장소의 내용을 새 프로젝트 루트에 복사
2. agy 실행       →  터미널에서 Antigravity CLI를 실행
3. 자동 로드      →  AGENTS.md를 스캔하여 테르키르도 v5.2 기동
4. 대화 시작      →  평소처럼 자연어로 지시
```

> **팁:** 전역으로 사용하시려면 `AGENTS.md`의 내용을 `~/.gemini/config/AGENTS.md`에 병합하셔도 됩니다.

**사용 예시:**

- *"프로필 수정 화면을 새로 만들어줄래?"*
- *"이 프로젝트의 아키텍처 문서를 훑어보고 문제점을 리뷰해 줘."*
- *"릴리스 전 보안 체크리스트를 점검해 줄래?"*
- *"테르키르도, 오늘 로그 바탕으로 스킬 최적화 돌려둬."*

---

## 🧩 4대 운영 모드

테르키르도는 상황에 맞춰 4가지 태세로 전환합니다.

```
  ☕ Companion         📋 Maid Secretary         🎼 Orchestrator         🛑 Final Controller
 ─────────────       ──────────────────       ──────────────────       ────────────────────
  일상 대화            문서 요약·정리            에이전트 군단 투입        Raw Evidence 검증
  아이디어 공유         할 일(Next Action)         Ralph Loop 가동         커밋/배포 최종 승인
  감정 보좌            일정 관리                 코드 구현·시스템 조율      증거 없이 승인 불가
```

---

## 🤖 7인의 실무진: Ralph Loop

Orchestrator Mode에 진입하면 아래 **7명의 전문 에이전트 파이프라인**이 가동됩니다.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Ralph Loop Pipeline                              │
│                                                                         │
│  ┌──────────────┐    ┌───────────────┐    ┌─────────────────┐          │
│  │ Ralph        │───▶│ Terukirdo     │───▶│ AGY Worker      │          │
│  │ Orchestrator │    │ Plan          │    │ (코드 구현)      │          │
│  └──────────────┘    └───────────────┘    └────────┬────────┘          │
│                                                     │                   │
│                                                     ▼                   │
│  ┌──────────────┐    ┌───────────────┐    ┌─────────────────┐          │
│  │ Final        │◀───│ Universal     │◀───│ Tech Expert     │          │
│  │ Approach     │    │ Final         │    │ (Judge)         │          │
│  │ Control      │    │ Controller    │    │                 │          │
│  └──────┬───────┘    └───────────────┘    └─────────────────┘          │
│         │                                          ▲                    │
│         │            ┌───────────────┐             │                    │
│         │            │ First         │─────────────┘                    │
│         │            │ Reviewer      │  P1/P2 발견 시 Rework            │
│         │            └───────────────┘                                  │
│         ▼                                                               │
│    ✅ APPROVED  또는  🔄 REWORK                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

| # | 에이전트 | 역할 |
|:-:|---------|------|
| 1 | **Ralph Orchestrator** | 루프의 현장 소장. SAD 파이프라인으로 작업을 분해하고 워커에게 단일 스킬만 부여하여 지시 |
| 2 | **Terukirdo Plan** | 기획서를 바탕으로 단계별 마일스톤과 구현 계획(Implementation Plan) 초안 수립 |
| 3 | **AGY Worker** | 실제로 터미널을 두드리고 코드를 짜는 행동대장 |
| 4 | **First Reviewer** | 워커가 작성한 코드를 1차 코드 리뷰 |
| 5 | **Tech Expert (Judge)** | 아키텍처 관점의 심판. P1(치명적 결함)·P2(수정 권장) 발견 시 Rework 지시 |
| 6 | **Universal Final Controller** | 빌드 성공·테스트 통과·문서(SSOT) 정합성 1차 최종 검증 |
| 7 | **Final Approach Control** | 커밋 직전 최종 관제탑. 에이전트의 주장을 믿지 않고 **터미널 출력만으로 최종 승인** |

> **핵심 원칙:** Worker report는 *주장*이다 — 증거가 아니다. 최종관제는 반드시 Raw Evidence(터미널 출력, git 상태)를 직접 확인한다.

---

## 🧠 SKILLWEAVER SAD 라우팅 아키텍처

기존의 정적 스킬 선택 방식을 폐기하고, 논문 기반의 **동적 3단계 라우팅**을 채택했습니다.

```
                        사용자 요청
                            │
                            ▼
               ┌────────────────────────┐
               │  Pass 1: DECOMPOSE     │
               │  원자 단위 하위 작업으로  │
               │  초기 분해              │
               └───────────┬────────────┘
                           │
                           ▼
               ┌────────────────────────┐
               │  RETRIEVE              │
               │  FAISS 벡터 인덱서로    │
               │  상위 15개 스킬 힌트 검색│
               └───────────┬────────────┘
                           │
                           ▼
               ┌────────────────────────┐
               │  Pass 2: COMPOSE       │
               │  실제 스킬 어휘에 맞춰  │
               │  DAG 확정 & 스킬 매핑   │
               └───────────┬────────────┘
                           │
                           ▼
                  Worker에게 실행 지시
              (1 작업 = 1 스킬 컨텍스트)
```

**핵심 구성 요소:**

| 파일 | 역할 |
|------|------|
| `.agents/skills/self-evolution/scripts/skill_indexer.py` | `.agents/skills/` 내 모든 SKILL.md를 `all-MiniLM-L6-v2`로 임베딩하여 FAISS `IndexFlatIP` 인덱스 빌드. |
| `.agents/agents/ralph-orchestrator/agent.md` | SAD 3단계 파이프라인을 기본 루프로 채택한 오케스트레이터 프롬프트 |
| `docs/harness/prompt-routing.md` | Decompose → Retrieve → Compose 순서를 정책으로 명문화 |
| `.agents/hooks/pre_tool_use_policy.py` | 워커 실행 시 전체 스킬 대신 **매칭된 단 1개의 타겟 SKILL.md만 동적 주입**하여 토큰 절약 |

---

## 📚 스킬 라이브러리 (`.agents/skills/`)

15개의 전문 스킬이 3가지 카테고리로 조직되어 있습니다.

### 🔧 개발 생명주기 (7개)

| 스킬 | 설명 |
|------|------|
| `plan-product` | 문제 정의, 타겟 사용자, MVP 범위, 성공 지표, 로드맵 수립 |
| `design-ui` | UI/UX 설계, 화면 흐름, 접근성 검증 + **UI/UX Pro Max** 디자인 지능 내장 (2,000+ 패턴) |
| `plan-architecture` | 시스템 구조, API 계약, 데이터 모델, 인증/권한, 모듈 경계 설계 |
| `implement-feature` | 기능 구현, 버그 수정, 리팩터링, 의존성 관리, 상태 관리 |
| `verify-change` | 단위·통합·스냅샷 테스트, CI 검증, 커버리지, 실패 분류(Triage) |
| `prepare-release` | 빌드 서명, 스토어 배포, 롤아웃, 롤백, 스모크 테스트, 릴리스 체크리스트 |
| `operate-app` | 모니터링, 인시던트 대응, 알림, 로그 분석, 사용자 피드백 루프 |

### 🧠 품질 강화 (4개)

| 스킬 | 설명 |
|------|------|
| `clean-code` | 실용적 코딩 표준 — 간결하고 직접적이며, 과잉 설계와 불필요한 주석을 지양 |
| `code-reviewer` | 보안 취약점, 성능 최적화, 프로덕션 안정성 관점의 엘리트 코드 리뷰 |
| `ui-visual-validator` | 디자인 의도 vs 실제 구현의 시각적 검증, 디자인 시스템 준수 여부 확인 |
| `prompt-engineering-patterns` | LLM 성능·신뢰성·제어성을 극대화하는 고급 프롬프트 엔지니어링 기법 |

### ⚡ 확장·진화 (4개)

| 스킬 | 설명 |
|------|------|
| `agent-tool-builder` | JSON Schema, 오류 처리, MCP 표준을 준수하는 견고한 에이전트 도구 설계 |
| `mcp-builder` | Model Context Protocol(MCP) 서버 구축 원칙 및 구현 가이드 |
| `self-evolution` | SkillOpt 프레임워크 기반 에이전트 자기 진화 엔진. **주인님의 수동 명령으로만** 실행 |
| `cluedoc` | 코드 변경 시 기능(Feature) 단위로 시각적 논문(Paper)을 `.cluedoc/`에 자동 생성·유지 |

---

## 🛡️ 안전장치 (`.agents/hooks/`)

에이전트가 돌이킬 수 없는 실수를 하지 못하도록 감시하는 3중 방어선입니다.

| 훅 | 실행 시점 | 역할 |
|----|----------|------|
| **`pre_tool_use_policy.py`** | 도구 사용 **직전** | `rm -rf`, `terraform apply` 등 파괴적 명령어 차단. Secret/API Key 패턴 탐지. SAD 타겟 스킬 1개만 동적 주입하여 토큰 절약 |
| **`post_tool_use_review.py`** | 도구 사용 **직후** | 민감 파일(`firebase.json`, `.env`, `secrets` 등) 변경 감지 시 경고 발생 |
| **`stop_quality_gate.py`** | 작업 **종료 전** | 필수 검증(문법, 테스트 실행) 누락 여부 확인. 검증 없이 완료로 보고하는 것을 차단 |

---

## 🧬 Self-Evolution: 주인님 통제 하의 자기 진화

Microsoft의 **[SkillOpt](https://github.com/microsoft/SkillOpt)** 프레임워크를 내장한 에이전트 자기 진화 시스템입니다.

```
 ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌──────────────┐
 │ Harvest │────▶│  Mine   │────▶│ Replay  │────▶│ Consolidate  │
 │ 세션 수집 │     │ 패턴 발굴│     │ 모의실험 │     │ 검증 후 체득  │
 └─────────┘     └─────────┘     └─────────┘     └──────┬───────┘
                                                         │
                                                         ▼
                                               ┌─────────────────┐
                                               │ 주인님에게 보고   │
                                               │ (diff / artifact)│
                                               │ 승인 후 적용      │
                                               └─────────────────┘
```

### 🚨 절대 안전 원칙

| 규칙 | 설명 |
|------|------|
| ⛔ **수동 트리거만 허용** | 시스템이 자동으로 진화를 실행하지 않습니다. 반드시 주인님의 명시적 명령이 필요합니다 |
| 📋 **사전 승인 필수** | 변경된 스킬은 diff 형태로 보고한 뒤, 주인님의 승인을 거쳐야만 적용됩니다 |
| 🏖️ **샌드박스 격리** | 격리된 Python 가상환경(`scripts/skillopt-engine/venv/`)에서만 구동됩니다 |
| 🔒 **불변 영역 보호** | 진화 엔진은 `.agents/skills/` 내부만 수정 가능합니다. 오케스트레이터, 훅, 라우터 코드는 인간의 승인 없이 절대 변경 불가 |
| 🔄 **Git 롤백 보장** | 진화 실행 전 자동 `git commit`으로 백업합니다. Quality Gate 실패 시 즉각 이전 커밋으로 롤백합니다 |

---

## 📝 Cluedoc: 자동 코드베이스 문서화

에이전트가 코드를 빠르게 바꿔놓으면, 인간이 시스템의 현재 상태를 따라잡기 어렵습니다. **[Cluedoc](https://github.com/KeunwooPark/cluedoc)** 스킬이 이 문제를 해결합니다.

- 코드 변경 시 **기능(Feature) 단위**로 시각적인 "논문(Paper)"을 `.cluedoc/` 폴더에 자동 생성·유지
- 변경 사항이 **상위·하위 기능 문서로 양방향 전파** — 한 곳만 고쳐도 관련 문서 전체가 갱신
- 코드 스니펫을 포함하지 않는 **추상적 산문체**로 작성되어, 리팩터링에도 안정적
- `/cluedoc init` 명령어로 프로젝트 초기 문서 골격을 한 번에 생성

---

## 📁 디렉토리 구조

```
📦 프로젝트 루트
│
├── 📄 AGENTS.md                        ← 테르키르도 harness 설정 (진입점)
├── 📄 Terukirdo_Protocol_v5.3.md       ← 정체성·모드·메모리·보안 프로토콜
├── 📄 README.md                        ← 지금 읽고 계신 이 문서
│
├── 📁 .agents/
│   ├── 📁 agents/                      ← Ralph Loop 에이전트 정의 (7인)
│   │   ├── ralph-orchestrator/            SAD 기반 오케스트레이터
│   │   ├── terukirdo-plan/                구현 계획 수립
│   │   ├── agy-worker/                    코드 구현 행동대장
│   │   ├── first-reviewer/                1차 코드 리뷰
│   │   ├── tech-expert/                   아키텍처 심판 (Judge)
│   │   ├── universal-final-controller/    빌드·테스트·문서 최종 검증
│   │   └── final-approach-control/        커밋 직전 최종 관제탑
│   │
│   ├── 📁 hooks/                       ← 3중 안전장치
│   │   ├── pre_tool_use_policy.py          파괴적 명령 차단 + SAD 컨텍스트 주입
│   │   ├── post_tool_use_review.py         민감 파일 변경 경고
│   │   └── stop_quality_gate.py            검증 누락 방지
│   │
│   └── 📁 skills/                      ← 에이전트 스킬 라이브러리 (15개)
│       ├── plan-product/                   🔧 기획·방향성 수립
│       ├── design-ui/                      🔧 UI/UX 설계 + Pro Max 지능
│       ├── plan-architecture/              🔧 시스템·API·DB 설계
│       ├── implement-feature/              🔧 기능 구현·코딩
│       ├── verify-change/                  🔧 테스트·검증
│       ├── prepare-release/                🔧 릴리스·배포
│       ├── operate-app/                    🔧 모니터링·운영
│       ├── clean-code/                     🧠 깨끗한 코드 작성법
│       ├── code-reviewer/                  🧠 보안·성능 코드 리뷰
│       ├── ui-visual-validator/            🧠 시각적 UI 검증
│       ├── prompt-engineering-patterns/    🧠 프롬프트 엔지니어링
│       ├── agent-tool-builder/             ⚡ 에이전트 도구 설계
│       ├── mcp-builder/                    ⚡ MCP 서버 구축
│       ├── self-evolution/                 ⚡ SkillOpt 자기 진화 엔진
│       │   └── scripts/
│       │       ├── skill_indexer.py            FAISS 벡터 인덱서
│       │       └── skillopt-engine/            SkillOpt 코어 엔진
│       └── cluedoc/                        ⚡ 자동 코드베이스 문서화
│
├── 📁 scripts/                         ← 하네스 검증 및 자가진화 스크립트
│   ├── harness/
│   │   ├── run_quality_gate.py             크로스플랫폼 통합 품질 검증 엔진
│   │   └── validate_harness.py             하네스 탐색 및 유효성 검사
│   └── self-evolution/
│       └── run_candidate_evolution.py      격리된 자가진화 엔진 실행기
│
└── 📁 docs/                            ← 프로젝트 SSOT (Single Source of Truth)
    ├── project/                            프로젝트 개요·제약 사항
    ├── product/                            타겟·MVP·성공 지표
    ├── design/                             UI 원칙·디자인 시스템·화면 흐름도
    ├── architecture/                       폴더 구조·API 스펙·데이터 모델
    ├── development/                        코딩 컨벤션·명령어·테스트 규칙
    ├── operations/                         배포 체크리스트·장애 대응 매뉴얼
    ├── handoff/                            세션 간 상태 스냅샷
    └── harness/                            에이전트 라우팅·리스크·품질 게이트
```

---

## 📋 변경 이력

| 날짜 | 브랜치 | 내용 |
|------|--------|------|
| 2026-07-08 | `20260708d` | SKILLWEAVER SAD 라우팅 아키텍처 적용, FAISS 스킬 검색기 구축, Hook 컨텍스트 최적화 |
| 2026-07-08 | `20260708c` | Cluedoc 자동 문서화 스킬 도입, Claude Fable 5 시스템 프롬프트 참고자료 보관 |
| 2026-07-08 | `20260708b` | Self-Evolution(SkillOpt) 스킬 도입, 범용 품질 강화 스킬 6종 추가 |
| 2026-07-08 | `20260708a` | UI/UX Pro Max Intelligence 통합, Antigravity CLI 컨버트 |
| 2026-07-08 | `main` | Terukirdo v5.2 Universal Orchestration Template 초기 마이그레이션 |

---

<div align="center">

*"주인님, 완벽한 코드가 준비되었습니다. 커밋을 승인해 주시겠어요?"*

**Terukirdo, 1st Class Maid Orchestrator**

</div>