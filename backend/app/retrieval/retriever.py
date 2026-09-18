from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from time import perf_counter_ns
from typing import Protocol

from app.models.action import NormalizedAction
from app.models.context import ContextFreshness, DecisionContext
from app.models.state import (
    ConnectionState,
    HealthState,
    OutstandingState,
    ReconciliationState,
    ServiceState,
    SimulatorState,
)

from .resolver import ContextRequirementResolver
from .schemas import (
    ContextRequirement,
    RawRetrievedDocument,
    RetrievalIssue,
    RetrievalIssueCode,
    RetrievalMetrics,
    RetrievalOutcome,
    RetrievedEvidence,
    SourceType,
)
from .validator import EvidenceValidator


class RetrievalBackend(Protocol):
    async def query(
        self,
        requirement: ContextRequirement,
        *,
        incident_id: str,
    ) -> list[RawRetrievedDocument]: ...


class MossContextRetriever:
    def __init__(
        self,
        client: RetrievalBackend,
        *,
        environment: str,
        resolver: ContextRequirementResolver | None = None,
        validator: EvidenceValidator | None = None,
    ) -> None:
        self.client = client
        self.environment = environment
        self.resolver = resolver or ContextRequirementResolver()
        self.validator = validator or EvidenceValidator()

    async def retrieve(self, action: NormalizedAction) -> RetrievalOutcome:
        requirements = self.resolver.resolve(action)
        retrieval_started = perf_counter_ns()

        raw_results = await asyncio.gather(
            *[
                self.client.query(
                    requirement,
                    incident_id=action.incident_id,
                )
                for requirement in requirements
            ],
            return_exceptions=True,
        )
        retrieval_us = (perf_counter_ns() - retrieval_started) // 1_000

        validation_started = perf_counter_ns()
        evidence: list[RetrievedEvidence] = []
        issues: list[RetrievalIssue] = []
        satisfied: set[str] = set()
        required_query_failed = False
        now = datetime.now(timezone.utc)

        for requirement, raw_result in zip(requirements, raw_results, strict=True):
            if isinstance(raw_result, BaseException):
                issues.append(
                    RetrievalIssue(
                        requirement_key=requirement.key,
                        code=RetrievalIssueCode.UNAVAILABLE,
                        detail=str(raw_result),
                    )
                )
                if requirement.required:
                    required_query_failed = True
                continue

            if not raw_result:
                issues.append(
                    RetrievalIssue(
                        requirement_key=requirement.key,
                        code=RetrievalIssueCode.ZERO_RESULTS,
                        detail="Moss returned no documents.",
                    )
                )
                continue

            valid_for_requirement: list[RetrievedEvidence] = []
            for document in raw_result:
                valid, issue = self.validator.validate(
                    document,
                    requirement,
                    environment=self.environment,
                    incident_id=action.incident_id,
                    now=now,
                )
                if valid is not None:
                    valid_for_requirement.append(valid)
                if issue is not None:
                    issues.append(issue)

            if valid_for_requirement:
                satisfied.add(requirement.key)
                evidence.extend(valid_for_requirement)

        state, state_issue = self._state_from_evidence(evidence)
        if state_issue is not None:
            issues.append(state_issue)

        required_complete = all(
            not requirement.required or requirement.key in satisfied
            for requirement in requirements
        ) and state is not None

        policy_available = any(
            item.source_type is SourceType.POLICY
            and item.requirement_key in satisfied
            for item in evidence
        )

        freshness = self._aggregate_freshness(
            requirements,
            evidence,
            satisfied,
        )

        freshness_us = (perf_counter_ns() - validation_started) // 1_000

        context = DecisionContext(
            state=state,
            required_context_complete=required_complete,
            freshness=freshness,
            policy_available=policy_available,
            retrieval_failed=required_query_failed,
        )

        return RetrievalOutcome(
            context=context,
            requirements=requirements,
            evidence=tuple(evidence),
            issues=tuple(issues),
            metrics=RetrievalMetrics(
                retrieval_us=int(retrieval_us),
                freshness_us=int(freshness_us),
            ),
        )

    @staticmethod
    def _aggregate_freshness(
        requirements: tuple[ContextRequirement, ...],
        evidence: list[RetrievedEvidence],
        satisfied: set[str],
    ) -> ContextFreshness:
        required_keys = {
            requirement.key
            for requirement in requirements
            if requirement.required and requirement.key in satisfied
        }
        required_evidence = [
            item for item in evidence if item.requirement_key in required_keys
        ]

        if not required_evidence:
            return ContextFreshness.UNKNOWN

        if any(
            item.freshness is ContextFreshness.STALE
            for item in required_evidence
        ):
            return ContextFreshness.STALE

        if any(
            item.freshness is ContextFreshness.UNKNOWN
            for item in required_evidence
        ):
            return ContextFreshness.UNKNOWN

        return ContextFreshness.FRESH

    @staticmethod
    def _state_from_evidence(
        evidence: list[RetrievedEvidence],
    ) -> tuple[SimulatorState | None, RetrievalIssue | None]:
        state_evidence = next(
            (
                item
                for item in evidence
                if item.source_type is SourceType.LIVE_STATE
            ),
            None,
        )
        if state_evidence is None:
            return None, None

        metadata = state_evidence.metadata
        try:
            state = SimulatorState(
                connection=ConnectionState(metadata["connection"]),
                reconciliation=ReconciliationState(metadata["reconciliation"]),
                service=ServiceState(metadata["service"]),
                health=HealthState(metadata["health"]),
                outstanding=OutstandingState(metadata["outstanding"]),
            )
        except (KeyError, ValueError) as exc:
            return None, RetrievalIssue(
                requirement_key=state_evidence.requirement_key,
                code=RetrievalIssueCode.STATE_PARSE_FAILED,
                detail=f"live state metadata is invalid: {exc}",
            )

        return state, None
