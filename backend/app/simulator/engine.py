from app.models.action import Operation
from app.models.state import (
    ConnectionState,
    HealthState,
    OutstandingState,
    ReconciliationState,
    ServiceState,
    SimulatorState,
)


class Simulator:
    def transition(self, state: SimulatorState, operation: Operation) -> SimulatorState:
        if operation is Operation.RECONCILE:
            return state.model_copy(
                update={
                    "reconciliation": ReconciliationState.COMPLETE,
                    "outstanding": OutstandingState.CLEAR,
                }
            )

        if operation is Operation.RESTART:
            return state.model_copy(update={"service": ServiceState.RESTARTING})

        if operation is Operation.RECOVER_CONNECTION:
            return state.model_copy(
                update={
                    "connection": ConnectionState.CONNECTED,
                    "health": HealthState.HEALTHY,
                }
            )

        if operation is Operation.RESUME:
            return state.model_copy(
                update={
                    "service": ServiceState.RUNNING,
                    "health": HealthState.HEALTHY,
                }
            )

        return state
