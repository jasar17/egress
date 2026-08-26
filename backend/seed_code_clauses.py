import json
import sqlite3
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "fls_demo.db"
JSON_PATH_BACKEND = DATA_DIR / "uae_fls_code_clauses_business_occupancy.json"
JSON_PATH_ROOT = BASE_DIR.parent / "seed" / "uae_fls_code_clauses_business_occupancy.json"


def get_json_path() -> Path:
    if JSON_PATH_BACKEND.exists():
        return JSON_PATH_BACKEND
    if JSON_PATH_ROOT.exists():
        return JSON_PATH_ROOT
    raise FileNotFoundError("Could not find uae_fls_code_clauses_business_occupancy.json in backend/data/ or seed/")


def seed_code_clauses(db_path: Path = DB_PATH) -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    json_file = get_json_path()
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    clauses: list[dict[str, Any]] = data.get("clauses", [])
    if not clauses:
        raise ValueError("No clauses found in JSON file.")

    conn = sqlite3.connect(db_path)
    try:
        # Check if legacy table structure exists
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='code_clauses'")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(code_clauses)")
            cols = [col[1] for col in cursor.fetchall()]
            if "clause_id" not in cols:
                print("Migrating legacy code_clauses table...")
                cursor.execute("DROP TABLE code_clauses")

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS code_clauses (
                clause_id TEXT PRIMARY KEY,
                topic TEXT NOT NULL,
                occupancy TEXT NOT NULL,
                requirement_type TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT NOT NULL,
                condition TEXT,
                note TEXT,
                source_table TEXT NOT NULL,
                source_page INTEGER NOT NULL
            )
            """
        )

        cursor.execute("DELETE FROM code_clauses")
        for clause in clauses:
            cursor.execute(
                """
                INSERT OR REPLACE INTO code_clauses (
                    clause_id, topic, occupancy, requirement_type, value, unit, condition, note, source_table, source_page
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    clause.get("clause_id"),
                    clause.get("topic"),
                    clause.get("occupancy"),
                    clause.get("requirement_type"),
                    float(clause.get("value")),
                    clause.get("unit"),
                    clause.get("condition"),
                    clause.get("note"),
                    clause.get("source_table"),
                    int(clause.get("source_page")),
                ),
            )
        conn.commit()
        print(f"Successfully loaded {len(clauses)} code clauses into '{db_path}' from '{json_file.name}'")
        return len(clauses)
    finally:
        conn.close()


if __name__ == "__main__":
    count = seed_code_clauses()
    print(f"Done. Seeded {count} clauses.")
