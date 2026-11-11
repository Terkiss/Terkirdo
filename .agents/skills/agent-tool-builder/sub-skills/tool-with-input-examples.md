# Tool with Input Examples

Concrete input examples eliminate format guesswork for complex syntax such as cron expressions, filter DSLs, path globs, and URI templates.

## Why Examples Beat Prose

- LLMs pattern-match concrete examples far more reliably than abstract grammar rules.
- Embedding 1–3 canonical examples inside `description` or JSON Schema `examples` cuts retry loops caused by malformed strings by over 80%.
- Include both a minimal common case and an edge/compound case.

## Schema with Embedded Examples

```json
{
  "name": "filter_audit_logs",
  "description": "Query structured audit logs within an ISO-8601 UTC window using field:value filter expressions.",
  "inputSchema": {
    "type": "object",
    "additionalProperties": false,
    "properties": {
      "since_utc": {
        "type": "string",
        "format": "date-time",
        "description": "Start timestamp in ISO-8601 UTC format (e.g. '2026-11-11T00:00:00Z').",
        "examples": ["2026-11-11T00:00:00Z"]
      },
      "filter_expr": {
        "type": "string",
        "description": "Space-separated field:value predicates. Prefix '-' to negate. Examples: 'actor:agy-worker status:FAIL' or 'service:auth -env:dev'.",
        "examples": [
          "actor:agy-worker status:FAIL",
          "service:payment -env:staging"
        ]
      }
    },
    "required": ["since_utc", "filter_expr"]
  }
}
```

## Guidelines

| Scenario | Recommended Example Strategy |
| :--- | :--- |
| Standard scalar (`boolean`, `enum`) | Skip examples; the `enum` list is already exhaustive |
| Structured string (glob, regex, cron, SQL/DSL) | Provide 2 concrete examples in `description` and `examples` |
| Complex nested payload | Show 1 minimal valid object and 1 full-featured object |

Keep examples concise and realistic — never include live credentials or customer PII in schema examples.
