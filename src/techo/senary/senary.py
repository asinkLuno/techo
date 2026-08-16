"""Senary — lunar-almanac month book, landscape m5 (105×67).

Usage: techo senary 2047-08 --base tranquility --partner cnsa

  Front (odd page):  month calendar — date badges coloured by lunar
                     day/night, each cell carries an *Earth-phase* square
                     (the lunar resident's "moon phase", doc §20–21).
  Back  (even page): habit tracker — date badges coloured by day/night.
  Days:              one portrait m5 page per day (three-layer almanac
                     header + LTC/partner timeline), batch PDF.
  JSON:              pre-computed almanac per day (doc §33) — astronomy and
                     typesetting stay fully separated.
"""

import calendar
from datetime import datetime

from .. import build, sizes
from ..sizes import FONT_CMD
from ..validation import parse_year_month
from .almanac import LunarAlmanac
from .astronomy import earth_illumination, earth_is_waxing, solar_alt_az
from .bases import base_by_id
from .day import day_page
from .partners import partner_by_id

# ── Calendar (front) ──
COLS = 7
BIND = 7.0  # mm, top binding margin
GM = 4.0  # mm, margin on the other three sides
HEAD_H = 4.0
WEEKDAYS = ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")  # Monday-first

# ── Fonts (defined in sizes.py, emitted to sizes.tex) ──
FONT_CAL = FONT_CMD["small"]
FONT_TRACKER_HEAD = FONT_CMD["small"]

# ── Earth-phase indicator (shared visual language with the old moon square) ──
PS = 2.0  # mm, phase square side

# ── Habit tracker (back) ──
A = 5.5  # mm, square check cell
ITEM_W = 2  # multiplier, item column = ITEM_W * A wide
ITEMS = 4  # blank habit rows


def _day_night_color(base, utc: datetime) -> str:
    """Badge colour: ChromeYellow lunar day, CobaltBlue lunar night."""
    alt, _ = solar_alt_az(base, utc)
    return "ChromeYellow" if alt > 0 else "CobaltBlue"


def _badge_data(base, utc: datetime) -> tuple[str, float]:
    """(day/night colour, Earth illumination 0..1) at one reference instant."""
    return _day_night_color(base, utc), earth_illumination(utc)


def date_node(day: int, color: str, x: float, y: float, font: str = FONT_CAL) -> str:
    """Colored date badge — fill hugs the text, anchor=north west at (x,y) mm."""
    label = f"\\phantom{{0}}{day}" if day < 10 else str(day)
    return (
        f"  \\node[font=\\{font}, anchor=north west, fill={color}, text=white]"
        f" at ([xshift={x:.2f}mm, yshift={-y:.2f}mm]current page.north west) {{{label}}};"
    )


def phase_square(
    phase: float, is_waxing: bool, rx: float, ty: float, ps: float = PS
) -> str:
    """Phase indicator square (always ChromeYellow). (rx,ty) = top-right corner.

    Filled fraction grows leftward while waxing, shrinks while waning —
    used for the Earth phase seen from the Moon (doc §20–21).
    """
    out = [
        f"  \\draw[ChromeYellow] ([xshift={rx - ps:.2f}mm, yshift={-ty:.2f}mm]current page.north west)"
        f" rectangle ([xshift={rx:.2f}mm, yshift={-(ty + ps):.2f}mm]current page.north west);"
    ]
    if is_waxing:
        left = rx - ps * phase
        out.append(
            f"  \\fill[ChromeYellow] ([xshift={left:.2f}mm, yshift={-ty:.2f}mm]current page.north west)"
            f" rectangle ([xshift={rx:.2f}mm, yshift={-(ty + ps):.2f}mm]current page.north west);"
        )
    else:
        right = rx - ps * (1 - phase)
        out.append(
            f"  \\fill[ChromeYellow] ([xshift={rx - ps:.2f}mm, yshift={-ty:.2f}mm]current page.north west)"
            f" rectangle ([xshift={right:.2f}mm, yshift={-(ty + ps):.2f}mm]current page.north west);"
        )
    return "\n".join(out)


def _cal(almanac: LunarAlmanac, year: int, month: int, pw: float, ph: float) -> str:
    base = almanac.base
    days = calendar.monthrange(year, month)[1]
    first = calendar.monthrange(year, month)[0]  # weekday of the 1st, 0=Mon
    weeks = (first + days + COLS - 1) // COLS
    lm, rm = GM, pw - GM  # left/right edges
    gy = BIND + HEAD_H  # grid top edge
    gb = ph - GM  # grid bottom edge
    cell_w = (rm - lm) / COLS
    cell_h = (gb - gy) / weeks
    out = [
        "\\begin{tikzpicture}[remember picture, overlay, every node/.style={inner sep=0pt}]"
    ]
    # gridlines with 0.2mm gaps at intersections
    GAP = 0.2
    for i in range(COLS + 1):
        x = lm + cell_w * i
        for j in range(weeks):
            y1 = gy + cell_h * j + GAP
            y2 = gy + cell_h * (j + 1) - GAP
            out.append(
                f"  \\draw[gridline] ([xshift={x:.2f}mm, yshift={-y1:.2f}mm]current page.north west)"
                f" -- ([xshift={x:.2f}mm, yshift={-y2:.2f}mm]current page.north west);"
            )
    for j in range(weeks + 1):
        y = gy + cell_h * j
        for i in range(COLS):
            x1 = lm + cell_w * i + GAP
            x2 = lm + cell_w * (i + 1) - GAP
            out.append(
                f"  \\draw[gridline] ([xshift={x1:.2f}mm, yshift={-y:.2f}mm]current page.north west)"
                f" -- ([xshift={x2:.2f}mm, yshift={-y:.2f}mm]current page.north west);"
            )
    for i, w in enumerate(WEEKDAYS):
        x = lm + cell_w * (i + 0.5)
        out.append(
            f"  \\node[font=\\{FONT_CAL}]"
            f" at ([xshift={x:.2f}mm, yshift={-(gy - HEAD_H / 2):.2f}mm]current page.north west)"
            f" {{{w}}};"
        )
    PAD = 0.2  # mm, offset from cell edge
    for d in range(1, days + 1):
        r, c = divmod(first + d - 1, COLS)
        x = lm + cell_w * c + PAD
        y = gy + cell_h * r + PAD
        ref = almanac.reference_instant(f"{year:04d}-{month:02d}-{d:02d}")
        color, illum = _badge_data(base, ref)
        out.append(date_node(d, color, x, y))
        # earth-phase indicator at top-right — always ChromeYellow
        rx = lm + cell_w * (c + 1) - PAD
        ty = gy + cell_h * r + PAD
        out.append(phase_square(illum, earth_is_waxing(ref), rx, ty))
    out.append("\\end{tikzpicture}%")
    return "\n".join(out)


def _table(
    lm: float,
    top: float,
    dates: list[int],
    almanac: LunarAlmanac,
    year: int,
    month: int,
    with_items: bool,
    with_header: bool = True,
) -> list[str]:
    """Verticals + horizontals + header dates for one tracker table."""
    xs = [lm]
    if with_items:
        xs.append(lm + ITEM_W * A)
    for _ in dates:
        xs.append(xs[-1] + A)
    rows = ITEMS + (1 if with_header else 0)
    off = 1 if with_items else 0
    out = []
    start_i = 1 if with_header else 0  # skip top line of header
    GAP = 0.2
    for x in xs:  # verticals with gaps at intersections
        for i in range(start_i, rows):
            y1 = top + i * A + GAP
            y2 = top + (i + 1) * A - GAP
            out.append(
                f"  \\draw[gridline] ([xshift={x:.2f}mm, yshift={-y1:.2f}mm]current page.north west)"
                f" -- ([xshift={x:.2f}mm, yshift={-y2:.2f}mm]current page.north west);"
            )
    for i in range(start_i, rows + 1):  # horizontals with gaps
        y = top + i * A
        for k in range(len(xs) - 1):
            x1 = xs[k] + GAP
            x2 = xs[k + 1] - GAP
            out.append(
                f"  \\draw[gridline] ([xshift={x1:.2f}mm, yshift={-y:.2f}mm]current page.north west)"
                f" -- ([xshift={x2:.2f}mm, yshift={-y:.2f}mm]current page.north west);"
            )
    if with_header:
        hy = top + A - 0.2
        for i, d in enumerate(dates):
            ref = almanac.reference_instant(f"{year:04d}-{month:02d}-{d:02d}")
            color = _day_night_color(almanac.base, ref)
            cx = xs[off + i + 1]
            label = f"\\phantom{{0}}{d}" if d < 10 else str(d)
            out.append(
                f"  \\node[font=\\{FONT_TRACKER_HEAD}, fill={color}, text=white, anchor=south east]"
                f" at ([xshift={cx:.2f}mm, yshift={-hy:.2f}mm]current page.north west) {{{label}}};"
            )
    return out


def _tracker(almanac: LunarAlmanac, year: int, month: int, days: int, pw: float, ph: float) -> str:
    dates1 = list(range(1, 15))  # 1–14
    dates2 = list(range(15, days + 1))  # 15–end
    w1 = ITEM_W * A + len(dates1) * A
    w2 = len(dates2) * A  # no item column
    lm = (pw - max(w1, w2)) / 2
    gap = 2.0  # mm between tables
    h1 = (ITEMS + 1) * A  # with header
    h2 = ITEMS * A  # no header
    TRACKER_UP = 3.0  # mm, nudge both tables up from center
    top1 = (ph - h1 - gap - h2) / 2 - TRACKER_UP
    top2 = top1 + h1 + gap
    out = [
        "\\begin{tikzpicture}[remember picture, overlay, every node/.style={inner sep=0pt}]"
    ]
    out += _table(lm, top1, dates1, almanac, year, month, with_items=True)
    out += _table(lm, top2, dates2, almanac, year, month, with_items=False, with_header=True)
    out.append("\\end{tikzpicture}%")
    return "\n".join(out)


def generate(ym: str, base_id: str = "tranquillity", partner_id: str = "cnsa") -> None:
    year, month = parse_year_month(ym)
    almanac = LunarAlmanac(base_by_id(base_id), partner_by_id(partner_id))

    key = "67m5l"
    pw, ph = sizes.SIZES[key]["pw"], sizes.SIZES[key]["ph"]
    days = calendar.monthrange(year, month)[1]

    edition = f"senary-{year}-{month:02d}-{base_id}"
    content = [
        "\\thispagestyle{empty}%",
        _cal(almanac, year, month, pw, ph),
        "\\null",
        "\\clearpage",
        "\\thispagestyle{empty}%",
        _tracker(almanac, year, month, days, pw, ph),
        "\\null",
        "\\clearpage",
    ]
    out = build.build_edition(
        edition,
        content,
        "../../src/techo/senary/senary.tex",
        defs={"EDITION": key},
        # The calendar/tracker anchor to `current page`; second pass places them.
        passes=2,
    )
    print(
        f"Generated {edition}/content.tex + {edition}.tex "
        f"({calendar.month_name[month]} {year}, {days} days, {pw}×{ph}mm landscape)"
    )

    # ── Pre-computed almanac JSON (doc §33) ──
    json_path = out / f"almanac_{year}-{month:02d}.json"
    almanac.write_month_json(year, month, json_path)
    print(f"  → {json_path.name}")

    # ── Day pages (all portrait m5 days in one PDF) ──
    day_key = "67m5"
    pw_day, ph_day = sizes.SIZES[day_key]["pw"], sizes.SIZES[day_key]["ph"]
    day_parts = []
    for d in range(1, days + 1):
        page, _ = day_page(
            f"{year:04d}-{month:02d}-{d:02d}", almanac, pw_day, ph_day, page_no=d
        )
        day_parts.append("\\thispagestyle{empty}%")
        day_parts.append(page)
        day_parts.append("\\null")
        day_parts.append("\\clearpage")
    days_tex = (
        "\\documentclass[10pt]{article}\n"
        "\\input{../../src/techo/senary/day-preamble.tex}\n"
        "\\begin{document}\n" + "\n".join(day_parts) + "\n"
        "\\end{document}\n"
    )
    (out / "days.tex").write_text(days_tex)
    build.compile_tex("days.tex", out, passes=2)
    print(f"  → days.pdf ({days} day pages)")
