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


class ScenarioId(str, Enum):
    SAFE_RESTART = "safe-restart"
    UNSAFE_RESTART = "unsafe-restart"
    MISSING_CONTEXT = "missing-context"
    STALE_CONTEXT = "stale-context"
    SUCCESSFUL_RECOVERY = "successful-recovery"


class ScenarioDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: ScenarioId
    label: str
    description: str
    expected: str


class ProductScenarioResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    scenario_id: ScenarioId
    label: str
    description: str
    incident_id: str
    initial_state: SimulatorState | None
    primary_evaluation: EvaluationResult
    recovery: ExecutedActionResult | None = None
    final_evaluation: EvaluationResult | None = None
    final_state: SimulatorState | None = None
    events: tuple[RuntimeEvent, ...]
