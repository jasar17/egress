from __future__ import annotations

import math
import sqlite3
from typing import Any


def calculate_occupant_loads(
    parsed_data: dict[str, Any],
    con: sqlite3.Connection,
    default_occupancy: str = "Business - Regular office areas",
) -> dict[str, Any]:
    """
    Calculates the real occupant load independently for EACH extracted room
    using its actual geometry floor area (m2) and the official occupant load factor
    from UAE Fire & Life Safety Code Table 3.13.

    POLICY FIX: Pre-written drawing text/labels (e.g. 'Occ: 79') are NEVER trusted.
    All occupant loads are calculated purely from physical room geometry and code factors.
    """
    cursor = con.cursor()
    cursor.execute(
        "SELECT clause_id, topic, occupancy, requirement_type, value, unit, source_table, source_page FROM code_clauses WHERE topic = 'occupant_load_factor'"
    )
    clauses = [dict(r) for r in cursor.fetchall()]
    clauses_by_id = {c["clause_id"]: c for c in clauses}

    # Baseline fallback clause
    regular_bus_clause = clauses_by_id.get("UAE-FLS-3.13-BUS-REG", {
        "clause_id": "UAE-FLS-3.13-BUS-REG",
        "occupancy": "Business - Regular office areas",
        "value": 9.3,
        "unit": "m2_per_person",
        "source_table": "Table 3.13",
        "source_page": 285,
    })

    rooms = parsed_data.get("rooms", [])
    updated_rooms: list[dict[str, Any]] = []

    for room in rooms:
        area_m2 = float(room.get("area_m2", 0.0))
        name = room.get("name", "").upper()

        if "STAIR" in name or "EXIT" in name:
            # Egress stairs / exits do not generate occupant load
            factor = float(regular_bus_clause["value"])
            clause_to_use = regular_bus_clause
            occ_load = 0
            occ_load_exact = 0.0
            is_assumed = False
            note = "Egress enclosure - 0 occupant load generated"
        elif "MULTI-PURPOSE" in name or "AUDITORIUM" in name:
            clause_to_use = clauses_by_id.get("UAE-FLS-3.13-ASSM-CONC", regular_bus_clause)
            factor = float(clause_to_use["value"])
            is_assumed = False
            occ_load_exact = round(area_m2 / factor, 2)
            occ_load = math.ceil(area_m2 / factor)
            note = f"{area_m2} m2 / {factor} m2/p = {occ_load_exact} ({occ_load} occupants) per UAE FLS {clause_to_use['source_table']} ({clause_to_use['clause_id']})"
        elif "PANTRY" in name or "BREAKOUT" in name or "CAFE" in name or "DINING" in name or "LOUNGE" in name:
            clause_to_use = clauses_by_id.get("UAE-FLS-3.13-ASSM-LESS-CONC", regular_bus_clause)
            factor = float(clause_to_use["value"])
            is_assumed = False
            occ_load_exact = round(area_m2 / factor, 2)
            occ_load = math.ceil(area_m2 / factor)
            note = f"{area_m2} m2 / {factor} m2/p = {occ_load_exact} ({occ_load} occupants) per UAE FLS {clause_to_use['source_table']} ({clause_to_use['clause_id']})"
        elif "RETAIL" in name or "SHOP" in name or "MERCANTILE" in name:
            clause_to_use = clauses_by_id.get("UAE-FLS-3.13-MERC-STREET", regular_bus_clause)
            factor = float(clause_to_use["value"])
            is_assumed = False
            occ_load_exact = round(area_m2 / factor, 2)
            occ_load = math.ceil(area_m2 / factor)
            note = f"{area_m2} m2 / {factor} m2/p = {occ_load_exact} ({occ_load} occupants) per UAE FLS {clause_to_use['source_table']} ({clause_to_use['clause_id']})"
        elif "STORAGE" in name or "SERVER" in name or "PLANT" in name or "BOH" in name or "SERVICE" in name:
            clause_to_use = clauses_by_id.get("UAE-FLS-3.13-STOR-GEN", regular_bus_clause)
            factor = float(clause_to_use["value"])
            is_assumed = False
            occ_load_exact = round(area_m2 / factor, 2)
            occ_load = math.ceil(area_m2 / factor)
            note = f"{area_m2} m2 / {factor} m2/p = {occ_load_exact} ({occ_load} occupants) per UAE FLS {clause_to_use['source_table']} ({clause_to_use['clause_id']})"
        elif "MEETING" in name or "BOARDROOM" in name or "CONFERENCE" in name:
            clause_to_use = clauses_by_id.get("UAE-FLS-3.13-ASSM-LESS-CONC", regular_bus_clause)
            factor = float(clause_to_use["value"])
            is_assumed = False
            occ_load_exact = round(area_m2 / factor, 2)
            occ_load = math.ceil(area_m2 / factor)
            note = f"{area_m2} m2 / {factor} m2/p = {occ_load_exact} ({occ_load} occupants) per UAE FLS {clause_to_use['source_table']} ({clause_to_use['clause_id']})"
        elif "CONCENTRATED" in name or "OPEN PLAN" in name or "WORKSTATION" in name or "DENSE" in name:
            clause_to_use = clauses_by_id.get("UAE-FLS-3.13-BUS-CONC", regular_bus_clause)
            factor = float(clause_to_use["value"])
            is_assumed = False
            occ_load_exact = round(area_m2 / factor, 2)
            occ_load = math.ceil(area_m2 / factor)
            note = f"{area_m2} m2 / {factor} m2/p = {occ_load_exact} ({occ_load} occupants) per UAE FLS {clause_to_use['source_table']} ({clause_to_use['clause_id']})"
        elif "OFFICE" in name or "CABIN" in name:
            clause_to_use = regular_bus_clause
            factor = float(clause_to_use["value"])
            is_assumed = False
            occ_load_exact = round(area_m2 / factor, 2)
            occ_load = math.ceil(area_m2 / factor)
            note = f"{area_m2} m2 / {factor} m2/p = {occ_load_exact} ({occ_load} occupants) per UAE FLS {clause_to_use['source_table']} ({clause_to_use['clause_id']})"
        else:
            # Default Business Regular Office (9.3 m2/person)
            clause_to_use = regular_bus_clause
            factor = float(clause_to_use["value"])
            is_assumed = True
            occ_load_exact = round(area_m2 / factor, 2)
            occ_load = math.ceil(area_m2 / factor)
            note = (
                f"{area_m2} m2 / {factor} m2/person = {occ_load_exact} ({occ_load} occupants) "
                f"per UAE FLS {clause_to_use['source_table']} ({clause_to_use['clause_id']}) [Defaulted Assumption]"
            )

        updated_room = {
            **room,
            "area_m2": area_m2,
            "occupant_load": occ_load,
            "occupant_load_exact": occ_load_exact,
            "occupant_load_factor": factor,
            "occupancy_type": clause_to_use["occupancy"],
            "occupancy_clause_id": clause_to_use["clause_id"],
            "occupancy_assumed": is_assumed,
            "occupancy_note": note,
        }
        updated_rooms.append(updated_room)

    # Update extracted_elements feature properties
    room_map = {r["name"]: r for r in updated_rooms}
    updated_elements: list[tuple[str, str, dict[str, Any]]] = []

    for item_type, name, feature_dict in parsed_data.get("elements", []):
        props = feature_dict.get("properties", {})
        if item_type == "room" and name in room_map:
            rm = room_map[name]
            props["area_m2"] = rm["area_m2"]
            props["occupant_load"] = rm["occupant_load"]
            props["occupant_load_exact"] = rm["occupant_load_exact"]
            props["occupant_load_factor"] = rm["occupant_load_factor"]
            props["occupancy_type"] = rm["occupancy_type"]
            props["occupancy_clause_id"] = rm["occupancy_clause_id"]
            props["occupancy_assumed"] = rm["occupancy_assumed"]
            props["occupancy_note"] = rm["occupancy_note"]
        feature_dict["properties"] = props
        updated_elements.append((item_type, name, feature_dict))

    parsed_data["elements"] = updated_elements
    parsed_data["rooms"] = updated_rooms
    return parsed_data
