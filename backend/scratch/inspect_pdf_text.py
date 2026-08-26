import sys
from pathlib import Path
import pymupdf

backend_dir = Path(__file__).resolve().parents[1]
pdf_path = backend_dir.parent / "floor plan" / "Dubai_Commercial_Building_FLS_Test_FloorPlans.pdf"

doc = pymupdf.open(str(pdf_path))
print(f"Total pages: {len(doc)}")

for i in range(len(doc)):
    page = doc[i]
    print(f"\n=================== PAGE {i} TEXT ===================")
    print(page.get_text())
