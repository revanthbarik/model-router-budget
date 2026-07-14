from unittest.mock import patch

from fastapi.testclient import TestClient

from app.database import get_connection, init_db
from app.main import app
from app.schemas.router_schema import RouteRequest
from app.services.budget_manager import get_budget_status, update_monthly_budget
from app.services.cost_calculator import estimate_input_cost_for_model


init_db()
client = TestClient(app)


def _seed_spend(amount: float) -> None:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO request_logs (
                    prompt, answer, difficulty, difficulty_score, selected_tier,
                    provider, selected_model, estimated_cost, billable_cost, latency_ms,
                    budget_status, llm_mode, input_tokens, output_tokens, total_tokens
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    "seed",
                    "",
                    "easy",
                    1,
                    "cheap",
                    "openai",
                    "gpt-4o-mini",
                    amount,
                    amount,
                    1.0,
                    "allowed",
                    "openai",
                    1,
                    1,
                    2,
                ),
            )
        conn.commit()


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"ok", "degraded"}
    assert "database" in payload


def test_force_run_defaults_false_in_schema() -> None:
    assert RouteRequest(prompt="x").force_run is False


def test_safe_request_invokes_provider() -> None:
    update_monthly_budget(5.0)
    with patch("app.api.routes.call_llm") as mock_llm:
        mock_llm.return_value = {
            "answer": "ok",
            "llm_mode": "fake",
            "input_tokens": 10,
            "output_tokens": 5,
            "total_tokens": 15,
        }
        response = client.post("/route", json={"prompt": "safe request"})
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["forced"] is False
        mock_llm.assert_called_once()


def test_over_budget_warning_does_not_call_provider_or_deduct() -> None:
    update_monthly_budget(0.10)
    _seed_spend(0.099999)
    before = get_budget_status()["monthly_billable_used"]

    with patch("app.api.routes.call_llm") as mock_llm:
        response = client.post(
            "/route",
            json={
                "prompt": "This is a longer soft-gate test prompt for tokens",
                "force_run": False,
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "budget_warning"
        assert body["estimated_cost"] > body["remaining_budget"]
        assert (
            body["message"]
            == "This prompt is estimated to exceed your remaining budget."
        )
        mock_llm.assert_not_called()

    after = get_budget_status()["monthly_billable_used"]
    assert after == before


def test_force_run_invokes_provider_and_allows_negative_remaining() -> None:
    update_monthly_budget(0.10)
    _seed_spend(0.099999)
    prompt = "This is a longer soft-gate test prompt for tokens"
    selected_model = "gpt-4o-mini"

    with patch("app.api.routes.call_llm") as mock_llm:
        mock_llm.return_value = {
            "answer": "forced answer",
            "llm_mode": "openai",
            "input_tokens": 1000,
            "output_tokens": 500,
            "total_tokens": 1500,
        }
        with patch("app.api.routes.choose_model") as mock_choose:
            mock_choose.return_value = {
                "selected_tier": "cheap",
                "selected_model": selected_model,
                "provider": "openai",
            }
            response = client.post(
                "/route",
                json={"prompt": prompt, "force_run": True},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["forced"] is True
        assert body["budget_status"] == "forced"
        assert body["actual_cost"] > 0
        mock_llm.assert_called_once()

    status = get_budget_status()
    assert status["remaining_budget"] < 0


def test_pre_call_gate_uses_input_estimate_only() -> None:
    prompt = "alpha beta gamma"
    estimated = estimate_input_cost_for_model(prompt, "gpt-4o")
    # 3 words * 2 = 6 tokens * 2.50 / 1M
    assert estimated == (6 / 1_000_000) * 2.50


def test_patch_budget_limit_resets_spend() -> None:
    update_monthly_budget(5.0, reset_usage=True)
    _seed_spend(1.25)
    assert get_budget_status()["monthly_billable_used"] >= 1.25

    response = client.patch(
        "/api/budget/limit",
        json={"limit": 8.0, "reset_usage": True},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["monthly_budget"] == 8.0
    assert body["monthly_billable_used"] == 0.0
    assert body["remaining_budget"] == 8.0

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) AS c FROM app_settings WHERE key = %s",
                ("monthly_budget_limit",),
            )
            count = cursor.fetchone()["c"]
            cursor.execute("SELECT COUNT(*) AS c FROM request_logs")
            logs = cursor.fetchone()["c"]

    assert count == 1
    assert logs == 0


def test_invalid_budget_limit_rejected() -> None:
    response = client.patch("/api/budget/limit", json={"limit": 0})
    assert response.status_code == 422

    response = client.patch("/api/budget/limit", json={"limit": -1})
    assert response.status_code == 422


def test_route_endpoint_contract() -> None:
    update_monthly_budget(5.0)
    response = client.post("/route", json={"prompt": "Route this request"})
    assert response.status_code == 200
    body = response.json()

    if body.get("status") == "budget_warning":
        assert "estimated_cost" in body
        assert "remaining_budget" in body
        return

    assert body["selected_model"] in {
        "gpt-4o-mini",
        "gpt-4o",
        "deepseek-chat",
        "deepseek-reasoner",
    }
    assert body["provider"] in {"fake", "deepseek", "openai"}
    assert body["budget_status"] in {"allowed", "forced"}
    assert "difficulty_score" in body
    assert "llm_mode" in body
    assert "estimated_input_tokens" in body
    assert "billable_cost" in body
    assert "actual_cost" in body
    assert "forced" in body
