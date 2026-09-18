from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.core.config import MossConfigurationError, MossSettings
from app.retrieval.moss_client import MossUnavailableError
from app.runtime.authorization import AuthorizationError
from app.runtime.events import RuntimeEvent
from app.runtime.factory import build_closed_loop_runtime
from app.runtime.models import (
    HeroScenarioRequest,
    HeroScenarioResult,
    ProductScenarioResult,
    ScenarioDefinition,
    ScenarioId,
)
from app.runtime.orchestrator import ClosedLoopRuntime, RuntimeInvariantError
from app.runtime.scenarios import ProductScenarioRunner, SCENARIOS
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
            detail="Required context retrieval is not configured.",
        ) from exc

    _runtime = build_closed_loop_runtime(settings)
    return _runtime


async def warm_closed_loop_runtime() -> None:
    global _runtime

    try:
        settings = MossSettings.from_env()
    except MossConfigurationError:
        return

    if _runtime is None:
        _runtime = build_closed_loop_runtime(settings)

    starter = getattr(_runtime.publisher, "start", None)
    if starter is not None:
        await starter()


@router.get("/scenarios", response_model=list[ScenarioDefinition])
def scenario_catalog() -> list[ScenarioDefinition]:
    return list(SCENARIOS)


@router.post(
    "/scenarios/{scenario_id}",
    response_model=ProductScenarioResult,
)
async def run_product_scenario(
    scenario_id: ScenarioId,
    runtime: ClosedLoopRuntime = Depends(get_closed_loop_runtime),
) -> ProductScenarioResult:
    try:
        return await ProductScenarioRunner(runtime).run(scenario_id)
    except MossUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Required context could not be verified. "
                "High-impact action was not authorized."
            ),
        ) from exc
    except (AuthorizationError, RuntimeInvariantError, StateUnavailableError) as exc:
        raise HTTPException(
            status_code=409,
            detail=(
                "The protected action could not complete its verified control loop."
            ),
        ) from exc


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
            detail=(
                "Required context could not be verified. "
                "High-impact action was not authorized."
            ),
        ) from exc
    except (AuthorizationError, RuntimeInvariantError, StateUnavailableError) as exc:
        raise HTTPException(
            status_code=409,
            detail=(
                "The protected action could not complete its verified control loop."
            ),
        ) from exc


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
