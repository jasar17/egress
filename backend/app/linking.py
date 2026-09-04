from __future__ import annotations

import json
import uuid
from typing import Any

from shapely.geometry import Point, Polygon
from app.db import now


import re

def link_fire_alarm_devices_to_rooms(
    project_id: str,
    con: Any,
    fa_drawing_id: str | None = None,
    arch_drawing_id: str | None = None
) -> list[dict[str, Any]]:
    """
    Cross-document entity linking:
    Connects fire alarm devices extracted from a fire_alarm shop drawing to room polygons
    extracted from the architectural floor plan of the same project using 2D point-in-polygon tests.
    
    Corridor spaces without explicit room polygons are classified as 'unassigned - corridor'.
    Results are persisted to the device_room_links table and denormalized into extracted_elements properties.
    """
    # 1. Resolve fire alarm drawing
    if not fa_drawing_id:
        fa_drawing = con.execute(
            "SELECT id, floor_name, file_url, file_type FROM drawings WHERE project_id = ? AND document_type = 'fire_alarm' ORDER BY created_at DESC LIMIT 1",
            (project_id,)
        ).fetchone()
        if not fa_drawing:
            return []
        fa_drawing_id = fa_drawing["id"]
    else:
        fa_drawing = con.execute(
            "SELECT id, floor_name, file_url, file_type FROM drawings WHERE id = ?",
            (fa_drawing_id,)
        ).fetchone()
        if not fa_drawing:
            return []

    # 2. Resolve matching architectural drawing
    if not arch_drawing_id or not str(arch_drawing_id).strip():
        raise ValueError("Explicit arch_drawing_id is strictly required to link fire alarm devices. Auto-selecting arbitrary architectural drawings is prohibited.")

    arch_drawing = con.execute(
        "SELECT id, floor_name, file_url, file_type FROM drawings WHERE id = ?",
        (arch_drawing_id.strip(),)
    ).fetchone()

    if not arch_drawing:
        raise ValueError(f"Specified architectural drawing '{arch_drawing_id}' does not exist in the database.")

    arch_drawing_id = arch_drawing["id"]

    # 3. Load architectural rooms (and exit stair enclosures if structured as polygons)
    arch_elements = con.execute(
        "SELECT id, name, type, geometry, properties FROM extracted_elements WHERE drawing_id = ? AND type IN ('room', 'exit')",
        (arch_drawing_id,)
    ).fetchall()

    room_polygons: list[dict[str, Any]] = []
    for r in arch_elements:
        try:
            geom = json.loads(r["geometry"])
            if geom.get("type") == "Polygon" and geom.get("coordinates"):
                poly = Polygon(geom["coordinates"][0])
                if not poly.is_valid:
                    poly = poly.buffer(0)
                room_polygons.append({
                    "id": r["id"],
                    "name": r["name"] or "Unknown Room",
                    "type": r["type"],
                    "polygon": poly,
                })
        except Exception:
            continue

    # 4. Load fire alarm devices
    fa_elements = con.execute(
        "SELECT id, name, type, geometry, properties FROM extracted_elements WHERE drawing_id = ? AND type != 'wall'",
        (fa_drawing_id,)
    ).fetchall()

    links: list[dict[str, Any]] = []

    # Clean previous links for this drawing to maintain idempotency
    con.execute("DELETE FROM device_room_links WHERE device_drawing_id = ?", (fa_drawing_id,))

    for dev in fa_elements:
        dev_id = dev["id"]
        dev_name = dev["name"]
        dev_type = dev["type"]
        geom = json.loads(dev["geometry"])
        props = json.loads(dev["properties"]) if dev["properties"] else {}

        tag = props.get("tag") or dev_name
        svg_coords = geom.get("coordinates", [50.0, 50.0])
        pos_m = props.get("pos_m") or props.get("raw_pos") or [0.0, 0.0]

        pt = Point(svg_coords[0], svg_coords[1])

        # Point-in-polygon test
        matched_room_id = None
        matched_room_name = None
        for room in room_polygons:
            if room["polygon"].contains(pt) or room["polygon"].touches(pt):
                matched_room_id = room["id"]
                matched_room_name = room["name"]
                break

        if matched_room_id:
            status = "assigned_room"
            assigned_room = matched_room_name
        else:
            status = "unassigned_corridor"
            assigned_room = "unassigned - corridor"

        link_id = str(uuid.uuid4())
        link_record = {
            "id": link_id,
            "project_id": project_id,
            "device_element_id": dev_id,
            "device_drawing_id": fa_drawing_id,
            "device_tag": tag,
            "device_type": dev_type,
            "room_element_id": matched_room_id,
            "room_drawing_id": arch_drawing_id,
            "room_name": assigned_room,
            "status": status,
            "x_m": pos_m[0] if len(pos_m) > 0 else None,
            "y_m": pos_m[1] if len(pos_m) > 1 else None,
            "svg_x": svg_coords[0],
            "svg_y": svg_coords[1],
            "created_at": now(),
        }

        # Insert into device_room_links
        con.execute(
            """
            INSERT INTO device_room_links (
                id, project_id, device_element_id, device_drawing_id, device_tag,
                device_type, room_element_id, room_drawing_id, room_name, status, x_m, y_m, svg_x, svg_y, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                link_id, project_id, dev_id, fa_drawing_id, tag,
                dev_type, matched_room_id, arch_drawing_id, assigned_room, status,
                link_record["x_m"], link_record["y_m"], link_record["svg_x"], link_record["svg_y"], link_record["created_at"]
            )
        )

        # Denormalize onto extracted_elements.properties
        props["linked_room_id"] = matched_room_id
        props["linked_room_name"] = assigned_room
        props["linking_status"] = status
        con.execute(
            "UPDATE extracted_elements SET properties = ? WHERE id = ?",
            (json.dumps(props), dev_id)
        )

        links.append(link_record)

    return links


def get_project_device_links(project_id: str, con: Any) -> list[dict[str, Any]]:
    """Retrieves all persisted device-room cross-document links for a project."""
    rows = con.execute(
        """
        SELECT * FROM device_room_links
        WHERE project_id = ?
        ORDER BY
            CASE
                WHEN device_tag LIKE 'SD-%' THEN 1
                WHEN device_tag LIKE 'HD-%' THEN 2
                WHEN device_tag LIKE 'MCP-%' THEN 3
                WHEN device_tag LIKE 'SN%-%' OR device_tag LIKE 'SB-%' THEN 4
                WHEN device_tag LIKE 'FACP-%' THEN 5
                ELSE 6
            END,
            device_tag ASC
        """,
        (project_id,)
    ).fetchall()
    return [dict(r) for r in rows]
