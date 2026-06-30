"""Senary — monthly calendar (front) + habit tracker (back), landscape m5 (105×67).

Usage: uv run python senary.py 2026-07
  Front (odd page): that month's calendar, landscape (no rotation — the page is wide).
  Back  (even page): single tracker — a 3-wide item column + one square check cell
                     per day (1–<last>). Width 105mm fits the whole month in one row.
"""

import calendar
import subprocess
import sys
from pathlib import Path

import sizes

# ── Calendar (front) ──
COLS = 7
BIND = 9.0  # mm, top binding margin
GM = 4.0  # mm, margin on the other three sides (left/right/bottom)
TITLE_H = 7.0
HEAD_H = 4.0
WEEKDAYS = ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")  # Monday-first

# ── Habit tracker (back) ──
A = 2.8  # mm, square check cell; item column = 3*A wide
ITEMS = 18  # blank habit rows


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
        f"  \\node[font=\\large]"
        f" at ([xshift={pw / 2:.2f}mm, yshift={-(BIND + TITLE_H / 2):.2f}mm]current page.north west)"
        f" {{{calendar.month_name[month]} {year}}};"
    )
    for i, w in enumerate(WEEKDAYS):
        x = lm + cell_w * (i + 0.5)
        out.append(
            f"  \\node[font=\\small]"
            f" at ([xshift={x:.2f}mm, yshift={-(gy - HEAD_H / 2):.2f}mm]current page.north west)"
            f" {{{w}}};"
        )
    for d in range(1, days + 1):
        r, c = divmod(first + d - 1, COLS)
        x = lm + cell_w * (c + 0.5)
        y = gy + cell_h * (r + 0.5)
        label = f"\\phantom{{0}}{d}" if d < 10 else str(d)
        out.append(
            f"  \\node[font=\\small]"
            f" at ([xshift={x:.2f}mm, yshift={-y:.2f}mm]current page.north west) {{{label}}};"
        )
    out.append("\\end{tikzpicture}%")
    return "\n".join(out)


def _table(lm: float, top: float, dates: list[int], with_items: bool) -> list[str]:
    """Verticals + horizontals + header dates for one tracker table."""
    xs = [lm]
    if with_items:
        xs.append(lm + 3 * A)
    for _ in dates:
        xs.append(xs[-1] + A)
    bottom = top + (ITEMS + 1) * A
    off = 1 if with_items else 0
    out = []
    for x in xs:  # verticals
        out.append(
            f"  \\draw[gridline] ([xshift={x:.2f}mm, yshift={-top:.2f}mm]current page.north west)"
            f" -- ([xshift={x:.2f}mm, yshift={-bottom:.2f}mm]current page.north west);"
        )
    for i in range(ITEMS + 2):  # horizontals
        y = top + i * A
        out.append(
            f"  \\draw[gridline] ([xshift={lm:.2f}mm, yshift={-y:.2f}mm]current page.north west)"
            f" -- ([xshift={xs[-1]:.2f}mm, yshift={-y:.2f}mm]current page.north west);"
        )
    hy = top + A / 2
    for i, d in enumerate(dates):  # header row
        cx = (xs[off + i] + xs[off + i + 1]) / 2
        label = f"\\phantom{{0}}{d}" if d < 10 else str(d)
        out.append(
            f"  \\node[font=\\tiny]"
            f" at ([xshift={cx:.2f}mm, yshift={-hy:.2f}mm]current page.north west) {{{label}}};"
        )
    return out


def _tracker(days: int, pw: float, ph: float) -> str:
    dates = list(range(1, days + 1))
    total_w = 3 * A + len(dates) * A  # item column + one cell per day
    lm = (pw - total_w) / 2
    top = (ph - (ITEMS + 1) * A) / 2
    out = [
        "\\begin{tikzpicture}[remember picture, overlay, every node/.style={inner sep=0pt}]"
    ]
    out += _table(lm, top, dates, with_items=True)
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
    out = Path(edition)
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
    (out / f"{edition}.tex").write_text("\\input{../senary.tex}%\n")
    print(
        f"Generated {edition}/content.tex + {edition}.tex "
        f"({calendar.month_name[month]} {year}, {days} days, {pw}×{ph}mm landscape)"
    )
    for _ in range(2):
        subprocess.run(["xelatex", f"{edition}.tex"], cwd=out, check=True)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: uv run python senary.py YYYY-MM  (e.g. 2026-07)")
        sys.exit(1)
    generate(sys.argv[1])
