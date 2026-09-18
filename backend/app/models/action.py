from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ToolName(str, Enum):
    EXECUTION_SERVICE = "execution_service"


class Operation(str, Enum):
    RESTART = "restart"
    RECONCILE = "reconcile"
    RECOVER_CONNECTION = "recover_connection"
    RESUME = "resume"


class ActionIntent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    action_id: str = Field(min_length=1)
    trace_id: str = Field(min_length=1)
    actor: str = Field(min_length=1)
    text: str = Field(min_length=1)
    incident_id: str | None = None
    timestamp: datetime

    @field_validator("timestamp")
    @classmethod
    def timestamp_must_include_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must include a timezone")
        return value


class NormalizedAction(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    action_id: str
    trace_id: str
    actor: str
    tool: ToolName
    operation: Operation
    arguments: dict[str, Any] = Field(default_factory=dict)
    impact: RiskLevel
    incident_id: str
    timestamp: datetime
