# Tool Error Handling

Returning structured, actionable error payloads that enable the LLM to self-correct on the next turn instead of guessing or looping.

## Principles of Self-Correcting Tool Errors

1. **State What Failed and Why**: Distinguish input validation errors (`INVALID_ARGUMENT`), missing entities (`NOT_FOUND`), permission blocks (`PERMISSION_DENIED`), and transient upstream faults (`RATE_LIMITED` / `UPSTREAM_UNAVAILABLE`).
2. **Tell the Agent How to Recover**: Include a `hint` or `allowed_values` field pointing to the exact corrective action (e.g., which tool to call first to discover valid IDs, or how long to wait before retrying).
3. **Never Leak Raw Stack Traces or Secrets**: Strip internal file paths, SQL queries, and tokens before returning error text to the model context.
4. **Explicit `isError: true` Flag**: In MCP and structured tool protocols, mark failed tool results explicitly so orchestrators do not mistake error text for valid data.

## Before vs. After Error Responses

| Situation | ❌ Unhelpful Error | ✅ Self-Correcting Error |
| :--- | :--- | :--- |
| Invalid enum | `"Error 400: Bad Request"` | `"Invalid 'priority': 'urgent'. Allowed values: ['P0', 'P1', 'P2', 'P3']."` |
| Unknown ID | `"NullReferenceException at line 84"` | `"Project 'proj_99' not found. Call 'list_projects' first to retrieve valid project IDs."` |
| Rate limit | `"Request failed"` | `"Rate limit exceeded (HTTP 429). Retry after 5 seconds or narrow your query page size."` |

## Reference Implementation Pattern (Python)

```python
def get_deployment_status(env_name: str) -> dict:
    valid_envs = ("dev", "staging", "prod")
    if env_name not in valid_envs:
        return {
            "ok": False,
            "error_code": "INVALID_ENVIRONMENT",
            "message": f"Unknown environment '{env_name}'.",
            "recovery_hint": f"Pass one of {list(valid_envs)}.",
        }
    # Execute lookup safely...
    return {"ok": True, "environment": env_name, "status": "healthy"}
```

Always design error messages assuming the reader is an LLM deciding its very next tool call without access to your server source code.
