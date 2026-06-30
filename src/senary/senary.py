"""Senary — monthly calendar (front) + habit tracker (back), landscape m5 (105×67).

Usage: uv run python src/senary/senary.py 2026-07 [TZ] [LOCATION]
  Front (odd page): that month's calendar, landscape (no rotation — the page is wide).
  Back  (even page): two tracker tables stacked — 1–14 (item col + header) +
                     15–end (header only, no item col), 6 rows each.
"""

import calendar
import math
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import ephem

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
LOCATIONS = {"tranquility": (0.67, 23.47)}


def _to_utc(year, month, day, tz_name):
    """Return UTC datetime string for midnight local time in tz_name."""
    local = datetime(year, month, day, tzinfo=ZoneInfo(tz_name))
    utc = local.astimezone(ZoneInfo("UTC"))
    return f"{utc.year}/{utc.month:02d}/{utc.day:02d} {utc.hour:02d}:{utc.minute:02d}:{utc.second:02d}"


def check_moon(year, month, day, tz_name="UTC", lat=0.67, lon=23.47):
    """Return (is_lunar_day: bool, moon_phase: float) at local midnight.

    moon_phase: 0=new moon, 1=full moon.
    """
    lat_target = math.radians(lat)
    lon_target = math.radians(lon)
    m = ephem.Moon()
    utc_str = _to_utc(year, month, day, tz_name)
    m.compute(utc_str)
    cos_angle = math.sin(m.subsolar_lat) * math.sin(lat_target) + math.cos(
        m.subsolar_lat
    ) * math.cos(lat_target) * math.cos(float(m.colong) - math.pi / 2 - lon_target)
    return cos_angle > 0, m.moon_phase


def _moon_color(year, month, day, tz_name="UTC", lat=0.67, lon=23.47):
    """Return '#ffa700' (lunar day) or '#0047ab' (lunar night)."""
    lat, lon = math.radians(lat), math.radians(lon)
    m = ephem.Moon()
    m.compute(_to_utc(year, month, day, tz_name))
    cos_a = math.sin(m.subsolar_lat) * math.sin(lat) + math.cos(
        m.subsolar_lat
    ) * math.cos(lat) * math.cos(float(m.colong) - math.pi / 2 - lon)
    return "ChromeYellow" if cos_a > 0 else "CobaltBlue"


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
    for i, w in enumerate(WEEKDAYS):
        x = lm + cell_w * (i + 0.5)
        out.append(
            f"  \\node[font=\\{FONT_CAL}]"
            f" at ([xshift={x:.2f}mm, yshift={-(gy - HEAD_H / 2):.2f}mm]current page.north west)"
            f" {{{w}}};"
        )
    PAD = 0.1  # mm, offset from cell top-left
    for d in range(1, days + 1):
        r, c = divmod(first + d - 1, COLS)
        x = lm + cell_w * c + PAD
        y = gy + cell_h * r + PAD
        color = _moon_color(year, month, d, tz_name, lat, lon)
        label = f"\\phantom{{0}}{d}" if d < 10 else str(d)
        out.append(
            f"  \\node[font=\\{FONT_CAL}, anchor=north west, fill={color}, text=white]"
            f" at ([xshift={x:.2f}mm, yshift={-y:.2f}mm]current page.north west) {{{label}}};"
        )
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
        hy = top + A - 0.1
        for i, d in enumerate(dates):
            color = _moon_color(year, month, d, tz_name, lat, lon)
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
    top1 = (ph - h1 - gap - h2) / 2
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


if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 4:
        print("Usage: uv run python src/senary/senary.py YYYY-MM [TZ] [LOCATION]")
        print("  TZ: IANA timezone name (default: UTC), e.g. Asia/Shanghai")
        print(f"  LOCATION: {list(LOCATIONS.keys())} (default: tranquility)")
        sys.exit(1)
    tz_name = sys.argv[2] if len(sys.argv) >= 3 else "UTC"
    location = sys.argv[3] if len(sys.argv) >= 4 else "tranquility"
    generate(sys.argv[1], tz_name, location)
    year, month = (int(x) for x in sys.argv[1].split("-"))
    lat, lon = LOCATIONS[location]
