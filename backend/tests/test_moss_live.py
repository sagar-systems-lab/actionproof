from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone

import pytest

from app.core.config import MossSettings
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
from app.retrieval.engine import RetrievalActionProofEngine
from app.retrieval.moss_client import MossClient
from app.retrieval.retriever import MossContextRetriever

pytestmark = pytest.mark.moss_live


def settings_or_skip() -> MossSettings:
    if not os.getenv("MOSS_PROJECT_ID") or not os.getenv("MOSS_PROJECT_KEY"):
        pytest.skip("live Moss credentials are not configured")
    return MossSettings.from_env()


def test_live_moss_retrieval_and_dynamic_state_update() -> None:
    settings = settings_or_skip()

    async def run() -> None:
        client = MossClient(settings)
        await client.start()

        unsafe_state = SimulatorState(
            connection=ConnectionState.DISCONNECTED,
            reconciliation=ReconciliationState.INCOMPLETE,
            service=ServiceState.RUNNING,
            health=HealthState.DEGRADED,
            outstanding=OutstandingState.UNKNOWN,
        )
        safe_state = SimulatorState(
            connection=ConnectionState.CONNECTED,
            reconciliation=ReconciliationState.COMPLETE,
            service=ServiceState.RUNNING,
            health=HealthState.HEALTHY,
            outstanding=OutstandingState.CLEAR,
        )

        engine = RetrievalActionProofEngine(
            MossContextRetriever(
                client,
                environment=settings.environment,
            )
        )
        intent = ActionIntent(
            action_id="ACT-LIVE-104",
            trace_id="TRACE-LIVE-104",
            actor="operations-agent",
            text="Restart the service.",
            incident_id="INC-104",
            timestamp=datetime.now(timezone.utc),
        )

        try:
            await client.upsert_live_state("INC-104", unsafe_state, version="2")
            blocked = await engine.evaluate(intent)
            assert blocked.decision.code is DecisionCode.BLOCK_RECONCILIATION_REQUIRED
            assert {
                item.source_type
                for item in blocked.proof.evidence
                if item.source_type is not None
            } >= {"policy", "runbook", "live_state"}
            assert blocked.proof.latency.retrieval_us > 0

            await client.upsert_live_state("INC-104", safe_state, version="3")
            allowed = await engine.evaluate(intent)
            assert allowed.decision.code is DecisionCode.ALLOW_SAFE_STATE
        finally:
            await client.upsert_live_state("INC-104", unsafe_state, version="4")

    asyncio.run(run())
