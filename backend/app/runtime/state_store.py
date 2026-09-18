from __future__ import annotations

from app.models.state import SimulatorState


class StateUnavailableError(RuntimeError):
    pass


class RuntimeStateStore:
    def __init__(self) -> None:
        self._states: dict[str, SimulatorState] = {}

    def set(self, incident_id: str, state: SimulatorState) -> None:
        self._states[incident_id] = state

    def get(self, incident_id: str) -> SimulatorState:
        try:
            return self._states[incident_id]
        except KeyError as exc:
            raise StateUnavailableError(
                f"no runtime state exists for incident '{incident_id}'"
            ) from exc
