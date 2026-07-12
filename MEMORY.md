# Terukirdo Memory Ledger

## Current Status
- Terukirdo v5.3 Runtime-First Integration is fully implemented, verified, and complete.
- Branch: `20260713a` (created and active).
- All 19 tests in the test suite pass.

## Key Learnings
- **Actionable Insight**: When batch editing or formatting files in Python, do not open files for writing (`open(f, 'w')`) before reading their contents in the same expression, as this immediately truncates the files to 0 bytes. Always read files fully into memory first, then write the cleaned contents.
- **Git Restore Insight**: `git checkout -- .` is useful for restoring unstaged changes of tracked files, but it does not restore untracked files. Storing code snippets in prompt history serves as a reliable fallback for recovering lost content.
- **Git status split parsing**: Parsing git status porcelain lines by splitting on whitespace (`line.split(None, 1)`) is much more robust than hardcoded slicing (`line[3:]`), which breaks when the git status indicator contains only one character instead of two.

## Open Questions
- None at this time.

## Next Steps
- Request user review and staging verification.
- Receive explicit user approval before executing any commits or push/release actions.
