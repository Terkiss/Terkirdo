# ✅ Passed (Z items)

How to record verified passing checks (`exit_code == 0`) as deterministic raw evidence in Terukirdo v5.7 completion reports.

## Reporting Format

Summarize each executed command alongside its exact exit code and key pass count:

```markdown
### ✅ Passed (4 items)
- `python scripts/harness/validate_harness.py --strict` → `exit_code: 0` (Harness Validation PASSED)
- `python -m unittest discover -s tests/harness -p "test_*.py" -v` → `exit_code: 0` (All unit tests OK)
- `powershell -ExecutionPolicy Bypass -File .agents/skills/implement-feature/scripts/verify.ps1` → `exit_code: 0`
- `git diff --cached --check` → `exit_code: 0` (Zero whitespace or conflict marker defects)
```

## Evidence Integrity Rules

1. **Raw Execution Only**: Only commands actually executed in the current final-state worktree count as `Passed`. Narrative claims without execution are invalid.
2. **Final-State Re-Verification**: If any file is edited after a check passes, re-run the affected verification commands so evidence matches the final diff.
3. **Skipped Checks Must Be Explicit**: If an environment lacks an external runtime, report it under `Skipped` with the exact reason rather than listing it under `Passed`.
