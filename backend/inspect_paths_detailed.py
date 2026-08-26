import pymupdf

def inspect(path):
    print("=" * 80)
    print(f"FILE: {path}")
    doc = pymupdf.open(path)
    for p_idx, page in enumerate(doc):
        pw, ph = page.rect.width, page.rect.height
        print(f"\n--- PAGE {p_idx} (Size: {pw:.2f} x {ph:.2f}, AR: {pw/ph:.4f}) ---")
        print("\n--- TEXT BLOCKS ---")
        for b in page.get_text("blocks"):
            text = b[4].strip().replace('\n', ' ')
            x0, y0, x1, y1 = b[0], b[1], b[2], b[3]
            print(f"{text[:45]:<45} | pt=({x0:5.1f}, {y0:5.1f}, {x1:5.1f}, {y1:5.1f}) | % = ({x0/pw*100:4.1f}%, {y0/ph*100:4.1f}%, {x1/pw*100:4.1f}%, {y1/ph*100:4.1f}%)")

        print("\n--- VECTOR DRAWINGS ---")
        for i, d in enumerate(page.get_drawings()):
            r = d['rect']
            items = d.get('items', [])
            print(f"Drawing {i:02d}: rect=({r.x0:5.1f}, {r.y0:5.1f}, {r.x1:5.1f}, {r.y1:5.1f}) | % = ({r.x0/pw*100:4.1f}%, {r.y0/ph*100:4.1f}%) to ({r.x1/pw*100:4.1f}%, {r.y1/ph*100:4.1f}%) | items={len(items)}")
            for it in items:
                if it[0] == 'l':
                    p1, p2 = it[1], it[2]
                    print(f"   LINE: ({p1.x/pw*100:4.1f}%, {p1.y/ph*100:4.1f}%) -> ({p2.x/pw*100:4.1f}%, {p2.y/ph*100:4.1f}%) [pts: ({p1.x:.1f}, {p1.y:.1f}) -> ({p2.x:.1f}, {p2.y:.1f})]")
                elif it[0] == 're':
                    rc = it[1]
                    print(f"   RECT: ({rc.x0/pw*100:4.1f}%, {rc.y0/ph*100:4.1f}%) -> ({rc.x1/pw*100:4.1f}%, {rc.y1/ph*100:4.1f}%) [pts: ({rc.x0:.1f}, {rc.y0:.1f}) -> ({rc.x1:.1f}, {rc.y1:.1f})]")

if __name__ == '__main__':
    inspect('../floor plan/Dubai_Commercial_Floor_Plan_Level02.pdf')
