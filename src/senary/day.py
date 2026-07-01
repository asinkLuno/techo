"""Day view — single day on vertical m5 (67×105), timeline layout.

Usage: techo day 2026-07-15 [--tz Asia/Shanghai] [--location tranquility]
"""

import calendar
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import sizes
from senary.senary import LOCATIONS, _moon_info, date_node
from sizes import FONT_CMD

# ── Layout ──
LEFT_MARGIN = 9.0  # mm, date strip width (left of the divider)

FONT_DAY = FONT_CMD["medium"]
FONT_HR = FONT_CMD["small"]


def _utc_axis(year, month, day, tz_name, lat, lon):
    """UTC offset (h), UTC date at UTC midnight within the local day, and its moon color."""
    local_midnight = datetime(year, month, day, tzinfo=ZoneInfo(tz_name))
    lm_utc = local_midnight.astimezone(ZoneInfo("UTC"))
    utc_midnight = lm_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    if utc_midnight < lm_utc:
        utc_midnight += timedelta(days=1)
    offset = local_midnight.utcoffset()
    assert offset is not None  # ZoneInfo always has a UTC offset
    offset_h = offset.total_seconds() / 3600
    utc_color, _, _ = _moon_info(
        utc_midnight.year, utc_midnight.month, utc_midnight.day, "UTC", lat, lon
    )
    return offset_h, utc_midnight.day, utc_color


def _day(
    year: int,
    month: int,
    day: int,
    pw: float,
    ph: float,
    tz_name: str,
    lat: float,
    lon: float,
) -> str:
    color, _, _ = _moon_info(year, month, day, tz_name, lat, lon)
    offset_h, utc_day, utc_color = _utc_axis(year, month, day, tz_name, lat, lon)
    utc_hour = offset_h % 24  # local hour at which UTC midnight falls
    dual = abs(offset_h) > 1e-6  # non-UTC tz → fill the right (UTC) strip

    out = [
        "\\begin{tikzpicture}[remember picture, overlay, every node/.style={inner sep=0pt}]"
    ]

    vl_x = LEFT_MARGIN
    vr_x = pw - LEFT_MARGIN  # right divider, mirroring the left
    PAD = 0.1  # mm, content inset from edges

    # ── Local date badge (top-left of the left strip) ──
    out.append(date_node(day, color, PAD, PAD, FONT_DAY))
    # ── Dividers (left + right), full height ──
    for vx in (vl_x, vr_x):
        out.append(
            f"  \\draw[gridline] ([xshift={vx:.2f}mm, yshift=0mm]current page.north west)"
            f" -- ([xshift={vx:.2f}mm, yshift={-ph:.2f}mm]current page.north west);"
        )

    # ── 24-row timeline (vl_x → vr_x, full height) ──
    tl_top = 0.0
    tl_bot = ph
    slot_h = (tl_bot - tl_top) / 24

    for row in range(24):
        y = tl_top + slot_h * row
        out.append(
            f"  \\draw[gridline] ([xshift={vl_x:.2f}mm, yshift={-y:.2f}mm]current page.north west)"
            f" -- ([xshift={vr_x:.2f}mm, yshift={-y:.2f}mm]current page.north west);"
        )
        label_y = y + slot_h / 2
        out.append(
            f"  \\node[font=\\{FONT_HR}, anchor=west]"
            f" at ([xshift={vl_x + PAD + 0.8:.2f}mm, yshift={-label_y:.2f}mm]current page.north west)"
            f" {{{row}}};"
        )
        if dual:
            u_min = int(round((row * 60 - offset_h * 60) % 1440))
            uh, um = divmod(u_min, 60)
            ulabel = f"{uh}" if um == 0 else f"{uh}:{um:02d}"
            out.append(
                f"  \\node[font=\\{FONT_HR}, anchor=east]"
                f" at ([xshift={vr_x - PAD - 0.8:.2f}mm, yshift={-label_y:.2f}mm]current page.north west)"
                f" {{{ulabel}}};"
            )
    # Bottom line
    out.append(
        f"  \\draw[gridline] ([xshift={vl_x:.2f}mm, yshift={-tl_bot:.2f}mm]current page.north west)"
        f" -- ([xshift={vr_x:.2f}mm, yshift={-tl_bot:.2f}mm]current page.north west);"
    )

    # ── UTC midnight: full-width line at its height, UTC date badge in the right
    #    strip (top edge on the line, like the local date), "utc" beneath it. ──
    if dual:
        y_utc = tl_top + slot_h * utc_hour
        out.append(
            f"  \\draw[gridline] ([xshift=0mm, yshift={-y_utc:.2f}mm]current page.north west)"
            f" -- ([xshift={pw:.2f}mm, yshift={-y_utc:.2f}mm]current page.north west);"
        )
        utc_label = f"\\phantom{{0}}{utc_day}" if utc_day < 10 else str(utc_day)
        out.append(
            f"  \\node[font=\\{FONT_DAY}, anchor=north east, fill={utc_color}, text=white]"
            f" at ([xshift={pw - PAD:.2f}mm, yshift={-y_utc:.2f}mm]current page.north west)"
            f" {{{utc_label}}};"
        )
        out.append(
            f"  \\node[font=\\{FONT_HR}, anchor=north east]"
            f" at ([xshift={pw - PAD:.2f}mm, yshift={-(y_utc + 2.4):.2f}mm]current page.north west)"
            f" {{utc}};"
        )

    out.append("\\end{tikzpicture}%")
    return "\n".join(out)


def generate(datestr: str, tz_name: str = "UTC", location: str = "tranquility") -> None:
    try:
        year, month, day = (int(x) for x in datestr.split("-"))
    except ValueError:
        print(f"Expected YYYY-MM-DD (e.g. 2026-07-15), got '{datestr}'")
        sys.exit(1)
    if not (1 <= month <= 12):
        print(f"Bad month {month} (need 1–12)")
        sys.exit(1)
    if location not in LOCATIONS:
        print(f"Unknown location '{location}'. Known: {list(LOCATIONS.keys())}")
        sys.exit(1)
    lat, lon = LOCATIONS[location]

    key = "m5"
    pw, ph = sizes.SIZES[key]["pw"], sizes.SIZES[key]["ph"]
    sizes.write_sizes_tex()

    edition = f"day-{year}-{month:02d}-{day:02d}"
    out = Path("outputs") / edition
    out.mkdir(parents=True, exist_ok=True)

    content = [
        "\\thispagestyle{empty}%",
        _day(year, month, day, pw, ph, tz_name, lat, lon),
        "\\null",
        "\\clearpage",
    ]
    (out / "content.tex").write_text("\n".join(content) + "\n")
    (out / f"{edition}.tex").write_text("\\input{../../src/senary/day.tex}%\n")
    print(
        f"Generated {edition}/content.tex + {edition}.tex "
        f"({calendar.day_name[datetime(year, month, day).weekday()]} "
        f"{day} {calendar.month_name[month]} {year}, {pw}×{ph}mm portrait)"
    )
    sizes.compile(f"{edition}.tex", out)
