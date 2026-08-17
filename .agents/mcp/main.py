import re
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from .security_hook import ValidationResult, SecurityEventContext, SecurityLevel, EventType

logger = logging.getLogger("mcp.immune_system")

class MCPImmuneSystem:
    """
    Main middleware class for inspecting and sanitizing all MCP traffic.
    """
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = Path(__file__).parent / "rules.yaml"
            
        try:
            with open(config_path, "r") as f:
                self.config = yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Failed to load rules.yaml: {e}")
            raise RuntimeError(f"Fail-closed policy: Missing or invalid rules.yaml. Error: {e}")
            
        self.blacklist_patterns = self._compile_blacklist(self.config.get("blacklist", []))
        self.whitelist_patterns = self._compile_patterns(self.config.get("whitelist", []))
        self.secret_patterns = self._compile_patterns(self.config.get("secrets", []))
        
    def _compile_patterns(self, patterns: List[str]) -> List[re.Pattern]:
        # Added re.DOTALL to prevent \n bypass in generic regexes
        return [re.compile(p, re.IGNORECASE | re.DOTALL) for p in patterns]
        
    def _compile_blacklist(self, items: List[Dict[str, str]]) -> List[Tuple[re.Pattern, EventType]]:
        compiled = []
        for item in items:
            pattern_str = item.get("pattern", "")
            event_type_str = item.get("type", "PROMPT_INJECTION")
            try:
                event_type = EventType(event_type_str)
            except ValueError:
                event_type = EventType.PROMPT_INJECTION
            # Added re.DOTALL and avoid excessive `.*`
            compiled.append((re.compile(pattern_str, re.IGNORECASE | re.DOTALL), event_type))
        return compiled

    def _check_rbac(self, agent_id: str, tool_name: str) -> bool:
        # TODO: Implement actual RBAC validation logic here
        return True
        
    def _check_params_recursive(self, params: Any, tool_name: str) -> Optional[Tuple[EventType, str]]:
        if isinstance(params, str):
            threat = self._detect_threat(params)
            if threat:
                return threat, params
            
            if tool_name in ["read_file", "write_file", "execute_command"]:
                if self._detect_path_traversal(params):
                    return EventType.PATH_TRAVERSAL, params
                    
        elif isinstance(params, dict):
            for v in params.values():
                res = self._check_params_recursive(v, tool_name)
                if res:
                    return res
                    
        elif isinstance(params, list):
            for v in params:
                res = self._check_params_recursive(v, tool_name)
                if res:
                    return res
                    
        return None

    def validate_ingress(self, agent_id: str, tool_name: str, params: Dict[str, Any]) -> ValidationResult:
        # 1. Check Tool Allowlist for Agent
        if not self._check_rbac(agent_id, tool_name):
            return self._build_rejection(agent_id, tool_name, EventType.UNAUTHORIZED_ACCESS)

        # 2. Iterate through parameters recursively and scan for threats
        finding = self._check_params_recursive(params, tool_name)
        if finding:
            event_type, payload = finding
            return self._build_rejection(agent_id, tool_name, event_type, payload=payload)

        return ValidationResult(is_safe=True, sanitized_params=params)

    def validate_egress(self, raw_output: str) -> str:
        # Prevent PII or Secrets from leaking back to the agent
        redacted_output = raw_output
        for pattern in self.secret_patterns:
            redacted_output = pattern.sub("[REDACTED]", redacted_output)
        return redacted_output

    def _detect_threat(self, payload: str) -> Optional[EventType]:
        for pattern, event_type in self.blacklist_patterns:
            if pattern.search(payload):
                return event_type
        return None
        
    def _detect_path_traversal(self, payload: str) -> bool:
        traversal_pattern = re.compile(r"(\.\./|\.\.\\|%2e%2e%2f|%2e%2e%5c)", re.IGNORECASE | re.DOTALL)
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
