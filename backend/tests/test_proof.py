from app.core.engine import ActionProofEngine
from app.models.action import ActionIntent
from app.models.context import DecisionContext
from app.models.decision import DecisionCode, DecisionStatus
from app.models.scenario import EvaluationRequest


def test_evaluation_builds_proof_packet(
    restart_intent: ActionIntent,
    unsafe_context: DecisionContext,
) -> None:
    result = ActionProofEngine().evaluate(
        EvaluationRequest(intent=restart_intent, context=unsafe_context)
    )

    assert result.proof.trace_id == "TRACE-104"
    assert result.proof.decision is DecisionStatus.BLOCK
    assert result.proof.decision_code is DecisionCode.BLOCK_RECONCILIATION_REQUIRED
    assert result.proof.matched_policy == "restart_requires_completed_reconciliation"
    assert result.proof.safe_next_action == "run_reconciliation"
    assert len(result.proof.evidence) == 6
    assert result.proof.latency.total_us == 0


def test_same_input_produces_same_decision_and_proof_id(
    restart_intent: ActionIntent,
    unsafe_context: DecisionContext,
) -> None:
    engine = ActionProofEngine()
    request = EvaluationRequest(intent=restart_intent, context=unsafe_context)

    first = engine.evaluate(request)
    second = engine.evaluate(request)

    assert first.decision == second.decision
    assert first.proof.proof_id == second.proof.proof_id
