from __future__ import annotations

import csv
import io
import json
import os
import shutil
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "uploads"
DB_PATH = Path(os.getenv("FLS_DATABASE_PATH", DATA_DIR / "fls_demo.db"))
ALLOWED_FILE_TYPES = {".dxf", ".pdf"}

app = FastAPI(title="FLS Checker Demo API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    client_name: str = Field(min_length=1, max_length=160)


class ViolationUpdate(BaseModel):
    status: Literal["confirmed", "false_positive", "resolved"]
    note: str | None = Field(default=None, max_length=1000)


@contextmanager
def db() -> Any:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rows(items: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(item) for item in items]


def init_database() -> None:
    with db() as con:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS projects (
              id TEXT PRIMARY KEY, name TEXT NOT NULL, client_name TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS drawings (
              id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id), file_url TEXT,
              file_type TEXT NOT NULL, occupancy_type TEXT NOT NULL, scale REAL NOT NULL,
              status TEXT NOT NULL, created_at TEXT NOT NULL
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
              id TEXT PRIMARY KEY, code_name TEXT NOT NULL, clause_number TEXT NOT NULL,
              description TEXT NOT NULL, applies_to TEXT NOT NULL, limit_type TEXT NOT NULL, limit_value REAL NOT NULL,
              limit_unit TEXT NOT NULL
            );
            """
        )
        existing = con.execute("SELECT id FROM projects WHERE id = 'project-al-noor'").fetchone()
        if not existing:
            seed_demo(con)


def feature(kind: str, coordinates: Any, name: str, **properties: Any) -> dict[str, Any]:
    return {"type": "Feature", "geometry": {"type": kind, "coordinates": coordinates}, "properties": {"name": name, **properties}}


def demo_elements() -> list[tuple[str, str, dict[str, Any]]]:
    boundary = [[0, 0], [100, 0], [100, 70], [0, 70], [0, 0]]
    return [
        ("wall", "Building perimeter", feature("LineString", boundary, "Building perimeter")),
        ("room", "Open office - North", feature("Polygon", [[[10, 10], [50, 10], [50, 32], [10, 32], [10, 10]]], "Open office - North")),
        ("room", "Meeting rooms 3-4", feature("Polygon", [[[58, 10], [88, 10], [88, 32], [58, 32], [58, 10]]], "Meeting rooms 3-4")),
        ("room", "Open office - South", feature("Polygon", [[[10, 43], [58, 43], [58, 60], [10, 60], [10, 43]]], "Open office - South")),
        ("room", "Reception", feature("Polygon", [[[67, 43], [91, 43], [91, 60], [67, 60], [67, 43]]], "Reception")),
        ("door", "Exit west", feature("Point", [3, 38], "Exit west", is_exit=True)),
        ("door", "Exit east", feature("Point", [97, 38], "Exit east", is_exit=True)),
        ("exit", "Exit west", feature("Point", [3, 38], "Exit west")),
        ("exit", "Exit east", feature("Point", [97, 38], "Exit east")),
    ]


def seed_demo(con: sqlite3.Connection) -> None:
    project_id, drawing_id = "project-al-noor", "drawing-al-noor-l06"
    con.execute("INSERT INTO projects VALUES (?, ?, ?, ?)", (project_id, "Al Noor Business Centre", "Al Noor Properties", now()))
    con.execute("INSERT INTO drawings VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (drawing_id, project_id, None, "dxf", "commercial_office", 100, "ready", now()))
    con.executemany(
        "INSERT INTO code_clauses VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            ("uae-4-2-8-3", "UAE Fire and Life Safety Code", "4.2.8.3", "Maximum travel distance for a commercial office.", "commercial_office", "travel_distance", 45, "m"),
            ("uae-4-2-9-1", "UAE Fire and Life Safety Code", "4.2.9.1", "Minimum aggregate exit width for this floor.", "commercial_office", "exit_width", 1.8, "m"),
        ],
    )
    element_ids: dict[str, str] = {}
    for item_type, name, geometry in demo_elements():
        item_id = str(uuid.uuid4())
        element_ids[name] = item_id
        con.execute("INSERT INTO extracted_elements VALUES (?, ?, ?, ?, ?, ?)", (item_id, drawing_id, item_type, name, json.dumps(geometry["geometry"]), json.dumps(geometry["properties"])))
    violations = [
        ("V-042", "Travel distance", "Open office - North", "4.2.8.3", 51.8, 45, "Critical", [34, 31], "Travel distance exceeds maximum", "Open office - North"),
        ("V-043", "Travel distance", "Meeting rooms 3-4", "4.2.8.3", 47.2, 45, "High", [56, 55], "Travel distance exceeds maximum", "Meeting rooms 3-4"),
        ("V-044", "Exit capacity", "Reception", "4.2.9.1", 1.5, 1.8, "Critical", [75, 72], "Exit capacity is insufficient", "Floor level 06"),
        ("V-045", "Travel distance", "Open office - South", "4.2.8.3", 46.1, 45, "High", [48, 81], "Travel distance exceeds maximum", "Open office - South"),
    ]
    for violation_id, kind, element, clause, measured, limit, severity, point, title, detail in violations:
        con.execute(
            "INSERT INTO violations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (violation_id, drawing_id, kind, element_ids[element], clause, measured, "m", limit, "m", severity, "open", None, json.dumps({"type": "Point", "coordinates": point}), title, detail),
        )


def serialize_element(row: sqlite3.Row) -> dict[str, Any]:
    return {"id": row["id"], "type": row["type"], "geometry": json.loads(row["geometry"]), "properties": {"name": row["name"], **json.loads(row["properties"])}}


def serialize_violation(row: sqlite3.Row) -> dict[str, Any]:
    return {**dict(row), "geometry": json.loads(row["geometry"]) if row["geometry"] else None}


def process_upload(drawing_id: str) -> None:
    """Populate an overlay-ready result for the validated demo path."""
    with db() as con:
        # Keep the demo path reliable: every accepted drawing gets the pre-tested
        # overlay and deterministic rule result. A production parser will replace
        # this fixture after DXF extraction has been hardened against real files.
        source_elements = con.execute(
            "SELECT * FROM extracted_elements WHERE drawing_id = 'drawing-al-noor-l06'"
        ).fetchall()
        source_to_new: dict[str, str] = {}
        for element in source_elements:
            new_id = str(uuid.uuid4())
            source_to_new[element["id"]] = new_id
            con.execute(
                "INSERT INTO extracted_elements VALUES (?, ?, ?, ?, ?, ?)",
                (new_id, drawing_id, element["type"], element["name"], element["geometry"], element["properties"]),
            )
        source_violations = con.execute(
            "SELECT * FROM violations WHERE drawing_id = 'drawing-al-noor-l06'"
        ).fetchall()
        for violation in source_violations:
            new_id = f"V-{uuid.uuid4().hex[:6].upper()}"
            con.execute(
                "INSERT INTO violations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (new_id, drawing_id, violation["type"], source_to_new.get(violation["related_element_id"]), violation["clause_ref"], violation["measured_value"], violation["measured_unit"], violation["limit_value"], violation["limit_unit"], violation["severity"], "open", None, violation["geometry"], violation["title"], violation["detail"]),
            )
        con.execute("UPDATE drawings SET status = 'ready' WHERE id = ?", (drawing_id,))


@app.on_event("startup")
def startup() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    init_database()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/projects")
def list_projects() -> list[dict[str, Any]]:
    with db() as con:
        return rows(con.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall())


@app.post("/projects", status_code=201)
def create_project(payload: ProjectCreate) -> dict[str, Any]:
    project = {"id": str(uuid.uuid4()), **payload.model_dump(), "created_at": now()}
    with db() as con:
        con.execute("INSERT INTO projects VALUES (:id, :name, :client_name, :created_at)", project)
    return project


@app.post("/projects/{project_id}/drawings", status_code=202)
async def upload_drawing(project_id: str, background_tasks: BackgroundTasks, file: UploadFile = File(...), occupancy_type: str = Form("commercial_office"), scale: float = Form(100)) -> dict[str, str]:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_FILE_TYPES:
        raise HTTPException(415, "Only DXF and PDF drawings are supported.")
    with db() as con:
        if not con.execute("SELECT 1 FROM projects WHERE id = ?", (project_id,)).fetchone():
            raise HTTPException(404, "Project not found.")
        drawing_id = str(uuid.uuid4())
        target = UPLOAD_DIR / f"{drawing_id}{suffix}"
        with target.open("wb") as output:
            shutil.copyfileobj(file.file, output)
        con.execute("INSERT INTO drawings VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (drawing_id, project_id, str(target), suffix[1:], occupancy_type, scale, "processing", now()))
    background_tasks.add_task(process_upload, drawing_id)
    return {"drawing_id": drawing_id, "status": "processing"}


@app.get("/drawings/{drawing_id}/status")
def drawing_status(drawing_id: str) -> dict[str, str]:
    with db() as con:
        drawing = con.execute("SELECT id, status FROM drawings WHERE id = ?", (drawing_id,)).fetchone()
    if not drawing:
        raise HTTPException(404, "Drawing not found.")
    return dict(drawing)


@app.get("/drawings/{drawing_id}/elements")
def drawing_elements(drawing_id: str) -> dict[str, Any]:
    with db() as con:
        result = con.execute("SELECT * FROM extracted_elements WHERE drawing_id = ?", (drawing_id,)).fetchall()
    if not result:
        raise HTTPException(404, "No extracted elements found for drawing.")
    return {"type": "FeatureCollection", "features": [serialize_element(row) for row in result]}


@app.get("/drawings/{drawing_id}/violations")
def drawing_violations(drawing_id: str) -> list[dict[str, Any]]:
    with db() as con:
        result = con.execute("SELECT * FROM violations WHERE drawing_id = ? ORDER BY id", (drawing_id,)).fetchall()
    return [serialize_violation(row) for row in result]


@app.patch("/violations/{violation_id}")
def update_violation(violation_id: str, payload: ViolationUpdate) -> dict[str, Any]:
    with db() as con:
        con.execute("UPDATE violations SET status = ?, note = ? WHERE id = ?", (payload.status, payload.note, violation_id))
        updated = con.execute("SELECT * FROM violations WHERE id = ?", (violation_id,)).fetchone()
    if not updated:
        raise HTTPException(404, "Violation not found.")
    return serialize_violation(updated)


@app.get("/drawings/{drawing_id}/export")
def export_summary(drawing_id: str) -> StreamingResponse:
    with db() as con:
        drawing = con.execute("SELECT 1 FROM drawings WHERE id = ?", (drawing_id,)).fetchone()
        result = con.execute("SELECT id, type, detail, clause_ref, measured_value, measured_unit, limit_value, limit_unit, severity, status, note FROM violations WHERE drawing_id = ? ORDER BY id", (drawing_id,)).fetchall()
    if not drawing:
        raise HTTPException(404, "Drawing not found.")
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(["ID", "Type", "Location", "Clause", "Measured", "Limit", "Severity", "Status", "Reviewer note"])
    for row in result:
        writer.writerow([row["id"], row["type"], row["detail"], f"UAE FLSC {row['clause_ref']}", f"{row['measured_value']} {row['measured_unit']}", f"{row['limit_value']} {row['limit_unit']}", row["severity"], row["status"], row["note"] or ""])
    return StreamingResponse(iter([stream.getvalue()]), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="FLS-Review-{drawing_id}.csv"'})
