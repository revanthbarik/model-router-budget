from app.services.difficulty_estimator import estimate_difficulty


def test_estimate_difficulty_returns_expected_fields() -> None:
    result = estimate_difficulty("Explain this API in simple steps")

    assert result["difficulty"] in {"easy", "medium", "hard"}
    assert isinstance(result["score"], int)
    assert isinstance(result["reasons"], list)
