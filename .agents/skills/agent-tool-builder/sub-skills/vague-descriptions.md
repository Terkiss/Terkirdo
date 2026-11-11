# ❌ Anti-Pattern: Vague Descriptions

Vague tool and parameter descriptions force the LLM to guess preconditions, side effects, and return shapes, causing wrong tool selection and wasted turns.

## Symptoms of a Vague Description

- Repeats the function name without adding behavioral detail (`update_user`: `"Updates a user"`).
- Hides destructive side effects, idempotency rules, or pagination caps.
- Fails to distinguish when to use Tool A vs. similar-sounding Tool B.

## Before vs. After Comparison

| Element | ❌ Vague (Causes Hallucination) | ✅ Precise (Guides Correct Selection) |
| :--- | :--- | :--- |
| **Tool `description`** | `"Gets file data."` | `"Read UTF-8 text contents of a repository file. Returns at most 800 lines per call. Do NOT use for binary archives; use 'inspect_artifact' instead."` |
| **`path` param** | `"The path"` | `"Repository-relative path using forward slashes (e.g. 'src/auth/login.ts'). Must not start with '/' or contain '..'."` |
| **`force` param** | `"Force flag"` | `"When true, overwrites an existing output file. Defaults to false, which aborts with ALREADY_EXISTS if the file exists."` |

## The 4-Part Tool Description Formula

Every production tool description should answer four questions in 2–4 concise sentences:

1. **Action & Output**: What exact operation does it perform and what structure/truncation limit does it return?
2. **Use When**: Which concrete scenario makes this the right tool?
3. **Do Not Use When**: Which adjacent tool should be chosen instead for similar tasks?
4. **Side Effects / Preconditions**: Does it mutate state, require prior authentication/discovery, or incur external calls?

```json
{
  "name": "archive_completed_tasks",
  "description": "Move tasks with status='done' older than `older_than_days` into cold archive storage and return the count of archived records. Mutates database state idempotently. Use for scheduled cleanup; do NOT use to delete active tasks (use 'cancel_task' instead)."
}
```

If two developers reading only your `description` would disagree on what the tool returns on an empty match, rewrite the description before shipping.
