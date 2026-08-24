# V2 아키텍처: Git Hook 기반 예지형 동기화 (Predictive Sync) 상세 기획서

## 1. 개요 (Overview)
본 문서는 V2 아키텍처의 핵심 기능 중 하나인 **Git Hook 기반 예지형 동기화(Predictive Sync)** 에 대한 포괄적이고 상세한 아키텍처 및 파이프라인 기획서입니다. 예지형 동기화는 개발자가 코드를 커밋하거나 병합하는 시점(Git Hooks)에 개입하여, 변경된 컨텍스트를 사전에 파악하고 이를 기반으로 백그라운드에서 지식 베이스(Corpus)를 동기화하여 지연 없는 AI 코드 어시스턴트 응답을 가능하게 합니다.

## 2. 핵심 목표 (Core Objectives)
- **Zero-Latency 인덱싱**: 사용자가 AI에게 질문하기 전에 컨텍스트 동기화를 완료.
- **충돌 방지 (Conflict Resolution)**: 병합 충돌 시 자동 롤백 및 동기화 중지 메커니즘.
- **크로스 플랫폼 호환성**: Windows, macOS, Linux 환경에서 동일하게 동작하는 Git Hook.
- **투명성 (Transparency)**: 개발자의 기존 Git 워크플로우를 방해하지 않음 (비동기 처리).

## 3. 파이프라인 아키텍처 (Pipeline Architecture)

### 3.1 전체 워크플로우 (High-Level Workflow)
1. **Developer Action**: `git commit` 또는 `git merge` 실행
2. **Git Hook Trigger**: `pre-commit` 또는 `post-merge` 훅 실행
3. **Change Detection**: 변경된 파일 목록 및 Diff 추출
4. **State Caching**: `.terkirdo_pre_cache.md`에 변경 상태 기록
5. **Background Sync**: 비동기 워커를 통해 AI 지식 베이스 업데이트
6. **Completion / Rollback**: 성공 시 캐시 정리, 실패 또는 충돌 시 롤백 수행

---

## 4. Git Hook 스크립트 설계 (Bash Script Design)

### 4.1 크로스 플랫폼 `pre-commit` 훅
이 스크립트는 커밋 전에 실행되어 변경된 파일을 분석하고 캐시 파일을 생성합니다. Windows(Git Bash)와 POSIX 시스템 모두에서 호환되도록 작성되었습니다.

```bash
#!/usr/bin/env bash
# .git/hooks/pre-commit
# Predictive Sync Pre-commit Hook

set -e

# OS 환경 확인
OS_TYPE=$(uname -s)
if [[ "$OS_TYPE" == *"MINGW"* ]] || [[ "$OS_TYPE" == *"CYGWIN"* ]] || [[ "$OS_TYPE" == *"MSYS"* ]]; then
    IS_WINDOWS=true
else
    IS_WINDOWS=false
fi

CACHE_FILE=".terkirdo_pre_cache.md"
LOCK_FILE=".terkirdo_sync.lock"

# 1. 변경된 파일 목록 추출 (Staged files)
CHANGED_FILES=$(git diff --cached --name-only --diff-filter=ACM)

if [ -z "$CHANGED_FILES" ]; then
    exit 0
fi

# 2. 캐시 및 락 파일 상태 확인
if [ -f "$LOCK_FILE" ]; then
    echo "[Predictive Sync] Warning: Sync is already in progress. Skipping pre-cache generation."
    exit 0
fi

# 3. 변경 상태 기록을 위한 JSON 래퍼 (MD 내부 보관)
CURRENT_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
COMMIT_HASH_TEMP="pending_$(head -c 8 /dev/urandom | xxd -p)"

cat <<EOF > "$CACHE_FILE"
---
sync_type: pre-commit
timestamp: "$CURRENT_TIME"
os: "$OS_TYPE"
pending_id: "$COMMIT_HASH_TEMP"
---
# Predictive Sync Context

\`\`\`json
{
  "event": "pre-commit",
  "files": [
EOF

# 파일 목록을 JSON 배열로 포맷팅
FIRST=true
while IFS= read -r file; do
    if [ "$FIRST" = true ]; then
        FIRST=false
    else
        echo "    ," >> "$CACHE_FILE"
    fi
    echo "    \"$file\"" >> "$CACHE_FILE"
done <<< "$CHANGED_FILES"

cat <<EOF >> "$CACHE_FILE"
  ]
}
\`\`\`
EOF

# 4. 백그라운드 동기화 프로세스 호출 (Non-blocking)
if [ "$IS_WINDOWS" = true ]; then
    # Windows 비동기 호출 (start)
    start /b terkirdo-cli sync --predictive --cache-file="$CACHE_FILE" > /dev/null 2>&1
else
    # POSIX 비동기 호출 (&)
    nohup terkirdo-cli sync --predictive --cache-file="$CACHE_FILE" > /dev/null 2>&1 &
fi

exit 0
```

### 4.2 `post-merge` 훅
병합 완료 후 원격 저장소에서 가져온 대규모 변경 사항을 반영합니다.

```bash
#!/usr/bin/env bash
# .git/hooks/post-merge
# Predictive Sync Post-merge Hook

set -e

IS_SQUASH=0
if [ "$1" = "1" ]; then
    IS_SQUASH=1
fi

CACHE_FILE=".terkirdo_pre_cache.md"
CHANGED_FILES=$(git diff-tree -r --name-only --no-commit-id HEAD@{1} HEAD)

# 기록 로직은 pre-commit과 유사하되, event가 "post-merge"로 기록됨.
# 비동기 워커를 호출하여 전체 컨텍스트 재평가 및 업데이트 트리거.
```

---

## 5. 상태 파일 구조 (`.terkirdo_pre_cache.md`)
이 파일은 Git Hook에 의해 생성되며 백그라운드 프로세스가 읽어들여 동기화 작업을 수행하는 기준이 됩니다.

```markdown
---
sync_type: pre-commit
timestamp: "2026-08-17T13:29:14Z"
os: "MINGW64_NT-10.0"
pending_id: "pending_a1b2c3d4"
status: "in_progress"
---
# Predictive Sync Context

## Metadata
- **Event:** `pre-commit`
- **Triggered By:** Local User
- **Target Branch:** `feature/v2-architecture`

## Changed Files Context
\`\`\`json
{
  "event": "pre-commit",
  "files": [
    "docs/v2_specs/01_Overview.md",
    "lib/core/sync_engine.dart",
    "test/sync_engine_test.dart"
  ],
  "diff_summary": {
    "additions": 145,
    "deletions": 23,
    "complexity_score": 7.5
  }
}
\`\`\`

## Sync Instructions for AI
1. Analyze changes in `lib/core/sync_engine.dart`.
2. Update the semantic index for `SyncEngine` class.
3. Cross-reference with `docs/v2_specs/01_Overview.md` to ensure architectural consistency.
```

---

## 6. 타임아웃 및 예외 처리 (Timeout & Rollback Scenarios)

### 6.1 Merge Conflict (병합 충돌) 발생 시나리오
Git에서 충돌이 발생하면 커밋이 중단되고 작업 트리가 불안정한 상태가 됩니다.
- **감지 메커니즘**: 백그라운드 워커는 주기적으로 `git status`를 폴링하여 `Unmerged paths`를 감지합니다.
- **롤백 프로세스**:
  1. 충돌 감지 시 즉시 진행 중인 동기화 작업(인덱스 업데이트 등)을 **일시 중지(Suspend)**.
  2. `.terkirdo_pre_cache.md`의 `status`를 `conflict_paused`로 변경.
  3. AI 벡터 DB에 커밋되지 않은 트랜잭션을 롤백(Drop uncommitted vectors).
  4. 사용자가 충돌을 해결하고 `git commit`을 완료하여 `post-commit` 훅이 트리거되면, 이전 `conflict_paused` 상태를 초기화하고 델타 동기화(Delta Sync)를 처음부터 재시작.

### 6.2 타임아웃 (Timeout) 처리
대규모 리팩토링으로 인해 동기화가 설정된 제한 시간(기본 5분)을 초과하는 경우.
- **감지 메커니즘**: 백그라운드 워커 내부의 하트비트 타이머.
- **처리 프로세스**:
  1. 5분 경과 시 현재 처리된 부분까지만 체크포인트(Checkpoint) 저장.
  2. 나머지 미처리 파일들은 **지연 큐(Deferred Queue)** 로 이동.
  3. 프로세스를 안전하게 종료하여 시스템 리소스(CPU/RAM) 독점 방지.
  4. 사용자가 AI에게 질문 시도 시, 지연 큐에 남은 작업이 있다면 "Just-in-Time(JIT) 동기화"로 전환하여 해당 파일만 즉시 분석 후 응답.

---

## 7. 크로스 플랫폼(Cross-Platform) 호환성 보장 방안

### 7.1 파일 경로 분리 기호 (Path Separator)
- Windows는 `\`, POSIX는 `/`를 사용하므로, 상태 파일(`.terkirdo_pre_cache.md`) 내의 모든 경로는 표준화된 `/` (Forward Slash)로 변환하여 저장 및 파싱.
- Node.js나 Python 백그라운드 워커에서 `path.normalize()` 또는 `os.path.normpath` 적용 의무화.

### 7.2 백그라운드 프로세스 디태치 (Detaching Processes)
- **Windows**: `start /b command` 사용으로 백그라운드 실행. (Git Bash 환경에서는 `nohup`이 불완전하게 동작할 수 있음)
- **Linux/macOS**: `nohup command > /dev/null 2>&1 &` 사용.
- 공통 락 파일(`.terkirdo_sync.lock`)을 생성하여 여러 훅이 동시에 트리거될 때 경쟁 조건(Race Condition)을 방지. 락 파일은 프로세스 종료 시 반드시 해제되어야 하며, `trap` 명령어를 통해 스크립트 강제 종료 시에도 삭제되도록 보장.

## 8. 결론
Git Hook 기반 예지형 동기화 파이프라인은 사용자의 인지적 부하와 대기 시간을 0으로 수렴시키는 V2 아키텍처의 핵심 기능입니다. 충돌 상황에 대한 엄격한 롤백 처리와 OS별 비동기 스레드 분리 전략을 통해 안정성을 극대화합니다.
