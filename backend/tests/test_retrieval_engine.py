import asyncio

from app.models.action import ActionIntent
from app.models.decision import DecisionCode, DecisionStatus
from app.retrieval.engine import RetrievalActionProofEngine
from app.retrieval.retriever import MossContextRetriever

from tests.retrieval_fakes import FakeMossBackend


def test_retrieval_engine_blocks_unsafe_restart_with_real_evidence_shape(
    restart_intent: ActionIntent,
) -> None:
    engine = RetrievalActionProofEngine(
        MossContextRetriever(
            FakeMossBackend(),
            environment="production",
        )
    )

    result = asyncio.run(engine.evaluate(restart_intent))

    assert result.decision.status is DecisionStatus.BLOCK
    assert result.decision.code is DecisionCode.BLOCK_RECONCILIATION_REQUIRED
    assert len(result.proof.evidence) >= 3
    assert {
        item.source_type
        for item in result.proof.evidence
        if item.source_type is not None
    } >= {"policy", "runbook", "live_state"}
    assert result.proof.latency.total_us >= result.proof.latency.retrieval_us
    assert result.proof.latency.policy_us >= 0


def test_retrieval_failure_blocks_high_impact_action(
    restart_intent: ActionIntent,
) -> None:
    engine = RetrievalActionProofEngine(
        MossContextRetriever(
            FakeMossBackend(fail_keys={"current_state"}),
            environment="production",
        )
    )

    result = asyncio.run(engine.evaluate(restart_intent))

    assert result.decision.status is DecisionStatus.BLOCK
    assert result.decision.code is DecisionCode.BLOCK_RETRIEVAL_FAILURE


def test_missing_policy_blocks_high_impact_action(
    restart_intent: ActionIntent,
) -> None:
    engine = RetrievalActionProofEngine(
        MossContextRetriever(
            FakeMossBackend(zero_keys={"restart_policy"}),
            environment="production",
        )
    )

    result = asyncio.run(engine.evaluate(restart_intent))

    assert result.decision.status is DecisionStatus.BLOCK
    assert result.decision.code is DecisionCode.BLOCK_POLICY_UNAVAILABLE


def test_stale_state_cannot_allow_restart(
    restart_intent: ActionIntent,
) -> None:
    engine = RetrievalActionProofEngine(
        MossContextRetriever(
            FakeMossBackend(stale_keys={"current_state"}),
            environment="production",
        )
    )

    result = asyncio.run(engine.evaluate(restart_intent))

    assert result.decision.status is DecisionStatus.BLOCK
    assert result.decision.code is DecisionCode.BLOCK_CONTEXT_STALE
