"""Model pricing and cost estimation (USD per 1M tokens)."""

MODEL_PRICING = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "deepseek-chat": {"input": 0.14, "output": 0.28},
    "deepseek-reasoner": {"input": 0.55, "output": 2.19},
}


def estimate_input_tokens(prompt: str) -> int:
    """Deterministic pre-call input token estimate."""
    return max(1, len(prompt.split()) * 2)


def get_model_pricing(selected_model: str) -> dict:
    if selected_model not in MODEL_PRICING:
        raise ValueError(f"Unsupported model pricing for '{selected_model}'.")
    return MODEL_PRICING[selected_model]


def estimate_input_cost_for_model(
    prompt: str,
    selected_model: str,
    selected_tier: str = "mid",
) -> float:
    """
    Pre-call budget gate: only estimated *input* cost (full float precision).
    """
    del selected_tier  # retained for call-site compatibility
    input_tokens = estimate_input_tokens(prompt)
    pricing = get_model_pricing(selected_model)
    return (input_tokens / 1_000_000) * pricing["input"]


def estimate_cost_for_model(
    prompt: str,
    selected_model: str | None,
    selected_tier: str = "mid",
) -> float:
    """Backward-compatible alias for budget gating (input-only estimate)."""
    if not selected_model:
        selected_model = "gpt-4o"
    return estimate_input_cost_for_model(
        prompt=prompt,
        selected_model=selected_model,
        selected_tier=selected_tier,
    )


def estimate_cost(prompt: str, selected_tier: str) -> float:
    tier_models = {"cheap": "gpt-4o-mini", "mid": "gpt-4o", "expert": "gpt-4o"}
    return estimate_input_cost_for_model(
        prompt=prompt,
        selected_model=tier_models.get(selected_tier, "gpt-4o"),
        selected_tier=selected_tier,
    )


def calculate_cost_breakdown(
    selected_model: str,
    input_tokens: int,
    output_tokens: int,
) -> dict:
    """
    True post-call costs from actual token usage.
    Values are left unrounded for accurate budget deduction.
    """
    pricing = get_model_pricing(selected_model)
    safe_input = max(0, int(input_tokens))
    safe_output = max(0, int(output_tokens))
    input_cost = (safe_input / 1_000_000) * pricing["input"]
    output_cost = (safe_output / 1_000_000) * pricing["output"]
    return {
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": input_cost + output_cost,
    }


def calculate_real_cost(
    selected_model: str,
    input_tokens: int,
    output_tokens: int,
    prompt: str = "",
    selected_tier: str = "mid",
) -> float:
    """
    Post-call billable total from actual provider usage tokens.
    Falls back to input-only estimate only when usage is missing.
    """
    if input_tokens <= 0 and output_tokens <= 0:
        return estimate_input_cost_for_model(
            prompt=prompt,
            selected_model=selected_model,
            selected_tier=selected_tier,
        )
    return calculate_cost_breakdown(selected_model, input_tokens, output_tokens)[
        "total_cost"
    ]
