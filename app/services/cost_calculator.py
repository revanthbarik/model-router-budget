MODEL_PRICING = {
    "fake-cheap-model": {"input": 0.05, "output": 0.10},
    "fake-mid-model": {"input": 0.10, "output": 0.20},
    "fake-expert-model": {"input": 0.20, "output": 0.40},
    "deepseek-chat": {"input": 0.27, "output": 1.10},
    "deepseek-reasoner": {"input": 0.55, "output": 2.19},
    "gpt-4.1-nano": {"input": 0.10, "output": 0.40},
    "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
}


def estimate_cost(prompt: str, selected_tier: str) -> float:
    return estimate_cost_for_model(prompt=prompt, selected_model=None, selected_tier=selected_tier)


def estimate_cost_for_model(
    prompt: str,
    selected_model: str | None,
    selected_tier: str = "mid",
) -> float:
    estimated_input_tokens = max(1, len(prompt.split()) * 2)
    estimated_output_tokens = max(20, estimated_input_tokens // 2)

    if selected_model and selected_model in MODEL_PRICING:
        pricing = MODEL_PRICING[selected_model]
        input_cost = (estimated_input_tokens / 1_000_000) * pricing["input"]
        output_cost = (estimated_output_tokens / 1_000_000) * pricing["output"]
        return round(input_cost + output_cost, 6)

    tier_defaults = {
        "cheap": "fake-cheap-model",
        "mid": "fake-mid-model",
        "expert": "fake-expert-model",
    }
    fallback_model = tier_defaults.get(selected_tier, "fake-mid-model")
    return estimate_cost_for_model(
        prompt=prompt,
        selected_model=fallback_model,
        selected_tier=selected_tier,
    )


def calculate_real_cost(
    selected_model: str,
    input_tokens: int,
    output_tokens: int,
    prompt: str = "",
    selected_tier: str = "mid",
) -> float:
    if input_tokens <= 0 and output_tokens <= 0:
        return estimate_cost(prompt, selected_tier)

    pricing = MODEL_PRICING.get(selected_model)
    if pricing is None:
        return estimate_cost(prompt, selected_tier)

    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    return round(input_cost + output_cost, 6)
