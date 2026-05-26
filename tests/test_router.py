from fastapi.testclient import TestClient

from app.database import init_db
from app.main import app


init_db()
client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_route_endpoint() -> None:
    response = client.post("/route", json={"prompt": "Route this request"})

    assert response.status_code == 200
    body = response.json()

    assert body["selected_model"] in {
        "fake-cheap-model",
        "fake-mid-model",
        "fake-expert-model",
        "deepseek-chat",
        "deepseek-reasoner",
        "gpt-4.1-nano",
        "gpt-4.1-mini",
    }
    assert body["provider"] in {"fake", "deepseek", "openai"}
    assert body["budget_status"] in {"allowed", "blocked"}
    assert "difficulty_score" in body
    assert "llm_mode" in body
