# Tool Schema Design

Creating clear, unambiguous JSON Schema definitions that constrain LLM tool calls and prevent malformed inputs before execution.

## Core Principles

1. **Constrain the State Space**: Prefer `enum`, `minimum`/`maximum`, `minLength`/`maxLength`, and `format` over open-ended `string` fields whenever valid values are bounded.
2. **Reject Hallucinated Keys**: Set `"additionalProperties": false` on every object schema so unknown fields fail deterministically at validation time.
3. **Document Units & Formats in Property Descriptions**: Explicitly state units (`timeout_ms` in milliseconds, ISO-8601 UTC timestamps, repository-relative forward-slash paths).
4. **Separate Required vs. Optional Parameters**: Put mandatory fields in `required` and state exact default behavior in optional parameter descriptions.

## Production JSON Schema Example

```json
{
  "name": "search_issue_tracker",
  "description": "Search project issues by status, priority, and text query. Returns at most `limit` matching issues ordered by updated_at descending.",
  "inputSchema": {
    "type": "object",
    "additionalProperties": false,
    "properties": {
      "query": {
        "type": "string",
        "minLength": 1,
        "maxLength": 200,
        "description": "Case-insensitive keyword or phrase matched against issue title and body."
      },
      "status": {
        "type": "string",
        "enum": ["open", "in_progress", "closed"],
        "description": "Filter by workflow state. Defaults to 'open' when omitted."
      },
      "limit": {
        "type": "integer",
        "minimum": 1,
        "maximum": 50,
        "default": 10,
        "description": "Maximum number of issues to return (1 to 50, default 10)."
      }
    },
    "required": ["query"]
  }
}
```

## Quick Checklist

- Every parameter name is self-explanatory (`timeout_ms`, not `t`).
- Mutually exclusive parameters are either combined into a discriminated union/mode enum or explicitly documented.
- Nested depths stay shallow (at most 2 levels) to minimize JSON serialization mistakes by smaller models.
