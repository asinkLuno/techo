"""Seyes — French-ruled pages.

Horizontal blue lines at 2mm intervals in groups of 4;
red vertical margin line on the binding side.
Outputs both flat pages and a booklet-imposed PDF (via pdfpages).

Usage: techo seyes --size tn
"""

from pathlib import Path

import sizes


def generate(size: str, sheets: int = 1) -> None:
    s = sizes.SIZES[size]
    g = sizes.SEYES[size]
    PW, PH = s["pw"], s["ph"]
    BINDING = g["binding"]
    OUTER = g["outer_margin"]
    TOP = g["top_margin"]
    BOTTOM = g["bottom_margin"]
    ROW_H = g["row_height"]
    GROUP = g["group_size"]
    THICK = g["thick_line"]
    THIN = g["thin_line"]
    RED_LW = g["red_line_width"]

    sizes.write_sizes_tex()

    # ── Horizontal lines ──
    odd_lines, even_lines = [], []
    y, row = TOP, 0
    while y <= PH - BOTTOM:
        lw = THICK if row % GROUP == 0 else THIN
        # ponytail: red-line side extends to page edge
        odd_lines.append(
            f"  \\fill[CobaltBlue!70] "
            f"(0, -{y:.1f}mm) "
            f"rectangle ++({PW - OUTER:.1f}mm, -{lw:.1f}mm);"
        )
        even_lines.append(
            f"  \\fill[CobaltBlue!70] "
            f"({OUTER:.1f}mm, -{y:.1f}mm) "
            f"rectangle ++({PW - OUTER:.1f}mm, -{lw:.1f}mm);"
        )
        y += ROW_H
        row += 1

    # ── Red vertical line ──
    odd_red = (
        f"  \\fill[IronOxideRed!60] "
        f"({BINDING:.1f}mm, 0) "
        f"rectangle ++({RED_LW:.1f}mm, -{PH:.1f}mm);"
    )
    even_red = (
        f"  \\fill[IronOxideRed!60] "
        f"({PW - BINDING:.1f}mm, 0) "
        f"rectangle ++({RED_LW:.1f}mm, -{PH:.1f}mm);"
    )

    def _page(red, lines):
        return [
            "\\thispagestyle{empty}%",
            "\\begin{tikzpicture}[remember picture, overlay]",
            red,
            *lines,
            "\\end{tikzpicture}%",
        ]

    # ── Build N spreads (odd + even) — 1 sheet = 2 spreads = 4 pages ──
    spreads = sheets * 2
    full = []
    for _ in range(spreads):
        full.extend(_page(odd_red, odd_lines))
        full.append("\\null")
        full.append("\\clearpage")
        full.extend(_page(even_red, even_lines))
        full.append("\\null")
        full.append("\\clearpage")

    out = Path("outputs") / f"seyes-{size}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "content.tex").write_text("\n".join(full) + "\n")
    (out / f"seyes-{size}.tex").write_text(
        f"\\def\\EDITION{{{size}}}%\n\\input{{../../src/seyes/seyes.tex}}%\n"
    )
    total_pages = spreads * 2
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
