from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

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


async def main() -> None:
    load_dotenv(ROOT / ".env")
    settings = MossSettings.from_env()
    client = MossClient(settings)
    await client.start()

    unsafe_state = SimulatorState(
        connection=ConnectionState.DISCONNECTED,
        reconciliation=ReconciliationState.INCOMPLETE,
        service=ServiceState.RUNNING,
        health=HealthState.DEGRADED,
        outstanding=OutstandingState.UNKNOWN,
    )
    await client.upsert_live_state("INC-104", unsafe_state, version="verify")

    engine = RetrievalActionProofEngine(
        MossContextRetriever(
            client,
            environment=settings.environment,
        )
    )

    result = await engine.evaluate(
        ActionIntent(
            action_id="ACT-LIVE-104",
            trace_id="TRACE-LIVE-104",
            actor="operations-agent",
            text="Restart the service.",
            incident_id="INC-104",
            timestamp=datetime.now(timezone.utc),
        )
    )

    source_types = {
        item.source_type
        for item in result.proof.evidence
        if item.source_type is not None
    }

    print(f"decision={result.decision.status.value}")
    print(f"decision_code={result.decision.code.value}")
    print(f"proof_id={result.proof.proof_id}")
    print(f"evidence={len(result.proof.evidence)}")
    print(f"source_types={','.join(sorted(source_types))}")
    print(f"retrieval_us={result.proof.latency.retrieval_us}")
    print(f"total_preflight_us={result.proof.latency.total_us}")

    if result.decision.code is not DecisionCode.BLOCK_RECONCILIATION_REQUIRED:
        raise SystemExit(
            "expected fresh unsafe state to block on incomplete reconciliation"
        )
    if not {"policy", "runbook", "live_state"}.issubset(source_types):
        raise SystemExit("required Moss evidence classes were not retrieved")

    print("MOSS_LIVE_VERIFY=PASS")


if __name__ == "__main__":
    asyncio.run(main())
