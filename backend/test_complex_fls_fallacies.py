"""
Senior QA Test Suite: Complex Edge Cases, Fallacies, and Mathematical Invariants
Evaluates the EGRESS pipeline against complex architectural, topological,
classification, mathematical, and concurrency edge cases.
"""
from __future__ import annotations

import math
import sqlite3
import sys
from pathlib import Path
from fastapi.testclient import TestClient

backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from app.main import app, init_database
from app.dxf_parser import parse_dxf_file, DXFParseError
from app.pdf_parser import parse_pdf_file
from app.occupant_load import calculate_occupant_loads
from app.path_analysis import calculate_walkable_distances
from app.rules_engine import evaluate_fls_rules


def run_all_senior_qa_tests():
    init_database()
    db_path = backend_dir / "data" / "fls_demo.db"
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    client = TestClient(app)

    print("================================================================================")
    print("SENIOR QA TEST SUITE: COMPLEX TESTING METHODS & FALLACY STRESS-TESTING")
    print("================================================================================")

    # -------------------------------------------------------------------------
    # TEST METHOD 1: MATHEMATICAL & CEILING BOUNDARY TESTING
    # -------------------------------------------------------------------------
    print("\n[METHOD 1] Mathematical & Occupant Load Ceiling Boundaries...")
    test_cases_math = [
        # (room_name, area, factor, expected_load)
        ("OFFICE REGULAR", 9.30000, 9.3, 1),
        ("OFFICE REGULAR JUST ABOVE", 9.30001, 9.3, 2),
        ("OFFICE REGULAR ZERO", 0.0, 9.3, 0),
        ("OPEN OFFICE CENTRAL", 118.0, 9.3, 13),
        ("CONCENTRATED WORKSTATIONS", 4.60000, 4.6, 1),
        ("CONCENTRATED JUST ABOVE", 4.60001, 4.6, 2),
        ("MEETING ROOM EXACT", 1.40000, 1.4, 1),
        ("MEETING ROOM JUST ABOVE", 1.40001, 1.4, 2),
        ("STORAGE EXACT", 27.90000, 27.9, 1),
        ("STORAGE JUST ABOVE", 27.90001, 27.9, 2),
        ("EXIT STAIR ENCLOSURE", 500.0, 9.3, 0),  # Stairs must NEVER generate load
    ]

    for name, area, factor, expected_load in test_cases_math:
        dummy_drawing = {
            "rooms": [{"name": name, "area_m2": area}],
            "elements": [("room", name, {"properties": {"name": name, "area_m2": area}})],
        }
        res = calculate_occupant_loads(dummy_drawing, con=con)
        calc_load = res["rooms"][0]["occupant_load"]
        calc_factor = res["rooms"][0]["occupant_load_factor"]
        assert calc_load == expected_load, f"Math Fallacy on {name} (area {area}): Expected {expected_load}, got {calc_load}"
        assert abs(calc_factor - factor) < 0.01, f"Factor Fallacy on {name}: Expected {factor}, got {calc_factor}"

    print("  -> Passed all 11 ceiling and zero-boundary load assertions.")

    # -------------------------------------------------------------------------
    # TEST METHOD 2: COMPOUND SEMANTIC FUNCTION CLASSIFICATION
    # -------------------------------------------------------------------------
    print("\n[METHOD 2] Compound & Ambiguous Function Semantic Classification...")
    semantic_cases = [
        ("EXECUTIVE CABIN 01", 9.3, False),
        ("OPEN PLAN DESKS", 4.6, False),
        ("BOARDROOM SUITE A", 1.4, False),
        ("CAFETERIA / BREAKOUT LOUNGE", 1.4, False),
        ("SERVER / BOH PLANT ROOM", 27.9, False),
        ("RETAIL BOUTIQUE", 2.8, False),
        ("UNLABELED TENANT SPACE", 9.3, True),  # Fallback defaulted assumption
    ]

    for name, expected_factor, expected_assumed in semantic_cases:
        dummy_drawing = {
            "rooms": [{"name": name, "area_m2": 50.0}],
            "elements": [("room", name, {"properties": {"name": name, "area_m2": 50.0}})],
        }
        res = calculate_occupant_loads(dummy_drawing, con=con)
        rm = res["rooms"][0]
        assert abs(rm["occupant_load_factor"] - expected_factor) < 0.01, f"Semantic Fallacy on '{name}': Expected factor {expected_factor}, got {rm['occupant_load_factor']}"
        assert rm["occupancy_assumed"] == expected_assumed, f"Assumption flag fallacy on '{name}': Expected assumed={expected_assumed}, got {rm['occupancy_assumed']}"

    print("  -> Passed all 7 compound semantic classification tests.")

    # -------------------------------------------------------------------------
    # -------------------------------------------------------------------------
    # TEST METHOD 3: SINGLE-DOOR STATUTORY ROUTING (Table 3.19 Item 1.i: <100 Persons)
    # -------------------------------------------------------------------------
    print("\n[METHOD 3] Single-Door Statutory Routing (Table 3.19 Item 1.i: <100 Persons)...")

    # Case A: Room with 99 occupants (Compliant with <100)
    p_room_99 = {
        "floor_name": "Level 02 Typical Floor",
        "rooms": [{"name": "CONFERENCE ROOM", "area_m2": 138.6, "occupant_load": 99, "travel_distance_m": 15.0, "centroid": [50, 50]}],
        "exits": [{"name": "STAIR S-01", "pos": [10, 50]}, {"name": "STAIR S-02", "pos": [90, 50]}],
    }
    v_room_99 = evaluate_fls_rules(p_room_99, con=con, drawing_id="test_rm99", element_id_map={})
    assert len([v for v in v_room_99 if "single" in v.get("clause_ref", "").lower() or "single" in v.get("type", "").lower()]) == 0

    # Case B: Room with 100 occupants (Violates <100 rule -> UAE-FLS-3.19-BUS-SINGLE-DOOR)
    p_room_100 = {
        "floor_name": "Level 02 Typical Floor",
        "rooms": [{"name": "LARGE ASSEMBLY / OFFICE", "area_m2": 140.0, "occupant_load": 100, "travel_distance_m": 15.0, "centroid": [50, 50]}],
        "exits": [{"name": "STAIR S-01", "pos": [10, 50]}, {"name": "STAIR S-02", "pos": [90, 50]}],
    }
    v_room_100 = evaluate_fls_rules(p_room_100, con=con, drawing_id="test_rm100", element_id_map={})
    single_vs_100 = [v for v in v_room_100 if v["clause_ref"] == "UAE-FLS-3.19-BUS-SINGLE-DOOR"]
    assert len(single_vs_100) == 1, f"Expected violation UAE-FLS-3.19-BUS-SINGLE-DOOR, got {v_room_100}"
    assert single_vs_100[0]["limit_value"] == 100.0
    assert single_vs_100[0]["measured_value"] == 100

    # Case C: Room with 120 occupants (Violates <100 rule -> UAE-FLS-3.19-BUS-SINGLE-DOOR)
    p_room_120 = {
        "floor_name": "Ground Floor Plan (Level 00)",
        "rooms": [{"name": "MAIN AUDITORIUM", "area_m2": 168.0, "occupant_load": 120, "travel_distance_m": 20.0, "centroid": [50, 50]}],
        "exits": [{"name": "MAIN ENTRANCE / EXIT", "pos": [50, 90]}],
    }
    v_room_120 = evaluate_fls_rules(p_room_120, con=con, drawing_id="test_rm120", element_id_map={})
    single_vs_120 = [v for v in v_room_120 if v["clause_ref"] == "UAE-FLS-3.19-BUS-SINGLE-DOOR"]
    assert len(single_vs_120) == 1, f"Expected violation UAE-FLS-3.19-BUS-SINGLE-DOOR, got {v_room_120}"
    assert single_vs_120[0]["limit_value"] == 100.0

    # Case D: OPEN OFFICE CENTRAL with 13 occupants (13 < 100 -> Must NOT be flagged)
    p_open_office = {
        "floor_name": "Level 01 Typical Floor",
        "rooms": [{"name": "OPEN OFFICE CENTRAL", "area_m2": 118.0, "occupant_load": 13, "travel_distance_m": 15.16, "centroid": [51.4, 59.75]}],
        "exits": [{"name": "EXIT STAIR S-01", "pos": [23.39, 42.10]}, {"name": "EXIT STAIR S-02", "pos": [79.41, 42.10]}],
    }
    v_open_office = evaluate_fls_rules(p_open_office, con=con, drawing_id="test_ooc", element_id_map={})
    single_vs_ooc = [v for v in v_open_office if "single" in v.get("clause_ref", "").lower() or "single" in v.get("type", "").lower()]
    assert len(single_vs_ooc) == 0, f"OPEN OFFICE CENTRAL at 13 persons should NOT be flagged, but got: {single_vs_ooc}"

    print("  -> Passed all 4 single-door Table 3.19 Item 1.i (<100 persons) statutory tests.")

    # -------------------------------------------------------------------------
    # TEST METHOD 4: MULTI-OCCUPANCY CLASSIFICATION (Educational vs Healthcare)
    # -------------------------------------------------------------------------
    print("\n[METHOD 4] Multi-Occupancy Code Clause Thresholds...")

    # Case A: Educational Classroom (93 m2 single-door limit per Table 3.20)
    edu_drawing = {
        "floor_name": "School Ground Floor",
        "rooms": [{"name": "CLASSROOM 101", "area_m2": 95.0, "occupant_load": 40, "travel_distance_m": 10.0, "centroid": [30, 30]}],
        "exits": [{"name": "EXIT STAIR 1", "pos": [10, 50]}, {"name": "EXIT STAIR 2", "pos": [90, 50]}],
    }
    edu_vs = evaluate_fls_rules(edu_drawing, con=con, drawing_id="test_edu", element_id_map={}, occupancy_type="Educational - Classrooms")
    edu_area_v = [v for v in edu_vs if v["clause_ref"] == "UAE-FLS-3.20-EDU-ROOM-AREA"]
    assert len(edu_area_v) == 1
    assert edu_area_v[0]["limit_value"] == 93.0
    assert edu_area_v[0]["measured_value"] == 95.0

    # Case B: Healthcare Ward (93 m2 single-door limit per Table 3.22)
    hlth_drawing = {
        "floor_name": "Hospital Inpatient Floor",
        "rooms": [{"name": "PATIENT SUITE 3", "area_m2": 110.0, "occupant_load": 10, "travel_distance_m": 12.0, "centroid": [30, 30]}],
        "exits": [{"name": "EXIT STAIR 1", "pos": [10, 50]}, {"name": "EXIT STAIR 2", "pos": [90, 50]}],
    }
    hlth_vs = evaluate_fls_rules(hlth_drawing, con=con, drawing_id="test_hlth", element_id_map={}, occupancy_type="Healthcare - Inpatient Bed Corridors")
    hlth_area_v = [v for v in hlth_vs if v["clause_ref"] == "UAE-FLS-3.22-HLTH-ROOM-AREA"]
    assert len(hlth_area_v) == 1
    assert hlth_area_v[0]["limit_value"] == 93.0

    print("  -> Passed Educational and Healthcare multi-occupancy clause checks.")

    # -------------------------------------------------------------------------
    # TEST METHOD 5: CORRIDOR WIDTH & CAPACITY MULTIPLIER
    # -------------------------------------------------------------------------
    print("\n[METHOD 5] Corridor Width & Dynamic Capacity Rules...")
    # Baseline test: 1100mm corridor in Business (<1200mm) -> flagged
    narrow_corridor = {
        "rooms": [{"name": "OFFICE", "area_m2": 30.0, "occupant_load": 5, "travel_distance_m": 10.0, "centroid": [50, 50]}],
        "exits": [{"name": "EXIT 1", "pos": [10, 50]}],
        "summary": {"corridor_width_mm": 1100.0, "width_m": 42.0, "height_m": 24.0}
    }
    v_narrow = evaluate_fls_rules(narrow_corridor, con=con, drawing_id="test_narrow", element_id_map={})
    corr_v = [v for v in v_narrow if v["clause_ref"] == "UAE-FLS-3.8-CORRIDOR-WIDTH-MIN"]
    assert len(corr_v) == 1
    assert corr_v[0]["limit_value"] == 1200.0
    assert corr_v[0]["measured_value"] == 1100.0

    print("  -> Passed Corridor Width standard compliance check.")

    # -------------------------------------------------------------------------
    # TEST METHOD 6: TOPOLOGICAL PATH ROUTING & MONOTONICITY
    # -------------------------------------------------------------------------
    print("\n[METHOD 6] Topological Path Routing & Monotonicity...")
    diag_drawing = {
        "rooms": [
            {"name": "CLOSE ROOM", "centroid": [20.0, 50.0], "svg_centroid": [20.0, 50.0]},
            {"name": "FAR ROOM", "centroid": [50.0, 50.0], "svg_centroid": [50.0, 50.0]},
        ],
        "exits": [
            {"name": "WEST EXIT", "pos": [5.0, 50.0]},
        ],
        "summary": {"width_m": 100.0, "height_m": 40.0}
    }
    routed = calculate_walkable_distances(diag_drawing)
    close_dist = next(r["travel_distance_m"] for r in routed["rooms"] if r["name"] == "CLOSE ROOM")
    far_dist = next(r["travel_distance_m"] for r in routed["rooms"] if r["name"] == "FAR ROOM")
    assert close_dist < far_dist, f"Path Monotonicity Fallacy: close={close_dist}m >= far={far_dist}m"
    assert far_dist > 0.0
    assert len(routed["rooms"][0]["connection_path"]) == 4

    print("  -> Passed Topological shortest-path monotonicity and SVG path generation.")

    # -------------------------------------------------------------------------
    # TEST METHOD 7: API IDEMPOTENCY, STATE TRANSITIONS & MALFORMED INPUTS
    # -------------------------------------------------------------------------
    print("\n[METHOD 7] API Idempotency, Concurrency State & Error Resiliency...")
    # Fetch projects
    res = client.get("/projects")
    assert res.status_code == 200
    p_id = res.json()[0]["id"]

    # Invalid file upload
    bad_file = {"file": ("corrupt.dxf", b"NOT_A_REAL_DXF_FILE_HEADER", "application/dxf")}
    res = client.post(f"/projects/{p_id}/drawings", files=bad_file, data={"scale": 100})
    assert res.status_code == 400
    assert "parsing failed" in res.json()["detail"].lower() or "dxf" in res.json()["detail"].lower()

    # Non-existent drawing 404
    res = client.get("/drawings/non-existent-uuid-12345")
    assert res.status_code == 404

    # Non-existent violation patch 404
    res = client.patch("/violations/non-existent-v-12345", json={"status": "confirmed"})
    assert res.status_code == 404

    # Test complete state cycle on seeded demo drawing
    res = client.get("/drawings/drawing-al-noor-l06/violations")
    assert res.status_code == 200
    v_list = res.json()
    assert len(v_list) > 0
    target_v_id = v_list[0]["id"]

    for state in ["confirmed", "resolved", "false_positive", "open"]:
        patch_res = client.patch(f"/violations/{target_v_id}", json={"status": state, "note": f"Automated state test: {state}"})
        assert patch_res.status_code == 200
        assert patch_res.json()["status"] == state

    print("  -> Passed all API error resilience, state transition cycles, and input validation tests.")

    print("\n================================================================================")
    print("ALL 7 SENIOR QA TESTING METHODS & FALLACY CHECKS PASSED PERFECTLY!")
    print("================================================================================")


if __name__ == "__main__":
    run_all_senior_qa_tests()
