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


def test_scenario_catalog_has_five_judge_scenarios() -> None:
    response = client.get("/api/runtime/scenarios")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [
        "safe-restart",
        "unsafe-restart",
        "missing-context",
        "stale-context",
        "successful-recovery",
    ]


def test_scenario_endpoint_returns_real_proof_shape(unsafe_state) -> None:
    runtime = make_runtime(unsafe_state)
    app.dependency_overrides[get_closed_loop_runtime] = lambda: runtime
    try:
        response = client.post("/api/runtime/scenarios/unsafe-restart")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["scenario_id"] == "unsafe-restart"
    assert (
        body["primary_evaluation"]["decision"]["code"]
        == "BLOCK_RECONCILIATION_REQUIRED"
    )
    assert len(body["primary_evaluation"]["proof"]["evidence"]) >= 3
    assert body["events"]
