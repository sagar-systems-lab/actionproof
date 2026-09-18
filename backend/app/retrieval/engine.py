from __future__ import annotations

from time import perf_counter_ns

from app.agent.normalizer import ActionNormalizer
from app.models.action import ActionIntent
from app.models.proof import EvidenceFact, LatencyBreakdown
from app.models.scenario import EvaluationResult
from app.policy.engine import PolicyEngine
from app.proof.composer import ProofComposer

from .retriever import MossContextRetriever
from .schemas import RetrievalOutcome


class RetrievalActionProofEngine:
    def __init__(
        self,
        retriever: MossContextRetriever,
        normalizer: ActionNormalizer | None = None,
        policy: PolicyEngine | None = None,
        proofs: ProofComposer | None = None,
    ) -> None:
        self.retriever = retriever
        self.normalizer = normalizer or ActionNormalizer()
        self.policy = policy or PolicyEngine()
        self.proofs = proofs or ProofComposer()

    async def evaluate(self, intent: ActionIntent) -> EvaluationResult:
        total_started = perf_counter_ns()
        action = self.normalizer.normalize(intent)

        retrieval = await self.retriever.retrieve(action)

        policy_started = perf_counter_ns()
        decision = self.policy.evaluate(action, retrieval.context)
        policy_us = (perf_counter_ns() - policy_started) // 1_000

        proof_started = perf_counter_ns()
        proof = self.proofs.compose(
            action,
            retrieval.context,
            decision,
            evidence=self._proof_evidence(retrieval),
        )
        proof_us = (perf_counter_ns() - proof_started) // 1_000

        latency = LatencyBreakdown(
            retrieval_us=retrieval.metrics.retrieval_us,
            freshness_us=retrieval.metrics.freshness_us,
            policy_us=int(policy_us),
            proof_us=int(proof_us),
            total_us=int((perf_counter_ns() - total_started) // 1_000),
        )
        proof = proof.model_copy(update={"latency": latency})

        return EvaluationResult(
            action=action,
            decision=decision,
            proof=proof,
        )

    @staticmethod
    def _proof_evidence(
        retrieval: RetrievalOutcome,
    ) -> tuple[EvidenceFact, ...]:
        return tuple(
            EvidenceFact(
                source=item.index_name,
                key=item.requirement_key,
                value=item.content,
                document_id=item.document_id,
                source_type=item.source_type.value,
                authority=item.authority,
                version=item.version,
                freshness=item.freshness,
                score=item.score,
                updated_at=item.updated_at,
            )
            for item in retrieval.evidence
        )
