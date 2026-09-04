"""
Automated Test Suite for Phase 2b: Cross-Document Entity Linking.
Validates:
1. Coordinate origin and scale parity between Architectural and Fire Alarm DXFs.
2. 2D Point-in-polygon assignment of fire alarm devices into architectural room polygons.
3. Circulation/corridor handling for devices falling outside room polygons.
4. Database persistence in device_room_links and extracted_elements denormalization.
5. Exact assignment verification across all 20 devices.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ["USE_LOCAL_SQLITE"] = "1"

backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

import ezdxf
from fastapi.testclient import TestClient
from app.main import app, init_database
from app.linking import link_fire_alarm_devices_to_rooms, get_project_device_links
from app.db import get_db


def test_coordinate_system_parity():
    """
    Step 0 Requirement:
    Confirm that architectural and fire alarm DXF files share the exact same
    coordinate origin, footprint, and scale (42.0m x 24.0m) without transformation.
    """
    arch_path = backend_dir.parent / "floor plan" / "Dubai_Commercial_Floor_Level_01_Typical.dxf"
    fa_path = backend_dir.parent / "floor plan" / "Dubai_Commercial_Floor_Level_01_FireAlarm.dxf"

    assert arch_path.exists(), f"Missing arch fixture: {arch_path}"
    assert fa_path.exists(), f"Missing fire alarm fixture: {fa_path}"

    doc_arch = ezdxf.readfile(str(arch_path))
    doc_fa = ezdxf.readfile(str(fa_path))

    def get_outer_bounds(msp):
        for e in msp.query("LWPOLYLINE"):
            if e.dxf.layer in ("A-WALL-EXTR", "WALL_EXTERNAL", "ENVELOPE"):
                pts = list(e.get_points())
                xs = [p[0] for p in pts]
                ys = [p[1] for p in pts]
                return (min(xs), min(ys), max(xs), max(ys))
        return None

    arch_box = get_outer_bounds(doc_arch.modelspace())
    fa_box = get_outer_bounds(doc_fa.modelspace())

    print("\n================================================================================")
    print("COORDINATE SYSTEM PARITY CHECK")
    print("================================================================================")
    print(f"Architectural BBox: {arch_box}")
    print(f"Fire Alarm BBox:    {fa_box}")

    assert arch_box == (0.0, 0.0, 42000.0, 24000.0), f"Unexpected Arch BBox: {arch_box}"
    assert fa_box == (0.0, 0.0, 42000.0, 24000.0), f"Unexpected Fire Alarm BBox: {fa_box}"
    print("[PASS] Coordinate origin (0, 0) and extents (42000mm x 24000mm) match 100%.")


def test_cross_document_entity_linking_end_to_end():
    """
    End-to-end multi-drawing upload and point-in-polygon entity linking verification.
    """
    init_database()
    client = TestClient(app)

    # 1. Create project
    p_res = client.post("/projects", json={
        "name": "Dubai Burj Al Waha - Phase 2b Linking Test",
        "client_name": "Al Waha Investments",
        "occupancy_type": "Business - Regular office areas",
        "sprinklered": True
    })
    assert p_res.status_code == 201
    project_id = p_res.json()["id"]

    # 2. Upload Architectural Floor Plan
    arch_path = backend_dir.parent / "floor plan" / "Dubai_Commercial_Floor_Level_01_Typical.dxf"
    with open(arch_path, "rb") as f:
        arch_bytes = f.read()

    arch_res = client.post(
        f"/projects/{project_id}/drawings",
        files={"file": ("Dubai_Level_01_Arch.dxf", arch_bytes, "application/dxf")},
        data={"document_type": "architectural", "occupancy_type": "Business - Regular office areas", "sprinklered": "true", "scale": "100"}
    )
    assert arch_res.status_code == 201
    arch_drawing_id = arch_res.json()["drawing_id"]
    print(f"[PASS] Uploaded Architectural Drawing: {arch_drawing_id}")

    # 3. Upload Fire Alarm Shop Drawing
    fa_path = backend_dir.parent / "floor plan" / "Dubai_Commercial_Floor_Level_01_FireAlarm.dxf"
    with open(fa_path, "rb") as f:
        fa_bytes = f.read()

    fa_res = client.post(
        f"/projects/{project_id}/drawings",
        files={"file": ("Dubai_Level_01_FireAlarm.dxf", fa_bytes, "application/dxf")},
        data={"document_type": "fire_alarm", "occupancy_type": "Business - Regular office areas", "sprinklered": "true", "scale": "100"}
    )
    assert fa_res.status_code == 201
    fa_drawing_id = fa_res.json()["drawing_id"]
    print(f"[PASS] Uploaded Fire Alarm Drawing: {fa_drawing_id}")

    # 4. Fetch Cross-Document Device Links via API
    links_res = client.get(f"/projects/{project_id}/device-links")
    assert links_res.status_code == 200
    links = links_res.json()
    assert len(links) == 20, f"Expected 20 linked devices, got {len(links)}"

    # 5. Summary statistics
    assigned_rooms = [l for l in links if l["status"] == "assigned_room"]
    unassigned = [l for l in links if l["status"] == "unassigned_corridor"]

    print("\n========================================================================================================================")
    print("PHASE 2B REAL CROSS-DOCUMENT ENTITY LINKING RESULTS (ALL 20 DEVICES)")
    print("========================================================================================================================")
    print(f"{'Tag':<8} | {'Type':<18} | {'Physical (m)':<15} | {'SVG Coord':<15} | {'Assigned Space':<24} | {'Status':<19} | {'Notes'}")
    print("-" * 120)

    for l in links:
        tag = l["device_tag"]
        dev_type = l["device_type"]
        pos_m = f"({l['x_m']}m, {l['y_m']}m)" if l["x_m"] is not None else "N/A"
        svg_c = f"[{l['svg_x']}, {l['svg_y']}]"
        room = l["room_name"]
        status = l["status"]
        
        note = ""
        if tag in ("SD-06", "SD-07", "SD-11"):
            note = "Past room East boundary; in circulation"
        elif tag == "HD-01":
            note = "Intended pantry; geometrically in Central Office"
        elif tag in ("SD-01", "SD-02"):
            note = "South wing; inside Meeting Room 1B"
        elif tag == "FACP-01":
            note = "Entrance / inside West Stair vestibule"
        elif "corridor" in room:
            note = "Central horizontal circulation spine"
        else:
            note = "Cleanly inside room boundary polygon"

        print(f"{tag:<8} | {dev_type:<18} | {pos_m:<15} | {svg_c:<15} | {room:<24} | {status:<19} | {note}")

    print("-" * 120)
    print(f"Total Devices: {len(links)} | Assigned to Rooms: {len(assigned_rooms)} | Unassigned (Corridor): {len(unassigned)}")

    # 6. Strict Assertions on Assignments
    link_map = {l["device_tag"]: l for l in links}

    # Meeting room & pantry detectors
    assert link_map["SD-01"]["room_name"] == "MEETING ROOM 1B"
    assert link_map["SD-02"]["room_name"] == "MEETING ROOM 1B"
    assert link_map["SD-03"]["room_name"] == "MEETING ROOM 1C"
    assert link_map["SD-04"]["room_name"] == "MEETING ROOM 1C"
    assert link_map["SD-05"]["room_name"] == "MEETING ROOM 1D"

    # Open office detectors
    assert link_map["SD-08"]["room_name"] == "OPEN OFFICE CENTRAL"
    assert link_map["SD-09"]["room_name"] == "OPEN OFFICE CENTRAL"
    assert link_map["SD-10"]["room_name"] == "OPEN OFFICE EAST"
    assert link_map["HD-01"]["room_name"] == "OPEN OFFICE CENTRAL"

    # Circulation / Corridor devices (not forced into nearest room)
    assert link_map["SD-06"]["room_name"] == "unassigned - corridor"
    assert link_map["SD-07"]["room_name"] == "unassigned - corridor"
    assert link_map["SD-11"]["room_name"] == "unassigned - corridor"
    assert link_map["SD-12"]["room_name"] == "unassigned - corridor"
    assert link_map["SD-13"]["room_name"] == "unassigned - corridor"
    assert link_map["MCP-01"]["room_name"] == "unassigned - corridor"
    assert link_map["MCP-02"]["room_name"] == "unassigned - corridor"
    assert link_map["MCP-03"]["room_name"] == "unassigned - corridor"
    assert link_map["SND-01"]["room_name"] == "unassigned - corridor"
    assert link_map["SND-02"]["room_name"] == "unassigned - corridor"

    # FACP vestibule
    assert link_map["FACP-01"]["room_name"] == "EXIT STAIR S-01 (WEST)"

    # 7. Check Database Persistence in device_room_links and extracted_elements
    with get_db() as con:
        db_links = con.execute("SELECT * FROM device_room_links WHERE project_id = ?", (project_id,)).fetchall()
        assert len(db_links) == 20

        # Verify denormalized fields on extracted_elements
        db_elem = con.execute(
            "SELECT properties FROM extracted_elements WHERE drawing_id = ? AND name = 'SD-01'",
            (fa_drawing_id,)
        ).fetchone()
        import json
        props = json.loads(db_elem["properties"])
        assert props["linked_room_name"] == "MEETING ROOM 1B"
        assert props["linking_status"] == "assigned_room"
        assert props["linked_room_id"] is not None

    print("[PASS] All 20 device-to-room cross-document relationships verified in database.")


if __name__ == "__main__":
    test_coordinate_system_parity()
    test_cross_document_entity_linking_end_to_end()
    print("\nALL PHASE 2B CROSS-DOCUMENT LINKING TESTS PASSED PERFECTLY.")
