from app.services.difficulty_estimator import estimate_difficulty


def test_estimate_difficulty_returns_placeholder_value() -> None:
    assert estimate_difficulty("Hello world") == "unknown"
