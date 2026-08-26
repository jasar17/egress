import sys
from pathlib import Path
import sqlite3
import json

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

from app.dxf_parser import parse_dxf_file
from app.pdf_parser import parse_pdf_file
from app.occupant_load import calculate_occupant_loads
from app.path_analysis import calculate_walkable_distances
from app.rules_engine import evaluate_fls_rules

# DB connection
db_path = backend_dir / "data" / "fls_demo.db"
con = sqlite3.connect(str(db_path))
con.row_factory = sqlite3.Row

print("=" * 100)
print("COMPARING DXF AND PDF TEST FILES FOR TYPICAL OFFICE FLOOR")
print("=" * 100)

dxf_file = backend_dir.parent / "floor plan" / "Dubai_Commercial_Floor_Level_01_Typical.dxf"
pdf_file = backend_dir.parent / "floor plan" / "Dubai_Commercial_Building_FLS_Test_FloorPlans.pdf"

print(f"\nDXF file exists: {dxf_file.exists()} ({dxf_file})")
print(f"PDF file exists: {pdf_file.exists()} ({pdf_file})")

# 1. Parse DXF
dxf_parsed = parse_dxf_file(dxf_file)
dxf_occ = calculate_occupant_loads(dxf_parsed, con, "Business - Regular office areas")
dxf_paths = calculate_walkable_distances(dxf_occ)
dxf_rules_s = evaluate_fls_rules(dxf_paths, con, drawing_id="test_dxf", element_id_map={}, is_sprinklered=True)
dxf_rules_ns = evaluate_fls_rules(dxf_paths, con, drawing_id="test_dxf", element_id_map={}, is_sprinklered=False)

# 2. Parse PDF Page 1 (Typical Floor)
pdf_parsed = parse_pdf_file(pdf_file, page_index=1)
pdf_occ = calculate_occupant_loads(pdf_parsed, con, "Business - Regular office areas")
pdf_paths = calculate_walkable_distances(pdf_occ)
pdf_rules_s = evaluate_fls_rules(pdf_paths, con, drawing_id="test_pdf", element_id_map={}, is_sprinklered=True)
pdf_rules_ns = evaluate_fls_rules(pdf_paths, con, drawing_id="test_pdf", element_id_map={}, is_sprinklered=False)

print("\n" + "#" * 100)
print("1. ROOM BREAKDOWN & OCCUPANT LOAD COMPARISON")
print("#" * 100)

print("\n--- DXF ROOMS (Dubai_Commercial_Floor_Level_01_Typical.dxf) ---")
print(f"Summary: {dxf_parsed['summary']}")
print(f"{'Room Name':<30} | {'Area (m2)':<10} | {'Explicit Occ':<12} | {'Computed Occ':<12} | {'Centroid':<25} | {'Occ Note'}")
print("-" * 110)
for r in dxf_occ["rooms"]:
    print(f"{r['name']:<30} | {r['area_m2']:<10.2f} | {str(r.get('occupant_load_explicit')):<12} | {r['occupant_load']:<12} | {str(r['centroid']):<25} | {r['occupancy_note']}")

print("\n--- PDF ROOMS (Dubai_Commercial_Building_FLS_Test_FloorPlans.pdf - Page 1) ---")
print(f"Summary: {pdf_parsed['summary']}")
print(f"{'Room Name':<30} | {'Area (m2)':<10} | {'Explicit Occ':<12} | {'Computed Occ':<12} | {'Centroid':<25} | {'Occ Note'}")
print("-" * 110)
for r in pdf_occ["rooms"]:
    print(f"{r['name']:<30} | {r['area_m2']:<10.2f} | {str(r.get('occupant_load_explicit')):<12} | {r['occupant_load']:<12} | {str(r['centroid']):<25} | {r['occupancy_note']}")

print("\n" + "#" * 100)
print("2. PATH DISTANCE & ROUTING COMPARISON")
print("#" * 100)

print("\n--- DXF EXITS & DOORS ---")
print(f"Exits: {dxf_paths.get('exits')}")
print(f"Doors: {dxf_paths.get('doors')}")
print(f"\n--- DXF PATH DISTANCES ---")
print(f"{'Room Name':<30} | {'Travel Dist (m)':<15} | {'Nearest Exit':<25} | {'Path Points Count'}")
print("-" * 90)
for r in dxf_paths["rooms"]:
    print(f"{r['name']:<30} | {r.get('travel_distance_m', 0):<15.2f} | {str(r.get('nearest_exit')):<25} | {len(r.get('egress_path', []))}")

print("\n--- PDF EXITS & DOORS ---")
print(f"Exits: {pdf_paths.get('exits')}")
print(f"Doors: {pdf_paths.get('doors')}")
print(f"\n--- PDF PATH DISTANCES ---")
print(f"{'Room Name':<30} | {'Travel Dist (m)':<15} | {'Nearest Exit':<25} | {'Path Points Count'}")
print("-" * 90)
for r in pdf_paths["rooms"]:
    print(f"{r['name']:<30} | {r.get('travel_distance_m', 0):<15.2f} | {str(r.get('nearest_exit')):<25} | {len(r.get('egress_path', []))}")

print("\n" + "#" * 100)
print("3. RULES EVALUATION & FINDINGS")
print("#" * 100)
print(f"DXF Sprinklered Violations: {len(dxf_rules_s)}")
for v in dxf_rules_s:
    print(f"  [{v['code_clause_id']}] {v['title']}: {v['description']}")

print(f"\nPDF Sprinklered Violations: {len(pdf_rules_s)}")
for v in pdf_rules_s:
    print(f"  [{v['code_clause_id']}] {v['title']}: {v['description']}")
