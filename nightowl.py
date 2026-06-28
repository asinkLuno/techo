"""Night Owl m5 — triangular numbers 0–26 in hourglass layout.

Usage: uv run python nightowl.py
"""

from pathlib import Path

ROWS = [1, 3, 4, 5, 1, 3, 4, 5, 1]  # 27 numbers total (0–26)

# Page (m5: 67×105mm)
PW = 67
PH = 105
BINDING = 12      # left gutter
RIGHT_MARGIN = 3  # right margin
ROW_GAP = 6.2     # mm
NUM_GAP = 11      # mm horizontal between adjacent numbers

TOTAL_PAGES = 1


def _label(n: int) -> str:
    """Pad single-digit numbers with an invisible 0 for alignment."""
    if n < 10:
        return f"\\phantom{{0}}{n}"
    return str(n)


def generate() -> None:
    # ── Compute positions ──
    total_rows = len(ROWS)
    tri_height = (total_rows - 1) * ROW_GAP
    top_margin = (PH - tri_height) / 2 + 8  # slightly below center

    usable_w = PW - BINDING - RIGHT_MARGIN  # 49mm
    center_x = BINDING + usable_w / 2       # center of usable area

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
    out = Path("night-owl-m5")
    out.mkdir(parents=True, exist_ok=True)

    full = []
    for _ in range(TOTAL_PAGES):
        full.append("\\thispagestyle{empty}%")
        full.append("\\begin{tikzpicture}[remember picture, overlay]")
        full.extend(page_nodes)
        full.append("\\end{tikzpicture}%")
        full.append("\\null")
        full.append("\\clearpage")

    (out / "content.tex").write_text("\n".join(full) + "\n")
    print(f"Generated {out / 'content.tex'} ({TOTAL_PAGES} pages, {n} numbers)")


if __name__ == "__main__":
    generate()
