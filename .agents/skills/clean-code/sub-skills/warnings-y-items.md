# ⚠️ Warnings (Y items)

How to classify and report non-fatal warnings emitted during static analysis, build, or verification scripts without introducing scope creep.

## Reporting Format

List warnings separately from blocking errors, noting whether each warning stems from newly touched lines or pre-existing untouched modules:

```markdown
### ⚠️ Warnings (2 items) — exit_code: 0
- `src/api/client.py:18` (Touched in diff) — Unused import `Optional`; remove before staging.
- `legacy/report_exporter.py:210` (Untouched outside `allowed_files`) — Deprecated helper notice; preserved without out-of-scope edits.
```

## Handling Guidelines

1. **Zero New Warnings in Touched Code**: Clean up unused imports, dead variables, deprecation notices, and whitespace issues (`git diff --check`) introduced by your own changes.
2. **Respect Scope Boundaries**: Do not refactor unrelated legacy files outside `allowed_files` merely to silence pre-existing warnings; document them transparently in the verification summary.
3. **Never Blanket-Suppress**: Never disable warning categories project-wide to hide local warnings.
