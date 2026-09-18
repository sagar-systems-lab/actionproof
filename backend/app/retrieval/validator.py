from __future__ import annotations

from datetime import datetime, timezone

from app.models.context import ContextFreshness

from .freshness import FreshnessEngine
from .schemas import (
    ContextRequirement,
    RawRetrievedDocument,
    RetrievalIssue,
    RetrievalIssueCode,
    RetrievedEvidence,
    SourceType,
)


class EvidenceValidator:
    _AUTHORITIES: dict[SourceType, set[str]] = {
        SourceType.POLICY: {"system"},
        SourceType.RUNBOOK: {"ops"},
        SourceType.HISTORY: {"ops"},
        SourceType.LIVE_STATE: {"runtime"},
    }

    def __init__(self, freshness: FreshnessEngine | None = None) -> None:
        self.freshness = freshness or FreshnessEngine()

    def validate(
        self,
        document: RawRetrievedDocument,
        requirement: ContextRequirement,
        *,
        environment: str,
        incident_id: str,
        now: datetime | None = None,
    ) -> tuple[RetrievedEvidence | None, RetrievalIssue | None]:
        metadata = document.metadata
        missing = [
            key
            for key in (
                "source_type",
                "authority",
                "version",
                "environment",
                "updated_at",
                "ttl_seconds",
            )
            if not metadata.get(key)
        ]
        if missing:
            return None, self._issue(
                requirement,
                RetrievalIssueCode.INVALID_METADATA,
                f"missing metadata: {', '.join(missing)}",
            )

        try:
            source_type = SourceType(metadata["source_type"])
        except ValueError:
            return None, self._issue(
                requirement,
                RetrievalIssueCode.WRONG_SOURCE_TYPE,
                f"unsupported source_type={metadata['source_type']}",
            )

        if source_type not in requirement.source_types:
            return None, self._issue(
                requirement,
                RetrievalIssueCode.WRONG_SOURCE_TYPE,
                f"expected {self._source_names(requirement)}, got {source_type.value}",
            )

        authority = metadata["authority"]
        if authority not in self._AUTHORITIES[source_type]:
            return None, self._issue(
                requirement,
                RetrievalIssueCode.WRONG_AUTHORITY,
                f"authority={authority} is not trusted for {source_type.value}",
            )

        if metadata["environment"] != environment:
            return None, self._issue(
                requirement,
                RetrievalIssueCode.WRONG_ENVIRONMENT,
                f"expected environment={environment}, got {metadata['environment']}",
            )

        doc_incident_id = metadata.get("incident_id") or None
        if requirement.incident_scoped and doc_incident_id != incident_id:
            return None, self._issue(
                requirement,
                RetrievalIssueCode.WRONG_INCIDENT,
                f"expected incident_id={incident_id}, got {doc_incident_id}",
            )

        try:
            updated_at = self._parse_datetime(metadata["updated_at"])
            ttl_seconds = int(metadata["ttl_seconds"])
        except (ValueError, TypeError):
            return None, self._issue(
                requirement,
                RetrievalIssueCode.INVALID_METADATA,
                "updated_at or ttl_seconds is invalid",
            )

        freshness = self.freshness.classify(
            updated_at,
            ttl_seconds,
            now=now or datetime.now(timezone.utc),
        )

        evidence = RetrievedEvidence(
            requirement_key=requirement.key,
            document_id=document.document_id,
            index_name=document.index_name,
            source_type=source_type,
            authority=authority,
            version=metadata["version"],
            environment=metadata["environment"],
            incident_id=doc_incident_id,
            updated_at=updated_at,
            ttl_seconds=ttl_seconds,
            freshness=freshness,
            content=document.content,
            score=document.score,
            metadata=dict(metadata),
        )

        if freshness is ContextFreshness.STALE:
            return evidence, self._issue(
                requirement,
                RetrievalIssueCode.STALE,
                f"{document.document_id} exceeded ttl_seconds={ttl_seconds}",
            )

        return evidence, None

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError("updated_at must include timezone")
        return parsed

    @staticmethod
    def _source_names(requirement: ContextRequirement) -> str:
        return "/".join(source.value for source in requirement.source_types)

    @staticmethod
    def _issue(
        requirement: ContextRequirement,
        code: RetrievalIssueCode,
        detail: str,
    ) -> RetrievalIssue:
        return RetrievalIssue(
            requirement_key=requirement.key,
            code=code,
            detail=detail,
        )
