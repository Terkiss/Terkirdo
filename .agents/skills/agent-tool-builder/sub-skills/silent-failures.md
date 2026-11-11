# ❌ Anti-Pattern: Silent Failures

Silent failures occur when a tool catches an exception, truncation, or partial write and returns `""`, `[]`, `null`, or `"Success"` without disclosing what went wrong.

## Why Silent Failures Break Agent Loops

- Returning `[]` on an expired API token convinces the LLM that **zero records exist**, leading to false conclusions or duplicate resource creation.
- Truncating 5,000 log lines to 100 lines without a `truncated: true` indicator causes the agent to miss critical errors at line 4,200 and declare the build healthy.
- Swallowing write failures causes downstream verification steps to debug phantom state mismatches.

## Anti-Pattern vs. Safe Pattern

```python
# ❌ BAD: Indistinguishable from "no matching orders exist"
def find_orders_bad(customer_id: str) -> list[dict]:
    try:
        return db.query_orders(customer_id, limit=100)
    except TimeoutError:
        return []


# ✅ GOOD: Distinguishes empty result, truncation, and operational failure
def find_orders_safe(customer_id: str) -> dict:
    try:
        rows = db.query_orders(customer_id, limit=101)
    except TimeoutError:
        return {
            "ok": False,
            "error_code": "DB_TIMEOUT",
            "message": "Order query timed out after 5000ms.",
            "recovery_hint": "Retry once or filter with a narrower date range.",
        }

    is_truncated = len(rows) > 100
    return {
        "ok": True,
        "count": min(len(rows), 100),
        "truncated": is_truncated,
        "next_cursor": rows[99]["id"] if is_truncated else None,
        "orders": rows[:100],
    }
```

## Mandatory Guarantees

1. **Empty != Error**: Empty success (`{"ok": true, "items": []}`) must never share the same representation as a failed call (`{"ok": false, ...}`).
2. **Explicit Truncation Metadata**: Whenever output is capped by line, byte, or row limits, return `truncated: true` plus continuation offset/cursor metadata.
3. **Verify Mutations**: After mutating state, confirm affected row/byte counts rather than returning unconditional `"OK"`.
