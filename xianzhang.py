"""Xianzhang — French ruled (Séyès) notebook generator.

Usage: uv run python xianzhang.py <edition>
  e.g. uv run python xianzhang.py xianzhang-cozyca
"""

import sys
from pathlib import Path

import sizes

TOTAL_PAGES = 2

# French ruling: 2mm thin lines, bold every 4th (8mm group)
LINE_STEP = 2       # mm between thin lines
GROUP_LINES = 4     # lines per group (4 thin → 1 bold)


def _french_ruled_page(pw: float, ph: float, top_gap: float) -> str:
    """Generate one page of French ruled TikZ code."""
    lines = ["\\begin{tikzpicture}[remember picture, overlay]"]

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
    key = edition.removeprefix("xianzhang-")
    s = sizes.SIZES.get(key)
    if s is None:
        print(f"Unknown edition '{edition}'. Known: {list(sizes.SIZES.keys())}")
        sys.exit(1)

    sizes.write_sizes_tex()
    ruled = _french_ruled_page(s["pw"], s["ph"], sizes.XIANZHANG[key])

    out = Path(edition)
    out.mkdir(parents=True, exist_ok=True)

    pages = []
    for _ in range(TOTAL_PAGES):
        pages += ["\\thispagestyle{empty}%", ruled, "\\null", "\\clearpage"]
    (out / "content.tex").write_text("\n".join(pages) + "\n")
    (out / f"{edition}.tex").write_text(
        f"\\def\\EDITION{{{key}}}%\n\\input{{../xianzhang.tex}}%\n"
    )
    print(f"Generated {out}/content.tex + {edition}.tex ({s['pw']}×{s['ph']}mm, Séyès ruled)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: uv run python xianzhang.py <edition>")
        sys.exit(1)
    generate(sys.argv[1])
