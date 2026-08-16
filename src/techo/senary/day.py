"""Day view — single day on portrait m5 (67×105), lunar-almanac layout v2.

Two-line header (design doc v2 §1):

1. date — `2026 AUG 01 · SAT` (Level 1) · lunation `L-166 · 60%` (Level 3)
2. sky  — `EARTH 07% ↑  SOL +30.0° ↓ · DAY  ALT +61.0°  SET 2D11H`
          (Level 2; Shackleton shows `DIRECT LIGHT` / `SHADOW` instead of
          `DAY` / `NIGHT`, and counts down to LIGHT / SHADOW)

Below the header: a BJT main axis (staff civil reference, fixed UTC+8)
with LTC demoted to a secondary column (doc v2 §2) — two continuous red
verticals (BJT|LTC and time|writing), no column headers, no slot numbers,
no hour lines.  The writing area is a plain dot grid (doc v2 §3).  The
moon-day yellow band is astronomy-driven: solar altitude > 0° (ordinary
bases) or > terrain horizon (direct light at polar bases), with actual
minute-level crossing boundaries — multiple bands per day at Shackleton
(doc v2 §4).  Page numbers are orange corner blocks, odd left / even right
mirrored per the spread (doc v2 §6).
"""

import calendar
from datetime import datetime, timedelta

from .. import build, sizes
from ..sizes import FONT_CMD
from ..texutil import tex_escape
from ..validation import parse_date
from .almanac import AlmanacDay, LunarAlmanac
from .astronomy import sunlight_segments
from .timebase import BJT_TZ, bjt_to_utc, to_ltc

# ── Layout (67×105 m5) ──
PAD = 2.0  # mm, page-frame inset

HEADER_ROW1_Y = 2.4  # mm below frame top — date (Level 1)
HEADER_ROW2_Y = 6.6  # mm — sky line (Level 2)
HEADER_BOT = 10.5  # mm — header rule; 8.5 mm band ≈ 8.1% of page height

# Three font levels (doc v2 §7): on m5 the width forces L2 and L3 to share
# the smallest size; hierarchy is carried by position and colour.
FONT_L1 = FONT_CMD["medium"]  # 9 pt — date
FONT_L2 = FONT_CMD["tiny"]  # 5 pt — sky line
FONT_L3 = FONT_CMD["tiny"]  # 5 pt — times + lunation

PAGE_NUM_W, PAGE_NUM_H = 6.5, 4.2  # mm, orange corner block

# Time column (doc v2 §2): BJT | LTC — 12.0 mm ≈ 19% of the 62 mm content
BJT_X = PAD + 0.5  # west anchor of BJT labels
TIME_LABEL_W = 4.8  # mm, "08:30" at 5 pt
LINE1_X = BJT_X + TIME_LABEL_W + 0.7  # BJT | LTC divider
LTC_X = LINE1_X + 0.5  # west anchor of LTC labels
LINE2_X = LTC_X + TIME_LABEL_W + 0.7  # time column | writing area

DOT_STEP = 4.0  # mm, dot-grid spacing (doc v2 §3)
DOT_R = 0.35  # mm, dot radius
DOT_PAD = 0.5  # mm, dot field inset from line2 / frame

TRANSITION_LABELS = {
    "sunset": "SET",
    "sunrise": "RISE",
    "direct-light": "LIGHT",
    "direct-shadow": "SHADOW",
}


def _fmt_countdown(hours: float | None) -> str:
    """Countdown label, positive: 2D11H / 4D06H / 9H (doc v2 §1, no minus)."""
    if hours is None:
        return "—"
    total = int(round(hours))
    d, h = divmod(total, 24)
    if d and h:
        return f"{d}D{h:02d}H"
    if d:
        return f"{d}D"
    return f"{h}H"


def _sky_state(day: AlmanacDay) -> str:
    """Solar state: DAY/NIGHT, or DIRECT LIGHT/SHADOW at polar bases."""
    astro = day.astronomy
    if day.base_id == "shackleton":
        return "DIRECT LIGHT" if astro.direct_sunlight else "SHADOW"
    return "DAY" if astro.astronomical_day else "NIGHT"


def _sky_line(day: AlmanacDay) -> str:
    """Row 2: EARTH 07% ↑  SOL +30.0° ↓ · DAY  ALT +61.0°  SET 2D11H."""
    astro = day.astronomy
    earth = f"EARTH {astro.earth_illumination * 100:.0f}% {day.earth_trend}"
    sol = f"SOL {astro.solar_altitude_deg:+.1f}°{astro.solar_trend} · {_sky_state(day)}"
    alt = f"ALT {astro.earth_altitude_deg:+.1f}°"
    label, hours = day.next_transition
    event = TRANSITION_LABELS.get(label or "", "")
    countdown = f"{event} {_fmt_countdown(hours)}" if event else ""
    return "  ".join(part for part in (earth, sol, alt, countdown) if part)


def _date_label(day: AlmanacDay) -> str:
    """`2026 AUG 01 · SAT` — the page's BJT date (day.date at 08:00 BJT ref)."""
    year, month, d = (int(part) for part in day.date.split("-"))
    return (
        f"{year} {calendar.month_abbr[month].upper()} {d:02d}"
        f" · {calendar.day_abbr[day.weekday].upper()}"
    )


def _dot_grid(fl: float, fr: float, fb: float) -> list[str]:
    """Plain dot grid over the writing area (no lines at all, doc v2 §3)."""
    x0, x1 = LINE2_X + DOT_PAD, fr - DOT_PAD
    y0, y1 = HEADER_BOT + DOT_PAD, fb - DOT_PAD
    cols = int((x1 - x0) // DOT_STEP)
    rows = int((y1 - y0) // DOT_STEP)
    off_x = (x1 - x0 - cols * DOT_STEP) / 2
    off_y = (y1 - y0 - rows * DOT_STEP) / 2
    out = []
    for j in range(rows):
        for i in range(cols):
            x = x0 + off_x + i * DOT_STEP
            y = y0 + off_y + j * DOT_STEP
            out.append(
                f"  \\fill[SenaryDot] ([xshift={x:.2f}mm, yshift={-y:.2f}mm]current page.north west)"
                f" circle ({DOT_R}mm);"
            )
    return out


def _day(
    day: AlmanacDay,
    t0: datetime,
    almanac: LunarAlmanac,
    pw: float,
    ph: float,
    page_no: int,
) -> str:
    """One portrait day page.  Main axis spans BJT [00,24) of the page date.

    *t0* — UTC instant of BJT midnight (the page's day window [t0, t0+24h)).
    *page_no* — 1-based; odd pages carry the orange block top-left, even
    pages top-right (mirrored per the spread, doc v2 §6).
    """
    is_odd = page_no % 2 == 1
    fl, fr = PAD, pw - PAD
    ft, fb = PAD, ph - PAD
    row_h = (fb - HEADER_BOT) / 24  # 24 hour rows over the time zone
    out = [
        "\\begin{tikzpicture}[remember picture, overlay, every node/.style={inner sep=0pt}]"
    ]

    # ── Moon-day yellow bands — astronomy-driven, behind everything ──
    for seg_start, seg_end in sunlight_segments(almanac.base, t0, t0 + timedelta(hours=24)):
        y1 = HEADER_BOT + (seg_start - t0).total_seconds() / 3600.0 * row_h
        y2 = HEADER_BOT + (seg_end - t0).total_seconds() / 3600.0 * row_h
        out.append(
            f"  \\fill[SenarySunlight] ([xshift={fl:.2f}mm, yshift={-y1:.2f}mm]current page.north west)"
            f" rectangle ([xshift={fr:.2f}mm, yshift={-y2:.2f}mm]current page.north west);"
        )

    # ── Writing area: dot grid ──
    out += _dot_grid(fl, fr, fb)

    # ── Structural lines (SenaryBrick, 0.4 pt): frame, header rule, two verticals ──
    out.append(
        f"  \\draw[gridline] ([xshift={fl:.2f}mm, yshift={-ft:.2f}mm]current page.north west)"
        f" rectangle ([xshift={fr:.2f}mm, yshift={-fb:.2f}mm]current page.north west);"
    )
    out.append(
        f"  \\draw[gridline] ([xshift={fl:.2f}mm, yshift={-HEADER_BOT:.2f}mm]current page.north west)"
        f" -- ([xshift={fr:.2f}mm, yshift={-HEADER_BOT:.2f}mm]current page.north west);"
    )
    for vx in (LINE1_X, LINE2_X):
        out.append(
            f"  \\draw[gridline] ([xshift={vx:.2f}mm, yshift={-HEADER_BOT:.2f}mm]current page.north west)"
            f" -- ([xshift={vx:.2f}mm, yshift={-fb:.2f}mm]current page.north west);"
        )

    # ── Page-number block: odd top-left, even top-right (mirrored) ──
    px = fl if is_odd else fr - PAGE_NUM_W
    cx, cy = px + PAGE_NUM_W / 2, ft + PAGE_NUM_H / 2
    out.append(
        f"  \\fill[SenaryPageNum] ([xshift={px:.2f}mm, yshift={-ft:.2f}mm]current page.north west)"
        f" rectangle ([xshift={px + PAGE_NUM_W:.2f}mm, yshift={-(ft + PAGE_NUM_H):.2f}mm]current page.north west);"
    )
    out.append(
        f"  \\node[font=\\{FONT_L1}, text=white, anchor=center]"
        f" at ([xshift={cx:.2f}mm, yshift={-cy:.2f}mm]current page.north west) {{{page_no}}};"
    )

    # ── Two-line header ──
    # row 1: date (L1) left of the corner block; lunation (L3) top-right
    date_x = fl + PAGE_NUM_W + 1.0 if is_odd else fl + 0.5
    lun_x = fr - 0.5 if is_odd else fr - PAGE_NUM_W - 1.0
    out.append(
        f"  \\node[font=\\{FONT_L1}, anchor=north west]"
        f" at ([xshift={date_x:.2f}mm, yshift={-HEADER_ROW1_Y:.2f}mm]current page.north west)"
        f" {{{tex_escape(_date_label(day))}}};"
    )
    lunation = f"{day.lunation_label} · {day.lunation_percent}%"
    out.append(
        f"  \\node[font=\\{FONT_L3}, anchor=north east]"
        f" at ([xshift={lun_x:.2f}mm, yshift={-HEADER_ROW1_Y:.2f}mm]current page.north west)"
        f" {{{tex_escape(lunation)}}};"
    )
    # row 2: the sky line, full content width
    out.append(
        f"  \\node[font=\\{FONT_L2}, anchor=north west]"
        f" at ([xshift={fl + 0.5:.2f}mm, yshift={-HEADER_ROW2_Y:.2f}mm]current page.north west)"
        f" {{{tex_escape(_sky_line(day))}}};"
    )

    # ── BJT | LTC time column: 24 whole-hour rows, no column headers ──
    for row in range(24):
        y = HEADER_BOT + row_h * (row + 0.5)
        bjt = f"{row:02d}:00"
        ltc = to_ltc(t0 + timedelta(hours=row))
        out.append(
            f"  \\node[font=\\{FONT_L3}, text=SenaryInk, anchor=west]"
            f" at ([xshift={BJT_X:.2f}mm, yshift={-y:.2f}mm]current page.north west)"
            f" {{{bjt}}};"
        )
        out.append(
            f"  \\node[font=\\{FONT_L3}, text=SenaryGray, anchor=west]"
            f" at ([xshift={LTC_X:.2f}mm, yshift={-y:.2f}mm]current page.north west)"
            f" {{{ltc:%H:%M}}};"
        )

    out.append("\\end{tikzpicture}%")
    return "\n".join(out)


def day_page(
    datestr: str,
    almanac: LunarAlmanac,
    pw: float,
    ph: float,
    page_no: int = 1,
) -> tuple[str, AlmanacDay]:
    """TikZ for one day page + its almanac snapshot.

    The page is anchored on the *BJT* date (doc v2 open question 1): the
    header shows the BJT calendar date, the axis covers BJT [00,24), and
    the snapshot is taken at 08:00 BJT (civil morning).
    """
    requested = parse_date(datestr)
    t0 = bjt_to_utc(
        datetime(requested.year, requested.month, requested.day, tzinfo=BJT_TZ)
    )
    day = almanac.at(almanac.reference_instant_bjt(requested.isoformat()))
    return _day(day, t0, almanac, pw, ph, page_no), day


def generate(
    datestr: str, base_id: str = "tranquillity", partner_id: str = "cnsa"
) -> None:
    """Single-day edition (debug/preview entry point)."""
    from .bases import base_by_id
    from .partners import partner_by_id

    almanac = LunarAlmanac(base_by_id(base_id), partner_by_id(partner_id))

    key = "67m5"
    pw, ph = sizes.SIZES[key]["pw"], sizes.SIZES[key]["ph"]

    requested = parse_date(datestr)
    edition = f"day-{requested.isoformat()}-{base_id}"

    content, _ = day_page(datestr, almanac, pw, ph, page_no=1)
    tex = [
        "\\thispagestyle{empty}%",
        content,
        "\\null",
        "\\clearpage",
    ]
    # Day pages anchor to `current page`; second pass places them.
    build.build_edition(edition, tex, "../../src/techo/senary/day.tex", passes=2)
    print(f"Generated {edition}/content.tex + {edition}.tex ({pw}×{ph}mm portrait)")


if __name__ == "__main__":
    import sys

    datestr = sys.argv[1] if len(sys.argv) > 1 else "2026-08-16"
    base_id = sys.argv[2] if len(sys.argv) > 2 else "tranquillity"
    generate(datestr, base_id)
