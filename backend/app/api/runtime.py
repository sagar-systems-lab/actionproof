from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.core.config import MossConfigurationError, MossSettings
from app.retrieval.moss_client import MossUnavailableError
from app.runtime.authorization import AuthorizationError
from app.runtime.events import RuntimeEvent
from app.runtime.factory import build_closed_loop_runtime
from app.runtime.models import HeroScenarioRequest, HeroScenarioResult
from app.runtime.orchestrator import ClosedLoopRuntime, RuntimeInvariantError
from app.runtime.state_store import StateUnavailableError

router = APIRouter(prefix="/api/runtime", tags=["runtime"])

_runtime: ClosedLoopRuntime | None = None


def get_closed_loop_runtime() -> ClosedLoopRuntime:
    global _runtime

    if _runtime is not None:
        return _runtime

    try:
        settings = MossSettings.from_env()
    except MossConfigurationError as exc:
        raise HTTPException(
            status_code=503,
            detail="Moss retrieval is not configured.",
        ) from exc

    _runtime = build_closed_loop_runtime(settings)
    return _runtime


@router.post("/hero", response_model=HeroScenarioResult)
async def run_hero_scenario(
    request: HeroScenarioRequest,
    runtime: ClosedLoopRuntime = Depends(get_closed_loop_runtime),
) -> HeroScenarioResult:
    try:
        return await runtime.run_hero_scenario(request.incident_id)
    except MossUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail="Moss runtime is unavailable.",
        ) from exc
    except (AuthorizationError, RuntimeInvariantError, StateUnavailableError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/events", response_model=list[RuntimeEvent])
def runtime_events(
    after_sequence: int = Query(default=0, ge=0),
    runtime: ClosedLoopRuntime = Depends(get_closed_loop_runtime),
) -> list[RuntimeEvent]:
    return list(runtime.events.snapshot(after_sequence=after_sequence))


@router.get("/events/stream")
async def runtime_event_stream(
    after_sequence: int = Query(default=0, ge=0),
    runtime: ClosedLoopRuntime = Depends(get_closed_loop_runtime),
) -> StreamingResponse:
    async def stream():
        async for event in runtime.events.stream(after_sequence=after_sequence):
            yield (
                f"id: {event.sequence}\n"
                f"event: {event.event.value}\n"
                f"data: {event.model_dump_json()}\n\n"
            )

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
