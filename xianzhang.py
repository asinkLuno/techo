"""Xianzhang — French ruled (Séyès) notebook generator.

Usage: uv run python xianzhang.py <edition>
  e.g. uv run python xianzhang.py xianzhang-cozyca
"""

import sys
from pathlib import Path

TOTAL_PAGES = 2

# ── Size presets (from sizes.tex) ──
SIZES = {
    "cozyca": {"pw": 100, "ph": 90, "top_gap": 9, "red_line": 8},
    "m5":     {"pw": 67,  "ph": 105, "top_gap": 9, "red_line": 7},
    "a5s":    {"pw": 110, "ph": 210, "top_gap": 12, "red_line": 12},
}

# French ruling: 2mm thin lines, bold every 4th (8mm group)
LINE_STEP = 2       # mm between thin lines
GROUP_LINES = 4     # lines per group (4 thin → 1 bold)


def _french_ruled_page(pw: float, ph: float, top_gap: float) -> str:
    """Generate one page of French ruled TikZ code."""
    lines = []
    lines.append("\\begin{tikzpicture}[remember picture, overlay]")

    bottom_margin = 5  # mm from bottom
    n = 0
    y = top_gap
    while y <= ph - bottom_margin:
        is_bold = (n % GROUP_LINES == 0)
        lw = 0.45 if is_bold else 0.18
        opacity = 65 if is_bold else 35
        lines.append(
            f"  \\draw[ruleblue!{opacity}, line width={lw}pt]"
            f" ([yshift=-{y:.1f}mm] current page.north west) --"
            f" ([yshift=-{y:.1f}mm] current page.north east);"
        )
        n += 1
        y += LINE_STEP

    lines.append("\\end{tikzpicture}%")
    return "\n".join(lines)


def generate(edition: str) -> None:
    # Extract size name from edition (e.g. "xianzhang-cozyca" → "cozyca")
    size_key = edition.replace("xianzhang-", "")
    cfg = SIZES.get(size_key)
    if cfg is None:
        print(f"Unknown size '{size_key}'. Known: {list(SIZES.keys())}")
        sys.exit(1)

    ruled = _french_ruled_page(cfg["pw"], cfg["ph"], cfg["top_gap"])

    out_pages = []
    for _ in range(TOTAL_PAGES):
        out_pages.append("\\thispagestyle{empty}%")
        out_pages.append(ruled)
        out_pages.append("\\null")
        out_pages.append("\\clearpage")

    out_dir = Path(edition)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "content.tex").write_text("\n".join(out_pages) + "\n")
    print(f"Generated {out_dir / 'content.tex'} ({TOTAL_PAGES} pages, Séyès ruled)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: uv run python xianzhang.py <edition>")
        sys.exit(1)
    generate(sys.argv[1])
