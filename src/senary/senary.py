"""Senary — monthly calendar + habit tracker + day pages, landscape m5 (105×67).

Usage: techo senary 2026-07 [--tz Asia/Shanghai] [--location tranquility]
  Front (odd page): that month's calendar, landscape (no rotation — the page is wide).
  Back  (even page): two tracker tables stacked — 1–14 (item col + header) +
                     15–end (header only, no item col), 6 rows each.
  Day pages: one portrait m5 page per day of the month (timeline view).
"""

import calendar
import math
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import ephem

import sizes
from sizes import FONT_CMD

# ── Calendar (front) ──
COLS = 7
BIND = 7.0  # mm, top binding margin
GM = 4.0  # mm, margin on the other three sides (left/right/bottom)
HEAD_H = 4.0
WEEKDAYS = ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")  # Monday-first

# ── Fonts (defined in sizes.py, emitted to sizes.tex) ──
FONT_CAL = FONT_CMD["small"]
FONT_TRACKER_HEAD = FONT_CMD["small"]

# ── Moon phase indicator (shared with day.py) ──
PS = 2.0  # mm, phase square side (matches digit height of \FontSmall, 8pt)

# ── Habit tracker (back) ──
A = 5.5  # mm, square check cell
ITEM_W = 2  # multiplier, item column = ITEM_W * A wide
ITEMS = 4  # blank habit rows
LOCATIONS = {"tranquility": (0.67, 23.47)}


def _to_utc(year, month, day, tz_name):
    """Return UTC datetime string for midnight local time in tz_name."""
    local = datetime(year, month, day, tzinfo=ZoneInfo(tz_name))
    utc = local.astimezone(ZoneInfo("UTC"))
    return f"{utc.year}/{utc.month:02d}/{utc.day:02d} {utc.hour:02d}:{utc.minute:02d}:{utc.second:02d}"


def _moon_info(year, month, day, tz_name="UTC", lat=0.67, lon=23.47):
    """Return (color: str, phase: float, is_waxing: bool). phase: 0=new, 1=full."""
    lat_r, lon_r = math.radians(lat), math.radians(lon)
    m = ephem.Moon()
    m.compute(_to_utc(year, month, day, tz_name))
    cos_a = math.sin(m.subsolar_lat) * math.sin(lat_r) + math.cos(
        m.subsolar_lat
    ) * math.cos(lat_r) * math.cos(float(m.colong) - math.pi / 2 - lon_r)
    color = "ChromeYellow" if cos_a > 0 else "CobaltBlue"
    phase = m.moon_phase
    # waxing/waning: compare with next day's phase
    days_in_month = calendar.monthrange(year, month)[1]
    if day < days_in_month:
        m2 = ephem.Moon()
        m2.compute(_to_utc(year, month, day + 1, tz_name))
        is_waxing = phase < m2.moon_phase
    else:
        is_waxing = True  # ponytail: last day, assume waxing
    return color, phase, is_waxing


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
    """Phase indicator square (always ChromeYellow). (rx,ty) = top-right corner; spans ps×ps."""
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


def _cal(
    year: int,
    month: int,
    pw: float,
    ph: float,
    tz_name: str = "UTC",
    lat: float = 0.67,
    lon: float = 23.47,
) -> str:
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
        color, phase, is_waxing = _moon_info(year, month, d, tz_name, lat, lon)
        out.append(date_node(d, color, x, y))
        # phase indicator at top-right — always ChromeYellow
        rx = lm + cell_w * (c + 1) - PAD
        ty = gy + cell_h * r + PAD
        out.append(phase_square(phase, is_waxing, rx, ty))
    out.append("\\end{tikzpicture}%")
    return "\n".join(out)


def _table(
    lm: float,
    top: float,
    dates: list[int],
    year: int,
    month: int,
    tz_name: str,
    lat: float,
    lon: float,
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
            color, _, _ = _moon_info(year, month, d, tz_name, lat, lon)
            cx = xs[off + i + 1]
            label = f"\\phantom{{0}}{d}" if d < 10 else str(d)
            out.append(
                f"  \\node[font=\\{FONT_TRACKER_HEAD}, fill={color}, text=white, anchor=south east]"
                f" at ([xshift={cx:.2f}mm, yshift={-hy:.2f}mm]current page.north west) {{{label}}};"
            )
    return out


def _tracker(
    year: int,
    month: int,
    days: int,
    pw: float,
    ph: float,
    tz_name: str = "UTC",
    lat: float = 0.67,
    lon: float = 23.47,
) -> str:
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
    out += _table(lm, top1, dates1, year, month, tz_name, lat, lon, with_items=True)
    out += _table(
        lm,
        top2,
        dates2,
        year,
        month,
        tz_name,
        lat,
        lon,
        with_items=False,
        with_header=True,
    )
    out.append("\\end{tikzpicture}%")
    return "\n".join(out)


def generate(ym: str, tz_name: str = "UTC", location: str = "tranquility") -> None:
    try:
        year, month = (int(x) for x in ym.split("-"))
    except ValueError:
        print(f"Expected YYYY-MM (e.g. 2026-07), got '{ym}'")
        sys.exit(1)
    if not (1 <= month <= 12):
        print(f"Bad month {month} (need 1–12)")
        sys.exit(1)
    if location not in LOCATIONS:
        print(f"Unknown location '{location}'. Known: {list(LOCATIONS.keys())}")
        sys.exit(1)
    lat, lon = LOCATIONS[location]

    key = "m5l"
    pw, ph = sizes.SIZES[key]["pw"], sizes.SIZES[key]["ph"]
    sizes.write_sizes_tex()
    days = calendar.monthrange(year, month)[1]

    edition = f"senary-{year}-{month:02d}"
    out = Path("outputs") / edition
    out.mkdir(parents=True, exist_ok=True)
    content = [
        "\\thispagestyle{empty}%",
        _cal(year, month, pw, ph, tz_name, lat, lon),
        "\\null",
        "\\clearpage",
        "\\thispagestyle{empty}%",
        _tracker(year, month, days, pw, ph, tz_name, lat, lon),
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

    # ── Day pages (one portrait m5 per day) ──
    from senary.day import generate as _generate_day

    for d in range(1, days + 1):
        _generate_day(f"{year}-{month:02d}-{d:02d}", tz_name, location)
