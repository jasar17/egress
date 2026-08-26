import pymupdf

doc = pymupdf.open('floor plan/Dubai_Commercial_Floor_Plan_Level02.pdf')
page = doc[0]
rect = page.rect
pw, ph = rect.width, rect.height
print(f"Page size: {pw:.2f} x {ph:.2f}")

drawings = page.get_drawings()
print(f"Found {len(drawings)} vector drawing paths\n")

for i, d in enumerate(drawings):
    r = d['rect']
    x0_pct = (r.x0 / pw) * 100
    y0_pct = (r.y0 / ph) * 100
    x1_pct = (r.x1 / pw) * 100
    y1_pct = (r.y1 / ph) * 100
    svg_x0 = x0_pct
    svg_y0 = y0_pct * 0.70
    svg_x1 = x1_pct
    svg_y1 = y1_pct * 0.70
    items = d.get('items', [])
    print(f"Path {i:02d}: rect=({r.x0:6.1f}, {r.y0:6.1f}, {r.x1:6.1f}, {r.y1:6.1f}) | SVG=({svg_x0:5.2f}, {svg_y0:5.2f}) to ({svg_x1:5.2f}, {svg_y1:5.2f}) | items={len(items)}")
    for it in items:
        cmd = it[0]
        if cmd == 'l': # line
            p1, p2 = it[1], it[2]
            p1_svg = ((p1.x/pw)*100, (p1.y/ph)*70)
            p2_svg = ((p2.x/pw)*100, (p2.y/ph)*70)
            print(f"    LINE: ({p1_svg[0]:.2f}, {p1_svg[1]:.2f}) -> ({p2_svg[0]:.2f}, {p2_svg[1]:.2f})")
        elif cmd == 're': # rect
            rc = it[1]
            rc_svg = ((rc.x0/pw)*100, (rc.y0/ph)*70, (rc.x1/pw)*100, (rc.y1/ph)*70)
            print(f"    RECT: ({rc_svg[0]:.2f}, {rc_svg[1]:.2f}) -> ({rc_svg[2]:.2f}, {rc_svg[3]:.2f})")

print("\n--- TEXT BLOCKS ---")
blocks = page.get_text("blocks")
for b in blocks:
    svg_bx0 = (b[0] / pw) * 100
    svg_by0 = (b[1] / ph) * 70
    svg_bx1 = (b[2] / pw) * 100
    svg_by1 = (b[3] / ph) * 70
    text = b[4].replace('\n', ' ').strip()
    print(f"Text: {text:45} | SVG=({svg_bx0:5.2f}, {svg_by0:5.2f}) to ({svg_bx1:5.2f}, {svg_by1:5.2f}) | Centroid=({(svg_bx0+svg_bx1)/2:5.2f}, {(svg_by0+svg_by1)/2:5.2f})")
