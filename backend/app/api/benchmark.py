from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.benchmark import BenchmarkRequest, BenchmarkRun, BenchmarkRunner
from app.core.config import MossConfigurationError, MossSettings
from app.retrieval.moss_client import MossUnavailableError
from app.runtime.orchestrator import ClosedLoopRuntime

from .runtime import get_closed_loop_runtime

router = APIRouter(prefix="/api/benchmarks", tags=["benchmarks"])

_latest: BenchmarkRun | None = None


@router.post("/run", response_model=BenchmarkRun)
async def run_benchmark(
    request: BenchmarkRequest,
    runtime: ClosedLoopRuntime = Depends(get_closed_loop_runtime),
) -> BenchmarkRun:
    global _latest

    try:
        settings = MossSettings.from_env()
    except MossConfigurationError as exc:
        raise HTTPException(
            status_code=503,
            detail="Latency benchmark is unavailable until Moss is configured.",
        ) from exc

    try:
        result = await BenchmarkRunner(
            runtime,
            environment=settings.environment,
        ).run(request)
    except MossUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail="Moss became unavailable during the benchmark run.",
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=409,
            detail="Benchmark integrity check failed.",
        ) from exc

    _latest = result
    return result


@router.get("/latest", response_model=BenchmarkRun)
def latest_benchmark() -> BenchmarkRun:
    if _latest is None:
        raise HTTPException(status_code=404, detail="No benchmark has been run yet.")
    return _latest
