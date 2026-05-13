from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_route_endpoint() -> None:
    response = client.post("/route", json={"prompt": "Route this request"})

    assert response.status_code == 200
    assert response.json()["selected_model"] == "demo-model"
