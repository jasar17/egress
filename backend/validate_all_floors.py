"""
Comprehensive FLS Validation Runner:
Executes the full real pipeline (Tasks 2 - 6) across all floors of the Dubai Commercial Building.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from app.dxf_parser import parse_dxf_file
from app.occupant_load import calculate_occupant_loads
from app.path_analysis import calculate_walkable_distances
from app.pdf_parser import parse_pdf_file
from app.rules_engine import evaluate_fls_rules


def run_validation():
    db_path = backend_dir / "data" / "fls_demo.db"
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row

    floor_files = [
        ("Level 00 - Ground Floor (Main Lobby & Retail)", "Dubai_Commercial_Floor_Level_00_Ground.dxf", 0),
        ("Level 01 - Typical Office Floor", "Dubai_Commercial_Floor_Level_01_Typical.dxf", 0),
        ("Level 02 - Typical Office Floor", "Dubai_Commercial_Floor_Level_02_Typical.dxf", 0),
        ("Level 03 - Typical Office Floor", "Dubai_Commercial_Floor_Level_03_Typical.dxf", 0),
        ("Level 04 - Executive Floor (Boardroom & Cabins)", "Dubai_Commercial_Floor_Level_04_Executive.dxf", 0),
        ("Level 05 - Non-Compliant Diagnostic Test Floor", "Dubai_Commercial_Floor_Level_05_NonCompliant.dxf", 0),
        ("Level 02 - Layout Plan (PDF Single Floor)", "Dubai_Commercial_Floor_Plan_Level02.pdf", 0),
        ("Level 00 - Ground Floor (PDF Set Page 0)", "Dubai_Commercial_Building_FLS_Test_FloorPlans.pdf", 0),
        ("Level 01 - Typical Office (PDF Set Page 1)", "Dubai_Commercial_Building_FLS_Test_FloorPlans.pdf", 1),
        ("Level 02 - Typical Office (PDF Set Page 2)", "Dubai_Commercial_Building_FLS_Test_FloorPlans.pdf", 2),
        ("Level 03 - Typical Office (PDF Set Page 3)", "Dubai_Commercial_Building_FLS_Test_FloorPlans.pdf", 3),
        ("Level 04 - Executive Floor (PDF Set Page 4)", "Dubai_Commercial_Building_FLS_Test_FloorPlans.pdf", 4),
    ]

    floor_plan_dir = Path(__file__).resolve().parents[1] / "floor plan"

    results = []

    print("=" * 100)
    print(" DUBAI COMMERCIAL BUILDING - FULL FLS CODE COMPLIANCE VALIDATION REPORT")
    print(" UAE Fire & Life Safety Code of Practice (Chapter 3: Means of Egress)")
    print("=" * 100)

    for floor_title, filename, page_idx in floor_files:
        filepath = floor_plan_dir / filename
        if not filepath.exists():
            print(f"[WARN] File not found: {filepath}")
            continue

        print(f"\n" + "#" * 90)
        print(f" PROCESSING: {floor_title}")
        print(f" Source File: {filename} (Page: {page_idx})")
        print("#" * 90)

        # 1. Parse DXF or PDF
        if filename.lower().endswith(".dxf"):
            parsed = parse_dxf_file(str(filepath))
        else:
            parsed = parse_pdf_file(str(filepath), page_index=page_idx)

        # 2. Path Analysis (Task 3)
        parsed = calculate_walkable_distances(parsed)
        # 3. Occupant Load (Task 4)
        parsed = calculate_occupant_loads(parsed, con=con, default_occupancy="Business - Regular office areas")

        # 4. Rules Evaluation (Task 5 & 6)
        element_id_map = {r["name"]: f"elem-{i}" for i, r in enumerate(parsed["rooms"])}
        
        # Sprinklered evaluation (Standard)
        violations_sprinklered = evaluate_fls_rules(
            parsed,
            con=con,
            drawing_id=filename,
            element_id_map=element_id_map,
            is_sprinklered=True,
            occupancy_type="Business - Regular office areas",
        )

        # Non-Sprinklered evaluation (Comparative)
        violations_nonsprinklered = evaluate_fls_rules(
            parsed,
            con=con,
            drawing_id=filename,
            element_id_map=element_id_map,
            is_sprinklered=False,
            occupancy_type="Business - Regular office areas",
        )

        summary = parsed["summary"]
        rooms = parsed["rooms"]
        habitable_rooms = [r for r in rooms if "STAIR" not in r["name"].upper() and "EXIT" not in r["name"].upper()]
        total_load = sum(r.get("occupant_load", 0) for r in habitable_rooms)

        floor_record = {
            "title": floor_title,
            "filename": filename,
            "elements_count": len(parsed["elements"]),
            "walls_count": summary["walls_count"],
            "rooms_count": len(rooms),
            "doors_count": summary["doors_count"],
            "exits_count": summary["exits_count"],
            "total_occupant_load": total_load,
            "rooms": rooms,
            "violations_sprinklered": violations_sprinklered,
            "violations_nonsprinklered": violations_nonsprinklered,
        }
        results.append(floor_record)

        print(f"Summary: Extracted {floor_record['elements_count']} elements ({summary['walls_count']} walls, {len(rooms)} rooms, {summary['doors_count']} doors, {summary['exits_count']} exits).")
        print(f"Total Floor Occupant Load: {total_load} persons across {len(habitable_rooms)} habitable spaces.")
        print("\nRoom Egress & Occupancy Breakdown:")
        print(f"  { 'Room Name':<26} | {'Area (m2)':<10} | {'Factor':<8} | {'Occ Load':<10} | {'Travel Dist':<12} | {'Nearest Exit':<15}")
        print("  " + "-" * 92)
        for r in rooms:
            print(f"  {r['name']:<26} | {r['area_m2']:>8.1f} m2 | {r['occupant_load_factor']:>6.1f} | {r['occupant_load']:>4} persons | {r.get('travel_distance_m', 0.0):>9.2f} m | {r.get('nearest_exit', 'N/A'):<15}")

        print(f"\nCode Compliance Findings (Sprinklered Mode): {len(violations_sprinklered)} violation(s)")
        if violations_sprinklered:
            for v in violations_sprinklered:
                print(f"  [!] {v['type']}: {v['title']} (Clause: {v['clause_ref']}, Measured: {v['measured_value']} {v['measured_unit']}, Limit: {v['limit_value']} {v['limit_unit']})")
        else:
            print("  [OK] 100% Compliant with UAE FLS Code 2018 (All travel distances <= 91m, areas <= 280m2, exit count >= 2).")

        if len(violations_nonsprinklered) != len(violations_sprinklered):
            print(f"Comparative Non-Sprinklered Mode: {len(violations_nonsprinklered)} violation(s) flagged under stricter 61m travel limit.")

    print("\n" + "=" * 100)
    print(" SUMMARY VALIDATION TABLE ACROSS ALL FLOORS")
    print("=" * 100)
    print(f"{ 'Floor':<32} | {'Rooms':<6} | {'Exits':<6} | {'Total Load':<11} | {'Max Travel':<11} | {'Sprinklered Violations':<24} | {'Status'}")
    print("-" * 115)
    for res in results:
        max_dist = max([r.get("travel_distance_m", 0.0) for r in res["rooms"]]) if res["rooms"] else 0.0
        v_count = len(res["violations_sprinklered"])
        status = "COMPLIANT" if v_count == 0 else f"NON-COMPLIANT ({v_count} findings)"
        print(f"{res['title']:<32} | {res['rooms_count']:>5} | {res['exits_count']:>5} | {res['total_occupant_load']:>9} p | {max_dist:>9.2f} m | {v_count:>22} | {status}")

    return results


if __name__ == "__main__":
    run_validation()
