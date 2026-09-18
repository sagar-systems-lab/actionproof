import asyncio
from pathlib import Path

from app.benchmark.models import BenchmarkRequest, BenchmarkScenario
from app.benchmark.runner import BenchmarkRunner
from app.retrieval.engine import RetrievalActionProofEngine
from app.retrieval.retriever import MossContextRetriever
from app.runtime.events import FlightRecorder
from app.runtime.orchestrator import ClosedLoopRuntime

from tests.retrieval_fakes import StatefulFakeMossBackend


def test_benchmark_reports_repeatable_percentiles(
    unsafe_state,
    tmp_path: Path,
) -> None:
    backend = StatefulFakeMossBackend(state=unsafe_state)
    events = FlightRecorder()
    engine = RetrievalActionProofEngine(
        MossContextRetriever(backend, environment="production"),
        events=events,
    )
    runtime = ClosedLoopRuntime(engine, backend, events=events)

    result = asyncio.run(
        BenchmarkRunner(
            runtime,
            environment="production",
            result_dir=tmp_path,
        ).run(
            BenchmarkRequest(
                iterations=100,
                scenario=BenchmarkScenario.MIXED,
                warmup=4,
            )
        )
    )

    assert result.iterations == 100
    assert result.errors == 0
    assert result.error_rate == 0
    assert result.metrics.moss_retrieval.p50_ns > 0
    assert result.metrics.moss_retrieval.p95_ns >= result.metrics.moss_retrieval.p50_ns
    assert result.metrics.total_preflight.p99_ns >= result.metrics.total_preflight.p95_ns
    assert result.metrics.total_preflight.max_ns >= result.metrics.total_preflight.p99_ns
    assert (tmp_path / result.result_file).is_file()
