from __future__ import annotations

import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator, Optional

try:
    import psycopg2
    import psycopg2.extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL") or os.getenv("SUPABASE_DATABASE_URL")
SQLITE_DB_PATH = Path(os.getenv("FLS_DATABASE_PATH", DATA_DIR / "fls_demo.db"))


def is_postgres() -> bool:
    return bool(DATABASE_URL and (DATABASE_URL.startswith("postgres://") or DATABASE_URL.startswith("postgresql://")))


def get_postgres_url() -> str:
    url = DATABASE_URL or ""
    # Render and Supabase sometimes provide postgres:// which psycopg2 requires as postgresql://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


class PostgresCursorWrapper:
    """
    Wraps a psycopg2 cursor to provide an interface compatible with sqlite3,
    converting '?' parameter placeholders to '%s' and handling SQLite-specific idioms.
    """
    def __init__(self, raw_cursor):
        self.cursor = raw_cursor

    def execute(self, query: str, params: Any = None):
        # Convert SQLite '?' placeholders to Postgres '%s'
        if params is not None:
            query = query.replace("?", "%s")
        # Handle SQLite 'INSERT OR REPLACE' in Postgres
        if "INSERT OR REPLACE INTO code_clauses" in query:
            query = """
            INSERT INTO code_clauses (
                clause_id, topic, occupancy, requirement_type, value, unit, condition, note, source_table, source_page
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (clause_id) DO UPDATE SET
                topic = EXCLUDED.topic,
                occupancy = EXCLUDED.occupancy,
                requirement_type = EXCLUDED.requirement_type,
                value = EXCLUDED.value,
                unit = EXCLUDED.unit,
                condition = EXCLUDED.condition,
                note = EXCLUDED.note,
                source_table = EXCLUDED.source_table,
                source_page = EXCLUDED.source_page
            """
        elif "INSERT OR REPLACE INTO projects" in query:
            query = """
            INSERT INTO projects (id, name, client_name, created_at, occupancy_type, sprinklered)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                client_name = EXCLUDED.client_name,
                occupancy_type = EXCLUDED.occupancy_type,
                sprinklered = EXCLUDED.sprinklered
            """
        elif "INSERT OR REPLACE INTO drawings" in query:
            query = """
            INSERT INTO drawings (id, project_id, file_url, file_type, occupancy_type, scale, status, created_at, sprinklered, page_index, floor_name)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                file_url = EXCLUDED.file_url,
                file_type = EXCLUDED.file_type,
                occupancy_type = EXCLUDED.occupancy_type,
                scale = EXCLUDED.scale,
                status = EXCLUDED.status,
                sprinklered = EXCLUDED.sprinklered,
                page_index = EXCLUDED.page_index,
                floor_name = EXCLUDED.floor_name
            """

        if params is not None:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)
        return self

    def executemany(self, query: str, seq_of_params: Any):
        if seq_of_params:
            query = query.replace("?", "%s")
        self.cursor.executemany(query, seq_of_params)
        return self

    def executescript(self, script: str):
        self.cursor.execute(script)
        return self

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()


class PostgresConnectionWrapper:
    def __init__(self, raw_conn):
        self.conn = raw_conn

    def execute(self, query: str, params: Any = None):
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        wrapper = PostgresCursorWrapper(cursor)
        return wrapper.execute(query, params)

    def executescript(self, script: str):
        cursor = self.conn.cursor()
        cursor.execute(script)
        return cursor

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()


@contextmanager
def get_db() -> Generator[Any, None, None]:
    if is_postgres():
        if not PSYCOPG2_AVAILABLE:
            raise RuntimeError("psycopg2 is required to connect to Postgres. Run: pip install psycopg2-binary")
        raw_conn = psycopg2.connect(get_postgres_url())
        conn_wrapper = PostgresConnectionWrapper(raw_conn)
        try:
            yield conn_wrapper
            conn_wrapper.commit()
        except Exception:
            raw_conn.rollback()
            raise
        finally:
            conn_wrapper.close()
    else:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(SQLITE_DB_PATH)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_code_clauses(con: Any) -> int:
    json_path = DATA_DIR / "uae_fls_code_clauses_business_occupancy.json"
    if not json_path.exists():
        json_path = BASE_DIR.parent / "seed" / "uae_fls_code_clauses_business_occupancy.json"
    if not json_path.exists():
        return 0
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    clauses = data.get("clauses", [])
    con.execute("DELETE FROM code_clauses")
    for clause in clauses:
        con.execute(
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
    return len(clauses)


def init_db() -> None:
    with get_db() as con:
        if is_postgres():
            con.executescript(
                """
                CREATE TABLE IF NOT EXISTS projects (
                  id TEXT PRIMARY KEY, name TEXT NOT NULL, client_name TEXT NOT NULL, created_at TEXT NOT NULL,
                  occupancy_type TEXT NOT NULL DEFAULT 'Business - Regular office areas',
                  sprinklered INTEGER NOT NULL DEFAULT 1
                );
                CREATE TABLE IF NOT EXISTS drawings (
                  id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE, file_url TEXT,
                  file_type TEXT NOT NULL, occupancy_type TEXT NOT NULL DEFAULT 'Business - Regular office areas', scale REAL NOT NULL,
                  status TEXT NOT NULL, created_at TEXT NOT NULL,
                  sprinklered INTEGER NOT NULL DEFAULT 1,
                  page_index INTEGER NOT NULL DEFAULT 0,
                  floor_name TEXT DEFAULT 'Architectural Floor Plan'
                );
                CREATE TABLE IF NOT EXISTS extracted_elements (
                  id TEXT PRIMARY KEY, drawing_id TEXT NOT NULL REFERENCES drawings(id) ON DELETE CASCADE, type TEXT NOT NULL,
                  name TEXT, geometry TEXT NOT NULL, properties TEXT NOT NULL DEFAULT '{}'
                );
                CREATE TABLE IF NOT EXISTS violations (
                  id TEXT PRIMARY KEY, drawing_id TEXT NOT NULL REFERENCES drawings(id) ON DELETE CASCADE, type TEXT NOT NULL,
                  related_element_id TEXT, clause_ref TEXT NOT NULL, measured_value REAL NOT NULL,
                  measured_unit TEXT NOT NULL, limit_value REAL NOT NULL, limit_unit TEXT NOT NULL,
                  severity TEXT NOT NULL, status TEXT NOT NULL, note TEXT, geometry TEXT, title TEXT NOT NULL,
                  detail TEXT NOT NULL
                );
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
                );
                """
            )
        else:
            con.executescript(
                """
                CREATE TABLE IF NOT EXISTS projects (
                  id TEXT PRIMARY KEY, name TEXT NOT NULL, client_name TEXT NOT NULL, created_at TEXT NOT NULL,
                  occupancy_type TEXT NOT NULL DEFAULT 'Business - Regular office areas',
                  sprinklered INTEGER NOT NULL DEFAULT 1
                );
                CREATE TABLE IF NOT EXISTS drawings (
                  id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id), file_url TEXT,
                  file_type TEXT NOT NULL, occupancy_type TEXT NOT NULL DEFAULT 'Business - Regular office areas', scale REAL NOT NULL,
                  status TEXT NOT NULL, created_at TEXT NOT NULL,
                  sprinklered INTEGER NOT NULL DEFAULT 1,
                  page_index INTEGER NOT NULL DEFAULT 0,
                  floor_name TEXT DEFAULT 'Architectural Floor Plan'
                );
                CREATE TABLE IF NOT EXISTS extracted_elements (
                  id TEXT PRIMARY KEY, drawing_id TEXT NOT NULL REFERENCES drawings(id), type TEXT NOT NULL,
                  name TEXT, geometry TEXT NOT NULL, properties TEXT NOT NULL DEFAULT '{}'
                );
                CREATE TABLE IF NOT EXISTS violations (
                  id TEXT PRIMARY KEY, drawing_id TEXT NOT NULL REFERENCES drawings(id), type TEXT NOT NULL,
                  related_element_id TEXT, clause_ref TEXT NOT NULL, measured_value REAL NOT NULL,
                  measured_unit TEXT NOT NULL, limit_value REAL NOT NULL, limit_unit TEXT NOT NULL,
                  severity TEXT NOT NULL, status TEXT NOT NULL, note TEXT, geometry TEXT, title TEXT NOT NULL,
                  detail TEXT NOT NULL
                );
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
                );
                """
            )

        load_code_clauses(con)
