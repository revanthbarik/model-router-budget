PROVIDER_MODEL_MAP = {
    "fake": {
        "easy": {
            "selected_tier": "cheap",
            "selected_model": "fake-cheap-model",
        },
        "medium": {
            "selected_tier": "mid",
            "selected_model": "fake-mid-model",
        },
        "hard": {
            "selected_tier": "expert",
            "selected_model": "fake-expert-model",
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
            "selected_model": "gpt-4.1-nano",
        },
        "medium": {
            "selected_tier": "mid",
            "selected_model": "gpt-4.1-mini",
        },
        "hard": {
            "selected_tier": "expert",
            "selected_model": "gpt-4.1-mini",
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
