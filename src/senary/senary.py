"""Senary — monthly calendar (front) + habit tracker (back), landscape m5 (105×67).

Usage: uv run python -m src.senary 2026-07
  Front (odd page): that month's calendar, landscape (no rotation — the page is wide).
  Back  (even page): two tracker tables stacked — 1–14 (item col + header) +
                     15–end (header only, no item col), 6 rows each.
"""

import calendar
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import sizes
from sizes import FONT_CMD

# ── Calendar (front) ──
COLS = 7
BIND = 9.0  # mm, top binding margin
GM = 4.0  # mm, margin on the other three sides (left/right/bottom)
TITLE_H = 7.0
HEAD_H = 4.0
WEEKDAYS = ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")  # Monday-first

# ── Fonts (defined in sizes.py, emitted to sizes.tex) ──
FONT_TITLE = FONT_CMD["large"]
FONT_CAL = FONT_CMD["small"]
FONT_TRACKER_HEAD = FONT_CMD["small"]

# ── Habit tracker (back) ──
A = 5.5  # mm, square check cell
ITEM_W = 2  # multiplier, item column = ITEM_W * A wide
ITEMS = 4  # blank habit rows


def _cal(year: int, month: int, pw: float, ph: float) -> str:
    days = calendar.monthrange(year, month)[1]
    first = calendar.monthrange(year, month)[0]  # weekday of the 1st, 0=Mon
    weeks = (first + days + COLS - 1) // COLS
    lm, rm = GM, pw - GM  # left/right edges
    gy = BIND + TITLE_H + HEAD_H  # grid top edge
    gb = ph - GM  # grid bottom edge
    cell_w = (rm - lm) / COLS
    cell_h = (gb - gy) / weeks
    out = [
        "\\begin{tikzpicture}[remember picture, overlay, every node/.style={inner sep=0pt}]"
    ]
    # explicit verticals + horizontals (tikz `grid[step]` aligns to the page
    # origin, which clipped the first/last column and row to wrong widths)
    for i in range(COLS + 1):
        x = lm + cell_w * i
        out.append(
            f"  \\draw[gridline] ([xshift={x:.2f}mm, yshift={-gy:.2f}mm]current page.north west)"
            f" -- ([xshift={x:.2f}mm, yshift={-gb:.2f}mm]current page.north west);"
        )
    for j in range(weeks + 1):
        y = gy + cell_h * j
        out.append(
            f"  \\draw[gridline] ([xshift={lm:.2f}mm, yshift={-y:.2f}mm]current page.north west)"
            f" -- ([xshift={rm:.2f}mm, yshift={-y:.2f}mm]current page.north west);"
        )
    out.append(
        f"  \\node[font=\\{FONT_TITLE}]"
        f" at ([xshift={pw / 2:.2f}mm, yshift={-(BIND + TITLE_H / 2):.2f}mm]current page.north west)"
        f" {{{calendar.month_name[month]} {year}}};"
    )
    for i, w in enumerate(WEEKDAYS):
        x = lm + cell_w * (i + 0.5)
        out.append(
            f"  \\node[font=\\{FONT_CAL}]"
            f" at ([xshift={x:.2f}mm, yshift={-(gy - HEAD_H / 2):.2f}mm]current page.north west)"
            f" {{{w}}};"
        )
    PAD = 0.8  # mm, offset from cell top-left
    for d in range(1, days + 1):
        r, c = divmod(first + d - 1, COLS)
        x = lm + cell_w * c + PAD
        y = gy + cell_h * r + PAD
        label = f"\\phantom{{0}}{d}" if d < 10 else str(d)
        out.append(
            f"  \\node[font=\\{FONT_CAL}, anchor=north west]"
            f" at ([xshift={x:.2f}mm, yshift={-y:.2f}mm]current page.north west) {{{label}}};"
        )
    out.append("\\end{tikzpicture}%")
    return "\n".join(out)


def _table(
    lm: float, top: float, dates: list[int], with_items: bool, with_header: bool = True
) -> list[str]:
    """Verticals + horizontals + header dates for one tracker table."""
    xs = [lm]
    if with_items:
        xs.append(lm + ITEM_W * A)
    for _ in dates:
        xs.append(xs[-1] + A)
    rows = ITEMS + (1 if with_header else 0)
    bottom = top + rows * A
    off = 1 if with_items else 0
    out = []
    vtop = top + (A if with_header else 0)  # verticals skip header row
    for x in xs:
        out.append(
            f"  \\draw[gridline] ([xshift={x:.2f}mm, yshift={-vtop:.2f}mm]current page.north west)"
            f" -- ([xshift={x:.2f}mm, yshift={-bottom:.2f}mm]current page.north west);"
        )
    start_i = 1 if with_header else 0  # skip top line of header
    for i in range(start_i, rows + 1):  # horizontals
        y = top + i * A
        out.append(
            f"  \\draw[gridline] ([xshift={lm:.2f}mm, yshift={-y:.2f}mm]current page.north west)"
            f" -- ([xshift={xs[-1]:.2f}mm, yshift={-y:.2f}mm]current page.north west);"
        )
    if with_header:
        hy = top + A / 2
        for i, d in enumerate(dates):
            cx = (xs[off + i] + xs[off + i + 1]) / 2
            label = f"\\phantom{{0}}{d}" if d < 10 else str(d)
            out.append(
                f"  \\node[font=\\{FONT_TRACKER_HEAD}]"
                f" at ([xshift={cx:.2f}mm, yshift={-hy:.2f}mm]current page.north west) {{{label}}};"
            )
    return out


def _tracker(days: int, pw: float, ph: float) -> str:
    dates1 = list(range(1, 15))  # 1–14
    dates2 = list(range(15, days + 1))  # 15–end
    w1 = ITEM_W * A + len(dates1) * A
    w2 = len(dates2) * A  # no item column
    lm = (pw - max(w1, w2)) / 2
    gap = 2.0  # mm between tables
    h1 = (ITEMS + 1) * A  # with header
    h2 = ITEMS * A  # no header
    top1 = (ph - h1 - gap - h2) / 2
    top2 = top1 + h1 + gap
    out = [
        "\\begin{tikzpicture}[remember picture, overlay, every node/.style={inner sep=0pt}]"
    ]
    out += _table(lm, top1, dates1, with_items=True)
    out += _table(lm, top2, dates2, with_items=False, with_header=True)
    out.append("\\end{tikzpicture}%")
    return "\n".join(out)


def generate(ym: str) -> None:
    try:
        year, month = (int(x) for x in ym.split("-"))
    except ValueError:
        print(f"Expected YYYY-MM (e.g. 2026-07), got '{ym}'")
        sys.exit(1)
    if not (1 <= month <= 12):
        print(f"Bad month {month} (need 1–12)")
        sys.exit(1)

    key = "m5l"
    pw, ph = sizes.SIZES[key]["pw"], sizes.SIZES[key]["ph"]
    sizes.write_sizes_tex()
    days = calendar.monthrange(year, month)[1]

    edition = f"senary-{year}-{month:02d}"
    out = Path("outputs") / edition
    out.mkdir(parents=True, exist_ok=True)
    content = [
        "\\thispagestyle{empty}%",
        _cal(year, month, pw, ph),
        "\\null",
        "\\clearpage",
        "\\thispagestyle{empty}%",
        _tracker(days, pw, ph),
        "\\null",
        "\\clearpage",
    ]
    (out / "content.tex").write_text("\n".join(content) + "\n")
    (out / f"{edition}.tex").write_text("\\input{../../src/senary/senary.tex}%\n")
    print(
        f"Generated {edition}/content.tex + {edition}.tex "
        f"({calendar.month_name[month]} {year}, {days} days, {pw}×{ph}mm landscape)"
    )
    sizes.compile(f"{edition}.tex", out)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: uv run python -m src.senary YYYY-MM  (e.g. 2026-07)")
        sys.exit(1)
    generate(sys.argv[1])
