from __future__ import annotations

from app.models.action import NormalizedAction, Operation
from app.models.state import SimulatorState

from .models import PostflightResult, PostflightStatus


class PostflightVerifier:
    def verify(
        self,
        action: NormalizedAction,
        observed_state: SimulatorState,
    ) -> PostflightResult:
        expected = self._expected(action.operation)
        observed_all = observed_state.model_dump(mode="json")
        observed = {
            key: str(observed_all[key])
            for key in expected
        }

        verified = all(observed[key] == value for key, value in expected.items())
        status = (
            PostflightStatus.VERIFIED
            if verified
            else PostflightStatus.FAILED
        )

        return PostflightResult(
            status=status,
            expected=expected,
            observed=observed,
            message=(
                "Observed state matches the authorized action."
                if verified
                else "Observed state does not match the authorized action."
            ),
        )

    @staticmethod
    def _expected(operation: Operation) -> dict[str, str]:
        expectations = {
            Operation.RECONCILE: {
                "reconciliation": "COMPLETE",
                "outstanding": "CLEAR",
            },
            Operation.RESTART: {"service": "RESTARTING"},
            Operation.RECOVER_CONNECTION: {
                "connection": "CONNECTED",
                "health": "HEALTHY",
            },
            Operation.RESUME: {
                "service": "RUNNING",
                "health": "HEALTHY",
            },
        }
        return expectations[operation]
