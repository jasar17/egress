import sys
from pathlib import Path
import json

backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

from app.dxf_parser import parse_dxf_file
from app.pdf_parser import parse_pdf_file

dxf_file = backend_dir.parent / "floor plan" / "Dubai_Commercial_Floor_Level_01_Typical.dxf"
pdf_file = backend_dir.parent / "floor plan" / "Dubai_Commercial_Building_FLS_Test_FloorPlans.pdf"

dxf_data = parse_dxf_file(dxf_file)
pdf_data = parse_pdf_file(pdf_file, page_index=1)

print("=" * 80)
print("DXF DATA STRUCTURE")
print("=" * 80)
print(f"DXF summary: {json.dumps(dxf_data.get('summary', {}), indent=2)}")
print(f"DXF exits: {json.dumps(dxf_data.get('exits', []), indent=2)}")
print(f"DXF first 3 rooms centroids:")
for r in dxf_data.get("rooms", [])[:3]:
    print(f"  {r['name']}: centroid={r.get('centroid')}, svg_centroid={r.get('svg_centroid')}")

print("\n" + "=" * 80)
print("PDF DATA STRUCTURE")
print("=" * 80)
print(f"PDF summary: {json.dumps(pdf_data.get('summary', {}), indent=2)}")
print(f"PDF exits: {json.dumps(pdf_data.get('exits', []), indent=2)}")
print(f"PDF first 3 rooms centroids:")
for r in pdf_data.get("rooms", [])[:3]:
    print(f"  {r['name']}: centroid={r.get('centroid')}, svg_centroid={r.get('svg_centroid')}")
