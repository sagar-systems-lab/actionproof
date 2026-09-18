from __future__ import annotations

import json
import math
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from typing import Callable

from app.models.action import ActionIntent
from app.models.decision import DecisionCode
from app.models.state import (
    ConnectionState,
    HealthState,
    OutstandingState,
    ReconciliationState,
    ServiceState,
    SimulatorState,
)
from app.runtime.orchestrator import ClosedLoopRuntime

from .models import (
    BenchmarkMetrics,
    BenchmarkRequest,
    BenchmarkRun,
    BenchmarkSample,
    BenchmarkScenario,
    LatencyDistribution,
)


class BenchmarkRunner:
    def __init__(
        self,
        runtime: ClosedLoopRuntime,
        *,
        environment: str,
        result_dir: Path | None = None,
    ) -> None:
        self.runtime = runtime
        self.environment = environment
        root = Path(__file__).resolve().parents[3]
        configured = os.getenv("ACTIONPROOF_BENCHMARK_DIR")
        self.result_dir = result_dir or (
            Path(configured) if configured else root / "benchmarks" / "results"
        )
        self.root = root

    async def run(
        self,
        request: BenchmarkRequest,
        progress: Callable[[str, int, int], None] | None = None,
    ) -> BenchmarkRun:
        await self._prepare_states()

        for index in range(request.warmup):
            lane = self._lane(request.scenario, index)
            await self._evaluate(lane, iteration=-(index + 1))
            if progress is not None:
                progress("warmup", index + 1, request.warmup)

        samples: list[BenchmarkSample] = []
        for index in range(request.iterations):
            lane = self._lane(request.scenario, index)
            samples.append(await self._sample(lane, index + 1))
            if progress is not None:
                progress("measure", index + 1, request.iterations)

        errors = sum(sample.error is not None for sample in samples)
        valid = [sample for sample in samples if sample.error is None]
        if not valid:
            raise RuntimeError("benchmark produced no valid samples")

        metrics = BenchmarkMetrics(
            normalization=self._distribution(
                [self._required(sample.normalization_ns) for sample in valid]
            ),
            context_resolve=self._distribution(
                [self._required(sample.context_resolve_ns) for sample in valid]
            ),
            moss_retrieval=self._distribution(
                [self._required(sample.moss_retrieval_ns) for sample in valid]
            ),
            freshness=self._distribution(
                [self._required(sample.freshness_ns) for sample in valid]
            ),
            policy_eval=self._distribution(
                [self._required(sample.policy_eval_ns) for sample in valid]
            ),
            proof_build=self._distribution(
                [self._required(sample.proof_build_ns) for sample in valid]
            ),
            total_preflight=self._distribution(
                [self._required(sample.total_preflight_ns) for sample in valid]
            ),
        )

        now = datetime.now(timezone.utc)
        run_id = f"BENCH-{now:%Y%m%dT%H%M%SZ}-{uuid4().hex[:8].upper()}"
        result_file = f"{run_id.lower()}.json"
        run = BenchmarkRun(
            run_id=run_id,
            revision=self._revision(),
            environment=self.environment,
            timestamp=now,
            scenario=request.scenario,
            warmup=request.warmup,
            iterations=request.iterations,
            errors=errors,
            error_rate=errors / request.iterations,
            percentile_method="nearest-rank",
            metrics=metrics,
            result_file=result_file,
        )

        self._store(run, samples)
        return run

    async def _prepare_states(self) -> None:
        safe = SimulatorState(
            connection=ConnectionState.CONNECTED,
            reconciliation=ReconciliationState.COMPLETE,
            service=ServiceState.RUNNING,
            health=HealthState.HEALTHY,
            outstanding=OutstandingState.CLEAR,
        )
        unsafe = SimulatorState(
            connection=ConnectionState.DISCONNECTED,
            reconciliation=ReconciliationState.INCOMPLETE,
            service=ServiceState.RUNNING,
            health=HealthState.DEGRADED,
            outstanding=OutstandingState.UNKNOWN,
        )

        await self.runtime.publisher.upsert_live_state(
            "BENCH-SAFE",
            safe,
            version="benchmark-safe",
            ttl_seconds=3600,
        )
        await self.runtime.publisher.upsert_live_state(
            "BENCH-UNSAFE",
            unsafe,
            version="benchmark-unsafe",
            ttl_seconds=3600,
        )
        self.runtime.state_store.set("BENCH-SAFE", safe)
        self.runtime.state_store.set("BENCH-UNSAFE", unsafe)

    async def _sample(
        self,
        lane: BenchmarkScenario,
        iteration: int,
    ) -> BenchmarkSample:
        try:
            result = await self._evaluate(lane, iteration=iteration)
            latency = result.proof.latency
            return BenchmarkSample(
                iteration=iteration,
                lane=lane,
                decision_code=result.decision.code.value,
                normalization_ns=latency.normalization_ns,
                context_resolve_ns=latency.context_resolve_ns,
                moss_retrieval_ns=latency.moss_retrieval_ns,
                freshness_ns=latency.freshness_ns,
                policy_eval_ns=latency.policy_eval_ns,
                proof_build_ns=latency.proof_build_ns,
                total_preflight_ns=latency.total_preflight_ns,
            )
        except Exception as exc:
            return BenchmarkSample(
                iteration=iteration,
                lane=lane,
                decision_code=None,
                normalization_ns=None,
                context_resolve_ns=None,
                moss_retrieval_ns=None,
                freshness_ns=None,
                policy_eval_ns=None,
                proof_build_ns=None,
                total_preflight_ns=None,
                error=f"{type(exc).__name__}: {exc}",
            )

    async def _evaluate(
        self,
        lane: BenchmarkScenario,
        *,
        iteration: int,
    ):
        incident_id = "BENCH-SAFE" if lane is BenchmarkScenario.SAFE else "BENCH-UNSAFE"
        trace_id = f"TRACE-BENCH-{lane.value.upper()}-{iteration}-{uuid4().hex[:8].upper()}"
        intent = ActionIntent(
            action_id=f"{trace_id}-RESTART",
            trace_id=trace_id,
            actor="benchmark-agent",
            text="Restart the service.",
            incident_id=incident_id,
            timestamp=datetime.now(timezone.utc),
        )
        result = await self.runtime.engine.evaluate(intent)

        expected = (
            DecisionCode.ALLOW_SAFE_STATE
            if lane is BenchmarkScenario.SAFE
            else DecisionCode.BLOCK_RECONCILIATION_REQUIRED
        )
        if result.decision.code is not expected:
            raise RuntimeError(
                f"{lane.value} lane returned {result.decision.code.value}, "
                f"expected {expected.value}"
            )
        return result

    @staticmethod
    def _lane(
        scenario: BenchmarkScenario,
        index: int,
    ) -> BenchmarkScenario:
        if scenario is BenchmarkScenario.MIXED:
            return BenchmarkScenario.SAFE if index % 2 == 0 else BenchmarkScenario.UNSAFE
        return scenario

    @classmethod
    def _distribution(cls, values: list[int]) -> LatencyDistribution:
        ordered = sorted(values)
        return LatencyDistribution(
            p50_ns=cls._nearest_rank(ordered, 0.50),
            p95_ns=cls._nearest_rank(ordered, 0.95),
            p99_ns=cls._nearest_rank(ordered, 0.99),
            max_ns=ordered[-1],
        )

    @staticmethod
    def _nearest_rank(ordered: list[int], percentile: float) -> int:
        rank = max(1, math.ceil(percentile * len(ordered)))
        return ordered[rank - 1]

    @staticmethod
    def _required(value: int | None) -> int:
        if value is None:
            raise RuntimeError("valid benchmark sample is missing latency data")
        return value

    def _revision(self) -> str:
        explicit = os.getenv("ACTIONPROOF_REVISION")
        if explicit:
            return explicit
        try:
            completed = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.root,
                check=True,
                capture_output=True,
                text=True,
                timeout=2,
            )
            return completed.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return "unknown"

    def _store(
        self,
        run: BenchmarkRun,
        samples: list[BenchmarkSample],
    ) -> None:
        self.result_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "summary": run.model_dump(mode="json"),
            "samples": [sample.model_dump(mode="json") for sample in samples],
        }
        destination = self.result_dir / run.result_file
        destination.write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )
