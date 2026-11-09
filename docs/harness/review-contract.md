# Review Contract

This document defines the interface and data contracts for review processes.

## Review Report Schema

All reviewers must generate reports conforming to the JSON Schema at [.agents/schemas/review-report.schema.json](../../.agents/schemas/review-report.schema.json).

### First Reviewer Verdicts

- `PASS`: Code changes meet all requirements, with no issues.
- `PASS WITH P3`: Code meets requirements with only minor stylistic suggestions (P3).
- `REWORK REQUIRED`: Critical (P1) or major (P2) issues found. Rework is required.
- `UNABLE TO VERIFY`: Incomplete files or missing logs prevent review.

### Tech Expert (Architectural Judge) Verdicts

- `ARCHITECTURALLY ACCEPTABLE`: Technical choices, module boundaries, and security policies are sound.
- `REWORK REQUIRED`: Architectural or security violations (P1/P2) detected.
- `EXPLORATION ONLY`: Approved only as a prototype; not for production staging.
- `UNABLE TO VERIFY`: Lack of documentation or remote access blocks validation.

## Review Rules

1. **Strict Read-Only**: Reviewers must not modify implementation code or git index states.
2. **Zero Finding Quota (Clean Review is Success)**: Reviewers have zero quota of findings to meet. When existing code satisfies contracts and boundaries, issuing `PASS` or `ARCHITECTURALLY ACCEPTABLE` without manufacturing speculative issues is a 100% successful review outcome.
3. **4-Element Defect Contract**: Every `P1` or `P2` finding that triggers `REWORK REQUIRED` must explicitly prove all 4 elements:
   - `Violated Contract / Requirement`: The exact specification, acceptance criterion, or boundary violated.
   - `Concrete Trigger`: The precise input, condition, or sequence causing the failure.
   - `Current Code Evidence`: File path and line number(s) demonstrating the flawed logic.
   - `Material Consequence`: The concrete runtime exception, data corruption, or operational damage resulting.
4. **Subagent Handle Reuse (`send_message`) & Final-State Verification**:
   - During Rework or follow-up verification within the same task/partition, orchestrators reuse active subagents via `send_message(Recipient=conversationId, Message=...)` to maintain file context and prior findings.
   - Re-verifying post-rework final diffs and re-running invalidated checks is mandatory before closing any finding as `FIXED`.
5. **Finding Severity**:
   - `P1` (Security/Data loss): Must be fixed before staging.
   - `P2` (Architecture/Bugs): Must be fixed before staging.
   - `P3` (Stylistic/Docs): Can be deferred and documented as residual risks; non-blocking.
