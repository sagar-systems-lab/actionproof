from datetime import datetime, timezone

import pytest

from app.agent.normalizer import ActionNormalizer, NormalizationError
from app.models.action import ActionIntent, Operation, RiskLevel, ToolName


def test_normalizes_restart_intent(restart_intent: ActionIntent) -> None:
    action = ActionNormalizer().normalize(restart_intent)

    assert action.tool is ToolName.EXECUTION_SERVICE
    assert action.operation is Operation.RESTART
    assert action.impact is RiskLevel.HIGH
    assert action.incident_id == "INC-104"


def test_rejects_unsupported_intent() -> None:
    intent = ActionIntent(
        action_id="ACT-105",
        trace_id="TRACE-105",
        actor="operations-agent",
        text="Summarize the incident.",
        incident_id="INC-105",
        timestamp=datetime(2026, 9, 18, 8, 15, tzinfo=timezone.utc),
    )

    with pytest.raises(NormalizationError, match="unsupported action"):
        ActionNormalizer().normalize(intent)


def test_high_impact_intent_requires_incident_id() -> None:
    intent = ActionIntent(
        action_id="ACT-106",
        trace_id="TRACE-106",
        actor="operations-agent",
        text="Restart the service.",
        timestamp=datetime(2026, 9, 18, 8, 15, tzinfo=timezone.utc),
    )

    with pytest.raises(NormalizationError, match="requires incident_id"):
        ActionNormalizer().normalize(intent)


def test_timestamp_requires_timezone() -> None:
    with pytest.raises(ValueError, match="timezone"):
        ActionIntent(
            action_id="ACT-107",
            trace_id="TRACE-107",
            actor="operations-agent",
            text="Restart the service.",
            incident_id="INC-107",
            timestamp=datetime(2026, 9, 18, 8, 15),
        )

@pytest.mark.parametrize(
    ("text", "expected_operation"),
    [
        ("Run reconciliation.", Operation.RECONCILE),
        ("Recover the connection.", Operation.RECOVER_CONNECTION),
        ("Resume operations.", Operation.RESUME),
    ],
)
def test_normalizes_supported_control_actions(
    text: str,
    expected_operation: Operation,
    restart_intent: ActionIntent,
) -> None:
    action = ActionNormalizer().normalize(restart_intent.model_copy(update={"text": text}))
    assert action.operation is expected_operation

