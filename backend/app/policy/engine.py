from app.models.action import NormalizedAction, Operation, RiskLevel
from app.models.context import ContextFreshness, DecisionContext
from app.models.decision import DecisionCode, DecisionStatus, PolicyDecision
from app.models.state import ConnectionState, HealthState, ReconciliationState


class PolicyEngine:
    def evaluate(self, action: NormalizedAction, context: DecisionContext) -> PolicyDecision:
        if action.impact is RiskLevel.HIGH and not context.policy_available:
            return PolicyDecision(
                status=DecisionStatus.BLOCK,
                code=DecisionCode.BLOCK_POLICY_UNAVAILABLE,
                matched_rule="policy_required_for_high_impact",
                reason="Required policy is unavailable for a high-impact action.",
                recommended_next_action="restore_policy_context",
            )

        if context.state is None or not context.required_context_complete:
            return PolicyDecision(
                status=DecisionStatus.CONFIRM,
                code=DecisionCode.CONFIRM_CONTEXT_INCOMPLETE,
                matched_rule="required_context_must_be_complete",
                reason="Required operational context is incomplete.",
                recommended_next_action="refresh_context",
            )

        if context.freshness is ContextFreshness.STALE:
            return PolicyDecision(
                status=DecisionStatus.BLOCK,
                code=DecisionCode.BLOCK_CONTEXT_STALE,
                matched_rule="stale_context_cannot_authorize_high_impact_action",
                reason="Required operational context is stale.",
                recommended_next_action="refresh_context",
            )

        if context.freshness is ContextFreshness.UNKNOWN:
            return PolicyDecision(
                status=DecisionStatus.CONFIRM,
                code=DecisionCode.CONFIRM_CONTEXT_INCOMPLETE,
                matched_rule="context_freshness_must_be_known",
                reason="Context freshness cannot be established.",
                recommended_next_action="refresh_context",
            )

        state = context.state

        if action.operation is Operation.RESTART:
            if state.reconciliation is not ReconciliationState.COMPLETE:
                return PolicyDecision(
                    status=DecisionStatus.BLOCK,
                    code=DecisionCode.BLOCK_RECONCILIATION_REQUIRED,
                    matched_rule="restart_requires_completed_reconciliation",
                    reason="Restart is not allowed until reconciliation is complete.",
                    recommended_next_action="run_reconciliation",
                )
            return self._allow()

        if action.operation is Operation.RECOVER_CONNECTION:
            if state.reconciliation is not ReconciliationState.COMPLETE:
                return PolicyDecision(
                    status=DecisionStatus.BLOCK,
                    code=DecisionCode.BLOCK_RECONCILIATION_REQUIRED,
                    matched_rule="connection_recovery_requires_completed_reconciliation",
                    reason="Connection recovery is not allowed until reconciliation is complete.",
                    recommended_next_action="run_reconciliation",
                )
            return self._allow()

        if action.operation is Operation.RESUME:
            if (
                state.connection is not ConnectionState.CONNECTED
                or state.reconciliation is not ReconciliationState.COMPLETE
                or state.health is not HealthState.HEALTHY
            ):
                return PolicyDecision(
                    status=DecisionStatus.BLOCK,
                    code=DecisionCode.BLOCK_UNSAFE_STATE,
                    matched_rule="resume_requires_connected_reconciled_healthy_state",
                    reason="Resume requires connected, reconciled, healthy state.",
                    recommended_next_action="recover_service_state",
                )
            return self._allow()

        if action.operation is Operation.RECONCILE:
            return self._allow()

        return PolicyDecision(
            status=DecisionStatus.BLOCK,
            code=DecisionCode.BLOCK_UNSAFE_STATE,
            matched_rule="unsupported_operation_fails_closed",
            reason="The requested operation is not authorized.",
        )

    @staticmethod
    def _allow() -> PolicyDecision:
        return PolicyDecision(
            status=DecisionStatus.ALLOW,
            code=DecisionCode.ALLOW_SAFE_STATE,
            matched_rule="required_state_is_safe",
            reason="Required context is complete, current, and policy conditions are satisfied.",
        )
