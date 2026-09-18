from app.agent.normalizer import ActionNormalizer
from app.models.action import ActionIntent, Operation
from app.retrieval.resolver import ContextRequirementResolver


def test_restart_resolver_queries_only_required_domains(
    restart_intent: ActionIntent,
) -> None:
    action = ActionNormalizer().normalize(restart_intent)
    requirements = ContextRequirementResolver().resolve(action)

    assert [item.key for item in requirements] == [
        "restart_policy",
        "current_state",
        "recovery_runbook",
        "incident_history",
    ]
    assert requirements[0].required is True
    assert requirements[1].incident_scoped is True
    assert requirements[3].required is False


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
