from app.agent.normalizer import ActionNormalizer
from app.models.action import ActionIntent
from app.models.context import ContextFreshness, DecisionContext
from app.models.decision import DecisionCode, DecisionStatus
from app.models.state import SimulatorState
from app.policy.engine import PolicyEngine


def test_safe_restart_is_allowed(
    restart_intent: ActionIntent,
    safe_context: DecisionContext,
) -> None:
    action = ActionNormalizer().normalize(restart_intent)
    decision = PolicyEngine().evaluate(action, safe_context)

    assert decision.status is DecisionStatus.ALLOW
    assert decision.code is DecisionCode.ALLOW_SAFE_STATE


def test_unsafe_restart_is_blocked(
    restart_intent: ActionIntent,
    unsafe_context: DecisionContext,
) -> None:
    action = ActionNormalizer().normalize(restart_intent)
    decision = PolicyEngine().evaluate(action, unsafe_context)

    assert decision.status is DecisionStatus.BLOCK
    assert decision.code is DecisionCode.BLOCK_RECONCILIATION_REQUIRED
    assert decision.recommended_next_action == "run_reconciliation"


def test_missing_context_cannot_allow(restart_intent: ActionIntent) -> None:
    action = ActionNormalizer().normalize(restart_intent)
    context = DecisionContext(state=None, required_context_complete=False)
    decision = PolicyEngine().evaluate(action, context)

    assert decision.status is DecisionStatus.CONFIRM
    assert decision.code is DecisionCode.CONFIRM_CONTEXT_INCOMPLETE


def test_stale_context_is_blocked(
    restart_intent: ActionIntent,
    safe_state: SimulatorState,
) -> None:
    action = ActionNormalizer().normalize(restart_intent)
    context = DecisionContext(
        state=safe_state,
        freshness=ContextFreshness.STALE,
        required_context_complete=True,
    )
    decision = PolicyEngine().evaluate(action, context)

    assert decision.status is DecisionStatus.BLOCK
    assert decision.code is DecisionCode.BLOCK_CONTEXT_STALE


def test_unknown_freshness_requires_confirmation(
    restart_intent: ActionIntent,
    safe_state: SimulatorState,
) -> None:
    action = ActionNormalizer().normalize(restart_intent)
    context = DecisionContext(
        state=safe_state,
        freshness=ContextFreshness.UNKNOWN,
        required_context_complete=True,
    )
    decision = PolicyEngine().evaluate(action, context)

    assert decision.status is DecisionStatus.CONFIRM
    assert decision.code is DecisionCode.CONFIRM_CONTEXT_INCOMPLETE


def test_missing_policy_fails_closed(
    restart_intent: ActionIntent,
    safe_state: SimulatorState,
) -> None:
    action = ActionNormalizer().normalize(restart_intent)
    context = DecisionContext(state=safe_state, policy_available=False)
    decision = PolicyEngine().evaluate(action, context)

    assert decision.status is DecisionStatus.BLOCK
    assert decision.code is DecisionCode.BLOCK_POLICY_UNAVAILABLE

def test_connection_recovery_requires_reconciliation(
    restart_intent: ActionIntent,
    unsafe_context: DecisionContext,
) -> None:
    action = ActionNormalizer().normalize(
        restart_intent.model_copy(update={"text": "Recover the connection."})
    )
    decision = PolicyEngine().evaluate(action, unsafe_context)

    assert decision.status is DecisionStatus.BLOCK
    assert decision.code is DecisionCode.BLOCK_RECONCILIATION_REQUIRED


def test_connection_recovery_is_allowed_after_reconciliation(
    restart_intent: ActionIntent,
    safe_context: DecisionContext,
) -> None:
    action = ActionNormalizer().normalize(
        restart_intent.model_copy(update={"text": "Recover the connection."})
    )
    decision = PolicyEngine().evaluate(action, safe_context)

    assert decision.status is DecisionStatus.ALLOW
    assert decision.code is DecisionCode.ALLOW_SAFE_STATE


def test_resume_is_blocked_from_unsafe_state(
    restart_intent: ActionIntent,
    unsafe_context: DecisionContext,
) -> None:
    action = ActionNormalizer().normalize(
        restart_intent.model_copy(update={"text": "Resume operations."})
    )
    decision = PolicyEngine().evaluate(action, unsafe_context)

    assert decision.status is DecisionStatus.BLOCK
    assert decision.code is DecisionCode.BLOCK_UNSAFE_STATE


def test_resume_is_allowed_from_safe_state(
    restart_intent: ActionIntent,
    safe_context: DecisionContext,
) -> None:
    action = ActionNormalizer().normalize(
        restart_intent.model_copy(update={"text": "Resume operations."})
    )
    decision = PolicyEngine().evaluate(action, safe_context)

    assert decision.status is DecisionStatus.ALLOW
    assert decision.code is DecisionCode.ALLOW_SAFE_STATE


def test_reconciliation_action_is_allowed(
    restart_intent: ActionIntent,
    unsafe_context: DecisionContext,
) -> None:
    action = ActionNormalizer().normalize(
        restart_intent.model_copy(update={"text": "Run reconciliation."})
    )
    decision = PolicyEngine().evaluate(action, unsafe_context)

    assert decision.status is DecisionStatus.ALLOW
    assert decision.code is DecisionCode.ALLOW_SAFE_STATE

