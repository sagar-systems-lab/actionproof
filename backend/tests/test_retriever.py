import asyncio

from app.agent.normalizer import ActionNormalizer
from app.models.action import ActionIntent
from app.models.context import ContextFreshness
from app.retrieval.retriever import MossContextRetriever
from app.retrieval.schemas import RetrievalIssueCode, SourceType

from retrieval_fakes import FakeMossBackend


def test_retriever_builds_context_from_moss_evidence(
    restart_intent: ActionIntent,
) -> None:
    action = ActionNormalizer().normalize(restart_intent)
    backend = FakeMossBackend()
    retriever = MossContextRetriever(backend, environment="production")

    result = asyncio.run(retriever.retrieve(action))

    assert result.context.required_context_complete is True
    assert result.context.policy_available is True
    assert result.context.retrieval_failed is False
    assert result.context.freshness is ContextFreshness.FRESH
    assert result.context.state is not None
    assert result.context.state.reconciliation.value == "INCOMPLETE"
    assert {item.source_type for item in result.evidence} >= {
        SourceType.POLICY,
        SourceType.RUNBOOK,
        SourceType.LIVE_STATE,
    }
    assert backend.queries == [
        "restart_policy",
        "current_state",
        "recovery_runbook",
        "incident_history",
    ]
    assert result.metrics.retrieval_us >= 0


def test_required_moss_failure_sets_fail_closed_context(
    restart_intent: ActionIntent,
) -> None:
    action = ActionNormalizer().normalize(restart_intent)
    retriever = MossContextRetriever(
        FakeMossBackend(fail_keys={"restart_policy"}),
        environment="production",
    )

    result = asyncio.run(retriever.retrieve(action))

    assert result.context.retrieval_failed is True
    assert result.context.policy_available is False
    assert result.context.required_context_complete is False
    assert any(
        issue.code is RetrievalIssueCode.UNAVAILABLE
        for issue in result.issues
    )


def test_zero_policy_result_is_not_treated_as_available(
    restart_intent: ActionIntent,
) -> None:
    action = ActionNormalizer().normalize(restart_intent)
    retriever = MossContextRetriever(
        FakeMossBackend(zero_keys={"restart_policy"}),
        environment="production",
    )

    result = asyncio.run(retriever.retrieve(action))

    assert result.context.retrieval_failed is False
    assert result.context.policy_available is False
    assert result.context.required_context_complete is False
    assert any(
        issue.code is RetrievalIssueCode.ZERO_RESULTS
        for issue in result.issues
    )


def test_stale_required_state_marks_context_stale(
    restart_intent: ActionIntent,
) -> None:
    action = ActionNormalizer().normalize(restart_intent)
    retriever = MossContextRetriever(
        FakeMossBackend(stale_keys={"current_state"}),
        environment="production",
    )

    result = asyncio.run(retriever.retrieve(action))

    assert result.context.freshness is ContextFreshness.STALE
    assert any(
        issue.code is RetrievalIssueCode.STALE
        for issue in result.issues
    )


def test_wrong_environment_cannot_complete_context(
    restart_intent: ActionIntent,
) -> None:
    action = ActionNormalizer().normalize(restart_intent)
    retriever = MossContextRetriever(
        FakeMossBackend(metadata_environment="development"),
        environment="production",
    )

    result = asyncio.run(retriever.retrieve(action))

    assert result.context.required_context_complete is False
    assert result.context.policy_available is False
    assert any(
        issue.code is RetrievalIssueCode.WRONG_ENVIRONMENT
        for issue in result.issues
    )
