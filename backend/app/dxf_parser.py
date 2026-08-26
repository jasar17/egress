from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import ezdxf
from shapely.geometry import LineString, Point, Polygon


class DXFParseError(Exception):
    """Raised when DXF parsing fails or finds no usable geometry."""
    pass


def normalize_layer_name(layer: str) -> str:
    return (layer or "").strip().upper()


def is_wall_layer(layer: str) -> bool:
    l = normalize_layer_name(layer)
    if any(k in l for k in ["WALL", "W_EXT", "W_INT", "PARTITION", "PERIMETER", "STRUCTURE", "ARCH-WALL", "A-WALL"]):
        return True
    return False


def is_room_layer(layer: str) -> bool:
    l = normalize_layer_name(layer)
    return any(k in l for k in ["ROOM", "SPACE", "AREA", "ZONE", "BOUNDARY", "A-AREA", "A-ROOM", "OFFICE", "TENANT"])


def is_door_layer(layer: str) -> bool:
    l = normalize_layer_name(layer)
    return any(k in l for k in ["DOOR", "A-DOOR", "DR", "OPENING", "PORT"])


def is_exit_layer(layer: str) -> bool:
    l = normalize_layer_name(layer)
    return any(k in l for k in ["EXIT", "STAIR", "EGRESS", "ESCAPE", "FIRE_EXIT", "CORE", "S-01", "S-02"])


def parse_dxf_file(file_path: str | Path, drawing_scale: float = 100.0) -> dict[str, Any]:
    path = Path(file_path)
    if not path.exists():
        raise DXFParseError(f"File not found: {path}")

    try:
        doc = ezdxf.readfile(str(path))
    except Exception as exc:
        raise DXFParseError(f"Could not open DXF file: {exc}") from exc

    msp = doc.modelspace()
    if msp is None:
        raise DXFParseError("DXF file has no modelspace.")

    raw_walls: list[list[tuple[float, float]]] = []
    raw_rooms: list[dict[str, Any]] = []
    raw_doors: list[dict[str, Any]] = []
    raw_exits: list[dict[str, Any]] = []
    raw_texts: list[dict[str, Any]] = []

    # 1. Extract texts for labeling
    for text_entity in msp.query("TEXT MTEXT"):
        try:
            content = text_entity.dxf.text if hasattr(text_entity.dxf, "text") else getattr(text_entity, "text", "")
            if not content and hasattr(text_entity, "plain_text"):
                content = text_entity.plain_text()
            content = str(content).strip()
            if not content:
                continue

            insert = text_entity.dxf.insert
            raw_texts.append({
                "text": content,
                "pos": (float(insert[0]), float(insert[1])),
                "layer": text_entity.dxf.layer,
            })
        except Exception:
            continue

    # 2. Extract Lines and Polylines
    for entity in msp:
        dxftype = entity.dxftype()
        layer = entity.dxf.layer if hasattr(entity.dxf, "layer") else ""

        if dxftype == "LINE":
            try:
                start = (float(entity.dxf.start.x), float(entity.dxf.start.y))
                end = (float(entity.dxf.end.x), float(entity.dxf.end.y))
                if is_door_layer(layer):
                    raw_doors.append({"pos": ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2), "layer": layer, "is_exit": is_exit_layer(layer)})
                elif is_exit_layer(layer):
                    raw_exits.append({"pos": ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2), "name": layer, "layer": layer})
                else:
                    raw_walls.append([start, end])
            except Exception:
                continue

        elif dxftype in ("LWPOLYLINE", "POLYLINE"):
            try:
                points = [(float(p[0]), float(p[1])) for p in entity.get_points(format="xy")]
                if len(points) < 2:
                    continue

                is_closed = getattr(entity, "is_closed", False) or getattr(entity.dxf, "flags", 0) & 1 == 1
                if is_closed and len(points) >= 3 and (is_room_layer(layer) or not is_wall_layer(layer)):
                    poly_pts = points[:]
                    if poly_pts[0] != poly_pts[-1]:
                        poly_pts.append(poly_pts[0])
                    raw_rooms.append({
                        "points": poly_pts,
                        "layer": layer,
                        "name": None,
                    })
                elif is_exit_layer(layer):
                    cx = sum(p[0] for p in points) / len(points)
                    cy = sum(p[1] for p in points) / len(points)
                    raw_exits.append({"pos": (cx, cy), "name": layer, "layer": layer})
                else:
                    raw_walls.append(points)
            except Exception:
                continue

        elif dxftype == "INSERT":
            # Block reference (e.g. door or exit block)
            try:
                block_name = entity.dxf.name
                insert = (float(entity.dxf.insert.x), float(entity.dxf.insert.y))
                if is_exit_layer(block_name) or is_exit_layer(layer):
                    raw_exits.append({"pos": insert, "name": block_name, "layer": layer})
                elif is_door_layer(block_name) or is_door_layer(layer):
                    raw_doors.append({"pos": insert, "name": block_name, "layer": layer, "is_exit": False})
            except Exception:
                continue

        elif dxftype in ("ARC", "CIRCLE"):
            try:
                center = (float(entity.dxf.center.x), float(entity.dxf.center.y))
                if is_door_layer(layer):
                    raw_doors.append({"pos": center, "layer": layer, "is_exit": False})
                elif is_exit_layer(layer):
                    raw_exits.append({"pos": center, "name": layer, "layer": layer})
            except Exception:
                continue

    # If no explicit rooms were parsed from room layers, attempt building rooms from closed polygons or building envelope
    all_points: list[tuple[float, float]] = []
    for w in raw_walls:
        all_points.extend(w)
    for r in raw_rooms:
        all_points.extend(r["points"])
    for d in raw_doors:
        all_points.append(d["pos"])
    for e in raw_exits:
        all_points.append(e["pos"])

    if not all_points:
        raise DXFParseError("DXF drawing is empty or contains no parseable 2D geometry.")

    xs = [p[0] for p in all_points]
    ys = [p[1] for p in all_points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    width = max_x - min_x
    height = max_y - min_y

    if width <= 0 or height <= 0:
        raise DXFParseError("Invalid DXF bounds: geometry has zero width or height.")

    # Detect drawing unit: if bounds > 500, drawing is in millimeters -> scale to meters
    unit_multiplier = 0.001 if max(width, height) > 500.0 else 1.0

    # Match room names from raw_texts
    named_rooms: list[dict[str, Any]] = []
    for r_idx, r in enumerate(raw_rooms):
        poly_pts = r["points"]
        try:
            poly = Polygon(poly_pts)
            if not poly.is_valid:
                poly = poly.buffer(0)
            area_m2 = poly.area * (unit_multiplier ** 2)
            centroid = (poly.centroid.x, poly.centroid.y)
        except Exception:
            centroid = (sum(p[0] for p in poly_pts) / len(poly_pts), sum(p[1] for p in poly_pts) / len(poly_pts))
            area_m2 = 10.0

        # Find best text label within or closest to polygon
        best_name = None
        min_dist = float("inf")
        for t in raw_texts:
            t_pt = Point(t["pos"])
            t_text = t["text"].strip()
            # Ignore purely numeric or dimension texts
            if t_text.replace(".", "").replace("m", "").replace("2", "").isdigit() or "OCC:" in t_text.upper():
                continue
            try:
                if 'poly' in locals() and poly.contains(t_pt):
                    best_name = t_text
                    break
                dist = math.hypot(centroid[0] - t["pos"][0], centroid[1] - t["pos"][1])
                if dist < min_dist:
                    min_dist = dist
                    best_name = t_text
            except Exception:
                pass

        room_name = best_name or f"Room {r_idx + 1}"
        named_rooms.append({
            "name": room_name,
            "points": poly_pts,
            "area_m2": round(area_m2, 2),
            "centroid": centroid,
            "layer": r["layer"],
        })

    # If raw_exits is empty, check if any door is labeled EXIT or near stairs
    if not raw_exits:
        for t in raw_texts:
            if "EXIT" in t["text"].upper() or "STAIR" in t["text"].upper() or "S-01" in t["text"].upper() or "S-02" in t["text"].upper():
                raw_exits.append({"pos": t["pos"], "name": t["text"], "layer": t.get("layer", "EXIT")})

    # Coordinate Normalization for SVG Viewer (Canvas: 0 0 100 100)
    # 5% padding to keep drawings neatly framed
    pad_x = 5.0
    pad_y = 5.0
    draw_w = 90.0
    draw_h = 90.0

    def to_svg(x: float, y: float) -> list[float]:
        nx = pad_x + ((x - min_x) / width) * draw_w
        # Flip Y so CAD +Y (up) maps to SVG +Y (down)
        ny = pad_y + ((max_y - y) / height) * draw_h
        return [round(nx, 2), round(ny, 2)]

    extracted_elements: list[tuple[str, str, dict[str, Any]]] = []

    # 1. Perimeter / Building walls
    for w_idx, pts in enumerate(raw_walls):
        svg_coords = [to_svg(p[0], p[1]) for p in pts]
        geom_type = "LineString" if len(svg_coords) > 1 else "Point"
        extracted_elements.append((
            "wall",
            f"Wall {w_idx + 1}",
            {
                "type": "Feature",
                "geometry": {"type": geom_type, "coordinates": svg_coords if geom_type == "LineString" else svg_coords[0]},
                "properties": {"name": f"Wall {w_idx + 1}", "raw_length_m": round(math.dist(pts[0], pts[-1]) * unit_multiplier, 2) if len(pts) > 1 else 0},
            }
        ))

    # 2. Rooms
    normalized_rooms: list[dict[str, Any]] = []
    for r in named_rooms:
        svg_coords = [[to_svg(p[0], p[1]) for p in r["points"]]]
        svg_centroid = to_svg(r["centroid"][0], r["centroid"][1])
        raw_centroid = [round(r["centroid"][0] * unit_multiplier, 2), round(r["centroid"][1] * unit_multiplier, 2)]
        
        extracted_elements.append((
            "room",
            r["name"],
            {
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": svg_coords},
                "properties": {
                    "name": r["name"],
                    "area_m2": r["area_m2"],
                    "raw_centroid": raw_centroid,
                    "centroid": svg_centroid,
                    "svg_centroid": svg_centroid,
                }
            }
        ))
        normalized_rooms.append({
            **r,
            "centroid": svg_centroid,
            "raw_centroid": raw_centroid,
            "svg_centroid": svg_centroid,
            "svg_coords": svg_coords[0],
        })

    # 3. Doors
    for d_idx, d in enumerate(raw_doors):
        svg_pos = to_svg(d["pos"][0], d["pos"][1])
        name = d.get("name") or f"Door {d_idx + 1}"
        extracted_elements.append((
            "door",
            name,
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": svg_pos},
                "properties": {"name": name, "is_exit": d.get("is_exit", False)},
            }
        ))

    # 4. Exits
    normalized_exits: list[dict[str, Any]] = []
    for e_idx, e in enumerate(raw_exits):
        svg_pos = to_svg(e["pos"][0], e["pos"][1])
        name = e.get("name") or f"Exit {e_idx + 1}"
        extracted_elements.append((
            "exit",
            name,
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": svg_pos},
                "properties": {"name": name, "is_exit": True},
            }
        ))
        normalized_exits.append({
            **e,
            "pos": svg_pos,
            "raw_pos": svg_pos,
        })

    return {
        "elements": extracted_elements,
        "summary": {
            "walls_count": len(raw_walls),
            "rooms_count": len(named_rooms),
            "doors_count": len(raw_doors),
            "exits_count": len(raw_exits),
            "width_m": round(width * unit_multiplier, 2),
            "height_m": round(height * unit_multiplier, 2),
            "unit_multiplier": unit_multiplier,
            "corridor_width_m": 2.40,
            "corridor_width_mm": 2400.0,
        },
        "rooms": normalized_rooms,
        "exits": normalized_exits,
    }
