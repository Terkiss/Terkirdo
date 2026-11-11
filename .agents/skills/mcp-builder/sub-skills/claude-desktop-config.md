# MCP Host Configuration (Antigravity CLI & Standard MCP Hosts)

Standard MCP hosts — including **Antigravity CLI (`agy`)**, VS Code / Cursor MCP integrations, and Claude Desktop — register local `stdio` servers using a unified `mcpServers` JSON structure:

| Field | Purpose |
|-------|---------|
| `command` | Executable binary or runtime (`python`, `node`, `uvx`, `npx`) |
| `args` | Ordered array of CLI arguments passed to `command` |
| `env` | Scoped environment variables (API keys, `PYTHONUTF8=1`, config paths) |

## Cross-Host Compatible `mcpServers` Example

```json
{
  "mcpServers": {
    "project-analytics": {
      "command": "python",
      "args": ["-m", "mcp_project_analytics.server"],
      "env": {
        "PYTHONUTF8": "1",
        "ANALYTICS_READONLY_TOKEN": "${ANALYTICS_READONLY_TOKEN}"
      }
    }
  }
}
```

## Host Compatibility Notes

- **Antigravity CLI (`agy`)**: Supports eager and lazy-loaded MCP tool schemas under `<appDataDir>/mcp/<serverName>/`; ensure every tool has a self-contained JSON Schema and concise `description` so lazy schema inspection succeeds cleanly.
- **Windows Path Safety**: Prefer forward slashes (`D:/tools/server.py`) or escaped backslashes (`D:\\tools\\server.py`) in `args` and always set `"PYTHONUTF8": "1"` for Python-based stdio servers on Windows.
