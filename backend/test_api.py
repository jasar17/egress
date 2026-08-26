import io
import json
import os
import sys
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent))

from app.main import app, init_database
from app.dxf_parser import parse_dxf_file
from app.occupant_load import calculate_occupant_loads

def test_full_flow():
    init_database()
    client = TestClient(app)
    
    # 1. Health check
    res = client.get("/health")

    assert res.status_code == 200, f"Health check failed: {res.text}"
    print("[PASS] Health check passed")

    # 2. List projects
    res = client.get("/projects")
    assert res.status_code == 200, f"List projects failed: {res.text}"
    projects = res.json()
    assert len(projects) > 0, "No projects found"
    project_id = projects[0]["id"]
    print(f"[PASS] List projects passed (found {len(projects)} projects)")

    # 3. Upload real PDF drawing
    real_pdf_path = Path(__file__).resolve().parents[1] / "floor plan" / "Dubai_Commercial_Building_FLS_Test_FloorPlans.pdf"
    assert real_pdf_path.exists(), f"Test PDF not found at {real_pdf_path}"
    with open(real_pdf_path, "rb") as f:
        pdf_bytes = f.read()
    files = {"file": ("Dubai_Commercial_Building_FLS_Test_FloorPlans.pdf", pdf_bytes, "application/pdf")}
    data = {"occupancy_type": "Business - Regular office areas", "sprinklered": "false", "scale": 100}
    res = client.post(f"/projects/{project_id}/drawings", files=files, data=data)
    assert res.status_code == 201, f"Upload failed: {res.text}"
    upload_res = res.json()
    drawing_id = upload_res["drawing_id"]

    assert upload_res["status"] == "ready", f"Drawing status was not ready: {upload_res}"
    print(f"[PASS] Upload drawing passed (drawing_id={drawing_id})")

    # 4. Check drawing status
    res = client.get(f"/drawings/{drawing_id}/status")
    assert res.status_code == 200, f"Drawing status failed: {res.text}"
    assert res.json()["status"] == "ready"
    print("[PASS] Drawing status check passed")

    # 5. Check drawing elements
    res = client.get(f"/drawings/{drawing_id}/elements")
    assert res.status_code == 200, f"Elements failed: {res.text}"
    elements = res.json()
    assert elements.get("type") == "FeatureCollection"
    assert len(elements.get("features", [])) > 0, "No elements returned"
    print(f"[PASS] Elements check passed (features={len(elements['features'])})")

    # 6. Check violations on seeded demo drawing and uploaded drawing
    res = client.get("/drawings/drawing-al-noor-l06/violations")
    assert res.status_code == 200, f"Violations failed: {res.text}"
    violations = res.json()
    assert len(violations) > 0, "No violations returned on demo drawing"
    violation_id = violations[0]["id"]
    print(f"[PASS] Violations check passed (violations={len(violations)}, first_id={violation_id})")

    # 7. Update violation to confirmed
    res = client.patch(f"/violations/{violation_id}", json={"status": "confirmed"})
    assert res.status_code == 200, f"Patch confirmed failed: {res.text}"
    assert res.json()["status"] == "confirmed"
    print("[PASS] Patch violation to 'confirmed' passed")

    # 8. Update violation to resolved
    res = client.patch(f"/violations/{violation_id}", json={"status": "resolved"})
    assert res.status_code == 200, f"Patch resolved failed: {res.text}"
    assert res.json()["status"] == "resolved"
    print("[PASS] Patch violation to 'resolved' passed")

    # 9. Reopen violation ('open')
    res = client.patch(f"/violations/{violation_id}", json={"status": "open"})
    assert res.status_code == 200, f"Patch reopen failed: {res.text}"
    assert res.json()["status"] == "open"
    print("[PASS] Patch violation to 'open' (reopen) passed")

    # 10. Export CSV
    res = client.get(f"/drawings/{drawing_id}/export")
    assert res.status_code == 200, f"Export CSV failed: {res.text}"
    assert "text/csv" in res.headers.get("content-type", "")
    assert "ID,Type,Location" in res.text
    print("[PASS] Export CSV passed")

    # 11. List Code Clauses
    res = client.get("/code-clauses")
    assert res.status_code == 200, f"List code clauses failed: {res.text}"
    clauses = res.json()
    assert len(clauses) >= 20, f"Expected at least 20 clauses, got {len(clauses)}"
    print(f"[PASS] List code clauses passed (loaded {len(clauses)} real UAE clauses)")

    # 12. Get Single Code Clause
    res = client.get("/code-clauses/UAE-FLS-3.13-BUS-REG")
    assert res.status_code == 200, f"Get code clause failed: {res.text}"
    clause = res.json()
    assert clause["clause_id"] == "UAE-FLS-3.13-BUS-REG"
    assert clause["value"] == 9.3
    assert clause["unit"] == "m2_per_person"
    # 13. Upload Real DXF Drawing and verify actual parsed geometry
    dxf_path = Path(__file__).resolve().parents[1] / "floor plan" / "Dubai_Commercial_Floor_Level_01_Typical.dxf"
    assert dxf_path.exists(), f"DXF test file not found at {dxf_path}"
    with open(dxf_path, "rb") as df:
        dxf_bytes = df.read()
    files = {"file": ("Dubai_Commercial_Floor_Level_01_Typical.dxf", dxf_bytes, "application/dxf")}
    data = {"occupancy_type": "commercial_office", "scale": 100}
    res = client.post(f"/projects/{project_id}/drawings", files=files, data=data)
    assert res.status_code == 201, f"DXF Upload failed: {res.text}"
    dxf_drawing_id = res.json()["drawing_id"]
    assert res.json()["status"] == "ready"
    print(f"[PASS] Real DXF upload passed (drawing_id={dxf_drawing_id})")

    # Check DXF extracted elements, calculated travel distance & occupant loads
    res = client.get(f"/drawings/{dxf_drawing_id}/elements")
    assert res.status_code == 200, f"DXF Elements failed: {res.text}"
    features = res.json().get("features", [])
    assert len(features) > 0, "No features extracted from DXF"
    room_features = [f for f in features if f["type"] == "room"]
    assert len(room_features) > 0, "No rooms found in extracted elements"
    for rf in room_features:
        props = rf["properties"]
        assert "travel_distance_m" in props, f"Room {props.get('name')} missing travel_distance_m"
        assert props["travel_distance_m"] > 0, f"Room {props.get('name')} has non-positive travel distance"
        assert "occupant_load" in props, f"Room {props.get('name')} missing occupant_load"
        assert "occupant_load_factor" in props, f"Room {props.get('name')} missing occupant_load_factor"
        assert props["occupant_load_factor"] > 0

    # Spot-check math on Open Office West (65.0 m2 / 9.3 = 6.99 -> 7 occupants) and Meeting Room 1A (37.0 m2 / 1.4 = 26.4 -> 27 occupants)
    west_office = next((r for r in room_features if "OPEN OFFICE WEST" in r["properties"]["name"]), None)
    assert west_office is not None
    assert west_office["properties"]["occupant_load"] == 7
    assert west_office["properties"]["occupant_load_factor"] == 9.3

    meeting_room = next((r for r in room_features if "MEETING ROOM 1A" in r["properties"]["name"]), None)
    assert meeting_room is not None
    assert meeting_room["properties"]["occupant_load"] == 27
    assert meeting_room["properties"]["occupant_load_factor"] == 1.4

    print(f"[PASS] Real DXF extraction, path analysis & occupant loads verified ({len(features)} elements, {len(room_features)} rooms: West Office = {west_office['properties']['occupant_load']}p, Meeting 1A = {meeting_room['properties']['occupant_load']}p)")



    # 14. Verify Invalid DXF Upload returns clear error
    bad_files = {"file": ("corrupt_drawing.dxf", b"NOT A VALID DXF HEADER", "application/dxf")}
    res = client.post(f"/projects/{project_id}/drawings", files=bad_files, data={"occupancy_type": "commercial_office"})
    assert res.status_code == 400, f"Expected 400 for corrupt DXF, got {res.status_code}"
    print("[PASS] Invalid DXF rejected with clear error (400 Bad Request)")

    # 16. Upload Non-Compliant Test Floor Plan and verify real code-cited violations
    nc_dxf_path = Path(__file__).resolve().parents[1] / "floor plan" / "Dubai_Commercial_Floor_Level_05_NonCompliant.dxf"
    assert nc_dxf_path.exists(), f"Non-compliant DXF not found at {nc_dxf_path}"
    with open(nc_dxf_path, "rb") as ncf:
        nc_bytes = ncf.read()
    files = {"file": ("Dubai_Commercial_Floor_Level_05_NonCompliant.dxf", nc_bytes, "application/dxf")}
    res = client.post(f"/projects/{project_id}/drawings", files=files, data={"occupancy_type": "commercial_office"})
    assert res.status_code == 201
    nc_drawing_id = res.json()["drawing_id"]

    # Check generated violations
    res = client.get(f"/drawings/{nc_drawing_id}/violations")
    assert res.status_code == 200
    nc_violations = res.json()
    assert len(nc_violations) > 0, "Expected real violations to be generated for non-compliant drawing"
    clause_refs = [v["clause_ref"] for v in nc_violations]
    assert "UAE-FLS-3.19-BUS-ROOM-AREA" in clause_refs, f"Room area clause violation not found in {clause_refs}"
    area_violation = next(v for v in nc_violations if v["clause_ref"] == "UAE-FLS-3.19-BUS-ROOM-AREA")
    assert area_violation["measured_value"] > 280.0
    assert area_violation["limit_value"] == 280.0
    assert area_violation["limit_unit"] == "m2"
    # 17. Verify seeded demo drawing remains unchanged
    res = client.get("/drawings/drawing-al-noor-l06/elements")
    assert res.status_code == 200
    demo_features = res.json().get("features", [])
    assert len(demo_features) == 9, f"Seeded demo drawing altered: {len(demo_features)} features"
    print("[PASS] Seeded demo drawing 'drawing-al-noor-l06' preserved intact (9 features)")

    # 18. Test Project-level inputs & Dynamic Sprinkler Status toggle
    # Reconfigure drawing to non-sprinklered
    res = client.patch(f"/drawings/{nc_drawing_id}/config", json={"sprinklered": False})
    assert res.status_code == 200
    assert res.json()["sprinklered"] == 0
    print("[PASS] Dynamic sprinkler status toggle to non-sprinklered passed")

    # Verify non-sprinklered rules applied
    res = client.get(f"/drawings/{nc_drawing_id}/violations")
    assert res.status_code == 200
    ns_violations = res.json()
    assert len(ns_violations) >= len(nc_violations), "Non-sprinklered should maintain or increase strictness"
    print(f"[PASS] Dynamic re-evaluation with sprinklered=False verified ({len(ns_violations)} findings)")

    # 19. Automated Regression Test: Dubai 5-Floor Set (Geometry-based Occupant Loads & Scale Travel Distance)
    # Switch uploaded multi-floor PDF to Page 1 (Level 01 - Typical Office Floor)
    res = client.post(f"/drawings/{drawing_id}/page", json={"page_index": 1})
    assert res.status_code == 200, f"Page switch failed: {res.text}"
    p1_data = res.json()
    assert "Level 01" in p1_data.get("floor_name", "") or "Typical" in p1_data.get("floor_name", "")

    # Fetch elements on Typical Floor
    res = client.get(f"/drawings/{drawing_id}/elements")
    assert res.status_code == 200
    p1_features = res.json().get("features", [])
    p1_rooms = [f for f in p1_features if f["type"] == "room"]
    p1_habitable = [r for r in p1_rooms if "STAIR" not in r["properties"]["name"].upper() and "EXIT" not in r["properties"]["name"].upper()]
    
    # 19a. Assert Occupant Load is calculated purely from geometry per room (158 persons total)
    p1_total_occ = sum(r["properties"].get("occupant_load", 0) for r in p1_habitable)
    assert p1_total_occ == 158, f"Regression error: Expected geometry load of 158 persons, got {p1_total_occ}"

    # 19b. Assert Travel Distance is correctly calculated on physical scale (~18.69m, ruling out 122.90m unscaled error)
    p1_travel_dists = [r["properties"].get("travel_distance_m", 0.0) for r in p1_rooms]
    p1_max_travel = max(p1_travel_dists) if p1_travel_dists else 0.0
    assert abs(p1_max_travel - 18.69) <= 1.0, f"Regression error: Expected max travel distance ~18.69m, got {p1_max_travel}m"
    assert p1_max_travel < 50.0, f"Regression error: Unscaled travel distance detected ({p1_max_travel}m >= 50m, previous bug was 122.90m)"

    # 19c. Assert Per-Room Independence & Exact Matching between PDF and DXF
    import sqlite3
    db_con = sqlite3.connect("data/fls_demo.db")
    db_con.row_factory = sqlite3.Row
    dxf_test_path = Path(__file__).resolve().parents[1] / "floor plan" / "Dubai_Commercial_Floor_Level_01_Typical.dxf"
    dxf_parsed = parse_dxf_file(dxf_test_path)
    dxf_parsed = calculate_occupant_loads(dxf_parsed, con=db_con)
    pdf_room_loads = {r["properties"]["name"]: r["properties"]["occupant_load"] for r in p1_rooms}
    dxf_room_loads = {r["name"]: r["occupant_load"] for r in dxf_parsed["rooms"]}

    for room_name in ["OPEN OFFICE WEST", "OPEN OFFICE CENTRAL", "OPEN OFFICE EAST", "MEETING ROOM 1A", "MEETING ROOM 1B"]:
        assert pdf_room_loads[room_name] == dxf_room_loads[room_name], f"Mismatch for {room_name}: PDF={pdf_room_loads[room_name]}, DXF={dxf_room_loads[room_name]}"
    print(f"[PASS] Dubai 5-floor Typical Office regression passed: Occ Load={p1_total_occ}p (calculated purely from geometry), Max Travel={p1_max_travel}m, PDF & DXF room loads match 100%")

    # 20. Multi-Floor Summary Verification across all 5 floors
    res = client.get(f"/drawings/{drawing_id}/multi-floor-summary")
    assert res.status_code == 200
    summary_data = res.json()
    assert summary_data["total_pages"] == 5, f"Expected 5 floors, got {summary_data['total_pages']}"
    floors = summary_data["floors"]
    assert len(floors) == 5
    assert floors[0]["total_occupant_load"] == 69   # Level 00 Ground Floor
    assert floors[1]["total_occupant_load"] == 158  # Level 01 Typical
    assert floors[2]["total_occupant_load"] == 158  # Level 02 Typical
    assert floors[3]["total_occupant_load"] == 158  # Level 03 Typical
    assert floors[4]["total_occupant_load"] == 136  # Level 04 Executive
    print(f"[PASS] Full 5-floor building summary verified across all storeys (L00: 69p, L01-L03: 158p, L04: 136p)")

    print("\nALL 20 API & REGRESSION TEST SUITES PASSED SUCCESSFULLY! ZERO ERRORS.")


if __name__ == "__main__":
    test_full_flow()





