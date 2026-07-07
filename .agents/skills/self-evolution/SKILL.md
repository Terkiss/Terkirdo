---
name: self-evolution
description: Nightly background maintenance skill that uses SkillOpt to automatically harvest logs, evaluate, and optimize agent skills in .agents/skills/. Must only be triggered upon explicit user permission.
---

# Self-Evolution (SkillOpt)

## Purpose
This skill serves as the orchestrator for **SkillOpt-Sleep**, a framework that treats `.md` agent skills as trainable parameters. It runs in the background (typically at night or when idle) to harvest recent session logs, mine them for failures/successes, replay scenarios, and safely optimize the prompt instructions in `.agents/skills/`.

## Rules
1. **Explicit Trigger Only:** Do not run this engine automatically without the user's explicit consent. The user must trigger it explicitly, e.g., using `/goal 스킬 최적화` or `/schedule`.
2. **Validation Gate:** Any proposed changes to skill files MUST NOT be immediately applied to the working branch blindly. They must be presented to the user via an Artifact (diff) or a Pull Request for approval.
3. **Sandboxed Environment:** The `skillopt-engine` relies on a Python environment. Do not install its dependencies globally in the project. Use a dedicated `venv` inside `scripts/skillopt-engine/`.

## Setup & Execution
1. To set up the sandbox (run once):
   ```powershell
   cd .agents/skills/self-evolution/scripts/skillopt-engine
   python -m venv venv
   .\venv\Scripts\activate
   pip install -e .
   ```
2. To trigger a sleep cycle (offline optimization) when authorized:
   ```powershell
   # Example workflow (refer to the SkillOpt documentation for exact arguments)
   .\venv\Scripts\python -m skillopt_sleep --harvest --mine --rollout
   ```

## Output & Approval
When the engine proposes new `best_skill.md` versions, read the changes, summarize the "Why" (why the engine thought this change was necessary based on past failures/successes), and ask the user for approval before updating the actual skill files.
