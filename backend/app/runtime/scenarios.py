from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from uuid import uuid4

from app.models.action import ActionIntent
from app.models.decision import DecisionCode
from app.models.state import (
    ConnectionState,
    HealthState,
    OutstandingState,
    ReconciliationState,
    ServiceState,
    SimulatorState,
)

from .events import RuntimeEventType
from .models import (
    ProductScenarioResult,
    ScenarioDefinition,
    ScenarioId,
)
from .orchestrator import ClosedLoopRuntime, RuntimeInvariantError


SCENARIOS: tuple[ScenarioDefinition, ...] = (
    ScenarioDefinition(
        id=ScenarioId.SAFE_RESTART,
        label="Safe Restart",
        description="Current state is connected, reconciled, and healthy.",
        expected="ALLOW",
    ),
    ScenarioDefinition(
        id=ScenarioId.UNSAFE_RESTART,
        label="Unsafe Restart",
        description="Connection is down and reconciliation is incomplete.",
        expected="BLOCK",
    ),
    ScenarioDefinition(
        id=ScenarioId.MISSING_CONTEXT,
        label="Missing Context",
        description="Required live state is unavailable for the incident.",
        expected="CONFIRM",
    ),
    ScenarioDefinition(
        id=ScenarioId.STALE_CONTEXT,
        label="Stale Context",
        description="Required state exists but has exceeded its freshness TTL.",
        expected="BLOCK",
    ),
    ScenarioDefinition(
        id=ScenarioId.SUCCESSFUL_RECOVERY,
        label="Successful Recovery",
        description="Blocked restart is recovered through reconciliation and retried.",
        expected="BLOCK → VERIFIED → ALLOW",
    ),
)

_DEFINITIONS = {item.id: item for item in SCENARIOS}


class ProductScenarioRunner:
    def __init__(self, runtime: ClosedLoopRuntime) -> None:
        self.runtime = runtime

    async def run(self, scenario_id: ScenarioId) -> ProductScenarioResult:
        definition = _DEFINITIONS[scenario_id]
        if scenario_id is ScenarioId.SUCCESSFUL_RECOVERY:
            return await self._successful_recovery(definition)
        if scenario_id is ScenarioId.MISSING_CONTEXT:
            return await self._missing_context(definition)
        if scenario_id is ScenarioId.STALE_CONTEXT:
            return await self._stale_context(definition)

        state = (
            self._safe_state()
            if scenario_id is ScenarioId.SAFE_RESTART
            else self.runtime.unsafe_state()
        )
        incident_id = (
            "INC-SAFE-RESTART"
            if scenario_id is ScenarioId.SAFE_RESTART
            else "INC-UNSAFE-RESTART"
        )
        expected_code = (
            DecisionCode.ALLOW_SAFE_STATE
            if scenario_id is ScenarioId.SAFE_RESTART
            else DecisionCode.BLOCK_RECONCILIATION_REQUIRED
        )
        return await self._state_restart(
            definition,
            incident_id=incident_id,
            state=state,
            expected_code=expected_code,
        )

    async def _state_restart(
        self,
        definition: ScenarioDefinition,
        *,
        incident_id: str,
        state: SimulatorState,
        expected_code: DecisionCode,
        ttl_seconds: int = 300,
        wait_seconds: float = 0,
    ) -> ProductScenarioResult:
        start_sequence = self.runtime.events.last_sequence
        trace_id = self._trace(definition.id)

        self.runtime.events.record(
            RuntimeEventType.SCENARIO_STARTED,
            trace_id=trace_id,
            summary=f"{definition.label} scenario started.",
        )
        await self.runtime.publisher.upsert_live_state(
            incident_id,
            state,
            version=f"scenario-{uuid4().hex[:8]}",
            ttl_seconds=ttl_seconds,
        )
        self.runtime.state_store.set(incident_id, state)
        self.runtime.events.record(
            RuntimeEventType.INCIDENT_CREATED,
            trace_id=trace_id,
            summary=self._state_summary(incident_id, state),
        )

        if wait_seconds:
            await asyncio.sleep(wait_seconds)

        evaluation = await self.runtime.evaluate(
            self._restart_intent(
                trace_id=trace_id,
                incident_id=incident_id,
            )
        )
        if evaluation.decision.code is not expected_code:
            raise RuntimeInvariantError(
                f"{definition.id.value} produced {evaluation.decision.code.value}, "
                f"expected {expected_code.value}"
            )

        return ProductScenarioResult(
            scenario_id=definition.id,
            label=definition.label,
            description=definition.description,
            incident_id=incident_id,
            initial_state=state,
            primary_evaluation=evaluation,
            final_state=state,
            events=self.runtime.events.snapshot(after_sequence=start_sequence),
        )

    async def _missing_context(
        self,
        definition: ScenarioDefinition,
    ) -> ProductScenarioResult:
        start_sequence = self.runtime.events.last_sequence
        trace_id = self._trace(definition.id)
        incident_id = f"INC-MISSING-{uuid4().hex[:10].upper()}"

        self.runtime.events.record(
            RuntimeEventType.SCENARIO_STARTED,
            trace_id=trace_id,
            summary=f"{definition.label} scenario started.",
        )
        self.runtime.events.record(
            RuntimeEventType.INCIDENT_CREATED,
            trace_id=trace_id,
            summary=f"{incident_id}: required live state is unavailable.",
        )

        evaluation = await self.runtime.evaluate(
            self._restart_intent(
                trace_id=trace_id,
                incident_id=incident_id,
            )
        )
        if evaluation.decision.code is not DecisionCode.CONFIRM_CONTEXT_INCOMPLETE:
            raise RuntimeInvariantError(
                "missing context did not require confirmation"
            )

        return ProductScenarioResult(
            scenario_id=definition.id,
            label=definition.label,
            description=definition.description,
            incident_id=incident_id,
            initial_state=None,
            primary_evaluation=evaluation,
            final_state=None,
            events=self.runtime.events.snapshot(after_sequence=start_sequence),
        )

    async def _stale_context(
        self,
        definition: ScenarioDefinition,
    ) -> ProductScenarioResult:
        return await self._state_restart(
            definition,
            incident_id="INC-STALE-CONTEXT",
            state=self._safe_state(),
            expected_code=DecisionCode.BLOCK_CONTEXT_STALE,
            ttl_seconds=1,
            wait_seconds=1.2,
        )

    async def _successful_recovery(
        self,
        definition: ScenarioDefinition,
    ) -> ProductScenarioResult:
        result = await self.runtime.run_hero_scenario("INC-SUCCESSFUL-RECOVERY")
        return ProductScenarioResult(
            scenario_id=definition.id,
            label=definition.label,
            description=definition.description,
            incident_id=result.incident_id,
            initial_state=result.initial_state,
            primary_evaluation=result.blocked_restart,
            recovery=result.recovery,
            final_evaluation=result.retry_restart,
            final_state=result.final_state,
            events=result.events,
        )

    @staticmethod
    def _safe_state() -> SimulatorState:
        return SimulatorState(
            connection=ConnectionState.CONNECTED,
            reconciliation=ReconciliationState.COMPLETE,
            service=ServiceState.RUNNING,
            health=HealthState.HEALTHY,
            outstanding=OutstandingState.CLEAR,
        )

    @staticmethod
    def _trace(scenario_id: ScenarioId) -> str:
        suffix = uuid4().hex[:10].upper()
        return f"TRACE-{scenario_id.value.upper()}-{suffix}"

    @staticmethod
    def _restart_intent(
        *,
        trace_id: str,
        incident_id: str,
    ) -> ActionIntent:
        return ActionIntent(
            action_id=f"{trace_id}-RESTART",
            trace_id=trace_id,
            actor="operations-agent",
            text="Restart the service.",
            incident_id=incident_id,
            timestamp=datetime.now(timezone.utc),
        )

    @staticmethod
    def _state_summary(
        incident_id: str,
        state: SimulatorState,
    ) -> str:
        return (
            f"{incident_id}: connection {state.connection.value}, "
            f"reconciliation {state.reconciliation.value}, "
            f"health {state.health.value}."
        )
