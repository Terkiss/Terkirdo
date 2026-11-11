# Input Schema Design

Every MCP tool must declare a strict JSON Schema `inputSchema` object:

| Field | Required? | Guideline |
|-------|-----------|-----------|
| `type` | Yes (`"object"`) | Root schema of an MCP tool input must always be `"object"` |
| `properties` | Yes | Define explicit types, bounds (`enum`, `minimum`, `maxLength`), and units |
| `required` | Recommended | List mandatory parameter names explicitly |
| `additionalProperties` | Recommended (`false`) | Reject misspelled or hallucinated argument keys early |
| `description` | Yes | Explain exact behavior, format, and defaults in plain language |

Validate arguments at the server boundary even when the host pre-validates schemas.
