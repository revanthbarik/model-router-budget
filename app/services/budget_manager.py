"""Budget tracking for model routing requests."""

from datetime import datetime, timezone

from app.config import MONTHLY_BUDGET
from app.database import get_connection


def get_current_month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def get_monthly_budget_totals() -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    current_month = get_current_month()

    cursor.execute(
        """
        SELECT
            COALESCE(SUM(billable_cost), 0) AS monthly_billable_used,
            COALESCE(SUM(estimated_cost), 0) AS monthly_estimated_cost
        FROM request_logs
        WHERE strftime('%Y-%m', created_at) = ?
        """
        ,
        (current_month,),
    )
    row = cursor.fetchone()
    conn.close()

    return {
        "current_month": current_month,
        "monthly_billable_used": round(float(row["monthly_billable_used"] or 0), 6),
        "monthly_estimated_cost": round(float(row["monthly_estimated_cost"] or 0), 6),
    }


def get_budget_status() -> dict:
    totals = get_monthly_budget_totals()
    remaining_budget = max(MONTHLY_BUDGET - totals["monthly_billable_used"], 0.0)

    if totals["monthly_billable_used"] >= MONTHLY_BUDGET:
        status = "exceeded"
    elif totals["monthly_billable_used"] >= MONTHLY_BUDGET * 0.8:
        status = "warning"
    else:
        status = "healthy"

    return {
        "monthly_budget": MONTHLY_BUDGET,
        "current_month": totals["current_month"],
        "monthly_billable_used": totals["monthly_billable_used"],
        "monthly_estimated_cost": totals["monthly_estimated_cost"],
        "remaining_budget": round(remaining_budget, 6),
        "status": status,
    }


def check_budget(estimated_cost: float) -> dict:
    budget_status = get_budget_status()
    remaining_budget = budget_status["remaining_budget"]

    if estimated_cost <= remaining_budget:
        status = "allowed"
    else:
        status = "blocked"

    return {
        **budget_status,
        "estimated_cost": round(estimated_cost, 6),
        "budget_status": status,
    }
