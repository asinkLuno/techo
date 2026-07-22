"""Midori Grid — square grids with hollow intersections.

Usage: techo midori-grid --size a5s
"""

from pathlib import Path

from .. import sizes

PEN = "cyan!40, line width=0.7pt"


def _dot_indices(n: int, freq: int) -> set[int]:
    """Symmetric grid indices (excludes borders) for hollow-intersection dots."""
    mid = n // 2
    return {i for k in range(n) for i in (mid - k * freq, mid + k * freq) if 0 < i < n}


def _coord_raw(x: float, y: float) -> str:
    """Raw TikZ coordinate ``({x}mm, -{y}mm)`` — midori_grid's own pages."""
    return f"({x:.2f}mm, -{y:.2f}mm)"


def grid_lines(
    start_x: float,
    start_y: float,
    num_x: int,
    num_y: int,
    *,
    step: float,
    gap: float,
    ext: float,
    dot_freq: int,
    pen: str = PEN,
    coord=_coord_raw,
) -> list[str]:
    """A continuous midori grid drawn from top-left ``start`` over ``num_x`` by
    ``num_y`` cells of size ``step``.

    Produces continuous horizontals, U-shaped verticals that gap at every
    intersection (the hollow crosses), every-other-line edge extensions (skipped on
    dot rows/columns and on the borders), and the symmetric helper dots.

    ``coord(x, y)`` formats each TikZ point, so callers can anchor differently:
    midori_grid's own pages use raw coordinates, while movie anchors every line to
    ``current page.north west`` so its printed characters land exactly on the cells.
    """
    grid_w = num_x * step
    grid_h = num_y * step
    x_dots = _dot_indices(num_x, dot_freq)
    y_dots = _dot_indices(num_y, dot_freq)
    lines: list[str] = []

    # 1. Horizontal lines (continuous inside the grid), with extensions every 2 rows
    #    — but not on dot rows, and not on the top/bottom borders.
    for y_idx in range(num_y + 1):
        y = start_y + y_idx * step
        lines.append(
            f"  \\draw[{pen}] {coord(start_x, y)} -- {coord(start_x + grid_w, y)};"
        )
        if y_idx % 2 == 0 and y_idx not in y_dots and y_idx != 0 and y_idx != num_y:
            lines.append(
                f"  \\draw[{pen}] {coord(start_x - gap - ext, y)}"
                f" -- {coord(start_x - gap, y)};"
            )
            lines.append(
                f"  \\draw[{pen}] {coord(start_x + grid_w + gap, y)}"
                f" -- {coord(start_x + grid_w + gap + ext, y)};"
            )

    # 2. Vertical lines: top/bottom extensions every 2 columns, then U-shape arms
    #    that touch each bottom line and gap before the top line.
    for x_idx in range(num_x + 1):
        x = start_x + x_idx * step
        path_cmds = []
        if x_idx % 2 == 0 and x_idx not in x_dots and x_idx != 0 and x_idx != num_x:
            y_last = start_y + num_y * step
            path_cmds.append(
                f"{coord(x, start_y - gap - ext)} -- {coord(x, start_y - gap)}"
            )
            path_cmds.append(
                f"{coord(x, y_last + gap)} -- {coord(x, y_last + gap + ext)}"
            )
        for y_idx in range(num_y):
            y_top = start_y + y_idx * step
            y_bottom = start_y + (y_idx + 1) * step
            path_cmds.append(f"{coord(x, y_top + gap)} -- {coord(x, y_bottom)}")
        lines.append(f"  \\draw[{pen}] {' '.join(path_cmds)};")

    # 3. Helper dots (symmetric from the edges)
    for x_idx in sorted(x_dots):
        x = start_x + x_idx * step
        lines.append(f"  \\fill[cyan!40] {coord(x, start_y - 1.5)} circle (0.4mm);")
        lines.append(
            f"  \\fill[cyan!40] {coord(x, start_y + grid_h + 1.5)} circle (0.4mm);"
        )
    for y_idx in sorted(y_dots):
        y = start_y + y_idx * step
        lines.append(f"  \\fill[cyan!40] {coord(start_x - 1.5, y)} circle (0.4mm);")
        lines.append(
            f"  \\fill[cyan!40] {coord(start_x + grid_w + 1.5, y)} circle (0.4mm);"
        )

    return lines


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

    lines_odd = grid_lines(
        start_x_odd,
        start_y,
        num_x,
        num_y,
        step=STEP,
        gap=GAP,
        ext=EXT,
        dot_freq=DOT_FREQ,
    )
    lines_even = grid_lines(
        start_x_even,
        start_y,
        num_x,
        num_y,
        step=STEP,
        gap=GAP,
        ext=EXT,
        dot_freq=DOT_FREQ,
    )

    out = Path("outputs") / f"midori-grid-{size}"
    out.mkdir(parents=True, exist_ok=True)

    def _page(is_odd: bool) -> list[str]:
        return [
            "\\thispagestyle{empty}%",
            "\\begin{tikzpicture}[remember picture, overlay]",
            *(lines_odd if is_odd else lines_even),
            "\\end{tikzpicture}%",
        ]

    full = []
    for is_odd in (True, False):
        full.extend(_page(is_odd))
        full.append("\\null")
        full.append("\\clearpage")

    (out / "content.tex").write_text("\n".join(full) + "\n")
    (out / f"midori-grid-{size}.tex").write_text(
        f"\\def\\EDITION{{{size}}}%\n\\input{{../../src/midori_grid/midori_grid.tex}}%\n"
    )
    print(
        f"Generated {out}/content.tex + midori-grid-{size}.tex "
        f"({PW}×{PH}mm, {num_x}x{num_y} grid, 2 pages)"
    )
    sizes.compile(f"midori-grid-{size}.tex", out)

    if size in ("tn", "tnp"):
        spread_tex = (
            "\\documentclass[10pt]{article}\n"
            f"\\usepackage[paperwidth={PW * 2}mm, paperheight={PH}mm, margin=0mm]{{geometry}}\n"
            "\\usepackage{pdfpages}\n"
            "\\begin{document}\n"
            f"\\includepdf[pages=-, booklet=true, landscape]"
            f"{{midori-grid-{size}.pdf}}\n"
            "\\end{document}\n"
        )
    else:
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
