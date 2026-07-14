"""Budget tracking for model routing requests."""

import math
from datetime import datetime, timezone

from app.config import MONTHLY_BUDGET
from app.database import get_connection


def get_current_month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def get_monthly_budget_limit() -> float:
    """Read the admin-configurable monthly budget limit from Postgres."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT value FROM app_settings WHERE key = %s",
                ("monthly_budget_limit",),
            )
            row = cursor.fetchone()

    if row is None:
        return float(MONTHLY_BUDGET)
    return float(row["value"])


def update_monthly_budget(new_limit: float, reset_usage: bool = True) -> dict:
    """
    Persist a new monthly budget limit (single global row) and return status.

    For the demo admin panel, reset_usage=True clears request history so
    billable spend returns to $0.00 and remaining equals the new limit.
    """
    if not isinstance(new_limit, (int, float)) or isinstance(new_limit, bool):
        raise ValueError("Monthly budget limit must be a number.")
    if not math.isfinite(new_limit) or new_limit <= 0:
        raise ValueError("Monthly budget limit must be a finite number greater than zero.")

    with get_connection() as conn:
        with conn.transaction():
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO app_settings (key, value)
                    VALUES (%s, %s)
                    ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
                    """,
                    ("monthly_budget_limit", float(new_limit)),
                )
                if reset_usage:
                    cursor.execute("DELETE FROM request_logs")

    return get_budget_status()


def get_monthly_budget_totals() -> dict:
    current_month = get_current_month()
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    COALESCE(SUM(billable_cost), 0) AS monthly_billable_used,
                    COALESCE(SUM(estimated_cost), 0) AS monthly_estimated_cost
                FROM request_logs
                WHERE to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM') = %s
                """,
                (current_month,),
            )
            row = cursor.fetchone()

    return {
        "current_month": current_month,
        "monthly_billable_used": float(row["monthly_billable_used"] or 0),
        "monthly_estimated_cost": float(row["monthly_estimated_cost"] or 0),
    }


def get_budget_status() -> dict:
    totals = get_monthly_budget_totals()
    monthly_budget = get_monthly_budget_limit()
    # Allow negative remaining to represent real credit overages — never clamp to 0.
    remaining_budget = monthly_budget - totals["monthly_billable_used"]

    if remaining_budget < 0:
        status = "overage"
    elif totals["monthly_billable_used"] >= monthly_budget:
        status = "exceeded"
    elif totals["monthly_billable_used"] >= monthly_budget * 0.8:
        status = "warning"
    else:
        status = "healthy"

    return {
        "monthly_budget": monthly_budget,
        "current_month": totals["current_month"],
        "monthly_billable_used": totals["monthly_billable_used"],
        "monthly_estimated_cost": totals["monthly_estimated_cost"],
        "remaining_budget": remaining_budget,
        "status": status,
    }


def check_budget(estimated_cost: float) -> dict:
    budget_status = get_budget_status()
    remaining_budget = budget_status["remaining_budget"]

    if estimated_cost <= remaining_budget:
        gate = "allowed"
    else:
        gate = "blocked"

    return {
        **budget_status,
        "estimated_cost": estimated_cost,
        "budget_status": gate,
    }
