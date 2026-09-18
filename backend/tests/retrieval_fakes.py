from __future__ import annotations

from datetime import datetime, timedelta, timezone

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


from app.models.state import SimulatorState


class StatefulFakeMossBackend(FakeMossBackend):
    def __init__(self, *, state: SimulatorState, environment: str = "production") -> None:
        super().__init__(environment=environment)
        self.state = state
        self.updates: list[SimulatorState] = []

    async def query(
        self,
        requirement: ContextRequirement,
        *,
        incident_id: str,
    ) -> list[RawRetrievedDocument]:
        documents = await super().query(
            requirement,
            incident_id=incident_id,
        )
        for document in documents:
            if document.metadata.get("source_type") == SourceType.LIVE_STATE.value:
                document.metadata.update(
                    {
                        "connection": self.state.connection.value,
                        "reconciliation": self.state.reconciliation.value,
                        "service": self.state.service.value,
                        "health": self.state.health.value,
                        "outstanding": self.state.outstanding.value,
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
        self.updates.append(state)
