"""Midori Grid — square grids with hollow intersections.

Usage: techo midori-grid --size a5s
"""

from pathlib import Path

import sizes


def generate(size: str, sheets: int = 1) -> None:
    s = sizes.SIZES[size]
    g = sizes.MIDORI_GRID[size]
    PW, PH = s["pw"], s["ph"]
    BINDING = g["binding"]
    RIGHT = g["right_margin"]
    TOP = g["top_margin"]
    BOTTOM = g["bottom_margin"]
    STEP = g["grid_step"]
    GAP = g["gap_size"]
    EXT = g["edge_extension"]
    DOT_FREQ = g["dot_freq"]

    sizes.write_sizes_tex()

    usable_w = PW - BINDING - RIGHT
    usable_h = PH - TOP - BOTTOM
    
    num_x = int(usable_w // STEP)
    num_y = int(usable_h // STEP)

    grid_w = num_x * STEP
    grid_h = num_y * STEP

    start_x = BINDING + (usable_w - grid_w) / 2.0
    start_y = TOP + (usable_h - grid_h) / 2.0

    # 1. Helper dots (Calculate first to exclude extensions on dot lines)
    x_dots = set()
    mid_x = num_x / 2.0
    i = 0
    while True:
        left = mid_x - i
        right = mid_x + i
        if left <= 0 and right >= num_x:
            break
        if left > 0:
            x_dots.add(left)
        if right < num_x:
            x_dots.add(right)
        i += DOT_FREQ

    y_dots = set()
    mid_y = num_y / 2.0
    i = 0
    while True:
        top = mid_y - i
        bottom = mid_y + i
        if top <= 0 and bottom >= num_y:
            break
        if top > 0:
            y_dots.add(top)
        if bottom < num_y:
            y_dots.add(bottom)
        i += DOT_FREQ

    lines = []
    # 2. Horizontal lines (continuous inside grid, extensions with gaps every 2 rows except on dot rows)
    for y_idx in range(num_y + 1):
        y = start_y + y_idx * STEP
        
        # Main continuous line inside grid
        lines.append(
            f"  \\draw[cyan!40, very thin] "
            f"({start_x:.2f}mm, -{y:.2f}mm) -- ({start_x + grid_w:.2f}mm, -{y:.2f}mm);"
        )
        
        # Extensions every 2 rows, BUT NOT on rows with dots, AND NOT on the very top/bottom borders
        if y_idx % 2 == 0 and y_idx not in y_dots and y_idx != 0 and y_idx != num_y:
            lines.append(
                f"  \\draw[cyan!40, very thin] "
                f"({start_x - GAP - EXT:.2f}mm, -{y:.2f}mm) -- ({start_x - GAP:.2f}mm, -{y:.2f}mm);"
            )
            lines.append(
                f"  \\draw[cyan!40, very thin] "
                f"({start_x + grid_w + GAP:.2f}mm, -{y:.2f}mm) -- ({start_x + grid_w + GAP + EXT:.2f}mm, -{y:.2f}mm);"
            )

    # 3. Vertical lines (U-shaped segments with gaps)
    for x_idx in range(num_x + 1):
        x = start_x + x_idx * STEP
        path_cmds = []
        
        # Top and bottom extensions every 2 columns, BUT NOT on columns with dots, AND NOT on left/right borders
        if x_idx % 2 == 0 and x_idx not in x_dots and x_idx != 0 and x_idx != num_x:
            path_cmds.append(f"({x:.2f}mm, -{start_y - GAP - EXT:.2f}mm) -- ({x:.2f}mm, -{start_y - GAP:.2f}mm)")
            
            y_last = start_y + num_y * STEP
            path_cmds.append(f"({x:.2f}mm, -{y_last + GAP:.2f}mm) -- ({x:.2f}mm, -{y_last + GAP + EXT:.2f}mm)")
        
        # Grid segments (U-shape arms: touch bottom line, gap before top line)
        for y_idx in range(num_y):
            y_top = start_y + y_idx * STEP
            y_bottom = start_y + (y_idx + 1) * STEP
            path_cmds.append(f"({x:.2f}mm, -{y_top + GAP:.2f}mm) -- ({x:.2f}mm, -{y_bottom:.2f}mm)")
            
        lines.append(f"  \\draw[cyan!40, very thin] {' '.join(path_cmds)};")

    # 4. Draw Helper dots (Symmetric from edges)
    for x_idx in sorted(x_dots):
        x = start_x + x_idx * STEP
        lines.append(f"  \\fill[cyan!40] ({x:.2f}mm, -{start_y - 1.5:.2f}mm) circle (0.4mm);")
        lines.append(f"  \\fill[cyan!40] ({x:.2f}mm, -{start_y + grid_h + 1.5:.2f}mm) circle (0.4mm);")
    
    for y_idx in sorted(y_dots):
        y = start_y + y_idx * STEP
        lines.append(f"  \\fill[cyan!40] ({start_x - 1.5:.2f}mm, -{y:.2f}mm) circle (0.4mm);")
        lines.append(f"  \\fill[cyan!40] ({start_x + grid_w + 1.5:.2f}mm, -{y:.2f}mm) circle (0.4mm);")

    def _page():
        return [
            "\\thispagestyle{empty}%",
            "\\begin{tikzpicture}[remember picture, overlay]",
            *lines,
            "\\end{tikzpicture}%",
        ]

    # ── Build N sheets (1 sheet = 4 pages) ──
    sheets_4 = sheets * 4
    full = []
    for _ in range(sheets_4):
        full.extend(_page())
        full.append("\\null")
        full.append("\\clearpage")

    out = Path("outputs") / f"midori-grid-{size}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "content.tex").write_text("\n".join(full) + "\n")
    (out / f"midori-grid-{size}.tex").write_text(
        f"\\def\\EDITION{{{size}}}%\n\\input{{../../src/midori_grid/midori_grid.tex}}%\n"
    )
    total_pages = sheets_4
    print(
        f"Generated {out}/content.tex + midori-grid-{size}.tex "
        f"({PW}×{PH}mm, {num_x}x{num_y} grid, {total_pages} pages)"
    )
    sizes.compile(f"midori-grid-{size}.tex", out)

    # ── Booklet imposition via pdfpages ──
    booklet_tex = (
        "\\documentclass[10pt]{article}\n"
        f"\\usepackage[paperwidth={PW * 2}mm, paperheight={PH}mm, margin=0mm]{{geometry}}\n"
        "\\usepackage{pdfpages}\n"
        "\\begin{document}\n"
        f"\\includepdf[pages=-, nup=2x1, signature={total_pages}, width={PW}mm, height={PH}mm]"
        f"{{midori-grid-{size}.pdf}}\n"
        "\\end{document}\n"
    )
    (out / "booklet.tex").write_text(booklet_tex)
    print(f"Generated {out}/booklet.tex (booklet imposition, {PW * 2}×{PH}mm)")
    sizes.compile("booklet.tex", out)
