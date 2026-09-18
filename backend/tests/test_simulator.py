from app.models.action import Operation
from app.models.state import (
    ConnectionState,
    HealthState,
    OutstandingState,
    ReconciliationState,
    ServiceState,
    SimulatorState,
)
from app.simulator.engine import Simulator


def test_reconciliation_transition_is_deterministic() -> None:
    state = SimulatorState(
        connection=ConnectionState.DISCONNECTED,
        reconciliation=ReconciliationState.INCOMPLETE,
        service=ServiceState.RUNNING,
        health=HealthState.DEGRADED,
        outstanding=OutstandingState.UNKNOWN,
    )

    updated = Simulator().transition(state, Operation.RECONCILE)

    assert updated.reconciliation is ReconciliationState.COMPLETE
    assert updated.outstanding is OutstandingState.CLEAR
    assert updated.connection is ConnectionState.DISCONNECTED
    assert state.reconciliation is ReconciliationState.INCOMPLETE


def test_restart_transition_changes_only_service_state() -> None:
    state = SimulatorState(
        connection=ConnectionState.CONNECTED,
        reconciliation=ReconciliationState.COMPLETE,
        service=ServiceState.RUNNING,
        health=HealthState.HEALTHY,
        outstanding=OutstandingState.CLEAR,
    )

    updated = Simulator().transition(state, Operation.RESTART)

    assert updated.service is ServiceState.RESTARTING
    assert updated.connection is state.connection
    assert updated.reconciliation is state.reconciliation
    assert updated.health is state.health
