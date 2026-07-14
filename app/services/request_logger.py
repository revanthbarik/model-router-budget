from app.database import get_connection
from app.services.budget_manager import get_current_month


def log_request(
    prompt: str,
    answer: str,
    provider: str,
    difficulty: str,
    difficulty_score: int,
    selected_tier: str,
    selected_model: str,
    estimated_cost: float,
    billable_cost: float,
    latency_ms: float,
    budget_status: str,
    llm_mode: str,
    input_tokens: int,
    output_tokens: int,
    total_tokens: int,
) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO request_logs (
                    prompt,
                    answer,
                    provider,
                    difficulty,
                    difficulty_score,
                    selected_tier,
                    selected_model,
                    estimated_cost,
                    billable_cost,
                    latency_ms,
                    budget_status,
                    llm_mode,
                    input_tokens,
                    output_tokens,
                    total_tokens
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                RETURNING *
                """,
                (
                    prompt,
                    answer,
                    provider,
                    difficulty,
                    difficulty_score,
                    selected_tier,
                    selected_model,
                    estimated_cost,
                    billable_cost,
                    latency_ms,
                    budget_status,
                    llm_mode,
                    input_tokens,
                    output_tokens,
                    total_tokens,
                ),
            )
            row = cursor.fetchone()
        conn.commit()

    return dict(row)


def get_logs() -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    prompt,
                    answer,
                    provider,
                    llm_mode,
                    selected_model,
                    selected_tier,
                    difficulty,
                    difficulty_score,
                    estimated_cost,
                    billable_cost,
                    latency_ms,
                    budget_status,
                    input_tokens,
                    output_tokens,
                    total_tokens,
                    created_at
                FROM request_logs
                ORDER BY id DESC
                LIMIT 50
                """
            )
            rows = cursor.fetchall()

    return [dict(row) for row in rows]


def get_metrics() -> dict:
    current_month = get_current_month()

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS count FROM request_logs")
            total_requests = cursor.fetchone()["count"]

            if total_requests == 0:
                return {
                    "total_requests": 0,
                    "total_cost": 0.0,
                    "average_latency_ms": 0.0,
                    "fake_requests": 0,
                    "deepseek_requests": 0,
                    "openai_requests": 0,
                    "fallback_requests": 0,
                    "blocked_requests": 0,
                    "current_month": current_month,
                    "monthly_requests": 0,
                    "monthly_billable_cost": 0.0,
                    "monthly_estimated_cost": 0.0,
                    "monthly_openai_requests": 0,
                    "monthly_deepseek_requests": 0,
                    "monthly_fake_requests": 0,
                    "monthly_blocked_requests": 0,
                    "model_usage": {},
                    "difficulty_usage": {},
                }

            cursor.execute(
                """
                SELECT COALESCE(SUM(billable_cost), 0) AS total_cost
                FROM request_logs
                """
            )
            total_cost = cursor.fetchone()["total_cost"]

            cursor.execute(
                "SELECT COALESCE(AVG(latency_ms), 0) AS average_latency FROM request_logs"
            )
            average_latency = cursor.fetchone()["average_latency"]

            cursor.execute(
                """
                SELECT COUNT(*) AS count
                FROM request_logs
                WHERE provider = 'fake' AND budget_status = 'allowed'
                """
            )
            fake_requests = cursor.fetchone()["count"]

            cursor.execute(
                """
                SELECT COUNT(*) AS count
                FROM request_logs
                WHERE provider = 'deepseek' AND budget_status = 'allowed'
                """
            )
            deepseek_requests = cursor.fetchone()["count"]

            cursor.execute(
                """
                SELECT COUNT(*) AS count
                FROM request_logs
                WHERE provider = 'openai' AND budget_status = 'allowed'
                """
            )
            openai_requests = cursor.fetchone()["count"]

            cursor.execute(
                """
                SELECT COUNT(*) AS count
                FROM request_logs
                WHERE llm_mode = 'fallback_fake'
                """
            )
            fallback_requests = cursor.fetchone()["count"]

            cursor.execute(
                """
                SELECT COUNT(*) AS count
                FROM request_logs
                WHERE budget_status = 'blocked'
                """
            )
            blocked_requests = cursor.fetchone()["count"]

            cursor.execute(
                """
                SELECT
                    COUNT(*) AS monthly_requests,
                    COALESCE(SUM(billable_cost), 0) AS monthly_billable_cost,
                    COALESCE(SUM(estimated_cost), 0) AS monthly_estimated_cost
                FROM request_logs
                WHERE to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM') = %s
                """,
                (current_month,),
            )
            monthly_totals = cursor.fetchone()

            cursor.execute(
                """
                SELECT COUNT(*) AS count
                FROM request_logs
                WHERE to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM') = %s
                  AND provider = 'openai'
                  AND budget_status = 'allowed'
                """,
                (current_month,),
            )
            monthly_openai_requests = cursor.fetchone()["count"]

            cursor.execute(
                """
                SELECT COUNT(*) AS count
                FROM request_logs
                WHERE to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM') = %s
                  AND provider = 'deepseek'
                  AND budget_status = 'allowed'
                """,
                (current_month,),
            )
            monthly_deepseek_requests = cursor.fetchone()["count"]

            cursor.execute(
                """
                SELECT COUNT(*) AS count
                FROM request_logs
                WHERE to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM') = %s
                  AND provider = 'fake'
                  AND budget_status = 'allowed'
                """,
                (current_month,),
            )
            monthly_fake_requests = cursor.fetchone()["count"]

            cursor.execute(
                """
                SELECT COUNT(*) AS count
                FROM request_logs
                WHERE to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM') = %s
                  AND budget_status = 'blocked'
                """,
                (current_month,),
            )
            monthly_blocked_requests = cursor.fetchone()["count"]

            cursor.execute(
                """
                SELECT selected_model, COUNT(*) AS count
                FROM request_logs
                GROUP BY selected_model
                """
            )
            model_usage = {
                row["selected_model"]: row["count"] for row in cursor.fetchall()
            }

            cursor.execute(
                """
                SELECT difficulty, COUNT(*) AS count
                FROM request_logs
                GROUP BY difficulty
                """
            )
            difficulty_usage = {
                row["difficulty"]: row["count"] for row in cursor.fetchall()
            }

    return {
        "total_requests": total_requests,
        "total_cost": round(float(total_cost), 6),
        "average_latency_ms": round(float(average_latency), 2),
        "fake_requests": fake_requests,
        "deepseek_requests": deepseek_requests,
        "openai_requests": openai_requests,
        "fallback_requests": fallback_requests,
        "blocked_requests": blocked_requests,
        "current_month": current_month,
        "monthly_requests": monthly_totals["monthly_requests"],
        "monthly_billable_cost": round(
            float(monthly_totals["monthly_billable_cost"] or 0), 6
        ),
        "monthly_estimated_cost": round(
            float(monthly_totals["monthly_estimated_cost"] or 0), 6
        ),
        "monthly_openai_requests": monthly_openai_requests,
        "monthly_deepseek_requests": monthly_deepseek_requests,
        "monthly_fake_requests": monthly_fake_requests,
        "monthly_blocked_requests": monthly_blocked_requests,
        "model_usage": model_usage,
        "difficulty_usage": difficulty_usage,
    }
