from openai import OpenAI

from app.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, OPENAI_API_KEY
from app.services.cost_calculator import estimate_input_tokens


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
        # Simulate realistic usage counts for local demos (not billed).
        simulated_input = estimate_input_tokens(prompt)
        simulated_output = max(12, simulated_input // 2)
        return {
            "answer": fake_llm(prompt, selected_model),
            "llm_mode": "fake",
            "input_tokens": simulated_input,
            "output_tokens": simulated_output,
            "total_tokens": simulated_input + simulated_output,
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
