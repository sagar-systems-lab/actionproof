import pytest

from app.core.engine import ActionProofEngine
from app.models.scenario import EvaluationRequest
from app.runtime.authorization import AuthorizationError, ProofAuthority
from app.runtime.executor import ProtectedToolExecutor
from app.runtime.state_store import RuntimeStateStore


def test_execution_permit_is_bound_to_exact_action(
    restart_intent,
    safe_context,
    safe_state,
) -> None:
    allowed = ActionProofEngine().evaluate(
        EvaluationRequest(intent=restart_intent, context=safe_context)
    )
    authority = ProofAuthority()
    store = RuntimeStateStore()
    store.set("INC-104", safe_state)
    executor = ProtectedToolExecutor(store, authority)
    permit = authority.issue(allowed)

    changed = allowed.action.model_copy(
        update={"arguments": {"force": True}}
    )
    with pytest.raises(AuthorizationError, match="changed after authorization"):
        executor.execute(changed, permit)

    executed = executor.execute(allowed.action, permit)
    assert executed.success is True
    assert executed.state.service.value == "RESTARTING"

    with pytest.raises(AuthorizationError, match="already been consumed"):
        executor.execute(allowed.action, permit)


def test_blocked_proof_cannot_mint_execution_permit(
    restart_intent,
    unsafe_context,
) -> None:
    blocked = ActionProofEngine().evaluate(
        EvaluationRequest(intent=restart_intent, context=unsafe_context)
    )

    with pytest.raises(AuthorizationError, match="ALLOW decision"):
        ProofAuthority().issue(blocked)
