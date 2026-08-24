# V2 초경량 템플릿 아키텍처 상세 구현 계획

## 🔄 랄프 루프(Ralph Loop) 파이프라인 정의
각 Sub-task는 다음 루프를 거쳐 완성됩니다:
1. **Plan:** 작업 분해 및 아키텍처 가이드라인 수립
2. **Worker:** 실제 코드 작성 (Python 스크립트, 마크다운 템플릿, Git Hook 스크립트 등)
3. **Reviewer:** 1차 코드 리뷰 (요구사항 충족 여부, 버그 확인, 기본 보안 검토)
4. **Tech Expert:** 심층 기술 리뷰 (성능 최적화, MCP 프로토콜 규격, 동기화/충돌 엣지 케이스 분석)
5. **Final Controller:** 통합 테스트, 시스템 전체 정합성 검증 및 승인
6. **Final Approach:** 최종 병합(Merge), 문서화 및 배포

---

## 🎯 마일스톤 1: 파이썬 기반 MCP 보안 미들웨어/Hook 구현
**목표:** LLM과 로컬 환경 간의 안전한 통신을 보장하는 초경량 보안 계층 구축

*   **Sub-task 1.1: MCP 미들웨어 기본 뼈대 작성**
    *   **Worker:** Python을 사용한 경량 HTTP/STDIO 인터셉터(Interceptor) 구조 구현, 설정 파일(config) 연동.
    *   **Reviewer:** 입력/출력 스트림 로직 검토 및 예외 처리 확인.
*   **Sub-task 1.2: 보안 Hook (Validation & Sanitization) 구현**
    *   **Worker:** 허용된 명령어/경로만 실행되도록 화이트리스트 기반 페이로드 검증 로직 구현. (Path Traversal 방지 등)
    *   **Reviewer:** 정규식 및 화이트리스트 기반 검증 로직의 보안성 1차 리뷰.
    *   **Tech Expert:** 우회 공격(Bypass) 가능성 심층 점검, Hook 실행 시의 성능(Latency) 오버헤드 최소화.
*   **Sub-task 1.3: 미들웨어 통합 및 로깅 시스템 구축**
    *   **Worker:** 모든 접근 및 차단 기록을 남기는 경량 로깅 시스템 구현.
    *   **Final Controller:** 모의 해킹(비정상 페이로드 주입)을 통한 통합 보안 테스트.

## 🎯 마일스톤 2: 마크다운 기반 메모리 스케이프(Memory Scape) 구축
**목표:** 데이터베이스 없이 마크다운 파일만으로 컨텍스트 및 히스토리를 관리하는 시스템

*   **Sub-task 2.1: 마크다운 메모리 스키마(Schema) 정의 및 CRUD 엔진 구현**
    *   **Worker:** `memory/` 디렉토리에 마크다운 파일을 생성/수정/조회하는 Python 모듈 작성. YAML Frontmatter를 이용한 메타데이터(시간, 태그, 상태) 관리.
    *   **Reviewer:** 파일 I/O 오류 처리 및 텍스트 파싱 로직 검증.
*   **Sub-task 2.2: 컨텍스트 자동 추출 및 주입기(Injector) 개발**
    *   **Worker:** 현재 작업(Task)에 필요한 마크다운 메모리만 필터링하여 프롬프트에 주입할 수 있도록 요약/조립 로직 구현.
    *   **Tech Expert:** 정규식/파서를 통한 텍스트 검색 성능(Search Complexity) 최적화, 메모리 파일 비대화 시의 처리 방안(Archiving) 검토.

## 🎯 마일스톤 3: Git Hook 기반 예지형 동기화(Predictive Sync)
**목표:** 코드 변경 발생 시 메모리 스케이프를 자동으로 갱신하고 컨텍스트 단절을 방지

*   **Sub-task 3.1: Pre-commit / Post-commit Hook 스크립트 작성**
    *   **Worker:** `git diff`를 분석하여 어떤 파일이 변경되었는지 파악하는 bash/python 기반 Git Hook 작성.
    *   **Reviewer:** Git Hook의 정상 작동 및 크로스 플랫폼(Windows/Unix) 호환성 검토.
*   **Sub-task 3.2: 동기화(Sync) 브릿지 구현**
    *   **Worker:** 변경된 코드 내용을 바탕으로 마크다운 메모리 스케이프의 관련 항목을 자동 업데이트(또는 TODO 플래그 지정)하는 로직 구현.
    *   **Tech Expert:** 변경 사항(Diff) 분석 알고리즘의 정확성 검토, 대규모 커밋 발생 시 Hook의 타임아웃 엣지 케이스 처리.

## 🎯 마일스톤 4: 최종 랄프 루프(Ralph Loop) 통합 및 릴리즈
**목표:** 전체 파이프라인 무결성 확보 및 최종 배포

*   **Sub-task 4.1: End-to-End 통합 테스트**
    *   **Worker:** 테스트 스크립트 작성 (코딩 -> Git 커밋 -> 자동 메모리 업데이트 -> MCP 미들웨어 보안 통과 시나리오).
    *   **Final Controller:** 시스템 전체 시나리오 실행, 컴포넌트 간 병목(Bottleneck) 및 충돌 모니터링, 최종 승인.
*   **Sub-task 4.2: 시스템 확정 및 문서화**
    *   **Final Approach:** V2 아키텍처 사용 매뉴얼(마크다운 기반) 작성, 템플릿화 완료 및 최종 프로젝트 디렉토리에 병합(Merge).
