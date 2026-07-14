"""Reset Postgres tables to a blank slate (0 requests, $0.00 billable used)."""

from app.database import reset_db


def main() -> None:
    reset_db()
    print("Database reset complete (Postgres).")
    print("  - request_logs dropped and recreated")
    print("  - app_settings reseeded")
    print("  - billable used: $0.00")
    print("  - request count: 0")
    print("  - monthly budget comes from MONTHLY_BUDGET in .env (default $5.00)")


if __name__ == "__main__":
    main()
