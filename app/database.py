import os
import sqlite3

DB_PATH = "data/model_router.db"
EXTRA_COLUMNS = [
    ("answer", "TEXT DEFAULT ''"),
    ("provider", "TEXT DEFAULT 'fake'"),
    ("llm_mode", "TEXT DEFAULT 'unknown'"),
    ("difficulty_score", "INTEGER DEFAULT 0"),
    ("billable_cost", "REAL DEFAULT 0"),
    ("input_tokens", "INTEGER DEFAULT 0"),
    ("output_tokens", "INTEGER DEFAULT 0"),
    ("total_tokens", "INTEGER DEFAULT 0"),
]


def get_connection():
    os.makedirs("data", exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS request_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt TEXT NOT NULL,
            answer TEXT DEFAULT '',
            difficulty TEXT NOT NULL,
            difficulty_score INTEGER DEFAULT 0,
            selected_tier TEXT NOT NULL,
            provider TEXT DEFAULT 'fake',
            selected_model TEXT NOT NULL,
            estimated_cost REAL NOT NULL,
            billable_cost REAL DEFAULT 0,
            latency_ms REAL NOT NULL,
            budget_status TEXT NOT NULL,
            llm_mode TEXT DEFAULT 'unknown',
            input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0,
            total_tokens INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    for column_name, column_type in EXTRA_COLUMNS:
        try:
            cursor.execute(
                f"ALTER TABLE request_logs ADD COLUMN {column_name} {column_type}"
            )
        except sqlite3.OperationalError as exc:
            if "duplicate column name" not in str(exc).lower():
                raise

    cursor.execute(
        """
        UPDATE request_logs
        SET billable_cost = estimated_cost
        WHERE llm_mode IN ('openai', 'deepseek')
          AND COALESCE(billable_cost, 0) = 0
        """
    )

    conn.commit()
    conn.close()
