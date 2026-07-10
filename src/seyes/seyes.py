"""Seyes — French-ruled pages.

Horizontal blue lines at 2mm intervals in groups of 4;
red vertical margin line on the binding side.
Outputs both flat pages and a booklet-imposed PDF (via pdfpages).

Usage: techo seyes --size tn
"""

from pathlib import Path

from .. import sizes


def generate(size: str, sheets: int = 1) -> None:
    s = sizes.SIZES[size]
    g = sizes.SEYES[size]
    PW, PH = s["pw"], s["ph"]
    BINDING = g["binding"]
    TOP = g["top_margin"]
    BOTTOM = g["bottom_margin"]
    ROW_H = g["row_height"]
    GROUP = g["group_size"]
    THICK = g["thick_line"]
    THIN = g["thin_line"]
    RED_LW = g["red_line_width"]

    sizes.write_sizes_tex()

    # ── Horizontal lines ──
    hlines = []
    y, row = TOP, 0
    while y <= PH - BOTTOM:
        lw = THICK if row % GROUP == 0 else THIN
        hlines.append(
            f"  \\fill[CobaltBlue!70] "
            f"(0, -{y:.1f}mm) "
            f"rectangle ++({PW:.1f}mm, -{lw:.1f}mm);"
        )
        y += ROW_H
        row += 1

    # ── Red vertical line (always on the left) ──
    red_line = (
        f"  \\fill[IronOxideRed!60] "
        f"({BINDING:.1f}mm, 0) "
        f"rectangle ++({RED_LW:.1f}mm, -{PH:.1f}mm);"
    )

    def _page():
        return [
            "\\thispagestyle{empty}%",
            "\\begin{tikzpicture}[remember picture, overlay]",
            red_line,
            *hlines,
            "\\end{tikzpicture}%",
        ]

    # ── Build N sheets (1 sheet = 4 pages) ──
    sheets_4 = sheets * 4
    full = []
    for _ in range(sheets_4):
        full.extend(_page())
        full.append("\\null")
        full.append("\\clearpage")

    out = Path("outputs") / f"seyes-{size}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "content.tex").write_text("\n".join(full) + "\n")
    (out / f"seyes-{size}.tex").write_text(
        f"\\def\\EDITION{{{size}}}%\n\\input{{../../src/seyes/seyes.tex}}%\n"
    )
    total_pages = sheets_4
    print(
        f"Generated {out}/content.tex + seyes-{size}.tex "
        f"({PW}×{PH}mm, {row} rows, {row // GROUP} groups, {total_pages} pages)"
    )
    sizes.compile(f"seyes-{size}.tex", out)

    # ── Booklet imposition via pdfpages ──
    booklet_tex = (
        "\\documentclass[10pt]{article}\n"
        f"\\usepackage[paperwidth={PW * 2}mm, paperheight={PH}mm, margin=0mm]{{geometry}}\n"
        "\\usepackage{pdfpages}\n"
        "\\begin{document}\n"
        f"\\includepdf[pages=-, nup=2x1, signature={total_pages}, width={PW}mm, height={PH}mm]"
        f"{{seyes-{size}.pdf}}\n"
        "\\end{document}\n"
    )
    (out / "booklet.tex").write_text(booklet_tex)
    print(f"Generated {out}/booklet.tex (booklet imposition, {PW * 2}×{PH}mm)")
    sizes.compile("booklet.tex", out)
