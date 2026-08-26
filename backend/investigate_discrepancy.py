import json
import sqlite3
from pathlib import Path
from app.dxf_parser import parse_dxf_file
from app.pdf_parser import parse_pdf_drawing
from app.occupant_load import calculate_occupant_loads
from app.path_analysis import calculate_walkable_distances
from app.rules_engine import evaluate_fls_rules

# Connect to database
db_path = Path("data/fls_demo.db")
con = sqlite3.connect(str(db_path))
con.row_factory = sqlite3.Row

print("=" * 80)
print("INVESTIGATION 1: COMPARING ROOMS & GEOMETRY EXTRACTED")
print("=" * 80)

# 1. DXF Level 01 Typical
dxf_path = Path("../floor plan/Dubai_Commercial_Floor_Level_01_Typical.dxf")
if not dxf_path.exists():
    dxf_path = Path("floor plan/Dubai_Commercial_Floor_Level_01_Typical.dxf")

dxf_raw = parse_dxf_file(dxf_path)
print(f"\n--- DXF EXTRACTED ROOMS ({len(dxf_raw['rooms'])}) ---")
print(f"DXF Summary: {dxf_raw['summary']}")
for r in dxf_raw["rooms"]:
    print(f"  Room: {r['name']:<25} | Area: {r['area_m2']:>6.2f} m2 | Centroid: {r['centroid']}")

# 2. PDF Level 01 Typical (Page 1)
pdf_path = Path("../floor plan/Dubai_Commercial_Building_FLS_Test_FloorPlans.pdf")
if not pdf_path.exists():
    pdf_path = Path("floor plan/Dubai_Commercial_Building_FLS_Test_FloorPlans.pdf")

pdf_raw = parse_pdf_drawing(pdf_path, page_index=1)
print(f"\n--- PDF EXTRACTED ROOMS ({len(pdf_raw['rooms'])}) ---")
print(f"PDF Summary: {pdf_raw['summary']}")
for r in pdf_raw["rooms"]:
    occ_exp = r.get("occupant_load_explicit")
    print(f"  Room: {r['name']:<25} | Area: {r['area_m2']:>6.2f} m2 | Centroid: {r['centroid']} | Explicit Occ: {occ_exp}")

print("\n" + "=" * 80)
print("INVESTIGATION 2: OCCUPANT LOAD CALCULATION")
print("=" * 80)

dxf_occ = calculate_occupant_loads(dxf_raw, con, "Business - Regular office areas")
print(f"\n--- DXF OCCUPANT LOADS ---")
dxf_habitable = [r for r in dxf_occ["rooms"] if "STAIR" not in r["name"].upper() and "EXIT" not in r["name"].upper()]
print(f"Total Occupants: {sum(r['occupant_load'] for r in dxf_habitable)}")
for r in dxf_occ["rooms"]:
    print(f"  {r['name']:<25} | Area: {r['area_m2']:>6.2f} m2 | Occ Load: {r['occupant_load']:>3} | Note: {r['occupancy_note']}")

pdf_occ = calculate_occupant_loads(pdf_raw, con, "Business - Regular office areas")
print(f"\n--- PDF OCCUPANT LOADS ---")
pdf_habitable = [r for r in pdf_occ["rooms"] if "STAIR" not in r["name"].upper() and "EXIT" not in r["name"].upper()]
print(f"Total Occupants: {sum(r['occupant_load'] for r in pdf_habitable)}")
for r in pdf_occ["rooms"]:
    print(f"  {r['name']:<25} | Area: {r['area_m2']:>6.2f} m2 | Occ Load: {r['occupant_load']:>3} | Note: {r['occupancy_note']}")

print("\n" + "=" * 80)
print("INVESTIGATION 3: PATH ANALYSIS & DISTANCE CALCULATION")
print("=" * 80)

dxf_paths = calculate_walkable_distances(dxf_occ)
print(f"\n--- DXF PATH DISTANCES ---")
print(f"DXF Exits: {dxf_paths['exits']}")
for r in dxf_paths["rooms"]:
    print(f"  {r['name']:<25} | Travel Dist: {r.get('travel_distance_m'):>6.2f} m | Nearest Exit: {r.get('nearest_exit')}")

pdf_paths = calculate_walkable_distances(pdf_occ)
print(f"\n--- PDF PATH DISTANCES ---")
print(f"PDF Exits: {pdf_paths['exits']}")
for r in pdf_paths["rooms"]:
    print(f"  {r['name']:<25} | Travel Dist: {r.get('travel_distance_m'):>6.2f} m | Nearest Exit: {r.get('nearest_exit')}")
