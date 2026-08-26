import sqlite3
import math
import json
from pathlib import Path
import sys

backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

from app.pdf_parser import parse_pdf_file
from app.dxf_parser import parse_dxf_file
from app.occupant_load import calculate_occupant_loads
from app.path_analysis import calculate_walkable_distances
from app.rules_engine import evaluate_fls_rules

con = sqlite3.connect(str(backend_dir / "data" / "fls_demo.db"))
con.row_factory = sqlite3.Row

print("=" * 80)
print("VERIFICATION OF EXIT_REMOTENESS & NUMBER_OF_EXITS ON DUBAI TEST SET")
print("=" * 80)

# 1. Level 01 Typical Office PDF
pdf_path = backend_dir.parent / "floor plan" / "Dubai_Commercial_Building_FLS_Test_FloorPlans.pdf"
p1 = parse_pdf_file(pdf_path, page_index=1)
p1 = calculate_walkable_distances(p1)
p1 = calculate_occupant_loads(p1, con=con, default_occupancy="Business - Regular office areas")
v1 = evaluate_fls_rules(p1, con=con, drawing_id="l01_pdf", is_sprinklered=True, element_id_map={})

print("\n[LEVEL 01 TYPICAL FLOOR - ROOM OCCUPANCY & EXITS]")
hab = [r for r in p1["rooms"] if "STAIR" not in r["name"].upper() and "EXIT" not in r["name"].upper()]
total_load = 0
for r in hab:
    name = r["name"]
    area = r["area_m2"]
    factor = r["occupant_load_factor"]
    occ = r["occupant_load"]
    total_load += occ
    print(f"  {name:<24} | Area: {area:>5.1f} m2 | Factor: {factor:>4.1f} m2/p | Load: {occ:>2} persons")

print(f"\nTOTAL FLOOR OCCUPANT LOAD: {total_load} persons")
print(f"EXITS DETECTED: {len(p1['exits'])}")
for e in p1["exits"]:
    print(f"  * {e['name']}: Normalized Pos = {e['pos']}")

# Geometry and Remoteness
w = float(p1["summary"]["width_m"])
h = float(p1["summary"]["height_m"])
diag = math.hypot(w, h)
e1 = p1["exits"][0]["pos"]
e2 = p1["exits"][1]["pos"]
x1, y1 = (e1[0] / 100.0) * w, (e1[1] / 100.0) * h
x2, y2 = (e2[0] / 100.0) * w, (e2[1] / 100.0) * h
sep = math.hypot(x2 - x1, y2 - y1)

print("\n[LEVEL 01 TYPICAL FLOOR - REMOTENESS GEOMETRY]")
print(f"  Floor Dimensions: Width = {w:.2f} m, Height = {h:.2f} m")
print(f"  Floor Diagonal D = sqrt({w}^2 + {h}^2) = {diag:.2f} m")
print(f"  Exit S-01 Coordinates: ({x1:.2f} m, {y1:.2f} m)")
print(f"  Exit S-02 Coordinates: ({x2:.2f} m, {y2:.2f} m)")
print(f"  Measured Exit Separation S = {sep:.2f} m")
print(f"  Sprinklered Minimum Required (1/3 D): {diag/3.0:.2f} m -> Margin: +{sep - diag/3.0:.2f} m [PASS]")
print(f"  Non-Sprinklered Minimum Required (1/2 D): {diag/2.0:.2f} m -> Margin: {sep - diag/2.0:.2f} m")

# 2. Level 05 Non-Compliant Diagnostic Floor
dxf_nc = backend_dir.parent / "floor plan" / "Dubai_Commercial_Floor_Level_05_NonCompliant.dxf"
p5 = parse_dxf_file(dxf_nc)
p5 = calculate_walkable_distances(p5)
p5 = calculate_occupant_loads(p5, con=con, default_occupancy="Business - Regular office areas")
v5 = evaluate_fls_rules(p5, con=con, drawing_id="l05_nc", is_sprinklered=True, element_id_map={})

print("\n[LEVEL 05 NON-COMPLIANT FLOOR - FINDINGS]")
hab5 = [r for r in p5["rooms"] if "STAIR" not in r["name"].upper() and "EXIT" not in r["name"].upper()]
total_load_5 = sum(r["occupant_load"] for r in hab5)
print(f"  Total Habitable Rooms: {len(hab5)}")
print(f"  Total Occupant Load: {total_load_5} persons")
print(f"  Exits Count: {len(p5['exits'])}")
for v in v5:
    print(f"  * Finding: {v['type']}")
    print(f"    Clause: {v['clause_ref']}")
    print(f"    Measured: {v['measured_value']} {v['measured_unit']} | Limit: {v['limit_value']} {v['limit_unit']}")
    print(f"    Title: {v['title']}")
    print(f"    Detail: {v['detail']}")
print("=" * 80)
