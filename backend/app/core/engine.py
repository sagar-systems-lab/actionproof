from app.agent.normalizer import ActionNormalizer
from app.models.scenario import EvaluationRequest, EvaluationResult
from app.policy.engine import PolicyEngine
from app.proof.composer import ProofComposer


class ActionProofEngine:
    def __init__(
        self,
        normalizer: ActionNormalizer | None = None,
        policy: PolicyEngine | None = None,
        proofs: ProofComposer | None = None,
    ) -> None:
        self.normalizer = normalizer or ActionNormalizer()
        self.policy = policy or PolicyEngine()
        self.proofs = proofs or ProofComposer()

    def evaluate(self, request: EvaluationRequest) -> EvaluationResult:
        action = self.normalizer.normalize(request.intent)
        decision = self.policy.evaluate(action, request.context)
        proof = self.proofs.compose(action, request.context, decision)
        return EvaluationResult(action=action, decision=decision, proof=proof)
