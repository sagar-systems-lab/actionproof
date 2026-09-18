from __future__ import annotations

import hashlib
import json

from app.models.action import NormalizedAction
from app.models.context import DecisionContext
from app.models.decision import PolicyDecision
from app.models.proof import EvidenceFact, LatencyBreakdown, ProofPacket


class ProofComposer:
    def compose(
        self,
        action: NormalizedAction,
        context: DecisionContext,
        decision: PolicyDecision,
        *,
        evidence: tuple[EvidenceFact, ...] | None = None,
        latency: LatencyBreakdown | None = None,
    ) -> ProofPacket:
        proof_evidence = (
            evidence
            if evidence is not None
            else self._evidence_from_context(context)
        )
        proof_id = self._proof_id(action, context, decision, proof_evidence)

        return ProofPacket(
            proof_id=proof_id,
            trace_id=action.trace_id,
            action=action,
            risk=action.impact,
            decision=decision.status,
            decision_code=decision.code,
            evidence=proof_evidence,
            matched_policy=decision.matched_rule,
            safe_next_action=decision.recommended_next_action,
            latency=latency or LatencyBreakdown(),
        )

    @staticmethod
    def _evidence_from_context(context: DecisionContext) -> tuple[EvidenceFact, ...]:
        if context.state is None:
            return ()

        state = context.state
        return (
            EvidenceFact(source="simulator", key="connection", value=state.connection.value),
            EvidenceFact(source="simulator", key="reconciliation", value=state.reconciliation.value),
            EvidenceFact(source="simulator", key="service", value=state.service.value),
            EvidenceFact(source="simulator", key="health", value=state.health.value),
            EvidenceFact(source="simulator", key="outstanding", value=state.outstanding.value),
            EvidenceFact(source="context", key="freshness", value=context.freshness.value),
        )

    @staticmethod
    def _proof_id(
        action: NormalizedAction,
        context: DecisionContext,
        decision: PolicyDecision,
        evidence: tuple[EvidenceFact, ...],
    ) -> str:
        canonical = {
            "action": action.model_dump(mode="json"),
            "context": context.model_dump(mode="json"),
            "decision": decision.model_dump(mode="json"),
            "evidence": [item.model_dump(mode="json") for item in evidence],
        }
        payload = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
        digest = hashlib.sha256(payload).hexdigest()[:12].upper()
        return f"PROOF-{digest}"
