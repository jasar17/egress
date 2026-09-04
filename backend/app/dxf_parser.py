from __future__ import annotations

import math
import re
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


def classify_fire_alarm_entity(layer: str, block_name: str = "") -> str | None:
    """
    Classifies fire alarm device type from layer and block reference name.
    Does NOT make hard assumptions on layer naming convention; matches standard
    MEP/AIA CAD conventions (e.g. FA-SMOKE, E-FA-SMOK, FIRE-ALARM-SMOKE, etc.).
    Returns device type string or None if not an alarm device.
    """
    l = normalize_layer_name(layer)
    b = (block_name or "").strip().upper()

    # 1. Smoke Detector
    if any(k in l for k in ["SMOKE", "SMOK", "DET-SMOKE", "OPTICAL", "PHOTOELECTRIC"]) or any(k in b for k in ["SMOKE", "SMOK", "DET-SMOKE"]):
        return "smoke_detector"
    if re.search(r'\bSD\b|FA[-_]SD|E[-_]FA[-_]SD', l) or re.search(r'\bSD\b', b):
        return "smoke_detector"

    # 2. Heat Detector
    if any(k in l for k in ["HEAT", "THERMAL", "DET-HEAT", "RATE-OF-RISE"]) or any(k in b for k in ["HEAT", "THERMAL"]):
        return "heat_detector"
    if re.search(r'\bHD\b|FA[-_]HD|E[-_]FA[-_]HD', l) or re.search(r'\bHD\b', b):
        return "heat_detector"

    # 3. Manual Call Point / Pull Station / Break Glass
    if any(k in l for k in ["MCP", "CALL-POINT", "CALL_POINT", "BREAK-GLASS", "BREAK_GLASS", "PULL-STATION", "PULL_STATION", "MANUAL-STATION", "MANUAL_CALL"]) or any(k in b for k in ["MCP", "CALL-POINT", "PULL"]):
        return "manual_call_point"
    if re.search(r'\bMCP\b|FA[-_]MCP|E[-_]FA[-_]MCP', l) or re.search(r'\bMCP\b', b):
        return "manual_call_point"

    # 4. Notification Appliance (Sounder / Horn / Strobe / Beacon / Bell)
    if any(k in l for k in ["SOUNDER", "HORN", "STROBE", "BELL", "BEACON", "ALARM-DEVICE", "AV-DEVICE", "NOTIFICATION"]) or any(k in b for k in ["SOUNDER", "HORN", "STROBE", "BELL"]):
        return "sounder"
    if re.search(r'\bSND\b|FA[-_]SND|FA[-_]AV|E[-_]FA[-_]SND', l) or re.search(r'\bSND\b', b):
        return "sounder"

    # 5. Fire Alarm Control Panel / Transponder / Repeater / Control Module
    if any(k in l for k in ["FACP", "FIRE-PANEL", "FIRE_PANEL", "MODULE", "CONTROL-UNIT"]) or any(k in b for k in ["FACP", "PANEL", "MODULE"]):
        return "fire_alarm_panel"
    if re.search(r'\bFACP\b|FA[-_]FACP|E[-_]FA[-_]FACP', l) or re.search(r'\bFACP\b', b):
        return "fire_alarm_panel"

    return None


def parse_fire_alarm_dxf_file(file_path: str | Path, drawing_scale: float = 100.0) -> dict[str, Any]:
    """
    Parses Fire Alarm / Detection Shop Drawings from AutoCAD DXF.
    Extracts point symbols (Smoke Detectors, Heat Detectors, Manual Call Points, Sounders, FACP)
    across standard layer naming conventions.
    Extracts device coordinates, physical meters, and normalized 0..100% coordinates.
    Extracts background walls if present for spatial reference.
    """
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

    raw_devices: list[dict[str, Any]] = []
    raw_walls: list[list[tuple[float, float]]] = []
    raw_texts: list[dict[str, Any]] = []

    # 1. Extract text entities for address matching
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
                "layer": text_entity.dxf.layer if hasattr(text_entity.dxf, "layer") else "",
            })
        except Exception:
            continue

    # 2. Extract devices and background walls from modelspace entities
    seen_positions: set[tuple[float, float, str]] = set()

    for entity in msp:
        dxftype = entity.dxftype()
        layer = entity.dxf.layer if hasattr(entity.dxf, "layer") else ""
        block_name = entity.dxf.name if hasattr(entity.dxf, "name") else ""

        device_type = classify_fire_alarm_entity(layer, block_name)

        if device_type:
            pos = None
            symbol_type = dxftype

            if dxftype == "POINT":
                pos = (float(entity.dxf.location.x), float(entity.dxf.location.y))
            elif dxftype == "INSERT":
                pos = (float(entity.dxf.insert.x), float(entity.dxf.insert.y))
            elif dxftype == "CIRCLE":
                pos = (float(entity.dxf.center.x), float(entity.dxf.center.y))
            elif dxftype in ("LWPOLYLINE", "POLYLINE"):
                pts = [(float(p[0]), float(p[1])) for p in entity.get_points()]
                if len(pts) >= 3:
                    cx = sum(p[0] for p in pts) / len(pts)
                    cy = sum(p[1] for p in pts) / len(pts)
                    pos = (cx, cy)

            if pos is not None:
                # Deduplicate: if POINT and CIRCLE/LWPOLYLINE were placed at the exact same location
                pos_key = (round(pos[0], 1), round(pos[1], 1), device_type)
                if pos_key not in seen_positions:
                    seen_positions.add(pos_key)
                    raw_devices.append({
                        "pos": pos,
                        "device_type": device_type,
                        "layer": layer,
                        "symbol_type": symbol_type,
                        "block_name": block_name,
                    })

        elif is_wall_layer(layer):
            if dxftype == "LINE":
                try:
                    start = (float(entity.dxf.start.x), float(entity.dxf.start.y))
                    end = (float(entity.dxf.end.x), float(entity.dxf.end.y))
                    raw_walls.append([start, end])
                except Exception:
                    pass
            elif dxftype in ("LWPOLYLINE", "POLYLINE"):
                try:
                    pts = [(float(p[0]), float(p[1])) for p in entity.get_points()]
                    if len(pts) >= 2:
                        for i in range(len(pts) - 1):
                            raw_walls.append([pts[i], pts[i + 1]])
                        if getattr(entity, "is_closed", False) or entity.dxf.flags & 1:
                            raw_walls.append([pts[-1], pts[0]])
                except Exception:
                    pass

    if not raw_devices:
        raise DXFParseError("No fire alarm devices (smoke detectors, heat detectors, manual call points) detected on drawing layers.")

    # 3. Associate nearby text tags with devices
    all_x: list[float] = [d["pos"][0] for d in raw_devices]
    all_y: list[float] = [d["pos"][1] for d in raw_devices]
    for seg in raw_walls:
        all_x.extend([seg[0][0], seg[1][0]])
        all_y.extend([seg[0][1], seg[1][1]])

    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    width = max(max_x - min_x, 10.0)
    height = max(max_y - min_y, 10.0)

    # Unit multiplier (mm to meters detection)
    if width > 500.0:
        unit_multiplier = 0.001
    else:
        unit_multiplier = 1.0

    match_threshold = 2500.0 if unit_multiplier == 0.001 else 2.5

    prefix_map = {
        "smoke_detector": "SD",
        "heat_detector": "HD",
        "manual_call_point": "MCP",
        "sounder": "SND",
        "fire_alarm_panel": "FACP",
    }
    type_counters: dict[str, int] = {}
    classified_devices: list[dict[str, Any]] = []
    used_text_indices: set[int] = set()

    for d in raw_devices:
        d_type = d["device_type"]
        type_counters[d_type] = type_counters.get(d_type, 0) + 1
        pos = d["pos"]

        best_text = None
        best_dist = float("inf")
        best_t_idx = -1

        for t_idx, t in enumerate(raw_texts):
            if t_idx in used_text_indices:
                continue
            dist = math.hypot(t["pos"][0] - pos[0], t["pos"][1] - pos[1])
            if dist < match_threshold and dist < best_dist:
                best_dist = dist
                best_text = t["text"]
                best_t_idx = t_idx

        if best_text and best_t_idx >= 0:
            tag = best_text
            used_text_indices.add(best_t_idx)
        else:
            tag = f"{prefix_map.get(d_type, 'DEV')}-{type_counters[d_type]:02d}"

        classified_devices.append({
            **d,
            "tag": tag,
        })

    def to_svg(x: float, y: float) -> list[float]:
        svg_x = ((x - min_x) / width) * 100.0
        svg_y = ((max_y - y) / height) * 100.0
        return [round(svg_x, 2), round(svg_y, 2)]

    def to_meters(x: float, y: float) -> list[float]:
        x_m = (x - min_x) * unit_multiplier
        y_m = (y - min_y) * unit_multiplier
        return [round(x_m, 2), round(y_m, 2)]

    # 4. Build output elements collection
    extracted_elements: list[tuple[str, str, dict[str, Any]]] = []

    # Devices
    for dev in classified_devices:
        pos = dev["pos"]
        svg_pos = to_svg(pos[0], pos[1])
        pos_m = to_meters(pos[0], pos[1])
        dev_type = dev["device_type"]
        tag = dev["tag"]

        extracted_elements.append((
            dev_type,
            tag,
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": svg_pos},
                "properties": {
                    "name": tag,
                    "tag": tag,
                    "device_type": dev_type,
                    "layer": dev["layer"],
                    "symbol_type": dev["symbol_type"],
                    "pos_m": pos_m,
                    "svg_pos": svg_pos,
                    "raw_pos": [round(pos[0] * unit_multiplier, 2), round(pos[1] * unit_multiplier, 2)],
                }
            }
        ))

    # Background Walls
    for i, seg in enumerate(raw_walls):
        svg_line = [to_svg(seg[0][0], seg[0][1]), to_svg(seg[1][0], seg[1][1])]
        extracted_elements.append((
            "wall",
            f"Wall-{i+1}",
            {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": svg_line},
                "properties": {"name": f"Wall-{i+1}", "is_background": True},
            }
        ))

    device_counts = {
        "smoke_detectors": sum(1 for d in classified_devices if d["device_type"] == "smoke_detector"),
        "heat_detectors": sum(1 for d in classified_devices if d["device_type"] == "heat_detector"),
        "manual_call_points": sum(1 for d in classified_devices if d["device_type"] == "manual_call_point"),
        "sounders": sum(1 for d in classified_devices if d["device_type"] == "sounder"),
        "panels": sum(1 for d in classified_devices if d["device_type"] == "fire_alarm_panel"),
    }

    layers_detected = sorted(list(set(d["layer"] for d in classified_devices)))

    return {
        "document_type": "fire_alarm",
        "elements": extracted_elements,
        "devices": classified_devices,
        "summary": {
            "document_type": "fire_alarm",
            "devices_count": len(classified_devices),
            **device_counts,
            "walls_count": len(raw_walls),
            "rooms_count": 0,
            "doors_count": 0,
            "exits_count": 0,
            "layers_detected": layers_detected,
            "width_m": round(width * unit_multiplier, 2),
            "height_m": round(height * unit_multiplier, 2),
            "unit_multiplier": unit_multiplier,
        },
        "rooms": [],
        "exits": [],
    }
