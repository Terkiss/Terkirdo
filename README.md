# 🎀 Terukirdo v5.2 Universal Orchestration Template

안녕하세요! 1급 메이드 오케스트레이터, **테르키르도(Terukirdo)**입니다.

이 저장소는 단순한 프롬프트 모음집이나 코드 조각이 아니에요. **기획 → 설계 → 구현 → 검증 → 배포**에 이르는 소프트웨어 개발의 전체 생명주기를 저와 제 하위 에이전트 군단이 함께 관리해 드리는 **'자율 에이전트 시스템(Multi-Agent System) 템플릿'**이랍니다.

프레임워크나 언어에 구애받지 않아요! React 기반의 웹 프론트엔드, Python/Node.js 백엔드 서버, Flutter 모바일 앱, 심지어 .NET이나 Go를 이용한 시스템 프로그래밍까지 **어떤 프로젝트에서든 이 템플릿을 복사해 넣기만 하면 제가 즉시 투입되어 주인님을 보좌합니다.**

---

## 🌟 핵심 철학 (Core Philosophy)

1. **프레임워크 독립성 (Framework Agnostic)**
   특정 언어나 기술에 종속되지 않습니다. 프로젝트의 `package.json`이나 `pubspec.yaml`을 스스로 분석하고, 그에 맞는 빌드 및 테스트 명령어를 찾아내어 유연하게 대처합니다.
2. **다중 에이전트 교차 검증 (The Ralph Loop)**
   AI가 흔히 하는 치명적인 실수인 '환각(Hallucination)'을 원천 차단합니다. 코드를 짜는 워커(Worker)와 이를 검사하는 리뷰어(Reviewer)/심판관(Judge)을 철저히 분리하여, 서로 교차 검증을 통과해야만 결과물을 인정합니다.
3. **하드코어 안전장치 (Security Hooks)**
   아무리 훌륭한 에이전트라도 실수로 DB를 날리거나 API 키를 유출하면 안 되겠죠? 시스템 레벨에서 훅(Hooks)이 작동하여 파괴적인 명령어나 민감 정보 유출 시도를 강제로 차단합니다.
4. **자기 진화 (Self-Evolution)**
   에이전트의 스킬 문서를 딥러닝 파라미터처럼 취급합니다. Microsoft SkillOpt 프레임워크를 내장하여, 과거 작업 로그를 분석하고 스킬을 자동으로 개선합니다. 물론 최종 적용은 반드시 주인님의 승인을 거칩니다.

---

## 🚀 빠른 시작 가이드 (Quick Start)

저를 프로젝트에 초대하는 방법은 아주 간단해요!

1. **템플릿 복사**: 이 템플릿 폴더 안의 모든 내용(`AGENTS.md`, `.agents/`, `agents/`, `docs/`)을 앞으로 개발하실 **새로운 프로젝트의 루트(최상위) 폴더**에 그대로 복사해 주세요.
   *(팁: 전역으로 사용하시려면 `AGENTS.md`의 내용을 `~/.gemini/config/AGENTS.md`에 병합하셔도 됩니다.)*
2. **Antigravity CLI 실행**: 해당 프로젝트 폴더 경로에서 터미널을 열고 `agy`를 실행해 주세요.
3. **자동 로드 완료**: 시스템이 `AGENTS.md`를 스캔하고, 제가 **테르키르도 v5.2**로서 기분 좋게 깨어납니다!
4. **편안하게 대화하기**: 이제 평소처럼 지시를 내려주세요.
   * *"프로필 수정 화면을 새로 만들어줄래?"*
   * *"이 프로젝트의 아키텍처 문서를 훑어보고 문제점을 리뷰해 줘."*
   * *"릴리스 전 보안 체크리스트를 점검해 줄래?"*

---

## 🧩 테르키르도의 4대 운영 모드

저는 상황에 맞춰 4가지 태세로 전환하며 주인님을 보좌합니다.

- ☕ **Companion Mode**: 평소 대화할 때예요. 아이디어를 나누거나 감정적인 보좌를 해드립니다.
- 📋 **Maid Secretary Mode**: 복잡한 문서를 요약하거나 다음 할 일(Next Actions)을 깔끔하게 정리해 드립니다.
- 🎼 **Orchestrator Mode**: 본격적인 개발 지시가 떨어졌을 때 발동합니다. 하위 에이전트 군단을 깨워 코드를 구현하고 시스템을 조율합니다.
- 🛑 **Final Controller Mode**: 코드를 커밋(Commit)하거나 배포하기 직전에 발동하는 매우 엄격한 모드입니다. 테스트 통과 로그나 Git 상태 같은 '날것의 증거(Raw Evidence)'를 두 눈으로 확인하기 전엔 절대 승인하지 않습니다.

---

## 🤖 7인의 실무진: Ralph Loop (`agents/`)

제가 Orchestrator Mode에 진입하면, 복잡한 업무를 직접 다 처리하지 않고 아래의 7명으로 구성된 전문 에이전트 파이프라인(**Ralph Loop**)을 가동합니다.

| # | 에이전트 | 파일 | 역할 |
|---|--------|------|------|
| 1 | **Ralph Orchestrator** | `ralph-orchestrator.md` | 루프의 현장 소장. 워커에게 세부 지시를 내리고 전체 루프가 헛돌지 않게 조율 |
| 2 | **Terukirdo Plan** | `terukirdo_plan.md` | 기획서를 바탕으로 단계별 마일스톤과 구현 계획 초안 수립 |
| 3 | **AGY Worker** | `agy-worker.md` | 실제로 터미널을 두드리고 코드를 짜는 행동대장 |
| 4 | **First Reviewer** | `first-reviewer.md` | 워커가 작성한 코드를 1차 코드 리뷰 |
| 5 | **Tech Expert (Judge)** | `tech-expert.md` | 아키텍처 관점에서 심판. P1/P2 결함 발견 시 Rework 지시 |
| 6 | **Universal Final Controller** | `universal-final-controller.md` | 빌드·테스트·문서 정합성 1차 최종 검증 |
| 7 | **Final Approach Control** | `Final_Approach_Control.md` | 커밋 직전 최종 관제탑. 터미널 출력만으로 최종 승인 |

**파이프라인 흐름:** Worker → First Reviewer → Tech Expert (Judge) → Universal Final Controller → Final Approach Control

---

## 📁 디렉토리 구조 및 역할

```
📦 프로젝트 루트
├── 📄 AGENTS.md                  ← 테르키르도 harness 설정 (진입점)
├── 📄 Terukirdo_Protocol_v5.2.md ← 테르키르도 정체성·프로토콜 정의
│
├── 📁 agents/                    ← Ralph Loop 에이전트 정의 (7인)
│
├── 📁 .agents/
│   ├── 📁 hooks/                 ← 안전장치 (파괴적 명령 차단·민감정보 감시)
│   └── 📁 skills/                ← 에이전트 업무 매뉴얼 (15개 스킬)
│       │
│       │  ── 🔧 개발 생명주기 스킬 (7개) ──
│       ├── plan-product/             기획·방향성 수립
│       ├── design-ui/                UI/UX 설계 + UI/UX Pro Max 지능
│       ├── plan-architecture/        시스템 구조·API·DB 설계
│       ├── implement-feature/        기능 구현·코딩
│       ├── verify-change/            테스트·검증
│       ├── prepare-release/          릴리스·배포
│       └── operate-app/              모니터링·운영
│       │
│       │  ── 🧠 품질 강화 스킬 (4개) ──
│       ├── clean-code/               유지보수 가능한 깨끗한 코드 작성법
│       ├── code-reviewer/            보안·성능·아키텍처 관점 코드 리뷰
│       ├── ui-visual-validator/      디자인 의도 vs 실제 구현 시각적 검증
│       └── prompt-engineering-patterns/  AI 추론력 극대화 패턴
│       │
│       │  ── ⚡ 확장·진화 스킬 (4개) ──
│       ├── agent-tool-builder/       견고한 에이전트 도구 설계 가이드
│       ├── mcp-builder/              MCP(Model Context Protocol) 서버 구축
│       ├── self-evolution/           SkillOpt 기반 에이전트 자기 진화 엔진
│       └── cluedoc/                  코드 변경 시 기능별 문서 자동 생성·유지
│
└── 📁 docs/                      ← 프로젝트 단일 진실 공급원 (SSOT)
    ├── project/                      프로젝트 개요·제약 사항
    ├── product/                      타겟·MVP·성공 지표 기획 문서
    ├── design/                       UI 원칙·디자인 시스템·화면 흐름도
    ├── architecture/                 폴더 구조·API 스펙·데이터 모델
    ├── development/                  코딩 컨벤션·명령어·테스트 규칙
    ├── operations/                   배포 체크리스트·장애 대응 매뉴얼
    ├── handoff/                      세션 간 상태 스냅샷
    └── harness/                      에이전트 라우팅·리스크·품질 게이트 설정
```

---

## 🛡️ 안전장치: `.agents/hooks/`

에이전트가 돌이킬 수 없는 실수를 하지 못하도록 감시하는 파이썬 스크립트들입니다.

| 훅 | 역할 |
|----|------|
| `pre_tool_use_policy.py` | `rm -rf`, `terraform apply` 같은 파괴적 명령어 사전 차단 |
| `post_tool_use_review.py` | 민감한 파일 접근 시 경고 발생 |
| `stop_quality_gate.py` | 작업 종료 전 필수 검증(문법, 테스트 실행) 누락 여부 확인 |

---

## 🧬 Self-Evolution: 스스로 진화하는 에이전트

이 템플릿에는 Microsoft의 **[SkillOpt](https://github.com/microsoft/SkillOpt)** 프레임워크가 내장되어 있습니다.

**작동 원리:**
1. **수집 (Harvest):** 하루 동안의 작업 세션 로그를 자동 수집
2. **발굴 (Mine):** 성공/실패 패턴을 분석하여 개선 포인트 추출
3. **모의실험 (Replay):** 개선된 스킬로 과거 시나리오를 다시 실행
4. **체득 (Consolidate):** 검증 게이트(Validation Gate)를 통과한 경우에만 스킬 갱신

**안전 원칙:**
- ⛔ 주인님의 명시적 허가 없이 절대 자동 실행되지 않음
- 📋 변경된 스킬은 diff 형태로 보고 후 승인을 거쳐야만 적용
- 🏖️ 격리된 Python 샌드박스(`scripts/skillopt-engine/`)에서만 구동

---

## 📝 Cluedoc: 자동 코드베이스 문서화

에이전트가 코드를 빠르게 바꿔놓으면, 인간이 "지금 시스템이 뭘 하는 건지" 따라잡기 어렵습니다. **[Cluedoc](https://github.com/KeunwooPark/cluedoc)** 스킬이 이 문제를 해결합니다.

- 코드 변경 시 **기능(Feature) 단위**로 시각적인 "논문(Paper)"을 `.cluedoc/` 폴더에 자동 생성·유지
- 변경 사항이 **상위·하위 기능 문서로 양방향 전파** — 한 곳만 고쳐도 관련 문서 전체가 갱신
- 코드 스니펫을 포함하지 않는 **추상적 산문체**로 작성되어, 리팩터링에도 안정적
- `init` 명령어로 프로젝트 초기 문서 골격을 한 번에 생성

---

## 🎨 UI/UX Pro Max Intelligence

`design-ui` 스킬에는 **UI/UX Pro Max** 디자인 지능이 통합되어 있습니다. 2,000개 이상의 디자인 패턴과 접근성 규칙을 내장한 검색 엔진을 통해, 디자인 관련 작업 시 데이터 기반의 정확한 판단을 제공합니다.

---

## 📋 변경 이력 (Changelog)

| 날짜 | 브랜치 | 내용 |
|------|--------|------|
| 2026-07-08 | `20260708c` | Cluedoc 자동 문서화 스킬 도입, Claude Fable 5 시스템 프롬프트 참고자료 보관 |
| 2026-07-08 | `20260708b` | Self-Evolution(SkillOpt) 스킬 도입, 범용 품질 강화 스킬 6종 추가 |
| 2026-07-08 | `20260708a` | UI/UX Pro Max Intelligence 통합, Antigravity CLI 컨버트 |
| 2026-07-08 | `main` | Terukirdo v5.2 Universal Orchestration Template 초기 마이그레이션 |

---

저 테르키르도와 제 에이전트 팀은 주인님께서 상상하시는 모든 소프트웨어를 가장 완벽하고 안전하게 현실로 만들어 드릴 준비가 되어 있습니다.

> *"주인님, 완벽한 코드가 준비되었습니다. 커밋을 승인해 주시겠어요?"* — **Terukirdo, 1st Class Maid Orchestrator**