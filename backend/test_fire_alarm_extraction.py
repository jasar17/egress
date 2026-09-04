"""
Automated Test Suite for Fire Alarm / Detection Shop Drawing Ingestion & Symbol Extraction.
Validates:
1. parse_fire_alarm_dxf_file() on real DXF test fixture.
2. Uploading fire_alarm document_type alongside architectural floor plans.
3. Multi-drawing project linkage via GET /projects/{project_id}/drawings.
4. Storage and verification of extracted symbol coordinates and tags in extracted_elements.
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
from app.dxf_parser import parse_fire_alarm_dxf_file


def test_fire_alarm_dxf_parser_direct():
    """Validates raw geometric and layer symbol extraction from Dubai Level 01 Fire Alarm DXF."""
    dxf_path = backend_dir.parent / "floor plan" / "Dubai_Commercial_Floor_Level_01_FireAlarm.dxf"
    assert dxf_path.exists(), f"Fire alarm fixture not found at {dxf_path}"

    res = parse_fire_alarm_dxf_file(dxf_path)
    summary = res["summary"]

    print("\n================================================================================")
    print("FIRE ALARM DXF SYMBOL EXTRACTION VERIFICATION")
    print("================================================================================")
    print(f"Document Type:       {summary['document_type']}")
    print(f"Total Devices:       {summary['devices_count']}")
    print(f"Smoke Detectors:     {summary['smoke_detectors']}")
    print(f"Heat Detectors:      {summary['heat_detectors']}")
    print(f"Manual Call Points:  {summary['manual_call_points']}")
    print(f"Sounders / Strobes:  {summary['sounders']}")
    print(f"Alarm Panels:        {summary['panels']}")
    print(f"Layers Detected:     {summary['layers_detected']}")
    print(f"Bounding Size (m):   {summary['width_m']}m x {summary['height_m']}m")
    print("-" * 80)

    assert summary["document_type"] == "fire_alarm"
    assert summary["devices_count"] == 20
    assert summary["smoke_detectors"] == 13
    assert summary["heat_detectors"] == 1
    assert summary["manual_call_points"] == 3
    assert summary["sounders"] == 2
    assert summary["panels"] == 1
    assert "FA-SMOKE" in summary["layers_detected"]
    assert "FA-HEAT" in summary["layers_detected"]
    assert "FA-MCP" in summary["layers_detected"]
    assert "FA-SOUNDER" in summary["layers_detected"]
    assert "FA-FACP" in summary["layers_detected"]
    assert summary["width_m"] == 42.0
    assert summary["height_m"] == 24.0

    # Assert element features structure and coordinate normalization
    elements = res["elements"]
    devices_only = [e for e in elements if e[0] != "wall"]
    assert len(devices_only) == 20

    print("Sample Extracted Symbols with Real Physical & Normalized Coordinates:")
    for item_type, tag, feat in devices_only[:7]:
        props = feat["properties"]
        geom = feat["geometry"]
        print(f"  [{props['device_type']:<18}] Tag: {tag:<8} | Layer: {props['layer']:<10} | SVG: {geom['coordinates']} | Meters: {props['pos_m']}")
        # Coordinate sanity checks
        assert 0.0 <= geom["coordinates"][0] <= 100.0
        assert 0.0 <= geom["coordinates"][1] <= 100.0
        assert 0.0 <= props["pos_m"][0] <= 42.0
        assert 0.0 <= props["pos_m"][1] <= 24.0

    print("[PASS] Direct DXF Fire Alarm Parser verified with 100% precision.")


def test_api_multi_drawing_project_upload():
    """
    Validates end-to-end multi-drawing workflow:
    1. Create a project.
    2. Upload Architectural DXF drawing (document_type="architectural").
    3. Upload Fire Alarm DXF drawing (document_type="fire_alarm") to the same project.
    4. Assert GET /projects/{project_id}/drawings returns both linked drawings.
    5. Assert fire alarm drawing elements are stored with zero egress violations.
    """
    init_database()
    client = TestClient(app)

    # 1. Create dedicated project
    p_res = client.post("/projects", json={
        "name": "Dubai Burj Al Waha - Multi-Drawing Test",
        "client_name": "Al Waha Investments",
        "occupancy_type": "Business - Regular office areas",
        "sprinklered": True
    })
    assert p_res.status_code == 201
    project_id = p_res.json()["id"]

    # 2. Upload Architectural DXF (Dubai Level 01)
    arch_path = backend_dir.parent / "floor plan" / "Dubai_Commercial_Floor_Level_01_Typical.dxf"
    with open(arch_path, "rb") as f:
        arch_bytes = f.read()

    arch_res = client.post(
        f"/projects/{project_id}/drawings",
        files={"file": ("Dubai_Level_01_Arch.dxf", arch_bytes, "application/dxf")},
        data={"document_type": "architectural", "occupancy_type": "Business - Regular office areas", "sprinklered": "true", "scale": "100"}
    )
    assert arch_res.status_code == 201, arch_res.text
    arch_data = arch_res.json()
    arch_drawing_id = arch_data["drawing_id"]
    assert arch_data["document_type"] == "architectural"
    assert arch_data["status"] == "ready"
    print(f"[PASS] Uploaded Architectural Drawing: {arch_drawing_id}")

    # 3. Upload Fire Alarm Shop Drawing DXF to SAME project
    fa_path = backend_dir.parent / "floor plan" / "Dubai_Commercial_Floor_Level_01_FireAlarm.dxf"
    with open(fa_path, "rb") as f:
        fa_bytes = f.read()

    fa_res = client.post(
        f"/projects/{project_id}/drawings",
        files={"file": ("Dubai_Level_01_FireAlarm.dxf", fa_bytes, "application/dxf")},
        data={"document_type": "fire_alarm", "occupancy_type": "Business - Regular office areas", "sprinklered": "true", "scale": "100"}
    )
    assert fa_res.status_code == 201, fa_res.text
    fa_data = fa_res.json()
    fa_drawing_id = fa_data["drawing_id"]
    assert fa_data["document_type"] == "fire_alarm"
    assert fa_data["status"] == "ready"
    print(f"[PASS] Uploaded Fire Alarm Drawing: {fa_drawing_id}")

    # 4. Assert Project Multi-Drawing Retrieval (GET /projects/{project_id}/drawings)
    list_res = client.get(f"/projects/{project_id}/drawings")
    assert list_res.status_code == 200, list_res.text
    linked_drawings = list_res.json()
    assert len(linked_drawings) == 2, f"Expected 2 linked drawings, got {len(linked_drawings)}"

    doc_types = {d["id"]: d["document_type"] for d in linked_drawings}
    assert doc_types[arch_drawing_id] == "architectural"
    assert doc_types[fa_drawing_id] == "fire_alarm"
    print(f"[PASS] GET /projects/{project_id}/drawings returned both linked drawings: {doc_types}")

    # 5. Assert Stored Elements for Fire Alarm Drawing
    elem_res = client.get(f"/drawings/{fa_drawing_id}/elements")
    assert elem_res.status_code == 200
    features = elem_res.json().get("features", [])
    alarm_devices = [f for f in features if f["type"] != "wall"]
    assert len(alarm_devices) == 20, f"Expected 20 alarm devices in DB, found {len(alarm_devices)}"

    # Check that individual types are stored correctly
    types_count = {}
    for d in alarm_devices:
        t = d["type"]
        types_count[t] = types_count.get(t, 0) + 1
    assert types_count["smoke_detector"] == 13
    assert types_count["heat_detector"] == 1
    assert types_count["manual_call_point"] == 3
    assert types_count["sounder"] == 2
    assert types_count["fire_alarm_panel"] == 1
    print(f"[PASS] Database extracted_elements verified: {types_count}")

    # 6. Assert Zero Violations for Fire Alarm Drawing in Phase 1
    v_res = client.get(f"/drawings/{fa_drawing_id}/violations")
    assert v_res.status_code == 200
    violations = v_res.json()
    assert len(violations) == 0, f"Expected 0 violations for fire alarm drawing in Phase 1, got {len(violations)}"
    print("[PASS] Zero egress violations asserted for fire alarm drawing (Phase 1 scope respected).")


if __name__ == "__main__":
    test_fire_alarm_dxf_parser_direct()
    test_api_multi_drawing_project_upload()
    print("\nALL FIRE ALARM EXTRACTION & MULTI-DRAWING TESTS PASSED PERFECTLY.")
