from datetime import datetime, timezone

import pytest

from app.models.action import ActionIntent
from app.models.context import ContextFreshness, DecisionContext
from app.models.state import (
    ConnectionState,
    HealthState,
    OutstandingState,
    ReconciliationState,
    ServiceState,
    SimulatorState,
)


@pytest.fixture
def restart_intent() -> ActionIntent:
    return ActionIntent(
        action_id="ACT-104",
        trace_id="TRACE-104",
        actor="operations-agent",
        text="Restart the service.",
        incident_id="INC-104",
        timestamp=datetime(2026, 9, 18, 8, 15, tzinfo=timezone.utc),
    )


@pytest.fixture
def safe_state() -> SimulatorState:
    return SimulatorState(
        connection=ConnectionState.CONNECTED,
        reconciliation=ReconciliationState.COMPLETE,
        service=ServiceState.RUNNING,
        health=HealthState.HEALTHY,
        outstanding=OutstandingState.CLEAR,
    )


@pytest.fixture
def unsafe_state() -> SimulatorState:
    return SimulatorState(
        connection=ConnectionState.DISCONNECTED,
        reconciliation=ReconciliationState.INCOMPLETE,
        service=ServiceState.RUNNING,
        health=HealthState.DEGRADED,
        outstanding=OutstandingState.UNKNOWN,
    )


@pytest.fixture
def safe_context(safe_state: SimulatorState) -> DecisionContext:
    return DecisionContext(
        state=safe_state,
        required_context_complete=True,
        freshness=ContextFreshness.FRESH,
        policy_available=True,
    )


@pytest.fixture
def unsafe_context(unsafe_state: SimulatorState) -> DecisionContext:
    return DecisionContext(
        state=unsafe_state,
        required_context_complete=True,
        freshness=ContextFreshness.FRESH,
        policy_available=True,
    )
