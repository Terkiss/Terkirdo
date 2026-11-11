# Agent → Script Mapping (Terukirdo v5.7)

Each Terukirdo v5.7 agent runs only the sanctioned verification, partitioning, or tactical coordination scripts aligned with its permission boundary and assigned `target_skill`.

## Sanctioned Agent-to-Script Matrix

| Agent | Role & Permission | Verification / Operational Script | Command |
| :--- | :--- | :--- | :--- |
| **`agy-worker`** | Core Implementation Worker (Write) | Feature Verification Gate | `powershell -ExecutionPolicy Bypass -File .agents/skills/implement-feature/scripts/verify.ps1` |
| **`agy-worker` / `legion-worker`** | Implementation & Test Worker (Write) | Change Verification Gate | `powershell -ExecutionPolicy Bypass -File .agents/skills/verify-change/scripts/verify.ps1` |
| **`legion-worker`** | Parallel Squad Worker (Write) | Tactical Radio Board | `python .agents/skills/agent-legion/scripts/legion_radio.py read --since 0` |
| **`legion-commander`** | Autonomous Meta-Reviewer (Read-Only + Shell) | Octa-Ralph Partition Validator | `python .agents/skills/agent-legion/scripts/partition_validator.py <plan.json>` |
| **`legion-commander` / `ralph-orchestrator`** | Command Spine (Read-Only + Shell) | Peer Tactical Radio CLI | `python .agents/skills/agent-legion/scripts/legion_radio.py` |
| **`universal-final-controller`** | Physical Build & Test Gatekeeper (Read-Only + Shell) | Strict Harness Validator | `python scripts/harness/validate_harness.py --strict` |
| **`universal-final-controller`** | Physical Build & Test Gatekeeper (Read-Only + Shell) | Harness Unit Test Suite | `python -m unittest discover -s tests/harness -p "test_*.py" -v` |
| **`final-approach-control`** | Git Index & Staging Gatekeeper (Read-Only + Shell) | Git Whitespace & Staging Audit | `git status --short --branch` / `git diff --cached --check` |

## Operational Rules

- **Write Boundary Enforcement**: Read-only verifiers (`universal-final-controller`, `final-approach-control`, `legion-commander`, `ralph-orchestrator`) execute verification commands via `run_command` to collect raw `exit_code` evidence, and must never mutate source files or SSOT documents.
- **Skill Gate Alignment**: Always run the `verify.ps1` script matching the Execution Card's `target_skill` (for example `.agents/skills/design-ui/scripts/verify.ps1` for `design-ui` or `.agents/skills/prepare-release/scripts/verify.ps1` for `prepare-release`).
