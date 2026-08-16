"""Day view — single day on portrait m5 (67×105), lunar-almanac layout.

Three-layer header (design doc §24–25):

1. social time   — LTC date · weekday · lunation (L094 · 83%)
2. earth contact — partner local time · work-window status
3. lunar nature  — solar altitude/state · next transition · earth phase

Below the header: a 24-row LTC timeline.  The right edge carries the
partner's local hours, a shaded work-window band, and the partner date
rollover line — the moon-side page answers “can I reach Earth now?” at a
glance (doc §7, §9).
"""

import calendar
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .. import sizes
from ..sizes import FONT_CMD
from ..validation import parse_date
from .almanac import AlmanacDay, LunarAlmanac
from .partners import EarthPartner, partner_time, work_window_segments
from .timebase import to_utc

# ── Layout ──
LEFT_MARGIN = 9.0  # mm, date strip width (left of the divider)
HEADER_H = 20.0  # mm, three-layer almanac header above the timeline

FONT_DATE = FONT_CMD["medium"]
FONT_HR = FONT_CMD["small"]

WORK_FILL = "ChromeYellow!35"


def _fmt_remaining(hours: float | None) -> str:
    """Countdown label: −4d17h / −9d / −13h (doc §15 prints the minus sign)."""
    if hours is None:
        return "—"
    total = int(round(hours))
    d, h = divmod(total, 24)
    if d and h:
        return f"−{d}d{h:02d}h"
    if d:
        return f"−{d}d"
    return f"−{h}h"


def _header_lines(day: AlmanacDay) -> list[tuple[str, str, str | None]]:
    """(left, right, status-color) rows for the three layers."""
    astro = day.astronomy
    mon = calendar.month_abbr[day.utc.month].upper()
    weekday = calendar.day_abbr[day.weekday].upper()
    lunation = f"{day.lunation_label} · {day.lunation_percent}%"

    p_local = day.partner_local_time
    dot_color = "NeonGreen" if day.partner_working else "IronOxideRed"
    partner_left = f"{p_local:%H:%M} {partner_short(day)}"
    partner_right = day.partner_status_label.replace("WORK →", "WORK→").replace(
        "OFF opens", "OFF→"
    )

    if astro.astronomical_day:
        state = "DAY"
    else:
        state = "NIGHT"
    sun_left = f"SOL {astro.solar_altitude_deg:+.1f}°{astro.solar_trend}"
    if day.base_id == "shackleton":
        sun_left += f" AZ{astro.solar_azimuth_deg:03.0f}°"
        state = "DIRECT LIGHT" if astro.direct_sunlight else "SHADOW"
    sun_left += f" {state}"
    trans_label, trans_h = day.next_transition
    sun_right = f"{(trans_label or '').upper()} {_fmt_remaining(trans_h)}"

    earth_left = f"EARTH {astro.earth_illumination * 100:.0f}%"
    phase = astro.earth_phase_name
    if any(k in phase for k in ("GIBBOUS", "QUARTER", "NEAR", "CRESCENT")):
        earth_left += f" {phase.split()[0][:4]}"
    earth_right = f"ALT {astro.earth_altitude_deg:+.1f}°"

    return [
        (f"{day.utc.year} {mon} {day.utc.day:02d} · {weekday}", lunation, None),
        (partner_left, partner_right, dot_color),
        (earth_left, earth_right, None),
        (sun_left, sun_right, None),
    ]


def partner_short(day: AlmanacDay) -> str:
    """Partner label cached on the snapshot's metadata."""
    from .partners import partner_by_id

    return partner_by_id(day.partner_id).short


def _header(day: AlmanacDay, x0: float, x1: float) -> list[str]:
    """Nodes for the almanac header between x0..x1, from the page top."""
    out = []
    y = 0.9  # mm below page top
    rows = _header_lines(day)
    for i, (left, right, dot_color) in enumerate(rows):
        font = FONT_DATE if i == 0 else FONT_HR
        line_h = 4.6 if i == 0 else 3.7
        if i == 2:  # small gap between contact and nature layers
            y += 0.6
        right_tex = _tex(right)
        if dot_color:
            glyph = "●" if day.partner_working else "○"
            right_tex = f"\\textcolor{{{dot_color}}}{{{glyph}}} {right_tex}"
        out.append(
            f"  \\node[font=\\{font}, anchor=north west]"
            f" at ([xshift={x0:.2f}mm, yshift={-y:.2f}mm]current page.north west)"
            f" {{{_tex(left)}}};"
        )
        out.append(
            f"  \\node[font=\\{font}, anchor=north east]"
            f" at ([xshift={x1:.2f}mm, yshift={-y:.2f}mm]current page.north west)"
            f" {{{right_tex}}};"
        )
        y += line_h
    # header rule closing the third layer
    out.append(
        f"  \\draw[gridline] ([xshift={x0:.2f}mm, yshift={-HEADER_H + 1.2:.2f}mm]current page.north west)"
        f" -- ([xshift={x1:.2f}mm, yshift={-HEADER_H + 1.2:.2f}mm]current page.north west);"
    )
    return out


def _tex(text: str) -> str:
    """Escape the few TeX-active characters we may emit."""
    return (
        text.replace("\\", "\\textbackslash{}")
        .replace("&", "\\&")
        .replace("%", "\\%")
        .replace("$", "\\$")
        .replace("#", "\\#")
        .replace("_", "\\_")
        .replace("{", "\\{")
        .replace("}", "\\}")
        .replace("~", "\\textasciitilde{}")
        .replace("^", "\\textasciicircum{}")
    )


def _day(
    day: AlmanacDay,
    t0_utc: datetime,
    partner: EarthPartner,
    pw: float,
    ph: float,
) -> str:
    """One portrait day page.  Timeline spans LTC [00,24) of the page date."""
    out = [
        "\\begin{tikzpicture}[remember picture, overlay, every node/.style={inner sep=0pt}]"
    ]

    vl_x = LEFT_MARGIN
    vr_x = pw - LEFT_MARGIN
    PAD = 0.1  # mm, content inset from edges

    # ── Date badge (top-left strip), coloured by lunar day/night ──
    color = "ChromeYellow" if day.astronomy.astronomical_day else "CobaltBlue"
    from .senary import date_node

    out.append(date_node(day.utc.day, color, PAD, PAD, FONT_DATE))

    # ── Dividers (left + right), full height ──
    for vx in (vl_x, vr_x):
        out.append(
            f"  \\draw[gridline] ([xshift={vx:.2f}mm, yshift=0mm]current page.north west)"
            f" -- ([xshift={vx:.2f}mm, yshift={-ph:.2f}mm]current page.north west);"
        )

    # ── Almanac header (three layers) ──
    out += _header(day, vl_x + PAD + 0.8, vr_x - PAD - 0.8)

    # ── 24-row LTC timeline ──
    tl_top = HEADER_H
    tl_bot = ph
    slot_h = (tl_bot - tl_top) / 24

    # work-window band (behind the grid)
    for seg_start, seg_end in work_window_segments(t0_utc, timedelta(hours=24), partner):
        y1 = tl_top + (seg_start - t0_utc).total_seconds() / 3600.0 * slot_h
        y2 = tl_top + (seg_end - t0_utc).total_seconds() / 3600.0 * slot_h
        out.append(
            f"  \\fill[{WORK_FILL}] ([xshift={vl_x:.2f}mm, yshift={-y1:.2f}mm]current page.north west)"
            f" rectangle ([xshift={vr_x:.2f}mm, yshift={-y2:.2f}mm]current page.north west);"
        )

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
        # partner local time at mid-row
        local = partner_time(t0_utc + timedelta(hours=row + 0.5), partner)
        if local.minute == 0:
            plabel = f"{local.hour}"
        else:
            plabel = f"{local.hour}:{local.minute:02d}"
        out.append(
            f"  \\node[font=\\{FONT_HR}, anchor=east]"
            f" at ([xshift={vr_x - PAD - 0.8:.2f}mm, yshift={-label_y:.2f}mm]current page.north west)"
            f" {{{plabel}}};"
        )
    out.append(
        f"  \\draw[gridline] ([xshift={vl_x:.2f}mm, yshift={-tl_bot:.2f}mm]current page.north west)"
        f" -- ([xshift={vr_x:.2f}mm, yshift={-tl_bot:.2f}mm]current page.north west);"
    )

    # ── Partner date rollover: full-width line + date badge on the right ──
    for row in range(24):
        b0 = partner_time(t0_utc + timedelta(hours=row), partner)
        b1 = partner_time(t0_utc + timedelta(hours=row + 1), partner)
        if b0.date() != b1.date():
            y = tl_top + slot_h * (row + 1)
            out.append(
                f"  \\draw[gridline] ([xshift=0mm, yshift={-y:.2f}mm]current page.north west)"
                f" -- ([xshift={pw:.2f}mm, yshift={-y:.2f}mm]current page.north west);"
            )
            label = f"\\phantom{{0}}{b1.day}" if b1.day < 10 else str(b1.day)
            out.append(
                f"  \\node[font=\\{FONT_DATE}, anchor=north east, fill=ChromeYellow, text=white]"
                f" at ([xshift={pw - PAD:.2f}mm, yshift={-y:.2f}mm]current page.north west)"
                f" {{{label}}};"
            )

    out.append("\\end{tikzpicture}%")
    return "\n".join(out)


def day_page(
    datestr: str, almanac: LunarAlmanac, pw: float, ph: float
) -> tuple[str, AlmanacDay]:
    """TikZ for one day page + its almanac snapshot (08:00 LTC reference)."""
    requested = parse_date(datestr)
    ltc_midnight = datetime(
        requested.year, requested.month, requested.day, tzinfo=timezone.utc
    )
    t0 = to_utc(ltc_midnight)
    day = almanac.at(almanac.reference_instant(requested.isoformat()))
    return _day(day, t0, almanac.partner, pw, ph), day


def generate(
    datestr: str, base_id: str = "tranquillity", partner_id: str = "cnsa"
) -> None:
    """Single-day edition (debug/preview entry point)."""
    from .bases import base_by_id
    from .partners import partner_by_id

    almanac = LunarAlmanac(base_by_id(base_id), partner_by_id(partner_id))

    key = "67m5"
    pw, ph = sizes.SIZES[key]["pw"], sizes.SIZES[key]["ph"]
    sizes.write_sizes_tex()

    requested = parse_date(datestr)
    edition = f"day-{requested.isoformat()}-{base_id}"
    out = Path("outputs") / edition
    out.mkdir(parents=True, exist_ok=True)

    content, _ = day_page(datestr, almanac, pw, ph)
    tex = [
        "\\thispagestyle{empty}%",
        content,
        "\\null",
        "\\clearpage",
    ]
    (out / "content.tex").write_text("\n".join(tex) + "\n")
    (out / f"{edition}.tex").write_text("\\input{../../src/techo/senary/day.tex}%\n")
    print(f"Generated {edition}/content.tex + {edition}.tex ({pw}×{ph}mm portrait)")
    sizes.compile(f"{edition}.tex", out)
