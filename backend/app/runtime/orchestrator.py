from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol
from uuid import uuid4

from app.models.action import ActionIntent
from app.models.decision import DecisionCode, DecisionStatus
from app.models.scenario import EvaluationResult
from app.models.state import (
    ConnectionState,
    HealthState,
    OutstandingState,
    ReconciliationState,
    ServiceState,
    SimulatorState,
)
from app.retrieval.engine import RetrievalActionProofEngine

from .authorization import ProofAuthority
from .events import FlightRecorder, RuntimeEventType
from .executor import ProtectedToolExecutor
from .models import (
    ExecutedActionResult,
    HeroScenarioResult,
    PostflightStatus,
)
from .postflight import PostflightVerifier
from .state_store import RuntimeStateStore


class LiveStatePublisher(Protocol):
    async def upsert_live_state(
        self,
        incident_id: str,
        state: SimulatorState,
        *,
        version: str = "1",
        ttl_seconds: int = 30,
    ) -> None: ...


class RuntimeInvariantError(RuntimeError):
    pass


class ClosedLoopRuntime:
    def __init__(
        self,
        engine: RetrievalActionProofEngine,
        publisher: LiveStatePublisher,
        *,
        events: FlightRecorder | None = None,
        state_store: RuntimeStateStore | None = None,
        authority: ProofAuthority | None = None,
        postflight: PostflightVerifier | None = None,
    ) -> None:
        self.engine = engine
        self.publisher = publisher
        self.events = events or FlightRecorder()
        self.state_store = state_store or RuntimeStateStore()
        self.authority = authority or ProofAuthority()
        self.executor = ProtectedToolExecutor(self.state_store, self.authority)
        self.postflight = postflight or PostflightVerifier()
        self._state_version = 0

    async def inject_disconnect(
        self,
        incident_id: str,
        *,
        trace_id: str,
    ) -> SimulatorState:
        state = self.unsafe_state()
        await self._publish_state(incident_id, state)
        self.state_store.set(incident_id, state)
        self.events.record(
            RuntimeEventType.INCIDENT_CREATED,
            trace_id=trace_id,
            summary=(
                f"{incident_id}: connection DISCONNECTED and "
                "reconciliation INCOMPLETE."
            ),
        )
        return state

    async def evaluate(self, intent: ActionIntent) -> EvaluationResult:
        self.events.record(
            RuntimeEventType.AGENT_INTENT_CREATED,
            trace_id=intent.trace_id,
            summary=intent.text,
        )
        return await self.engine.evaluate(intent)

    async def execute_allowed(
        self,
        result: EvaluationResult,
    ) -> ExecutedActionResult:
        permit = self.authority.issue(result)
        execution = self.executor.execute(result.action, permit)
        self.events.record(
            RuntimeEventType.ACTION_EXECUTED,
            trace_id=result.action.trace_id,
            summary=execution.message,
        )

        observed = self.state_store.get(result.action.incident_id)
        postflight = self.postflight.verify(result.action, observed)
        self.events.record(
            (
                RuntimeEventType.POSTFLIGHT_VERIFIED
                if postflight.status is PostflightStatus.VERIFIED
                else RuntimeEventType.POSTFLIGHT_FAILED
            ),
            trace_id=result.action.trace_id,
            summary=postflight.message,
        )

        if postflight.status is not PostflightStatus.VERIFIED:
            raise RuntimeInvariantError("postflight verification failed")

        await self._publish_state(result.action.incident_id, observed)

        return ExecutedActionResult(
            evaluation=result,
            execution=execution,
            postflight=postflight,
        )

    async def run_hero_scenario(
        self,
        incident_id: str = "INC-104",
    ) -> HeroScenarioResult:
        start_sequence = self.events.last_sequence
        trace_root = f"TRACE-HERO-{uuid4().hex[:10].upper()}"

        self.events.record(
            RuntimeEventType.SCENARIO_STARTED,
            trace_id=trace_root,
            summary="Unsafe restart recovery scenario started.",
        )
        initial = await self.inject_disconnect(
            incident_id,
            trace_id=trace_root,
        )

        blocked = await self.evaluate(
            self._intent(
                action_id=f"{trace_root}-RESTART-1",
                trace_id=trace_root,
                incident_id=incident_id,
                text="Restart the service.",
            )
        )
        if blocked.decision.code is not DecisionCode.BLOCK_RECONCILIATION_REQUIRED:
            raise RuntimeInvariantError(
                "hero restart did not block on incomplete reconciliation"
            )
        if blocked.decision.recommended_next_action != "run_reconciliation":
            raise RuntimeInvariantError("safe recovery action was not surfaced")

        recovery_evaluation = await self.evaluate(
            self._intent(
                action_id=f"{trace_root}-RECONCILE",
                trace_id=trace_root,
                incident_id=incident_id,
                text="Run reconciliation.",
            )
        )
        if recovery_evaluation.decision.status is not DecisionStatus.ALLOW:
            raise RuntimeInvariantError("reconciliation was not authorized")

        recovery = await self.execute_allowed(recovery_evaluation)

        retry = await self.evaluate(
            self._intent(
                action_id=f"{trace_root}-RESTART-2",
                trace_id=trace_root,
                incident_id=incident_id,
                text="Restart the service.",
            )
        )
        if retry.decision.code is not DecisionCode.ALLOW_SAFE_STATE:
            raise RuntimeInvariantError(
                "restart retry was not allowed after reconciliation"
            )

        final_state = self.state_store.get(incident_id)
        return HeroScenarioResult(
            incident_id=incident_id,
            initial_state=initial,
            blocked_restart=blocked,
            recovery=recovery,
            retry_restart=retry,
            final_state=final_state,
            events=self.events.snapshot(after_sequence=start_sequence),
        )

    async def _publish_state(
        self,
        incident_id: str,
        state: SimulatorState,
    ) -> None:
        self._state_version += 1
        await self.publisher.upsert_live_state(
            incident_id,
            state,
            version=f"runtime-{self._state_version}",
            ttl_seconds=300,
        )

    @staticmethod
    def _intent(
        *,
        action_id: str,
        trace_id: str,
        incident_id: str,
        text: str,
    ) -> ActionIntent:
        return ActionIntent(
            action_id=action_id,
            trace_id=trace_id,
            actor="operations-agent",
            text=text,
            incident_id=incident_id,
            timestamp=datetime.now(timezone.utc),
        )

    @staticmethod
    def unsafe_state() -> SimulatorState:
        return SimulatorState(
            connection=ConnectionState.DISCONNECTED,
            reconciliation=ReconciliationState.INCOMPLETE,
            service=ServiceState.RUNNING,
            health=HealthState.DEGRADED,
            outstanding=OutstandingState.UNKNOWN,
        )
