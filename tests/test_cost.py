from app.schemas.router_schema import RouteRequest
from app.services.cost_calculator import (
    MODEL_PRICING,
    calculate_cost_breakdown,
    estimate_input_cost_for_model,
    estimate_input_tokens,
)


def test_force_run_defaults_to_false() -> None:
    request = RouteRequest(prompt="hello")
    assert request.force_run is False


def test_pricing_table_contains_supported_models_only() -> None:
    assert set(MODEL_PRICING.keys()) == {
        "gpt-4o-mini",
        "gpt-4o",
        "deepseek-chat",
        "deepseek-reasoner",
    }


def test_pricing_calculations_for_all_models() -> None:
    cases = [
        ("gpt-4o-mini", 1_000_000, 500_000, 0.15, 0.30),
        ("gpt-4o", 1_000_000, 100_000, 2.50, 1.00),
        ("deepseek-chat", 2_000_000, 1_000_000, 0.28, 0.28),
        ("deepseek-reasoner", 100_000, 50_000, 0.055, 0.1095),
    ]
    for model, inp, out, expected_in, expected_out in cases:
        costs = calculate_cost_breakdown(model, inp, out)
        assert abs(costs["input_cost"] - expected_in) < 1e-12
        assert abs(costs["output_cost"] - expected_out) < 1e-12
        assert abs(costs["total_cost"] - (expected_in + expected_out)) < 1e-12


def test_pre_call_estimate_uses_input_only() -> None:
    prompt = "one two three four"
    tokens = estimate_input_tokens(prompt)
    assert tokens == 8
    estimated = estimate_input_cost_for_model(prompt, "gpt-4o-mini")
    expected = (8 / 1_000_000) * 0.15
    assert estimated == expected
