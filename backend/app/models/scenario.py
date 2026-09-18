from pydantic import BaseModel, ConfigDict

from .action import ActionIntent, NormalizedAction
from .context import DecisionContext
from .decision import PolicyDecision
from .proof import ProofPacket


class EvaluationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: ActionIntent
    context: DecisionContext


class MossEvaluationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: ActionIntent


class EvaluationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: NormalizedAction
    decision: PolicyDecision
    proof: ProofPacket
