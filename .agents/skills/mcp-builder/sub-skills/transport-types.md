# Transport Types

Choose the MCP transport that matches deployment topology and process isolation:

| Type | Primary Use Case | Notes |
|------|------------------|-------|
| **Stdio** | Local subprocess / CLI hosts (Antigravity CLI, IDEs) | Never write debug logs to `stdout` (reserved for JSON-RPC frames); log only to `stderr` |
| **Streamable HTTP / SSE** | Remote or shared multi-client MCP services | Enforce TLS, authentication headers, and request timeouts |
| **WebSocket** | Full-duplex persistent local/remote daemons | Handle reconnects and backpressure explicitly |

Default to `Stdio` for local developer tools and `Streamable HTTP` for shared team infrastructure.
