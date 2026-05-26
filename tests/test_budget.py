from app.services.budget_manager import check_budget


def test_check_budget_returns_status_details() -> None:
    result = check_budget(estimated_cost=0.01)

    assert result["budget_status"] in {"allowed", "blocked"}
    assert "remaining_budget" in result
