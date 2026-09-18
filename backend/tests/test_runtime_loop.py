import asyncio

from app.models.decision import DecisionCode
from app.models.state import ReconciliationState
from app.retrieval.engine import RetrievalActionProofEngine
from app.retrieval.retriever import MossContextRetriever
from app.runtime.events import FlightRecorder, RuntimeEventType
from app.runtime.models import PostflightStatus
from app.runtime.orchestrator import ClosedLoopRuntime

from tests.retrieval_fakes import StatefulFakeMossBackend


def test_hero_scenario_closes_the_control_loop(unsafe_state) -> None:
    backend = StatefulFakeMossBackend(state=unsafe_state)
    events = FlightRecorder()
    engine = RetrievalActionProofEngine(
        MossContextRetriever(backend, environment="production"),
        events=events,
    )
    runtime = ClosedLoopRuntime(engine, backend, events=events)

    result = asyncio.run(runtime.run_hero_scenario("INC-104"))

    assert (
        result.blocked_restart.decision.code
        is DecisionCode.BLOCK_RECONCILIATION_REQUIRED
    )
    assert result.blocked_restart.decision.recommended_next_action == "run_reconciliation"
    assert result.recovery.postflight.status is PostflightStatus.VERIFIED
    assert result.recovery.execution.state.reconciliation is ReconciliationState.COMPLETE
    assert result.retry_restart.decision.code is DecisionCode.ALLOW_SAFE_STATE
    assert backend.state.reconciliation is ReconciliationState.COMPLETE

    event_types = [item.event for item in result.events]
    for expected in (
        RuntimeEventType.SCENARIO_STARTED,
        RuntimeEventType.INCIDENT_CREATED,
        RuntimeEventType.AGENT_INTENT_CREATED,
        RuntimeEventType.ACTION_NORMALIZED,
        RuntimeEventType.MOSS_QUERY_STARTED,
        RuntimeEventType.MOSS_QUERY_COMPLETED,
        RuntimeEventType.CONTEXT_VALIDATED,
        RuntimeEventType.POLICY_EVALUATED,
        RuntimeEventType.PROOF_CREATED,
        RuntimeEventType.ACTION_BLOCKED,
        RuntimeEventType.ACTION_ALLOWED,
        RuntimeEventType.ACTION_EXECUTED,
        RuntimeEventType.POSTFLIGHT_VERIFIED,
    ):
        assert expected in event_types

    assert [item.sequence for item in result.events] == sorted(
        item.sequence for item in result.events
    )
