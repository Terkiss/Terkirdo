# Terukirdo Memory Ledger

## Current Status
- Terukirdo V2 초경량 템플릿의 3대 코어 컴포넌트(MCP Immune System, Memory Scape, Predictive Sync) 구축 완료.
- 12인의 에이전트 자율 랄프 루프(Autonomous Ralph Loop)를 통한 기획, 구현, 검증, 깃 커밋 완전 자동화 성공.
- Branch: `20260817a` (완료 및 Github 푸시됨).

## Key Learnings
- **Actionable Insight (V2)**: Python `yaml` 라이브러리의 `safe_load`는 ISO 8601 형식의 날짜 문자열을 자동으로 `datetime` 객체로 변환합니다. JSON Schema에서 `type: string`으로 정의된 필드를 검증할 때 타입 에러(TypeError)가 발생할 수 있으므로, 검증기에서 명시적으로 `isinstance(val, datetime)`를 체크하고 문자열로 캐스팅하는 방어 로직이 필수적입니다.
- **Actionable Insight (V2)**: Windows Git 환경(MSYS/MINGW)에서 Git Hook(pre-commit 등)을 작성할 때, 비동기 백그라운드 프로세스를 실행하려면 `nohup` 대신 `start /b`를 사용해야 터미널 점유나 무한 대기(Deadlock)를 방지할 수 있습니다.
- **Actionable Insight**: When batch editing or formatting files in Python, do not open files for writing (`open(f, 'w')`) before reading their contents in the same expression, as this immediately truncates the files to 0 bytes. Always read files fully into memory first, then write the cleaned contents.
- **결정론적 Turn-End Memory Sync**: 확률적인 프롬프트 의존성(MD 파일 지시)을 제거하기 위해, `stop_quality_gate.py`에 강제 검증 로직을 추가했습니다. 의미 있는 파일 변경(Harness/문서 포함)이 감지되었으나 `MEMORY.md` 또는 `docs/Terukirdo_Trajectory.txt`가 업데이트되지 않은 경우, 턴 종료가 차단(Blocked/Continue)됩니다.
- **Git status split parsing**: Parsing git status porcelain lines by splitting on whitespace (`line.split(None, 1)`) is much more robust than hardcoded slicing (`line[3:]`), which breaks when the git status indicator contains only one character instead of two.

## Open Questions
- 완성된 V2 템플릿 아키텍처를 기반으로 어떤 실무 프로젝트(새로운 기능, 앱, 스크립트 등)에 투입할 것인가?

## Next Steps
- 기존 메모리 시스템(예: `Terukirdo_memory.txt`)의 지식 중 일부를 새로운 V2 Memory Scape(`.agents/memory/`)로 마이그레이션(아카이빙)하는 것을 고려.
- 주인님이 하달하실 새로운 임무 및 프로젝트 목표 대기.
