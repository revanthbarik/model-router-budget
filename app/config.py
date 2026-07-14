import os

from dotenv import load_dotenv

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
USE_REAL_LLM = os.getenv("USE_REAL_LLM", "false").lower() == "true"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
MONTHLY_BUDGET = float(os.getenv("MONTHLY_BUDGET", "5.00"))
MAX_PROMPT_CHARS = int(os.getenv("MAX_PROMPT_CHARS", "4000"))


def _normalize_database_url(url: str) -> str:
    cleaned = url.strip().strip('"').strip("'")
    # libpq/psycopg prefer the postgresql:// scheme
    if cleaned.startswith("postgres://"):
        cleaned = "postgresql://" + cleaned[len("postgres://") :]
    return cleaned


DATABASE_URL = _normalize_database_url(os.getenv("DATABASE_URL", ""))


def get_llm_provider() -> str:
    provider = os.getenv("LLM_PROVIDER")
    if provider:
        provider = provider.lower().strip()
        if provider in {"fake", "deepseek", "openai"}:
            return provider

    if USE_REAL_LLM:
        return "deepseek"

    return "fake"
