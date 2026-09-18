from datetime import datetime, timezone

from app.models.context import ContextFreshness
from app.retrieval.schemas import (
    ContextRequirement,
    RawRetrievedDocument,
    RetrievalDomain,
    RetrievalIssueCode,
    SourceType,
)
from app.retrieval.validator import EvidenceValidator


def requirement() -> ContextRequirement:
    return ContextRequirement(
        key="current_state",
        domain=RetrievalDomain.LIVE_STATE,
        source_types=(SourceType.LIVE_STATE,),
        query="current state",
        incident_scoped=True,
    )


def document(**metadata_overrides: str) -> RawRetrievedDocument:
    metadata = {
        "source_type": "live_state",
        "authority": "runtime",
        "version": "1",
        "environment": "production",
        "incident_id": "INC-104",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "ttl_seconds": "30",
        "connection": "DISCONNECTED",
        "reconciliation": "INCOMPLETE",
        "service": "RUNNING",
        "health": "DEGRADED",
        "outstanding": "UNKNOWN",
    }
    metadata.update(metadata_overrides)
    return RawRetrievedDocument(
        document_id="STATE-INC-104",
        index_name="actionproof-live-state",
        content="current state",
        score=0.99,
        metadata=metadata,
    )


def test_valid_metadata_is_accepted() -> None:
    evidence, issue = EvidenceValidator().validate(
        document(),
        requirement(),
        environment="production",
        incident_id="INC-104",
    )

    assert issue is None
    assert evidence is not None
    assert evidence.freshness is ContextFreshness.FRESH


def test_wrong_environment_is_rejected() -> None:
    evidence, issue = EvidenceValidator().validate(
        document(environment="development"),
        requirement(),
        environment="production",
        incident_id="INC-104",
    )

    assert evidence is None
    assert issue is not None
    assert issue.code is RetrievalIssueCode.WRONG_ENVIRONMENT


def test_wrong_incident_is_rejected() -> None:
    evidence, issue = EvidenceValidator().validate(
        document(incident_id="INC-999"),
        requirement(),
        environment="production",
        incident_id="INC-104",
    )

    assert evidence is None
    assert issue is not None
    assert issue.code is RetrievalIssueCode.WRONG_INCIDENT


def test_wrong_authority_is_rejected() -> None:
    evidence, issue = EvidenceValidator().validate(
        document(authority="user"),
        requirement(),
        environment="production",
        incident_id="INC-104",
    )

    assert evidence is None
    assert issue is not None
    assert issue.code is RetrievalIssueCode.WRONG_AUTHORITY
