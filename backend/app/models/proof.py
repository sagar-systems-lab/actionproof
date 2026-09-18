from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from .action import NormalizedAction, RiskLevel
from .context import ContextFreshness
from .decision import DecisionCode, DecisionStatus


class EvidenceFact(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source: str
    key: str
    value: str
    document_id: str | None = None
    source_type: str | None = None
    authority: str | None = None
    version: str | None = None
    freshness: ContextFreshness | None = None
    score: float | None = None
    updated_at: datetime | None = None


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
