from __future__ import annotations

from app.core.config import MossSettings
from app.retrieval.engine import RetrievalActionProofEngine
from app.retrieval.moss_client import MossClient
from app.retrieval.retriever import MossContextRetriever

from .events import FlightRecorder
from .orchestrator import ClosedLoopRuntime


def build_closed_loop_runtime(settings: MossSettings) -> ClosedLoopRuntime:
    events = FlightRecorder()
    client = MossClient(settings)
    engine = RetrievalActionProofEngine(
        MossContextRetriever(
            client,
            environment=settings.environment,
        ),
        events=events,
    )
    return ClosedLoopRuntime(
        engine,
        client,
        events=events,
    )
