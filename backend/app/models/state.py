from enum import Enum

from pydantic import BaseModel, ConfigDict


class ConnectionState(str, Enum):
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"


class ReconciliationState(str, Enum):
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    UNKNOWN = "UNKNOWN"


class ServiceState(str, Enum):
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    RESTARTING = "RESTARTING"


class HealthState(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"


class OutstandingState(str, Enum):
    CLEAR = "CLEAR"
    UNKNOWN = "UNKNOWN"


class SimulatorState(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    connection: ConnectionState
    reconciliation: ReconciliationState
    service: ServiceState
    health: HealthState
    outstanding: OutstandingState
