from openai import OpenAI

from app.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, OPENAI_API_KEY


def fake_llm(prompt: str, selected_model: str) -> str:
    return (
        f"This is a fake response from {selected_model}. "
        f"Received prompt: {prompt}"
    )


def _extract_usage(response) -> tuple[int, int, int]:
    usage = getattr(response, "usage", None)
    if usage is None:
        return 0, 0, 0

    input_tokens = getattr(usage, "prompt_tokens", None)
    if input_tokens is None:
        input_tokens = getattr(usage, "input_tokens", 0) or 0

    output_tokens = getattr(usage, "completion_tokens", None)
    if output_tokens is None:
        output_tokens = getattr(usage, "output_tokens", 0) or 0

    total_tokens = getattr(usage, "total_tokens", None)
    if total_tokens is None:
        total_tokens = int(input_tokens) + int(output_tokens)

    return int(input_tokens or 0), int(output_tokens or 0), int(total_tokens or 0)


def call_deepseek_llm(prompt: str, selected_model: str) -> dict:
    client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
    )

    response = client.chat.completions.create(
        model=selected_model,
        messages=[
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": prompt},
        ],
    )

    answer = response.choices[0].message.content or ""
    input_tokens, output_tokens, total_tokens = _extract_usage(response)

    return {
        "answer": answer,
        "llm_mode": "deepseek",
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
    }


def call_openai_llm(prompt: str, selected_model: str) -> dict:
    client = OpenAI(api_key=OPENAI_API_KEY)

    response = client.chat.completions.create(
        model=selected_model,
        messages=[
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": prompt},
        ],
    )

    answer = response.choices[0].message.content or ""
    input_tokens, output_tokens, total_tokens = _extract_usage(response)

    return {
        "answer": answer,
        "llm_mode": "openai",
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
    }


def fallback_fake_response(
    prompt: str,
    selected_model: str,
    provider: str,
    reason: str,
) -> dict:
    return {
        "answer": (
            f"[{provider} unavailable - using fake fallback: {reason}] "
            f"{fake_llm(prompt, selected_model)}"
        ),
        "llm_mode": "fallback_fake",
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
    }


def call_llm(prompt: str, selected_model: str, provider: str) -> dict:
    if provider == "fake":
        estimated_input_tokens = max(1, len(prompt.split()) * 2)
        estimated_output_tokens = max(12, estimated_input_tokens // 2)
        return {
            "answer": fake_llm(prompt, selected_model),
            "llm_mode": "fake",
            "input_tokens": estimated_input_tokens,
            "output_tokens": estimated_output_tokens,
            "total_tokens": estimated_input_tokens + estimated_output_tokens,
        }

    if provider == "deepseek":
        if not DEEPSEEK_API_KEY:
            return fallback_fake_response(
                prompt=prompt,
                selected_model=selected_model,
                provider="DeepSeek",
                reason="missing DEEPSEEK_API_KEY",
            )
        try:
            return call_deepseek_llm(prompt, selected_model)
        except Exception as exc:
            return fallback_fake_response(
                prompt=prompt,
                selected_model=selected_model,
                provider="DeepSeek",
                reason=str(exc),
            )

    if provider == "openai":
        if not OPENAI_API_KEY:
            return fallback_fake_response(
                prompt=prompt,
                selected_model=selected_model,
                provider="OpenAI",
                reason="missing OPENAI_API_KEY",
            )
        try:
            return call_openai_llm(prompt, selected_model)
        except Exception as exc:
            return fallback_fake_response(
                prompt=prompt,
                selected_model=selected_model,
                provider="OpenAI",
                reason=str(exc),
            )

    return fallback_fake_response(
        prompt=prompt,
        selected_model=selected_model,
        provider="Unknown provider",
        reason="unsupported provider",
    )
