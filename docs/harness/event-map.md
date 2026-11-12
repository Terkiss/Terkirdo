# Harness Event Map

이 문서는 harness 내부 요소가 언제 관여하는지 설명한다. Runtime 우선순위는 `AGENTS.md`, 선택된 skill, hooks, scripts의 실제 구현이 가진다. 이 문서는 그 연결 관계를 기록한다.

## Lifecycle

1. User prompt arrives.
2. Antigravity CLI (`v1.5.7`) reads `AGENTS.md` and loads `.agents/rules/*.md` rules declaring `trigger: always_on` in YAML frontmatter (`safety.md`, `evidence.md`, `documentation.md`, `planning.md`).
3. Antigravity/AGY classifies intent, scope, risk.
4. Antigravity/AGY selects the minimal skill set from `.agents/skills/*/SKILL.md`.
5. The selected skill reads only the needed documents from its `Context Loading`.
6. If a blocking question exists, Antigravity/AGY asks the user before editing files or running commands.
7. Antigravity/AGY edits files or runs commands.
8. `PreToolUse` hooks check risky tool payloads (`run_command`, `write_file`, `edit_file`, `notebook_edit`, legacy file tools, and `invoke_subagent`) before matched tool calls.
9. `PostToolUse` hooks review changed paths and Python AST syntax after matched tool calls (`run_command`, `write_file`, `edit_file`, `notebook_edit`, and legacy file tools).
10. Antigravity/AGY runs the relevant skill script or project command when verification is needed.
11. `Stop` hook (configured as a flat handler list in `.agents/hooks.json`) runs the final harness quality gate before completion, returning `decision` (`allow` | `continue`) alongside backward-compatible `status` while honoring `continuationActive` and `terminationReason` to prevent infinite continuation loops.
12. Antigravity/AGY reports changes, verification, and residual risk.

## Tool Hooks

| Event | Config | Script | Role |
| --- | --- | --- | --- |
| `PreToolUse` | `.agents/hooks.json` (grouped `matcher` + `hooks`, relative `hooks/...` CWD) | `.agents/hooks/pre_tool_use_policy.py` | Blocks destructive commands, workspace escapes, secret literals across `write_file`/`edit_file`/`notebook_edit`, and non-slash `legion-commander` invocations (`Prompt` + `lastUserInput` + `transcriptPath`). |
| `PostToolUse` | `.agents/hooks.json` (grouped `matcher` + `hooks`, relative `hooks/...` CWD) | `.agents/hooks/post_tool_use_review.py` | Warns when paths touched via `write_file`/`edit_file`/`notebook_edit` or `run_command` look high-risk and checks Python AST syntax. |
| `Stop` | `.agents/hooks.json` (flat handler list, relative `hooks/...` CWD) | `.agents/hooks/stop_quality_gate.py` | Validates harness structure (`validate_harness.py --strict`), `git diff --check`, and Turn-End Memory Sync (`MEMORY.md` / `docs/Terukirdo_Trajectory.txt`), anchored to `<repo>/.agents/state/stop_gate_state.json` with CLI v1.5.7 `decision` + `continuationActive` loop safety. |

Pre/Post hooks run around matched tool calls. Stop runs before completion. Hooks do not know the full product intent and do not replace skill selection, testing, or review.

## Request Events

| Request event | Typical route | Verification |
| --- | --- | --- |
| New feature | `product -> design/architecture -> implementation -> test` | Product docs, implementation checks, related tests |
| UI polish | `design -> implementation` | UI script, visual verification when possible |
| API/data change | `architecture -> implementation -> test` | Architecture script, targeted tests |
| Bug fix | `implementation -> test` | Regression test or targeted verification |
| Test work | `test` | `verify-change` script and relevant project tests |
| Release work | `deploy -> test -> operations` | Release script, rollback, monitoring |
| Incident | `operations -> deploy` when rollback or production config may change | Operations script, rollback criteria |
| Harness policy | harness files only | path checks, syntax checks, skill script checks |

## Skill Scripts

| Intent | Script |
| --- | --- |
| product | `.agents/skills/plan-product/scripts/verify.ps1` |
| design | `.agents/skills/design-ui/scripts/verify.ps1` |
| architecture | `.agents/skills/plan-architecture/scripts/verify.ps1` |
| implementation | `.agents/skills/implement-feature/scripts/verify.ps1` |
| test | `.agents/skills/verify-change/scripts/verify.ps1` |
| deploy | `.agents/skills/prepare-release/scripts/verify.ps1` |
| operations | `.agents/skills/operate-app/scripts/verify.ps1` |

## Handoff Events

| When | Document |
| --- | --- |
| Current task state must be preserved | `docs/handoff/current-state.md` |
| A decision is confirmed | `docs/handoff/decisions.md` |
| A missing answer remains after the user defers it | `docs/handoff/open-questions.md` |
| A blocking question is deferred | `docs/handoff/open-questions.md` |
| Follow-up work remains | `docs/handoff/next-actions.md` |

Do not use handoff docs as a command log. Report the need first, then record reusable status, decisions, questions, and next actions only after user request or approval.
