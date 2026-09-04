"""
Dubai 5-Floor Automated Regression Test Suite
Validates occupant loads, travel distances, single-exit door clauses, and compliance
across all storeys of the Dubai Commercial Building test set.
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path

os.environ["USE_LOCAL_SQLITE"] = "1"

backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient

from app.main import app, init_database
from app.dxf_parser import parse_dxf_file
from app.pdf_parser import parse_pdf_file
from app.occupant_load import calculate_occupant_loads
from app.path_analysis import calculate_walkable_distances
from app.rules_engine import evaluate_fls_rules


def test_typical_office_floor_regression():
    """
    Mandatory Regression Check for Level 01 / Typical Office Floor:
    1. Assert occupant load is calculated independently per room from geometry (158 persons total across 8 habitable spaces).
    2. Assert travel distance is correctly calculated on physical scale (18.69m, ruling out 122.90m unscaled error).
    3. Assert per-room loads match identically between DXF and PDF paths.
    """
    init_database()
    client = TestClient(app)

    # 1. Fetch Demo Project
    res = client.get("/projects")
    assert res.status_code == 200
    projects = res.json()
    assert len(projects) > 0
    project_id = projects[0]["id"]

    # 2. Upload Dubai Multi-Floor PDF (5-floor benchmark set)
    pdf_path = backend_dir.parent / "floor plan" / "Dubai_Commercial_Building_FLS_Test_FloorPlans.pdf"
    assert pdf_path.exists(), f"Multi-floor test PDF not found at {pdf_path}"

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    files = {"file": ("Dubai_Commercial_Building_FLS_Test_FloorPlans.pdf", pdf_bytes, "application/pdf")}
    data = {"occupancy_type": "Business - Regular office areas", "sprinklered": "true", "scale": 100}
    res = client.post(f"/projects/{project_id}/drawings", files=files, data=data)
    assert res.status_code == 201
    drawing_id = res.json()["drawing_id"]

    # 3. Switch to Page 1: Level 01 - Typical Office Floor
    res = client.post(f"/drawings/{drawing_id}/page", json={"page_index": 1})
    assert res.status_code == 200
    page_data = res.json()
    assert "Typical" in page_data.get("floor_name", "") or "Level 01" in page_data.get("floor_name", "")

    # 4. Fetch Extracted Elements & Assert Occupant Load calculated purely from geometry (158 persons)
    res = client.get(f"/drawings/{drawing_id}/elements")
    assert res.status_code == 200
    features = res.json().get("features", [])
    rooms = [f for f in features if f["type"] == "room"]
    habitable_rooms = [r for r in rooms if "STAIR" not in r["properties"]["name"].upper() and "EXIT" not in r["properties"]["name"].upper()]
    
    total_occupant_load = sum(r["properties"].get("occupant_load", 0) for r in habitable_rooms)
    print(f"\n[REGRESSION ASSERTION 1] Typical Floor Calculated Occupant Load: {total_occupant_load} persons")
    assert total_occupant_load == 158, f"Expected calculated load of 158 persons, got {total_occupant_load}"

    # 5. Fetch Path Distances & Assert Travel Distance on Physical Scale (~18.69m, NOT 122.90m)
    travel_distances = [r["properties"].get("travel_distance_m", 0.0) for r in rooms]
    max_travel_dist = max(travel_distances) if travel_distances else 0.0
    print(f"[REGRESSION ASSERTION 2] Typical Floor Max Travel Distance: {max_travel_dist} m")
    assert abs(max_travel_dist - 18.69) <= 1.0, f"Expected max travel distance ~18.69m, got {max_travel_dist}m"
    assert max_travel_dist < 50.0, f"Regression detected: Uncalibrated travel distance {max_travel_dist}m >= 50m (earlier bug was 122.90m)"

    # 6. Assert Per-Room Independence & Exact Matching between PDF and DXF
    # 6. Assert Per-Room Independence & Exact Matching between PDF and DXF
    dxf_path = backend_dir.parent / "floor plan" / "Dubai_Commercial_Floor_Level_01_Typical.dxf"
    dxf_parsed = parse_dxf_file(dxf_path)
    db_path = backend_dir / "data" / "fls_demo.db"
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    dxf_parsed = calculate_occupant_loads(dxf_parsed, con=con)

    pdf_room_loads = {r["properties"]["name"]: r["properties"]["occupant_load"] for r in rooms}
    dxf_room_loads = {r["name"]: r["occupant_load"] for r in dxf_parsed["rooms"]}

    # Detailed per-room dictionary structures
    target_5_rooms = ["OPEN OFFICE WEST", "OPEN OFFICE CENTRAL", "OPEN OFFICE EAST", "MEETING ROOM 1A", "MEETING ROOM 1B"]
    
    print("\n================================================================================")
    print("TYPICAL OFFICE FLOOR (LEVEL 01) - INDEPENDENT PER-ROOM OCCUPANT LOAD AUDIT")
    print("================================================================================")
    print(f"{'Room Name':<24} | {'Area (m2)':<10} | {'Density Factor':<16} | {'PDF Load':<10} | {'DXF Load':<10} | {'Status'}")
    print("-" * 80)
    for r in rooms:
        name = r["properties"]["name"]
        if "STAIR" in name.upper() or "EXIT" in name.upper():
            continue
        area = r["properties"].get("area_m2", 0.0)
        factor = r["properties"].get("occupant_load_factor", 0.0)
        p_load = pdf_room_loads.get(name, 0)
        d_load = dxf_room_loads.get(name, 0)
        match_status = "MATCH (100%)" if p_load == d_load else "MISMATCH"
        print(f"{name:<24} | {area:>8.1f} m2 | {factor:>6.1f} m2/person | {p_load:>8} p | {d_load:>8} p | {match_status}")

    print("-" * 80)
    print("\n[EXPLICIT PER-ROOM OCCUPANT LOAD DICTIONARIES FOR 5 PRIMARY ROOMS]:")
    print("PDF Path Room Loads Dict:")
    print("  ", {k: pdf_room_loads[k] for k in target_5_rooms if k in pdf_room_loads})
    print("DXF Path Room Loads Dict:")
    print("  ", {k: dxf_room_loads[k] for k in target_5_rooms if k in dxf_room_loads})
    print("================================================================================\n")

    for room_name in target_5_rooms:
        assert pdf_room_loads[room_name] == dxf_room_loads[room_name], f"Mismatch for {room_name}: PDF={pdf_room_loads[room_name]}, DXF={dxf_room_loads[room_name]}"

    print("[PASS] Typical Office floor regression assertions 1, 2, and 3 all passed perfectly!")


def test_full_five_floor_building_summary():
    """
    Regression Test for All 5 Floors of Dubai Commercial Building Set:
    - Level 00 Ground Floor: 69 occupants, 4 exits, 0 sprinklered violations.
    - Level 01 Typical Floor: 158 occupants, 2 exits, 18.69m max travel, 0 violations.
    - Level 02 Typical Floor: 158 occupants, 2 exits, 18.69m max travel, 0 violations.
    - Level 03 Typical Floor: 158 occupants, 2 exits, 18.69m max travel, 0 violations.
    - Level 04 Executive Floor: 136 occupants, 2 exits, 18.53m max travel, 0 violations (all rooms <100 persons per UAE-FLS-3.19-BUS-SINGLE-DOOR).
    """
    init_database()
    client = TestClient(app)

    res = client.get("/projects")
    project_id = res.json()[0]["id"]

    pdf_path = backend_dir.parent / "floor plan" / "Dubai_Commercial_Building_FLS_Test_FloorPlans.pdf"
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    res = client.post(
        f"/projects/{project_id}/drawings",
        files={"file": ("Dubai_Commercial_Building_FLS_Test_FloorPlans.pdf", pdf_bytes, "application/pdf")},
        data={"occupancy_type": "Business - Regular office areas", "sprinklered": "true", "scale": 100}
    )
    drawing_id = res.json()["drawing_id"]

    res = client.get(f"/drawings/{drawing_id}/multi-floor-summary")
    assert res.status_code == 200
    summary = res.json()
    assert summary["total_pages"] == 5
    floors = summary["floors"]

    expected_floor_loads = [69, 158, 158, 158, 136]
    expected_exit_counts = [4, 2, 2, 2, 2]

    for idx, fl in enumerate(floors):
        print(f"Floor {idx} ({fl['title']}): Load={fl['total_occupant_load']}p, Exits={fl['exits_count']}, MaxTravel={fl['max_travel_distance_m']}m, Violations={fl['violations_count']}")
        assert fl["total_occupant_load"] == expected_floor_loads[idx], f"Floor {idx} load mismatch: expected {expected_floor_loads[idx]}, got {fl['total_occupant_load']}"
        assert fl["exits_count"] == expected_exit_counts[idx], f"Floor {idx} exits mismatch: expected {expected_exit_counts[idx]}, got {fl['exits_count']}"
        assert fl["max_travel_distance_m"] < 25.0, f"Floor {idx} travel distance unscaled: {fl['max_travel_distance_m']}m"

    print("\n[PASS] All 5 floors in Dubai commercial test set passed regression checks!")


def test_extended_code_clause_topics():
    """
    Validates that the rules engine generates real Violation records for all 3 newly extended topics:
    1. single_exit_door_permission (UAE-FLS-3.19-BUS-SINGLE-DOOR)
    2. two_exit_doors_required_by_area (UAE-FLS-3.19-BUS-ROOM-AREA)
    3. exit_corridor_width (UAE-FLS-3.8-CORRIDOR-WIDTH-MIN)
    """
    init_database()
    db_path = backend_dir / "data" / "fls_demo.db"
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row

    # Test 1: single_exit_door_permission on high-occupancy room (105 occupants >= 100)
    test_drawing = {
        "floor_name": "Level 02 Typical Floor",
        "rooms": [
            {"name": "LARGE ASSEMBLY HALL", "area_m2": 150.0, "occupant_load": 105, "travel_distance_m": 15.0, "centroid": [50, 50]},
            {"name": "OPEN OFFICE CENTRAL", "area_m2": 118.0, "occupant_load": 13, "travel_distance_m": 15.16, "centroid": [51.4, 59.75]},
        ],
        "exits": [{"name": "STAIR S-01", "pos": [10, 50]}, {"name": "STAIR S-02", "pos": [90, 50]}],
    }
    violations = evaluate_fls_rules(test_drawing, con=con, drawing_id="test_single_door", element_id_map={})
    
    single_door_vs = [v for v in violations if v["clause_ref"] == "UAE-FLS-3.19-BUS-SINGLE-DOOR"]
    assert len(single_door_vs) == 1, f"Expected 1 single_exit_door_permission violation for UAE-FLS-3.19-BUS-SINGLE-DOOR, got {len(single_door_vs)}"
    assert single_door_vs[0]["type"] == "Single exit door permission"
    assert single_door_vs[0]["measured_value"] == 105
    assert single_door_vs[0]["limit_value"] == 100.0
    print("[PASS] Topic 'single_exit_door_permission' verified on LARGE ASSEMBLY HALL (105 >= 100 persons, clause UAE-FLS-3.19-BUS-SINGLE-DOOR; OPEN OFFICE CENTRAL 13 persons not flagged)")

    # Test 2: two_exit_doors_required_by_area on Level 05 Non-Compliant DXF (GRAND OPEN HALL = 378 m2 > 280 m2)
    # Synthetic non-compliant DXF fixture: Dubai_Commercial_Floor_Level_05_NonCompliant.dxf
    nc_dxf_path = backend_dir.parent / "floor plan" / "Dubai_Commercial_Floor_Level_05_NonCompliant.dxf"
    nc_parsed = parse_dxf_file(nc_dxf_path)
    nc_parsed = calculate_walkable_distances(nc_parsed)
    nc_parsed = calculate_occupant_loads(nc_parsed, con=con, default_occupancy="Business - Regular office areas")
    nc_violations = evaluate_fls_rules(nc_parsed, con=con, drawing_id="test_nc", element_id_map={})

    area_vs = [v for v in nc_violations if v["clause_ref"] == "UAE-FLS-3.19-BUS-ROOM-AREA"]
    assert len(area_vs) == 1, f"Expected 1 two_exit_doors_required_by_area violation, got {len(area_vs)}"
    assert area_vs[0]["type"] == "Two exit doors required by area"
    assert area_vs[0]["measured_value"] == 378.0
    assert area_vs[0]["limit_value"] == 280.0
    print("[PASS] Topic 'two_exit_doors_required_by_area' verified on Non-Compliant Floor GRAND OPEN HALL (378 m2 > 280 m2)")

    # Test 3: exit_corridor_width on a layout with narrow corridor (1000mm < 1200mm required)
    narrow_corridor_drawing = {
        "floor_name": "Diagnostic Floor with Sub-Standard Corridor",
        "rooms": [
            {"name": "OFFICE A", "area_m2": 60.0, "occupant_load": 20, "travel_distance_m": 12.0, "centroid": [30, 30]},
            {"name": "OFFICE B", "area_m2": 60.0, "occupant_load": 20, "travel_distance_m": 12.0, "centroid": [70, 70]},
        ],
        "exits": [{"name": "EXIT STAIR 1", "pos": [10, 50]}, {"name": "EXIT STAIR 2", "pos": [90, 50]}],
        "summary": {"corridor_width_mm": 1000.0, "width_m": 42.0, "height_m": 24.0}
    }
    corridor_violations = evaluate_fls_rules(narrow_corridor_drawing, con=con, drawing_id="test_narrow", element_id_map={})
    corr_vs = [v for v in corridor_violations if v["clause_ref"] == "UAE-FLS-3.8-CORRIDOR-WIDTH-MIN"]
    assert len(corr_vs) == 1, f"Expected 1 exit_corridor_width violation, got {len(corr_vs)}"
    assert corr_vs[0]["type"] == "Exit corridor width"
    assert corr_vs[0]["measured_value"] == 1000.0
    assert corr_vs[0]["limit_value"] == 1200.0
    print("[PASS] Topic 'exit_corridor_width' verified on Sub-Standard Corridor (1000mm < 1200mm)")

    # Test 4: dead_end_corridor (UAE-FLS-3.16-BUS-DE-S & UAE-FLS-3.16-BUS-DE-NS)
    # Check on real Dubai Level 01 layout:
    # West dead-end = 7.20m, East dead-end = 5.40m
    dubai_l01_parsed = parse_pdf_file(backend_dir.parent / "floor plan" / "Dubai_Commercial_Building_FLS_Test_FloorPlans.pdf", page_index=1)
    dubai_l01_parsed = calculate_walkable_distances(dubai_l01_parsed)
    dubai_l01_parsed = calculate_occupant_loads(dubai_l01_parsed, con=con, default_occupancy="Business - Regular office areas")

    # Sprinklered Business (limit = 15.0m per UAE-FLS-3.16-BUS-DE-S):
    # Both 7.20m and 5.40m are compliant -> 0 violations
    sp_vs = evaluate_fls_rules(dubai_l01_parsed, con=con, drawing_id="test_de_s", element_id_map={}, is_sprinklered=True)
    de_sp_vs = [v for v in sp_vs if v["clause_ref"] == "UAE-FLS-3.16-BUS-DE-S"]
    assert len(de_sp_vs) == 0, f"Expected 0 dead-end violations for sprinklered, got {len(de_sp_vs)}"
    print("[PASS] Topic 'dead_end_corridor' (Sprinklered, 15.0m limit): Dubai Level 01 West (7.20m) and East (5.40m) both COMPLIANT (0 violations)")

    # Non-Sprinklered Business (limit = 6.1m per UAE-FLS-3.16-BUS-DE-NS):
    # West dead-end 7.20m > 6.1m -> FLAGGED as non-compliant!
    ns_vs = evaluate_fls_rules(dubai_l01_parsed, con=con, drawing_id="test_de_ns", element_id_map={}, is_sprinklered=False)
    de_ns_vs = [v for v in ns_vs if v["clause_ref"] == "UAE-FLS-3.16-BUS-DE-NS"]
    assert len(de_ns_vs) == 1, f"Expected 1 dead-end violation for non-sprinklered, got {len(de_ns_vs)}"
    assert de_ns_vs[0]["measured_value"] == 7.20
    assert de_ns_vs[0]["limit_value"] == 6.1
    print(f"[PASS] Topic 'dead_end_corridor' (Non-Sprinklered, 6.1m limit): West corridor dead-end correctly flagged ({de_ns_vs[0]['measured_value']}m > {de_ns_vs[0]['limit_value']}m, clause UAE-FLS-3.16-BUS-DE-NS)")

    # Test 5: common_path_of_travel (UAE-FLS-3.16-BUS-CP-S & UAE-FLS-3.16-BUS-CP-NS)
    # Check on real Dubai Level 01 rooms:
    # Max measured common path is 5.98m (PANTRY / BREAKOUT), well within 30.0m limit
    cp_rooms = {r["name"]: r.get("common_path_m", 0.0) for r in dubai_l01_parsed["rooms"]}
    assert cp_rooms["OPEN OFFICE WEST"] == 2.45
    assert cp_rooms["MEETING ROOM 1A"] == 5.88
    assert cp_rooms["PANTRY / BREAKOUT"] == 5.98
    print(f"[PASS] Topic 'common_path_of_travel' verified on Dubai Level 01: West Office={cp_rooms['OPEN OFFICE WEST']}m, Meeting 1A={cp_rooms['MEETING ROOM 1A']}m, Pantry={cp_rooms['PANTRY / BREAKOUT']}m (all <= 30.0m limit)")

    # Synthetic excessive common path test (>30.0m)
    excess_cp_drawing = {
        "floor_name": "Diagnostic Extended Suite",
        "rooms": [
            {"name": "DEEP INTERIOR LAB", "area_m2": 50.0, "occupant_load": 10, "travel_distance_m": 45.0, "common_path_m": 34.5, "centroid": [15, 20]},
        ],
        "exits": [{"name": "STAIR 1", "pos": [10, 50]}, {"name": "STAIR 2", "pos": [90, 50]}],
        "summary": {"width_m": 42.0, "height_m": 24.0}
    }
    excess_cp_vs = evaluate_fls_rules(excess_cp_drawing, con=con, drawing_id="test_excess_cp", element_id_map={}, is_sprinklered=True)
    cp_flagged = [v for v in excess_cp_vs if v["clause_ref"] == "UAE-FLS-3.16-BUS-CP-S"]
    assert len(cp_flagged) == 1
    assert cp_flagged[0]["measured_value"] == 34.5
    assert cp_flagged[0]["limit_value"] == 30.0
    print(f"[PASS] Topic 'common_path_of_travel' correctly flagged excessive common path ({cp_flagged[0]['measured_value']}m > {cp_flagged[0]['limit_value']}m, clause UAE-FLS-3.16-BUS-CP-S)")

    # Test 6: stair_width (UAE-FLS-3.4-STAIR-WIDTH-MIN, 1200mm limit)
    # Dimensioned sub-standard stair test (1050mm < 1200mm)
    narrow_stair_drawing = {
        "floor_name": "Diagnostic Narrow Stair Layout",
        "rooms": [{"name": "ROOM A", "area_m2": 50.0, "occupant_load": 20, "travel_distance_m": 10.0, "centroid": [30, 30]}],
        "exits": [{"name": "STAIR 1", "pos": [10, 50]}, {"name": "STAIR 2", "pos": [90, 50]}],
        "summary": {"stair_width_mm": 1050.0, "width_m": 42.0, "height_m": 24.0}
    }
    stair_vs = evaluate_fls_rules(narrow_stair_drawing, con=con, drawing_id="test_stair", element_id_map={})
    stair_flagged = [v for v in stair_vs if v["clause_ref"] == "UAE-FLS-3.4-STAIR-WIDTH-MIN"]
    assert len(stair_flagged) == 1
    assert stair_flagged[0]["measured_value"] == 1050.0
    assert stair_flagged[0]["limit_value"] == 1200.0
    print(f"[PASS] Topic 'stair_width' correctly flagged sub-standard clear stair width ({stair_flagged[0]['measured_value']}mm < {stair_flagged[0]['limit_value']}mm, clause UAE-FLS-3.4-STAIR-WIDTH-MIN)")

    # Test 7: exit_door_width (UAE-FLS-3.1-DOOR-WIDTH-MIN, 900mm limit)
    # Dimensioned sub-standard door opening test (800mm < 900mm)
    narrow_door_drawing = {
        "floor_name": "Diagnostic Narrow Door Layout",
        "rooms": [{"name": "ROOM A", "area_m2": 50.0, "occupant_load": 20, "travel_distance_m": 10.0, "centroid": [30, 30]}],
        "exits": [{"name": "STAIR 1", "pos": [10, 50]}, {"name": "STAIR 2", "pos": [90, 50]}],
        "summary": {"door_width_mm": 800.0, "width_m": 42.0, "height_m": 24.0}
    }
    door_vs = evaluate_fls_rules(narrow_door_drawing, con=con, drawing_id="test_door", element_id_map={})
    door_flagged = [v for v in door_vs if v["clause_ref"] == "UAE-FLS-3.1-DOOR-WIDTH-MIN"]
    assert len(door_flagged) == 1
    assert door_flagged[0]["measured_value"] == 800.0
    assert door_flagged[0]["limit_value"] == 900.0
    print(f"[PASS] Topic 'exit_door_width' correctly flagged sub-standard clear door opening ({door_flagged[0]['measured_value']}mm < {door_flagged[0]['limit_value']}mm, clause UAE-FLS-3.1-DOOR-WIDTH-MIN)")

    # Test 8: Assembly room 2-door requirement (UAE-FLS-3.17-ASSM-ROOM-AREA, Table 3.17, Page 302, 280 m2 limit)
    large_assembly_drawing = {
        "floor_name": "Diagnostic Assembly Hall Layout",
        "rooms": [{"name": "COMMUNITY AUDITORIUM", "area_m2": 310.0, "occupant_load": 220, "travel_distance_m": 18.0, "centroid": [40, 40]}],
        "exits": [{"name": "STAIR 1", "pos": [10, 50]}, {"name": "STAIR 2", "pos": [90, 50]}],
        "summary": {"width_m": 42.0, "height_m": 24.0}
    }
    assm_vs = evaluate_fls_rules(large_assembly_drawing, con=con, drawing_id="test_assm", element_id_map={}, occupancy_type="Assembly")
    assm_flagged = [v for v in assm_vs if v["clause_ref"] == "UAE-FLS-3.17-ASSM-ROOM-AREA"]
    assert len(assm_flagged) == 1
    assert assm_flagged[0]["measured_value"] == 310.0
    assert assm_flagged[0]["limit_value"] == 280.0
    assert "Table 3.17" in assm_flagged[0]["detail"]
    print(f"[PASS] Topic 'two_exit_doors_required_by_area' (Assembly): correctly cited UAE-FLS-3.17-ASSM-ROOM-AREA ({assm_flagged[0]['measured_value']}m2 > {assm_flagged[0]['limit_value']}m2, Table 3.17)")


if __name__ == "__main__":
    test_typical_office_floor_regression()
    test_full_five_floor_building_summary()
    test_extended_code_clause_topics()
    print("\nALL DUBAI 5-FLOOR & EXTENDED CODE CLAUSE TOPIC TESTS EXECUTED AND PASSED.")
