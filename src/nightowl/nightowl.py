"""Night Owl — triangular numbers 0–26 in hourglass layout.

Usage: techo nightowl --size m5|cozyca|74m5
"""

from pathlib import Path

import sizes

ROWS = [1, 3, 4, 5, 1, 3, 4, 5, 1]  # 27 numbers total (0–26)


def _label(n: int) -> str:
    """Pad single-digit numbers with an invisible 0 for alignment."""
    if n < 10:
        return f"\\phantom{{0}}{n}"
    return str(n)


def generate(size: str) -> None:
    s = sizes.SIZES[size]
    g = sizes.NIGHTOWL[size]
    PW, PH = s["pw"], s["ph"]
    BINDING, RIGHT_MARGIN = g["binding"], g["right_margin"]
    ROW_GAP, NUM_GAP = g["row_gap"], g["num_gap"]

    # ── Compute positions ──
    tri_height = (len(ROWS) - 1) * ROW_GAP
    top_margin = (PH - tri_height) / 2 + 2  # slightly below center

    usable_w = PW - BINDING - RIGHT_MARGIN
    center_x = BINDING + usable_w / 2

    sizes.write_sizes_tex()

    page_nodes = []
    n = 0
    for ri, cnt in enumerate(ROWS):
        y_mm = -(top_margin + ri * ROW_GAP)
        x_start = center_x - (cnt - 1) * NUM_GAP / 2
        for ci in range(cnt):
            x_mm = x_start + ci * NUM_GAP
            page_nodes.append(
                f"  \\node[font=\\nightowlfont, inner sep=0pt] "
                f"at ({x_mm:.1f}mm, {y_mm:.1f}mm) {{{_label(n)}}};"
            )
            n += 1

    out = Path("outputs") / f"night-owl-{size}"
    out.mkdir(parents=True, exist_ok=True)

    full = [
        "\\thispagestyle{empty}%",
        "\\begin{tikzpicture}[remember picture, overlay]",
        *page_nodes,
        "\\end{tikzpicture}%",
        "\\null",
        "\\clearpage",
        "\\thispagestyle{empty}%",
        "\\null",
        "\\clearpage",
    ]
    (out / "content.tex").write_text("\n".join(full) + "\n")
    (out / f"night-owl-{size}.tex").write_text(
        f"\\def\\EDITION{{{size}}}%\n\\input{{../../src/nightowl/night-owl.tex}}%\n"
    )
    print(f"Generated {out}/content.tex + night-owl-{size}.tex ({PW}×{PH}mm)")
    sizes.compile(f"night-owl-{size}.tex", out)
