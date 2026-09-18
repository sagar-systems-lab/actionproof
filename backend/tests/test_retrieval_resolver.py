from app.agent.normalizer import ActionNormalizer
from app.models.action import ActionIntent, Operation
from app.retrieval.resolver import ContextRequirementResolver


def test_restart_resolver_keeps_optional_history_off_the_hot_path(
    restart_intent: ActionIntent,
) -> None:
    action = ActionNormalizer().normalize(restart_intent)
    requirements = ContextRequirementResolver().resolve(action)

    assert [item.key for item in requirements] == [
        "restart_policy",
        "current_state",
        "recovery_runbook",
    ]
    assert all(item.required for item in requirements)
    assert requirements[1].incident_scoped is True


def test_resume_resolver_is_operation_specific(
    restart_intent: ActionIntent,
) -> None:
    action = ActionNormalizer().normalize(
        restart_intent.model_copy(update={"text": "Resume operations."})
    )
    assert action.operation is Operation.RESUME

    requirements = ContextRequirementResolver().resolve(action)

    assert [item.key for item in requirements] == [
        "resume_policy",
        "current_state",
        "resume_runbook",
    ]
