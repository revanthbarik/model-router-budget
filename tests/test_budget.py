from app.services.budget_manager import check_budget


def test_check_budget_returns_true() -> None:
    assert check_budget() is True
