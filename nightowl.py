"""Night Owl — triangular numbers 0–26 in hourglass layout.

Usage: uv run python nightowl.py [--size m5|cozyca]
"""

import sys
from pathlib import Path

ROWS = [1, 3, 4, 5, 1, 3, 4, 5, 1]  # 27 numbers total (0–26)

# ── Size presets ──
SIZES = {
    "m5": {"pw": 67, "ph": 105, "binding": 12, "right_margin": 3, "row_gap": 8.0, "num_gap": 11},
    "cozyca": {"pw": 100, "ph": 90, "binding": 15, "right_margin": 3, "row_gap": 7.5, "num_gap": 16},
}


def _label(n: int) -> str:
    """Pad single-digit numbers with an invisible 0 for alignment."""
    if n < 10:
        return f"\\phantom{{0}}{n}"
    return str(n)


def generate(size: str) -> None:
    cfg = SIZES[size]
    PW, PH = cfg["pw"], cfg["ph"]
    BINDING = cfg["binding"]
    RIGHT_MARGIN = cfg["right_margin"]
    ROW_GAP = cfg["row_gap"]
    NUM_GAP = cfg["num_gap"]

    # ── Compute positions ──
    total_rows = len(ROWS)
    tri_height = (total_rows - 1) * ROW_GAP
    top_margin = (PH - tri_height) / 2 + 8  # slightly below center

    usable_w = PW - BINDING - RIGHT_MARGIN
    center_x = BINDING + usable_w / 2

    page_nodes = []
    n = 0
    for ri, cnt in enumerate(ROWS):
        y_mm = -(top_margin + ri * ROW_GAP)
        row_w = (cnt - 1) * NUM_GAP
        x_start = center_x - row_w / 2
        for ci in range(cnt):
            x_mm = x_start + ci * NUM_GAP
            page_nodes.append(
                f"  \\node[font=\\nightowlfont, inner sep=0pt] "
                f"at ({x_mm:.1f}mm, {y_mm:.1f}mm) {{{_label(n)}}};"
            )
            n += 1

    # ── Assemble pages ──
    dir_name = f"night-owl-{size}" if size != "m5" else "night-owl-m5"
    out = Path(dir_name)
    out.mkdir(parents=True, exist_ok=True)

    full = []
    full.append("\\thispagestyle{empty}%")
    full.append("\\begin{tikzpicture}[remember picture, overlay]")
    full.extend(page_nodes)
    full.append("\\end{tikzpicture}%")
    full.append("\\null")
    full.append("\\clearpage")
    full.append("\\thispagestyle{empty}%")
    full.append("\\null")
    full.append("\\clearpage")

    (out / "content.tex").write_text("\n".join(full) + "\n")
    text = "Generated"
    # ponytail: print path for verification
    print(f"{text} {out / 'content.tex'} ({size}: {PW}×{PH}mm)")


if __name__ == "__main__":
    size = "cozyca" if "--size" in sys.argv and "cozyca" in sys.argv else \
           sys.argv[sys.argv.index("--size") + 1] if "--size" in sys.argv else \
           "m5"
    generate(size)
