import sys
from pathlib import Path
import networkx as nx
import math

backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

from app.dxf_parser import parse_dxf_file
from app.pdf_parser import parse_pdf_file

dxf_file = backend_dir.parent / "floor plan" / "Dubai_Commercial_Floor_Level_01_Typical.dxf"
pdf_file = backend_dir.parent / "floor plan" / "Dubai_Commercial_Building_FLS_Test_FloorPlans.pdf"

dxf_parsed = parse_dxf_file(dxf_file)
pdf_parsed = parse_pdf_file(pdf_file, page_index=1)

print("=" * 80)
print("TRACING DXF PATH ANALYSIS")
print("=" * 80)
summary = dxf_parsed.get("summary", {})
unit_multiplier = summary.get("unit_multiplier", 1.0)
width_m = summary.get("width_m", 42.0)
height_m = summary.get("height_m", 24.0)
print(f"DXF summary unit_multiplier={unit_multiplier}, width_m={width_m}, height_m={height_m}")

for r in dxf_parsed["rooms"][:3]:
    centroid_raw = r.get("svg_centroid") or r.get("centroid", [50, 35])
    centroid_m = (centroid_raw[0] * unit_multiplier, centroid_raw[1] * unit_multiplier)
    print(f"Room: {r['name']}")
    print(f"  centroid in parsed_data: {centroid_raw}")
    print(f"  centroid_m computed as:  {centroid_m} (multiplied by {unit_multiplier})")

for e in dxf_parsed["exits"]:
    pos = e["pos"]
    pos_m = (pos[0] * unit_multiplier, pos[1] * unit_multiplier)
    print(f"Exit: {e.get('name')}")
    print(f"  pos in parsed_data: {pos}")
    print(f"  pos_m computed as:  {pos_m} (multiplied by {unit_multiplier})")

print("\n" + "=" * 80)
print("TRACING PDF PATH ANALYSIS")
print("=" * 80)
pdf_summary = pdf_parsed.get("summary", {})
pdf_unit_multiplier = pdf_summary.get("unit_multiplier", 1.0)
pdf_width_m = pdf_summary.get("width_m", 42.0)
pdf_height_m = pdf_summary.get("height_m", 24.0)
print(f"PDF summary unit_multiplier={pdf_unit_multiplier}, width_m={pdf_width_m}, height_m={pdf_height_m}")

for r in pdf_parsed["rooms"][:3]:
    centroid_raw = r.get("svg_centroid") or r.get("centroid", [50, 35])
    centroid_m = (centroid_raw[0] * pdf_unit_multiplier, centroid_raw[1] * pdf_unit_multiplier)
    print(f"Room: {r['name']}")
    print(f"  centroid in parsed_data: {centroid_raw}")
    print(f"  centroid_m computed as:  {centroid_m} (multiplied by {pdf_unit_multiplier})")

for e in pdf_parsed["exits"]:
    pos = e["pos"]
    pos_m = (pos[0] * pdf_unit_multiplier, pos[1] * pdf_unit_multiplier)
    print(f"Exit: {e.get('name')}")
    print(f"  pos in parsed_data: {pos}")
    print(f"  pos_m computed as:  {pos_m} (multiplied by {pdf_unit_multiplier})")
