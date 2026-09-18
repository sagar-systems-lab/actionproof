from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_evaluate_endpoint_returns_block_with_proof() -> None:
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
            },
            "context": {
                "state": {
                    "connection": "DISCONNECTED",
                    "reconciliation": "INCOMPLETE",
                    "service": "RUNNING",
                    "health": "DEGRADED",
                    "outstanding": "UNKNOWN",
                },
                "required_context_complete": True,
                "freshness": "FRESH",
                "policy_available": True,
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["decision"]["status"] == "BLOCK"
    assert body["decision"]["code"] == "BLOCK_RECONCILIATION_REQUIRED"
    assert body["proof"]["proof_id"].startswith("PROOF-")


def test_evaluate_endpoint_rejects_unrecognized_action() -> None:
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
            },
            "context": {
                "required_context_complete": False,
                "freshness": "UNKNOWN",
                "policy_available": True,
            },
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "unsupported action intent"
