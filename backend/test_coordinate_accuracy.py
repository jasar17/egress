import json
import sys
from pathlib import Path
from fastapi.testclient import TestClient

backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from app.main import app, init_database


def test_api_upload():
    init_database()
    client = TestClient(app)

    # 1. Check health
    res = client.get("/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print("[OK] Backend health ok")

    # 2. Get demo project
    res = client.get("/projects")
    projects = res.json()
    assert len(projects) > 0
    project_id = projects[0]["id"]
    print(f"[OK] Using project: {project_id}")

    # 3. Upload Level 02 PDF
    pdf_path = Path("floor plan/Dubai_Commercial_Floor_Plan_Level02.pdf")
    if not pdf_path.exists():
        pdf_path = Path("../floor plan/Dubai_Commercial_Floor_Plan_Level02.pdf")
    if not pdf_path.exists():
        pdf_path = backend_dir.parent / "floor plan" / "Dubai_Commercial_Floor_Plan_Level02.pdf"

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    files = {"file": (pdf_path.name, pdf_bytes, "application/pdf")}
    data = {"occupancy_type": "Business - Regular office areas", "sprinklered": "true", "scale": 100}
    res = client.post(f"/projects/{project_id}/drawings", files=files, data=data)
    assert res.status_code == 201, f"Upload failed: {res.text}"
    drawing_id = res.json()["drawing_id"]
    print(f"[OK] Uploaded drawing: {drawing_id} (Status: {res.json().get('status')}, Floor: {res.json().get('floor_name')})")

    # 4. Get Elements
    res = client.get(f"/drawings/{drawing_id}/elements")
    assert res.status_code == 200
    features = res.json().get("features", [])
    print(f"[OK] Extracted elements count: {len(features)}")
    rooms = [e for e in features if e["type"] == "room"]
    for rm in rooms:
        props = rm.get("properties", {})
        coords = rm.get("geometry", {}).get("coordinates", [[]])[0]
        print(f"  Room: {props.get('name', 'N/A'):<25} | Centroid: {props.get('centroid')} | Box: ({coords[0][0]:.2f}, {coords[0][1]:.2f}) -> ({coords[2][0]:.2f}, {coords[2][1]:.2f})")

    # 5. Get Violations
    res = client.get(f"/drawings/{drawing_id}/violations")
    assert res.status_code == 200
    violations = res.json()
    print(f"[OK] Violations count: {len(violations)}")
    for v in violations:
        coords = v.get("geometry", {}).get("coordinates")
        print(f"  Violation {v['id']}: {v['title'][:40]:<40} | Coords: {coords} | Severity: {v['severity']}")

    # 6. Test Multi-floor PDF
    multi_pdf_path = Path("floor plan/Dubai_Commercial_Building_FLS_Test_FloorPlans.pdf")
    if not multi_pdf_path.exists():
        multi_pdf_path = Path("../floor plan/Dubai_Commercial_Building_FLS_Test_FloorPlans.pdf")
    if not multi_pdf_path.exists():
        multi_pdf_path = backend_dir.parent / "floor plan" / "Dubai_Commercial_Building_FLS_Test_FloorPlans.pdf"

    with open(multi_pdf_path, "rb") as f:
        multi_bytes = f.read()

    files = {"file": (multi_pdf_path.name, multi_bytes, "application/pdf")}
    res = client.post(f"/projects/{project_id}/drawings", files=files, data=data)
    assert res.status_code == 201, f"Multi-floor upload failed: {res.text}"
    multi_res = res.json()
    multi_id = multi_res["drawing_id"]
    print(f"\n[OK] Uploaded multi-floor PDF: {multi_id} (Pages: {multi_res.get('pages_count')})")

    # Switch to Page 4 (Level 04)
    res = client.post(f"/drawings/{multi_id}/page", json={"page_index": 4})
    assert res.status_code == 200, f"Page select failed: {res.text}"
    p4_data = res.json()
    print(f"[OK] Switched to Page 4: {p4_data.get('floor_name')}")
    
    res = client.get(f"/drawings/{multi_id}/elements")
    assert res.status_code == 200
    p4_features = res.json().get("features", [])
    p4_rooms = [e for e in p4_features if e["type"] == "room"]
    for rm in p4_rooms:
        props = rm.get("properties", {})
        coords = rm.get("geometry", {}).get("coordinates", [[]])[0]
        print(f"  Room: {props.get('name', 'N/A'):<25} | Centroid: {props.get('centroid')} | Box: ({coords[0][0]:.2f}, {coords[0][1]:.2f}) -> ({coords[2][0]:.2f}, {coords[2][1]:.2f})")


if __name__ == "__main__":
    test_api_upload()

