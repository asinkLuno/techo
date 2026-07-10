"""Midori Grid — square grids with hollow intersections.

Usage: techo midori-grid --size a5s
"""

from pathlib import Path

import sizes

PEN = "cyan!40, line width=0.7pt"


def _dot_indices(n, freq):
    """Symmetric grid indices (excludes borders) for hollow-intersection dots."""
    mid = n // 2
    return {i for k in range(n) for i in (mid - k * freq, mid + k * freq) if 0 < i < n}


def generate(size: str) -> None:
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

    start_x_odd = BINDING + (usable_w - grid_w) / 2.0
    start_x_even = RIGHT + (usable_w - grid_w) / 2.0
    start_y = TOP + (usable_h - grid_h) / 2.0

    # 1. Helper dots (computed first to exclude extensions on dot rows/columns)
    x_dots = _dot_indices(num_x, DOT_FREQ)
    y_dots = _dot_indices(num_y, DOT_FREQ)

    def _generate_lines(start_x):
        lines = []
        # 2. Horizontal lines (continuous inside grid, extensions with gaps every 2 rows except on dot rows)
        for y_idx in range(num_y + 1):
            y = start_y + y_idx * STEP
            
            # Main continuous line inside grid
            lines.append(
                f"  \\draw[{PEN}] "
                f"({start_x:.2f}mm, -{y:.2f}mm) -- ({start_x + grid_w:.2f}mm, -{y:.2f}mm);"
            )
            
            # Extensions every 2 rows, BUT NOT on rows with dots, AND NOT on the very top/bottom borders
            if y_idx % 2 == 0 and y_idx not in y_dots and y_idx != 0 and y_idx != num_y:
                lines.append(
                    f"  \\draw[{PEN}] "
                    f"({start_x - GAP - EXT:.2f}mm, -{y:.2f}mm) -- ({start_x - GAP:.2f}mm, -{y:.2f}mm);"
                )
                lines.append(
                    f"  \\draw[{PEN}] "
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
                
            lines.append(f"  \\draw[{PEN}] {' '.join(path_cmds)};")

        # 4. Draw Helper dots (Symmetric from edges)
        for x_idx in sorted(x_dots):
            x = start_x + x_idx * STEP
            lines.append(f"  \\fill[cyan!40] ({x:.2f}mm, -{start_y - 1.5:.2f}mm) circle (0.4mm);")
            lines.append(f"  \\fill[cyan!40] ({x:.2f}mm, -{start_y + grid_h + 1.5:.2f}mm) circle (0.4mm);")
        
        for y_idx in sorted(y_dots):
            y = start_y + y_idx * STEP
            lines.append(f"  \\fill[cyan!40] ({start_x - 1.5:.2f}mm, -{y:.2f}mm) circle (0.4mm);")
            lines.append(f"  \\fill[cyan!40] ({start_x + grid_w + 1.5:.2f}mm, -{y:.2f}mm) circle (0.4mm);")
            
        return lines

    lines_odd = _generate_lines(start_x_odd)
    lines_even = _generate_lines(start_x_even)

    def _page(is_odd: bool):
        return [
            "\\thispagestyle{empty}%",
            "\\begin{tikzpicture}[remember picture, overlay]",
            *(lines_odd if is_odd else lines_even),
            "\\end{tikzpicture}%",
        ]

    # ── 2 pages: front (odd) + back (even) ──
    full = []
    for is_odd in (True, False):
        full.extend(_page(is_odd))
        full.append("\\null")
        full.append("\\clearpage")

    out = Path("outputs") / f"midori-grid-{size}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "content.tex").write_text("\n".join(full) + "\n")
    (out / f"midori-grid-{size}.tex").write_text(
        f"\\def\\EDITION{{{size}}}%\n\\input{{../../src/midori_grid/midori_grid.tex}}%\n"
    )
    print(
        f"Generated {out}/content.tex + midori-grid-{size}.tex "
        f"({PW}×{PH}mm, {num_x}x{num_y} grid, 2 pages)"
    )
    sizes.compile(f"midori-grid-{size}.tex", out)

    # ── Spread: 2 pages side-by-side (nup=2x1) ──
    spread_tex = (
        "\\documentclass[10pt]{article}\n"
        f"\\usepackage[paperwidth={PW * 2}mm, paperheight={PH}mm, margin=0mm]{{geometry}}\n"
        "\\usepackage{pdfpages}\n"
        "\\begin{document}\n"
        f"\\includepdf[pages={{1,2}}, nup=2x1, width={PW}mm, height={PH}mm]"
        f"{{midori-grid-{size}.pdf}}\n"
        "\\end{document}\n"
    )
    (out / "spread.tex").write_text(spread_tex)
    sizes.compile("spread.tex", out)
    print(f"Generated {out}/spread.pdf (spread, {PW * 2}×{PH}mm)")
