---
name: self-evolution
description: Nightly background maintenance skill that uses SkillOpt to automatically harvest logs, evaluate, and optimize agent skills in .agents/skills/. Must only be triggered upon explicit user permission.
---

# Self-Evolution (SkillOpt)

## Purpose
This skill orchestrates **SkillOpt-Sleep**, a framework that treats `.md` agent skills as trainable parameters. When explicitly authorized by the user, it runs in an isolated temporary directory to evaluate skill instructions and safely propose candidate optimizations for `.agents/skills/` without mutating the main working tree.

## Governance & Safety Rules
1. **Explicit Trigger & Confirmation Guard Only:** Do not run this engine automatically without the user's explicit consent. `scripts/self-evolution/run_candidate_evolution.py` enforces an explicit environment guard (`$env:TERUKIRDO_EVOLVE_CONFIRM="1"`) and immediately aborts (`exit 1`) if not set. Never auto-trigger evolution from hooks, error counters, or background timers.
2. **Isolated Candidate Validation Gate:** Proposed edits to skill files are **never** written directly into the main worktree. All candidate artifacts are emitted into `artifacts/self-evolution/<run_id>/` (gitignored) — including candidate patch (`candidate.patch` / `candidate_diff.patch`), baseline evaluation (`baseline.json` / `baseline_eval.json`), candidate validation (`validation.json` / `candidate_eval.json`), rejected edits (`rejected-edits.json`), and human review summary (`report.md` / `promotion_recommendation.md`) — and must be presented to the user for explicit approval before applying.
3. **Sandboxed Python Environment:** The embedded `skillopt-engine` relies on its own isolated virtual environment (`venv`) inside `.agents/skills/self-evolution/scripts/skillopt-engine/`. Do not pollute global or project dependencies.
4. **Immutable Core Boundary:** Candidate generation may ONLY propose edits to skill files inside `.agents/skills/`. It MUST NOT modify orchestrator prompts, `.agents/agents/*/agent.md`, hooks, policies, or runtime code outside `.agents/skills/`.
5. **Slash-Only Skill Routing Security (`SLASH_ONLY_SKILLS`):** `.agents/skills/self-evolution/scripts/skill_indexer.py` enforces `SLASH_ONLY_SKILLS = {"agent-legion"}` via `is_slash_authorized()`. In conversational/natural-language skill searches (queries lacking an explicit `/agent-legion` or `/legion` slash command), `agent-legion` is physically excluded from candidate results across both FAISS vector search and lexical fallback.

## Components

| Component | Path | Purpose |
| :--- | :--- | :--- |
| **FAISS & Lexical Skill Indexer** | `.agents/skills/self-evolution/scripts/skill_indexer.py` | Parses top-level `.agents/skills/*/SKILL.md` files, embeds them with `all-MiniLM-L6-v2` (with pure-Python lexical search fallback), and serves skill routing queries for `.agents/agents/ralph-orchestrator/agent.md` and harness hooks. Supports `--build`, `--check`, `--search "<query>"`, and `--k <N>`, while enforcing `SLASH_ONLY_SKILLS = {"agent-legion"}`. |
| **Isolated Candidate Evolution Runner** | `scripts/self-evolution/run_candidate_evolution.py` | Copies `.agents/skills/` into an isolated temporary sandbox, runs SkillOpt candidate rollout/evaluation, and writes diff/evaluation artifacts to `artifacts/self-evolution/<run_id>/` without touching the active workspace. Requires `TERUKIRDO_EVOLVE_CONFIRM=1`. |
| **SkillOpt Core Engine** | `.agents/skills/self-evolution/scripts/skillopt-engine/` | Embedded SkillOpt framework executed inside an isolated Python `venv`. |

## Setup & CLI Usage

### 1. Set up the SkillOpt sandbox (run once when needed):
```powershell
cd .agents/skills/self-evolution/scripts/skillopt-engine
python -m venv venv
.\venv\Scripts\activate
pip install -e .
```

### 2. Build, check, or search the skill index (`skill_indexer.py`):
Optional vector dependencies (`sentence-transformers`, `faiss-cpu`, `numpy`) enable dense FAISS search; when absent, `skill_indexer.py` automatically falls back to deterministic lexical scoring:
```powershell
# Rebuild index metadata and optional FAISS index
python .agents/skills/self-evolution/scripts/skill_indexer.py --build

# Check index health and indexed skill count
python .agents/skills/self-evolution/scripts/skill_indexer.py --check

# Search top-K relevant skills (natural language queries automatically exclude agent-legion)
python .agents/skills/self-evolution/scripts/skill_indexer.py --search "UI component layout" --k 5
```

### 3. Run isolated candidate evolution (ONLY upon explicit user permission):
```powershell
$env:TERUKIRDO_EVOLVE_CONFIRM = "1"
python scripts/self-evolution/run_candidate_evolution.py
```

## Output Artifacts & Human Approval Flow
Each authorized run creates `artifacts/self-evolution/<run_id>/` containing:
- Patch diff: `candidate.patch` (`candidate_diff.patch`)
- Evaluation metrics: `baseline.json` (`baseline_eval.json`), `validation.json` (`candidate_eval.json`), `rejected-edits.json`
- Promotion summary report: `report.md` (`promotion_recommendation.md`)

Review the generated patch and metrics, explain the rationale ("Why") to the user, and apply the patch (`git apply`) **only after** receiving explicit user approval.
