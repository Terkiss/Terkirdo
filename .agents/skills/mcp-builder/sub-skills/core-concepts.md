# Core Concepts

MCP servers expose three primary capability primitives to host agents:

| Concept | Purpose | Typical Direction |
|---------|---------|-------------------|
| **Tools** | Executable functions the AI model can invoke (with JSON Schema validation) | Model-controlled |
| **Resources** | Read-only structured context or files addressed by URI | Application/User-controlled |
| **Prompts** | Reusable, parameterized workflow templates | User-initiated |

Design Tools for actions/queries with bounded inputs, and Resources for addressable read-only state.
