import sys
from pathlib import Path
import pymupdf

pdf_path = Path("floor plan/UAE Fire and Life Safety Code of Practice.pdf")
if not pdf_path.exists():
    pdf_path = Path("../floor plan/UAE Fire and Life Safety Code of Practice.pdf")

if pdf_path.exists():
    doc = pymupdf.open(str(pdf_path))
    print(f"Found Code PDF: {pdf_path}")
    print(f"Total Pages: {len(doc)}")
    for i in range(min(5, len(doc))):
        print(f"Page {i+1} sample: {doc[i].get_text()[:200]!r}")
else:
    print("Code PDF not found.")
