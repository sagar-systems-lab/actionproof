from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from app.models.context import ContextFreshness, DecisionContext


class RetrievalDomain(str, Enum):
    POLICY = "policy"
    KNOWLEDGE = "knowledge"
    LIVE_STATE = "live_state"


class SourceType(str, Enum):
    POLICY = "policy"
    RUNBOOK = "runbook"
    HISTORY = "history"
    LIVE_STATE = "live_state"


class RetrievalIssueCode(str, Enum):
    UNAVAILABLE = "UNAVAILABLE"
    ZERO_RESULTS = "ZERO_RESULTS"
    INVALID_METADATA = "INVALID_METADATA"
    WRONG_SOURCE_TYPE = "WRONG_SOURCE_TYPE"
    WRONG_AUTHORITY = "WRONG_AUTHORITY"
    WRONG_ENVIRONMENT = "WRONG_ENVIRONMENT"
    WRONG_INCIDENT = "WRONG_INCIDENT"
    STALE = "STALE"
    STATE_PARSE_FAILED = "STATE_PARSE_FAILED"


class ContextRequirement(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    key: str = Field(min_length=1)
    domain: RetrievalDomain
    source_types: tuple[SourceType, ...]
    query: str = Field(min_length=1)
    required: bool = True
    top_k: int = Field(default=1, ge=1, le=10)
    incident_scoped: bool = False


class RawRetrievedDocument(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    document_id: str
    index_name: str
    content: str
    score: float
    metadata: dict[str, str]


class RetrievedEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    requirement_key: str
    document_id: str
    index_name: str
    source_type: SourceType
    authority: str
    version: str
    environment: str
    incident_id: str | None
    updated_at: datetime
    ttl_seconds: int
    freshness: ContextFreshness
    content: str
    score: float
    metadata: dict[str, str]


class RetrievalIssue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    requirement_key: str
    code: RetrievalIssueCode
    detail: str


class RetrievalMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    retrieval_us: int
    freshness_us: int


class RetrievalOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    context: DecisionContext
    requirements: tuple[ContextRequirement, ...]
    evidence: tuple[RetrievedEvidence, ...]
    issues: tuple[RetrievalIssue, ...]
    metrics: RetrievalMetrics
