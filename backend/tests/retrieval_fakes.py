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
