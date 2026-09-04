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

try:
    from dotenv import load_dotenv
    load_dotenv()
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
SQLITE_DB_PATH = Path(os.getenv("FLS_DATABASE_PATH", DATA_DIR / "fls_demo.db"))
DEFAULT_SUPABASE_URL = "postgresql://postgres.xtppmnmpunfflnxrfinb:a%26WHy9%25K48Yas3M@aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres"


def get_raw_db_url() -> Optional[str]:
    if os.getenv("USE_LOCAL_SQLITE") == "1" or os.getenv("DATABASE_URL") == "sqlite":
        return None
    return os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL") or DEFAULT_SUPABASE_URL


def is_postgres(con: Any = None) -> bool:
    if con is not None:
        return isinstance(con, PostgresConnectionWrapper)
    url = get_raw_db_url()
    return bool(url and (url.startswith("postgres://") or url.startswith("postgresql://")))


def get_postgres_url() -> str:
    url = get_raw_db_url() or ""
    # Render and Supabase often provide postgres:// which psycopg2 requires as postgresql://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


import re

class PostgresCursorWrapper:
    """
    Wraps a psycopg2 cursor to provide an interface compatible with sqlite3,
    converting '?' parameter placeholders to '%s' and handling SQLite-specific idioms.
    """
    def __init__(self, raw_cursor):
        self.cursor = raw_cursor

    def execute(self, query: str, params: Any = None):
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
            INSERT INTO drawings (id, project_id, file_url, file_type, occupancy_type, scale, status, created_at, sprinklered, page_index, floor_name, document_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                file_url = EXCLUDED.file_url,
                file_type = EXCLUDED.file_type,
                occupancy_type = EXCLUDED.occupancy_type,
                scale = EXCLUDED.scale,
                status = EXCLUDED.status,
                sprinklered = EXCLUDED.sprinklered,
                page_index = EXCLUDED.page_index,
                floor_name = EXCLUDED.floor_name,
                document_type = EXCLUDED.document_type
            """
        elif "INSERT OR REPLACE INTO drawing_files" in query:
            query = """
            INSERT INTO drawing_files (drawing_id, filename, file_type, file_bytes, created_at)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (drawing_id) DO UPDATE SET
                filename = EXCLUDED.filename,
                file_type = EXCLUDED.file_type,
                file_bytes = EXCLUDED.file_bytes,
                created_at = EXCLUDED.created_at
            """
        elif "INSERT OR REPLACE INTO device_room_links" in query:
            query = """
            INSERT INTO device_room_links (
                id, project_id, device_element_id, device_drawing_id, device_tag,
                device_type, room_element_id, room_drawing_id, room_name, status, x_m, y_m, svg_x, svg_y, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                room_element_id = EXCLUDED.room_element_id,
                room_drawing_id = EXCLUDED.room_drawing_id,
                room_name = EXCLUDED.room_name,
                status = EXCLUDED.status,
                x_m = EXCLUDED.x_m,
                y_m = EXCLUDED.y_m,
                svg_x = EXCLUDED.svg_x,
                svg_y = EXCLUDED.svg_y
            """

        # Convert parameter placeholders from SQLite '?' to Postgres '%s'
        if params is not None:
            if isinstance(params, dict):
                query = re.sub(r':([a-zA-Z_][a-zA-Z0-9_]*)', r'%(\1)s', query)
            elif "?" in query:
                # Escape existing literal '%' characters (e.g. LIKE 'pattern%') before converting '?' to '%s'
                query = query.replace("%", "%%").replace("?", "%s")

        if params is not None:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)
        return self

    def executemany(self, query: str, seq_of_params: Any):
        if seq_of_params:
            if "?" in query:
                query = query.replace("%", "%%").replace("?", "%s")
        self.cursor.executemany(query, seq_of_params)
        return self

    def executescript(self, script: str):
        self.cursor.execute(script)
        return self

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()

    def fetchmany(self, size=None):
        return self.cursor.fetchmany(size) if size is not None else self.cursor.fetchmany()

    def close(self):
        self.cursor.close()

    def __iter__(self):
        return iter(self.cursor)

    @property
    def rowcount(self):
        return self.cursor.rowcount

    @property
    def description(self):
        return self.cursor.description


class PostgresConnectionWrapper:
    def __init__(self, raw_conn):
        self.conn = raw_conn

    def cursor(self):
        raw_cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        return PostgresCursorWrapper(raw_cur)

    def execute(self, query: str, params: Any = None):
        cursor = self.cursor()
        return cursor.execute(query, params)

    def executescript(self, script: str):
        cursor = self.conn.cursor()
        cursor.execute(script)
        return cursor

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()


@contextmanager
def get_db() -> Generator[Any, None, None]:
    if is_postgres():
        if PSYCOPG2_AVAILABLE:
            raw_conn = None
            try:
                raw_conn = psycopg2.connect(get_postgres_url(), connect_timeout=3)
            except Exception as e:
                import logging
                logging.getLogger("uvicorn").warning(f"Postgres connection failed ({e}). Falling back to local SQLite.")

            if raw_conn is not None:
                conn_wrapper = PostgresConnectionWrapper(raw_conn)
                try:
                    yield conn_wrapper
                    conn_wrapper.commit()
                except Exception:
                    raw_conn.rollback()
                    raise
                finally:
                    conn_wrapper.close()
                return
        else:
            import logging
            logging.getLogger("uvicorn").warning("psycopg2 is not available. Falling back to local SQLite.")

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
        if is_postgres(con):
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
                  floor_name TEXT DEFAULT 'Architectural Floor Plan',
                  document_type TEXT NOT NULL DEFAULT 'architectural'
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
                CREATE TABLE IF NOT EXISTS drawing_files (
                  drawing_id TEXT PRIMARY KEY,
                  filename TEXT NOT NULL,
                  file_type TEXT NOT NULL,
                  file_bytes BYTEA NOT NULL,
                  created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS device_room_links (
                  id TEXT PRIMARY KEY,
                  project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                  device_element_id TEXT NOT NULL REFERENCES extracted_elements(id) ON DELETE CASCADE,
                  device_drawing_id TEXT NOT NULL REFERENCES drawings(id) ON DELETE CASCADE,
                  device_tag TEXT,
                  device_type TEXT NOT NULL,
                  room_element_id TEXT REFERENCES extracted_elements(id) ON DELETE SET NULL,
                  room_drawing_id TEXT REFERENCES drawings(id) ON DELETE SET NULL,
                  room_name TEXT NOT NULL,
                  status TEXT NOT NULL,
                  x_m REAL,
                  y_m REAL,
                  svg_x REAL,
                  svg_y REAL,
                  created_at TEXT NOT NULL
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
                  floor_name TEXT DEFAULT 'Architectural Floor Plan',
                  document_type TEXT NOT NULL DEFAULT 'architectural'
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
                CREATE TABLE IF NOT EXISTS drawing_files (
                  drawing_id TEXT PRIMARY KEY,
                  filename TEXT NOT NULL,
                  file_type TEXT NOT NULL,
                  file_bytes BLOB NOT NULL,
                  created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS device_room_links (
                  id TEXT PRIMARY KEY,
                  project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                  device_element_id TEXT NOT NULL REFERENCES extracted_elements(id) ON DELETE CASCADE,
                  device_drawing_id TEXT NOT NULL REFERENCES drawings(id) ON DELETE CASCADE,
                  device_tag TEXT,
                  device_type TEXT NOT NULL,
                  room_element_id TEXT REFERENCES extracted_elements(id) ON DELETE SET NULL,
                  room_drawing_id TEXT REFERENCES drawings(id) ON DELETE SET NULL,
                  room_name TEXT NOT NULL,
                  status TEXT NOT NULL,
                  x_m REAL,
                  y_m REAL,
                  svg_x REAL,
                  svg_y REAL,
                  created_at TEXT NOT NULL
                );
                """
            )

        # Migration check: Ensure document_type exists on pre-existing drawings tables
        try:
            if is_postgres(con):
                con.execute("ALTER TABLE drawings ADD COLUMN IF NOT EXISTS document_type TEXT NOT NULL DEFAULT 'architectural'")
            else:
                raw_cols = [c[1] for c in con.execute("PRAGMA table_info(drawings)").fetchall()]
                if "document_type" not in raw_cols:
                    con.execute("ALTER TABLE drawings ADD COLUMN document_type TEXT NOT NULL DEFAULT 'architectural'")
        except Exception:
            pass

        # Migration check: Ensure device_room_links table exists
        try:
            con.execute("SELECT id FROM device_room_links LIMIT 1")
        except Exception:
            try:
                con.execute("""
                    CREATE TABLE IF NOT EXISTS device_room_links (
                      id TEXT PRIMARY KEY,
                      project_id TEXT NOT NULL,
                      device_element_id TEXT NOT NULL,
                      device_drawing_id TEXT NOT NULL,
                      device_tag TEXT,
                      device_type TEXT NOT NULL,
                      room_element_id TEXT,
                      room_drawing_id TEXT,
                      room_name TEXT NOT NULL,
                      status TEXT NOT NULL,
                      x_m REAL,
                      y_m REAL,
                      svg_x REAL,
                      svg_y REAL,
                      created_at TEXT NOT NULL
                    )
                """)
            except Exception:
                pass

        # Migration check: Ensure room_drawing_id column exists on device_room_links
        try:
            if is_postgres(con):
                con.execute("ALTER TABLE device_room_links ADD COLUMN IF NOT EXISTS room_drawing_id TEXT REFERENCES drawings(id) ON DELETE SET NULL")
            else:
                raw_cols = [c[1] for c in con.execute("PRAGMA table_info(device_room_links)").fetchall()]
                if "room_drawing_id" not in raw_cols:
                    con.execute("ALTER TABLE device_room_links ADD COLUMN room_drawing_id TEXT REFERENCES drawings(id) ON DELETE SET NULL")
        except Exception:
            pass

        load_code_clauses(con)


def save_drawing_file(drawing_id: str, filename: str, file_type: str, file_bytes: bytes, con: Any) -> None:
    if is_postgres(con):
        query = """
        INSERT INTO drawing_files (drawing_id, filename, file_type, file_bytes, created_at)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (drawing_id) DO UPDATE SET
            filename = EXCLUDED.filename,
            file_type = EXCLUDED.file_type,
            file_bytes = EXCLUDED.file_bytes,
            created_at = EXCLUDED.created_at
        """
        import psycopg2
        con.execute(query, (drawing_id, filename, file_type, psycopg2.Binary(file_bytes), now()))
    else:
        query = """
        INSERT OR REPLACE INTO drawing_files (drawing_id, filename, file_type, file_bytes, created_at)
        VALUES (?, ?, ?, ?, ?)
        """
        import sqlite3
        con.execute(query, (drawing_id, filename, file_type, sqlite3.Binary(file_bytes), now()))


def get_drawing_file(drawing_id: str, con: Any) -> tuple[str, str, bytes] | None:
    """Returns (filename, file_type, file_bytes) from persistent storage, or None."""
    row = con.execute("SELECT filename, file_type, file_bytes FROM drawing_files WHERE drawing_id = ?", (drawing_id,)).fetchone()
    if not row:
        return None
    raw_data = row["file_bytes"]
    if isinstance(raw_data, memoryview):
        b = raw_data.tobytes()
    elif hasattr(raw_data, "tobytes"):
        b = raw_data.tobytes()
    elif not isinstance(raw_data, bytes):
        b = bytes(raw_data)
    else:
        b = raw_data
    return (row["filename"], row["file_type"], b)
