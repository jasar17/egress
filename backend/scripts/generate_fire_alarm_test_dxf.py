import ezdxf
from pathlib import Path

def create_fire_alarm_test_dxf(output_path: str = "floor plan/Dubai_Commercial_Floor_Level_01_FireAlarm.dxf"):
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    # 1. Setup Standard Layers
    doc.layers.add("A-WALL-EXTR", color=7)
    doc.layers.add("A-WALL-INTR", color=8)
    doc.layers.add("FA-SMOKE", color=1)       # Red: Smoke Detectors
    doc.layers.add("FA-HEAT", color=2)        # Yellow: Heat Detectors
    doc.layers.add("FA-MCP", color=6)         # Magenta: Manual Call Points
    doc.layers.add("FA-SOUNDER", color=4)     # Cyan: Notification appliances
    doc.layers.add("FA-FACP", color=3)        # Green: Fire Alarm Control Panel
    doc.layers.add("FA-TEXT", color=7)        # Device Address Text Tags

    # 2. Add Background Building Envelope (42.0m x 24.0m in mm)
    envelope = [(0.0, 0.0), (42000.0, 0.0), (42000.0, 24000.0), (0.0, 24000.0)]
    msp.add_lwpolyline(envelope, close=True, dxfattribs={"layer": "A-WALL-EXTR"})

    # Corridor Spine Walls (Y = 10000 and Y = 14000)
    msp.add_line((3000.0, 10000.0), (39000.0, 10000.0), dxfattribs={"layer": "A-WALL-INTR"})
    msp.add_line((3000.0, 14000.0), (39000.0, 14000.0), dxfattribs={"layer": "A-WALL-INTR"})

    # Stair Enclosures
    msp.add_lwpolyline([(3000.0, 9000.0), (7000.0, 9000.0), (7000.0, 15000.0), (3000.0, 15000.0)], close=True, dxfattribs={"layer": "A-WALL-INTR"})
    msp.add_lwpolyline([(35000.0, 9000.0), (39000.0, 9000.0), (39000.0, 15000.0), (35000.0, 15000.0)], close=True, dxfattribs={"layer": "A-WALL-INTR"})

    # 3. Fire Alarm Devices Specification
    # Smoke Detectors (FA-SMOKE)
    smoke_devices = [
        ("SD-01", 13000.0, 5000.0),     # Open Office West
        ("SD-02", 13000.0, 8000.0),     # Open Office West
        ("SD-03", 19000.0, 5000.0),     # Open Office Central
        ("SD-04", 22000.0, 7500.0),     # Open Office Central
        ("SD-05", 25000.0, 5000.0),     # Open Office Central
        ("SD-06", 30000.0, 5000.0),     # Open Office East
        ("SD-07", 30000.0, 8000.0),     # Open Office East
        ("SD-08", 12500.0, 19000.0),    # Meeting Room 1A
        ("SD-09", 17500.0, 19000.0),    # Meeting Room 1B
        ("SD-10", 26500.0, 19000.0),    # Meeting Room 1C
        ("SD-11", 31000.0, 19000.0),    # Meeting Room 1D
        ("SD-12", 15000.0, 12000.0),    # Central Corridor West
        ("SD-13", 27000.0, 12000.0),    # Central Corridor East
    ]

    for tag, x, y in smoke_devices:
        msp.add_point((x, y), dxfattribs={"layer": "FA-SMOKE"})
        msp.add_circle((x, y), radius=250.0, dxfattribs={"layer": "FA-SMOKE"})
        msp.add_text(tag, dxfattribs={"layer": "FA-TEXT", "height": 300.0}).set_placement((x + 350.0, y - 150.0))

    # Heat Detectors (FA-HEAT) - Pantry / Breakout Room
    heat_devices = [
        ("HD-01", 22000.0, 19000.0),    # Pantry / Breakout Area
    ]
    for tag, x, y in heat_devices:
        msp.add_point((x, y), dxfattribs={"layer": "FA-HEAT"})
        msp.add_circle((x, y), radius=300.0, dxfattribs={"layer": "FA-HEAT"})
        msp.add_text(tag, dxfattribs={"layer": "FA-TEXT", "height": 300.0}).set_placement((x + 400.0, y - 150.0))

    # Manual Call Points (FA-MCP) - Exits and Corridors
    mcp_devices = [
        ("MCP-01", 7500.0, 12000.0),    # At West Exit Stair S-01 Door
        ("MCP-02", 34500.0, 12000.0),   # At East Exit Stair S-02 Door
        ("MCP-03", 21000.0, 12000.0),   # Central Corridor Midpoint
    ]
    for tag, x, y in mcp_devices:
        msp.add_point((x, y), dxfattribs={"layer": "FA-MCP"})
        # MCP square symbol (300mm box)
        box = [(x - 150.0, y - 150.0), (x + 150.0, y - 150.0), (x + 150.0, y + 150.0), (x - 150.0, y + 150.0)]
        msp.add_lwpolyline(box, close=True, dxfattribs={"layer": "FA-MCP"})
        msp.add_text(tag, dxfattribs={"layer": "FA-TEXT", "height": 300.0}).set_placement((x + 250.0, y - 150.0))

    # Sounders / Notification Appliances (FA-SOUNDER)
    sounder_devices = [
        ("SND-01", 11000.0, 12000.0),
        ("SND-02", 31000.0, 12000.0),
    ]
    for tag, x, y in sounder_devices:
        msp.add_point((x, y), dxfattribs={"layer": "FA-SOUNDER"})
        msp.add_text(tag, dxfattribs={"layer": "FA-TEXT", "height": 300.0}).set_placement((x + 250.0, y - 150.0))

    # Fire Alarm Control Panel (FA-FACP)
    msp.add_point((4000.0, 12000.0), dxfattribs={"layer": "FA-FACP"})
    facp_box = [(3700.0, 11700.0), (4300.0, 11700.0), (4300.0, 12300.0), (3700.0, 12300.0)]
    msp.add_lwpolyline(facp_box, close=True, dxfattribs={"layer": "FA-FACP"})
    msp.add_text("FACP-01", dxfattribs={"layer": "FA-TEXT", "height": 350.0}).set_placement((4500.0, 11850.0))

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(output_path)
    print(f"Successfully generated Fire Alarm DXF test fixture at: {output_path}")

if __name__ == "__main__":
    create_fire_alarm_test_dxf()
