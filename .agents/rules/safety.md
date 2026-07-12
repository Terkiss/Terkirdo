# Safety Policies and Invariants

This document outlines the safety guardrails, commands classifications, and permission priorities.

## Permission Hierarchy

1. **Platform Permission Engine** (1st line of defense)
2. **PreToolUse Hook** (2nd line of defense - runtime command checking)
3. **Execution Card Scope** (3rd line of defense - allowed/forbidden files check)
4. **Review/Controller Gates** (4th line of defense - evidence validation)

## Command Classification Rules

### 1. DENY (Strictly Prohibited)
The following actions must be blocked by hooks immediately:
- `rm -rf /` or `rm -rf <workspace root>`
- `git reset --hard`
- `git clean -fd` / `-fdx` / `-f` (without `-n` or `--dry-run`)
- `git checkout -- <path>`
- `Format-Volume`
- `dotnet ef database drop` or `Drop-Database`
- `terraform destroy`
- Direct modifications under `.git/` folder
- Workspace escape (modifying files outside allowed workspace folders)
- Writing literal API keys / secret tokens directly into code files (except documentation)

### 2. FORCE_ASK (Explicit Confirmation Required)
The following actions require explicit user review and confirmation before execution:
- `terraform apply`
- `kubectl apply/delete/rollout/scale`
- `firebase deploy`
- `gcloud app deploy`
- `fastlane deliver/supply/pilot`
- `git commit`
- Database migrations (`supabase db push`, `dotnet ef database update`)
- Staging production configuration changes
- Installing new software packages (`npm install`, `pip install`, `pub get` etc.)

### 3. ALLOW (Automatically Permitted)
- Read-only actions (`git status`, `git diff`, `git diff --check`, `git clean -n`)
- Local build, lint, and test runs
- Filesystem editing within the authorized workspace scope
