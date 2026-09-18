from fastapi.testclient import TestClient

from app.api.actions import get_retrieval_engine
from app.main import app
from app.retrieval.engine import RetrievalActionProofEngine
from app.retrieval.retriever import MossContextRetriever
from tests.retrieval_fakes import FakeMossBackend

client = TestClient(app)


def fake_engine() -> RetrievalActionProofEngine:
    return RetrievalActionProofEngine(
        MossContextRetriever(
            FakeMossBackend(),
            environment="production",
        )
    )


def test_evaluate_endpoint_returns_block_with_proof() -> None:
    app.dependency_overrides[get_retrieval_engine] = fake_engine
    try:
        response = client.post(
            "/api/evaluate",
            json={
                "intent": {
                    "action_id": "ACT-104",
                    "trace_id": "TRACE-104",
                    "actor": "operations-agent",
                    "text": "Restart the service.",
                    "incident_id": "INC-104",
                    "timestamp": "2026-09-18T08:15:00Z",
                }
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["decision"]["status"] == "BLOCK"
    assert body["decision"]["code"] == "BLOCK_RECONCILIATION_REQUIRED"
    assert body["proof"]["proof_id"].startswith("PROOF-")
    assert len(body["proof"]["evidence"]) >= 3


def test_evaluate_endpoint_rejects_unrecognized_action() -> None:
    app.dependency_overrides[get_retrieval_engine] = fake_engine
    try:
        response = client.post(
            "/api/evaluate",
            json={
                "intent": {
                    "action_id": "ACT-105",
                    "trace_id": "TRACE-105",
                    "actor": "operations-agent",
                    "text": "Write a summary.",
                    "incident_id": "INC-105",
                    "timestamp": "2026-09-18T08:15:00Z",
                }
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["detail"] == "unsupported action intent"


def test_retrieval_status_does_not_expose_credentials() -> None:
    response = client.get("/api/retrieval/status")

    assert response.status_code == 200
    body = response.json()
    assert "project_key" not in body
    assert "project_id" not in body
    assert set(body["indexes"]) == {"policy", "knowledge", "live_state"}
