---
name: clean-code
description: Pragmatic coding standards - concise, direct, no over-engineering, no unnecessary comments
category: development
version: 4.1.0-fractal
layer: master-skill
---

# Clean Code - Pragmatic AI Coding Standards

> **CRITICAL SKILL** - Be **concise, direct, and solution-focused**.

---

## Core Principles

| Principle | Rule |
|-----------|------|
| **SRP** | Single Responsibility - each function/class does ONE thing |
| **DRY** | Don't Repeat Yourself - extract duplicates, reuse |
| **KISS** | Keep It Simple - simplest solution that works |
| **YAGNI** | You Aren't Gonna Need It - don't build unused features |
| **Boy Scout** | Leave touched code cleaner within authorized scope |

---

## Naming Rules

| Element | Convention |
|---------|------------|
| **Variables** | Reveal intent: `userCount` not `n` |
| **Functions** | Verb + noun: `getUserById()` not `user()` |
| **Booleans** | Question form: `isActive`, `hasPermission`, `canEdit` |
| **Constants** | SCREAMING_SNAKE: `MAX_RETRY_COUNT` |

> **Rule:** If you need a comment to explain a new symbol's name, rename it instead.

---

## Function Rules

| Rule | Description |
|------|-------------|
| **Small** | Max 20 lines, ideally 5-10 |
| **One Thing** | Does one thing, does it well |
| **One Level** | One level of abstraction per function |
| **Few Args** | Max 3 arguments, prefer 0-2 |
| **No Side Effects** | Don't mutate inputs unexpectedly |

---

## Code Structure

| Pattern | Apply |
|---------|-------|
| **Guard Clauses** | Early returns for edge cases |
| **Flat > Nested** | Avoid deep nesting (max 2 levels) |
| **Composition** | Small functions composed together |
| **Colocation** | Keep related code close |

---

## AI Coding Style

| Situation | Action |
|-----------|--------|
| User asks for feature | Write it directly within `allowed_files` |
| User reports bug | Fix root cause and verify with tests |
| No clear requirement | Ask, don't assume |

---

## Anti-Patterns (DON'T)

| ❌ Pattern | ✅ Fix |
|-----------|-------|
| Comment every new line | Avoid obvious comments in new code (preserve existing unrelated comments/docstrings) |
| Helper for one-liner | Inline the code |
| Factory for 2 objects | Direct instantiation |
| utils.ts with 1 function | Put code where used |
| "First we import..." | Just write code |
| Deep nesting | Guard clauses |
| Magic numbers | Named constants |
| God functions | Split by responsibility |

---

## 🔴 Before Editing ANY File (THINK FIRST!)

**Before changing a file, ask yourself:**

| Question | Why |
|----------|-----|
| **What imports this file?** | They might break |
| **What does this file import?** | Interface changes |
| **What tests cover this?** | Tests might fail (never weaken baseline tests!) |
| **Is this a shared component?** | Multiple places affected |

**Quick Check:**
```
File to edit: UserService.ts
└── Who imports this? → UserController.ts, AuthController.ts
└── Do they need changes too? → Check function signatures & allowed_files scope
```

> 🔴 **Rule:** Keep all dependent updates coherent within the authorized task scope.
> 🔴 **Never leave broken imports, missing updates, or weakened baseline tests.**

---

## Summary

| Do | Don't |
|----|-------|
| Write code directly | Write tutorials |
| Let new code self-document | Add redundant comments (never strip existing unrelated docstrings) |
| Fix bugs immediately | Explain the fix without verifying |
| Inline small things | Create unnecessary files |
| Name things clearly | Use abbreviations |
| Keep functions small | Write 100+ line functions |

> **Remember: Deliver verified working code with minimal surface churn.**

---

## 🔴 Self-Check Before Completing (MANDATORY)

**Before saying "task complete", verify:**

| Check | Question |
|-------|----------|
| ✅ **Goal met?** | Did I satisfy every acceptance criterion within `allowed_files`? |
| ✅ **Files edited?** | Did I modify all necessary files without touching unauthorized files? |
| ✅ **Code works?** | Did I execute physical verification commands (`exit_code == 0`)? |
| ✅ **No errors?** | Do static analysis, build, and test gates pass cleanly? |
| ✅ **Nothing forgotten?** | Are edge cases covered and baseline tests untouched? |

> 🔴 **Rule:** If ANY check fails, fix the implementation before reporting completion.

---

## Verification Scripts (Terukirdo v5.7 Mandatory Gate)

> 🔴 **CRITICAL:** Under Terukirdo Protocol v5.7, completion claims require raw command execution evidence (`exit_code == 0`) from the assigned `target_skill` verification script (`.agents/skills/<skill>/scripts/verify.ps1`), harness/unit test suites, and applicable project build/test gates.

## 🧠 Knowledge Modules (Fractal Skills)

### 1. [Agent → Script Mapping](./sub-skills/agent-script-mapping.md)
### 2. [🔴 Script Output Handling (READ → SUMMARIZE → ASK)](./sub-skills/script-output-handling-read-summarize-ask.md)
### 3. [❌ Errors Found (X items)](./sub-skills/errors-found-x-items.md)
### 4. [⚠️ Warnings (Y items)](./sub-skills/warnings-y-items.md)
### 5. [✅ Passed (Z items)](./sub-skills/passed-z-items.md)

> Consult the sub-skill modules above when mapping Terukirdo v5.7 agents to verification scripts and formatting evidence reports.
