from __future__ import annotations

import re

from app.models.action import ActionIntent, NormalizedAction, Operation, RiskLevel, ToolName


class NormalizationError(ValueError):
    pass


class ActionNormalizer:
    _RULES: tuple[tuple[re.Pattern[str], Operation, RiskLevel], ...] = (
        (re.compile(r"\b(restart|reboot)\b", re.IGNORECASE), Operation.RESTART, RiskLevel.HIGH),
        (re.compile(r"\b(reconcile|reconciliation)\b", re.IGNORECASE), Operation.RECONCILE, RiskLevel.HIGH),
        (
            re.compile(r"\b(reconnect|recover (?:the )?(?:connection|session))\b", re.IGNORECASE),
            Operation.RECOVER_CONNECTION,
            RiskLevel.HIGH,
        ),
        (re.compile(r"\bresume\b", re.IGNORECASE), Operation.RESUME, RiskLevel.HIGH),
    )

    def normalize(self, intent: ActionIntent) -> NormalizedAction:
        operation: Operation | None = None
        impact: RiskLevel | None = None

        for pattern, candidate_operation, candidate_impact in self._RULES:
            if pattern.search(intent.text):
                operation = candidate_operation
                impact = candidate_impact
                break

        if operation is None or impact is None:
            raise NormalizationError("unsupported action intent")

        if impact is RiskLevel.HIGH and not intent.incident_id:
            raise NormalizationError("high-impact action requires incident_id")

        return NormalizedAction(
            action_id=intent.action_id,
            trace_id=intent.trace_id,
            actor=intent.actor,
            tool=ToolName.EXECUTION_SERVICE,
            operation=operation,
            arguments={},
            impact=impact,
            incident_id=intent.incident_id,
            timestamp=intent.timestamp,
        )
