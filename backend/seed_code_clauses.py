import sys
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.db import get_db, init_db, is_postgres, load_code_clauses


def run_seed() -> int:
    init_db()
    with get_db() as con:
        count = load_code_clauses(con)
        db_type = "Supabase Postgres" if is_postgres() else "SQLite"
        print(f"Successfully seeded {count} UAE FLS code clauses into {db_type}.")
        return count


if __name__ == "__main__":
    count = run_seed()
    print(f"Done. Seeded {count} clauses.")
