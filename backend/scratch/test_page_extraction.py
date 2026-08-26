import sys
from pathlib import Path
import sqlite3
import pymupdf

pdf_path = Path("floor plan/UAE Fire and Life Safety Code of Practice.pdf")
doc = pymupdf.open(str(pdf_path))

# Check page 285 (0-indexed 284)
for pg in [285, 293, 294, 301, 75, 1051, 1088]:
    # Page numbers in PDF: let's check both 0-indexed and 1-indexed
    # When doc index is pg - 1:
    p = doc[pg - 1]
    text = p.get_text()
    print(f"\n" + "="*80)
    print(f"PAGE {pg} (Index {pg - 1})")
    print("="*80)
    print(text[:600])
