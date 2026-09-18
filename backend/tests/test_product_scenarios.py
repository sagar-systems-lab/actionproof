import asyncio

from app.models.decision import DecisionCode
from app.retrieval.engine import RetrievalActionProofEngine
from app.retrieval.retriever import MossContextRetriever
from app.runtime.events import FlightRecorder
from app.runtime.models import PostflightStatus, ScenarioId
from app.runtime.orchestrator import ClosedLoopRuntime
from app.runtime.scenarios import ProductScenarioRunner

from tests.retrieval_fakes import StatefulFakeMossBackend


def runtime_for(state) -> ClosedLoopRuntime:
    backend = StatefulFakeMossBackend(state=state)
    events = FlightRecorder()
    engine = RetrievalActionProofEngine(
        MossContextRetriever(backend, environment="production"),
        events=events,
    )
    return ClosedLoopRuntime(engine, backend, events=events)


def test_safe_and_unsafe_restart_scenarios(unsafe_state) -> None:
    runtime = runtime_for(unsafe_state)
    runner = ProductScenarioRunner(runtime)

    safe = asyncio.run(runner.run(ScenarioId.SAFE_RESTART))
    unsafe = asyncio.run(runner.run(ScenarioId.UNSAFE_RESTART))

    assert safe.primary_evaluation.decision.code is DecisionCode.ALLOW_SAFE_STATE
    assert (
        unsafe.primary_evaluation.decision.code
        is DecisionCode.BLOCK_RECONCILIATION_REQUIRED
    )


def test_missing_context_scenario_requires_confirmation(unsafe_state) -> None:
    runtime = runtime_for(unsafe_state)
    result = asyncio.run(
        ProductScenarioRunner(runtime).run(ScenarioId.MISSING_CONTEXT)
    )

    assert (
        result.primary_evaluation.decision.code
        is DecisionCode.CONFIRM_CONTEXT_INCOMPLETE
    )
    assert result.initial_state is None


def test_stale_context_scenario_blocks(unsafe_state) -> None:
    runtime = runtime_for(unsafe_state)
    result = asyncio.run(
        ProductScenarioRunner(runtime).run(ScenarioId.STALE_CONTEXT)
    )

    assert (
        result.primary_evaluation.decision.code
        is DecisionCode.BLOCK_CONTEXT_STALE
    )


def test_successful_recovery_exposes_before_and_after(unsafe_state) -> None:
    runtime = runtime_for(unsafe_state)
    result = asyncio.run(
        ProductScenarioRunner(runtime).run(ScenarioId.SUCCESSFUL_RECOVERY)
    )

    assert (
        result.primary_evaluation.decision.code
        is DecisionCode.BLOCK_RECONCILIATION_REQUIRED
    )
    assert result.recovery is not None
    assert result.recovery.postflight.status is PostflightStatus.VERIFIED
    assert result.final_evaluation is not None
    assert result.final_evaluation.decision.code is DecisionCode.ALLOW_SAFE_STATE
