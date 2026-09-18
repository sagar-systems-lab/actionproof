from __future__ import annotations

from time import perf_counter_ns

from app.agent.normalizer import ActionNormalizer
from app.models.action import ActionIntent
from app.models.decision import DecisionStatus
from app.models.proof import EvidenceFact, LatencyBreakdown
from app.models.scenario import EvaluationResult
from app.policy.engine import PolicyEngine
from app.proof.composer import ProofComposer
from app.runtime.events import RuntimeEventSink, RuntimeEventType

from .retriever import MossContextRetriever
from .schemas import RetrievalOutcome


class RetrievalActionProofEngine:
    def __init__(
        self,
        retriever: MossContextRetriever,
        normalizer: ActionNormalizer | None = None,
        policy: PolicyEngine | None = None,
        proofs: ProofComposer | None = None,
        events: RuntimeEventSink | None = None,
    ) -> None:
        self.retriever = retriever
        self.normalizer = normalizer or ActionNormalizer()
        self.policy = policy or PolicyEngine()
        self.proofs = proofs or ProofComposer()
        self.events = events

    async def evaluate(self, intent: ActionIntent) -> EvaluationResult:
        total_started = perf_counter_ns()
        action = self.normalizer.normalize(intent)
        self._record(
            RuntimeEventType.ACTION_NORMALIZED,
            action.trace_id,
            f"Normalized {action.operation.value} as {action.impact.value} impact.",
        )

        self._record(
            RuntimeEventType.MOSS_QUERY_STARTED,
            action.trace_id,
            "Retrieving action-specific policy and operational context.",
        )
        retrieval = await self.retriever.retrieve(action)
        self._record(
            RuntimeEventType.MOSS_QUERY_COMPLETED,
            action.trace_id,
            (
                f"Retrieved {len(retrieval.evidence)} evidence items "
                f"in {retrieval.metrics.retrieval_us} us."
            ),
        )
        self._record(
            RuntimeEventType.CONTEXT_VALIDATED,
            action.trace_id,
            (
                f"complete={retrieval.context.required_context_complete} "
                f"freshness={retrieval.context.freshness.value} "
                f"issues={len(retrieval.issues)}"
            ),
        )

        policy_started = perf_counter_ns()
        decision = self.policy.evaluate(action, retrieval.context)
        policy_us = (perf_counter_ns() - policy_started) // 1_000
        self._record(
            RuntimeEventType.POLICY_EVALUATED,
            action.trace_id,
            f"{decision.status.value}: {decision.code.value}",
        )

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
        self._record(
            RuntimeEventType.PROOF_CREATED,
            action.trace_id,
            f"{proof.proof_id} bound to {action.operation.value}.",
        )

        if decision.status is DecisionStatus.ALLOW:
            self._record(
                RuntimeEventType.ACTION_ALLOWED,
                action.trace_id,
                decision.reason,
            )
        elif decision.status is DecisionStatus.BLOCK:
            self._record(
                RuntimeEventType.ACTION_BLOCKED,
                action.trace_id,
                decision.reason,
            )

        return EvaluationResult(
            action=action,
            decision=decision,
            proof=proof,
        )

    def _record(
        self,
        event: RuntimeEventType,
        trace_id: str,
        summary: str,
    ) -> None:
        if self.events is not None:
            self.events.record(
                event,
                trace_id=trace_id,
                summary=summary,
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
