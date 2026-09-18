from __future__ import annotations

from app.models.action import NormalizedAction, Operation
from app.simulator.engine import Simulator

from .authorization import ExecutionPermit, ProofAuthority
from .models import ToolExecutionResult
from .state_store import RuntimeStateStore


class ProtectedToolExecutor:
    """The only simulated side-effect path. A valid single-use permit is mandatory."""

    def __init__(
        self,
        state_store: RuntimeStateStore,
        authority: ProofAuthority,
        simulator: Simulator | None = None,
    ) -> None:
        self.state_store = state_store
        self.authority = authority
        self.simulator = simulator or Simulator()

    def execute(
        self,
        action: NormalizedAction,
        permit: ExecutionPermit,
    ) -> ToolExecutionResult:
        self.authority.validate_and_consume(action, permit)

        before = self.state_store.get(action.incident_id)
        after = self.simulator.transition(before, action.operation)
        self.state_store.set(action.incident_id, after)

        before_data = before.model_dump(mode="json")
        after_data = after.model_dump(mode="json")
        changes = {
            key: str(value)
            for key, value in after_data.items()
            if before_data.get(key) != value
        }

        return ToolExecutionResult(
            success=True,
            state_changes=changes,
            message=self._message(action.operation),
            state=after,
        )

    @staticmethod
    def _message(operation: Operation) -> str:
        messages = {
            Operation.RECONCILE: "Reconciliation completed in the simulator.",
            Operation.RESTART: "Service restart started in the simulator.",
            Operation.RECOVER_CONNECTION: "Connection recovered in the simulator.",
            Operation.RESUME: "Operations resumed in the simulator.",
        }
        return messages[operation]
