PROVIDER_MODEL_MAP = {
    # Fake mode uses the same real model IDs so simulated costs match live pricing.
    "fake": {
        "easy": {
            "selected_tier": "cheap",
            "selected_model": "gpt-4o-mini",
        },
        "medium": {
            "selected_tier": "mid",
            "selected_model": "gpt-4o",
        },
        "hard": {
            "selected_tier": "expert",
            "selected_model": "gpt-4o",
        },
    },
    "deepseek": {
        "easy": {
            "selected_tier": "cheap",
            "selected_model": "deepseek-chat",
        },
        "medium": {
            "selected_tier": "mid",
            "selected_model": "deepseek-chat",
        },
        "hard": {
            "selected_tier": "expert",
            "selected_model": "deepseek-reasoner",
        },
    },
    "openai": {
        "easy": {
            "selected_tier": "cheap",
            "selected_model": "gpt-4o-mini",
        },
        "medium": {
            "selected_tier": "mid",
            "selected_model": "gpt-4o",
        },
        "hard": {
            "selected_tier": "expert",
            "selected_model": "gpt-4o",
        },
    },
}


def choose_model(difficulty: str, provider: str) -> dict:
    provider_map = PROVIDER_MODEL_MAP.get(provider, PROVIDER_MODEL_MAP["fake"])
    model_result = provider_map.get(difficulty, provider_map["medium"])
    return {
        **model_result,
        "provider": provider if provider in PROVIDER_MODEL_MAP else "fake",
    }
