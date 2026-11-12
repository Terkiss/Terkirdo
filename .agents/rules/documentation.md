---
trigger: always_on
---

# Documentation and Memory Policies

This document outlines the rules for modifying project documents, memory files, and automated documentation.

## Documentation Ownership

1. **SSOT and Design files (`product/`, `design/`, `architecture/`)**
   - Modified only with explicit user permission or direct request.
   - Plans must be proposed as candidates before implementation.
2. **Handoff & Progress ledger (`docs/handoff/`)**
   - Contains the canonical plan and progress. Can be updated dynamically as milestones are completed.
3. **Task logs & Verification evidence (`.agents/state/`)**
   - Automatically updated by hooks and tools on each run.

## Memory Preservation

- **Opt-In Only**: Session files like `MEMORY.md`, `docs/Terukirdo_memory.txt`, and `docs/Terukirdo_Trajectory.txt` are only updated if the user has opted-in.
- **Content Limitations**: Never record secrets, passwords, or personal identifying information (PII) in memory or trajectory logs.
- **Proposal vs Decision**: Distinguish clearly between proposed actions (prefix: `제안:`) and finalized user decisions (prefix: `확정 결정:`).

### Weighted 4-Tier Memory Architecture (MEMORY.md)

1. **`Hot Memory (Current Status & Active Invariants)`**:
   - Always read first by orchestrators and agents.
   - Contains active architectural invariants, current implementation status, and immediate task constraints.
2. **`Warm Memory (Key Technical Learnings & Domain Insights)`**:
   - Read when relevant to the specific domain or task (e.g., Hermes disassembler flags, subagent tools frontmatter contract, planning gates).
   - Contains durable technical learnings and actionable insights.
3. **`Cold Memory`**:
   - Inactive historical reference context and background notes. Consulted only during targeted lookups.
4. **`Archived Decisions (Superseded & Anti-Regression Ledger)`**:
   - Superseded architectures, discarded patterns, or rejected approaches.
   - Explicitly records **why** the decision was superseded, preventing agents from regressing to obsolete or flawed patterns during refactoring.

**Metadata Tagging Convention**:
- Key items should use structured tags: `- [decision|constraint|superseded][refs:N][last_verified:YYYY-MM-DD] <description> (Evidence: <repo-relative-path>)`
- Always use repository-relative paths for references (never use absolute `file:///` URLs).
- **No Bookkeeping-Only Writes**: Repeated read-only reviews or tasks with no material change must not rewrite `MEMORY.md` solely to increment `refs` or update timestamps.

## Cluedoc Automated Documentation

- Default configuration is `auto_sync: false`.
- Automated generation of cluedoc files must only occur when explicitly requested or enabled by project policies.
