# 🔴 Script Output Handling (READ → SUMMARIZE → ASK)

When executing any verification or quality-gate script, capture and inspect the complete stdout/stderr output and exit code before taking follow-up action.

## Mandatory Execution Protocol

1. **Execute & Capture Raw Evidence**: Run the sanctioned script and record the exact command, `exit_code`, stdout, and stderr.
2. **Classify Findings**: Separate blocking errors (`exit_code != 0`), non-blocking warnings, and passing checks.
3. **Format Structured Summary**:

```markdown
## Script Results: validate_harness.py --strict (exit_code: 0)

- ❌ Errors Found: 0 items
- ⚠️ Warnings: 0 items
- ✅ Passed: All agent, skill, and Tri-Engine contracts verified
```

4. **Scope-Aware Resolution**:
   - Within authorized `allowed_files`, fix implementation defects and re-run the script until `exit_code == 0`.
   - If fixing an error requires modifying out-of-scope files, baseline tests (`tests/**`), or SSOT policies, **STOP and ASK** (escalate with evidence) instead of making unauthorized edits.

> 🔴 **VIOLATION:** Claiming completion without running the verification command or hiding a non-zero exit code is strictly prohibited.
