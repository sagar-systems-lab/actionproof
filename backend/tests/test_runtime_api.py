from fastapi.testclient import TestClient

from app.api.runtime import get_closed_loop_runtime
from app.main import app
from app.retrieval.engine import RetrievalActionProofEngine
from app.retrieval.retriever import MossContextRetriever
from app.runtime.events import FlightRecorder
from app.runtime.orchestrator import ClosedLoopRuntime

from tests.retrieval_fakes import StatefulFakeMossBackend


client = TestClient(app)


def make_runtime(unsafe_state) -> ClosedLoopRuntime:
    backend = StatefulFakeMossBackend(state=unsafe_state)
    events = FlightRecorder()
    engine = RetrievalActionProofEngine(
        MossContextRetriever(backend, environment="production"),
        events=events,
    )
    return ClosedLoopRuntime(engine, backend, events=events)


def test_runtime_hero_endpoint_returns_closed_loop_result(unsafe_state) -> None:
    runtime = make_runtime(unsafe_state)
    app.dependency_overrides[get_closed_loop_runtime] = lambda: runtime
    try:
        response = client.post(
            "/api/runtime/hero",
            json={"incident_id": "INC-104"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert (
        body["blocked_restart"]["decision"]["code"]
        == "BLOCK_RECONCILIATION_REQUIRED"
    )
    assert body["recovery"]["postflight"]["status"] == "VERIFIED"
    assert body["retry_restart"]["decision"]["code"] == "ALLOW_SAFE_STATE"

    app.dependency_overrides[get_closed_loop_runtime] = lambda: runtime
    try:
        events = client.get("/api/runtime/events")
    finally:
        app.dependency_overrides.clear()

    assert events.status_code == 200
    assert any(item["event"] == "POSTFLIGHT_VERIFIED" for item in events.json())
