from enum import Enum

from pydantic import BaseModel, ConfigDict


class DecisionStatus(str, Enum):
    ALLOW = "ALLOW"
    CONFIRM = "CONFIRM"
    BLOCK = "BLOCK"


class DecisionCode(str, Enum):
    ALLOW_SAFE_STATE = "ALLOW_SAFE_STATE"
    BLOCK_RECONCILIATION_REQUIRED = "BLOCK_RECONCILIATION_REQUIRED"
    BLOCK_POLICY_UNAVAILABLE = "BLOCK_POLICY_UNAVAILABLE"
    BLOCK_CONTEXT_STALE = "BLOCK_CONTEXT_STALE"
    BLOCK_UNSAFE_STATE = "BLOCK_UNSAFE_STATE"
    CONFIRM_CONTEXT_INCOMPLETE = "CONFIRM_CONTEXT_INCOMPLETE"


class PolicyDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: DecisionStatus
    code: DecisionCode
    matched_rule: str
    reason: str
    recommended_next_action: str | None = None
