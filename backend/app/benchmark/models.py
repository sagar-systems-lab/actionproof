from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class BenchmarkScenario(str, Enum):
    SAFE = "safe"
    UNSAFE = "unsafe"
    MIXED = "mixed"


class BenchmarkRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    iterations: Literal[100, 500, 1000] = 100
    scenario: BenchmarkScenario = BenchmarkScenario.MIXED
    warmup: int = Field(default=10, ge=0, le=100)


class LatencyDistribution(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    p50_ns: int
    p95_ns: int
    p99_ns: int
    max_ns: int


class BenchmarkMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    normalization: LatencyDistribution
    context_resolve: LatencyDistribution
    moss_retrieval: LatencyDistribution
    freshness: LatencyDistribution
    policy_eval: LatencyDistribution
    proof_build: LatencyDistribution
    total_preflight: LatencyDistribution


class BenchmarkSample(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    iteration: int
    lane: BenchmarkScenario
    decision_code: str | None
    normalization_ns: int | None
    context_resolve_ns: int | None
    moss_retrieval_ns: int | None
    freshness_ns: int | None
    policy_eval_ns: int | None
    proof_build_ns: int | None
    total_preflight_ns: int | None
    error: str | None = None


class BenchmarkRun(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    run_id: str
    revision: str
    environment: str
    timestamp: datetime
    scenario: BenchmarkScenario
    warmup: int
    iterations: int
    errors: int
    error_rate: float
    percentile_method: str
    metrics: BenchmarkMetrics
    result_file: str
