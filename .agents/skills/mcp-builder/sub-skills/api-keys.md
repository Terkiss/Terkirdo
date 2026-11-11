# API Keys & Secret Handling

- **Inject via Environment Variables**: Pass credentials through host-configured `env` blocks or OS secret stores — never hardcode keys in source files or tool schemas.
- **Redact Logs & Error Messages**: Mask `Authorization` headers, tokens, and connection strings in both `stderr` logs and returned tool payloads.
- **Enforce Least Privilege**: Scope API keys to the minimum read/write permissions required by the MCP server's declared tools.
- **Fail Fast on Startup**: Validate required environment variables when the server boots and emit a clear diagnostic message if missing.
