# URI Patterns

MCP Resources use canonical custom or standard URI schemes so hosts can list, subscribe, and read context deterministically:

| Pattern | Example | When to Use |
|---------|---------|-------------|
| **Fixed** | `docs://architecture/overview` | Singleton configuration or canonical reference docs |
| **Parameterized Template** | `users://{userId}/profile` | Entity lookups exposed via RFC 6570 URI templates |
| **Collection** | `files://workspace/logs` | Paginated or directory-scoped resource listings |

Always canonicalize and validate path segments inside URI handlers to prevent path traversal (`..`).
