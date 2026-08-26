import os
from pathlib import Path
import ezdxf

OUTPUT_DIR = Path(__file__).resolve().parents[2] / "floor plan"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def create_floor_dxf(filename: str, floor_name: str, rooms_layout: list[dict], stairs: list[dict], doors: list[dict]):
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    # Create layers
    doc.layers.add(name="A-WALL-EXTR", color=7)
    doc.layers.add(name="A-WALL-INTR", color=8)
    doc.layers.add(name="A-AREA-ROOM", color=4)
    doc.layers.add(name="A-DOOR", color=2)
    doc.layers.add(name="A-EXIT", color=1)
    doc.layers.add(name="A-TEXT", color=3)

    # Building perimeter: 42.0m x 24.0m in millimeters (42000 x 24000)
    w, h = 42000, 24000
    perimeter = [(0, 0), (w, 0), (w, h), (0, h)]
    msp.add_lwpolyline(perimeter, close=True, dxfattribs={"layer": "A-WALL-EXTR"})

    # Central Corridor: Y from 10000 to 14000, X from 3000 to 39000
    corridor = [(3000, 10000), (39000, 10000), (39000, 14000), (3000, 14000)]
    msp.add_lwpolyline(corridor, close=True, dxfattribs={"layer": "A-WALL-INTR"})
    msp.add_text("MAIN CORRIDOR", dxfattribs={"layer": "A-TEXT", "height": 600, "insert": (21000, 12000)})

    # Rooms
    for r in rooms_layout:
        pts = r["points"]
        msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "A-AREA-ROOM"})
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        msp.add_text(r["name"], dxfattribs={"layer": "A-TEXT", "height": 500, "insert": (cx - 1500, cy)})

    # Exit Stairs
    for s in stairs:
        pts = s["points"]
        msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "A-EXIT"})
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        msp.add_text(s["name"], dxfattribs={"layer": "A-EXIT", "height": 600, "insert": (cx - 1200, cy)})

    # Doors
    for d in doors:
        pos = d["pos"]
        layer = "A-EXIT" if d.get("is_exit") else "A-DOOR"
        msp.add_circle(pos, radius=450, dxfattribs={"layer": layer})
        msp.add_text(d["name"], dxfattribs={"layer": "A-TEXT", "height": 350, "insert": (pos[0] + 500, pos[1])})

    file_path = OUTPUT_DIR / filename
    doc.saveas(str(file_path))
    print(f"Generated DXF: {file_path}")


def generate_all():
    # Common Exit Stairs (S-01 West, S-02 East)
    stair_w = [(500, 9500), (3000, 9500), (3000, 14500), (500, 14500)]
    stair_e = [(39000, 9500), (41500, 9500), (41500, 14500), (39000, 14500)]
    stairs = [
        {"name": "EXIT STAIR S-01", "points": stair_w},
        {"name": "EXIT STAIR S-02", "points": stair_e},
    ]

    # --- Floor 00: Ground Floor ---
    f00_rooms = [
        {"name": "RECEPTION & LOBBY", "points": [(3000, 14000), (21000, 14000), (21000, 23500), (3000, 23500)]},
        {"name": "FACILITIES OFFICE", "points": [(21000, 14000), (31000, 14000), (31000, 23500), (21000, 23500)]},
        {"name": "SECURITY / CONTROL", "points": [(31000, 14000), (39000, 14000), (39000, 23500), (31000, 23500)]},
        {"name": "CAFE / LOUNGE", "points": [(3000, 500), (15000, 500), (15000, 10000), (3000, 10000)]},
        {"name": "PLANT ROOM", "points": [(15000, 500), (25000, 500), (25000, 10000), (15000, 10000)]},
        {"name": "ELEC / IT ROOM", "points": [(25000, 500), (32000, 500), (32000, 10000), (25000, 10000)]},
        {"name": "RESTROOMS (M/F)", "points": [(32000, 500), (39000, 500), (39000, 10000), (32000, 10000)]},
    ]
    f00_doors = [
        {"name": "EXIT S-01 DOOR", "pos": (3000, 12000), "is_exit": True},
        {"name": "EXIT S-02 DOOR", "pos": (39000, 12000), "is_exit": True},
        {"name": "MAIN ENTRANCE EXIT", "pos": (21000, 23800), "is_exit": True},
        {"name": "SERVICE EXIT", "pos": (21000, 200), "is_exit": True},
    ]
    create_floor_dxf("Dubai_Commercial_Floor_Level_00_Ground.dxf", "Level 00 - Ground", f00_rooms, stairs, f00_doors)

    # --- Floor 01: Typical Office Floor ---
    f01_rooms = [
        {"name": "OPEN OFFICE NORTH", "points": [(3000, 14000), (23000, 14000), (23000, 23500), (3000, 23500)]},
        {"name": "OPEN OFFICE EAST", "points": [(23000, 14000), (39000, 14000), (39000, 23500), (23000, 23500)]},
        {"name": "MEETING ROOM 1A", "points": [(3000, 500), (10000, 500), (10000, 10000), (3000, 10000)]},
        {"name": "MEETING ROOM 1B", "points": [(10000, 500), (17000, 500), (17000, 10000), (10000, 10000)]},
        {"name": "PANTRY / BREAKOUT", "points": [(17000, 500), (24000, 500), (24000, 10000), (17000, 10000)]},
        {"name": "MEETING ROOM 1C", "points": [(24000, 500), (31000, 500), (31000, 10000), (24000, 10000)]},
        {"name": "MEETING ROOM 1D", "points": [(31000, 500), (39000, 500), (39000, 10000), (31000, 10000)]},
    ]
    f01_doors = [
        {"name": "EXIT S-01 DOOR", "pos": (3000, 12000), "is_exit": True},
        {"name": "EXIT S-02 DOOR", "pos": (39000, 12000), "is_exit": True},
        {"name": "NORTH OFFICE DOOR", "pos": (13000, 14000), "is_exit": False},
        {"name": "EAST OFFICE DOOR", "pos": (31000, 14000), "is_exit": False},
    ]
    create_floor_dxf("Dubai_Commercial_Floor_Level_01_Typical.dxf", "Level 01 - Typical Office", f01_rooms, stairs, f01_doors)
    create_floor_dxf("Dubai_Commercial_Floor_Level_02_Typical.dxf", "Level 02 - Typical Office", f01_rooms, stairs, f01_doors)
    create_floor_dxf("Dubai_Commercial_Floor_Level_03_Typical.dxf", "Level 03 - Typical Office", f01_rooms, stairs, f01_doors)

    # --- Floor 04: Executive Floor ---
    f04_rooms = [
        {"name": "EXECUTIVE BOARDROOM", "points": [(3000, 14000), (18000, 14000), (18000, 23500), (3000, 23500)]},
        {"name": "EXECUTIVE LOUNGE", "points": [(18000, 14000), (30000, 14000), (30000, 23500), (18000, 23500)]},
        {"name": "CONFERENCE ROOM", "points": [(3000, 500), (10000, 500), (10000, 10000), (3000, 10000)]},
        {"name": "EXEC CABIN 1", "points": [(10000, 500), (17000, 500), (17000, 10000), (10000, 10000)]},
        {"name": "EXEC CABIN 2", "points": [(17000, 500), (24000, 500), (24000, 10000), (17000, 10000)]},
        {"name": "EXEC CABIN 3", "points": [(24000, 500), (31000, 500), (31000, 10000), (24000, 10000)]},
        {"name": "EXEC CABIN 4", "points": [(31000, 500), (39000, 500), (39000, 10000), (31000, 10000)]},
    ]
    f04_doors = [
        {"name": "EXIT S-01 DOOR", "pos": (3000, 12000), "is_exit": True},
        {"name": "EXIT S-02 DOOR", "pos": (39000, 12000), "is_exit": True},
        {"name": "BOARDROOM DOOR", "pos": (10500, 14000), "is_exit": False},
        {"name": "LOUNGE DOOR", "pos": (24000, 14000), "is_exit": False},
    ]
    create_floor_dxf("Dubai_Commercial_Floor_Level_04_Executive.dxf", "Level 04 - Executive", f04_rooms, stairs, f04_doors)

    # --- Floor 05: Non-Compliant Test Floor (Large Hall > 280 m2 & Extended Wing) ---
    f05_rooms = [
        # Large open space 36m x 10m = 360 m2 (> 280 m2 limit per UAE-FLS-3.19-BUS-ROOM-AREA)
        {"name": "GRAND OPEN HALL", "points": [(3000, 13000), (39000, 13000), (39000, 23500), (3000, 23500)]},
        {"name": "TRAINING ROOM A", "points": [(3000, 500), (18000, 500), (18000, 10000), (3000, 10000)]},
        {"name": "TRAINING ROOM B", "points": [(18000, 500), (39000, 500), (39000, 10000), (18000, 10000)]},
    ]
    # Single exit only at East end (insufficient exit redundancy / remoteness)
    f05_stairs = [{"name": "EXIT STAIR S-02", "points": stair_e}]
    f05_doors = [
        {"name": "EXIT S-02 DOOR", "pos": (39000, 12000), "is_exit": True},
        {"name": "HALL ENTRY DOOR", "pos": (21000, 13000), "is_exit": False},
    ]
    create_floor_dxf("Dubai_Commercial_Floor_Level_05_NonCompliant.dxf", "Level 05 - Non-Compliant Test", f05_rooms, f05_stairs, f05_doors)



if __name__ == "__main__":
    generate_all()
