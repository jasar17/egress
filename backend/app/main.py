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
import pymupdf

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, Response, UploadFile
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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    client_name: str = Field(min_length=1, max_length=160)
    occupancy_type: str = Field(default="Business - Regular office areas")
    sprinklered: bool = Field(default=True)


class DrawingConfigUpdate(BaseModel):
    sprinklered: bool | None = None
    occupancy_type: str | None = None
    page_index: int | None = None


class PageSelect(BaseModel):
    page_index: int = 0


class ViolationUpdate(BaseModel):
    status: Literal["confirmed", "false_positive", "resolved", "open"]
    note: str | None = Field(default=None, max_length=1000)


from app.db import get_db as db, get_drawing_file, init_db, is_postgres, load_code_clauses, now, save_drawing_file


def rows(items: list[Any]) -> list[dict[str, Any]]:
    return [dict(item) for item in items]


def init_database() -> None:
    init_db()
    with db() as con:
        existing = con.execute("SELECT id FROM projects WHERE id = ?", ("project-al-noor",)).fetchone()
        if not existing:
            seed_demo(con)


def feature(kind: str, coordinates: Any, name: str, **properties: Any) -> dict[str, Any]:
    return {"type": "Feature", "geometry": {"type": kind, "coordinates": coordinates}, "properties": {"name": name, **properties}}


def demo_elements() -> list[tuple[str, str, dict[str, Any]]]:
    boundary = [[5, 5], [95, 5], [95, 95], [5, 95], [5, 5]]
    return [
        ("wall", "Building perimeter", feature("LineString", boundary, "Building perimeter")),
        ("room", "Open office - North", feature("Polygon", [[[10, 10], [50, 10], [50, 42], [10, 42], [10, 10]]], "Open office - North", area_m2=120.0, centroid=[30, 26], occupant_load=13)),
        ("room", "Meeting rooms 3-4", feature("Polygon", [[[58, 10], [88, 10], [88, 42], [58, 42], [58, 10]]], "Meeting rooms 3-4", area_m2=66.0, centroid=[73, 26], occupant_load=8)),
        ("room", "Open office - South", feature("Polygon", [[[10, 58], [58, 58], [58, 90], [10, 90], [10, 58]]], "Open office - South", area_m2=140.0, centroid=[34, 74], occupant_load=15)),
        ("room", "Reception", feature("Polygon", [[[67, 58], [91, 58], [91, 90], [67, 90], [67, 58]]], "Reception", area_m2=70.0, centroid=[79, 74], occupant_load=8)),
        ("door", "Exit west", feature("Point", [5, 50], "Exit west", is_exit=True)),
        ("door", "Exit east", feature("Point", [95, 50], "Exit east", is_exit=True)),
        ("exit", "Exit west", feature("Point", [5, 50], "Exit west")),
        ("exit", "Exit east", feature("Point", [95, 50], "Exit east")),
    ]


def seed_demo(con: sqlite3.Connection) -> None:
    project_id, drawing_id = "project-al-noor", "drawing-al-noor-l06"
    con.execute("DELETE FROM extracted_elements WHERE drawing_id = ?", (drawing_id,))
    con.execute("DELETE FROM violations WHERE drawing_id = ?", (drawing_id,))
    con.execute("INSERT OR REPLACE INTO projects VALUES (?, ?, ?, ?, ?, ?)", (project_id, "Al Noor Business Centre", "Al Noor Properties", now(), "Business - Regular office areas", 1))
    con.execute("INSERT OR REPLACE INTO drawings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (drawing_id, project_id, None, "dxf", "Business - Regular office areas", 100, "ready", now(), 1, 0, "Level 06 - Architectural CAD Overview"))
    element_ids: dict[str, str] = {}
    for item_type, name, geometry in demo_elements():
        item_id = str(uuid.uuid4())
        element_ids[name] = item_id
        con.execute("INSERT INTO extracted_elements VALUES (?, ?, ?, ?, ?, ?)", (item_id, drawing_id, item_type, name, json.dumps(geometry["geometry"]), json.dumps(geometry["properties"])))
    violations = [
        ("V-042", "Travel distance", "Open office - North", "3.16-BUS-TD-S", 51.8, 45, "Critical", [30, 26], "Travel distance exceeds maximum", "Open office - North"),
        ("V-043", "Travel distance", "Meeting rooms 3-4", "3.16-BUS-TD-S", 47.2, 45, "High", [73, 26], "Travel distance exceeds maximum", "Meeting rooms 3-4"),
        ("V-044", "Exit capacity", "Reception", "3.14-LT500", 1.5, 1.8, "Critical", [79, 74], "Exit capacity is insufficient", "Floor level 06"),
        ("V-045", "Travel distance", "Open office - South", "3.16-BUS-TD-S", 46.1, 45, "High", [34, 74], "Travel distance exceeds maximum", "Open office - South"),
    ]
    for violation_id, kind, element, clause, measured, limit, severity, point, title, detail in violations:
        con.execute(
            "INSERT INTO violations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (violation_id, drawing_id, kind, element_ids.get(element), clause, measured, "m", limit, "m", severity, "open", None, json.dumps({"type": "Point", "coordinates": point}), title, detail),
        )


def serialize_element(row: sqlite3.Row) -> dict[str, Any]:
    return {"id": row["id"], "type": row["type"], "geometry": json.loads(row["geometry"]), "properties": {"name": row["name"], **json.loads(row["properties"])}}


def serialize_violation(row: sqlite3.Row) -> dict[str, Any]:
    return {**dict(row), "geometry": json.loads(row["geometry"]) if row["geometry"] else None}


# Global in-memory caches for fast multi-floor navigation and image delivery
_MULTI_FLOOR_CACHE: dict[str, dict[str, Any]] = {}
_IMAGE_CACHE: dict[str, tuple[bytes, float]] = {}


def invalidate_drawing_cache(drawing_id: str) -> None:
    """Invalidates cached floor analyses and rendered images when a drawing is modified or reconfigured."""
    prefix = f"{drawing_id}_"
    for k in list(_MULTI_FLOOR_CACHE.keys()):
        if k == drawing_id or k.startswith(prefix):
            _MULTI_FLOOR_CACHE.pop(k, None)
    for k in list(_IMAGE_CACHE.keys()):
        if k == drawing_id or k.startswith(prefix):
            _IMAGE_CACHE.pop(k, None)


from app.dxf_parser import DXFParseError, parse_dxf_file
from app.occupant_load import calculate_occupant_loads
from app.path_analysis import calculate_walkable_distances
from app.pdf_parser import PDFParseError, get_pdf_pages_metadata, parse_pdf_file
from app.rules_engine import evaluate_fls_rules


def ensure_drawing_file(drawing_id: str, con: Any) -> tuple[Path | None, bytes | None]:
    """
    Checks if drawing file exists locally on disk in UPLOAD_DIR.
    If missing (e.g. after a Render container redeploy or restart),
    restores the binary from persistent Supabase PostgreSQL storage.
    Returns (local_path, file_bytes).
    """
    drawing = con.execute("SELECT * FROM drawings WHERE id = ?", (drawing_id,)).fetchone()
    if not drawing:
        return None, None

    file_type = drawing["file_type"]
    target = UPLOAD_DIR / f"{drawing_id}.{file_type}"

    # 1. If already on local disk and non-empty
    if target.exists() and target.stat().st_size > 0:
        try:
            with open(target, "rb") as f:
                return target, f.read()
        except Exception:
            return target, None

    # 2. Check persistent drawing_files table (Supabase Postgres)
    stored = get_drawing_file(drawing_id, con)
    if stored:
        _, _, file_bytes = stored
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        with open(target, "wb") as f:
            f.write(file_bytes)
        return target, file_bytes

    # 3. Fallback: check drawing["file_url"]
    raw_url = drawing["file_url"]
    if raw_url and Path(raw_url).exists() and Path(raw_url).stat().st_size > 0:
        try:
            with open(raw_url, "rb") as f:
                return Path(raw_url), f.read()
        except Exception:
            return Path(raw_url), None

    return None, None


def process_upload(drawing_id: str, page_index: int | None = None) -> None:
    """Process uploaded drawing: real parsing for DXF and PDF files, preserving seeded drawing as demo fixture."""
    with db() as con:
        drawing = con.execute("SELECT * FROM drawings WHERE id = ?", (drawing_id,)).fetchone()
        if not drawing:
            return

        file_type = drawing["file_type"]
        is_sprinklered = bool(drawing["sprinklered"]) if "sprinklered" in drawing.keys() and drawing["sprinklered"] is not None else True
        occupancy_type = drawing["occupancy_type"] if drawing["occupancy_type"] else "Business - Regular office areas"
        active_page = page_index if page_index is not None else (drawing["page_index"] if "page_index" in drawing.keys() else 0)

        file_path, _ = ensure_drawing_file(drawing_id, con)
        file_url = str(file_path) if file_path else drawing["file_url"]

        if file_url and file_type in ("dxf", "pdf"):
            try:
                if file_type == "dxf":
                    parsed = parse_dxf_file(file_url, drawing_scale=drawing["scale"])
                    floor_name = drawing["floor_name"] or Path(file_url).stem.replace("_", " ")
                else:
                    parsed = parse_pdf_file(file_url, page_index=active_page)
                    floor_name = parsed.get("floor_name") or f"Level {active_page:02d}"

                parsed = calculate_walkable_distances(parsed)
                parsed = calculate_occupant_loads(parsed, con=con, default_occupancy=occupancy_type)
                elements = parsed["elements"]
                if not elements:
                    raise DXFParseError(f"No architectural elements could be extracted from this {file_type.upper()} file.")

                # Remove previous elements/violations for this drawing
                con.execute("DELETE FROM extracted_elements WHERE drawing_id = ?", (drawing_id,))
                con.execute("DELETE FROM violations WHERE drawing_id = ?", (drawing_id,))

                # Insert real extracted elements (walls, rooms, doors, exits) with path distances & loads
                element_id_map: dict[str, str] = {}
                for item_type, name, geom in elements:
                    item_id = str(uuid.uuid4())
                    element_id_map[name] = item_id
                    con.execute(
                        "INSERT INTO extracted_elements VALUES (?, ?, ?, ?, ?, ?)",
                        (
                            item_id,
                            drawing_id,
                            item_type,
                            name,
                            json.dumps(geom["geometry"]),
                            json.dumps(geom.get("properties", {})),
                        ),
                    )

                # Generate Real UAE Code-Cited Violations based on exact sprinkler & occupancy inputs
                real_violations = evaluate_fls_rules(
                    parsed,
                    con=con,
                    drawing_id=drawing_id,
                    element_id_map=element_id_map,
                    is_sprinklered=is_sprinklered,
                    occupancy_type=occupancy_type,
                )

                for v in real_violations:
                    con.execute(
                        "INSERT INTO violations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            v["id"],
                            drawing_id,
                            v["type"],
                            v["related_element_id"],
                            v["clause_ref"],
                            v["measured_value"],
                            v["measured_unit"],
                            v["limit_value"],
                            v["limit_unit"],
                            v["severity"],
                            v["status"],
                            v["note"],
                            json.dumps(v["geometry"]) if v["geometry"] else None,
                            v["title"],
                            v["detail"],
                        ),
                    )

                con.execute("UPDATE drawings SET status = 'ready', floor_name = ?, page_index = ? WHERE id = ?", (floor_name, active_page, drawing_id))
            except Exception as e:
                con.execute("UPDATE drawings SET status = 'failed' WHERE id = ?", (drawing_id,))
                raise HTTPException(400, f"{file_type.upper()} Parsing Failed: {str(e)}")

        else:
            # Fallback path for legacy fixtures
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
                    (
                        new_id,
                        drawing_id,
                        violation["type"],
                        source_to_new.get(violation["related_element_id"]),
                        violation["clause_ref"],
                        violation["measured_value"],
                        violation["measured_unit"],
                        violation["limit_value"],
                        violation["limit_unit"],
                        violation["severity"],
                        "open",
                        None,
                        violation["geometry"],
                        violation["title"],
                        violation["detail"],
                    ),
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
    project = {
        "id": str(uuid.uuid4()),
        "name": payload.name,
        "client_name": payload.client_name,
        "occupancy_type": payload.occupancy_type,
        "sprinklered": 1 if payload.sprinklered else 0,
        "created_at": now(),
    }
    with db() as con:
        con.execute(
            "INSERT INTO projects VALUES (?, ?, ?, ?, ?, ?)",
            (project["id"], project["name"], project["client_name"], project["created_at"], project["occupancy_type"], project["sprinklered"])
        )
    return project


@app.post("/projects/{project_id}/drawings", status_code=201)
async def upload_drawing(
    project_id: str,
    file: UploadFile = File(...),
    occupancy_type: str = Form("Business - Regular office areas"),
    sprinklered: bool = Form(True),
    scale: float = Form(100)
) -> dict[str, Any]:
    if not occupancy_type or not occupancy_type.strip():
        raise HTTPException(400, "Occupancy type is required to select appropriate UAE FLS Code limits.")
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_FILE_TYPES:
        raise HTTPException(415, "Only DXF and PDF drawings are supported.")
    with db() as con:
        if not con.execute("SELECT 1 FROM projects WHERE id = ?", (project_id,)).fetchone():
            raise HTTPException(404, "Project not found.")
        drawing_id = str(uuid.uuid4())
        target = UPLOAD_DIR / f"{drawing_id}{suffix}"
        content = await file.read()
        with target.open("wb") as output:
            output.write(content)

        # Initial floor name guess from filename
        raw_floor = Path(file.filename or "").stem.replace("_", " ")
        con.execute(
            "INSERT INTO drawings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (drawing_id, project_id, str(target), suffix[1:], occupancy_type.strip(), scale, "processing", now(), 1 if sprinklered else 0, 0, raw_floor)
        )
        # Store file binary in persistent Supabase PostgreSQL storage
        save_drawing_file(drawing_id, file.filename or f"drawing_{drawing_id[:8]}{suffix}", suffix[1:], content, con)

    # Invalidate any stale cache for this drawing id
    invalidate_drawing_cache(drawing_id)

    # Process drawing geometry for page 0
    process_upload(drawing_id, page_index=0)
    
    with db() as con:
        drawing = con.execute("SELECT * FROM drawings WHERE id = ?", (drawing_id,)).fetchone()
        final_status = drawing["status"] if drawing else "ready"
        final_floor = drawing["floor_name"] if drawing and "floor_name" in drawing.keys() else raw_floor
        summary = compute_multi_floor_summary(drawing_id, con)
        pages = [
            {
                "index": f["index"],
                "title": f["title"],
                "rooms_count": f["rooms_count"],
                "exits_count": f["exits_count"],
                "total_occupant_load": f["total_occupant_load"],
                "total_floor_area_m2": f["total_floor_area_m2"],
                "max_travel_distance_m": f["max_travel_distance_m"],
                "violations_count": f["violations_count"],
                "status": f["status"],
            }
            for f in summary.get("floors", [])
        ]

    return {
        "drawing_id": drawing_id,
        "status": final_status,
        "file_name": file.filename or f"drawing_{drawing_id[:8]}",
        "floor_name": final_floor,
        "occupancy_type": occupancy_type,
        "sprinklered": sprinklered,
        "scale": scale,
        "has_image": suffix == ".pdf",
        "page_index": 0,
        "pages_count": len(pages) if pages else 1,
        "pages": pages,
        "multi_floor_summary": summary,
    }


@app.get("/drawings/{drawing_id}/image")
def get_drawing_image(drawing_id: str, page: int | None = None) -> Response:
    """Renders the exact architectural PDF page into a crisp PNG image overview, cached in memory."""
    target_page_idx = page if page is not None else 0
    cache_key = f"{drawing_id}_{target_page_idx}"
    if cache_key in _IMAGE_CACHE:
        img_bytes, aspect_ratio = _IMAGE_CACHE[cache_key]
        return Response(
            content=img_bytes,
            media_type="image/png",
            headers={
                "Cache-Control": "public, max-age=86400",
                "X-Floor-Page": str(target_page_idx),
                "X-Aspect-Ratio": str(aspect_ratio),
                "Access-Control-Expose-Headers": "X-Aspect-Ratio, X-Floor-Page, X-Total-Pages"
            }
        )

    with db() as con:
        drawing = con.execute("SELECT * FROM drawings WHERE id = ?", (drawing_id,)).fetchone()
        if not drawing:
            raise HTTPException(404, "Drawing not found.")

        file_type = drawing["file_type"]
        if file_type != "pdf":
            raise HTTPException(404, "No rendered raster image available for this drawing format.")

        file_path, file_bytes = ensure_drawing_file(drawing_id, con)

    if not file_path and not file_bytes:
        raise HTTPException(404, "No rendered raster image available for this drawing format.")

    try:
        if file_bytes:
            doc = pymupdf.open(stream=file_bytes, filetype="pdf")
        else:
            doc = pymupdf.open(str(file_path))
        if len(doc) == 0:
            raise HTTPException(404, "PDF document is empty.")

        target_page = page if page is not None else (drawing["page_index"] if "page_index" in drawing.keys() else 0)
        target_page = min(max(0, target_page), len(doc) - 1)

        pdf_page = doc[target_page]
        pix = pdf_page.get_pixmap(dpi=220)
        img_bytes = pix.tobytes("png")
        aspect_ratio = round(pdf_page.rect.width / pdf_page.rect.height, 4) if pdf_page.rect.height > 0 else 1.4142

        # Cache rendered image bytes in memory
        _IMAGE_CACHE[f"{drawing_id}_{target_page}"] = (img_bytes, aspect_ratio)

        return Response(
            content=img_bytes,
            media_type="image/png",
            headers={
                "Cache-Control": "public, max-age=86400",
                "X-Floor-Page": str(target_page),
                "X-Total-Pages": str(len(doc)),
                "X-Aspect-Ratio": str(aspect_ratio),
                "Access-Control-Expose-Headers": "X-Aspect-Ratio, X-Floor-Page, X-Total-Pages"
            }
        )
    except Exception as e:
        raise HTTPException(500, f"Failed to render drawing image: {str(e)}")


@app.get("/drawings/{drawing_id}/file")
def get_drawing_file_download(drawing_id: str) -> Response:
    """Downloads the original persistent CAD DXF or PDF drawing file."""
    with db() as con:
        drawing = con.execute("SELECT * FROM drawings WHERE id = ?", (drawing_id,)).fetchone()
        if not drawing:
            raise HTTPException(404, "Drawing not found.")
        file_path, file_bytes = ensure_drawing_file(drawing_id, con)

    if not file_bytes and file_path and file_path.exists():
        with open(file_path, "rb") as f:
            file_bytes = f.read()

    if not file_bytes:
        raise HTTPException(404, "Drawing file binary not found in persistent storage.")

    filename = drawing["floor_name"] or f"drawing_{drawing_id[:8]}"
    file_type = drawing["file_type"]
    if not filename.endswith(f".{file_type}"):
        filename = f"{filename}.{file_type}"

    media_type = "application/pdf" if file_type == "pdf" else "application/dxf" if file_type == "dxf" else "application/octet-stream"
    return Response(
        content=file_bytes,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Drawing-Id": drawing_id,
            "X-File-Size": str(len(file_bytes)),
            "Access-Control-Expose-Headers": "Content-Disposition, X-Drawing-Id, X-File-Size"
        }
    )


def compute_multi_floor_summary(drawing_id: str, con: sqlite3.Connection) -> dict[str, Any]:
    """Decodes and analyzes all floor plans in a drawing (single or multi-page), evaluating violations per floor with in-memory caching."""
    drawing = con.execute("SELECT * FROM drawings WHERE id = ?", (drawing_id,)).fetchone()
    if not drawing:
        raise HTTPException(404, "Drawing not found.")

    file_type = drawing["file_type"]
    is_sprinklered = bool(drawing["sprinklered"]) if "sprinklered" in drawing.keys() and drawing["sprinklered"] is not None else True
    occupancy_type = drawing["occupancy_type"] if drawing["occupancy_type"] else "Business - Regular office areas"
    active_page = drawing["page_index"] if "page_index" in drawing.keys() and drawing["page_index"] is not None else 0

    cache_key = f"{drawing_id}_{int(is_sprinklered)}_{occupancy_type}"
    if cache_key in _MULTI_FLOOR_CACHE:
        cached = _MULTI_FLOOR_CACHE[cache_key]
        cached["active_page_index"] = active_page
        return cached

    file_path, _ = ensure_drawing_file(drawing_id, con)
    file_url = str(file_path) if file_path else drawing["file_url"]

    if not file_url or not Path(file_url).exists():
        # Demo drawing fallback
        demo_violations = con.execute("SELECT * FROM violations WHERE drawing_id = ?", (drawing_id,)).fetchall()
        demo_elements = con.execute("SELECT * FROM extracted_elements WHERE drawing_id = ?", (drawing_id,)).fetchall()
        v_list = [serialize_violation(v) for v in demo_violations]
        demo_features = [serialize_element(e) for e in demo_elements]
        room_elements = [e for e in demo_elements if e["type"] == "room"]
        result = {
            "drawing_id": drawing_id,
            "total_pages": 1,
            "active_page_index": 0,
            "total_violations_count": len(demo_violations),
            "floors": [{
                "index": 0,
                "title": drawing["floor_name"] or "Level 06 - Architectural CAD Overview",
                "rooms_count": len(room_elements),
                "walls_count": 1,
                "doors_count": 2,
                "exits_count": 2,
                "total_occupant_load": 44,
                "total_floor_area_m2": 396.0,
                "max_travel_distance_m": 51.8,
                "violations_count": len(demo_violations),
                "status": "NON-COMPLIANT" if demo_violations else "COMPLIANT",
                "violations": v_list,
                "elements": demo_features,
                "rooms_summary": [
                    {
                        "name": r["name"],
                        "area_m2": json.loads(r["properties"]).get("area_m2", 0),
                        "occupant_load": json.loads(r["properties"]).get("occupant_load", 0),
                        "travel_distance_m": 0.0,
                        "nearest_exit": "Exit west",
                    }
                    for r in room_elements
                ]
            }]
        }
        _MULTI_FLOOR_CACHE[cache_key] = result
        return result

    floors: list[dict[str, Any]] = []
    total_violations = 0

    if file_type == "pdf":
        try:
            doc = pymupdf.open(file_url)
            total_pages = len(doc)
        except Exception:
            total_pages = 1

        for p_idx in range(total_pages):
            try:
                parsed = parse_pdf_file(file_url, page_index=p_idx)
                parsed = calculate_walkable_distances(parsed)
                parsed = calculate_occupant_loads(parsed, con=con, default_occupancy=occupancy_type)
                floor_title = parsed.get("floor_name") or f"Floor Level {p_idx:02d}"

                element_id_map = {r["name"]: f"{drawing_id}-elem-{p_idx}-{i}" for i, r in enumerate(parsed.get("rooms", []))}
                floor_violations = evaluate_fls_rules(
                    parsed,
                    con=con,
                    drawing_id=drawing_id,
                    element_id_map=element_id_map,
                    is_sprinklered=is_sprinklered,
                    occupancy_type=occupancy_type,
                )

                # Format GeoJSON features for this floor
                floor_features: list[dict[str, Any]] = []
                for i, (item_type, name, geom) in enumerate(parsed.get("elements", [])):
                    floor_features.append({
                        "id": element_id_map.get(name, f"{drawing_id}-elem-{p_idx}-{i}"),
                        "type": item_type,
                        "geometry": geom["geometry"],
                        "properties": {"name": name, **geom.get("properties", {})}
                    })

                rooms = parsed.get("rooms", [])
                habitable_rooms = [r for r in rooms if "STAIR" not in r["name"].upper() and "EXIT" not in r["name"].upper()]
                total_load = sum(r.get("occupant_load", 0) for r in habitable_rooms)
                total_area = round(sum(r.get("area_m2", 0.0) for r in rooms), 1)
                max_travel = max([r.get("travel_distance_m", 0.0) for r in rooms]) if rooms else 0.0
                v_count = len(floor_violations)
                total_violations += v_count

                floors.append({
                    "index": p_idx,
                    "title": floor_title,
                    "rooms_count": len(rooms),
                    "walls_count": parsed.get("summary", {}).get("walls_count", 0),
                    "doors_count": parsed.get("summary", {}).get("doors_count", 0),
                    "exits_count": len(parsed.get("exits", [])),
                    "total_occupant_load": total_load,
                    "total_floor_area_m2": total_area,
                    "max_travel_distance_m": round(max_travel, 2),
                    "violations_count": v_count,
                    "status": "COMPLIANT" if v_count == 0 else "NON-COMPLIANT",
                    "violations": floor_violations,
                    "elements": floor_features,
                    "rooms_summary": [
                        {
                            "name": r["name"],
                            "area_m2": r.get("area_m2", 0.0),
                            "occupant_load": r.get("occupant_load", 0),
                            "travel_distance_m": r.get("travel_distance_m", 0.0),
                            "nearest_exit": r.get("nearest_exit", "N/A"),
                        }
                        for r in rooms
                    ]
                })
            except Exception as e:
                floors.append({
                    "index": p_idx,
                    "title": f"Floor Page {p_idx + 1}",
                    "rooms_count": 0,
                    "walls_count": 0,
                    "doors_count": 0,
                    "exits_count": 0,
                    "total_occupant_load": 0,
                    "total_floor_area_m2": 0.0,
                    "max_travel_distance_m": 0.0,
                    "violations_count": 0,
                    "status": "ERROR",
                    "error": str(e),
                    "violations": [],
                    "elements": [],
                    "rooms_summary": []
                })
    else:
        # DXF File
        parsed = parse_dxf_file(file_url, drawing_scale=drawing["scale"])
        parsed = calculate_walkable_distances(parsed)
        parsed = calculate_occupant_loads(parsed, con=con, default_occupancy=occupancy_type)
        floor_title = drawing["floor_name"] or Path(file_url).stem.replace("_", " ")
        element_id_map = {r["name"]: f"{drawing_id}-elem-0-{i}" for i, r in enumerate(parsed.get("rooms", []))}
        floor_violations = evaluate_fls_rules(
            parsed,
            con=con,
            drawing_id=drawing_id,
            element_id_map=element_id_map,
            is_sprinklered=is_sprinklered,
            occupancy_type=occupancy_type,
        )

        dxf_features: list[dict[str, Any]] = []
        for i, (item_type, name, geom) in enumerate(parsed.get("elements", [])):
            dxf_features.append({
                "id": element_id_map.get(name, f"{drawing_id}-elem-0-{i}"),
                "type": item_type,
                "geometry": geom["geometry"],
                "properties": {"name": name, **geom.get("properties", {})}
            })

        rooms = parsed.get("rooms", [])
        habitable_rooms = [r for r in rooms if "STAIR" not in r["name"].upper() and "EXIT" not in r["name"].upper()]
        total_load = sum(r.get("occupant_load", 0) for r in habitable_rooms)
        total_area = round(sum(r.get("area_m2", 0.0) for r in rooms), 1)
        max_travel = max([r.get("travel_distance_m", 0.0) for r in rooms]) if rooms else 0.0
        v_count = len(floor_violations)
        total_violations += v_count

        floors.append({
            "index": 0,
            "title": floor_title,
            "rooms_count": len(rooms),
            "walls_count": parsed.get("summary", {}).get("walls_count", 0),
            "doors_count": parsed.get("summary", {}).get("doors_count", 0),
            "exits_count": len(parsed.get("exits", [])),
            "total_occupant_load": total_load,
            "total_floor_area_m2": total_area,
            "max_travel_distance_m": round(max_travel, 2),
            "violations_count": v_count,
            "status": "COMPLIANT" if v_count == 0 else "NON-COMPLIANT",
            "violations": floor_violations,
            "elements": dxf_features,
            "rooms_summary": [
                {
                    "name": r["name"],
                    "area_m2": r.get("area_m2", 0.0),
                    "occupant_load": r.get("occupant_load", 0),
                    "travel_distance_m": r.get("travel_distance_m", 0.0),
                    "nearest_exit": r.get("nearest_exit", "N/A"),
                }
                for r in rooms
            ]
        })

    summary_result = {
        "drawing_id": drawing_id,
        "total_pages": len(floors),
        "active_page_index": active_page,
        "total_violations_count": total_violations,
        "floors": floors,
    }
    _MULTI_FLOOR_CACHE[cache_key] = summary_result
    return summary_result


@app.get("/drawings/{drawing_id}/multi-floor-summary")
def get_multi_floor_summary(drawing_id: str) -> dict[str, Any]:
    """Returns complete decoded analysis, room breakdowns, and error lists for every floor plan in the drawing."""
    with db() as con:
        return compute_multi_floor_summary(drawing_id, con)


@app.get("/drawings/{drawing_id}/pages")
def get_drawing_pages(drawing_id: str) -> list[dict[str, Any]]:
    """Returns detected floor plan pages with error counts for multi-floor drawings."""
    with db() as con:
        summary = compute_multi_floor_summary(drawing_id, con)
        return [
            {
                "index": f["index"],
                "title": f["title"],
                "rooms_count": f["rooms_count"],
                "exits_count": f["exits_count"],
                "total_occupant_load": f["total_occupant_load"],
                "total_floor_area_m2": f["total_floor_area_m2"],
                "max_travel_distance_m": f["max_travel_distance_m"],
                "violations_count": f["violations_count"],
                "status": f["status"],
            }
            for f in summary.get("floors", [])
        ]


@app.post("/drawings/{drawing_id}/page")
def select_drawing_page(drawing_id: str, payload: PageSelect) -> dict[str, Any]:
    """Switches the active floor page for a drawing, updating active page instantly."""
    with db() as con:
        drawing = con.execute("SELECT * FROM drawings WHERE id = ?", (drawing_id,)).fetchone()
        if not drawing:
            raise HTTPException(404, "Drawing not found.")

    is_sprinklered = bool(drawing["sprinklered"]) if "sprinklered" in drawing.keys() and drawing["sprinklered"] is not None else True
    occupancy_type = drawing["occupancy_type"] if drawing["occupancy_type"] else "Business - Regular office areas"
    cache_key = f"{drawing_id}_{int(is_sprinklered)}_{occupancy_type}"

    # Fast-path: If multi-floor summary is already cached, reuse cached floor data to sync DB
    cached_summary = _MULTI_FLOOR_CACHE.get(cache_key)
    target_floor_data = None
    if cached_summary:
        target_floor_data = next((f for f in cached_summary.get("floors", []) if f["index"] == payload.page_index), None)

    if target_floor_data and "elements" in target_floor_data:
        floor_name = target_floor_data["title"]
        with db() as con:
            con.execute("DELETE FROM extracted_elements WHERE drawing_id = ?", (drawing_id,))
            con.execute("DELETE FROM violations WHERE drawing_id = ?", (drawing_id,))
            for elem in target_floor_data.get("elements", []):
                con.execute(
                    "INSERT INTO extracted_elements VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        elem["id"],
                        drawing_id,
                        elem["type"],
                        elem["properties"].get("name", ""),
                        json.dumps(elem["geometry"]),
                        json.dumps(elem.get("properties", {})),
                    ),
                )
            for v in target_floor_data.get("violations", []):
                con.execute(
                    "INSERT INTO violations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        v["id"],
                        drawing_id,
                        v["type"],
                        v.get("related_element_id"),
                        v["clause_ref"],
                        v["measured_value"],
                        v["measured_unit"],
                        v["limit_value"],
                        v["limit_unit"],
                        v["severity"],
                        v.get("status", "open"),
                        v.get("note"),
                        json.dumps(v["geometry"]) if v.get("geometry") else None,
                        v["title"],
                        v["detail"],
                    ),
                )
            con.execute("UPDATE drawings SET status = 'ready', floor_name = ?, page_index = ? WHERE id = ?", (floor_name, payload.page_index, drawing_id))
    else:
        # Fallback to full process_upload
        process_upload(drawing_id, page_index=payload.page_index)

    with db() as con:
        updated = con.execute("SELECT * FROM drawings WHERE id = ?", (drawing_id,)).fetchone()
        d_dict = dict(updated)
        summary = compute_multi_floor_summary(drawing_id, con)
        d_dict["multi_floor_summary"] = summary
        d_dict["pages"] = [
            {
                "index": f["index"],
                "title": f["title"],
                "rooms_count": f["rooms_count"],
                "exits_count": f["exits_count"],
                "total_occupant_load": f["total_occupant_load"],
                "total_floor_area_m2": f["total_floor_area_m2"],
                "max_travel_distance_m": f["max_travel_distance_m"],
                "violations_count": f["violations_count"],
                "status": f["status"],
            }
            for f in summary.get("floors", [])
        ]
        return d_dict


@app.patch("/drawings/{drawing_id}/config")
def update_drawing_config(drawing_id: str, payload: DrawingConfigUpdate) -> dict[str, Any]:
    # Invalidate multi-floor cache since occupancy or sprinkler rules may change
    invalidate_drawing_cache(drawing_id)

    with db() as con:
        drawing = con.execute("SELECT * FROM drawings WHERE id = ?", (drawing_id,)).fetchone()
        if not drawing:
            raise HTTPException(404, "Drawing not found.")

        updates = []
        params: list[Any] = []
        if payload.sprinklered is not None:
            updates.append("sprinklered = ?")
            params.append(1 if payload.sprinklered else 0)
        if payload.occupancy_type is not None:
            if not payload.occupancy_type.strip():
                raise HTTPException(400, "Occupancy type cannot be empty.")
            updates.append("occupancy_type = ?")
            params.append(payload.occupancy_type.strip())
        if payload.page_index is not None:
            updates.append("page_index = ?")
            params.append(payload.page_index)

        if updates:
            params.append(drawing_id)
            con.execute(f"UPDATE drawings SET {', '.join(updates)} WHERE id = ?", params)

    # Re-evaluate rules with updated configuration
    page_idx = payload.page_index if payload.page_index is not None else (drawing["page_index"] if "page_index" in drawing.keys() else 0)
    process_upload(drawing_id, page_index=page_idx)
    with db() as con:
        updated = con.execute("SELECT * FROM drawings WHERE id = ?", (drawing_id,)).fetchone()
        return dict(updated)


@app.get("/drawings/{drawing_id}")
def get_drawing(drawing_id: str) -> dict[str, Any]:
    with db() as con:
        drawing = con.execute("SELECT * FROM drawings WHERE id = ?", (drawing_id,)).fetchone()
        if not drawing:
            raise HTTPException(404, "Drawing not found.")
        
        d_dict = dict(drawing)
        summary = compute_multi_floor_summary(drawing_id, con)
        d_dict["pages_count"] = summary.get("total_pages", 1)
        d_dict["pages"] = [
            {
                "index": f["index"],
                "title": f["title"],
                "rooms_count": f["rooms_count"],
                "exits_count": f["exits_count"],
                "total_occupant_load": f["total_occupant_load"],
                "total_floor_area_m2": f["total_floor_area_m2"],
                "max_travel_distance_m": f["max_travel_distance_m"],
                "violations_count": f["violations_count"],
                "status": f["status"],
            }
            for f in summary.get("floors", [])
        ]
        d_dict["multi_floor_summary"] = summary
        d_dict["has_image"] = d_dict.get("file_type") == "pdf"
        return d_dict


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


@app.get("/code-clauses")
def list_code_clauses(topic: str | None = None, occupancy: str | None = None) -> list[dict[str, Any]]:
    with db() as con:
        query = "SELECT * FROM code_clauses WHERE 1=1"
        params: list[Any] = []
        if topic:
            query += " AND topic = ?"
            params.append(topic)
        if occupancy:
            query += " AND occupancy LIKE ?"
            params.append(f"%{occupancy}%")
        query += " ORDER BY source_page, clause_id"
        return rows(con.execute(query, params).fetchall())


@app.get("/code-clauses/{clause_id}")
def get_code_clause(clause_id: str) -> dict[str, Any]:
    with db() as con:
        clause = con.execute("SELECT * FROM code_clauses WHERE clause_id = ?", (clause_id,)).fetchone()
    if not clause:
        raise HTTPException(404, "Code clause not found.")
    return dict(clause)
