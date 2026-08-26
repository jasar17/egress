import requests
from pathlib import Path

pdf_path = Path("floor plan/Dubai_Commercial_Floor_Plan_Level02.pdf")
with open(pdf_path, "rb") as f:
    files = {"file": ("Dubai_Commercial_Floor_Plan_Level02.pdf", f, "application/pdf")}
    data = {"occupancy_type": "Business - Regular office areas", "sprinklered": "true", "scale": 100}
    r = requests.post("http://127.0.0.1:8000/projects/project-al-noor/drawings", files=files, data=data)
    print("Upload Status:", r.status_code)
    res = r.json()
    did = res["drawing_id"]
    print("Drawing ID:", did)

r_el = requests.get(f"http://127.0.0.1:8000/drawings/{did}/elements")
features = r_el.json()["features"]
print(f"Extracted {len(features)} features on live server:")
for f in features:
    if f["type"] == "room":
        print(f"  Room: {f['properties']['name']} -> {f['geometry']['coordinates'][0]}")
    elif f["type"] == "exit":
        print(f"  Exit: {f['properties']['name']} -> {f['geometry']['coordinates']}")
