import pymupdf

def test_extract(pdf_path, page_idx=0):
    doc = pymupdf.open(pdf_path)
    page = doc[page_idx]
    pw, ph = page.rect.width, page.rect.height
    print(f"\n==========================================")
    print(f"FILE: {pdf_path} (Page {page_idx}: {pw:.1f} x {ph:.1f})")
    print(f"==========================================")
    
    # 1. Text blocks
    texts = []
    for b in page.get_text('blocks'):
        txt = b[4].strip()
        texts.append({
            'text': txt,
            'rect': (b[0], b[1], b[2], b[3]),
            'pct_rect': (b[0]/pw*100, b[1]/ph*100, b[2]/pw*100, b[3]/ph*100),
            'centroid': ((b[0]+b[2])/2 / pw * 100, (b[1]+b[3])/2 / ph * 100)
        })
    
    # 2. Vector rectangles and closed polylines
    drawings = page.get_drawings()
    rects = []
    lines = []
    for d in drawings:
        r = d['rect']
        w_pct = (r.x1 - r.x0) / pw * 100
        h_pct = (r.y1 - r.y0) / ph * 100
        for it in d.get('items', []):
            if it[0] == 're':
                rc = it[1]
                rw_pct = (rc.x1 - rc.x0) / pw * 100
                rh_pct = (rc.y1 - rc.y0) / ph * 100
                if 2.0 < rw_pct < 85.0 and 2.0 < rh_pct < 85.0:
                    rects.append({
                        'rect': (rc.x0, rc.y0, rc.x1, rc.y1),
                        'pct': (rc.x0/pw*100, rc.y0/ph*100, rc.x1/pw*100, rc.y1/ph*100),
                        'w_m': (rc.x1 - rc.x0) / pw * 42.0,
                        'h_m': (rc.y1 - rc.y0) / ph * 24.0,
                    })
            elif it[0] == 'l':
                p1, p2 = it[1], it[2]
                lines.append([(p1.x/pw*100, p1.y/ph*100), (p2.x/pw*100, p2.y/ph*100)])
    
    print(f"Total Texts: {len(texts)}, Candidate Room Rectangles: {len(rects)}, Lines: {len(lines)}")
    for i, r in enumerate(rects):
        rx0, ry0, rx1, ry1 = r['pct']
        contained_texts = [t['text'].replace('\n', ' ') for t in texts if rx0 <= t['centroid'][0] <= rx1 and ry0 <= t['centroid'][1] <= ry1]
        print(f"  Rect {i:02d} [{rx0:5.1f}%, {ry0:5.1f}% -> {rx1:5.1f}%, {ry1:5.1f}%] -> Texts: {contained_texts}")

if __name__ == '__main__':
    test_extract('../floor plan/Dubai_Commercial_Floor_Plan_Level02.pdf', 0)
    for p in range(5):
        test_extract('../floor plan/Dubai_Commercial_Building_FLS_Test_FloorPlans.pdf', p)
