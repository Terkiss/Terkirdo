# ❌ Errors Found (X items)

How to structure, triage, and resolve blocking errors (`exit_code != 0`) reported by verification scripts, compilers, or test suites.

## Reporting Format

Always cite exact file paths, line numbers, exit codes, and failure messages so reviewers can reproduce or audit every item deterministically:

```markdown
### ❌ Errors Found (2 items) — exit_code: 1
- `src/services/order_service.py:42` — `TypeError`: expected `Decimal`, got `float` in `calculate_total()`.
- `scripts/harness/validate_harness.py` — Frontmatter `name` mismatch in `.agents/skills/clean-code/SKILL.md`.
```

## Triage & Resolution Rules

1. **Never Mask Failures**: Do not suppress linter rules, add `<NoWarn>`, skip tests, or weaken baseline `tests/**` assertions to make errors disappear.
2. **Fix Root Cause in Scope**: Repair the production code defect inside `allowed_files`, then re-run the exact failing command to confirm `exit_code == 0`.
3. **Escalate Out-of-Scope Blockers**: If the error originates outside `allowed_files` or requires an architectural/SSOT change, report the raw error output and request orchestrator/user authorization.
