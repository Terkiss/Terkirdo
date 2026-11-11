# Best Practices

- **Return Structured, Actionable Errors**: Set `isError: true` on tool execution failures and include concrete recovery hints so the agent can self-correct.
- **Never Leak Internal Stack Traces or Secrets**: Sanitize file paths, credentials, and raw database exceptions before returning tool output.
- **Keep `stdout` Pure on Stdio Servers**: Route all operational logging to `stderr` or log files so JSON-RPC framing is never corrupted.
- **Bound Output Size**: Cap payload rows/bytes and include pagination cursors so a single tool call cannot overflow the model context window.
