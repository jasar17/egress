import json
import sqlite3
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app, db, seed_demo

client = TestClient(app)

def test_multi_floor_summary_flow():
    # 1. Test Seeded Drawing Multi-Floor Summary
    res = client.get("/drawings/drawing-al-noor-l06/multi-floor-summary")
    assert res.status_code == 200, f"Failed: {res.text}"
    summary = res.json()
    assert summary["total_pages"] == 1
    assert len(summary["floors"]) == 1
    print("[PASS] Seeded drawing summary works")

    # 2. Test Multi-page PDF Upload & Summary
    pdf_path = Path("floor plan/Dubai_Commercial_Building_FLS_Test_FloorPlans.pdf")
    if not pdf_path.exists():
        pdf_path = Path("../floor plan/Dubai_Commercial_Building_FLS_Test_FloorPlans.pdf")

    with open(pdf_path, "rb") as f:
        res = client.post(
            "/projects/project-al-noor/drawings",
            files={"file": (pdf_path.name, f, "application/pdf")},
            data={"occupancy_type": "Business - Regular office areas", "sprinklered": "true", "scale": "100"}
        )
    assert res.status_code == 201, f"Upload failed: {res.text}"
    drawing_data = res.json()
    drawing_id = drawing_data["drawing_id"]
    assert drawing_data["pages_count"] == 5
    assert len(drawing_data["pages"]) == 5
    print(f"[PASS] Uploaded multi-page PDF ({drawing_id}) with 5 decoded pages")

    # 3. Test multi-floor-summary endpoint
    res = client.get(f"/drawings/{drawing_id}/multi-floor-summary")
    assert res.status_code == 200
    mf_summary = res.json()
    assert mf_summary["total_pages"] == 5
    assert len(mf_summary["floors"]) == 5
    
    print("\n--- ALL 5 DECODED FLOORS & THEIR ERRORS ---")
    for fl in mf_summary["floors"]:
        print(f"Floor {fl['index']}: {fl['title']:<45} | Rooms: {fl['rooms_count']:>2} | Exits: {fl['exits_count']} | Occ: {fl['total_occupant_load']:>3}p | Max Travel: {fl['max_travel_distance_m']:>6.2f}m | Errors: {fl['violations_count']:>2} | Status: {fl['status']}")
        for v in fl["violations"]:
            print(f"   -> [{v['severity']}] {v['type']}: {v['title']} (Clause: {v['clause_ref']})")

    # 4. Test page switching to Level 04
    res = client.post(f"/drawings/{drawing_id}/page", json={"page_index": 4})
    assert res.status_code == 200
    p4_data = res.json()
    assert p4_data["page_index"] == 4
    print("\n[PASS] Switched active floor to Page 4 (Level 04)")

    # 5. Check active Page 4 data and compliance
    res = client.get(f"/drawings/{drawing_id}/violations")
    assert res.status_code == 200
    p4_violations = res.json()
    assert isinstance(p4_violations, list)
    print(f"[PASS] Active floor 4 decoded successfully with {len(p4_violations)} violations in sprinklered review mode")

if __name__ == "__main__":
    test_multi_floor_summary_flow()
