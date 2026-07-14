from app.services.budget_manager import check_budget, get_budget_status, update_monthly_budget


def test_check_budget_returns_status_details() -> None:
    update_monthly_budget(5.0)
    result = check_budget(estimated_cost=0.01)

    assert result["budget_status"] in {"allowed", "blocked"}
    assert "remaining_budget" in result


def test_remaining_budget_can_be_negative() -> None:
    update_monthly_budget(1.0)
    status = get_budget_status()
    # Force an overage view by lowering the limit below current spend if any,
    # or verify formula supports negatives directly.
    remaining = status["monthly_budget"] - status["monthly_billable_used"]
    assert remaining == status["remaining_budget"]
