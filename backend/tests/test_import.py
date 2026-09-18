from fastapi.testclient import TestClient

from app.main import app


def test_backend_imports() -> None:
    assert app.title == "ActionProof API"


def test_health_route() -> None:
    response = TestClient(app).get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["phase"] == "01-foundation"
