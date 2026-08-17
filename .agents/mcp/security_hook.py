from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from enum import Enum
from datetime import datetime, timezone

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
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    agent_id: str
    tool_name: str
    suspicious_payload: Optional[str] = None
    severity: SecurityLevel
    event_type: EventType

class ValidationResult(BaseModel):
    is_safe: bool
    sanitized_params: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    security_event: Optional[SecurityEventContext] = None
