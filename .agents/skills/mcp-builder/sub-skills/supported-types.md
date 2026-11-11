# Supported Types

MCP tool responses and resource contents support typed content blocks:

| Type | Encoding | Notes |
|------|----------|-------|
| **Text** | UTF-8 plain text / JSON / Markdown | Primary format for structured tool outputs and code snippets |
| **Images** | Base64 data + explicit `mimeType` (`image/png`, `image/jpeg`) | Compress large screenshots before encoding |
| **Embedded Resources / Files** | URI + `mimeType` + text or Base64 blob | Prefer URI references for large binary artifacts |

Always set an accurate `mimeType` so host UIs and multimodal models decode payloads properly.
