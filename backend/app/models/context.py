from enum import Enum

from pydantic import BaseModel, ConfigDict

from .state import SimulatorState


class ContextFreshness(str, Enum):
    FRESH = "FRESH"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"


class DecisionContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    state: SimulatorState | None = None
    required_context_complete: bool = True
    freshness: ContextFreshness = ContextFreshness.FRESH
    policy_available: bool = True
    retrieval_failed: bool = False
