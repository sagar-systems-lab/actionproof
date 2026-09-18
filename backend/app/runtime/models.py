from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from app.models.scenario import EvaluationResult
from app.models.state import SimulatorState

from .events import RuntimeEvent


class PostflightStatus(str, Enum):
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"


class ToolExecutionResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    success: bool
    state_changes: dict[str, str]
    message: str
    state: SimulatorState


class PostflightResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: PostflightStatus
    expected: dict[str, str]
    observed: dict[str, str]
    message: str


class ExecutedActionResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    evaluation: EvaluationResult
    execution: ToolExecutionResult
    postflight: PostflightResult


class HeroScenarioRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    incident_id: str = Field(default="INC-104", min_length=1)


class HeroScenarioResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    incident_id: str
    initial_state: SimulatorState
    blocked_restart: EvaluationResult
    recovery: ExecutedActionResult
    retry_restart: EvaluationResult
    final_state: SimulatorState
    events: tuple[RuntimeEvent, ...]
