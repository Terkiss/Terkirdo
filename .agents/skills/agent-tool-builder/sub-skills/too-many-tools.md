# ❌ Anti-Pattern: Too Many Tools

Exposing dozens of fine-grained, overlapping tools inflates prompt token overhead on every turn and degrades LLM tool-selection accuracy.

## Why Tool Sprawl Hurts Performance

- Every eagerly loaded tool schema consumes context tokens on **every single model turn**, even when unused.
- Overlapping tools (`get_user_by_id`, `get_user_by_email`, `find_user_profile`, `lookup_account`) create decision paralysis and misrouting.
- Wrapping thin internal microservice endpoints 1:1 forces the agent to execute 6 sequential round-trips for one logical user intent.

## Consolidation Strategies

| Smell | Consolidation Fix |
| :--- | :--- |
| 5 lookup tools differing only by filter key | Merge into `get_user` accepting `id` OR `email` with clear validation |
| Raw CRUD endpoints requiring 4 sequential calls | Provide an intent-level workflow tool (e.g., `upsert_workspace_member`) |
| 80+ specialized domain tools loaded eagerly | Keep 10–20 core tools eager; expose specialized tools via lazy MCP schema discovery |
| Write tools mixed into read-only reviewer agents | Enforce least-privilege tool whitelists per agent role |

## Before vs. After Tool Surface

```json
// ❌ Too granular: 4 separate schema definitions for one resource
["list_open_tickets", "list_closed_tickets", "list_tickets_by_assignee", "search_ticket_titles"]

// ✅ Consolidated: 1 cohesive query tool with orthogonal filters
{
  "name": "query_tickets",
  "description": "List or search tickets filtered by status, assignee, and title keyword.",
  "inputSchema": {
    "type": "object",
    "additionalProperties": false,
    "properties": {
      "status": { "type": "string", "enum": ["open", "closed", "all"], "default": "open" },
      "assignee": { "type": "string", "description": "Optional username filter." },
      "query": { "type": "string", "description": "Optional keyword matched against title." }
    }
  }
}
```

## Related Skills

Works well with: `mcp-builder`, `clean-code`
