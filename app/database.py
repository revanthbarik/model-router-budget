"""PostgreSQL database access for Model Router with Budgets."""

from threading import Lock

import psycopg
from psycopg.rows import dict_row

from app.config import DATABASE_URL, MONTHLY_BUDGET

_init_lock = Lock()
_db_initialized = False


def get_connection():
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not set. Add a Postgres connection string to your "
            ".env file (local) or Vercel Environment Variables (production)."
        )
    ensure_db()
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def ensure_db() -> None:
    """Idempotent schema bootstrap. Safe to call from request handlers."""
    global _db_initialized
    if _db_initialized:
        return
    with _init_lock:
        if _db_initialized:
            return
        init_db()
        _db_initialized = True


def init_db():
    """Create request_logs + app_settings schema if missing."""
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not set. Add a Postgres connection string to your "
            ".env file (local) or Vercel Environment Variables (production)."
        )
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS request_logs (
                    id BIGSERIAL PRIMARY KEY,
                    prompt TEXT NOT NULL,
                    answer TEXT DEFAULT '',
                    difficulty TEXT NOT NULL,
                    difficulty_score INTEGER DEFAULT 0,
                    selected_tier TEXT NOT NULL,
                    provider TEXT DEFAULT 'fake',
                    selected_model TEXT NOT NULL,
                    estimated_cost DOUBLE PRECISION NOT NULL,
                    billable_cost DOUBLE PRECISION DEFAULT 0,
                    latency_ms DOUBLE PRECISION NOT NULL,
                    budget_status TEXT NOT NULL,
                    llm_mode TEXT DEFAULT 'unknown',
                    input_tokens INTEGER DEFAULT 0,
                    output_tokens INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value DOUBLE PRECISION NOT NULL
                )
                """
            )

            cursor.execute(
                "SELECT value FROM app_settings WHERE key = %s",
                ("monthly_budget_limit",),
            )
            if cursor.fetchone() is None:
                cursor.execute(
                    """
                    INSERT INTO app_settings (key, value)
                    VALUES (%s, %s)
                    """,
                    ("monthly_budget_limit", float(MONTHLY_BUDGET)),
                )

        conn.commit()


def reset_db():
    """
    Drop existing tables and recreate a blank schema.

    After reset: 0 request logs, $0.00 billable used, budget limit reseeds from env.
    """
    global _db_initialized
    with _init_lock:
        _db_initialized = False
        with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
            with conn.cursor() as cursor:
                cursor.execute("DROP TABLE IF EXISTS request_logs")
                cursor.execute("DROP TABLE IF EXISTS app_settings")
            conn.commit()
        init_db()
        _db_initialized = True


def probe_database() -> dict:
    """Lightweight readiness check used by /health."""
    try:
        ensure_db()
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 AS ok")
                cursor.fetchone()
        return {"database": "ready", "error": None}
    except Exception as exc:  # noqa: BLE001
        return {"database": "unavailable", "error": str(exc)}
