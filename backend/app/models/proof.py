from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from .action import NormalizedAction, RiskLevel
from .decision import DecisionCode, DecisionStatus


class EvidenceFact(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source: str
    key: str
    value: str


class LatencyBreakdown(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    retrieval_us: int = 0
    freshness_us: int = 0
    policy_us: int = 0
    proof_us: int = 0
    total_us: int = 0


class ProofPacket(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    proof_id: str
    trace_id: str
    action: NormalizedAction
    risk: RiskLevel
    decision: DecisionStatus
    decision_code: DecisionCode
    evidence: tuple[EvidenceFact, ...]
    matched_policy: str
    safe_next_action: str | None
    latency: LatencyBreakdown
