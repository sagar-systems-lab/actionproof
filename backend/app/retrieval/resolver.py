from app.models.action import NormalizedAction, Operation

from .schemas import ContextRequirement, RetrievalDomain, SourceType


class ContextRequirementResolver:
    def resolve(self, action: NormalizedAction) -> tuple[ContextRequirement, ...]:
        if action.operation is Operation.RESTART:
            return (
                self._policy(
                    "restart_policy",
                    "restart service reconciliation policy",
                ),
                self._live_state(
                    "current_state",
                    "current execution service connection reconciliation state",
                ),
                self._runbook(
                    "recovery_runbook",
                    "disconnect recovery restart service reconciliation procedure",
                ),
                self._history(
                    "incident_history",
                    "similar disconnect incident restart recovery",
                ),
            )

        if action.operation is Operation.RECONCILE:
            return (
                self._policy(
                    "reconciliation_policy",
                    "reconciliation policy outstanding external state",
                ),
                self._live_state(
                    "current_state",
                    "current execution service outstanding reconciliation state",
                ),
                self._runbook(
                    "reconciliation_runbook",
                    "state reconciliation procedure external state",
                ),
            )

        if action.operation is Operation.RECOVER_CONNECTION:
            return (
                self._policy(
                    "reconciliation_policy",
                    "connection recovery reconciliation policy",
                ),
                self._live_state(
                    "current_state",
                    "current execution service connection reconciliation state",
                ),
                self._runbook(
                    "disconnect_runbook",
                    "connection loss recovery session recovery",
                ),
            )

        if action.operation is Operation.RESUME:
            return (
                self._policy(
                    "resume_policy",
                    "resume operations connected reconciled healthy policy",
                ),
                self._live_state(
                    "current_state",
                    "current execution service connection reconciliation health",
                ),
                self._runbook(
                    "resume_runbook",
                    "resume workflow service recovery",
                ),
            )

        return ()

    @staticmethod
    def _policy(key: str, query: str) -> ContextRequirement:
        return ContextRequirement(
            key=key,
            domain=RetrievalDomain.POLICY,
            source_types=(SourceType.POLICY,),
            query=query,
        )

    @staticmethod
    def _live_state(key: str, query: str) -> ContextRequirement:
        return ContextRequirement(
            key=key,
            domain=RetrievalDomain.LIVE_STATE,
            source_types=(SourceType.LIVE_STATE,),
            query=query,
            incident_scoped=True,
        )

    @staticmethod
    def _runbook(key: str, query: str) -> ContextRequirement:
        return ContextRequirement(
            key=key,
            domain=RetrievalDomain.KNOWLEDGE,
            source_types=(SourceType.RUNBOOK,),
            query=query,
        )

    @staticmethod
    def _history(key: str, query: str) -> ContextRequirement:
        return ContextRequirement(
            key=key,
            domain=RetrievalDomain.KNOWLEDGE,
            source_types=(SourceType.HISTORY,),
            query=query,
            required=False,
            top_k=2,
        )
