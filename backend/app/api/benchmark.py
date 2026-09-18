from __future__ import annotations

import asyncio
from time import monotonic
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from app.benchmark import BenchmarkRequest, BenchmarkRun, BenchmarkRunner
from app.benchmark.models import BenchmarkJob
from app.core.config import MossConfigurationError, MossSettings
from app.retrieval.moss_client import MossUnavailableError
from app.runtime.orchestrator import ClosedLoopRuntime

from .runtime import get_closed_loop_runtime

router = APIRouter(prefix="/api/benchmarks", tags=["benchmarks"])

_latest: BenchmarkRun | None = None
_job: BenchmarkJob | None = None
_task: asyncio.Task[None] | None = None
_started_at: float | None = None


def _settings() -> MossSettings:
    try:
        return MossSettings.from_env()
    except MossConfigurationError as exc:
        raise HTTPException(
            status_code=503,
            detail="Latency benchmark is unavailable until Moss is configured.",
        ) from exc


def _snapshot() -> BenchmarkJob:
    if _job is None:
        raise HTTPException(status_code=404, detail="No benchmark has been started yet.")

    elapsed = _job.elapsed_seconds
    if _job.state == "running" and _started_at is not None:
        elapsed = monotonic() - _started_at
    return _job.model_copy(update={"elapsed_seconds": round(elapsed, 1)})


@router.post("/start", response_model=BenchmarkJob)
async def start_benchmark(
    request: BenchmarkRequest,
    runtime: ClosedLoopRuntime = Depends(get_closed_loop_runtime),
) -> BenchmarkJob:
    global _job, _task, _started_at

    if _task is not None and not _task.done():
        raise HTTPException(
            status_code=409,
            detail="A latency benchmark is already running.",
        )

    settings = _settings()
    job_id = f"JOB-{uuid4().hex[:10].upper()}"
    _started_at = monotonic()
    _job = BenchmarkJob(
        job_id=job_id,
        state="running",
        scenario=request.scenario,
        iterations=request.iterations,
        warmup=request.warmup,
        message="Preparing benchmark state.",
    )

    def progress(stage: str, completed: int, total: int) -> None:
        global _job
        if _job is None:
            return
        if stage == "warmup":
            _job = _job.model_copy(
                update={
                    "completed_warmup": completed,
                    "message": f"Warmup {completed}/{total}",
                }
            )
        else:
            _job = _job.model_copy(
                update={
                    "completed_iterations": completed,
                    "message": f"Measured {completed}/{total}",
                }
            )

    async def execute() -> None:
        global _latest, _job, _started_at
        assert _job is not None
        try:
            result = await BenchmarkRunner(
                runtime,
                environment=settings.environment,
            ).run(request, progress=progress)
            _latest = result
            elapsed = monotonic() - _started_at if _started_at is not None else 0.0
            _job = _job.model_copy(
                update={
                    "state": "completed",
                    "completed_warmup": request.warmup,
                    "completed_iterations": request.iterations,
                    "elapsed_seconds": round(elapsed, 1),
                    "message": "Benchmark complete.",
                    "result": result,
                }
            )
        except MossUnavailableError:
            elapsed = monotonic() - _started_at if _started_at is not None else 0.0
            _job = _job.model_copy(
                update={
                    "state": "failed",
                    "elapsed_seconds": round(elapsed, 1),
                    "message": "Moss became unavailable during the benchmark.",
                }
            )
        except Exception:
            elapsed = monotonic() - _started_at if _started_at is not None else 0.0
            _job = _job.model_copy(
                update={
                    "state": "failed",
                    "elapsed_seconds": round(elapsed, 1),
                    "message": "Benchmark integrity check failed.",
                }
            )

    _task = asyncio.create_task(execute())
    return _snapshot()


@router.get("/current", response_model=BenchmarkJob)
def current_benchmark() -> BenchmarkJob:
    return _snapshot()


@router.get("/latest", response_model=BenchmarkRun)
def latest_benchmark() -> BenchmarkRun:
    if _latest is None:
        raise HTTPException(status_code=404, detail="No benchmark has been run yet.")
    return _latest
