"""Linear — ruled horizontal lines at 7mm intervals, 2mm thick.

Usage: techo linear --size a5s
"""

from pathlib import Path

from .. import sizes


def generate(size: str) -> None:
    s = sizes.SIZES[size]
    g = sizes.LINEAR[size]
    PW, PH = s["pw"], s["ph"]
    BINDING, RIGHT_MARGIN = g["binding"], g["right_margin"]
    TOP, BOTTOM = g["top_margin"], g["bottom_margin"]
    GAP, LW = g["line_gap"], g["line_width"]

    sizes.write_sizes_tex()

    usable_w = PW - BINDING - RIGHT_MARGIN
    line_nodes = []
    y = TOP
    while y <= PH - BOTTOM:
        line_nodes.append(
            f"  \\fill[IronOxideRed!60] "
            f"({BINDING:.1f}mm, -{y:.1f}mm) "
            f"rectangle ++({usable_w:.1f}mm, -{LW:.1f}mm);"
        )
        y += GAP

    out = Path("outputs") / f"linear-{size}"
    out.mkdir(parents=True, exist_ok=True)

    full = [
        "\\thispagestyle{empty}%",
        "\\begin{tikzpicture}[remember picture, overlay]",
        *line_nodes,
        "\\end{tikzpicture}%",
        "\\null",
        "\\clearpage",
        "\\thispagestyle{empty}%",
        "\\null",
        "\\clearpage",
    ]
    (out / "content.tex").write_text("\n".join(full) + "\n")
    (out / f"linear-{size}.tex").write_text(
        f"\\def\\EDITION{{{size}}}%\n\\input{{../../src/linear/linear.tex}}%\n"
    )
    print(
        f"Generated {out}/content.tex + linear-{size}.tex ({PW}×{PH}mm, {len(line_nodes)} lines)"
    )
    sizes.compile(f"linear-{size}.tex", out)
