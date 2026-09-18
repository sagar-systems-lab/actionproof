from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.models.state import SimulatorState
from app.retrieval.schemas import (
    ContextRequirement,
    RawRetrievedDocument,
    SourceType,
)


class FakeMossBackend:
    def __init__(
        self,
        *,
        fail_keys: set[str] | None = None,
        zero_keys: set[str] | None = None,
        stale_keys: set[str] | None = None,
        environment: str = "production",
        metadata_environment: str | None = None,
    ) -> None:
        self.fail_keys = fail_keys or set()
        self.zero_keys = zero_keys or set()
        self.stale_keys = stale_keys or set()
        self.environment = environment
        self.metadata_environment = metadata_environment or environment
        self.queries: list[str] = []

    async def query(
        self,
        requirement: ContextRequirement,
        *,
        incident_id: str,
    ) -> list[RawRetrievedDocument]:
        self.queries.append(requirement.key)

        if requirement.key in self.fail_keys:
            raise RuntimeError(f"moss unavailable for {requirement.key}")
        if requirement.key in self.zero_keys:
            return []

        source_type = requirement.source_types[0]
        updated_at = datetime.now(timezone.utc)
        ttl = 300
        if requirement.key in self.stale_keys:
            updated_at -= timedelta(hours=1)
            ttl = 1

        metadata = {
            "source_type": source_type.value,
            "authority": self._authority(source_type),
            "version": "1",
            "environment": self.metadata_environment,
            "updated_at": updated_at.isoformat(),
            "ttl_seconds": str(ttl),
        }

        if source_type is SourceType.LIVE_STATE:
            metadata.update(
                {
                    "incident_id": incident_id,
                    "connection": "DISCONNECTED",
                    "reconciliation": "INCOMPLETE",
                    "service": "RUNNING",
                    "health": "DEGRADED",
                    "outstanding": "UNKNOWN",
                }
            )

        return [
            RawRetrievedDocument(
                document_id=f"DOC-{requirement.key}",
                index_name=f"index-{requirement.domain.value}",
                content=f"evidence for {requirement.key}",
                score=0.97,
                metadata=metadata,
            )
        ]

    @staticmethod
    def _authority(source_type: SourceType) -> str:
        if source_type is SourceType.POLICY:
            return "system"
        if source_type in (SourceType.RUNBOOK, SourceType.HISTORY):
            return "ops"
        return "runtime"


class StatefulFakeMossBackend(FakeMossBackend):
    def __init__(self, *, state: SimulatorState, environment: str = "production") -> None:
        super().__init__(environment=environment)
        now = datetime.now(timezone.utc)
        self.state = state
        self.states: dict[str, SimulatorState] = {"INC-104": state}
        self.state_updated_at: dict[str, datetime] = {"INC-104": now}
        self.state_ttl: dict[str, int] = {"INC-104": 300}
        self.updates: list[SimulatorState] = []

    async def query(
        self,
        requirement: ContextRequirement,
        *,
        incident_id: str,
    ) -> list[RawRetrievedDocument]:
        if (
            requirement.source_types
            and requirement.source_types[0] is SourceType.LIVE_STATE
            and incident_id not in self.states
        ):
            self.queries.append(requirement.key)
            return []

        documents = await super().query(
            requirement,
            incident_id=incident_id,
        )
        for document in documents:
            if document.metadata.get("source_type") == SourceType.LIVE_STATE.value:
                state = self.states[incident_id]
                document.metadata.update(
                    {
                        "incident_id": incident_id,
                        "updated_at": self.state_updated_at[incident_id].isoformat(),
                        "ttl_seconds": str(self.state_ttl[incident_id]),
                        "connection": state.connection.value,
                        "reconciliation": state.reconciliation.value,
                        "service": state.service.value,
                        "health": state.health.value,
                        "outstanding": state.outstanding.value,
                    }
                )
        return documents

    async def upsert_live_state(
        self,
        incident_id: str,
        state: SimulatorState,
        *,
        version: str = "1",
        ttl_seconds: int = 30,
    ) -> None:
        self.state = state
        self.states[incident_id] = state
        self.state_updated_at[incident_id] = datetime.now(timezone.utc)
        self.state_ttl[incident_id] = ttl_seconds
        self.updates.append(state)
