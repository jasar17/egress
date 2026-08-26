from __future__ import annotations

import math
import sqlite3
import uuid
from typing import Any


def evaluate_fls_rules(
    parsed_data: dict[str, Any],
    con: sqlite3.Connection,
    drawing_id: str,
    element_id_map: dict[str, str],
    is_sprinklered: bool = True,
    occupancy_type: str = "Business - Regular office areas",
) -> list[dict[str, Any]]:
    """
    Evaluates real calculated geometry, path lengths, occupant loads, and corridor dimensions
    against official UAE Fire and Life Safety Code clauses from the database.
    Generates Violation records only for rooms/elements that exceed limits.
    Topics checked:
      1. travel_distance_to_exit
      2. two_exit_doors_required_by_area
      3. single_exit_door_permission
      4. number_of_exits
      5. exit_corridor_width
      6. exit_remoteness
    """
    cursor = con.cursor()
    cursor.execute("SELECT * FROM code_clauses")
    all_clauses = {r["clause_id"]: dict(r) for r in cursor.fetchall()}

    rooms = parsed_data.get("rooms", [])
    exits = parsed_data.get("exits", [])
    summary = parsed_data.get("summary", {})
    width_m = summary.get("width_m", 42.0)
    height_m = summary.get("height_m", 24.0)

    violations: list[dict[str, Any]] = []

    # 1. Fetch Applicable Code Clauses for each topic
    # Topic: travel_distance_to_exit
    travel_clause_id = "UAE-FLS-3.16-BUS-TD-S" if is_sprinklered else "UAE-FLS-3.16-BUS-TD-NS"
    travel_clause = all_clauses.get(travel_clause_id, {
        "clause_id": travel_clause_id,
        "value": 91.0 if is_sprinklered else 61.0,
        "unit": "m",
        "source_table": "Table 3.16",
        "source_page": 293,
        "occupancy": occupancy_type,
    })

    # Topic: two_exit_doors_required_by_area
    if "EDUCATIONAL" in occupancy_type.upper():
        area_clause_id = "UAE-FLS-3.20-EDU-ROOM-AREA"
    elif "HEALTH" in occupancy_type.upper() or "HOSPITAL" in occupancy_type.upper():
        area_clause_id = "UAE-FLS-3.22-HLTH-ROOM-AREA"
    else:
        area_clause_id = "UAE-FLS-3.19-BUS-ROOM-AREA"

    two_doors_area_clause = all_clauses.get(area_clause_id, {
        "clause_id": area_clause_id,
        "value": 280.0 if area_clause_id == "UAE-FLS-3.19-BUS-ROOM-AREA" else 93.0,
        "unit": "m2",
        "source_table": "Table 3.19" if area_clause_id == "UAE-FLS-3.19-BUS-ROOM-AREA" else ("Table 3.20" if area_clause_id == "UAE-FLS-3.20-EDU-ROOM-AREA" else "Table 3.22"),
        "source_page": 304 if area_clause_id == "UAE-FLS-3.19-BUS-ROOM-AREA" else (305 if area_clause_id == "UAE-FLS-3.20-EDU-ROOM-AREA" else 310),
        "occupancy": occupancy_type,
    })

    # Topic: single_exit_door_permission (Table 3.19 Item 1.i: <100 persons)
    single_door_clause = all_clauses.get("UAE-FLS-3.19-BUS-SINGLE-DOOR", {
        "clause_id": "UAE-FLS-3.19-BUS-SINGLE-DOOR",
        "value": 100.0,
        "unit": "max_occupant_load_for_single_exit",
        "source_table": "Table 3.19",
        "source_page": 304,
        "occupancy": occupancy_type,
    })

    # Topic: exit_corridor_width
    if "EDUCATIONAL" in occupancy_type.upper():
        corridor_clause_id = "UAE-FLS-3.21-CORRIDOR-EDU-DOUBLE"
    elif "HEALTH" in occupancy_type.upper() or "HOSPITAL" in occupancy_type.upper():
        corridor_clause_id = "UAE-FLS-3.22-CORRIDOR-HOSPITAL"
    else:
        corridor_clause_id = "UAE-FLS-3.8-CORRIDOR-WIDTH-MIN"

    corridor_width_clause = all_clauses.get(corridor_clause_id, {
        "clause_id": corridor_clause_id,
        "value": 1200.0 if corridor_clause_id == "UAE-FLS-3.8-CORRIDOR-WIDTH-MIN" else (2440.0 if corridor_clause_id == "UAE-FLS-3.22-CORRIDOR-HOSPITAL" else 3000.0),
        "unit": "mm",
        "source_table": "Table 3.8" if corridor_clause_id == "UAE-FLS-3.8-CORRIDOR-WIDTH-MIN" else ("Table 3.22" if corridor_clause_id == "UAE-FLS-3.22-CORRIDOR-HOSPITAL" else "Table 3.21"),
        "source_page": 276 if corridor_clause_id == "UAE-FLS-3.8-CORRIDOR-WIDTH-MIN" else (310 if corridor_clause_id == "UAE-FLS-3.22-CORRIDOR-HOSPITAL" else 307),
        "occupancy": occupancy_type,
    })

    # Topic: exit_remoteness
    remoteness_clause_id = "UAE-FLS-3.15A-REMOTE-LOWRISE-S" if is_sprinklered else "UAE-FLS-3.15A-REMOTE-LOWRISE-NS"
    remoteness_clause = all_clauses.get(remoteness_clause_id, {
        "clause_id": remoteness_clause_id,
        "value": 0.333 if is_sprinklered else 0.5,
        "unit": "fraction_of_floor_diagonal",
        "source_table": "Table 3.15.a",
        "source_page": 288,
        "occupancy": "Any - Lowrise / Midrise",
    })

    # --- TOPIC 1: travel_distance_to_exit ---
    max_travel_dist = float(travel_clause["value"])
    for room in rooms:
        travel_dist = float(room.get("travel_distance_m", 0.0))
        room_name = room.get("name", "Room")

        if travel_dist > max_travel_dist:
            v_id = f"V-{uuid.uuid4().hex[:6].upper()}"
            elem_id = element_id_map.get(room_name)
            svg_centroid = room.get("centroid", (50, 35))

            violations.append({
                "id": v_id,
                "drawing_id": drawing_id,
                "type": "Travel distance",
                "related_element_id": elem_id,
                "clause_ref": travel_clause["clause_id"],
                "measured_value": travel_dist,
                "measured_unit": "m",
                "limit_value": max_travel_dist,
                "limit_unit": "m",
                "severity": "Critical" if travel_dist > max_travel_dist * 1.1 else "High",
                "status": "open",
                "note": None,
                "geometry": {"type": "Point", "coordinates": list(svg_centroid)},
                "title": f"Travel distance exceeds maximum ({travel_dist}m > {max_travel_dist}m)",
                "detail": f"{room_name} - Travel distance to {room.get('nearest_exit', 'exit')} is {travel_dist}m, exceeding the allowable {max_travel_dist}m limit for {travel_clause.get('occupancy', occupancy_type)} ({'sprinklered' if is_sprinklered else 'non-sprinklered'}) per UAE FLS {travel_clause['source_table']} (Page {travel_clause['source_page']}).",
            })

    # --- TOPIC 2: two_exit_doors_required_by_area ---
    max_single_door_area = float(two_doors_area_clause["value"])
    for room in rooms:
        name_upper = room.get("name", "").upper()
        if "STAIR" in name_upper or "EXIT" in name_upper:
            continue

        area_m2 = float(room.get("area_m2", 0.0))
        room_name = room.get("name", "Room")
        elem_id = element_id_map.get(room_name)
        svg_centroid = room.get("centroid", (50, 35))

        if area_m2 > max_single_door_area:
            v_id = f"V-{uuid.uuid4().hex[:6].upper()}"
            violations.append({
                "id": v_id,
                "drawing_id": drawing_id,
                "type": "Two exit doors required by area",
                "related_element_id": elem_id,
                "clause_ref": two_doors_area_clause["clause_id"],
                "measured_value": area_m2,
                "measured_unit": "m2",
                "limit_value": max_single_door_area,
                "limit_unit": "m2",
                "severity": "Critical",
                "status": "open",
                "note": None,
                "geometry": {"type": "Point", "coordinates": list(svg_centroid)},
                "title": f"Room area exceeds single-door maximum ({area_m2} m2 > {max_single_door_area} m2)",
                "detail": f"{room_name} has a floor area of {area_m2} m2. Rooms exceeding {max_single_door_area} m2 require at least 2 remote exit doors per UAE FLS {two_doors_area_clause['source_table']} ({two_doors_area_clause['clause_id']}).",
            })

    # --- TOPIC 3: single_exit_door_permission ---
    single_door_threshold = float(single_door_clause["value"])

    for room in rooms:
        name_upper = room.get("name", "").upper()
        if "STAIR" in name_upper or "EXIT" in name_upper:
            continue

        occ_load = int(room.get("occupant_load", 0))
        room_name = room.get("name", "Room")
        elem_id = element_id_map.get(room_name)
        svg_centroid = room.get("centroid", (50, 35))

        if occ_load >= single_door_threshold:
            v_id = f"V-{uuid.uuid4().hex[:6].upper()}"
            violations.append({
                "id": v_id,
                "drawing_id": drawing_id,
                "type": "Single exit door permission",
                "related_element_id": elem_id,
                "clause_ref": single_door_clause["clause_id"],
                "measured_value": occ_load,
                "measured_unit": "persons",
                "limit_value": single_door_threshold,
                "limit_unit": "persons",
                "severity": "High",
                "status": "open",
                "note": None,
                "geometry": {"type": "Point", "coordinates": list(svg_centroid)},
                "title": f"Room occupant load exceeds single-door allowance ({occ_load} persons >= {int(single_door_threshold)})",
                "detail": f"{room_name} has an occupant load of {occ_load} persons. A single exit door is permitted only for rooms with an occupant load of less than {int(single_door_threshold)} persons discharging directly outside (travel distance <= 30m) per UAE FLS {single_door_clause['source_table']} ({single_door_clause['clause_id']}). At least 2 remote exit doors are required.",
            })

    # --- TOPIC 4: number_of_exits ---
    habitable_rooms = [r for r in rooms if "STAIR" not in r["name"].upper() and "EXIT" not in r["name"].upper()]
    total_floor_load = sum(r.get("occupant_load", 0) for r in habitable_rooms)
    exits_count = len(exits) if exits else 2  # Baseline stairs

    # Look up required exits from Table 3.14
    if total_floor_load > 1000:
        req_exits = 4
        exit_clause_id = "UAE-FLS-3.14-GT1000"
    elif total_floor_load >= 500:
        req_exits = 3
        exit_clause_id = "UAE-FLS-3.14-500-1000"
    else:
        req_exits = 2
        exit_clause_id = "UAE-FLS-3.14-LT500"

    exit_clause = all_clauses.get(exit_clause_id, {
        "clause_id": exit_clause_id,
        "value": req_exits,
        "unit": "exits",
        "source_table": "Table 3.14",
        "source_page": 287,
    })

    if exits_count < req_exits:
        v_id = f"V-{uuid.uuid4().hex[:6].upper()}"
        violations.append({
            "id": v_id,
            "drawing_id": drawing_id,
            "type": "Number of floor exits",
            "related_element_id": None,
            "clause_ref": exit_clause["clause_id"],
            "measured_value": exits_count,
            "measured_unit": "exits",
            "limit_value": req_exits,
            "limit_unit": "exits",
            "severity": "Critical",
            "status": "open",
            "note": None,
            "geometry": {"type": "Point", "coordinates": [50.0, 50.0]},
            "title": f"Insufficient exits for occupant load ({exits_count} < {req_exits} required)",
            "detail": f"Total floor occupant load of {total_floor_load} requires at least {req_exits} remote exits per UAE FLS {exit_clause['source_table']} ({exit_clause['clause_id']}), but only {exits_count} exits were provided.",
        })

    # --- TOPIC 5: exit_corridor_width ---
    base_corridor_width_limit = float(corridor_width_clause["value"])
    capacity_width_required = round(total_floor_load * 5.0, 1)  # 5.0 mm per person
    required_corridor_width = max(base_corridor_width_limit, capacity_width_required)

    measured_corridor_width = float(summary.get("corridor_width_mm") or (summary.get("corridor_width_m", 2.40) * 1000.0))

    if measured_corridor_width < required_corridor_width:
        v_id = f"V-{uuid.uuid4().hex[:6].upper()}"
        violations.append({
            "id": v_id,
            "drawing_id": drawing_id,
            "type": "Exit corridor width",
            "related_element_id": None,
            "clause_ref": corridor_clause_id,
            "measured_value": measured_corridor_width,
            "measured_unit": "mm",
            "limit_value": required_corridor_width,
            "limit_unit": "mm",
            "severity": "Critical" if measured_corridor_width < 1000.0 else "High",
            "status": "open",
            "note": None,
            "geometry": {"type": "Point", "coordinates": [50.0, 50.0]},
            "title": f"Exit corridor width is insufficient ({measured_corridor_width}mm < {required_corridor_width}mm)",
            "detail": f"Corridor clear width of {measured_corridor_width}mm is below the required width of {required_corridor_width}mm (minimum {base_corridor_width_limit}mm, capacity requirement {capacity_width_required}mm for {total_floor_load} occupants at 5mm/person) per UAE FLS {corridor_width_clause['source_table']} ({corridor_width_clause['clause_id']}).",
        })

    # --- TOPIC 6: exit_remoteness ---
    floor_diagonal = math.hypot(width_m, height_m)
    fraction = float(remoteness_clause["value"])
    min_separation_required = round(floor_diagonal * fraction, 2)

    # Measured separation between exit points
    if len(exits) >= 2:
        max_sep = 0.0
        for i in range(len(exits)):
            for j in range(i + 1, len(exits)):
                p1 = exits[i].get("pos") or [15.0, 50.0]
                p2 = exits[j].get("pos") or [85.0, 50.0]
                x1, y1 = (p1[0] / 100.0) * width_m, (p1[1] / 100.0) * height_m
                x2, y2 = (p2[0] / 100.0) * width_m, (p2[1] / 100.0) * height_m
                d = math.hypot(x2 - x1, y2 - y1)
                if d > max_sep:
                    max_sep = d
        stair_separation = round(max_sep, 2)
    else:
        stair_separation = round(width_m - 6.0, 2)

    if stair_separation < min_separation_required:
        v_id = f"V-{uuid.uuid4().hex[:6].upper()}"
        violations.append({
            "id": v_id,
            "drawing_id": drawing_id,
            "type": "Exit remoteness",
            "related_element_id": None,
            "clause_ref": remoteness_clause["clause_id"],
            "measured_value": stair_separation,
            "measured_unit": "m",
            "limit_value": min_separation_required,
            "limit_unit": "m",
            "severity": "High",
            "status": "open",
            "note": None,
            "geometry": {"type": "Point", "coordinates": [50.0, 50.0]},
            "title": f"Exit separation below remoteness minimum ({stair_separation}m < {min_separation_required}m)",
            "detail": f"Floor diagonal is {round(floor_diagonal, 1)}m. Exits must be separated by at least {fraction} of floor diagonal ({min_separation_required}m) per UAE FLS {remoteness_clause['source_table']} ({remoteness_clause['clause_id']}).",
        })

    return violations
